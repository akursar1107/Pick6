"""Health check endpoints for monitoring"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.api.dependencies import get_current_user, get_db, require_admin
from app.db.models.user import User
from app.db.models.pick import Pick, PickResult
from app.db.models.game import Game
from app.worker.scheduler import get_scheduler

router = APIRouter()


@router.get("/scheduler")
async def scheduler_health_check():
    """
    Health check endpoint for scheduler status.

    Returns scheduler status and information about scheduled jobs including
    next run times and job configurations.

    **Authentication Required:** No

    **Requirements:** 7.4

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "running": true,
        "jobs": [
            {
                "id": "fetch_upcoming_games",
                "name": "Fetch Upcoming Games",
                "next_run_time": "2024-12-08T01:59:00-05:00",
                "trigger": "cron[hour='1', minute='59']"
            },
            {
                "id": "grade_early_games",
                "name": "Grade Early Games",
                "next_run_time": "2024-12-08T16:30:00-05:00",
                "trigger": "cron[day_of_week='sun', hour='16', minute='30']"
            }
        ],
        "timezone": "America/New_York"
    }
    ```

    **Status Values:**
    - healthy: Scheduler is running normally
    - stopped: Scheduler is not running
    - not_initialized: Scheduler has not been initialized
    """
    scheduler = get_scheduler()

    if not scheduler:
        return {"status": "not_initialized", "running": False, "jobs": []}

    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": (
                    job.next_run_time.isoformat() if job.next_run_time else None
                ),
                "trigger": str(job.trigger),
            }
        )

    return {
        "status": "healthy" if scheduler.running else "stopped",
        "running": scheduler.running,
        "jobs": jobs_info,
        "timezone": str(scheduler.timezone),
    }


@router.get("/scoring")
async def scoring_health_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Health check endpoint for scoring system.

    Returns recent scoring statistics and system health including:
    - Database connectivity status
    - Picks graded in last 7 days
    - Games scored in last 7 days
    - Pending picks count
    - Last scoring activity timestamp

    **Authentication Required:** Yes (Bearer token with admin role)

    **Authorization:** Admin only

    **Requirements:** 7.4

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "database_healthy": true,
        "statistics": {
            "picks_graded_7d": 150,
            "games_scored_7d": 12,
            "pending_picks": 45,
            "last_scoring_time": "2024-12-07T20:30:00Z",
            "last_scored_game": "2024_12_07_KC_BUF"
        },
        "issues": null
    }
    ```

    **Status Values:**
    - healthy: All systems operating normally
    - degraded: System is functional but has warnings (high pending picks, no recent scoring)
    - unhealthy: Critical issues detected (database connection failed)

    **Error Codes:**
    - 401: Unauthorized - Invalid or missing authentication token
    - 403: Forbidden - User is not an admin
    """
    try:
        # Get database connection health
        await db.execute(text("SELECT 1"))
        db_healthy = True
    except Exception:
        db_healthy = False

    # Get recent scoring statistics (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # Count picks graded in last 7 days
    picks_graded_result = await db.execute(
        select(func.count(Pick.id)).where(
            Pick.scored_at.isnot(None), Pick.scored_at >= seven_days_ago
        )
    )
    picks_graded_7d = picks_graded_result.scalar() or 0

    # Count games scored in last 7 days
    games_scored_result = await db.execute(
        select(func.count(Game.id)).where(
            Game.scored_at.isnot(None), Game.scored_at >= seven_days_ago
        )
    )
    games_scored_7d = games_scored_result.scalar() or 0

    # Count pending picks
    pending_picks_result = await db.execute(
        select(func.count(Pick.id)).where(Pick.status == PickResult.PENDING)
    )
    pending_picks = pending_picks_result.scalar() or 0

    # Get most recent scoring activity
    recent_scoring_result = await db.execute(
        select(Game.scored_at, Game.external_id)
        .where(Game.scored_at.isnot(None))
        .order_by(Game.scored_at.desc())
        .limit(1)
    )
    recent_scoring = recent_scoring_result.first()

    last_scoring_time = None
    last_scored_game = None
    if recent_scoring:
        last_scoring_time = recent_scoring[0].isoformat()
        last_scored_game = recent_scoring[1]

    # Calculate health status
    status = "healthy"
    issues = []

    if not db_healthy:
        status = "unhealthy"
        issues.append("Database connection failed")

    if pending_picks > 1000:
        status = "degraded"
        issues.append(f"High number of pending picks: {pending_picks}")

    if last_scoring_time:
        last_scoring_dt = datetime.fromisoformat(
            last_scoring_time.replace("Z", "+00:00")
        )
        hours_since_scoring = (
            datetime.utcnow() - last_scoring_dt.replace(tzinfo=None)
        ).total_seconds() / 3600
        if hours_since_scoring > 48:
            status = "degraded"
            issues.append(f"No scoring activity in {hours_since_scoring:.1f} hours")

    return {
        "status": status,
        "database_healthy": db_healthy,
        "statistics": {
            "picks_graded_7d": picks_graded_7d,
            "games_scored_7d": games_scored_7d,
            "pending_picks": pending_picks,
            "last_scoring_time": last_scoring_time,
            "last_scored_game": last_scored_game,
        },
        "issues": issues if issues else None,
    }


@router.get("/system")
async def system_health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Overall system health check.

    Returns health status of all system components including database
    and scheduler. Useful for monitoring and alerting systems.

    **Authentication Required:** No

    **Example Response:**
    ```json
    {
        "status": "healthy",
        "components": {
            "database": "healthy",
            "scheduler": "healthy"
        },
        "timestamp": "2024-12-07T20:30:00Z"
    }
    ```

    **Status Values:**
    - healthy: All components operational
    - unhealthy: One or more components failing
    """
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"

    # Check scheduler
    scheduler = get_scheduler()
    scheduler_status = "healthy" if (scheduler and scheduler.running) else "unhealthy"

    # Overall status
    if db_status == "unhealthy" or scheduler_status == "unhealthy":
        overall_status = "unhealthy"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "components": {
            "database": db_status,
            "scheduler": scheduler_status,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
