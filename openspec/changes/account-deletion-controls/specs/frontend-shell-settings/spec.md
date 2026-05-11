## ADDED Requirements

### Requirement: Admin user list exposes guarded batch deletion

CarbonRag SHALL let administrators batch-select deletable normal users from the admin user list while preventing selection of the current user and administrator accounts.

#### Scenario: Admin opens user management
- **WHEN** the admin user list is displayed
- **THEN** current-account and admin-account rows are not selectable for deletion

#### Scenario: Admin confirms batch deletion
- **WHEN** the administrator confirms selected user deletion
- **THEN** the UI requires the current account password before calling the deletion API

### Requirement: Settings exposes self account cancellation

CarbonRag SHALL provide a danger-zone control in general settings for users to cancel their own account after current-password verification.

#### Scenario: User cancels account from settings
- **WHEN** a user enters the current password and confirms account cancellation
- **THEN** the UI calls the self-cancellation API and returns to the unauthenticated state
