# TODO API Skill

Use this skill when interacting with the running GTD TODOs application over HTTP.

## Base Assumptions

- Local Docker Compose URL: `http://localhost:8080`
- Health endpoint: `GET /health`
- Landing page redirects to: `GET /inbox`

## Startup Checklist

1. Start the app with `docker compose up --build` or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`.
2. Verify reachability with `GET /health`.
3. Expect JSON `{"status": "ok"}` from the health route.

## Page Routes

- `GET /` redirects to `/inbox`.
- `GET /inbox` shows inbox tasks with a quick-add form.
- `GET /tasks/{task_id}/edit` shows the task edit form.

## Mutation Routes

- `POST /tasks` creates a task (form field: `title`). Redirects to `/inbox`.
- `POST /tasks/{task_id}/update` updates a task from the edit form. Redirects to `/inbox`.
- `POST /tasks/{task_id}/complete` completes a task. Redirects to `/inbox`.
- `POST /tasks/{task_id}/reopen` reopens a task to inbox. Redirects to `/inbox`.

See `docs/api.md` for full form field specifications.

## General Conventions

- HTML page routes return server-rendered responses.
- Mutation routes accept form-encoded POST data and redirect on success.
- Not-found resources return HTTP 404.
- SQLite persistence uses the database URL configured in `DATABASE_URL`.

## Troubleshooting

- If the app is unreachable, confirm the container or local process is running.
- If database startup fails, verify that the SQLite target directory is writable.
- If behavior changes, update `docs/api.md` and this skill file together.