# Design Document: Basic Authentication

## Overview

The Basic Authentication feature provides a simple, secure authentication system using email/password credentials and JWT (JSON Web Token) tokens. This feature enables users to log in, maintain authenticated sessions across page refreshes, and securely access protected resources. It serves as the foundation for all user-specific functionality in the application.

The system uses industry-standard practices: bcrypt for password hashing, JWT for stateless authentication, and secure token storage in browser localStorage. The design prioritizes simplicity and security while providing a smooth user experience.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (Frontend)                      │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Login Form    │  │  Auth Store  │  │  API Client     │ │
│  │  Component     │→ │  (Zustand)   │→ │  (Axios)        │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
│           │                  │                    │          │
│           │                  ↓                    │          │
│           │          localStorage                 │          │
│           │          (JWT Token)                  │          │
└───────────┼──────────────────────────────────────┼──────────┘
            │                                       │
            │              HTTPS/REST               │
            ↓                                       ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Auth          │  │  Auth        │  │  Security       │ │
│  │  Endpoints     │→ │  Service     │→ │  Utils          │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
│           │                  │                    │          │
│           │                  ↓                    ↓          │
│           │          ┌──────────────┐    ┌──────────────┐  │
│           │          │  User Model  │    │  JWT Utils   │  │
│           │          │  (Database)  │    │  (jose)      │  │
│           │          └──────────────┘    └──────────────┘  │
└───────────┴──────────────────────────────────────────────────┘
```

### Authentication Flow

```
User                 Frontend              Backend              Database
 │                      │                     │                     │
 │  1. Enter email/pwd  │                     │                     │
 │─────────────────────>│                     │                     │
 │                      │  2. POST /login     │                     │
 │                      │────────────────────>│                     │
 │                      │                     │  3. Query user      │
 │                      │                     │────────────────────>│
 │                      │                     │<────────────────────│
 │                      │                     │  4. User record     │
 │                      │                     │                     │
 │                      │                     │  5. Verify password │
 │                      │                     │     (bcrypt)        │
 │                      │                     │                     │
 │                      │                     │  6. Generate JWT    │
 │                      │                     │     (user_id, exp)  │
 │                      │                     │                     │
 │                      │  7. Return token    │                     │
 │                      │<────────────────────│                     │
 │                      │                     │                     │
 │                      │  8. Store in        │                     │
 │                      │     localStorage    │                     │
 │                      │                     │                     │
 │  9. Redirect to app  │                     │                     │
 │<─────────────────────│                     │                     │
```

### Protected Request Flow

```
User                 Frontend              Backend
 │                      │                     │
 │  1. Access /picks    │                     │
 │─────────────────────>│                     │
 │                      │  2. GET /picks      │
 │                      │     Authorization:  │
 │                      │     Bearer <token>  │
 │                      │────────────────────>│
 │                      │                     │  3. Validate JWT
 │                      │                     │     Extract user_id
 │                      │                     │
 │                      │  4. Return data     │
 │                      │<────────────────────│
 │  5. Display picks    │                     │
 │<─────────────────────│                     │
```

## Components and Interfaces

### Backend API Endpoints

#### POST /api/v1/auth/login

Authenticate user and return JWT token.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "username",
    "display_name": "Display Name"
  }
}
```

**Error Responses:**

- 401: Invalid credentials
- 422: Validation error (missing fields)
- 500: Server error

#### POST /api/v1/auth/logout

Logout endpoint (client-side token removal, server can add token blacklist later).

**Response (200 OK):**

```json
{
  "message": "Logged out successfully"
}
```

#### GET /api/v1/auth/me

Get current authenticated user information.

**Headers:**

```
Authorization: Bearer <token>
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "display_name": "Display Name",
  "is_active": true
}
```

**Error Responses:**

- 401: Invalid or missing token

### Backend Service Methods

#### AuthService

```python
class AuthService:
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> User | None:
        """
        Verify email and password, return user if valid.
        Returns None if authentication fails.
        """

    async def create_access_token(
        self,
        user_id: UUID,
        expires_delta: timedelta = timedelta(hours=24)
    ) -> str:
        """
        Generate JWT access token with user_id and expiration.
        """

    async def get_current_user(
        self,
        token: str
    ) -> User | None:
        """
        Validate token and return user.
        Returns None if token is invalid or expired.
        """
```

### Frontend Components

#### LoginForm Component

```typescript
interface LoginFormProps {
  onSuccess?: () => void;
}

function LoginForm({ onSuccess }: LoginFormProps) {
  // Form state: email, password, loading, error
  // Handle form submission
  // Call login API
  // Store token on success
  // Redirect to intended destination
}
```

#### Auth Store (Zustand)

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUserFromToken: () => Promise<void>;
  setUser: (user: User) => void;
}
```

#### ProtectedRoute Component

```typescript
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) return <LoadingSpinner />;

  if (!isAuthenticated) {
    // Save intended destination
    return <Navigate to="/login" state={{ from: location }} />;
  }

  return <>{children}</>;
}
```

### API Client Configuration

```typescript
// Axios interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Axios interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

## Data Models

### User Model (Existing - Enhanced)

```python
class User(Base):
    __tablename__ = "users"

    id: UUID (PK)
    email: str (unique, indexed)
    username: str (unique, indexed)
    hashed_password: str  # bcrypt hash
    display_name: str (nullable)
    is_active: bool (default=True)

    created_at: datetime
    updated_at: datetime (nullable)

    # WebAuthn fields (for future enhancement)
    webauthn_credential_id: str (nullable)
    webauthn_public_key: str (nullable)
```

**Note**: The User model already exists. We just need to ensure `hashed_password` field is present and properly used.

### JWT Token Payload

```json
{
  "sub": "user-uuid", // Subject (user ID)
  "exp": 1234567890, // Expiration timestamp
  "iat": 1234567890, // Issued at timestamp
  "type": "access" // Token type
}
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property Reflection

After analyzing all acceptance criteria, I've identified the following consolidations:

- **Properties 1.1, 1.2, 1.3** can be combined into a comprehensive "successful login" property
- **Properties 1.4, 1.5** can be combined into a single "invalid credentials rejection" property
- **Properties 2.1, 2.2, 2.3** are UI-specific examples that don't need separate properties
- **Properties 3.2, 4.1, 4.2, 4.3** are UI behavior examples
- **Properties 5.1, 5.2, 5.3** are UI error display examples
- **Properties 6.1, 6.2, 6.3** can be combined into token expiration properties
- **Properties 7.1-7.4** are UI rendering/behavior examples
- **Properties 8.1, 8.2, 8.3** cover password hashing comprehensively
- **Properties 9.1-9.3** are UI redirect examples

After consolidation, here are the unique correctness properties:

### Property 1: Successful login returns valid token

_For any_ user with valid credentials (existing email and correct password), logging in should return a JWT token that contains the user's ID and has a valid expiration time.
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Invalid credentials are rejected

_For any_ login attempt with either a non-existent email or incorrect password, the system should reject the login and return an authentication error.
**Validates: Requirements 1.4, 1.5**

### Property 3: Valid tokens grant access

_For any_ valid JWT token, requests to protected endpoints should be accepted and the user ID should be correctly extracted from the token.
**Validates: Requirements 3.1, 3.3**

### Property 4: Invalid tokens are rejected

_For any_ invalid, malformed, or expired JWT token, requests to protected endpoints should be rejected with an authentication error.
**Validates: Requirements 2.4, 3.4**

### Property 5: Token expiration is enforced

_For any_ JWT token, the expiration time should be set to 24 hours from creation, and tokens past their expiration should be rejected during validation.
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 6: Passwords are securely hashed

_For any_ password stored in the database, it should be hashed using bcrypt, and the plaintext password should never be stored or logged.
**Validates: Requirements 8.1, 8.3**

### Property 7: Password verification works correctly

_For any_ user with a stored password hash, verifying the correct password should succeed, and verifying an incorrect password should fail.
**Validates: Requirements 8.2**

### Property 8: Token contains correct user ID

_For any_ generated JWT token, decoding the token should yield the same user ID that was used to create it.
**Validates: Requirements 1.2, 3.3**

## Error Handling

### Authentication Errors

**Invalid Credentials:**

- Return HTTP 401 with message: "Invalid email or password"
- Do not reveal whether email or password was incorrect (security)

**Missing Credentials:**

- Return HTTP 422 with message: "Email and password are required"

**Inactive User:**

- Return HTTP 401 with message: "Account is inactive"

### Token Errors

**Missing Token:**

- Return HTTP 401 with message: "Authentication required"

**Invalid Token:**

- Return HTTP 401 with message: "Invalid authentication token"

**Expired Token:**

- Return HTTP 401 with message: "Authentication token has expired"

**Malformed Token:**

- Return HTTP 401 with message: "Invalid authentication token"

### Frontend Error Handling

**Network Errors:**

- Display: "Unable to connect. Please check your internet connection."

**Server Errors (500):**

- Display: "Something went wrong. Please try again later."

**Validation Errors:**

- Display field-specific errors inline

## Testing Strategy

### Unit Testing

Unit tests will cover specific examples and edge cases:

**Login:**

- Login with valid credentials
- Login with non-existent email
- Login with wrong password
- Login with inactive user
- Login with missing email
- Login with missing password

**Token Generation:**

- Generate token for valid user
- Verify token contains user ID
- Verify token has correct expiration

**Token Validation:**

- Validate valid token
- Validate expired token
- Validate malformed token
- Validate token with invalid signature

**Password Hashing:**

- Hash password and verify it's different from plaintext
- Verify correct password against hash
- Verify incorrect password fails against hash

### Property-Based Testing

Property-based tests will verify universal properties across many random inputs using **Hypothesis** (Python property-based testing library). Each test will run a minimum of 100 iterations with randomly generated data.

**Test Configuration:**

```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Test implementation
```

**Data Generators:**

```python
# Generate random emails
email_strategy = st.emails()

# Generate random passwords
password_strategy = st.text(min_size=8, max_size=72)

# Generate random UUIDs
uuid_strategy = st.uuids()

# Generate random user data
user_data = st.builds(
    dict,
    email=email_strategy,
    username=st.text(min_size=3, max_size=50),
    password=password_strategy
)
```

**Property Test Examples:**

```python
@settings(max_examples=100)
@given(
    email=st.emails(),
    password=st.text(min_size=8, max_size=72),
    username=st.text(min_size=3, max_size=50)
)
async def test_property_1_successful_login_returns_valid_token(
    email, password, username, auth_service, db_session
):
    """
    Feature: basic-authentication, Property 1: Successful login returns valid token
    For any user with valid credentials, logging in should return a JWT token
    that contains the user's ID and has a valid expiration time.
    """
    # Setup: Create user with known password
    user = await create_test_user(db_session, email, username, password)

    # Action: Authenticate with correct credentials
    authenticated_user = await auth_service.authenticate_user(email, password)

    # Assert: Authentication succeeds
    assert authenticated_user is not None
    assert authenticated_user.id == user.id

    # Action: Generate token
    token = await auth_service.create_access_token(user.id)

    # Assert: Token is valid and contains user ID
    assert token is not None
    payload = decode_access_token(token)
    assert payload is not None
    assert UUID(payload["sub"]) == user.id
    assert "exp" in payload
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()
```

### Integration Testing

Integration tests will verify end-to-end workflows:

- Complete login flow (POST /login → store token → access protected route)
- Token refresh on page load
- Logout flow (clear token → redirect → cannot access protected routes)
- 401 error handling and redirect to login

### Frontend Testing

Frontend tests will verify UI behavior:

- Login form renders correctly
- Form validation works
- Loading states display
- Error messages display
- Successful login redirects
- Token is stored in localStorage
- Logout clears token and redirects

## Security Considerations

### Password Security

- **Hashing**: Use bcrypt with appropriate work factor (12 rounds minimum)
- **No Plaintext**: Never store or log plaintext passwords
- **Timing Attacks**: Use constant-time comparison for password verification
- **Password Requirements**: Enforce minimum length (8 characters) in validation

### Token Security

- **Signing**: Use HS256 algorithm with strong secret key
- **Expiration**: Set reasonable expiration (24 hours)
- **Claims**: Include only necessary claims (user_id, expiration)
- **Validation**: Always validate signature and expiration
- **Storage**: Store in localStorage (acceptable for this use case)

### API Security

- **HTTPS**: Require HTTPS in production
- **CORS**: Configure appropriate CORS policies
- **Rate Limiting**: Implement rate limiting on login endpoint (future enhancement)
- **Brute Force Protection**: Add account lockout after failed attempts (future enhancement)

### Error Messages

- **Generic Errors**: Don't reveal whether email exists
- **No Information Leakage**: Use same error for invalid email and invalid password
- **Logging**: Log authentication failures for security monitoring

## Performance Considerations

### Database Queries

- Index on `users.email` for fast lookup
- Index on `users.username` for fast lookup
- Use connection pooling for database connections

### Token Operations

- JWT signing/verification is fast (< 1ms)
- Cache user lookups if needed (future optimization)

### Frontend Performance

- Lazy load login form component
- Debounce form validation
- Show loading states immediately

## Deployment Considerations

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Password Hashing
BCRYPT_ROUNDS=12
```

### Database Migration

No new tables needed. User model already exists. Ensure `hashed_password` field is present:

```python
def upgrade():
    # Add hashed_password column if it doesn't exist
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))
```

### Backward Compatibility

- Existing users without passwords will need to set passwords
- Can add password reset flow later
- WebAuthn fields already exist for future enhancement

### Monitoring

- Track login success/failure rates
- Monitor token validation errors
- Alert on unusual authentication patterns
- Log authentication events for security audit

## Future Enhancements

### Phase 2 Features

- Password reset via email
- "Remember me" option (longer token expiration)
- Refresh tokens for extended sessions
- Multi-factor authentication (MFA)
- WebAuthn/Passkey support
- Magic link authentication
- Social login (Google, GitHub)

### Security Enhancements

- Token blacklist for logout
- Account lockout after failed attempts
- Rate limiting on login endpoint
- CAPTCHA for brute force protection
- Session management (view/revoke active sessions)

### User Experience

- "Stay logged in" checkbox
- Password strength indicator
- Show/hide password toggle
- Auto-focus on email field
- Remember last logged-in email
