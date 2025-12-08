"""Scheduled jobs for scoring system using APScheduler"""

import logging
import time
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from pytz import timezone

from app.db.session import AsyncSessionLocal
from app.services.nfl_ingest import NFLIngestService
from app.services.scoring import ScoringService
from app.services.alert_service import get_alert_service
from app.core.logging_config import ScoringLogger
from app.db.models.game import Game, GameStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)
scoring_logger = ScoringLogger("app.worker.scheduler")

# Configure timezone
EST = timezone("America/New_York")

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """
    Get or create the scheduler instance.

    Returns:
        AsyncIOScheduler instance configured with timezone support
    """
    global scheduler

    if scheduler is None:
        scheduler = AsyncIOScheduler(timezone=EST)

        # Add event listeners for monitoring
        scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
        scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)

        logger.info("Scheduler created with timezone: America/New_York")

    return scheduler


def job_executed_listener(event):
    """
    Listener for successful job executions.
    Logs job completion for monitoring.

    Requirements: 7.4
    """
    job_id = event.job_id
    scheduled_run_time = event.scheduled_run_time
    run_time = event.retval if hasattr(event, "retval") else None

    logger.info(
        f"Job '{job_id}' executed successfully at {scheduled_run_time}. "
        f"Return value: {run_time}"
    )


def job_error_listener(event):
    """
    Listener for job execution errors.
    Logs errors with stack traces for monitoring.

    Requirements: 7.5
    """
    job_id = event.job_id
    scheduled_run_time = event.scheduled_run_time
    exception = event.exception
    traceback = event.traceback

    logger.error(
        f"Job '{job_id}' failed at {scheduled_run_time}. "
        f"Exception: {exception}\n"
        f"Traceback: {traceback}"
    )

    # TODO: Send admin alert
    # await send_admin_alert(f"Scheduled job '{job_id}' failed", str(exception))


def configure_jobs(scheduler: AsyncIOScheduler):
    """
    Configure all scheduled jobs.

    Jobs configured:
    - fetch_upcoming_games: Daily at 1:59 AM EST
    - grade_early_games: Sundays at 4:30 PM EST
    - grade_late_games: Sundays at 8:30 PM EST

    Args:
        scheduler: The AsyncIOScheduler instance

    Requirements: 7.1, 7.2, 7.3
    """
    # Job 1: Fetch upcoming games daily at 1:59 AM EST
    scheduler.add_job(
        fetch_upcoming_games_job,
        CronTrigger(hour=1, minute=59, timezone=EST),
        id="fetch_upcoming_games",
        name="Fetch Upcoming Games",
        replace_existing=True,
        max_instances=1,  # Prevent concurrent runs
    )
    logger.info("Scheduled job: fetch_upcoming_games (daily at 1:59 AM EST)")

    # Job 2: Grade early games on Sundays at 4:30 PM EST
    scheduler.add_job(
        grade_completed_games_job,
        CronTrigger(day_of_week="sun", hour=16, minute=30, timezone=EST),
        id="grade_early_games",
        name="Grade Early Games",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("Scheduled job: grade_early_games (Sundays at 4:30 PM EST)")

    # Job 3: Grade late games on Sundays at 8:30 PM EST
    scheduler.add_job(
        grade_completed_games_job,
        CronTrigger(day_of_week="sun", hour=20, minute=30, timezone=EST),
        id="grade_late_games",
        name="Grade Late Games",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("Scheduled job: grade_late_games (Sundays at 8:30 PM EST)")

    logger.info("All scheduled jobs configured successfully")


async def fetch_upcoming_games_job():
    """
    Scheduled job to fetch upcoming games from nflreadpy.
    Runs daily at 1:59 AM EST.

    This job:
    1. Determines current NFL season and week
    2. Fetches upcoming games from nflreadpy
    3. Updates database with game data

    Requirements: 7.1
    """
    job_start = time.time()
    scoring_logger.log_job_start("fetch_upcoming_games")

    try:
        async with AsyncSessionLocal() as db:
            nfl_service = NFLIngestService(db)

            # Determine current NFL season and week
            # For now, using current year as season
            # In production, this would be more sophisticated
            current_date = datetime.now(EST)
            season = current_date.year

            # Simple week calculation (would need refinement for actual NFL calendar)
            # This is a placeholder - actual implementation would need to determine
            # the current NFL week based on the season start date
            week = 1  # Default to week 1 for now

            logger.info(f"Fetching games for season {season}, week {week}")

            # Fetch upcoming games from nflreadpy
            games_data = await nfl_service.fetch_upcoming_games(season, week)

            # Sync games to database
            games_synced = await nfl_service.sync_games_to_database(games_data)

            duration = time.time() - job_start
            results = {
                "status": "success",
                "games_fetched": len(games_data),
                "games_synced": games_synced,
            }

            scoring_logger.log_job_complete("fetch_upcoming_games", duration, results)

            return {**results, "duration_seconds": duration}

    except Exception as e:
        duration = time.time() - job_start
        scoring_logger.log_job_error("fetch_upcoming_games", duration, e)

        # Send admin alert
        alert_service = get_alert_service()
        await alert_service.send_job_failure_alert("fetch_upcoming_games", e, duration)

        # Don't re-raise - let scheduler continue
        return {"status": "error", "error": str(e), "duration_seconds": duration}


async def grade_completed_games_job():
    """
    Scheduled job to grade completed games.
    Runs on Sundays at 4:30 PM and 8:30 PM EST.

    This job:
    1. Finds games with status=COMPLETED that haven't been scored
    2. Fetches touchdown data from nflreadpy
    3. Validates the data
    4. Calls ScoringService.grade_game for each game

    Requirements: 7.2, 7.3
    """
    job_start = time.time()
    scoring_logger.log_job_start("grade_completed_games")

    try:
        async with AsyncSessionLocal() as db:
            nfl_service = NFLIngestService(db)
            scoring_service = ScoringService(db)

            # Find completed games that haven't been scored yet
            stmt = select(Game).where(
                Game.status == GameStatus.COMPLETED, Game.scored_at.is_(None)
            )
            result = await db.execute(stmt)
            games_to_score = result.scalars().all()

            logger.info(f"Found {len(games_to_score)} completed games to score")

            games_graded = 0
            games_failed = 0
            total_picks_graded = 0

            for game in games_to_score:
                try:
                    logger.info(f"Processing game {game.external_id}")

                    # Fetch game results
                    game_result = await nfl_service.fetch_game_results(game.external_id)
                    if not game_result:
                        logger.warning(
                            f"Could not fetch results for game {game.external_id}"
                        )
                        games_failed += 1
                        continue

                    # Fetch touchdown data
                    td_data = await nfl_service.fetch_touchdown_scorers(
                        game.external_id
                    )
                    if not td_data:
                        logger.warning(
                            f"Could not fetch TD data for game {game.external_id}"
                        )
                        games_failed += 1
                        continue

                    # Validate data
                    is_valid, errors = await nfl_service.validate_game_data(
                        game.external_id, td_data
                    )

                    if not is_valid:
                        scoring_logger.log_validation_error(
                            "game", game.external_id, errors
                        )
                        games_failed += 1
                        continue

                    # Update game with results
                    await nfl_service.update_game_results(game.id, game_result, td_data)

                    # Grade all picks for this game
                    picks_graded = await scoring_service.grade_game(game.id)

                    logger.info(
                        f"Successfully graded game {game.external_id}: "
                        f"{picks_graded} picks graded"
                    )

                    games_graded += 1
                    total_picks_graded += picks_graded

                except Exception as game_error:
                    logger.error(
                        f"Error grading game {game.external_id}: {str(game_error)}",
                        exc_info=True,
                    )
                    games_failed += 1
                    # Continue with next game - don't let one failure stop the job

            duration = time.time() - job_start
            results = {
                "status": "success",
                "games_graded": games_graded,
                "games_failed": games_failed,
                "total_picks_graded": total_picks_graded,
            }

            scoring_logger.log_job_complete("grade_completed_games", duration, results)

            return {**results, "duration_seconds": duration}

    except Exception as e:
        duration = time.time() - job_start
        scoring_logger.log_job_error("grade_completed_games", duration, e)

        # Send admin alert
        alert_service = get_alert_service()
        await alert_service.send_job_failure_alert("grade_completed_games", e, duration)

        # Don't re-raise - let scheduler continue
        return {"status": "error", "error": str(e), "duration_seconds": duration}
