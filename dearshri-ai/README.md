# DearShri AI

A FastAPI backend foundation for DearShri AI, including one-time passcode
authentication, a sequential 250-question journey, empathetic insights, and
JSON-backed memories and admin inbox storage.

## Run locally

From the project root:

```bash
python -m uvicorn app.main:app --app-dir dearshri-ai --reload
```

The API is available at:

- `GET /` — service welcome response
- `GET /health` — health status and timestamp
- `POST /auth/login` — consume the one-time passcode and create a session
- `POST /auth/verify-admin` — verify the admin secret
- `GET /journey/status` — read progress using `X-Session-Token`
- `POST /journey/answer` — submit the next sequential answer
- `GET /journey/admin-inbox` — read forwarded answers using `X-Admin-Secret`
- `/docs` — interactive OpenAPI documentation

Journey answer requests use this shape:

```json
{
  "question_number": 1,
  "answer": "I love quiet mornings."
}
```

The one-time passcode is consumed on the first successful login. Once question
250 is submitted, the journey is marked complete and locked.

The app uses the `PORT` environment variable when launched by the Replit workflow, falling back to port `8000`.