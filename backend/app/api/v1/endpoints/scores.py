"""Scoring endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.schemas.scoring import (
    UserScore,
    PickResultResponse,
    GameResultResponse,
    ManualScoringRequest,
    OverridePickRequest,
)
from app.services.scoring import ScoringService
from app.api.dependencies import get_current_user, get_current_admin
from app.core.exceptions import NotFoundError, UnauthorizedError

router = APIRouter()


@router.get("/user/{user_id}", response_model=UserScore)
async def get_user_score(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Get user's total score and statistics.

    Returns the user's cumulative scoring data including:
    - Total points earned across all winning picks
    - Number of wins and losses
    - Win percentage

    **Authentication Required:** Yes (Bearer token)

    **Requirements:** 11.1, 11.2, 11.3, 11.4

    **Example Response:**
    ```json
    {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "total_score": 42,
        "total_wins": 10,
        "total_losses": 5,
        "win_percentage": 66.67
    }
    ```

    **Error Codes:**
    - 401: Unauthorized - Invalid or missing authentication token
    - 404: Not Found - User does not exist
    """
    scoring_service = ScoringService(db)

    user_score = await scoring_service.get_user_total_score(user_id)
    if not user_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user_score


@router.get("/pick/{pick_id}", response_model=PickResultResponse)
async def get_pick_result(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Get detailed result for a specific pick.

    Returns comprehensive scoring details for a pick including:
    - Pick status (pending, win, loss)
    - Points breakdown (FTD and ATTD separately)
    - Actual first touchdown scorer
    - All touchdown scorers in the game
    - Grading timestamp

    **Authentication Required:** Yes (Bearer token)

    **Authorization:** User must own the pick or be an admin

    **Requirements:** 12.1, 12.2, 12.3, 12.4

    **Example Response:**
    ```json
    {
        "pick_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "win",
        "ftd_points": 3,
        "attd_points": 1,
        "total_points": 4,
        "first_td_scorer_id": "789e4567-e89b-12d3-a456-426614174000",
        "first_td_scorer_name": "Patrick Mahomes",
        "all_td_scorers": [
            {"player_id": "789e4567-e89b-12d3-a456-426614174000", "name": "Patrick Mahomes"},
            {"player_id": "456e4567-e89b-12d3-a456-426614174000", "name": "Travis Kelce"}
        ],
        "scored_at": "2024-12-07T20:30:00Z"
    }
    ```

    **Error Codes:**
    - 401: Unauthorized - Invalid or missing authentication token
    - 403: Forbidden - User does not own this pick
    - 404: Not Found - Pick does not exist
    """
    scoring_service = ScoringService(db)

    # Get the pick result
    pick_result = await scoring_service.get_pick_result(pick_id)
    if not pick_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pick not found",
        )

    # Get the pick to verify ownership
    from app.db.models.pick import Pick
    from sqlalchemy import select

    result = await db.execute(select(Pick).where(Pick.id == pick_id))
    pick = result.scalar_one_or_none()

    if not pick:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pick not found",
        )

    # Verify user owns pick (no admin check for now - will be added later)
    if pick.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this pick",
        )

    return PickResultResponse(**pick_result)


@router.get("/game/{game_id}", response_model=GameResultResponse)
async def get_game_result(
    game_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Get scoring results for a game.

    Returns game-level scoring information including:
    - First touchdown scorer
    - All touchdown scorers
    - Number of picks graded
    - Scoring timestamp
    - Whether game was manually scored

    **Authentication Required:** Yes (Bearer token)

    **Requirements:** 8.1, 8.2, 8.3, 8.4

    **Example Response:**
    ```json
    {
        "game_id": "123e4567-e89b-12d3-a456-426614174000",
        "first_td_scorer_id": "789e4567-e89b-12d3-a456-426614174000",
        "first_td_scorer_name": "Patrick Mahomes",
        "all_td_scorers": [
            {"player_id": "789e4567-e89b-12d3-a456-426614174000", "name": "Patrick Mahomes"},
            {"player_id": "456e4567-e89b-12d3-a456-426614174000", "name": "Travis Kelce"}
        ],
        "picks_graded": 25,
        "scored_at": "2024-12-07T20:30:00Z",
        "is_manually_scored": false
    }
    ```

    **Error Codes:**
    - 401: Unauthorized - Invalid or missing authentication token
    - 404: Not Found - Game does not exist or has not been scored yet
    """
    scoring_service = ScoringService(db)

    game_result = await scoring_service.get_game_result(game_id)
    if not game_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found",
        )

    return GameResultResponse(**game_result)


@router.post("/game/{game_id}/manual", response_model=dict)
async def manual_score_game(
    game_id: UUID,
    request: ManualScoringRequest,
    db: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_current_admin),
):
    """
    Manually score a game (admin only).

    Allows administrators to manually trigger scoring for a game by specifying
    the touchdown scorers. Uses the same grading logic as automatic scoring.

    **Authentication Required:** Yes (Bearer token with admin role)

    **Authorization:** Admin only

    **Requirements:** 9.1, 9.2, 9.3, 9.4

    **Request Body:**
    ```json
    {
        "first_td_scorer": "789e4567-e89b-12d3-a456-426614174000",
        "all_td_scorers": [
            "789e4567-e89b-12d3-a456-426614174000",
            "456e4567-e89b-12d3-a456-426614174000"
        ]
    }
    ```

    **Example Response:**
    ```json
    {
        "message": "Game scored successfully",
        "game_id": "123e4567-e89b-12d3-a456-426614174000",
        "picks_graded": 25
    }
    ```

    **Error Codes:**
    - 401: Unauthorized - Invalid or missing authentication token
    - 403: Forbidden - User is not an admin
    - 404: Not Found - Game does not exist
    """
    scoring_service = ScoringService(db)

    try:
        graded_count = await scoring_service.manual_grade_game(
            game_id=game_id,
            first_td_scorer=request.first_td_scorer,
            all_td_scorers=request.all_td_scorers,
            admin_id=admin_id,
        )

        await db.commit()

        return {
            "message": "Game scored successfully",
            "game_id": str(game_id),
            "picks_graded": graded_count,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/admin/picks", response_model=list)
async def get_all_picks_for_admin(
    db: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_current_admin),
):
    """
    Get all picks in the system (admin only).

    Returns all picks with complete game and player information for admin override functionality.

    **Authentication Required:** Yes (Bearer token with admin role)
    **Authorization:** Admin only
    """
    from app.services.pick_service import PickService
    from app.schemas.pick import PickResponse

    pick_service = PickService(db)
    picks = await pick_service.get_picks()  # Get all picks with relationships

    return picks


@router.patch("/pick/{pick_id}/override", response_model=dict)
async def override_pick_score(
    pick_id: UUID,
    request: OverridePickRequest,
    db: AsyncSession = Depends(get_db),
    admin_id: UUID = Depends(get_current_admin),
):
    """
    Override a pick's score (admin only).

    Allows administrators to manually override a pick's scoring result.
    Records an audit trail including the admin ID and timestamp.
    Recalculates the user's total score accordingly.

    **Authentication Required:** Yes (Bearer token with admin role)

    **Authorization:** Admin only

    **Requirements:** 10.1, 10.2, 10.3, 10.4

    **Request Body:**
    ```json
    {
        "status": "win",
        "ftd_points": 3,
        "attd_points": 1
    }
    ```

    **Example Response:**
    ```json
    {
        "message": "Pick score overridden successfully",
        "pick_id": "123e4567-e89b-12d3-a456-426614174000",
        "status": "win",
        "ftd_points": 3,
        "attd_points": 1,
        "total_points": 4
    }
    ```

    **Error Codes:**
    - 400: Bad Request - Invalid status value (must be 'win' or 'loss')
    - 401: Unauthorized - Invalid or missing authentication token
    - 403: Forbidden - User is not an admin
    - 404: Not Found - Pick does not exist
    """
    scoring_service = ScoringService(db)

    # Convert status string to PickResult enum
    from app.db.models.pick import PickResult

    try:
        status_enum = PickResult(request.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {request.status}. Must be 'win' or 'loss'",
        )

    try:
        updated_pick = await scoring_service.override_pick_score(
            pick_id=pick_id,
            status=status_enum,
            ftd_points=request.ftd_points,
            attd_points=request.attd_points,
            admin_id=admin_id,
        )

        if not updated_pick:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pick not found",
            )

        await db.commit()

        return {
            "message": "Pick score overridden successfully",
            "pick_id": str(updated_pick.id),
            "status": updated_pick.status.value,
            "ftd_points": updated_pick.ftd_points,
            "attd_points": updated_pick.attd_points,
            "total_points": updated_pick.total_points,
        }
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
