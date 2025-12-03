"""API router aggregator"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, games, picks, users

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(picks.router, prefix="/picks", tags=["picks"])

