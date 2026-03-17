# TODO API Skill

Use this skill when interacting with the running GTD TODOs application over HTTP.

## Base Assumptions

- Local Docker Compose URL: `http://localhost:8080`
- Health endpoint: `GET /health`
- Current landing page: `GET /`

## Startup Checklist

1. Start the app with `docker compose up --build` or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`.
2. Verify reachability with `GET /health`.
3. Expect JSON `{"status": "ok"}` from the health route.

## Route Conventions

- HTML page routes return server-rendered responses.
- Mutation routes will be added in later phases and documented in `docs/api.md`.
- SQLite persistence uses the database URL configured in `DATABASE_URL`.

## Troubleshooting

- If the app is unreachable, confirm the container or local process is running.
- If database startup fails, verify that the SQLite target directory is writable.
- If behavior changes, update `docs/api.md` and this skill file together.