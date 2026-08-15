# DearShri AI

A FastAPI backend for DearShri AI, including phone authentication, isolated
SQLite user records, a sequential journey, empathetic insights, chat history,
notices, and an admin dashboard API.

## Run locally

From the project root:

```bash
python -m uvicorn app.main:app --app-dir dearshri-ai --reload
```

The API is available at:

- `GET /` — service welcome response
- `GET /health` — health status and timestamp
- `POST /auth/login` — authenticate a phone number and create a persisted session
- `GET /auth/me` — read the authenticated user's isolated profile
- `POST /auth/logout` — explicitly revoke the current session
- `GET /auth/admin/daily-code` — read today's normal-user code as the admin only
- `GET /journey/status` — read progress using `X-Session-Token`
- `POST /journey/answer` — submit the next sequential answer
- `GET /journey/admin-inbox` — read all user responses using the admin session
- `POST /api/chat/message` — send a user-scoped message using `X-Session-Token`
- `GET /api/chat/history` — read only that user's chat history
- `DELETE /api/chat/history` — clear only that user's history
- `PATCH /api/chat/preferences` — update only that user's preferences
- `GET /api/notices/for-user` — read notices not dismissed by that user
- `POST /api/notices` — broadcast an admin-only notice
- `POST /api/notices/{notice_id}/dismiss` — dismiss a notice for one user
- `GET /admin/dashboard` — admin counts, published set, and current daily code
- `GET /admin/users` — user profiles and response summaries
- `GET /admin/journey-responses` — chronological user-wise responses
- `GET /admin/journey-sets` — list draft, published, and archived sets
- `POST /admin/journey-sets/draft` — create a draft question set
- `POST /admin/journey-sets/{id}/publish` — publish a draft and archive the old set
- `/docs` — interactive OpenAPI documentation

## Authentication rules

- `8303796575` is pre-seeded with the requested private profile and receives a
  persistent session until explicit logout.
- `9792836590` is the admin account and uses static code `2007`.
- Other users receive a server-generated six-digit code for the current India
  calendar day. The code is stored in `daily_codes` and is never returned by
  normal-user endpoints.
- Every normal user is created independently by phone number and never inherits
  the seeded profile.

## SQLite schema

The runtime database is created at `data/dearshri.sqlite3` and is ignored from
source control. On first startup it creates:

`users`, `sessions`, `daily_codes`, `journey_sets`, `journey_questions`,
`journey_responses`, `user_profiles`, `personality_traits`, `chat_messages`,
`user_preferences`, `system_notices`, and `notice_dismissals`.

Journey answer requests use this shape:

```json
{
  "question_number": 1,
  "answer": "I love quiet mornings."
}
```

Once the last question in the published journey set is submitted, that user's
journey is marked complete and locked. Publishing a new set does not mix
responses between users or between journey versions.

The app uses the `PORT` environment variable when launched by the Replit workflow, falling back to port `8000`.