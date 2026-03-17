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

## Companion Assets

- `.github/copilot-instructions.md`
- `.github/skills/todo-api/SKILL.md`
- `.github/skills/todo-data-model/SKILL.md`