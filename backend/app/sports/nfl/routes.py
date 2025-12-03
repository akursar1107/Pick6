# NFL routes
from fastapi import APIRouter
from app.api.v1.endpoints import games, picks

router = APIRouter()
router.include_router(games.router, prefix="/games", tags=["nfl-games"])
router.include_router(picks.router, prefix="/picks", tags=["nfl-picks"])
