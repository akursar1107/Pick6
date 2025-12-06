"""Property-based tests for Authentication service

Feature: basic-authentication
These tests use Hypothesis to verify correctness properties across many random inputs.
"""

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from app.services.auth_service import AuthService
from app.db.models.user import User
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


# Hypothesis strategies for generating test data
def email_strategy():
    """Generate random valid email addresses"""
    return st.emails()


def password_strategy():
    """Generate random passwords (8-72 characters for bcrypt)"""
    return st.text(
        min_size=8,
        max_size=72,
        alphabet=st.characters(min_codepoint=33, max_codepoint=126),
    )


def username_strategy():
    """Generate random usernames (alphanumeric only)"""
    return st.text(
        min_size=3,
        max_size=30,
        alphabet=st.characters(min_codepoint=ord("a"), max_codepoint=ord("z")),
    )


def display_name_strategy():
    """Generate random display names (printable ASCII only)"""
    return st.text(
        min_size=3,
        max_size=50,
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    )


@pytest.mark.asyncio
@settings(
    max_examples=35,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    password=password_strategy(),
    username=username_strategy(),
    display_name=display_name_strategy(),
)
async def test_property_1_successful_login_returns_valid_token(
    db_session,
    password,
    username,
    display_name,
):
    """
    Feature: basic-authentication, Property 1: Successful login returns valid token

    For any user with valid credentials (existing email and correct password),
    logging in should return a JWT token that contains the user's ID and has
    a valid expiration time.

    Validates: Requirements 1.1, 1.2, 1.3
    """
    # Setup: Create auth service
    auth_service = AuthService(db_session)

    # Generate unique email and username to avoid conflicts across test runs
    unique_suffix = uuid4().hex[:8]
    email = f"{username}_{unique_suffix}@example.com"
    unique_username = f"{username}_{unique_suffix}"

    # Setup: Create user with hashed password
    hashed_password = get_password_hash(password)
    user = User(
        id=uuid4(),
        email=email,
        username=unique_username,
        display_name=display_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Action: Authenticate with correct credentials (Requirement 1.1)
    authenticated_user = await auth_service.authenticate_user(email, password)

    # Assert: Authentication succeeds and returns the user
    assert (
        authenticated_user is not None
    ), f"Authentication should succeed for valid credentials"
    assert (
        authenticated_user.id == user.id
    ), f"Expected authenticated user ID {user.id}, got {authenticated_user.id}"
    assert (
        authenticated_user.email == email
    ), f"Expected email {email}, got {authenticated_user.email}"

    # Action: Generate JWT token (Requirement 1.2)
    token = create_access_token(user.id)

    # Assert: Token is generated successfully
    assert token is not None, "Token should be generated"
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 0, "Token should not be empty"

    # Action: Decode and validate token (Requirement 1.3)
    payload = decode_access_token(token)

    # Assert: Token contains correct user ID
    assert payload is not None, "Token should be decodable"
    assert "sub" in payload, "Token should contain 'sub' claim"
    assert UUID(payload["sub"]) == user.id, (
        f"Token 'sub' claim should contain user ID {user.id}, " f"got {payload['sub']}"
    )

    # Assert: Token has valid expiration time
    assert "exp" in payload, "Token should contain 'exp' claim"
    assert "iat" in payload, "Token should contain 'iat' claim"

    # Verify expiration is in the future
    exp_timestamp = payload["exp"]
    current_timestamp = datetime.now(timezone.utc).timestamp()
    assert (
        exp_timestamp > current_timestamp
    ), f"Token expiration {exp_timestamp} should be in the future (current: {current_timestamp})"

    # Verify expiration is approximately 24 hours from now (within 1 minute tolerance)
    expected_exp = current_timestamp + (24 * 60 * 60)  # 24 hours in seconds
    time_diff = abs(exp_timestamp - expected_exp)
    assert (
        time_diff < 60
    ), f"Token expiration should be ~24 hours from now, but difference is {time_diff} seconds"

    # Assert: Token type is correct
    assert "type" in payload, "Token should contain 'type' claim"
    assert (
        payload["type"] == "access"
    ), f"Token type should be 'access', got {payload['type']}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    correct_password=password_strategy(),
    wrong_password=password_strategy(),
    username=username_strategy(),
    display_name=display_name_strategy(),
)
async def test_property_2_invalid_credentials_are_rejected(
    db_session,
    correct_password,
    wrong_password,
    username,
    display_name,
):
    """
    Feature: basic-authentication, Property 2: Invalid credentials are rejected

    For any login attempt with either a non-existent email or incorrect password,
    the system should reject the login and return an authentication error (None).

    Validates: Requirements 1.4, 1.5
    """
    # Setup: Create auth service
    auth_service = AuthService(db_session)

    # Generate unique email and username to avoid conflicts
    unique_suffix = uuid4().hex[:8]
    email = f"{username}_{unique_suffix}@example.com"
    unique_username = f"{username}_{unique_suffix}"
    non_existent_email = f"nonexistent_{unique_suffix}@example.com"

    # Setup: Create user with hashed password
    hashed_password = get_password_hash(correct_password)
    user = User(
        id=uuid4(),
        email=email,
        username=unique_username,
        display_name=display_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Test Case 1: Non-existent email (Requirement 1.4)
    authenticated_user = await auth_service.authenticate_user(
        non_existent_email, correct_password
    )
    assert (
        authenticated_user is None
    ), f"Authentication should fail for non-existent email {non_existent_email}"

    # Test Case 2: Invalid password (Requirement 1.5)
    # Only test if wrong_password is different from correct_password
    if wrong_password != correct_password:
        authenticated_user = await auth_service.authenticate_user(email, wrong_password)
        assert (
            authenticated_user is None
        ), f"Authentication should fail for incorrect password"

    # Test Case 3: Both email and password are wrong
    authenticated_user = await auth_service.authenticate_user(
        non_existent_email, wrong_password
    )
    assert (
        authenticated_user is None
    ), f"Authentication should fail for both non-existent email and incorrect password"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    password=password_strategy(),
)
async def test_property_6_passwords_are_securely_hashed(
    password,
):
    """
    Feature: basic-authentication, Property 6: Passwords are securely hashed

    For any password stored in the database, it should be hashed using bcrypt,
    and the plaintext password should never be stored or logged.

    Validates: Requirements 8.1, 8.3
    """
    # Action: Hash the password
    hashed_password = get_password_hash(password)

    # Assert: Hashed password is not None and is a string
    assert hashed_password is not None, "Hashed password should not be None"
    assert isinstance(hashed_password, str), "Hashed password should be a string"
    assert len(hashed_password) > 0, "Hashed password should not be empty"

    # Assert: Hashed password is different from plaintext (Requirement 8.3)
    assert (
        hashed_password != password
    ), f"Hashed password should never equal plaintext password"

    # Assert: Hashed password follows bcrypt format (Requirement 8.1)
    # Bcrypt hashes start with $2a$, $2b$, or $2y$ followed by cost factor
    assert hashed_password.startswith(
        ("$2a$", "$2b$", "$2y$")
    ), f"Hashed password should use bcrypt format, got: {hashed_password[:4]}"

    # Assert: Bcrypt cost factor is at least 12 (security requirement)
    # Format: $2b$12$... where 12 is the cost factor
    cost_factor = int(hashed_password.split("$")[2])
    assert (
        cost_factor >= 12
    ), f"Bcrypt cost factor should be at least 12, got {cost_factor}"

    # Assert: Hash length is consistent with bcrypt (60 characters)
    assert (
        len(hashed_password) == 60
    ), f"Bcrypt hash should be 60 characters, got {len(hashed_password)}"

    # Assert: Plaintext password is not contained in the hash
    # This verifies we're not accidentally storing plaintext
    assert (
        password not in hashed_password
    ), f"Plaintext password should not appear in the hash"

    # Assert: Hash is deterministic for verification but unique per call
    # (bcrypt uses random salt, so same password produces different hashes)
    hashed_password_2 = get_password_hash(password)
    assert (
        hashed_password != hashed_password_2
    ), "Same password should produce different hashes due to random salt"

    # Assert: Both hashes should verify against the original password
    assert verify_password(
        password, hashed_password
    ), "First hash should verify against original password"
    assert verify_password(
        password, hashed_password_2
    ), "Second hash should verify against original password"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    correct_password=password_strategy(),
    wrong_password=password_strategy(),
)
async def test_property_7_password_verification_works_correctly(
    correct_password,
    wrong_password,
):
    """
    Feature: basic-authentication, Property 7: Password verification works correctly

    For any user with a stored password hash, verifying the correct password should
    succeed, and verifying an incorrect password should fail.

    Validates: Requirements 8.2
    """
    # Setup: Hash the correct password
    hashed_password = get_password_hash(correct_password)

    # Assert: Hashed password is valid
    assert hashed_password is not None, "Hashed password should not be None"
    assert isinstance(hashed_password, str), "Hashed password should be a string"

    # Test Case 1: Correct password verification should succeed (Requirement 8.2)
    verification_result = verify_password(correct_password, hashed_password)
    assert verification_result is True, f"Verifying correct password should return True"

    # Test Case 2: Incorrect password verification should fail (Requirement 8.2)
    # Only test if wrong_password is different from correct_password
    if wrong_password != correct_password:
        verification_result = verify_password(wrong_password, hashed_password)
        assert (
            verification_result is False
        ), f"Verifying incorrect password should return False"

    # Test Case 3: Empty password should fail verification
    # (unless the correct password is also empty, which is unlikely with min_size=8)
    if correct_password != "":
        verification_result = verify_password("", hashed_password)
        assert (
            verification_result is False
        ), "Verifying empty password should return False when password is not empty"

    # Test Case 4: Verification is case-sensitive
    # Test with a case-modified version if the password contains letters
    if any(c.isalpha() for c in correct_password):
        # Create a case-swapped version
        case_swapped = correct_password.swapcase()
        if case_swapped != correct_password:
            verification_result = verify_password(case_swapped, hashed_password)
            assert (
                verification_result is False
            ), "Password verification should be case-sensitive"

    # Test Case 5: Verification works consistently (multiple calls with same password)
    verification_result_1 = verify_password(correct_password, hashed_password)
    verification_result_2 = verify_password(correct_password, hashed_password)
    assert (
        verification_result_1 == verification_result_2 == True
    ), "Password verification should be consistent across multiple calls"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    username=username_strategy(),
    display_name=display_name_strategy(),
)
async def test_property_3_valid_tokens_grant_access(
    db_session,
    username,
    display_name,
):
    """
    Feature: basic-authentication, Property 3: Valid tokens grant access

    For any valid JWT token, requests to protected endpoints should be accepted
    and the user ID should be correctly extracted from the token.

    Validates: Requirements 3.1, 3.3
    """
    from app.api.dependencies import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    # Setup: Create a user
    unique_suffix = uuid4().hex[:8]
    email = f"{username}_{unique_suffix}@example.com"
    unique_username = f"{username}_{unique_suffix}"
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    user = User(
        id=uuid4(),
        email=email,
        username=unique_username,
        display_name=display_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Action: Generate a valid JWT token for the user
    token = create_access_token(user.id)

    # Assert: Token is generated successfully
    assert token is not None, "Token should be generated"
    assert isinstance(token, str), "Token should be a string"

    # Action: Decode the token to verify it's valid
    payload = decode_access_token(token)

    # Assert: Token is valid and contains correct user ID (Requirement 3.3)
    assert payload is not None, "Token should be decodable"
    assert "sub" in payload, "Token should contain 'sub' claim"
    assert UUID(payload["sub"]) == user.id, (
        f"Token 'sub' claim should contain user ID {user.id}, " f"got {payload['sub']}"
    )

    # Action: Simulate using the token with get_current_user dependency
    # Create mock credentials object
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    # Call get_current_user with the valid token (Requirement 3.1)
    extracted_user_id = await get_current_user(credentials)

    # Assert: User ID is correctly extracted from the token
    assert (
        extracted_user_id == user.id
    ), f"Expected user ID {user.id}, got {extracted_user_id}"
    assert isinstance(
        extracted_user_id, UUID
    ), f"Extracted user ID should be a UUID, got {type(extracted_user_id)}"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    user_id=st.uuids(),
)
async def test_property_8_token_contains_correct_user_id(
    user_id,
):
    """
    Feature: basic-authentication, Property 8: Token contains correct user ID

    For any generated JWT token, decoding the token should yield the same
    user ID that was used to create it.

    Validates: Requirements 1.2, 3.3
    """
    # Action: Generate a JWT token with the given user_id (Requirement 1.2)
    token = create_access_token(user_id)

    # Assert: Token is generated successfully
    assert token is not None, "Token should be generated"
    assert isinstance(token, str), "Token should be a string"
    assert len(token) > 0, "Token should not be empty"

    # Action: Decode the token (Requirement 3.3)
    payload = decode_access_token(token)

    # Assert: Token is decodable
    assert payload is not None, "Token should be decodable"
    assert isinstance(payload, dict), "Decoded payload should be a dictionary"

    # Assert: Token contains the "sub" claim
    assert "sub" in payload, "Token should contain 'sub' claim with user ID"

    # Assert: The "sub" claim contains the correct user ID
    decoded_user_id = UUID(payload["sub"])
    assert (
        decoded_user_id == user_id
    ), f"Token should contain user ID {user_id}, got {decoded_user_id}"

    # Assert: User ID round-trips correctly (encode then decode)
    assert str(user_id) == payload["sub"], (
        f"User ID should round-trip correctly: "
        f"original={user_id}, encoded={payload['sub']}"
    )

    # Assert: Token contains other required claims
    assert "exp" in payload, "Token should contain 'exp' (expiration) claim"
    assert "iat" in payload, "Token should contain 'iat' (issued at) claim"
    assert "type" in payload, "Token should contain 'type' claim"
    assert (
        payload["type"] == "access"
    ), f"Token type should be 'access', got {payload['type']}"

    # Assert: Expiration is in the future
    exp_timestamp = payload["exp"]
    current_timestamp = datetime.now(timezone.utc).timestamp()
    assert (
        exp_timestamp > current_timestamp
    ), f"Token expiration should be in the future"

    # Assert: Issued at is in the past or present
    iat_timestamp = payload["iat"]
    assert (
        iat_timestamp <= current_timestamp + 1
    ), f"Token 'iat' should be in the past or present (allowing 1 second tolerance)"


@pytest.mark.asyncio
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
)
@given(
    username=username_strategy(),
    display_name=display_name_strategy(),
)
async def test_property_4_invalid_tokens_are_rejected(
    db_session,
    username,
    display_name,
):
    """
    Feature: basic-authentication, Property 4: Invalid tokens are rejected

    For any invalid, malformed, or expired JWT token, requests to protected
    endpoints should be rejected with an authentication error.

    Validates: Requirements 2.4, 3.4
    """
    from app.api.dependencies import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials
    from fastapi import HTTPException

    # Setup: Create a user for generating valid tokens
    unique_suffix = uuid4().hex[:8]
    email = f"{username}_{unique_suffix}@example.com"
    unique_username = f"{username}_{unique_suffix}"
    password = "testpassword123"
    hashed_password = get_password_hash(password)

    user = User(
        id=uuid4(),
        email=email,
        username=unique_username,
        display_name=display_name,
        hashed_password=hashed_password,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Test Case 1: Malformed token (not a valid JWT)
    malformed_token = "this.is.not.a.valid.jwt.token"
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=malformed_token
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Malformed token should return 401, " f"got {exc_info.value.status_code}"
    )
    assert "Invalid authentication token" in exc_info.value.detail, (
        f"Error message should indicate invalid token, " f"got: {exc_info.value.detail}"
    )

    # Test Case 2: Token with invalid signature
    # Create a token with a different secret key
    import jwt as pyjwt

    invalid_token = pyjwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "type": "access",
        },
        "wrong-secret-key",  # Different secret
        algorithm="HS256",
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=invalid_token
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Token with invalid signature should return 401, "
        f"got {exc_info.value.status_code}"
    )

    # Test Case 3: Expired token (Requirement 2.4)
    # Create a token that expired 1 hour ago
    expired_token = create_access_token(
        user.id, expires_delta=timedelta(hours=-1)  # Negative delta = expired
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=expired_token
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Expired token should return 401, " f"got {exc_info.value.status_code}"
    )

    # Test Case 4: Token without "sub" claim
    # Create a token missing the user ID
    from jose import jwt as jose_jwt
    from app.core.config import settings

    token_without_sub = jose_jwt.encode(
        {
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "type": "access",
            # Missing "sub" claim
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=token_without_sub
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Token without 'sub' claim should return 401, "
        f"got {exc_info.value.status_code}"
    )

    # Test Case 5: Token with invalid UUID in "sub" claim
    token_with_invalid_uuid = jose_jwt.encode(
        {
            "sub": "not-a-valid-uuid",  # Invalid UUID format
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "type": "access",
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=token_with_invalid_uuid
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Token with invalid UUID should return 401, "
        f"got {exc_info.value.status_code}"
    )

    # Test Case 6: Empty token
    empty_token = ""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=empty_token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401, (
        f"Empty token should return 401, " f"got {exc_info.value.status_code}"
    )
