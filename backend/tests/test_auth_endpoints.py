"""Unit tests for authentication endpoints

These tests verify specific scenarios for the login endpoint.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
from app.main import app
from app.db.models.user import User
from app.core.security import get_password_hash


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user with a known password"""
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    user = User(
        id=uuid4(),
        email="testuser@example.com",
        username="testuser",
        display_name="Test User",
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Attach the plaintext password for testing
    user.plaintext_password = password
    return user


@pytest.mark.asyncio
async def test_login_success_with_valid_credentials(test_user, db_session):
    """
    Test successful login with valid credentials.

    Requirements: 1.1
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "access_token" in data
    assert "token_type" in data
    assert "user" in data

    # Verify token type
    assert data["token_type"] == "bearer"

    # Verify user information
    assert data["user"]["id"] == str(test_user.id)
    assert data["user"]["email"] == test_user.email
    assert data["user"]["username"] == test_user.username
    assert data["user"]["display_name"] == test_user.display_name


@pytest.mark.asyncio
async def test_login_failure_with_invalid_email(db_session):
    """
    Test login failure with non-existent email.

    Requirements: 1.4
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_failure_with_invalid_password(test_user, db_session):
    """
    Test login failure with incorrect password.

    Requirements: 1.5
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_with_missing_email(db_session):
    """
    Test login with missing email field.

    Requirements: 1.1
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "password": "somepassword",
            },
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_with_missing_password(db_session):
    """
    Test login with missing password field.

    Requirements: 1.1
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
            },
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_with_invalid_email_format(db_session):
    """
    Test login with invalid email format.

    Requirements: 1.1
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "somepassword",
            },
        )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_me_with_valid_token(test_user, db_session):
    """
    Test GET /me endpoint with valid authentication token.

    Requirements: 3.1, 3.3
    """
    # First, login to get a token
    async with AsyncClient(app=app, base_url="http://test") as client:
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Now call /me with the token
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_response.status_code == 200
        data = me_response.json()

        # Verify user information
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["display_name"] == test_user.display_name
        assert data["is_active"] == True


@pytest.mark.asyncio
async def test_get_me_without_token(db_session):
    """
    Test GET /me endpoint without authentication token.

    Requirements: 3.1, 3.3
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden without auth


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(db_session):
    """
    Test GET /me endpoint with invalid authentication token.

    Requirements: 3.4
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401
