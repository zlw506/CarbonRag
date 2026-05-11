# Change: Account Deletion Controls

## Summary

Add guarded account deletion controls for administrators and self-service account cancellation for normal users.

## Motivation

CarbonRag needs stronger account lifecycle controls before wider team usage:

- Administrators need to remove non-admin accounts from the admin user list.
- Batch deletion must not allow deleting the current account or other administrator accounts.
- Destructive account actions must require current-password verification.
- Users need a self-service account cancellation entry in general settings, also protected by current-password verification.

## Scope

- Backend auth/admin APIs for account deletion.
- Admin user list batch selection and deletion UX.
- General settings danger-zone self-cancellation UX.
- Regression tests for password verification and protected targets.

## Non-Goals

- Deleting administrator accounts.
- Deleting the currently logged-in admin from the admin panel.
- Full data erasure of historical sessions/reports in this round.
- External identity provider integration.
