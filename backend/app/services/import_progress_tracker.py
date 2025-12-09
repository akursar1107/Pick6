"""Import Progress Tracker - Redis-based progress tracking for import jobs"""

import json
import logging
from typing import Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ImportProgress:
    """Progress information for an import job"""

    status: str  # pending, running, completed, failed
    current_step: str
    games_processed: int
    total_games: int
    teams_created: int = 0
    players_created: int = 0
    games_created: int = 0
    games_updated: int = 0
    games_graded: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ImportProgressTracker:
    """
    Tracks import progress in Redis for real-time updates.

    Requirements: 4.1, 4.2, 4.3
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the progress tracker.

        Args:
            redis_client: Optional Redis client. If None, creates a new one.
        """
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        self._key_prefix = "import_progress"
        self._key_expiration = 86400  # 24 hours in seconds

    async def _ensure_redis(self) -> redis.Redis:
        """Ensure Redis client is available"""
        if self.redis is None:
            self.redis = await redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis

    def _get_key(self, job_id: str) -> str:
        """Get Redis key for a job ID"""
        return f"{self._key_prefix}:{job_id}"

    async def update_progress(self, job_id: str, progress: ImportProgress) -> None:
        """
        Update progress in Redis.

        Args:
            job_id: Import job ID
            progress: ImportProgress object with current state

        Requirements: 4.2, 4.3
        """
        try:
            redis_client = await self._ensure_redis()
            key = self._get_key(job_id)

            # Convert progress to JSON
            progress_dict = asdict(progress)
            progress_json = json.dumps(progress_dict)

            # Store in Redis with expiration
            await redis_client.setex(key, self._key_expiration, progress_json)

            self.logger.debug(
                f"Updated progress for job {job_id}: "
                f"{progress.games_processed}/{progress.total_games} games"
            )

        except Exception as e:
            self.logger.error(
                f"Error updating progress for job {job_id}: {str(e)}", exc_info=True
            )
            # Don't raise - progress tracking failures shouldn't stop import

    async def get_progress(self, job_id: str) -> Optional[ImportProgress]:
        """
        Get current progress from Redis.

        Args:
            job_id: Import job ID

        Returns:
            ImportProgress object or None if not found

        Requirements: 4.1, 4.2
        """
        try:
            redis_client = await self._ensure_redis()
            key = self._get_key(job_id)

            # Get from Redis
            progress_json = await redis_client.get(key)

            if not progress_json:
                self.logger.debug(f"No progress found for job {job_id}")
                return None

            # Parse JSON and create ImportProgress object
            progress_dict = json.loads(progress_json)
            progress = ImportProgress(**progress_dict)

            return progress

        except Exception as e:
            self.logger.error(
                f"Error getting progress for job {job_id}: {str(e)}", exc_info=True
            )
            return None

    async def mark_complete(self, job_id: str, stats: dict) -> None:
        """
        Mark import as complete with final statistics.

        Args:
            job_id: Import job ID
            stats: Final statistics dictionary

        Requirements: 4.5
        """
        try:
            # Get current progress or create new one
            progress = await self.get_progress(job_id)

            if progress is None:
                progress = ImportProgress(
                    status="completed",
                    current_step="Import completed",
                    games_processed=stats.get("total_games", 0),
                    total_games=stats.get("total_games", 0),
                )

            # Update with completion status and stats
            progress.status = "completed"
            progress.current_step = "Import completed successfully"
            progress.teams_created = stats.get("teams_created", 0)
            progress.players_created = stats.get("players_created", 0)
            progress.games_created = stats.get("games_created", 0)
            progress.games_updated = stats.get("games_updated", 0)
            progress.games_graded = stats.get("games_graded", 0)
            progress.games_processed = stats.get("total_games", 0)
            progress.total_games = stats.get("total_games", 0)

            await self.update_progress(job_id, progress)

            self.logger.info(f"Marked job {job_id} as complete")

        except Exception as e:
            self.logger.error(
                f"Error marking job {job_id} as complete: {str(e)}", exc_info=True
            )

    async def mark_failed(self, job_id: str, error: str) -> None:
        """
        Mark import as failed with error message.

        Args:
            job_id: Import job ID
            error: Error message

        Requirements: 4.5
        """
        try:
            # Get current progress or create new one
            progress = await self.get_progress(job_id)

            if progress is None:
                progress = ImportProgress(
                    status="failed",
                    current_step="Import failed",
                    games_processed=0,
                    total_games=0,
                )

            # Update with failure status and error
            progress.status = "failed"
            progress.current_step = f"Import failed: {error}"
            if error not in progress.errors:
                progress.errors.append(error)

            await self.update_progress(job_id, progress)

            self.logger.error(f"Marked job {job_id} as failed: {error}")

        except Exception as e:
            self.logger.error(
                f"Error marking job {job_id} as failed: {str(e)}", exc_info=True
            )

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
