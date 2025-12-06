"""Create a new user"""

import asyncio
import sys
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.db.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash


async def create_user(
    email: str, username: str, password: str, display_name: str = None
):
    """Create a new user in the database"""
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user already exists by email
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"❌ User with email {email} already exists!")
            print(f"   User ID: {existing_user.id}")
            print(f"   Username: {existing_user.username}")
            return None

        # Check if username is taken
        result = await session.execute(select(User).where(User.username == username))
        existing_username = result.scalar_one_or_none()

        if existing_username:
            print(f"❌ Username {username} is already taken!")
            return None

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            id=uuid4(),
            email=email,
            username=username,
            display_name=display_name or username,
            hashed_password=hashed_password,
            is_active=True,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print(f"✅ Created user successfully!")
        print(f"   User ID: {new_user.id}")
        print(f"   Email: {new_user.email}")
        print(f"   Username: {new_user.username}")
        print(f"   Display Name: {new_user.display_name}")
        print()
        print("You can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")

        return new_user


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Usage: python -m scripts.create_user <email> <username> <password> [display_name]"
        )
        print()
        print("Example:")
        print(
            '  python -m scripts.create_user "akursar@example.com" "akursar" "mypassword" "Akursar"'
        )
        sys.exit(1)

    email = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    display_name = sys.argv[4] if len(sys.argv) > 4 else None

    asyncio.run(create_user(email, username, password, display_name))
