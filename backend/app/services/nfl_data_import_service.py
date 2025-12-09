"""NFL Data Import Service - Clean implementation for admin data import feature"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import nflreadpy as nfl

from app.db.models.game import Game, GameStatus, GameType
from app.db.models.team import Team
from app.db.models.player import Player
from app.services.import_progress_tracker import ImportProgressTracker, ImportProgress

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for an import operation"""

    teams_created: int = 0
    players_created: int = 0
    games_created: int = 0
    games_updated: int = 0
    games_graded: int = 0
    total_games: int = 0


class NFLDataImportService:
    """
    Service for importing NFL data from nflreadpy.

    This is a clean, new implementation separate from the legacy command-line scripts.
    Designed to be used by the admin data import feature.

    Requirements: 7.1, 7.2, 7.3
    """

    def __init__(
        self, db: AsyncSession, progress_tracker: Optional[ImportProgressTracker] = None
    ):
        """
        Initialize the import service.

        Args:
            db: Async database session
            progress_tracker: Optional progress tracker for real-time updates
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._stats: Optional[ImportStats] = None  # Track stats during import
        self.progress_tracker = progress_tracker or ImportProgressTracker()

    async def get_or_create_team(
        self, team_abbr: str, team_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Team, bool]:
        """
        Get or create a team by abbreviation.

        Args:
            team_abbr: Team abbreviation (e.g., 'KC', 'SF')
            team_data: Optional dictionary with team details

        Returns:
            Tuple of (Team, was_created)

        Requirements: 7.2
        """
        try:
            # Try to find existing team by abbreviation
            stmt = select(Team).where(Team.abbreviation == team_abbr)
            result = await self.db.execute(stmt)
            team = result.scalar_one_or_none()

            if team:
                return team, False

            # Create new team
            # Use team_abbr as external_id if no data provided
            external_id = team_abbr
            name = team_abbr
            city = team_abbr

            if team_data:
                external_id = team_data.get("team_id", team_abbr)
                name = team_data.get("team_name", team_abbr)
                city = team_data.get("team_city", team_abbr)

            team = Team(
                external_id=external_id,
                name=name,
                abbreviation=team_abbr,
                city=city,
            )

            self.db.add(team)
            await self.db.flush()  # Flush to get the ID without committing

            # Track in stats if available
            if self._stats:
                self._stats.teams_created += 1

            self.logger.info(f"Created team: {team_abbr} (ID: {team.id})")
            return team, True

        except Exception as e:
            self.logger.error(f"Error getting/creating team {team_abbr}: {str(e)}")
            raise

    async def get_or_create_player(
        self,
        player_id: str,
        player_name: str,
        position: Optional[str],
        team: Team,
    ) -> Tuple[Player, bool]:
        """
        Get or create a player.

        Args:
            player_id: External player ID from nflreadpy
            player_name: Player's name
            position: Player's position (QB, RB, WR, etc.)
            team: Team the player belongs to

        Returns:
            Tuple of (Player, was_created)

        Requirements: 7.2
        """
        try:
            # Try to find existing player by external_id
            stmt = select(Player).where(Player.external_id == player_id)
            result = await self.db.execute(stmt)
            player = result.scalar_one_or_none()

            if player:
                # Update team if changed
                if player.team_id != team.id:
                    player.team_id = team.id
                    self.logger.info(
                        f"Updated player {player_name} team to {team.abbreviation}"
                    )
                return player, False

            # Create new player
            player = Player(
                external_id=player_id,
                name=player_name,
                team_id=team.id,
                position=position,
                is_active=True,
            )

            self.db.add(player)
            await self.db.flush()  # Flush to get the ID without committing

            # Track in stats if available
            if self._stats:
                self._stats.players_created += 1

            self.logger.info(
                f"Created player: {player_name} ({position}) - {team.abbreviation} (ID: {player.id})"
            )
            return player, True

        except Exception as e:
            self.logger.error(
                f"Error getting/creating player {player_name} ({player_id}): {str(e)}"
            )
            raise

    async def fetch_schedule(
        self, season: int, weeks: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch NFL schedule from nflreadpy with retry logic.

        Args:
            season: NFL season year (e.g., 2024)
            weeks: Optional list of week numbers to fetch. If None, fetches all weeks.

        Returns:
            List of game dictionaries from nflreadpy

        Raises:
            ValueError: If season or weeks are invalid
            ConnectionError: If network request fails after retries
            RuntimeError: If data fetching fails for other reasons

        Requirements: 2.1, 2.2, 2.5
        """
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Fetching schedule for season {season}, weeks: {weeks or 'all'} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                # Fetch schedules for the season using nflreadpy
                schedules_df = nfl.load_schedules(seasons=[season]).to_pandas()

                # Filter by weeks if specified
                if weeks:
                    schedules_df = schedules_df[schedules_df["week"].isin(weeks)]

                if schedules_df.empty:
                    self.logger.warning(
                        f"No games found for season {season}, weeks: {weeks or 'all'}"
                    )
                    return []

                # Convert to list of dictionaries
                games_list = schedules_df.to_dict("records")

                self.logger.info(
                    f"Successfully fetched {len(games_list)} games for season {season}"
                )

                return games_list

            except (ConnectionError, TimeoutError) as e:
                # Network-related errors - retry
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Network error fetching schedule (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    import asyncio

                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    error_msg = f"Failed to fetch schedule after {max_retries} attempts: {str(e)}"
                    self.logger.error(error_msg, exc_info=True)
                    raise ConnectionError(error_msg) from e

            except ValueError as e:
                # Invalid input - don't retry
                error_msg = f"Invalid season or weeks parameter: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg) from e

            except Exception as e:
                # Other errors - log and raise
                error_msg = f"Unexpected error fetching schedule for season {season}, weeks {weeks}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e

        # Should never reach here, but just in case
        raise RuntimeError(f"Failed to fetch schedule after {max_retries} attempts")

    def _determine_game_status(self, game_data: Dict[str, Any]) -> GameStatus:
        """
        Determine game status from nflreadpy data.

        Args:
            game_data: Game dictionary from nflreadpy

        Returns:
            GameStatus enum value
        """
        # nflreadpy uses game_type field which can be 'REG', 'POST', etc.
        # and has separate status indicators

        # Check if game has started/completed based on scores
        home_score = game_data.get("home_score")
        away_score = game_data.get("away_score")

        # If both scores are present and not None, game is likely completed
        if home_score is not None and away_score is not None:
            return GameStatus.COMPLETED

        # Check gameday - if it's in the past, might be completed
        gameday = game_data.get("gameday")
        if gameday:
            try:
                game_date = datetime.fromisoformat(str(gameday))
                if game_date < datetime.now(timezone.utc):
                    # Game date has passed
                    if home_score is None and away_score is None:
                        # No scores yet, might be scheduled or in progress
                        return GameStatus.SCHEDULED
                    return GameStatus.COMPLETED
            except (ValueError, TypeError):
                pass

        # Default to scheduled
        return GameStatus.SCHEDULED

    def _determine_game_type(self, game_data: Dict[str, Any]) -> GameType:
        """
        Determine game type from nflreadpy data.

        Args:
            game_data: Game dictionary from nflreadpy

        Returns:
            GameType enum value
        """
        # Check for special game types based on day of week and time
        # nflreadpy provides 'gameday' which is the date

        # For now, default to Sunday main
        # TODO: Enhance this logic based on actual game time
        return GameType.SUNDAY_MAIN

    async def create_or_update_game(
        self, game_data: Dict[str, Any]
    ) -> Tuple[Game, bool]:
        """
        Create or update a game from nflreadpy data.

        Args:
            game_data: Game dictionary from nflreadpy

        Returns:
            Tuple of (Game, was_created)

        Requirements: 1.3, 8.2, 8.3, 8.5
        """
        try:
            game_id = game_data.get("game_id")
            if not game_id:
                raise ValueError("Game data missing game_id")

            # Check if game already exists
            stmt = select(Game).where(Game.external_id == game_id)
            result = await self.db.execute(stmt)
            existing_game = result.scalar_one_or_none()

            # Get or create teams
            home_team_abbr = game_data.get("home_team")
            away_team_abbr = game_data.get("away_team")

            if not home_team_abbr or not away_team_abbr:
                raise ValueError(f"Game {game_id} missing team information")

            home_team, _ = await self.get_or_create_team(home_team_abbr)
            away_team, _ = await self.get_or_create_team(away_team_abbr)

            # Parse game date
            gameday = game_data.get("gameday")
            if gameday:
                try:
                    game_date = datetime.fromisoformat(str(gameday))
                    if game_date.tzinfo is None:
                        game_date = game_date.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    game_date = datetime.now(timezone.utc)
            else:
                game_date = datetime.now(timezone.utc)

            # Determine game status
            game_status = self._determine_game_status(game_data)

            # Extract scores (handle NaN values from pandas)
            home_score = game_data.get("home_score")
            away_score = game_data.get("away_score")

            # Convert NaN to None for database compatibility
            import math

            if home_score is not None and (
                isinstance(home_score, float) and math.isnan(home_score)
            ):
                home_score = None
            if away_score is not None and (
                isinstance(away_score, float) and math.isnan(away_score)
            ):
                away_score = None

            if existing_game:
                # Update existing game
                existing_game.status = game_status
                existing_game.final_score_home = home_score
                existing_game.final_score_away = away_score
                existing_game.home_team_id = home_team.id
                existing_game.away_team_id = away_team.id
                existing_game.game_date = game_date
                existing_game.kickoff_time = game_date

                await self.db.flush()

                self.logger.info(f"Updated game: {game_id}")
                return existing_game, False

            # Create new game
            season = game_data.get("season", datetime.now().year)
            week = game_data.get("week", 1)
            game_type = self._determine_game_type(game_data)

            new_game = Game(
                external_id=game_id,
                season_year=season,
                week_number=week,
                game_type=game_type,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                game_date=game_date,
                kickoff_time=game_date,
                status=game_status,
                final_score_home=home_score,
                final_score_away=away_score,
            )

            self.db.add(new_game)
            await self.db.flush()

            self.logger.info(
                f"Created game: {game_id} - {away_team_abbr} @ {home_team_abbr}"
            )
            return new_game, True

        except Exception as e:
            self.logger.error(
                f"Error creating/updating game {game_data.get('game_id')}: {str(e)}",
                exc_info=True,
            )
            raise

    async def grade_game(self, game: Game) -> bool:
        """
        Grade a completed game by fetching touchdown scorer data with retry logic.

        Args:
            game: Game object to grade

        Returns:
            True if grading succeeded, False otherwise

        Requirements: 3.2, 3.3, 3.4
        """
        max_retries = 2
        retry_delay = 3  # seconds

        for attempt in range(max_retries):
            try:
                # Only grade completed games
                if game.status != GameStatus.COMPLETED:
                    self.logger.debug(
                        f"Skipping grading for non-completed game: {game.external_id}"
                    )
                    return False

                self.logger.info(
                    f"Grading game: {game.external_id} (attempt {attempt + 1}/{max_retries})"
                )

                # Extract season from game_id (format: YYYY_WW_AWAY_HOME)
                season = game.season_year

                # Fetch play-by-play data for the season
                pbp_df = nfl.load_pbp(seasons=[season]).to_pandas()

                # Filter to touchdown plays for this specific game
                game_tds = pbp_df[
                    (pbp_df["game_id"] == game.external_id) & (pbp_df["touchdown"] == 1)
                ].copy()

                if game_tds.empty:
                    self.logger.info(f"No touchdowns found for game {game.external_id}")
                    # Mark as graded even with no TDs
                    game.scored_at = datetime.now(timezone.utc)
                    await self.db.flush()
                    return True

                # Sort by game_seconds_remaining (descending = chronological order)
                game_tds_sorted = game_tds.sort_values(
                    "game_seconds_remaining", ascending=False
                )

                # Get first TD scorer
                first_td = game_tds_sorted.iloc[0]
                first_td_scorer_id = first_td.get("td_player_id")
                first_td_scorer_name = first_td.get("td_player_name")

                # Get all unique TD scorers
                all_td_scorer_ids = (
                    game_tds_sorted["td_player_id"]
                    .dropna()
                    .unique()
                    .astype(str)
                    .tolist()
                )

                # Process first TD scorer
                if first_td_scorer_id and first_td_scorer_name:
                    # Get team for the player (use home team as default, should be refined)
                    # In a real scenario, we'd need to determine which team the player is on
                    home_team_stmt = select(Team).where(Team.id == game.home_team_id)
                    home_team_result = await self.db.execute(home_team_stmt)
                    home_team = home_team_result.scalar_one()

                    # Get or create player
                    first_td_player, _ = await self.get_or_create_player(
                        player_id=str(first_td_scorer_id),
                        player_name=str(first_td_scorer_name),
                        position=first_td.get("td_player_position"),
                        team=home_team,
                    )

                    game.first_td_scorer_player_id = first_td_player.id

                # Process all TD scorers
                all_td_player_uuids = []
                for td_scorer_id in all_td_scorer_ids:
                    # Find the TD play for this scorer to get their name
                    td_play = game_tds_sorted[
                        game_tds_sorted["td_player_id"].astype(str) == str(td_scorer_id)
                    ].iloc[0]

                    td_scorer_name = td_play.get("td_player_name")
                    if not td_scorer_name:
                        continue

                    # Get team (simplified - use home team)
                    home_team_stmt = select(Team).where(Team.id == game.home_team_id)
                    home_team_result = await self.db.execute(home_team_stmt)
                    home_team = home_team_result.scalar_one()

                    # Get or create player
                    td_player, _ = await self.get_or_create_player(
                        player_id=str(td_scorer_id),
                        player_name=str(td_scorer_name),
                        position=td_play.get("td_player_position"),
                        team=home_team,
                    )

                    all_td_player_uuids.append(str(td_player.id))

                # Update game with TD scorer data
                game.all_td_scorer_player_ids = all_td_player_uuids
                game.scored_at = datetime.now(timezone.utc)

                await self.db.flush()

                self.logger.info(
                    f"Successfully graded game {game.external_id}: "
                    f"first_td={first_td_scorer_name}, total_scorers={len(all_td_player_uuids)}"
                )

                return True

            except (ConnectionError, TimeoutError) as e:
                # Network-related errors - retry
                if attempt < max_retries - 1:
                    self.logger.warning(
                        f"Network error grading game {game.external_id} "
                        f"(attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    import asyncio

                    await asyncio.sleep(retry_delay)
                else:
                    self.logger.error(
                        f"Failed to grade game {game.external_id} after {max_retries} attempts: {str(e)}",
                        exc_info=True,
                    )
                    # Don't raise - allow import to continue
                    return False

            except Exception as e:
                self.logger.error(
                    f"Error grading game {game.external_id}: {str(e)}", exc_info=True
                )
                # Don't raise - allow import to continue
                return False

        # Should never reach here, but just in case
        return False

    async def import_season_data(
        self,
        season: int,
        weeks: Optional[List[int]] = None,
        grade_games: bool = False,
        job_id: Optional[str] = None,
    ) -> ImportStats:
        """
        Main import orchestration method.

        Imports NFL season data including games, teams, and optionally grades completed games.

        Args:
            season: NFL season year (e.g., 2024)
            weeks: Optional list of week numbers. If None, imports all weeks.
            grade_games: Whether to fetch touchdown data for completed games
            job_id: Optional import job ID for progress tracking

        Returns:
            ImportStats object with counts of created/updated records

        Requirements: 1.4, 1.5, 3.5, 4.3, 4.2, 4.3, 4.4
        """
        stats = ImportStats()
        # Set stats reference for tracking in helper methods
        self._stats = stats

        try:
            self.logger.info(
                f"Starting import for season {season}, weeks: {weeks or 'all'}, "
                f"grade_games: {grade_games}"
            )

            # Initialize progress tracking
            if job_id:
                progress = ImportProgress(
                    status="running",
                    current_step="Fetching schedule from nflreadpy",
                    games_processed=0,
                    total_games=0,
                )
                await self.progress_tracker.update_progress(job_id, progress)

            # Fetch schedule
            games_data = await self.fetch_schedule(season, weeks)
            stats.total_games = len(games_data)

            self.logger.info(f"Found {stats.total_games} games to import")

            # Update progress with total games
            if job_id:
                progress.total_games = stats.total_games
                progress.current_step = f"Processing {stats.total_games} games"
                await self.progress_tracker.update_progress(job_id, progress)

            # Process games sequentially
            for idx, game_data in enumerate(games_data, 1):
                try:
                    # Update progress with current step
                    if job_id:
                        game_id = game_data.get("game_id", "unknown")
                        progress.current_step = (
                            f"Processing game {idx}/{stats.total_games}: {game_id}"
                        )
                        progress.games_processed = idx - 1  # Not yet processed
                        await self.progress_tracker.update_progress(job_id, progress)

                    # Create or update game
                    game, was_created = await self.create_or_update_game(game_data)

                    if was_created:
                        stats.games_created += 1
                    else:
                        stats.games_updated += 1

                    # Grade game if requested and game is completed
                    if grade_games and game.status == GameStatus.COMPLETED:
                        if job_id:
                            progress.current_step = f"Grading game {idx}/{stats.total_games}: {game.external_id}"
                            await self.progress_tracker.update_progress(
                                job_id, progress
                            )

                        graded = await self.grade_game(game)
                        if graded:
                            stats.games_graded += 1

                    # Commit after each game to ensure progress is saved
                    await self.db.commit()

                    # Update progress after successful processing
                    if job_id:
                        progress.games_processed = idx
                        progress.teams_created = stats.teams_created
                        progress.players_created = stats.players_created
                        progress.games_created = stats.games_created
                        progress.games_updated = stats.games_updated
                        progress.games_graded = stats.games_graded
                        await self.progress_tracker.update_progress(job_id, progress)

                    self.logger.info(
                        f"Processed game {idx}/{stats.total_games}: {game.external_id}"
                    )

                except Exception as game_error:
                    # Log error but continue with other games (error isolation)
                    error_msg = f"Error processing game {game_data.get('game_id')}: {str(game_error)}"
                    self.logger.error(error_msg, exc_info=True)

                    # Update progress with error
                    if job_id:
                        if error_msg not in progress.errors:
                            progress.errors.append(error_msg)
                        await self.progress_tracker.update_progress(job_id, progress)

                    # Rollback this game's transaction
                    await self.db.rollback()
                    # Continue with next game

            self.logger.info(
                f"Import complete: {stats.teams_created} teams created, "
                f"{stats.players_created} players created, "
                f"{stats.games_created} games created, "
                f"{stats.games_updated} games updated, "
                f"{stats.games_graded} games graded"
            )

            # Mark as complete in progress tracker
            if job_id:
                await self.progress_tracker.mark_complete(
                    job_id,
                    {
                        "teams_created": stats.teams_created,
                        "players_created": stats.players_created,
                        "games_created": stats.games_created,
                        "games_updated": stats.games_updated,
                        "games_graded": stats.games_graded,
                        "total_games": stats.total_games,
                    },
                )

            return stats

        except Exception as e:
            error_msg = f"Error during import for season {season}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)

            # Mark as failed in progress tracker
            if job_id:
                await self.progress_tracker.mark_failed(job_id, str(e))

            await self.db.rollback()
            raise
        finally:
            # Clean up stats reference
            self._stats = None
