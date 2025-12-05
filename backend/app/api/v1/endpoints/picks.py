"""Pick endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.schemas.pick import PickResponse, PickCreate, PickUpdate
from app.services.pick_service import PickService
from app.api.dependencies import get_current_user
from app.core.exceptions import (
    DuplicatePickError,
    GameLockedError,
    NotFoundError,
    UnauthorizedError,
)

router = APIRouter()


@router.post("/", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def create_pick(
    pick_data: PickCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Create a new pick.
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 9.1
    """
    pick_service = PickService(db)

    try:
        pick = await pick_service.create_pick(pick_data, user_id=current_user_id)
        return pick
    except DuplicatePickError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except GameLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/", response_model=List[PickResponse])
async def get_picks(
    game_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Get picks for the authenticated user with optional game filter.
    Requirements: 2.1, 2.2, 2.3, 2.4, 9.2
    """
    pick_service = PickService(db)
    picks = await pick_service.get_user_picks(user_id=current_user_id, game_id=game_id)
    return picks


@router.get("/{pick_id}", response_model=PickResponse)
async def get_pick(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Get a specific pick by ID.
    Requirements: 2.2, 9.2, 9.3
    """
    pick_service = PickService(db)
    pick = await pick_service.get_pick_by_id(pick_id)

    if not pick:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found"
        )

    # Verify user owns the pick
    if pick.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this pick",
        )

    return pick


@router.patch("/{pick_id}", response_model=PickResponse)
async def update_pick(
    pick_id: UUID,
    pick_update: PickUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Update a pick (only before game starts).
    Requirements: 3.1, 3.2, 3.3, 3.4, 9.3
    """
    pick_service = PickService(db)

    try:
        pick = await pick_service.update_pick(pick_id, current_user_id, pick_update)
        return pick
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except GameLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{pick_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pick(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user),
):
    """
    Delete a pick (only before game starts).
    Requirements: 4.1, 4.2, 4.3, 9.4
    """
    pick_service = PickService(db)

    try:
        await pick_service.delete_pick(pick_id, current_user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except GameLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
