# API Boundary Draft

Version: `V1.0.0`  
Status: `identity, isolation, and admin foundation`

## Global Rules
- `GET /healthz` stays public.
- `GET /api/v1/system/info` now requires authentication.
- All business resources are scoped to the authenticated user.
- Clients must never send `user_id`.
- Cross-user reads return `404`.
- Admin routes are prefixed with `/api/v1/admin/*` and require `role=admin`.

## Auth

### `POST /api/v1/auth/register`
Request:

```json
{
  "username": "trial_user",
  "password": "pass123456"
}
```

Notes:
- normal registration creates `role=user`
- `username=admin` is reserved for seed-admin recovery
- if the register request uses `admin / 123456`, the system restores the initial admin account and marks it `password_must_change=true`

Response:

```json
{
  "user": {
    "user_id": "string",
    "username": "trial_user",
    "role": "user",
    "is_active": true,
    "password_must_change": false,
    "created_at": "string",
    "updated_at": "string",
    "last_login_at": null
  }
}
```

### `POST /api/v1/auth/login`
Request:

```json
{
  "username": "trial_user",
  "password": "pass123456"
}
```

Response:

```json
{
  "user": {
    "user_id": "string",
    "username": "trial_user",
    "role": "user",
    "is_active": true,
    "password_must_change": false,
    "created_at": "string",
    "updated_at": "string",
    "last_login_at": "string | null"
  },
  "must_change_password": false
}
```

Notes:
- login writes `carbonrag_session` cookie
- cookie is `HttpOnly`, `SameSite=Lax`
- production uses `Secure=true`

### `POST /api/v1/auth/logout`
Response:

```json
{
  "status": "ok"
}
```

### `GET /api/v1/auth/me`
Response:

```json
{
  "user": {
    "user_id": "string",
    "username": "string",
    "role": "user | admin",
    "is_active": true,
    "password_must_change": false,
    "created_at": "string",
    "updated_at": "string",
    "last_login_at": "string | null"
  }
}
```

### `POST /api/v1/auth/change-password`
Request:

```json
{
  "current_password": "string",
  "new_password": "string"
}
```

Response:

```json
{
  "user": {
    "user_id": "string",
    "username": "string",
    "role": "user | admin",
    "is_active": true,
    "password_must_change": false,
    "created_at": "string",
    "updated_at": "string",
    "last_login_at": "string | null"
  },
  "must_change_password": false
}
```

## Session and Ask

### `POST /api/v1/sessions`
- requires auth
- creates a session owned by the current user

### `GET /api/v1/sessions`
- requires auth
- returns only the current user's sessions

### `GET /api/v1/sessions/{id}`
- requires auth
- returns only the current user's session detail
- returns `404` if the session belongs to another user

### `POST /api/v1/sessions/{id}/ask`
Request:

```json
{
  "question": "string",
  "knowledge_scope": "public | private_sample | mixed",
  "top_k": 5,
  "attached_file_ids": []
}
```

Response:

```json
{
  "answer": "string",
  "mode": "ask",
  "status": "ok | provider_error | invalid_input",
  "citations": [
    {
      "doc_id": "string",
      "title": "string",
      "source_type": "public_policy | private_sample",
      "source": "string",
      "source_url": "string | null",
      "snippet": "string",
      "chunk_id": "string"
    }
  ],
  "source_summary": {
    "knowledge_scope": "public | private_sample | mixed",
    "public_policy_count": 0,
    "private_sample_count": 0,
    "total_citation_count": 0
  },
  "trace_id": "string"
}
```

## Files and Private Samples

### `POST /api/v1/files`
- requires auth
- multipart upload
- uploaded file is bound to the current user's session

### `GET /api/v1/private-samples`
- requires auth
- returns current attachable catalog view

### `PUT /api/v1/sessions/{id}/attached-files/private-samples`
Request:

```json
{
  "doc_ids": ["enterprise_doc_001", "energy_bill_sample_001"]
}
```

- requires auth
- replaces the current user's attached private sample set for that session

## Calc Carbon

### `POST /api/v1/calc-carbon`
Request:

```json
{
  "session_id": "optional",
  "period_label": "2026-Q1",
  "electricity_kwh": 12000,
  "natural_gas_m3": 800,
  "diesel_l": 120
}
```

Response:

```json
{
  "status": "ok",
  "trace_id": "string",
  "total_emission_kgco2e": 12345.67,
  "breakdown": [
    {
      "item": "electricity",
      "activity_value": 12000,
      "activity_unit": "kWh",
      "factor_value": 0.57,
      "factor_unit": "kgCO2e/kWh",
      "emission_kgco2e": 6840.0,
      "factor_id": "string"
    }
  ],
  "formula_summary": "string",
  "citations": [
    {
      "factor_id": "string",
      "source": "string",
      "source_url": "string"
    }
  ]
}
```

## Feedback

### `POST /api/v1/feedback`
Request:

```json
{
  "target_type": "ask | calc_carbon",
  "trace_id": "string",
  "session_id": "optional",
  "rating": "up | down",
  "comment": "optional"
}
```

Response:

```json
{
  "status": "ok",
  "feedback_id": "string",
  "created_at": "string"
}
```

## Reports

### `POST /api/v1/reports`
Request:

```json
{
  "session_id": "string",
  "report_type": "policy_summary | mixed_analysis | carbon_summary",
  "title": "optional",
  "source_message_ids": [],
  "carbon_result_id": "optional",
  "output_format": "markdown"
}
```

Response:

```json
{
  "report_id": "string",
  "session_id": "string",
  "report_type": "policy_summary",
  "title": "string",
  "content": "markdown string",
  "output_format": "markdown",
  "citations": [],
  "source_summary": {
    "public_policy_count": 0,
    "private_sample_count": 0,
    "carbon_factor_count": 0,
    "total_citation_count": 0
  },
  "sources": [],
  "trace_id": "string",
  "created_at": "string",
  "updated_at": "string"
}
```

### `GET /api/v1/reports/{report_id}`
- requires auth
- returns only the current user's report

### `PATCH /api/v1/reports/{report_id}`
Request:

```json
{
  "title": "optional",
  "content": "updated markdown"
}
```

- requires auth
- updates only the current user's report

### `GET /api/v1/sessions/{id}/reports`
- requires auth
- returns only reports bound to the current user's session

### `GET /api/v1/sessions/{id}/carbon-calculations`
- requires auth
- returns only carbon calculation summaries bound to the current user's session

## Admin APIs

### `GET /api/v1/admin/system/status`
- admin only
- returns system metadata, total counts, and latest refresh status

### `GET /api/v1/admin/users`
- admin only
- returns user metadata only
- does not return ordinary users' session or report body content

### `PATCH /api/v1/admin/users/{user_id}`
Request:

```json
{
  "role": "user | admin",
  "is_active": true
}
```

### `POST /api/v1/admin/users/{user_id}/reset-password`
Response:

```json
{
  "status": "ok",
  "temporary_password": "string"
}
```

### `GET /api/v1/admin/feedback/overview`
- admin only
- returns aggregate counts and recent metadata only

### `GET /api/v1/admin/private-samples`
- admin only
- returns manifest plus override view

### `PATCH /api/v1/admin/private-samples/{doc_id}`
Request:

```json
{
  "is_enabled": true,
  "session_attachable": true
}
```

### `GET /api/v1/admin/knowledge-refresh-tasks`
- admin only

### `POST /api/v1/admin/knowledge-refresh-tasks`
Request:

```json
{
  "scope": "public_policy | private_sample | all"
}
```

Notes:
- refresh is synchronous in V1.0.0
- status transitions: `running -> succeeded | failed`
