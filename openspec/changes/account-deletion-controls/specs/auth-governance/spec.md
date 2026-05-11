## ADDED Requirements

### Requirement: Admin account deletion is password-gated and target-limited

CarbonRag SHALL allow administrators to delete non-admin user accounts only after verifying the current administrator password.

#### Scenario: Admin deletes selected normal users
- **WHEN** an administrator submits selected non-admin user IDs with the current password
- **THEN** CarbonRag deletes those user accounts and invalidates their auth sessions

#### Scenario: Admin attempts to delete self or another admin
- **WHEN** an administrator deletion request includes the current administrator account or any administrator account
- **THEN** CarbonRag rejects the request and does not delete those accounts

### Requirement: Self account cancellation is password-gated

CarbonRag SHALL allow an authenticated user to cancel their own account only after verifying the current password.

#### Scenario: User cancels own account
- **WHEN** a user submits the current password to cancel their own account
- **THEN** CarbonRag deletes that account, invalidates auth sessions, and clears the current session cookie

#### Scenario: User provides the wrong password
- **WHEN** a user submits an incorrect current password for account cancellation
- **THEN** CarbonRag rejects the request and keeps the account active
