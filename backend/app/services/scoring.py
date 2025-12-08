"""Scoring service for grading picks"""

import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game
from app.db.models.user import User
from app.schemas.scoring import UserScore
from app.core.logging_config import ScoringLogger
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional


class ScoringService:
    """Service for scoring and grading picks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = ScoringLogger("app.services.scoring")

    async def calculate_ftd_points(
        self, pick: Pick, first_td_scorer: Optional[UUID]
    ) -> int:
        """
        Calculate FTD (First Touchdown) points for a pick.

        Args:
            pick: The pick to evaluate
            first_td_scorer: UUID of the player who scored the first touchdown (None if no TDs)

        Returns:
            3 if pick matches first TD scorer, 0 otherwise
        """
        if first_td_scorer is None:
            return 0

        if pick.player_id == first_td_scorer:
            return 3

        return 0

    async def calculate_attd_points(
        self, pick: Pick, all_td_scorers: List[UUID]
    ) -> int:
        """
        Calculate ATTD (Anytime Touchdown) points for a pick.

        Args:
            pick: The pick to evaluate
            all_td_scorers: List of UUIDs (or strings) of all players who scored touchdowns

        Returns:
            1 if pick's player scored any touchdown, 0 otherwise
        """
        if not all_td_scorers:
            return 0

        # Convert all_td_scorers to UUIDs if they're strings (from JSON)
        td_scorer_uuids = []
        for scorer in all_td_scorers:
            if isinstance(scorer, str):
                td_scorer_uuids.append(UUID(scorer))
            else:
                td_scorer_uuids.append(scorer)

        if pick.player_id in td_scorer_uuids:
            return 1

        return 0

    async def update_pick_result(
        self, pick: Pick, ftd_points: int, attd_points: int, status: PickResult
    ) -> None:
        """
        Update a pick with scoring results.

        Args:
            pick: The pick to update
            ftd_points: Points awarded for FTD (0 or 3)
            attd_points: Points awarded for ATTD (0 or 1)
            status: The result status (WIN or LOSS)
        """
        pick.ftd_points = ftd_points
        pick.attd_points = attd_points
        pick.total_points = ftd_points + attd_points
        pick.status = status
        pick.scored_at = datetime.now(timezone.utc)
        pick.settled_at = datetime.now(timezone.utc)
        await self.db.flush()  # Flush changes to make them visible in the same transaction

    async def update_user_score(self, user_id: UUID, points: int, is_win: bool) -> None:
        """
        Update a user's total score and win/loss counts.

        Args:
            user_id: UUID of the user to update
            points: Points to add to user's total score
            is_win: Whether this is a win (True) or loss (False)
        """
        # Get the user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return

        # Update user scores
        user.total_score += points
        if is_win:
            user.total_wins += 1
        else:
            user.total_losses += 1

        await self.db.flush()

    async def get_user_total_score(self, user_id: UUID) -> Optional[UserScore]:
        """
        Get a user's total score and statistics.

        This method calculates:
        - Total score (sum of all points from winning picks)
        - Total wins (count of winning picks)
        - Total losses (count of losing picks)
        - Win percentage

        Args:
            user_id: UUID of the user

        Returns:
            UserScore object with total, wins, losses, percentage, or None if user not found

        Requirements: 11.1, 11.2, 11.3, 11.4
        """
        # Get the user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Calculate win percentage
        total_picks = user.total_wins + user.total_losses
        win_percentage = (
            (user.total_wins / total_picks * 100) if total_picks > 0 else 0.0
        )

        return UserScore(
            user_id=user.id,
            total_score=user.total_score,
            total_wins=user.total_wins,
            total_losses=user.total_losses,
            win_percentage=win_percentage,
        )

    async def get_pick_result(self, pick_id: UUID) -> Optional[dict]:
        """
        Get detailed result for a specific pick.

        Args:
            pick_id: UUID of the pick

        Returns:
            Dictionary with pick result details, or None if pick not found

        Requirements: 12.1, 12.2, 12.3, 12.4
        """
        # Get the pick with its game
        result = await self.db.execute(
            select(Pick, Game)
            .join(Game, Pick.game_id == Game.id)
            .where(Pick.id == pick_id)
        )
        row = result.first()

        if not row:
            return None

        pick, game = row

        return {
            "pick_id": pick.id,
            "status": pick.status.value,
            "ftd_points": pick.ftd_points,
            "attd_points": pick.attd_points,
            "total_points": pick.total_points,
            "actual_first_td_scorer": game.first_td_scorer_player_id,
            "all_td_scorers": game.all_td_scorer_player_ids or [],
            "scored_at": pick.scored_at,
        }

    async def get_game_result(self, game_id: UUID) -> Optional[dict]:
        """
        Get scoring results for a game.

        Args:
            game_id: UUID of the game

        Returns:
            Dictionary with game scoring details, or None if game not found

        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        # Get the game
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()

        if not game:
            return None

        # Count picks graded for this game
        picks_graded_result = await self.db.execute(
            select(func.count(Pick.id))
            .where(Pick.game_id == game_id)
            .where(Pick.scored_at.isnot(None))
        )
        picks_graded = picks_graded_result.scalar() or 0

        return {
            "game_id": game.id,
            "first_td_scorer": game.first_td_scorer_player_id,
            "all_td_scorers": game.all_td_scorer_player_ids or [],
            "scored_at": game.scored_at,
            "picks_graded": picks_graded,
            "is_manually_scored": game.is_manually_scored,
        }

    async def grade_game(self, game_id: UUID) -> int:
        """
        Grade all pending picks for a completed game.

        This method:
        1. Identifies all pending picks for the game
        2. Fetches touchdown data from the game
        3. Calculates points for each pick
        4. Updates pick statuses and points
        5. Updates user scores

        Args:
            game_id: UUID of the game to grade

        Returns:
            Number of picks graded

        Requirements: 1.1, 1.3, 1.4, 2.4, 3.4
        """
        start_time = time.time()

        try:
            # Get the game
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()

            if not game:
                self.logger.logger.warning(f"Game not found: game_id={game_id}")
                return 0

            # Get all pending picks for this game
            picks_result = await self.db.execute(
                select(Pick).where(
                    Pick.game_id == game_id, Pick.status == PickResult.PENDING
                )
            )
            picks = picks_result.scalars().all()

            self.logger.log_grading_start(str(game_id), len(picks))

            graded_count = 0
            errors = 0
            first_td_scorer_id = game.first_td_scorer_player_id
            all_td_scorer_ids = game.all_td_scorer_player_ids or []

            for pick in picks:
                try:
                    # Calculate points
                    ftd_points = await self.calculate_ftd_points(
                        pick, first_td_scorer_id
                    )
                    attd_points = await self.calculate_attd_points(
                        pick, all_td_scorer_ids
                    )

                    # Determine status
                    if ftd_points > 0 or attd_points > 0:
                        status = PickResult.WIN
                    else:
                        status = PickResult.LOSS

                    # Update pick
                    await self.update_pick_result(pick, ftd_points, attd_points, status)

                    # Update user score
                    total_points = ftd_points + attd_points
                    is_win = status == PickResult.WIN
                    await self.update_user_score(pick.user_id, total_points, is_win)

                    # Log pick result
                    self.logger.log_pick_result(
                        str(pick.id),
                        str(pick.user_id),
                        status.value,
                        ftd_points,
                        attd_points,
                    )

                    graded_count += 1

                except Exception as pick_error:
                    errors += 1
                    self.logger.logger.error(
                        f"Error grading pick {pick.id}: {str(pick_error)}",
                        exc_info=True,
                    )
                    # Continue with next pick

            # Mark game as scored
            game.scored_at = datetime.now(timezone.utc)

            await self.db.commit()

            duration = time.time() - start_time
            self.logger.log_grading_complete(
                str(game_id), graded_count, duration, errors
            )

            return graded_count

        except Exception as e:
            duration = time.time() - start_time
            self.logger.log_grading_error(str(game_id), e)
            await self.db.rollback()
            raise

    async def grade_picks_for_game(self, game_id: UUID) -> int:
        """
        Grade all picks for a completed game.

        Deprecated: Use grade_game() instead.
        This method is kept for backward compatibility.
        """
        return await self.grade_game(game_id)

    async def manual_grade_game(
        self,
        game_id: UUID,
        first_td_scorer: Optional[UUID],
        all_td_scorers: List[UUID],
        admin_id: UUID,
    ) -> int:
        """
        Manually grade a game with admin-provided touchdown data.

        This method uses the same grading logic as automatic scoring but allows
        an administrator to manually specify the touchdown scorers. This is useful
        for handling edge cases or API failures.

        Args:
            game_id: UUID of the game to grade
            first_td_scorer: UUID of the player who scored the first touchdown (None if no TDs)
            all_td_scorers: List of UUIDs of all players who scored touchdowns
            admin_id: UUID of the administrator performing the manual scoring

        Returns:
            Number of picks graded

        Requirements: 9.1, 9.2, 9.3, 9.4
        """
        # Get the game
        result = await self.db.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()

        if not game:
            return 0

        # Update game with touchdown data
        game.first_td_scorer_player_id = first_td_scorer
        game.all_td_scorer_player_ids = [str(scorer) for scorer in all_td_scorers]
        game.scored_at = datetime.now(timezone.utc)
        game.is_manually_scored = True

        # Get all pending picks for this game
        picks_result = await self.db.execute(
            select(Pick).where(
                Pick.game_id == game_id, Pick.status == PickResult.PENDING
            )
        )
        picks = picks_result.scalars().all()

        graded_count = 0

        for pick in picks:
            # Calculate points using the same logic as automatic scoring
            ftd_points = await self.calculate_ftd_points(pick, first_td_scorer)
            attd_points = await self.calculate_attd_points(pick, all_td_scorers)

            # Determine status
            if ftd_points > 0 or attd_points > 0:
                status = PickResult.WIN
            else:
                status = PickResult.LOSS

            # Update pick
            await self.update_pick_result(pick, ftd_points, attd_points, status)

            # Update user score
            total_points = ftd_points + attd_points
            is_win = status == PickResult.WIN
            await self.update_user_score(pick.user_id, total_points, is_win)

            graded_count += 1

        await self.db.commit()
        return graded_count

    async def override_pick_score(
        self,
        pick_id: UUID,
        status: PickResult,
        ftd_points: int,
        attd_points: int,
        admin_id: UUID,
    ) -> Optional[Pick]:
        """
        Override a pick's score with admin-provided values.

        This method allows an administrator to manually override a pick's score,
        status, and points. This is useful for correcting errors or handling disputes.
        The override is recorded in an audit trail.

        Args:
            pick_id: UUID of the pick to override
            status: New status for the pick (WIN, LOSS, or VOID)
            ftd_points: New FTD points (0 or 3)
            attd_points: New ATTD points (0 or 1)
            admin_id: UUID of the administrator performing the override

        Returns:
            Updated Pick object, or None if pick not found

        Requirements: 10.1, 10.2, 10.3, 10.4
        """
        # Get the pick
        result = await self.db.execute(select(Pick).where(Pick.id == pick_id))
        pick = result.scalar_one_or_none()

        if not pick:
            return None

        # Store old values for user score recalculation
        old_total_points = pick.total_points
        old_status = pick.status

        # Update pick with new values
        pick.status = status
        pick.ftd_points = ftd_points
        pick.attd_points = attd_points
        pick.total_points = ftd_points + attd_points
        pick.is_manual_override = True
        pick.override_by_user_id = admin_id
        pick.override_at = datetime.now(timezone.utc)

        # Recalculate user's total score
        result = await self.db.execute(select(User).where(User.id == pick.user_id))
        user = result.scalar_one_or_none()

        if not user:
            await self.db.commit()
            await self.db.refresh(pick)
            return pick

        # Remove old status effects
        if old_status == PickResult.WIN:
            user.total_score -= old_total_points
            user.total_wins -= 1
        elif old_status == PickResult.LOSS:
            user.total_losses -= 1

        # Apply new status effects
        if status == PickResult.WIN:
            user.total_score += pick.total_points
            user.total_wins += 1
        elif status == PickResult.LOSS:
            user.total_losses += 1

        await self.db.commit()
        await self.db.refresh(pick)
        return pick
