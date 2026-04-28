## Purpose
Defines the browser workbench shell, chat experience, settings page, theme preferences, and user-facing interaction states.

## Requirements

### Requirement: Frontend uses environment-specific API base
CarbonRag SHALL use local backend URLs in local development and `/api` in production builds.

#### Scenario: Production frontend calls API
- **WHEN** the frontend is built for production
- **THEN** API requests use the `/api/v1/...` proxy path

### Requirement: Protected workbench routes require authentication
CarbonRag SHALL prevent unauthenticated access to workbench pages.

#### Scenario: Anonymous user opens protected page
- **WHEN** no valid auth cookie exists
- **THEN** the frontend routes the user to the login flow
