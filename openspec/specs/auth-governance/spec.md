## Purpose
Defines identity, user ownership, role separation, admin governance APIs, and protected routes.

## Requirements

### Requirement: Authentication uses server-side cookie sessions
CarbonRag SHALL authenticate users through HttpOnly cookie-backed server-side sessions.

#### Scenario: User logs in successfully
- **WHEN** valid credentials are submitted
- **THEN** the backend creates an auth session and sets the session cookie

### Requirement: Admin access is role gated
CarbonRag SHALL restrict admin APIs and admin pages to users with the admin role.

#### Scenario: Normal user calls admin API
- **WHEN** a non-admin user requests an admin endpoint
- **THEN** the backend rejects the request with an authorization error
