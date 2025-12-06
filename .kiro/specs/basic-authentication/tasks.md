# Implementation Plan: Basic Authentication

## Overview

This implementation plan transforms the Basic Authentication design into actionable coding tasks. The plan follows a bottom-up approach: starting with backend authentication logic (password hashing, JWT generation, login endpoint), then building frontend components (auth store, login form, protected routes), and finally integrating everything with proper error handling and testing.

## Tasks

- [x] 1. Implement backend authentication service

  - [x] 1.1 Enhance AuthService with password authentication

    - Update `backend/app/services/auth_service.py`
    - Implement `authenticate_user(email, password)` method
    - Query user by email
    - Verify password using bcrypt
    - Return user if valid, None if invalid
    - _Requirements: 1.1, 1.4, 1.5_

  - [x] 1.2 Implement JWT token generation

    - Update `backend/app/core/security.py`
    - Implement `create_access_token(user_id, expires_delta)` function
    - Set expiration to 24 hours by default
    - Include user_id in "sub" claim
    - Sign token with HS256 algorithm
    - _Requirements: 1.2, 6.1_

  - [x] 1.3 Write property test for successful login

    - **Property 1: Successful login returns valid token**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 1.4 Write property test for invalid credentials rejection

    - **Property 2: Invalid credentials are rejected**
    - **Validates: Requirements 1.4, 1.5**

  - [x] 1.5 Write property test for password hashing

    - **Property 6: Passwords are securely hashed**

    - **Validates: Requirements 8.1, 8.3**

  - [x] 1.6 Write property test for password verification

    - **Property 7: Password verification works correctly**
    - **Validates: Requirements 8.2**

- [x] 2. Create login API endpoint

  - [x] 2.1 Create login request/response schemas

    - Create `backend/app/schemas/auth.py`
    - Define LoginRequest schema (email, password)
    - Define LoginResponse schema (access_token, token_type, user)
    - Add validation for required fields
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 2.2 Implement POST /api/v1/auth/login endpoint

    - Update `backend/app/api/v1/endpoints/auth.py`
    - Accept LoginRequest body
    - Call AuthService.authenticate_user
    - Generate JWT token on success
    - Return LoginResponse with token and user info
    - Return 401 on invalid credentials
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.3 Implement GET /api/v1/auth/me endpoint

    - Add endpoint to get current user info
    - Require authentication (use get_current_user dependency)
    - Return user information
    - _Requirements: 3.1, 3.3_

  - [x] 2.4 Write unit tests for login endpoint

    - Test successful login with valid credentials
    - Test login failure with invalid email
    - Test login failure with invalid password
    - Test login with missing fields
    - _Requirements: 1.1, 1.4, 1.5_

- [x] 3. Enhance token validation

  - [x] 3.1 Update get_current_user dependency

    - Update `backend/app/api/dependencies.py`
    - Ensure token expiration is checked
    - Return proper error messages for different failure cases
    - _Requirements: 3.3, 3.4, 6.2, 6.3_

  - [x] 3.2 Write property test for valid token access

    - **Property 3: Valid tokens grant access**
    - **Validates: Requirements 3.1, 3.3**

  - [x] 3.3 Write property test for invalid token rejection

    - **Property 4: Invalid tokens are rejected**
    - **Validates: Requirements 2.4, 3.4**

  - [ ]\* 3.4 Write property test for token expiration

    - **Property 5: Token expiration is enforced**
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [x] 3.5 Write property test for token user ID

    - **Property 8: Token contains correct user ID**
    - **Validates: Requirements 1.2, 3.3**

- [x] 4. Create frontend auth store

  - [x] 4.1 Create auth store with Zustand

    - Create `frontend/src/stores/authStore.ts`
    - Define AuthState interface (user, token, isAuthenticated, isLoading)
    - Implement login action (call API, store token, set user)
    - Implement logout action (clear token, clear user, redirect)
    - Implement loadUserFromToken action (validate stored token)
    - _Requirements: 2.1, 2.2, 2.3, 4.1, 4.2, 4.3_

  - [x] 4.2 Create auth API client functions

    - Create `frontend/src/lib/api/auth.ts`
    - Implement login(email, password) function
    - Implement logout() function
    - Implement getCurrentUser() function
    - Add proper TypeScript types
    - _Requirements: 1.1, 4.1_

  - [x] 4.3 Create TypeScript types for auth

    - Create `frontend/src/types/auth.ts`
    - Define User type
    - Define LoginRequest type
    - Define LoginResponse type
    - Export types for use across components
    - _Requirements: 1.3_

- [x] 5. Update API client with auth interceptors

  - [x] 5.1 Add request interceptor for auth token

    - Update `frontend/src/lib/api.ts`
    - Add interceptor to include Authorization header
    - Get token from localStorage
    - Add "Bearer <token>" to all requests
    - _Requirements: 3.2_

  - [x] 5.2 Add response interceptor for 401 errors

    - Add interceptor to handle 401 responses
    - Clear token from localStorage on 401
    - Redirect to login page
    - Clear auth store state
    - _Requirements: 2.4, 3.4_

- [x] 6. Create login form component

  - [x] 6.1 Create LoginForm component

    - Create `frontend/src/features/auth/components/LoginForm.tsx`
    - Add email and password input fields
    - Add form validation (required fields, email format)
    - Handle form submission
    - Show loading state during login
    - Display error messages
    - Disable submit button while loading
    - _Requirements: 7.1, 7.2, 7.3, 5.1, 5.2, 5.3_

  - [x] 6.2 Implement redirect after login

    - Get intended destination from location state
    - Redirect to intended destination on success
    - Default to /picks if no destination
    - _Requirements: 7.4, 9.1, 9.2, 9.3_

  - [x] 6.3 Add error handling to login form

    - Display validation errors inline
    - Display authentication errors from API
    - Display network errors
    - Clear errors on retry
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 7. Update ProtectedRoute component

  - [x] 7.1 Enhance ProtectedRoute with auth store

    - Update `frontend/src/routes/ProtectedRoute.tsx`
    - Use auth store instead of localStorage check
    - Show loading spinner while checking auth
    - Save intended destination in location state
    - Redirect to login if not authenticated
    - _Requirements: 3.1, 9.1_

  - [x] 7.2 Add token validation on app load

    - Update `frontend/src/App.tsx`
    - Call loadUserFromToken on mount
    - Validate stored token with backend
    - Clear invalid tokens
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 8. Add logout functionality

  - [x] 8.1 Add logout button to header

    - Update `frontend/src/components/layout/Header.tsx`
    - Add logout button (visible when authenticated)
    - Call auth store logout action
    - Show user info (username/email)
    - _Requirements: 4.1, 4.2_

  - [x] 8.2 Implement logout action

    - Ensure logout clears localStorage
    - Ensure logout clears auth store state
    - Ensure logout redirects to login page
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 9. Add error handling and user feedback

  - [x] 9.1 Create error handling utilities

    - Create `frontend/src/lib/auth-errors.ts`
    - Parse authentication error responses
    - Map error codes to user-friendly messages
    - Export error handling functions
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 9.2 Add toast notifications for auth events

    - Show success toast on login
    - Show error toast on login failure
    - Show info toast on logout
    - Show error toast on session expiration
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 10. Checkpoint - Ensure all tests pass

  - Run all property-based tests
  - Run all unit tests
  - Test login flow manually
  - Test logout flow manually
  - Test protected routes manually
  - Ensure all tests pass, ask the user if questions arise

- [x] 11. Integration testing and polish

  - [x] 11.1 Test complete login flow

    - Login with valid credentials
    - Verify token is stored
    - Verify redirect works
    - Access protected route
    - Verify API calls include token
    - _Requirements: 1.1, 2.1, 3.1, 3.2_

  - [x] 11.2 Test logout flow

    - Logout from authenticated state
    - Verify token is cleared
    - Verify redirect to login
    - Verify cannot access protected routes
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 11.3 Test token expiration handling

    - Create expired token
    - Attempt to access protected route
    - Verify redirect to login
    - Verify token is cleared
    - _Requirements: 2.4, 6.2_

  - [x] 11.4 Test error scenarios

    - Test with invalid credentials
    - Test with network errors
    - Test with server errors
    - Verify appropriate error messages
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 11.5 Test redirect after login

    - Navigate to protected route while logged out
    - Login successfully
    - Verify redirect to original destination
    - Test default redirect when no destination
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 11.6 Test session persistence

    - Login successfully
    - Refresh page
    - Verify still authenticated
    - Verify user info is loaded
    - _Requirements: 2.1, 2.2, 2.3_

## Implementation Notes

### Backend Implementation

- The User model already exists with `hashed_password` field
- The `get_current_user` dependency already exists and validates JWT tokens
- We need to implement the password authentication logic in AuthService
- We need to create the login endpoint that ties everything together

### Frontend Implementation

- The ProtectedRoute component exists but needs enhancement
- We need to create a proper auth store to manage authentication state
- The login form component needs to be created from scratch
- API interceptors need to be added for automatic token inclusion

### Testing Strategy

- Property-based tests will validate core authentication logic
- Unit tests will cover specific scenarios and edge cases
- Integration tests will verify end-to-end flows
- Manual testing will ensure good user experience

### Security Considerations

- Never log plaintext passwords
- Use bcrypt for password hashing (already configured)
- Validate token expiration on every request
- Use HTTPS in production
- Implement rate limiting later as enhancement

## Estimated Effort

- Backend authentication: 1-2 hours
- Frontend auth store and API client: 1 hour
- Login form component: 1-2 hours
- Protected routes and redirects: 1 hour
- Testing and polish: 1-2 hours

**Total: 5-8 hours**

## Success Criteria

✅ Users can log in with email/password
✅ JWT tokens are generated and validated
✅ Tokens are stored in localStorage
✅ Protected routes require authentication
✅ Users can log out
✅ Sessions persist across page refreshes
✅ Expired tokens are handled gracefully
✅ Error messages are user-friendly
✅ All property-based tests pass
✅ All unit tests pass
