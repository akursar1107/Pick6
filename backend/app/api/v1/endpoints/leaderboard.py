"""Leaderboard endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional, Literal
from io import StringIO
import csv
import json
from datetime import datetime

from app.db.session import get_db
from app.schemas.leaderboard import LeaderboardEntry, UserStats
from app.services.leaderboard_service import LeaderboardService
from app.api.dependencies import get_current_user_optional
from app.core.config import settings
import redis.asyncio as redis

router = APIRouter()


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client for caching.

    Returns:
        Redis client instance
    """
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@router.get(
    "/season/{season}",
    response_model=List[LeaderboardEntry],
    summary="Get season leaderboard",
    description="Retrieve the season-long leaderboard showing all users ranked by total points",
    responses={
        200: {
            "description": "Successful response with leaderboard entries",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "rank": 1,
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "john_doe",
                            "display_name": "John Doe",
                            "total_points": 45,
                            "ftd_points": 36,
                            "attd_points": 9,
                            "wins": 15,
                            "losses": 3,
                            "pending": 2,
                            "win_percentage": 83.33,
                            "is_tied": False,
                        },
                        {
                            "rank": 2,
                            "user_id": "223e4567-e89b-12d3-a456-426614174001",
                            "username": "jane_smith",
                            "display_name": "Jane Smith",
                            "total_points": 42,
                            "ftd_points": 33,
                            "attd_points": 9,
                            "wins": 14,
                            "losses": 4,
                            "pending": 1,
                            "win_percentage": 77.78,
                            "is_tied": False,
                        },
                    ]
                }
            },
        },
        400: {
            "description": "Invalid season parameter",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid season. Must be between 2020 and 2025"
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to retrieve leaderboard. Please try again later."
                    }
                }
            },
        },
    },
)
async def get_season_leaderboard(
    season: int,
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis_client),
):
    """
    Get season leaderboard for all users.

    Requirements: 1.1, 1.2

    Args:
        season: Season year (e.g., 2024)
        db: Database session
        cache: Redis cache client

    Returns:
        List of LeaderboardEntry objects sorted by rank

    Raises:
        HTTPException: 400 if season is invalid
        HTTPException: 503 if database error occurs
    """
    # Validate season parameter
    current_year = datetime.now().year
    if season < 2020 or season > current_year + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season. Must be between 2020 and {current_year + 1}",
        )

    try:
        leaderboard_service = LeaderboardService(db, cache)
        leaderboard = await leaderboard_service.get_season_leaderboard(season)
        return leaderboard
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error getting season leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve leaderboard. Please try again later.",
        )


@router.get(
    "/week/{season}/{week}",
    response_model=List[LeaderboardEntry],
    summary="Get weekly leaderboard",
    description="Retrieve the weekly leaderboard showing all users ranked by points earned in a specific week",
    responses={
        200: {
            "description": "Successful response with weekly leaderboard entries",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "rank": 1,
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "john_doe",
                            "display_name": "John Doe",
                            "total_points": 12,
                            "ftd_points": 9,
                            "attd_points": 3,
                            "wins": 4,
                            "losses": 0,
                            "pending": 0,
                            "win_percentage": 100.0,
                            "is_tied": False,
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Invalid season or week parameter",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_season": {
                            "value": {
                                "detail": "Invalid season. Must be between 2020 and 2025"
                            }
                        },
                        "invalid_week": {
                            "value": {
                                "detail": "Invalid week number. Must be between 1 and 18"
                            }
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to retrieve leaderboard. Please try again later."
                    }
                }
            },
        },
    },
)
async def get_weekly_leaderboard(
    season: int,
    week: int,
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis_client),
):
    """
    Get weekly leaderboard for all users.

    Requirements: 2.1, 2.2

    Args:
        season: Season year (e.g., 2024)
        week: Week number (1-18)
        db: Database session
        cache: Redis cache client

    Returns:
        List of LeaderboardEntry objects sorted by rank

    Raises:
        HTTPException: 400 if season or week is invalid
        HTTPException: 503 if database error occurs
    """
    # Validate season parameter
    current_year = datetime.now().year
    if season < 2020 or season > current_year + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season. Must be between 2020 and {current_year + 1}",
        )

    # Validate week parameter
    if week < 1 or week > 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid week number. Must be between 1 and 18",
        )

    try:
        leaderboard_service = LeaderboardService(db, cache)
        leaderboard = await leaderboard_service.get_weekly_leaderboard(season, week)
        return leaderboard
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error getting weekly leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve leaderboard. Please try again later.",
        )


@router.get(
    "/user/{user_id}/stats",
    response_model=UserStats,
    summary="Get user statistics",
    description="Retrieve detailed statistics for a specific user including overall performance, FTD/ATTD breakdowns, weekly performance, and streaks",
    responses={
        200: {
            "description": "Successful response with user statistics",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "john_doe",
                        "display_name": "John Doe",
                        "total_points": 45,
                        "total_wins": 15,
                        "total_losses": 3,
                        "total_pending": 2,
                        "win_percentage": 83.33,
                        "current_rank": 1,
                        "ftd_wins": 12,
                        "ftd_losses": 2,
                        "ftd_points": 36,
                        "ftd_percentage": 85.71,
                        "attd_wins": 9,
                        "attd_losses": 1,
                        "attd_points": 9,
                        "attd_percentage": 90.0,
                        "best_week": {
                            "week": 5,
                            "points": 15,
                            "wins": 5,
                            "losses": 0,
                            "rank": 1,
                        },
                        "worst_week": {
                            "week": 3,
                            "points": 3,
                            "wins": 1,
                            "losses": 2,
                            "rank": 8,
                        },
                        "weekly_breakdown": [],
                        "current_streak": {"type": "win", "count": 5},
                        "longest_win_streak": 7,
                        "longest_loss_streak": 2,
                    }
                }
            },
        },
        400: {
            "description": "Invalid season parameter",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid season. Must be between 2020 and 2025"
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
        503: {
            "description": "Service unavailable - database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to retrieve user statistics. Please try again later."
                    }
                }
            },
        },
    },
)
async def get_user_stats(
    user_id: UUID,
    season: Optional[int] = Query(None, description="Optional season filter"),
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis_client),
):
    """
    Get detailed statistics for a user.

    Requirements: 3.1, 3.2

    Args:
        user_id: User ID
        season: Optional season filter
        db: Database session
        cache: Redis cache client

    Returns:
        UserStats object with detailed statistics

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if season is invalid
        HTTPException: 503 if database error occurs
    """
    # Validate season parameter if provided
    if season is not None:
        current_year = datetime.now().year
        if season < 2020 or season > current_year + 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid season. Must be between 2020 and {current_year + 1}",
            )

    try:
        leaderboard_service = LeaderboardService(db, cache)
        user_stats = await leaderboard_service.get_user_stats(user_id, season)
        return user_stats
    except ValueError as e:
        # User not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to retrieve user statistics. Please try again later.",
        )


@router.get(
    "/export/{season}",
    summary="Export leaderboard data",
    description="Export leaderboard data as CSV or JSON file. Supports both season-long and weekly exports.",
    responses={
        200: {
            "description": "Successful file download",
            "content": {
                "text/csv": {
                    "example": "Rank,Username,Display Name,Total Points,FTD Points,ATTD Points,Wins,Losses,Pending,Win Percentage,Is Tied\n1,john_doe,John Doe,45,36,9,15,3,2,83.33,False\n"
                },
                "application/json": {
                    "example": [
                        {
                            "rank": 1,
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "john_doe",
                            "display_name": "John Doe",
                            "total_points": 45,
                            "ftd_points": 36,
                            "attd_points": 9,
                            "wins": 15,
                            "losses": 3,
                            "pending": 2,
                            "win_percentage": 83.33,
                            "is_tied": False,
                        }
                    ]
                },
            },
        },
        400: {
            "description": "Invalid season or week parameter",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_season": {
                            "value": {
                                "detail": "Invalid season. Must be between 2020 and 2025"
                            }
                        },
                        "invalid_week": {
                            "value": {
                                "detail": "Invalid week number. Must be between 1 and 18"
                            }
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable - database error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to export leaderboard. Please try again later."
                    }
                }
            },
        },
    },
)
async def export_leaderboard(
    season: int,
    week: Optional[int] = Query(
        None, description="Optional week filter for weekly export"
    ),
    format: Literal["csv", "json"] = Query(
        "csv", description="Export format (csv or json)"
    ),
    db: AsyncSession = Depends(get_db),
    cache: redis.Redis = Depends(get_redis_client),
):
    """
    Export leaderboard data to CSV or JSON.

    Requirements: 10.1, 10.2

    Args:
        season: Season year (e.g., 2024)
        week: Optional week number for weekly export
        format: Export format (csv or json)
        db: Database session
        cache: Redis cache client

    Returns:
        File download with leaderboard data

    Raises:
        HTTPException: 400 if season or week is invalid
        HTTPException: 503 if database error occurs
    """
    # Validate season parameter
    current_year = datetime.now().year
    if season < 2020 or season > current_year + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season. Must be between 2020 and {current_year + 1}",
        )

    # Validate week parameter if provided
    if week is not None and (week < 1 or week > 18):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid week number. Must be between 1 and 18",
        )

    try:
        leaderboard_service = LeaderboardService(db, cache)

        # Get leaderboard data
        if week is not None:
            leaderboard = await leaderboard_service.get_weekly_leaderboard(season, week)
            filename_base = f"leaderboard_season_{season}_week_{week}"
        else:
            leaderboard = await leaderboard_service.get_season_leaderboard(season)
            filename_base = f"leaderboard_season_{season}"

        # Generate export based on format
        if format == "csv":
            # Generate CSV
            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "Rank",
                    "Username",
                    "Display Name",
                    "Total Points",
                    "FTD Points",
                    "ATTD Points",
                    "Wins",
                    "Losses",
                    "Pending",
                    "Win Percentage",
                    "Is Tied",
                ]
            )

            # Write data rows
            for entry in leaderboard:
                writer.writerow(
                    [
                        entry.rank,
                        entry.username,
                        entry.display_name,
                        entry.total_points,
                        entry.ftd_points,
                        entry.attd_points,
                        entry.wins,
                        entry.losses,
                        entry.pending,
                        entry.win_percentage,
                        entry.is_tied,
                    ]
                )

            # Prepare response
            output.seek(0)
            filename = f"{filename_base}.csv"

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        else:  # format == "json"
            # Generate JSON
            data = [entry.model_dump(mode="json") for entry in leaderboard]
            json_str = json.dumps(data, indent=2)
            filename = f"{filename_base}.json"

            return StreamingResponse(
                iter([json_str]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error exporting leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to export leaderboard. Please try again later.",
        )
