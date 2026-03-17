# GTD TODOs Copilot Instructions

## Working Model

- Implement one phase at a time from `docs/TODO-App-Implementation-Plan.md`.
- Follow test-driven development for every feature and change.
- Start a new conversation from current code, tests, docs, and `.github` assets instead of relying on previous chat history.

## Canonical Commands

Install development dependencies:

```bash
pip install -e .[dev]
```

Run the test suite:

```bash
pytest
```

Run lint checks:

```bash
ruff check .
```

Run type checks:

```bash
mypy app
```

Run the app locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

Build the image:

```bash
docker build .
```

Start the compose stack:

```bash
docker compose up --build
```

## Architecture Constraints

- Backend: FastAPI on Python 3.12.
- UI: server-rendered Jinja templates with small HTMX interactions when needed.
- Persistence: SQLite, with the canonical persistent path under `/data` in Docker.
- Domain rule: recurring tasks remain single persistent task records whose `due_date` advances on completion.
- Notes rule: task notes are stored as raw Markdown and rendered as safe HTML.

## Documentation Expectations

- Keep `README.md`, `docs/`, and `.github/skills/` synchronized with behavior.
- Treat `.github` assets as part of the product surface for future agent sessions.