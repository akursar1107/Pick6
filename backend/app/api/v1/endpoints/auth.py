"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    user = await auth_service.create_user(user_data)
    return user


@router.post("/login")
async def login(
    # TODO: Implement login logic
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint"""
    return {"message": "Login endpoint - TODO: Implement WebAuthn/Magic Link"}


@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Logged out successfully"}

