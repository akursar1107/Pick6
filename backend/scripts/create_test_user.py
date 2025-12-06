"""Create a test user for development"""

import asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.models.user import User
from app.core.config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_test_user():
    """Create a test user in the database"""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user already exists
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"✅ Test user already exists: {existing_user.email}")
            print(f"   User ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            return existing_user

        # Create new test user
        hashed_password = pwd_context.hash("testpass123")
        test_user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
        )

        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        print(f"✅ Created test user: {test_user.email}")
        print(f"   User ID: {test_user.id}")
        print(f"   Username: {test_user.username}")
        print(f"   Password: testpass123")
        print()
        print("You can now login with:")
        print("   Email: test@example.com")
        print("   Password: testpass123")

        return test_user


if __name__ == "__main__":
    asyncio.run(create_test_user())
