"""Game endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.sports.nfl.schemas import GameResponse, GameCreate
from app.sports.nfl.services import GameService

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
