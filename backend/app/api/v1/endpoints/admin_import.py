"""Admin import endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.api.dependencies import require_admin
from app.db.models.user import User
from app.db.models.import_job import ImportJob, ImportJobStatus
from app.db.models.game import Game
from app.schemas.import_job import (
    ImportStartRequest,
    ImportStartResponse,
    ImportStatusResponse,
    ImportHistoryResponse,
    ImportHistoryItem,
    ImportProgressResponse,
    ImportStatsResponse,
    ExistingDataCheckRequest,
    ExistingDataCheckResponse,
)
from app.services.import_progress_tracker import ImportProgressTracker
from app.worker.tasks import start_import_job_async, check_concurrent_import

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/start",
    response_model=ImportStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start NFL Data Import",
    description="Initiates a background job to import NFL season data from nflreadpy",
    responses={
        201: {
            "description": "Import job created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "message": "Import job started successfully",
                        "estimated_duration_minutes": 30,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_weeks": {
                            "summary": "Invalid week numbers",
                            "value": {
                                "detail": "Week numbers must be between 1 and 18. Invalid weeks: 19, 20"
                            },
                        },
                        "no_weeks": {
                            "summary": "No weeks selected",
                            "value": {
                                "detail": "Please select at least one week to import"
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Not authorized (admin access required)",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
        409: {
            "description": "Concurrent import already in progress",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An import is already in progress for season 2024. Please wait for it to complete before starting a new import."
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An unexpected error occurred while starting the import. Please try again later."
                    }
                }
            },
        },
    },
)
async def start_import(
    request: ImportStartRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Start an NFL data import job.

    This endpoint initiates a background job to import NFL season data from nflreadpy.
    The import runs asynchronously, allowing you to continue using the dashboard while
    data is being imported.

    **Authentication:** Requires admin user authentication via Bearer token.

    **Process:**
    1. Validates the import parameters (season year, week numbers)
    2. Checks for concurrent imports for the same season
    3. Creates an ImportJob record in the database
    4. Queues a background task for execution
    5. Returns the job_id for status tracking

    **Parameters:**
    - **season**: NFL season year (2020-2030)
    - **weeks**: Either "all" for entire season or list of week numbers (1-18)
    - **grade_games**: Whether to fetch touchdown scorer data for completed games

    **Estimated Duration:**
    - Full season import: ~30 minutes
    - Per week import: ~2 minutes per week

    **Requirements:** 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
    """
    try:
        logger.info(
            f"Import request from user {current_user.id}: "
            f"season={request.season}, weeks={request.weeks}, "
            f"grade_games={request.grade_games}"
        )

        # Validate week numbers if specific weeks are provided
        if isinstance(request.weeks, list):
            invalid_weeks = [w for w in request.weeks if w < 1 or w > 18]
            if invalid_weeks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Week numbers must be between 1 and 18. Invalid weeks: {', '.join(map(str, invalid_weeks))}",
                )

            if len(request.weeks) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please select at least one week to import",
                )

        # Check for concurrent imports for the same season
        concurrent_job = await check_concurrent_import(request.season)
        if concurrent_job:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An import is already in progress for season {request.season}. "
                f"Please wait for it to complete before starting a new import.",
            )

        # Convert "all" to None for the service layer
        weeks_list = None if request.weeks == "all" else request.weeks

        # Start the import job
        job_id = await start_import_job_async(
            season=request.season,
            weeks=weeks_list,
            grade_games=request.grade_games,
            admin_user_id=current_user.id,
        )

        # Estimate duration (rough estimate: 2 minutes per week, or 30 minutes for full season)
        if weeks_list:
            estimated_duration = len(weeks_list) * 2
        else:
            estimated_duration = 30

        logger.info(f"Import job {job_id} created and queued")

        return ImportStartResponse(
            job_id=job_id,
            message="Import job started successfully",
            estimated_duration_minutes=estimated_duration,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error starting import: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid import parameters: {str(e)}",
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error starting import job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while starting the import. Please try again later.",
        )


@router.get(
    "/status/{job_id}",
    response_model=ImportStatusResponse,
    summary="Get Import Job Status",
    description="Retrieves the current status and progress of an import job",
    responses={
        200: {
            "description": "Import job status retrieved successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "running": {
                            "summary": "Import in progress",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "running",
                                "progress": {
                                    "status": "running",
                                    "current_step": "Processing game 45 of 272",
                                    "games_processed": 45,
                                    "total_games": 272,
                                    "teams_created": 32,
                                    "players_created": 128,
                                    "games_created": 45,
                                    "games_updated": 0,
                                    "games_graded": 12,
                                    "errors": [],
                                },
                                "stats": None,
                                "started_at": "2024-12-08T10:30:00Z",
                                "completed_at": None,
                                "errors": [],
                            },
                        },
                        "completed": {
                            "summary": "Import completed",
                            "value": {
                                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                                "status": "completed",
                                "progress": None,
                                "stats": {
                                    "teams_created": 32,
                                    "players_created": 456,
                                    "games_created": 272,
                                    "games_updated": 0,
                                    "games_graded": 89,
                                    "total_games": 272,
                                },
                                "started_at": "2024-12-08T10:30:00Z",
                                "completed_at": "2024-12-08T11:00:00Z",
                                "errors": [],
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Not authorized (admin access required)",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
        404: {
            "description": "Import job not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Import job not found. The job may have expired or been deleted."
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while fetching import status. Please try again."
                    }
                }
            },
        },
    },
)
async def get_import_status(
    job_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the status of an import job.

    This endpoint retrieves the current status and progress of an import job by job_id.
    It combines data from the database (persistent job record) and Redis (real-time progress).

    **Authentication:** Requires admin user authentication via Bearer token.

    **Process:**
    1. Fetches the ImportJob record from the database
    2. Gets current progress from Redis (if job is running)
    3. Returns combined status and progress information

    **Status Values:**
    - **pending**: Job created but not yet started
    - **running**: Job is currently executing
    - **completed**: Job finished successfully
    - **failed**: Job encountered an error and stopped

    **Progress Information (when running):**
    - Current step description
    - Games processed / total games
    - Statistics counters (teams, players, games created/updated/graded)
    - Any errors encountered

    **Use Case:** Poll this endpoint every 2 seconds to display real-time progress in the UI.

    **Requirements:** 4.1, 4.2, 4.3, 5.4
    """
    try:
        # Fetch import job from database
        stmt = select(ImportJob).where(ImportJob.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import job not found. The job may have expired or been deleted.",
            )

        # Get progress from Redis
        progress_tracker = ImportProgressTracker()
        progress = await progress_tracker.get_progress(str(job_id))

        # Build progress response
        progress_response = None
        if progress:
            progress_response = ImportProgressResponse(
                status=progress.status,
                current_step=progress.current_step,
                games_processed=progress.games_processed,
                total_games=progress.total_games,
                teams_created=progress.teams_created,
                players_created=progress.players_created,
                games_created=progress.games_created,
                games_updated=progress.games_updated,
                games_graded=progress.games_graded,
                errors=progress.errors or [],
            )

        # Build stats response if job is completed
        stats_response = None
        if job.status == ImportJobStatus.COMPLETED:
            stats_response = ImportStatsResponse(
                teams_created=job.teams_created,
                players_created=job.players_created,
                games_created=job.games_created,
                games_updated=job.games_updated,
                games_graded=job.games_graded,
                total_games=job.total_games,
            )

        return ImportStatusResponse(
            job_id=job.id,
            status=job.status.value,
            progress=progress_response,
            stats=stats_response,
            started_at=job.started_at,
            completed_at=job.completed_at,
            errors=job.errors or [],
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Error fetching import status for job {job_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching import status. Please try again.",
        )


@router.get(
    "/history",
    response_model=ImportHistoryResponse,
    summary="Get Import History",
    description="Retrieves a paginated list of import jobs with optional filters",
    responses={
        200: {
            "description": "Import history retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "imports": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "season": 2024,
                                "weeks": None,
                                "grade_games": True,
                                "status": "completed",
                                "started_at": "2024-12-08T10:30:00Z",
                                "completed_at": "2024-12-08T11:00:00Z",
                                "stats": {
                                    "teams_created": 32,
                                    "players_created": 456,
                                    "games_created": 272,
                                    "games_updated": 0,
                                    "games_graded": 89,
                                    "total_games": 272,
                                },
                                "admin_user_id": "660e8400-e29b-41d4-a716-446655440000",
                            },
                            {
                                "id": "770e8400-e29b-41d4-a716-446655440000",
                                "season": 2024,
                                "weeks": [1, 2, 3],
                                "grade_games": False,
                                "status": "completed",
                                "started_at": "2024-12-07T14:20:00Z",
                                "completed_at": "2024-12-07T14:26:00Z",
                                "stats": {
                                    "teams_created": 0,
                                    "players_created": 0,
                                    "games_created": 48,
                                    "games_updated": 0,
                                    "games_graded": 0,
                                    "total_games": 48,
                                },
                                "admin_user_id": "660e8400-e29b-41d4-a716-446655440000",
                            },
                        ],
                        "total": 15,
                    }
                }
            },
        },
        400: {
            "description": "Invalid filter parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid status filter: invalid_status. Valid values: pending, running, completed, failed"
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Not authorized (admin access required)",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
    },
)
async def get_import_history(
    limit: int = 10,
    offset: int = 0,
    season: Optional[int] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get import history with optional filters.

    This endpoint retrieves a paginated list of import jobs, ordered by most recent first.
    Use this to display import history in the admin dashboard.

    **Authentication:** Requires admin user authentication via Bearer token.

    **Query Parameters:**
    - **limit**: Maximum number of results to return (default: 10)
    - **offset**: Number of results to skip for pagination (default: 0)
    - **season**: Filter by NFL season year (optional)
    - **status_filter**: Filter by status: pending, running, completed, failed (optional)

    **Response:**
    - **imports**: List of import job records with statistics
    - **total**: Total count of jobs matching the filters (for pagination)

    **Ordering:** Results are ordered by started_at descending (most recent first).

    **Use Cases:**
    - Display recent imports in the admin dashboard
    - Show import history for a specific season
    - Filter by status to find failed imports for troubleshooting

    **Requirements:** 6.1, 6.2, 6.3, 6.4
    """
    # Build query
    stmt = select(ImportJob)

    # Apply filters
    if season:
        stmt = stmt.where(ImportJob.season == season)

    if status_filter:
        try:
            status_enum = ImportJobStatus(status_filter)
            stmt = stmt.where(ImportJob.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}. "
                f"Valid values: pending, running, completed, failed",
            )

    # Order by started_at descending (most recent first)
    stmt = stmt.order_by(ImportJob.started_at.desc())

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar()

    # Apply pagination
    stmt = stmt.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Build response
    history_items = []
    for job in jobs:
        stats = ImportStatsResponse(
            teams_created=job.teams_created,
            players_created=job.players_created,
            games_created=job.games_created,
            games_updated=job.games_updated,
            games_graded=job.games_graded,
            total_games=job.total_games,
        )

        history_item = ImportHistoryItem(
            id=job.id,
            season=job.season,
            weeks=job.weeks,
            grade_games=job.grade_games,
            status=job.status.value,
            started_at=job.started_at,
            completed_at=job.completed_at,
            stats=stats,
            admin_user_id=job.admin_user_id,
        )
        history_items.append(history_item)

    return ImportHistoryResponse(imports=history_items, total=total)


@router.post(
    "/check-existing",
    response_model=ExistingDataCheckResponse,
    summary="Check for Existing Data",
    description="Checks if games already exist for the selected season/weeks before importing",
    responses={
        200: {
            "description": "Existing data check completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "has_existing": {
                            "summary": "Existing data found",
                            "value": {
                                "has_existing_data": True,
                                "existing_games_count": 150,
                                "games_to_create": 122,
                                "games_to_update": 150,
                                "warning_message": "Found 150 existing games for 2024 season (all weeks). Approximately 150 games will be updated and 122 new games will be created. Existing pick data will be preserved.",
                            },
                        },
                        "no_existing": {
                            "summary": "No existing data",
                            "value": {
                                "has_existing_data": False,
                                "existing_games_count": 0,
                                "games_to_create": 272,
                                "games_to_update": 0,
                                "warning_message": None,
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Not authorized (admin access required)",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while checking for existing data. Please try again."
                    }
                }
            },
        },
    },
)
async def check_existing_data(
    request: ExistingDataCheckRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Check for existing games in the selected season/weeks.

    This endpoint checks the database for existing games before starting an import.
    Use this to warn users if they're about to overwrite existing data.

    **Authentication:** Requires admin user authentication via Bearer token.

    **Process:**
    1. Queries database for existing games in selected season/weeks
    2. Estimates total games that would be imported
    3. Calculates games to create vs update
    4. Returns warning message if existing data found

    **Parameters:**
    - **season**: NFL season year (2020-2030)
    - **weeks**: Either "all" for entire season or list of week numbers (1-18)

    **Response:**
    - **has_existing_data**: Whether any games exist for the selection
    - **existing_games_count**: Count of games already in database
    - **games_to_create**: Estimated new games to be created
    - **games_to_update**: Estimated existing games to be updated
    - **warning_message**: User-friendly warning message (if applicable)

    **Important:** Existing pick data is always preserved when games are updated.

    **Use Case:** Call this before showing the import confirmation dialog to warn users
    about potential data updates.

    **Requirements:** 8.1, 8.2, 8.3, 8.4
    """
    try:
        logger.info(
            f"Checking existing data for season {request.season}, weeks {request.weeks}"
        )

        # Build query for existing games
        stmt = select(func.count(Game.id)).where(Game.season_year == request.season)

        # Filter by weeks if specific weeks are provided
        if isinstance(request.weeks, list):
            stmt = stmt.where(Game.week_number.in_(request.weeks))

        # Execute query
        result = await db.execute(stmt)
        existing_games_count = result.scalar() or 0

        # Estimate total games that would be imported
        # This is an approximation - actual count would require fetching from nflreadpy
        if isinstance(request.weeks, list):
            # Rough estimate: ~16 games per week
            estimated_total_games = len(request.weeks) * 16
        else:
            # Full season: ~18 weeks * 16 games = ~288 games
            estimated_total_games = 288

        # Calculate games to create vs update
        games_to_update = min(existing_games_count, estimated_total_games)
        games_to_create = max(0, estimated_total_games - existing_games_count)

        has_existing_data = existing_games_count > 0

        # Build warning message
        warning_message = None
        if has_existing_data:
            if isinstance(request.weeks, list):
                weeks_str = f"weeks {', '.join(map(str, sorted(request.weeks)))}"
            else:
                weeks_str = "all weeks"

            warning_message = (
                f"Found {existing_games_count} existing games for {request.season} season ({weeks_str}). "
                f"Approximately {games_to_update} games will be updated and {games_to_create} new games will be created. "
                f"Existing pick data will be preserved."
            )

        logger.info(
            f"Existing data check: {existing_games_count} existing games, "
            f"{games_to_update} to update, {games_to_create} to create"
        )

        return ExistingDataCheckResponse(
            has_existing_data=has_existing_data,
            existing_games_count=existing_games_count,
            games_to_create=games_to_create,
            games_to_update=games_to_update,
            warning_message=warning_message,
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error checking existing data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking for existing data. Please try again.",
        )
