# GTD TODOs

GTD TODOs is a local-first task application for a single laptop user. The MVP is intentionally small: FastAPI serves HTML pages, SQLite persists data, and the app is designed around GTD task states, optional due dates, recurring tasks, Markdown notes, and simple project organization.

![GTD TODOs logo](docs/gtd-todos-logo.png)

## Local Python Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (e.g. `brew install uv`).
2. Install the project with development dependencies.

```bash
uv sync
```

3. Run the app locally.

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The default database URL is `sqlite:////data/todo.db`. For local development outside Docker, set `DATABASE_URL` to a writable path such as `sqlite:///./data/todo.db`.

## Docker Compose

The compose stack requires `AUTH_SECRET_KEY`. Generate one and export it (or add it to a `.env` file next to `docker-compose.yml`):

```bash
# Generate a secret
python -c "import secrets; print(secrets.token_hex(32))"

# Export it (or add AUTH_SECRET_KEY=<value> to .env)
export AUTH_SECRET_KEY=<value>
```

Start the app with a persistent named volume mounted at `/data`:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

The container listens internally on port 8080 but is mapped to **port 8081** on the host: `http://localhost:8081`.

## Authentication

GTD TODOs supports single-user passkey (WebAuthn) authentication. On first visit a passkey is registered, and subsequent access requires authenticating with that passkey.

### Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `APP_HOST` | Bind address | `0.0.0.0` |
| `APP_PORT` | Listen port | `8080` |
| `DATABASE_URL` | SQLite connection string | `sqlite:////data/todo.db` |
| `TZ` | Container timezone | *(unset)* |
| `AUTH_DISABLED` | Disable auth entirely (for local dev / existing tests) | `false` |
| `AUTH_SECRET_KEY` | Secret for signing session cookies | *auto-generated* |
| `AUTH_SESSION_MAX_AGE` | Session cookie max age in seconds | `604800` (7 days) |
| `WEBAUTHN_RP_ID` | WebAuthn Relying Party ID (domain) | `localhost` |
| `WEBAUTHN_RP_NAME` | Human-readable RP name | `GTD TODOs` |
| `WEBAUTHN_ORIGIN` | Expected origin for WebAuthn ceremonies | `http://localhost:8080` |

### API Keys (Programmatic Access)

API keys allow CLI tools and scripts to access the API without a browser session. Generate keys from the Settings page (gear icon in the nav bar) after logging in with a passkey.

Use the key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer gtd_your_key_here" http://localhost:8080/export/tasks.json
```

Keys are shown in full once at creation time and stored as SHA-256 hashes. Up to 10 keys can be active. Revoke keys from the Settings page.

### Disabling Auth for Local Development

Set `AUTH_DISABLED=true` to skip all authentication:

```bash
AUTH_DISABLED=true uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### First-Run Setup

When no credentials exist in the database, visiting any page redirects to `/auth/setup` where you register a passkey. After setup, future visits go through the login flow at `/auth/login`.

## Backup and Restore

The SQLite database file is stored in the Docker volume at `/data/todo.db`. Back it up by copying the file or using the export endpoints:

```bash
# Copy the database file directly
docker compose cp todo-app:/data/todo.db ./backup-todo.db

# Or export data as CSV / JSON (use port 8081 for Docker Compose)
curl -o tasks.csv http://localhost:8081/export/tasks.csv
curl -o projects.json http://localhost:8081/export/projects.json
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
uv run pytest
```

Run lint checks:

```bash
uv run ruff check .
```

Run type checks:

```bash
uv run mypy app
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

## Documentation

- [docs/api.md](docs/api.md)
- [docs/llm-integration.md](docs/llm-integration.md)
- [.github/skills/todo-api/SKILL.md](.github/skills/todo-api/SKILL.md)
- [.github/skills/todo-data-model/SKILL.md](.github/skills/todo-data-model/SKILL.md)