"""NFL data ingestion service"""

import httpx
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import nflreadpy as nfl

from app.core.config import settings
from app.core.logging_config import ScoringLogger
from app.db.models.game import Game, GameStatus
from app.db.models.player import Player

logger = logging.getLogger(__name__)


class NFLDataFetchError(Exception):
    """Exception raised when NFL data fetching fails after retries"""

    pass


class GameResult:
    """Data class for game results"""

    def __init__(
        self,
        game_id: str,
        status: str,
        home_score: Optional[int] = None,
        away_score: Optional[int] = None,
    ):
        self.game_id = game_id
        self.status = status
        self.home_score = home_score
        self.away_score = away_score


class TouchdownData:
    """Data class for touchdown scorer information"""

    def __init__(
        self,
        game_id: str,
        first_td_scorer_id: Optional[str] = None,
        first_td_scorer_name: Optional[str] = None,
        all_td_scorer_ids: Optional[List[str]] = None,
        all_td_scorer_names: Optional[List[str]] = None,
    ):
        self.game_id = game_id
        self.first_td_scorer_id = first_td_scorer_id
        self.first_td_scorer_name = first_td_scorer_name
        self.all_td_scorer_ids = all_td_scorer_ids or []
        self.all_td_scorer_names = all_td_scorer_names or []


class NFLIngestService:
    """Service for ingesting NFL data using nflreadpy"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_url = "https://api.balldontlie.io/v1"
        self.api_key = settings.BALLDONTLIE_API_KEY
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay in seconds for exponential backoff
        self.logger = ScoringLogger("app.services.nfl_ingest")

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff.

        Args:
            func: The function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function call

        Raises:
            NFLDataFetchError: If all retries fail

        Requirements: 13.1, 13.2, 13.3, 13.4
        """
        last_exception = None
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                self.logger.log_api_call(
                    "nflreadpy",
                    func.__name__,
                    {"attempt": attempt + 1, "max_retries": self.max_retries},
                )
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if attempt > 0:
                    self.logger.log_api_success(
                        "nflreadpy",
                        func.__name__,
                        duration,
                        f"Succeeded on attempt {attempt + 1}",
                    )
                else:
                    self.logger.log_api_success("nflreadpy", func.__name__, duration)

                return result

            except Exception as e:
                last_exception = e
                duration = time.time() - start_time

                self.logger.log_api_error(
                    "nflreadpy", func.__name__, duration, e, retry=attempt + 1
                )

                if attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay: 1s, 2s, 4s
                    delay = self.base_delay * (2**attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # All retries exhausted
                    error_msg = f"{func.__name__} failed after {self.max_retries} attempts: {str(e)}"
                    logger.error(error_msg)

                    # Send admin alert
                    from app.services.alert_service import get_alert_service

                    alert_service = get_alert_service()
                    await alert_service.send_api_failure_alert(
                        "nflreadpy", func.__name__, last_exception, self.max_retries
                    )

                    raise NFLDataFetchError(error_msg) from last_exception

        # Should never reach here, but just in case
        raise NFLDataFetchError(
            f"{func.__name__} failed after {self.max_retries} attempts"
        ) from last_exception

    async def fetch_game_results(self, game_id: str) -> Optional[GameResult]:
        """
        Fetch final score and status for a game using nflreadpy.
        Includes retry logic with exponential backoff.

        Args:
            game_id: The external game ID (nflreadpy game_id)

        Returns:
            GameResult object with game status and scores, or None if not found

        Requirements: 1.2, 7.1, 7.2, 7.3, 13.1, 13.2, 13.3, 13.4
        """
        return await self._retry_with_backoff(self._fetch_game_results_impl, game_id)

    async def _fetch_game_results_impl(self, game_id: str) -> Optional[GameResult]:
        """
        Internal implementation of fetch_game_results.
        This method is wrapped by retry logic.
        """
        try:
            logger.info(f"Fetching game results for game_id: {game_id}")

            # Extract season from game_id (format: YYYY_WW_AWAY_HOME)
            season = int(game_id.split("_")[0])

            # Fetch schedules for the season
            schedules_df = nfl.load_schedules(seasons=[season]).to_pandas()

            # Filter to the specific game
            game_data = schedules_df[schedules_df["game_id"] == game_id]

            if game_data.empty:
                logger.warning(f"Game not found: {game_id}")
                return None

            game_row = game_data.iloc[0]

            # Map nflreadpy status to our GameStatus
            # nflreadpy uses: 'scheduled', 'in_progress', 'final', etc.
            status_mapping = {
                "scheduled": GameStatus.SCHEDULED.value,
                "in_progress": GameStatus.IN_PROGRESS.value,
                "final": GameStatus.COMPLETED.value,
                "postponed": GameStatus.SUSPENDED.value,
                "suspended": GameStatus.SUSPENDED.value,
            }

            game_status = status_mapping.get(
                game_row.get("game_type", "scheduled").lower(),
                GameStatus.SCHEDULED.value,
            )

            # Extract scores (may be None if game not completed)
            home_score = (
                int(game_row["home_score"])
                if game_row.get("home_score") is not None
                else None
            )
            away_score = (
                int(game_row["away_score"])
                if game_row.get("away_score") is not None
                else None
            )

            result = GameResult(
                game_id=game_id,
                status=game_status,
                home_score=home_score,
                away_score=away_score,
            )

            logger.info(
                f"Successfully fetched game results for {game_id}: status={game_status}, "
                f"home={home_score}, away={away_score}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error fetching game results for {game_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def fetch_touchdown_scorers(self, game_id: str) -> Optional[TouchdownData]:
        """
        Fetch all touchdown scorers and first TD scorer using nflreadpy play-by-play data.
        Includes retry logic with exponential backoff.

        Args:
            game_id: The external game ID (nflreadpy game_id)

        Returns:
            TouchdownData object with first TD scorer and all TD scorers, or None if not found

        Requirements: 1.2, 7.1, 7.2, 7.3, 13.1, 13.2, 13.3, 13.4
        """
        return await self._retry_with_backoff(
            self._fetch_touchdown_scorers_impl, game_id
        )

    async def _fetch_touchdown_scorers_impl(
        self, game_id: str
    ) -> Optional[TouchdownData]:
        """
        Internal implementation of fetch_touchdown_scorers.
        This method is wrapped by retry logic.
        """
        try:
            logger.info(f"Fetching touchdown scorers for game_id: {game_id}")

            # Extract season from game_id
            season = int(game_id.split("_")[0])

            # Fetch play-by-play data for the season
            logger.info(f"Loading play-by-play data for season {season}...")
            pbp_df = nfl.load_pbp(seasons=[season]).to_pandas()

            # Filter to touchdown plays for this specific game
            game_tds = pbp_df[
                (pbp_df["game_id"] == game_id) & (pbp_df["touchdown"] == 1)
            ].copy()

            if game_tds.empty:
                logger.info(f"No touchdowns found for game {game_id}")
                return TouchdownData(game_id=game_id)

            # Sort by game_seconds_remaining (descending = chronological order)
            game_tds_sorted = game_tds.sort_values(
                "game_seconds_remaining", ascending=False
            )

            # Get first TD scorer
            first_td = game_tds_sorted.iloc[0]
            first_td_scorer_id = (
                str(first_td["td_player_id"])
                if first_td.get("td_player_id") is not None
                else None
            )
            first_td_scorer_name = (
                str(first_td["td_player_name"])
                if first_td.get("td_player_name") is not None
                else None
            )

            # Get all unique TD scorers
            all_td_scorer_ids = (
                game_tds_sorted["td_player_id"].dropna().unique().astype(str).tolist()
            )
            all_td_scorer_names = (
                game_tds_sorted["td_player_name"].dropna().unique().tolist()
            )

            td_data = TouchdownData(
                game_id=game_id,
                first_td_scorer_id=first_td_scorer_id,
                first_td_scorer_name=first_td_scorer_name,
                all_td_scorer_ids=all_td_scorer_ids,
                all_td_scorer_names=all_td_scorer_names,
            )

            logger.info(
                f"Successfully fetched touchdown data for {game_id}: "
                f"first_td={first_td_scorer_name}, total_tds={len(game_tds_sorted)}, "
                f"unique_scorers={len(all_td_scorer_ids)}"
            )

            return td_data

        except Exception as e:
            logger.error(
                f"Error fetching touchdown scorers for {game_id}: {str(e)}",
                exc_info=True,
            )
            raise

    async def update_game_results(
        self, game_id: UUID, result: GameResult, td_data: TouchdownData
    ) -> None:
        """
        Update game with final results and touchdown scorer data.

        Args:
            game_id: Internal UUID of the game
            result: GameResult object with scores and status
            td_data: TouchdownData object with TD scorer information

        Requirements: 8.1, 8.2, 8.3, 8.4
        """
        try:
            logger.info(f"Updating game results for game_id: {game_id}")

            # Fetch the game from database
            stmt = select(Game).where(Game.id == game_id)
            db_result = await self.db.execute(stmt)
            game = db_result.scalar_one_or_none()

            if not game:
                logger.error(f"Game not found in database: {game_id}")
                raise ValueError(f"Game not found: {game_id}")

            # Update game status and scores
            game.status = GameStatus(result.status)
            game.final_score_home = result.home_score
            game.final_score_away = result.away_score

            # Update touchdown scorer data
            if td_data.first_td_scorer_id:
                # Find player by external_id
                first_td_player = await self._get_player_by_external_id(
                    td_data.first_td_scorer_id
                )
                if first_td_player:
                    game.first_td_scorer_player_id = first_td_player.id
                else:
                    logger.warning(
                        f"First TD scorer not found in database: {td_data.first_td_scorer_id} "
                        f"({td_data.first_td_scorer_name})"
                    )

            # Update all TD scorers (convert external IDs to internal UUIDs)
            if td_data.all_td_scorer_ids:
                all_td_player_uuids = []
                for external_id in td_data.all_td_scorer_ids:
                    player = await self._get_player_by_external_id(external_id)
                    if player:
                        all_td_player_uuids.append(str(player.id))
                    else:
                        logger.warning(
                            f"TD scorer not found in database: {external_id}"
                        )

                game.all_td_scorer_player_ids = all_td_player_uuids

            # Mark game as scored
            game.scored_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(game)

            logger.info(
                f"Successfully updated game {game_id}: status={game.status}, "
                f"first_td={game.first_td_scorer_player_id}, "
                f"all_tds={len(game.all_td_scorer_player_ids or [])}"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating game results for {game_id}: {str(e)}")
            raise

    async def validate_game_data(
        self, game_external_id: str, td_data: TouchdownData
    ) -> tuple[bool, List[str]]:
        """
        Validate game data before processing.

        Verifies:
        - Game exists in database
        - All player_ids exist in database
        - Logs validation errors

        Args:
            game_external_id: The external game ID
            td_data: TouchdownData object to validate

        Returns:
            Tuple of (is_valid, error_messages)

        Requirements: 14.1, 14.2, 14.3, 14.4
        """
        errors = []

        try:
            # Verify game exists in database
            stmt = select(Game).where(Game.external_id == game_external_id)
            result = await self.db.execute(stmt)
            game = result.scalar_one_or_none()

            if not game:
                error_msg = f"Game not found in database: {game_external_id}"
                logger.error(error_msg)
                errors.append(error_msg)
                return False, errors

            # Verify first TD scorer exists (if provided)
            if td_data.first_td_scorer_id:
                first_td_player = await self._get_player_by_external_id(
                    td_data.first_td_scorer_id
                )
                if not first_td_player:
                    error_msg = (
                        f"First TD scorer not found in database: "
                        f"{td_data.first_td_scorer_id} ({td_data.first_td_scorer_name})"
                    )
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Verify all TD scorers exist
            if td_data.all_td_scorer_ids:
                for external_id in td_data.all_td_scorer_ids:
                    player = await self._get_player_by_external_id(external_id)
                    if not player:
                        error_msg = f"TD scorer not found in database: {external_id}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            # Return validation result
            is_valid = len(errors) == 0
            if is_valid:
                logger.info(
                    f"Game data validation passed for {game_external_id}: "
                    f"first_td={td_data.first_td_scorer_name}, "
                    f"total_scorers={len(td_data.all_td_scorer_ids)}"
                )
            else:
                logger.warning(
                    f"Game data validation failed for {game_external_id}: "
                    f"{len(errors)} error(s)"
                )

                # Send admin alert for validation errors
                from app.services.alert_service import get_alert_service

                alert_service = get_alert_service()
                await alert_service.send_validation_error_alert(
                    "game", game_external_id, errors
                )

            return is_valid, errors

        except Exception as e:
            error_msg = f"Error validating game data for {game_external_id}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors

    async def _get_player_by_external_id(self, external_id: str) -> Optional[Player]:
        """
        Helper method to get player by external_id.

        Args:
            external_id: The external player ID from nflreadpy

        Returns:
            Player object or None if not found
        """
        stmt = select(Player).where(Player.external_id == external_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def fetch_upcoming_games(
        self, season: int, week: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch upcoming games from nflreadpy for a specific season and week.

        Args:
            season: NFL season year (e.g., 2024)
            week: Week number (1-18 for regular season)

        Returns:
            List of game dictionaries with schedule data

        Requirements: 7.1
        """
        try:
            logger.info(f"Fetching upcoming games for season {season}, week {week}")

            # Fetch schedules for the season
            schedules_df = nfl.load_schedules(seasons=[season]).to_pandas()

            # Filter to the specific week
            week_games = schedules_df[schedules_df["week"] == week]

            if week_games.empty:
                logger.info(f"No games found for season {season}, week {week}")
                return []

            # Convert to list of dictionaries
            games_list = week_games.to_dict("records")

            logger.info(
                f"Successfully fetched {len(games_list)} games for "
                f"season {season}, week {week}"
            )

            return games_list

        except Exception as e:
            logger.error(
                f"Error fetching upcoming games for season {season}, week {week}: {str(e)}",
                exc_info=True,
            )
            raise

    async def sync_games_to_database(self, games_data: List[Dict[str, Any]]) -> int:
        """
        Sync games from nflreadpy to the database.

        Args:
            games_data: List of game dictionaries from nflreadpy

        Returns:
            Number of games synced

        Requirements: 7.1
        """
        try:
            logger.info(f"Syncing {len(games_data)} games to database")

            games_synced = 0

            for game_data in games_data:
                try:
                    game_id = game_data.get("game_id")
                    if not game_id:
                        logger.warning("Game missing game_id, skipping")
                        continue

                    # Check if game already exists
                    stmt = select(Game).where(Game.external_id == game_id)
                    result = await self.db.execute(stmt)
                    existing_game = result.scalar_one_or_none()

                    if existing_game:
                        # Update existing game
                        logger.debug(f"Game {game_id} already exists, updating")
                        # TODO: Update game fields if needed
                        continue

                    # TODO: Create new game
                    # This would require mapping nflreadpy data to our Game model
                    # and looking up team IDs, etc.
                    logger.debug(f"Would create new game: {game_id}")
                    games_synced += 1

                except Exception as game_error:
                    logger.error(
                        f"Error syncing game {game_data.get('game_id')}: {str(game_error)}"
                    )
                    continue

            await self.db.commit()

            logger.info(f"Successfully synced {games_synced} games to database")
            return games_synced

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error syncing games to database: {str(e)}", exc_info=True)
            raise

    # Legacy methods (kept for backward compatibility)
    async def fetch_games(
        self, season: Optional[int] = None, week: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch games from BallDontLie API (legacy method)"""
        # TODO: Implement actual API call
        # This is a placeholder
        async with httpx.AsyncClient() as client:
            params = {}
            if season:
                params["seasons[]"] = season
            if week:
                params["per_page"] = 100  # Adjust as needed

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await client.get(
                f"{self.base_url}/games", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def fetch_teams(self) -> Dict[str, Any]:
        """Fetch teams from BallDontLie API (legacy method)"""
        # TODO: Implement actual API call
        async with httpx.AsyncClient() as client:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await client.get(f"{self.base_url}/teams", headers=headers)
            response.raise_for_status()
            return response.json()

    async def fetch_players(self, team_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch players from BallDontLie API (legacy method)"""
        # TODO: Implement actual API call
        async with httpx.AsyncClient() as client:
            params = {}
            if team_id:
                params["team_ids[]"] = team_id

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await client.get(
                f"{self.base_url}/players", params=params, headers=headers
            )
            response.raise_for_status()
            return response.json()
