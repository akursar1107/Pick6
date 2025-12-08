"""API router aggregator"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, players, picks, games, scores, health
from app.sports.nfl import routes as nfl_routes

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(players.router, prefix="/players", tags=["players"])
api_router.include_router(picks.router, prefix="/picks", tags=["picks"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(scores.router, prefix="/scores", tags=["scoring"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
# Mount all NFL endpoints under /nfl
api_router.include_router(nfl_routes.router, prefix="/nfl", tags=["nfl"])
