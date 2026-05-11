# Design

## Backend

Use existing `AuthService` as the account lifecycle boundary.

- Admin endpoint: `DELETE /api/v1/admin/users`
- Self endpoint: `DELETE /api/v1/auth/me`
- Both endpoints accept `current_password`.
- Admin endpoint also accepts `user_ids`.

Deletion rules:

- The current user must pass password verification.
- Admin batch deletion rejects empty selections.
- Admin batch deletion rejects the current account.
- Admin batch deletion rejects any target whose role is `admin`.
- Successful deletion removes target auth sessions and user rows.
- Self cancellation removes the user's auth sessions and user row, then clears the cookie.

## Frontend

Admin user list:

- Add row selection.
- Disable selection for the current user and admin users.
- Batch delete button opens a password confirmation modal.
- After success, refresh users and system status.

Settings page:

- Add danger-zone card under data/privacy.
- User enters current password to cancel their own account.
- After success, client logs out locally and redirects through protected-route behavior.

## Data Retention

This round removes account login capability. Historical content rows are not hard-deleted in this change to avoid cascading data loss across sessions, reports, feedback, and RAG artifacts. Follow-up data-erasure policy can be defined separately.
