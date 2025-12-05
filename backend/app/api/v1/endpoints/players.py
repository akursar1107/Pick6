"""Player endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
from app.db.session import get_db
from app.db.models.player import Player
from app.db.models.team import Team
from app.schemas.player import PlayerResponse
from app.services.player_service import PlayerService

router = APIRouter()


@router.get("/search", response_model=List[PlayerResponse])
async def search_players(
    q: str = Query(..., description="Search query for player name"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication requirement
):
    """
    Search for players by name.

    Returns players whose names match the search query (case-insensitive).
    """
    player_service = PlayerService(db)
    players = await player_service.search_players(q, limit)

    # Convert to response format with team information
    result = []
    for player in players:
        # Fetch team information
        team_result = await db.execute(select(Team).where(Team.id == player.team_id))
        team = team_result.scalar_one_or_none()

        result.append(
            PlayerResponse(
                id=player.id,
                name=player.name,
                team=team.abbreviation if team else "Unknown",
                position=player.position,
            )
        )

    return result


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add authentication requirement
):
    """
    Get a player by ID.

    Returns player information including team and position.
    """
    player_service = PlayerService(db)
    player = await player_service.get_player_by_id(player_id)

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player not found"
        )

    # Fetch team information
    team_result = await db.execute(select(Team).where(Team.id == player.team_id))
    team = team_result.scalar_one_or_none()

    return PlayerResponse(
        id=player.id,
        name=player.name,
        team=team.abbreviation if team else "Unknown",
        position=player.position,
    )
