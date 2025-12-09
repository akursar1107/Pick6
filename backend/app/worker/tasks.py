"""Background tasks for data ingestion"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from app.services.nfl_ingest import NFLIngestService
from app.services.nfl_data_import_service import NFLDataImportService
from app.services.import_progress_tracker import ImportProgressTracker
from app.db.session import AsyncSessionLocal
from app.services.game_service import GameService
from app.db.models.import_job import ImportJob, ImportJobStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def sync_nfl_schedule():
    """Sync NFL schedule from BallDontLie API"""
    ingest_service = NFLIngestService()

    # Get current season (approximate)
    current_year = datetime.now().year
    current_month = datetime.now().month

    # NFL season typically runs from September to February
    if current_month >= 9:
        season = current_year
    else:
        season = current_year - 1

    try:
        games_data = await ingest_service.fetch_games(season=season)
        # TODO: Process and store games in database
        print(f"Fetched {len(games_data.get('data', []))} games for season {season}")
    except Exception as e:
        print(f"Error syncing NFL schedule: {e}")


async def sync_nfl_teams():
    """Sync NFL teams from BallDontLie API"""
    ingest_service = NFLIngestService()

    try:
        teams_data = await ingest_service.fetch_teams()
        # TODO: Process and store teams in database
        print(f"Fetched {len(teams_data.get('data', []))} teams")
    except Exception as e:
        print(f"Error syncing NFL teams: {e}")


async def sync_nfl_players():
    """Sync NFL players from BallDontLie API"""
    ingest_service = NFLIngestService()

    try:
        players_data = await ingest_service.fetch_players()
        # TODO: Process and store players in database
        print(f"Fetched {len(players_data.get('data', []))} players")
    except Exception as e:
        print(f"Error syncing NFL players: {e}")


# Example: Run sync tasks periodically
# This would typically be set up with Celery Beat or similar
if __name__ == "__main__":
    asyncio.run(sync_nfl_schedule())


async def execute_import_job(job_id: UUID) -> dict:
    """
    Background task to execute an NFL data import job.

    This task:
    1. Fetches the ImportJob from database
    2. Checks for concurrent imports (prevention)
    3. Updates job status to RUNNING
    4. Calls NFLDataImportService.import_season_data()
    5. Updates job status and statistics on completion/failure
    6. Handles timeouts and errors gracefully

    Args:
        job_id: UUID of the ImportJob to execute

    Returns:
        Dictionary with execution results

    Requirements: 5.1, 5.2, 5.3, 5.5
    """
    logger.info(f"Starting import job execution: {job_id}")

    async with AsyncSessionLocal() as db:
        try:
            # Fetch the import job
            stmt = select(ImportJob).where(ImportJob.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if not job:
                error_msg = f"Import job {job_id} not found"
                logger.error(error_msg)
                return {"status": "error", "error": error_msg}

            # Check for concurrent imports for the same season (Requirement 5.5)
            concurrent_check_stmt = select(ImportJob).where(
                ImportJob.season == job.season,
                ImportJob.status == ImportJobStatus.RUNNING,
                ImportJob.id != job_id,
            )
            concurrent_result = await db.execute(concurrent_check_stmt)
            concurrent_job = concurrent_result.scalar_one_or_none()

            if concurrent_job:
                error_msg = (
                    f"Another import job is already running for season {job.season}"
                )
                logger.warning(error_msg)

                # Mark this job as failed
                job.status = ImportJobStatus.FAILED
                job.errors = [error_msg]
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

                return {"status": "error", "error": error_msg}

            # Update job status to RUNNING
            job.status = ImportJobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(
                f"Import job {job_id} started: season={job.season}, "
                f"weeks={job.weeks or 'all'}, grade_games={job.grade_games}"
            )

            # Initialize import service with progress tracker
            progress_tracker = ImportProgressTracker()
            import_service = NFLDataImportService(db, progress_tracker)

            # Execute the import
            stats = await import_service.import_season_data(
                season=job.season,
                weeks=job.weeks,
                grade_games=job.grade_games,
                job_id=str(job_id),
            )

            # Update job with final statistics
            job.status = ImportJobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.teams_created = stats.teams_created
            job.players_created = stats.players_created
            job.games_created = stats.games_created
            job.games_updated = stats.games_updated
            job.games_graded = stats.games_graded
            job.total_games = stats.total_games
            job.games_processed = stats.total_games

            await db.commit()

            logger.info(
                f"Import job {job_id} completed successfully: "
                f"teams={stats.teams_created}, players={stats.players_created}, "
                f"games_created={stats.games_created}, games_updated={stats.games_updated}, "
                f"games_graded={stats.games_graded}"
            )

            return {
                "status": "success",
                "job_id": str(job_id),
                "stats": {
                    "teams_created": stats.teams_created,
                    "players_created": stats.players_created,
                    "games_created": stats.games_created,
                    "games_updated": stats.games_updated,
                    "games_graded": stats.games_graded,
                    "total_games": stats.total_games,
                },
            }

        except asyncio.TimeoutError:
            # Handle timeout
            error_msg = f"Import job {job_id} timed out after 30 minutes"
            logger.error(error_msg)

            # Update job status with rollback
            try:
                await db.rollback()
                job.status = ImportJobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                if not job.errors:
                    job.errors = []
                job.errors.append(error_msg)
                await db.commit()

                # Mark as failed in progress tracker
                progress_tracker = ImportProgressTracker()
                await progress_tracker.mark_failed(str(job_id), error_msg)
            except Exception as update_error:
                logger.error(
                    f"Failed to update job status after timeout: {str(update_error)}"
                )

            return {"status": "error", "error": error_msg}

        except ConnectionError as e:
            # Handle network failures
            error_msg = f"Network error during import job {job_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Update job status with rollback
            try:
                await db.rollback()
                job.status = ImportJobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                if not job.errors:
                    job.errors = []
                job.errors.append(
                    "Failed to fetch data from NFL API. Please check your network connection and try again."
                )
                await db.commit()

                # Mark as failed in progress tracker
                progress_tracker = ImportProgressTracker()
                await progress_tracker.mark_failed(str(job_id), str(e))
            except Exception as update_error:
                logger.error(
                    f"Failed to update job status after network error: {str(update_error)}"
                )

            return {"status": "error", "error": error_msg}

        except ValueError as e:
            # Handle validation errors
            error_msg = f"Invalid parameters for import job {job_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Update job status with rollback
            try:
                await db.rollback()
                job.status = ImportJobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                if not job.errors:
                    job.errors = []
                job.errors.append(f"Invalid import parameters: {str(e)}")
                await db.commit()

                # Mark as failed in progress tracker
                progress_tracker = ImportProgressTracker()
                await progress_tracker.mark_failed(str(job_id), str(e))
            except Exception as update_error:
                logger.error(
                    f"Failed to update job status after validation error: {str(update_error)}"
                )

            return {"status": "error", "error": error_msg}

        except Exception as e:
            # Handle general errors
            error_msg = f"Import job {job_id} failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Update job status with rollback
            try:
                await db.rollback()
                job.status = ImportJobStatus.FAILED
                job.completed_at = datetime.now(timezone.utc)
                if not job.errors:
                    job.errors = []
                job.errors.append(str(e))
                await db.commit()

                # Mark as failed in progress tracker
                progress_tracker = ImportProgressTracker()
                await progress_tracker.mark_failed(str(job_id), str(e))
            except Exception as update_error:
                logger.error(
                    f"Failed to update job status after error: {str(update_error)}"
                )

            return {"status": "error", "error": str(e)}


async def start_import_job_async(
    season: int, weeks: Optional[List[int]], grade_games: bool, admin_user_id: UUID
) -> UUID:
    """
    Helper function to create and start an import job.

    This function:
    1. Creates an ImportJob record
    2. Queues the background task
    3. Returns the job_id

    Args:
        season: NFL season year
        weeks: Optional list of week numbers
        grade_games: Whether to grade completed games
        admin_user_id: UUID of the admin user starting the import

    Returns:
        UUID of the created import job

    Requirements: 5.1
    """
    async with AsyncSessionLocal() as db:
        # Create import job record
        job = ImportJob(
            season=season,
            weeks=weeks,
            grade_games=grade_games,
            admin_user_id=admin_user_id,
            status=ImportJobStatus.PENDING,
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        job_id = job.id

        logger.info(f"Created import job {job_id} for season {season}")

        # Queue the background task
        # Note: In a production environment, this would use Celery, ARQ, or similar
        # For now, we'll use asyncio.create_task to run it in the background
        asyncio.create_task(execute_import_job(job_id))

        return job_id


async def check_concurrent_import(season: int) -> Optional[ImportJob]:
    """
    Check if there's already a running import for the given season.

    Args:
        season: NFL season year to check

    Returns:
        ImportJob if one is running, None otherwise

    Requirements: 5.5
    """
    async with AsyncSessionLocal() as db:
        stmt = select(ImportJob).where(
            ImportJob.season == season, ImportJob.status == ImportJobStatus.RUNNING
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
