"""Pick endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.db.session import get_db
from app.schemas.pick import PickResponse, PickCreate, PickUpdate
from app.services.pick_service import PickService

router = APIRouter()


@router.get("/", response_model=List[PickResponse])
async def get_picks(
    user_id: UUID = None,
    game_id: UUID = None,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication
):
    """Get picks with optional filters"""
    pick_service = PickService(db)
    picks = await pick_service.get_picks(user_id=user_id, game_id=game_id)
    return picks


@router.get("/{pick_id}", response_model=PickResponse)
async def get_pick(
    pick_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get pick by ID"""
    pick_service = PickService(db)
    pick = await pick_service.get_pick_by_id(pick_id)
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    return pick


@router.post("/", response_model=PickResponse, status_code=status.HTTP_201_CREATED)
async def create_pick(
    pick_data: PickCreate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication and get user_id from token
):
    """Create a new pick"""
    pick_service = PickService(db)
    # TODO: Get user_id from authenticated user
    user_id = None  # Placeholder
    pick = await pick_service.create_pick(pick_data, user_id=user_id)
    return pick


@router.patch("/{pick_id}", response_model=PickResponse)
async def update_pick(
    pick_id: UUID,
    pick_update: PickUpdate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add authentication
):
    """Update a pick (only before game starts)"""
    pick_service = PickService(db)
    pick = await pick_service.update_pick(pick_id, pick_update)
    if not pick:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pick not found")
    return pick

