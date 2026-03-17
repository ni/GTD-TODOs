# GTD TODOs

GTD TODOs is a local-first task application for a single laptop user. The MVP is intentionally small: FastAPI serves HTML pages, SQLite persists data, and the app is designed around GTD task states, optional due dates, recurring tasks, Markdown notes, and simple project organization.

![GTD TODOs logo](docs/gtd-todos-logo.png)

## Local Python Setup

1. Create and activate a Python 3.12 environment.
2. Install the project with development dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

3. Run the app locally.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The default database URL is `sqlite:////data/todo.db`. For local development outside Docker, set `DATABASE_URL` to a writable path such as `sqlite:///./data/todo.db`.

## Docker Compose

Start the app with a persistent named volume mounted at `/data`:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

The application listens on `http://localhost:8080`.

## Backup and Restore

The SQLite database file is stored in the Docker volume at `/data/todo.db`. Back it up by copying the file or using the export endpoints:

```bash
# Copy the database file directly
docker compose cp todo-app:/data/todo.db ./backup-todo.db

# Or export data as CSV / JSON
curl -o tasks.csv http://localhost:8080/export/tasks.csv
curl -o projects.json http://localhost:8080/export/projects.json
```

To restore, copy the backup into the running container and restart:

```bash
docker compose down
docker compose cp ./backup-todo.db todo-app:/data/todo.db
docker compose up
```

If the container is not available for `docker compose cp`, you can copy
directly into the named volume's mount point on the host:

```bash
# Find the volume's mount point
docker volume inspect gtd-todos_todo_app_data --format '{{ .Mountpoint }}'

# Copy the backup there (may require sudo on Linux)
sudo cp ./backup-todo.db "$(docker volume inspect gtd-todos_todo_app_data --format '{{ .Mountpoint }}')/todo.db"
```

See [docs/api.md](docs/api.md) for full export endpoint documentation.

## Developer Commands

Run tests:

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

Build the container image:

```bash
docker build .
```

## Project Structure

- `app/`: FastAPI app, routes, SQLModel models, Markdown helpers, templates, and static assets.
- `tests/`: test coverage for app import, page rendering, health checks, SQLite initialization, GTD workflow routes, and service-layer logic.
- `docs/`: human-readable API and agent-integration documentation.
- `.github/`: Copilot instructions, skills, and CI workflow.
- `scripts/`: repository bootstrap helpers.

## Documentation

- [docs/api.md](docs/api.md)
- [docs/llm-integration.md](docs/llm-integration.md)
- [.github/skills/todo-api/SKILL.md](.github/skills/todo-api/SKILL.md)
- [.github/skills/todo-data-model/SKILL.md](.github/skills/todo-data-model/SKILL.md)