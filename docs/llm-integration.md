# LLM Integration Guide

The repository includes `.github` customization assets so a new agent conversation can work from code and documentation instead of relying on prior chat state.

## Ground Rules

- Work phase-by-phase using test-driven development.
- Use the repository docs, tests, and `.github` assets as the source of truth.
- Keep API behavior, docs, and skill files synchronized.
- Preserve the architectural constraints: FastAPI, server-rendered pages, SQLite persistence, single-record recurring tasks, and Markdown notes rendered safely.

## Local App Assumptions

- Docker Compose starts the app on `http://localhost:8080`.
- The canonical persistent database path is `/data/todo.db` in the container.
- Health checks are available at `GET /health`.
- The home page (`GET /`) redirects to the inbox.

## Core Workflow Routes

- `GET /inbox` — inbox page with quick-add form.
- `POST /tasks` — create a task (form field: `title`).
- `GET /tasks/{id}/edit` — edit form for a task.
- `POST /tasks/{id}/update` — update task from edit form.
- `POST /tasks/{id}/complete` — complete a task.
- `POST /tasks/{id}/reopen` — reopen a completed task.

See `docs/api.md` for full route and form field documentation.

## Companion Assets

- `.github/copilot-instructions.md`
- `.github/skills/todo-api/SKILL.md`
- `.github/skills/todo-data-model/SKILL.md`