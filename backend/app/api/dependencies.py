"""API dependencies for authentication and authorization"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, AsyncGenerator
from app.core.security import decode_access_token
from app.db.session import get_db as _get_db
from app.db.models.user import User

security = HTTPBearer()


# Re-export get_db from session module
get_db = _get_db


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Extract and validate user_id from JWT token.

    Requirements: 3.3, 3.4, 6.2, 6.3

    Raises:
        HTTPException: 401 if token is invalid, expired, or missing
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    # Check if token is invalid or expired
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token contains user_id in "sub" claim
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate user_id format
    try:
        return UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[UUID]:
    """
    Extract user_id from JWT token if present, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    try:
        return UUID(user_id)
    except (ValueError, TypeError):
        return None


async def get_current_admin(
    current_user_id: UUID = Depends(get_current_user),
) -> UUID:
    """
    Verify that the current user is an admin.

    Note: This is a placeholder implementation. In a production system,
    you would check the user's role in the database.

    For now, this just returns the user_id, allowing any authenticated user
    to access admin endpoints. This should be updated when a proper role
    system is implemented.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    # TODO: Implement proper admin role checking
    # For now, just return the user_id (all authenticated users are "admins")
    return current_user_id


async def require_admin(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Require that the current user is an admin.

    Returns the full User object for admin operations.

    Note: This is a placeholder implementation. In a production system,
    you would check the user's role in the database.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    from sqlalchemy import select

    # Get user from database
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # TODO: Implement proper admin role checking
    # For now, all authenticated users are "admins"
    return user
