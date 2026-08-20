---
wave: 2
depends_on: ["1-01"]
files_modified:
  - app/core/security.py
  - app/api/deps.py
  - app/api/auth.py
  - app/schemas/auth.py
  - app/main.py
autonomous: true
requirements: REQ-SEC-01
---

# Plan 2: Authentication & Security

## Objective
Implement JWT-based authentication with role-based access control (RBAC) and bcrypt password hashing.

## Must Haves
- truths:
  - Passwords hashed using bcrypt with cost factor 12.
  - JWT access tokens expire in 30 minutes, refresh tokens in 7 days.
  - Roles defined: RM, MANAGER, ADMIN, CREDIT_APPROVER.

## Tasks

### 1. Password Hashing & Token Utilities
- **`<read_first>`**: `app/core/security.py`, `app/core/config.py`
- **`<action>`**: Implement `get_password_hash` and `verify_password` using `passlib` (bcrypt, cost=12). Implement `create_access_token` and `create_refresh_token` using `python-jose`, signing with `JWT_SECRET`.
- **`<acceptance_criteria>`**: `pytest` passes for a simple hashing and token issuance test.

### 2. Authentication Schemas
- **`<read_first>`**: `app/schemas/auth.py`
- **`<action>`**: Create Pydantic schemas for `Token` (access_token, refresh_token, token_type) and `TokenPayload` (sub, role). Create `UserCreate` and `UserLogin` schemas.
- **`<acceptance_criteria>`**: Schemas validate correctly with Pydantic.

### 3. Dependency Injection (RBAC)
- **`<read_first>`**: `app/api/deps.py`, `app/db/session.py`
- **`<action>`**: Create a FastAPI dependency `get_current_user` that extracts the JWT token, decodes it, and retrieves the User from the DB. Create a factory `get_current_active_user` and `RoleChecker` class to enforce required roles on routes.
- **`<acceptance_criteria>`**: A dummy protected route returns 401/403 when unauthenticated or lacking required roles.

### 4. Auth Endpoints
- **`<read_first>`**: `app/api/auth.py`, `app/main.py`
- **`<action>`**: Implement `/api/auth/login` (generates access and refresh tokens), `/api/auth/me` (returns current user profile), and `/api/auth/refresh` (issues new access token). Register the `auth_router` in `app/main.py`.
- **`<acceptance_criteria>`**: `POST /api/auth/login` returns a valid JWT structure for seeded credentials.

## Verification
- Test login with correct and incorrect passwords.
- Test endpoint authorization using a role that does not have access.
