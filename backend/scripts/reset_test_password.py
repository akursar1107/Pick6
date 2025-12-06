"""Reset test user password"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash


async def reset_password():
    """Reset test user password"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Find test user
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Test user not found!")
            return

        # Reset password
        new_password = "testpass123"
        user.hashed_password = get_password_hash(new_password)

        await session.commit()

        print(f"✅ Password reset for user: {user.email}")
        print(f"   New password: {new_password}")
        print()
        print("You can now login with:")
        print(f"   Email: {user.email}")
        print(f"   Password: {new_password}")


if __name__ == "__main__":
    asyncio.run(reset_password())
