"""API router aggregator"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users
from app.sports.nfl import routes as nfl_routes

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Mount all NFL endpoints under /nfl
api_router.include_router(nfl_routes.router, prefix="/nfl", tags=["nfl"])
