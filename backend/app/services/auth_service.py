"""Authentication service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create new user
        user = User(
            username=user_data.username,
            email=user_data.email,
            display_name=user_data.display_name or user_data.username,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

