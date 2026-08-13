# DearShri-AI

A FastAPI starter service for DearShri-AI.

## Run locally

From the project root:

```bash
python -m uvicorn app.main:app --app-dir dearshri-ai --reload
```

The API is available at:

- `GET /` — service welcome response
- `GET /health` — health status and timestamp
- `/docs` — interactive OpenAPI documentation

The app uses the `PORT` environment variable when launched by the Replit workflow, falling back to port `8000`.