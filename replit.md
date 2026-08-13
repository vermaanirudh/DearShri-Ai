# DearShri-AI

DearShri-AI is a Python FastAPI service foundation with health checks and interactive API documentation.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `python -m uvicorn app.main:app --app-dir dearshri-ai --reload` — run DearShri-AI locally
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `dearshri-ai/app/main.py` — FastAPI application and service endpoints
- `dearshri-ai/requirements.txt` — Python runtime dependencies
- `dearshri-ai/README.md` — DearShri-AI usage notes and endpoint overview

## Architecture decisions

- DearShri-AI is kept as a standalone Python service rather than being coupled to the existing TypeScript API server.
- The workflow uses `PORT` when provided and defaults to port `8000` for local runs.

## Product

- Returns a service welcome response from `/`.
- Reports service health and a UTC timestamp from `/health`.
- Provides generated interactive OpenAPI docs at `/docs`.

## User preferences

No additional preferences recorded.

## Gotchas

- Run the DearShri-AI workflow or launch Uvicorn with `dearshri-ai` as the app directory.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
