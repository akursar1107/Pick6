"""Game endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.sports.nfl.schemas import GameResponse, GameCreate
from app.sports.nfl.services import GameService
from app.schemas.game import GameWithPickResponse
from app.services.game_service import GameService as MainGameService
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=List[GameResponse])
async def get_games(
    week: Optional[int] = Query(None),
    season: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get games with optional filters"""
    game_service = GameService(db)
    games = await game_service.get_games(week=week, season=season, status=status)
    return games


@router.get("/available", response_model=List[GameWithPickResponse])
async def get_available_games(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user),
):
    """
    Get games available for picks (future kickoffs).
    Includes user's existing picks.

    Requirements: 7.1, 7.2, 7.3, 7.4, 8.1, 8.2
    """
    game_service = MainGameService(db)
    games = await game_service.get_available_games(user_id=user_id)
    return games


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get game by ID"""
    game_service = GameService(db)
    game = await game_service.get_game_by_id(game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )
    return game


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameCreate,
    db: AsyncSession = Depends(get_db),
    # TODO: Add admin authentication
):
    """Create a new game (admin only)"""
    game_service = GameService(db)
    game = await game_service.create_game(game_data)
    return game
