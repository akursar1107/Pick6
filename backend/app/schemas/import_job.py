"""Import job schemas"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Literal


def get_current_nfl_season() -> int:
    """
    Calculate the current NFL season.

    NFL season runs from September through February.
    If we're in January-August, the current season is the previous year.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    # NFL season runs September (9) through February (2)
    return year if month >= 9 else year - 1


class ImportStartRequest(BaseModel):
    """
    Schema for starting an import job.

    Use this to initiate a background job that imports NFL season data from nflreadpy.
    """

    season: int = Field(
        ge=2020,
        description="NFL season year (e.g., 2024 for the 2024 season)",
        examples=[2024],
    )

    @field_validator("season")
    @classmethod
    def validate_season(cls, v: int) -> int:
        current_season = get_current_nfl_season()
        if v > current_season:
            raise ValueError(
                f"Cannot import future seasons. Current season is {current_season}"
            )
        if v < 2020:
            raise ValueError("Season must be 2020 or later")
        return v

    weeks: List[int] | Literal["all"] = Field(
        default="all",
        description="Week numbers to import (1-18) or 'all' for entire season",
        examples=["all", [1, 2, 3]],
    )
    grade_games: bool = Field(
        default=False,
        description="Whether to fetch touchdown scorer data for completed games",
        examples=[True, False],
    )


class ImportStartResponse(BaseModel):
    """
    Schema for import start response.

    Returned when an import job is successfully created and queued.
    """

    job_id: UUID = Field(
        description="Unique identifier for the import job. Use this to check status.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    message: str = Field(
        description="Success message",
        examples=["Import job started successfully"],
    )
    estimated_duration_minutes: int = Field(
        description="Estimated time to complete the import in minutes",
        examples=[30, 6],
    )


class ImportProgressResponse(BaseModel):
    """
    Schema for import progress information.

    Real-time progress data retrieved from Redis while import is running.
    """

    status: str = Field(
        description="Current job status: pending, running, completed, failed",
        examples=["running"],
    )
    current_step: str = Field(
        description="Description of current operation",
        examples=["Processing game 45 of 272"],
    )
    games_processed: int = Field(
        description="Number of games processed so far",
        examples=[45],
    )
    total_games: int = Field(
        description="Total number of games to process",
        examples=[272],
    )
    teams_created: int = Field(
        default=0,
        description="Number of new teams created",
        examples=[32],
    )
    players_created: int = Field(
        default=0,
        description="Number of new players created",
        examples=[128],
    )
    games_created: int = Field(
        default=0,
        description="Number of new games created",
        examples=[45],
    )
    games_updated: int = Field(
        default=0,
        description="Number of existing games updated",
        examples=[0],
    )
    games_graded: int = Field(
        default=0,
        description="Number of games graded (touchdown data fetched)",
        examples=[12],
    )
    errors: List[str] = Field(
        default=[],
        description="List of error messages encountered during import",
        examples=[[]],
    )


class ImportStatsResponse(BaseModel):
    """
    Schema for import statistics.

    Final statistics after import completes successfully.
    """

    teams_created: int = Field(
        description="Total number of new teams created",
        examples=[32],
    )
    players_created: int = Field(
        description="Total number of new players created",
        examples=[456],
    )
    games_created: int = Field(
        description="Total number of new games created",
        examples=[272],
    )
    games_updated: int = Field(
        description="Total number of existing games updated",
        examples=[0],
    )
    games_graded: int = Field(
        description="Total number of games graded (touchdown data fetched)",
        examples=[89],
    )
    total_games: int = Field(
        description="Total number of games processed",
        examples=[272],
    )


class ImportStatusResponse(BaseModel):
    """
    Schema for import status response.

    Complete status information for an import job, including real-time progress
    (if running) and final statistics (if completed).
    """

    job_id: UUID = Field(
        description="Unique identifier for the import job",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        description="Current job status: pending, running, completed, failed",
        examples=["running", "completed"],
    )
    progress: Optional[ImportProgressResponse] = Field(
        default=None,
        description="Real-time progress information (only present when job is running)",
    )
    stats: Optional[ImportStatsResponse] = Field(
        default=None,
        description="Final statistics (only present when job is completed)",
    )
    started_at: datetime = Field(
        description="Timestamp when the import job started",
        examples=["2024-12-08T10:30:00Z"],
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the import job completed (null if still running)",
        examples=["2024-12-08T11:00:00Z"],
    )
    errors: List[str] = Field(
        default=[],
        description="List of error messages (if job failed or encountered errors)",
        examples=[[]],
    )


class ImportHistoryItem(BaseModel):
    """
    Schema for import history item.

    Represents a single import job in the history list.
    """

    id: UUID = Field(
        description="Unique identifier for the import job",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    season: int = Field(
        description="NFL season year that was imported",
        examples=[2024],
    )
    weeks: Optional[List[int]] = Field(
        default=None,
        description="Week numbers that were imported (null means all weeks)",
        examples=[[1, 2, 3], None],
    )
    grade_games: bool = Field(
        description="Whether touchdown data was fetched",
        examples=[True, False],
    )
    status: str = Field(
        description="Job status: pending, running, completed, failed",
        examples=["completed"],
    )
    started_at: datetime = Field(
        description="Timestamp when the import started",
        examples=["2024-12-08T10:30:00Z"],
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the import completed",
        examples=["2024-12-08T11:00:00Z"],
    )
    stats: ImportStatsResponse = Field(
        description="Import statistics",
    )
    admin_user_id: UUID = Field(
        description="ID of the admin user who started the import",
        examples=["660e8400-e29b-41d4-a716-446655440000"],
    )

    class Config:
        from_attributes = True


class ImportHistoryResponse(BaseModel):
    """
    Schema for import history response.

    Paginated list of import jobs with total count for pagination.
    """

    imports: List[ImportHistoryItem] = Field(
        description="List of import jobs (ordered by most recent first)",
    )
    total: int = Field(
        description="Total count of jobs matching the filters (for pagination)",
        examples=[15],
    )


class ExistingDataCheckRequest(BaseModel):
    """
    Schema for checking existing data.

    Use this to check if games already exist before starting an import.
    """

    season: int = Field(
        ge=2020,
        description="NFL season year to check",
        examples=[2024],
    )

    @field_validator("season")
    @classmethod
    def validate_season(cls, v: int) -> int:
        current_season = get_current_nfl_season()
        if v > current_season:
            raise ValueError(
                f"Cannot check future seasons. Current season is {current_season}"
            )
        if v < 2020:
            raise ValueError("Season must be 2020 or later")
        return v

    weeks: List[int] | Literal["all"] = Field(
        default="all",
        description="Week numbers to check (1-18) or 'all' for entire season",
        examples=["all", [1, 2, 3]],
    )


class ExistingDataCheckResponse(BaseModel):
    """
    Schema for existing data check response.

    Provides information about existing games and what would happen during import.
    """

    has_existing_data: bool = Field(
        description="Whether any games exist for the selected season/weeks",
        examples=[True, False],
    )
    existing_games_count: int = Field(
        description="Count of games already in the database",
        examples=[150, 0],
    )
    games_to_create: int = Field(
        description="Estimated number of new games that would be created",
        examples=[122, 272],
    )
    games_to_update: int = Field(
        description="Estimated number of existing games that would be updated",
        examples=[150, 0],
    )
    warning_message: Optional[str] = Field(
        default=None,
        description="User-friendly warning message if existing data found",
        examples=[
            "Found 150 existing games for 2024 season (all weeks). Approximately 150 games will be updated and 122 new games will be created. Existing pick data will be preserved."
        ],
    )
