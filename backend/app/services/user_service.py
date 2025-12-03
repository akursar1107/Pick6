"""User service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    """Service for user operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> User | None:
        """Update user"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if user_update.display_name is not None:
            user.display_name = user_update.display_name
        if user_update.email is not None:
            user.email = user_update.email

        await self.db.commit()
        await self.db.refresh(user)
        return user

