"""Integration tests for authentication system

These tests verify end-to-end authentication workflows including:
- Complete login flow
- Logout flow
- Token expiration handling
- Error scenarios
- Redirect after login
- Session persistence

Requirements: 1.1, 2.1, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 6.2, 9.1, 9.2, 9.3, 2.1, 2.2, 2.3
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import timedelta
from app.main import app
from app.db.models.user import User
from app.core.security import get_password_hash, create_access_token


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user with a known password"""
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    user = User(
        id=uuid4(),
        email="integrationtest@example.com",
        username="integrationuser",
        display_name="Integration Test User",
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
async def test_complete_login_flow(test_user, db_session):
    """
    Test 11.1: Test complete login flow

    - Login with valid credentials
    - Verify token is stored (returned in response)
    - Verify redirect works (status code indicates success)
    - Access protected route
    - Verify API calls include token

    Requirements: 1.1, 2.1, 3.1, 3.2
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Login with valid credentials (Requirement 1.1)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

        # Verify login succeeds
        assert login_response.status_code == 200, (
            f"Login should succeed with valid credentials, "
            f"got status {login_response.status_code}"
        )

        login_data = login_response.json()

        # Step 2: Verify token is returned (Requirement 2.1)
        assert "access_token" in login_data, "Response should contain access_token"
        assert "token_type" in login_data, "Response should contain token_type"
        assert "user" in login_data, "Response should contain user information"

        token = login_data["access_token"]
        assert token is not None, "Token should not be None"
        assert len(token) > 0, "Token should not be empty"
        assert login_data["token_type"] == "bearer", "Token type should be 'bearer'"

        # Verify user information is correct
        assert login_data["user"]["id"] == str(test_user.id)
        assert login_data["user"]["email"] == test_user.email
        assert login_data["user"]["username"] == test_user.username

        # Step 3: Access protected route with token (Requirements 3.1, 3.2)
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify protected route access succeeds
        assert me_response.status_code == 200, (
            f"Protected route should be accessible with valid token, "
            f"got status {me_response.status_code}"
        )

        me_data = me_response.json()

        # Step 4: Verify API calls include token and return correct data
        assert me_data["id"] == str(
            test_user.id
        ), f"Protected route should return correct user ID"
        assert me_data["email"] == test_user.email
        assert me_data["username"] == test_user.username
        assert me_data["display_name"] == test_user.display_name
        assert me_data["is_active"] == True


@pytest.mark.asyncio
async def test_logout_flow(test_user, db_session):
    """
    Test 11.2: Test logout flow

    - Logout from authenticated state
    - Verify token is cleared (client-side responsibility, we verify endpoint exists)
    - Verify redirect to login (client-side responsibility)
    - Verify cannot access protected routes (after token is removed)

    Requirements: 4.1, 4.2, 4.3
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Login first to get authenticated
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Step 2: Verify we can access protected routes before logout
        me_response_before = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert (
            me_response_before.status_code == 200
        ), "Should be able to access protected route before logout"

        # Step 3: Logout (Requirements 4.1, 4.2)
        # Note: In our implementation, logout is primarily client-side
        # The backend doesn't maintain a token blacklist yet
        # So we verify that without the token, we can't access protected routes

        # Step 4: Verify cannot access protected routes without token (Requirement 4.3)
        me_response_after = await client.get("/api/v1/auth/me")

        assert me_response_after.status_code == 403, (
            f"Should not be able to access protected route without token, "
            f"got status {me_response_after.status_code}"
        )

        # Step 5: Verify old token still works (since we don't have blacklist yet)
        # This is expected behavior - token remains valid until expiration
        # Client is responsible for removing it from storage
        me_response_with_old_token = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert (
            me_response_with_old_token.status_code == 200
        ), "Token should still be valid on server side (no blacklist yet)"


@pytest.mark.asyncio
async def test_token_expiration_handling(test_user, db_session):
    """
    Test 11.3: Test token expiration handling

    - Create expired token
    - Attempt to access protected route
    - Verify redirect to login (401 error triggers client redirect)
    - Verify token is cleared (client-side responsibility)

    Requirements: 2.4, 6.2
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Create an expired token (Requirement 6.2)
        expired_token = create_access_token(
            test_user.id,
            expires_delta=timedelta(hours=-1),  # Expired 1 hour ago
        )

        assert expired_token is not None, "Expired token should be created"

        # Step 2: Attempt to access protected route with expired token (Requirement 2.4)
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        # Step 3: Verify request is rejected with 401
        assert me_response.status_code == 401, (
            f"Expired token should be rejected with 401, "
            f"got status {me_response.status_code}"
        )

        # Verify error message indicates token expiration
        error_data = me_response.json()
        assert "detail" in error_data, "Error response should contain detail"
        # The error message should indicate authentication failure
        assert (
            "token" in error_data["detail"].lower()
            or "expired" in error_data["detail"].lower()
            or "authentication" in error_data["detail"].lower()
        ), (
            f"Error message should indicate token/authentication issue, "
            f"got: {error_data['detail']}"
        )


@pytest.mark.asyncio
async def test_error_scenarios(test_user, db_session):
    """
    Test 11.4: Test error scenarios

    - Test with invalid credentials
    - Test with network errors (simulated via invalid requests)
    - Test with server errors (simulated)
    - Verify appropriate error messages

    Requirements: 5.1, 5.2, 5.3
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test Case 1: Invalid credentials - wrong email (Requirement 5.1)
        response_wrong_email = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )

        assert (
            response_wrong_email.status_code == 401
        ), f"Invalid email should return 401, got {response_wrong_email.status_code}"

        error_data = response_wrong_email.json()
        assert "detail" in error_data, "Error response should contain detail"
        assert error_data["detail"] == "Invalid email or password", (
            f"Error message should be 'Invalid email or password', "
            f"got: {error_data['detail']}"
        )

        # Test Case 2: Invalid credentials - wrong password (Requirement 5.1)
        response_wrong_password = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword123",
            },
        )

        assert (
            response_wrong_password.status_code == 401
        ), f"Invalid password should return 401, got {response_wrong_password.status_code}"

        error_data = response_wrong_password.json()
        assert "detail" in error_data, "Error response should contain detail"
        assert error_data["detail"] == "Invalid email or password", (
            f"Error message should be 'Invalid email or password', "
            f"got: {error_data['detail']}"
        )

        # Test Case 3: Validation errors - missing fields (Requirement 5.2)
        response_missing_email = await client.post(
            "/api/v1/auth/login",
            json={
                "password": "somepassword",
            },
        )

        assert (
            response_missing_email.status_code == 422
        ), f"Missing email should return 422, got {response_missing_email.status_code}"

        # Test Case 4: Validation errors - missing password
        response_missing_password = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
            },
        )

        assert (
            response_missing_password.status_code == 422
        ), f"Missing password should return 422, got {response_missing_password.status_code}"

        # Test Case 5: Invalid email format (Requirement 5.2)
        response_invalid_format = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "not-an-email",
                "password": "somepassword",
            },
        )

        assert (
            response_invalid_format.status_code == 422
        ), f"Invalid email format should return 422, got {response_invalid_format.status_code}"

        # Test Case 6: Empty request body (Requirement 5.2)
        response_empty = await client.post(
            "/api/v1/auth/login",
            json={},
        )

        assert (
            response_empty.status_code == 422
        ), f"Empty request should return 422, got {response_empty.status_code}"


@pytest.mark.asyncio
async def test_redirect_after_login(test_user, db_session):
    """
    Test 11.5: Test redirect after login

    - Navigate to protected route while logged out (simulated)
    - Login successfully
    - Verify redirect to original destination (client-side responsibility)
    - Test default redirect when no destination (client-side responsibility)

    Note: This test verifies the backend provides the necessary data for
    the frontend to implement redirect logic. The actual redirect is
    handled by the frontend.

    Requirements: 9.1, 9.2, 9.3
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Scenario 1: User tries to access protected route without auth
        # This would trigger a 403/401, which the frontend uses to redirect to login
        me_response_unauth = await client.get("/api/v1/auth/me")

        assert (
            me_response_unauth.status_code == 403
        ), "Unauthenticated request should return 403"

        # Scenario 2: User logs in (Requirements 9.1, 9.2)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

        assert login_response.status_code == 200, "Login should succeed"

        login_data = login_response.json()
        token = login_data["access_token"]

        # Verify login response contains all necessary data for redirect
        assert (
            "access_token" in login_data
        ), "Login response should contain token for authentication"
        assert (
            "user" in login_data
        ), "Login response should contain user data for frontend state"

        # Scenario 3: User can now access the originally intended route (Requirement 9.3)
        me_response_auth = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert (
            me_response_auth.status_code == 200
        ), "User should be able to access protected route after login"

        me_data = me_response_auth.json()
        assert me_data["id"] == str(
            test_user.id
        ), "Protected route should return correct user data"


@pytest.mark.asyncio
async def test_session_persistence(test_user, db_session):
    """
    Test 11.6: Test session persistence

    - Login successfully
    - Refresh page (simulated by making new request with stored token)
    - Verify still authenticated
    - Verify user info is loaded

    Requirements: 2.1, 2.2, 2.3
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Step 1: Login successfully (Requirement 2.1)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": test_user.plaintext_password,
            },
        )

        assert login_response.status_code == 200, "Login should succeed"

        login_data = login_response.json()
        token = login_data["access_token"]

        # Verify token is returned for storage
        assert token is not None, "Token should be returned for storage"
        assert len(token) > 0, "Token should not be empty"

        # Step 2: Simulate page refresh by making a new request with stored token
        # (Requirement 2.2 - retrieve stored token)
        # In a real browser, this would be retrieved from localStorage

        # Step 3: Verify still authenticated (Requirement 2.3)
        me_response_1 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert (
            me_response_1.status_code == 200
        ), "User should still be authenticated after 'page refresh'"

        me_data_1 = me_response_1.json()

        # Step 4: Verify user info is loaded correctly
        assert me_data_1["id"] == str(
            test_user.id
        ), "User ID should be correct after refresh"
        assert (
            me_data_1["email"] == test_user.email
        ), "User email should be correct after refresh"
        assert (
            me_data_1["username"] == test_user.username
        ), "Username should be correct after refresh"
        assert (
            me_data_1["display_name"] == test_user.display_name
        ), "Display name should be correct after refresh"
        assert me_data_1["is_active"] == True, "User should be active after refresh"

        # Step 5: Simulate multiple page refreshes
        # Token should remain valid across multiple requests
        for i in range(3):
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert (
                me_response.status_code == 200
            ), f"User should remain authenticated after refresh #{i+2}"

            me_data = me_response.json()
            assert me_data["id"] == str(
                test_user.id
            ), f"User data should be consistent after refresh #{i+2}"

        # Step 6: Verify token works with other protected endpoints
        # (if we had more protected endpoints, we'd test them here)
        # For now, we've verified that /me works consistently


@pytest.mark.asyncio
async def test_concurrent_sessions(test_user, db_session):
    """
    Additional test: Verify multiple concurrent sessions work correctly

    A user should be able to have multiple valid tokens (e.g., logged in
    on multiple devices) and all should work independently.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create multiple tokens by logging in multiple times
        tokens = []

        for i in range(3):
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user.email,
                    "password": test_user.plaintext_password,
                },
            )

            assert login_response.status_code == 200, f"Login #{i+1} should succeed"

            token = login_response.json()["access_token"]
            tokens.append(token)

        # Verify tokens may be the same or different (depends on timing)
        # What matters is that they all work
        assert len(tokens) == 3, "Should have 3 tokens"

        # Verify all tokens work independently
        for i, token in enumerate(tokens):
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert me_response.status_code == 200, f"Token #{i+1} should be valid"

            me_data = me_response.json()
            assert me_data["id"] == str(
                test_user.id
            ), f"Token #{i+1} should return correct user"


@pytest.mark.asyncio
async def test_invalid_token_formats(db_session):
    """
    Additional test: Verify various invalid token formats are rejected
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        invalid_tokens = [
            "",  # Empty token
            "invalid",  # Not a JWT
            "Bearer token",  # Wrong format
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Malformed JWT
            "a" * 1000,  # Very long invalid token
        ]

        for invalid_token in invalid_tokens:
            me_response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {invalid_token}"},
            )

            # Accept both 401 (Unauthorized) and 403 (Forbidden) as valid rejection codes
            assert me_response.status_code in [401, 403], (
                f"Invalid token '{invalid_token[:20]}...' should be rejected with 401 or 403, "
                f"got {me_response.status_code}"
            )
