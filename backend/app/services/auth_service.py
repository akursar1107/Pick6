"""Authentication service"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


class AuthService:
    """Service for authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address
            password: User's plaintext password

        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Query user by email
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Return None if user doesn't exist
        if not user:
            return None

        # Return None if user has no password set
        if not user.hashed_password:
            return None

        # Verify password using bcrypt
        if not verify_password(password, user.hashed_password):
            return None

        # Return user if valid
        return user

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
