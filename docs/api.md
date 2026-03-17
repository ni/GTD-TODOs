# API Overview

## Page Routes

- `GET /`: Returns the initial HTML landing page.

## Operational Routes

- `GET /health`: Returns JSON health status.

### `GET /health`

Response:

```json
{
  "status": "ok"
}
```

## Data Model

### Projects

| Column | Type | Notes |
|---|---|---|
| `id` | integer | Primary key, auto-generated |
| `name` | text | Required, unique |
| `description` | text | Optional |
| `created_at` | datetime | UTC timestamp |
| `updated_at` | datetime | UTC timestamp |
| `archived_at` | datetime | Optional, set when archived |

### Tasks

| Column | Type | Notes |
|---|---|---|
| `id` | integer | Primary key, auto-generated |
| `title` | text | Required |
| `notes` | text | Optional, raw Markdown |
| `status` | text | One of: `inbox`, `next_action`, `waiting_for`, `scheduled`, `someday_maybe`, `done` |
| `due_date` | date | Optional |
| `is_recurring` | boolean | Default `false` |
| `recurrence_type` | text | Optional: `daily`, `weekly`, `monthly`, `interval_days` |
| `recurrence_interval_days` | integer | Optional, used when `recurrence_type = interval_days` |
| `last_completed_at` | datetime | Set each time a recurring task is completed |
| `project_id` | integer | Optional foreign key to `projects.id` |
| `created_at` | datetime | UTC timestamp |
| `updated_at` | datetime | UTC timestamp |
| `completed_at` | datetime | Set when a non-recurring task is completed |

## Service Layer

### Project Operations

```python
create_project(session, name=..., description=...)  -> Project
get_project(session, project_id)                     -> Project | None
list_projects(session, include_archived=False)       -> list[Project]
update_project(session, project_id, name=..., description=...) -> Project | None
archive_project(session, project_id)                 -> Project | None
```

### Task Operations

```python
create_task(session, title=..., notes=..., status=..., due_date=...,
            is_recurring=..., recurrence_type=...,
            recurrence_interval_days=..., project_id=...) -> Task
get_task(session, task_id)                            -> Task | None
list_tasks(session, status=..., project_id=...)       -> list[Task]
update_task(session, task_id, **fields)               -> Task | None
complete_task(session, task_id)                        -> Task | None
reopen_task(session, task_id)                         -> Task | None
```

### Completion Behavior

- **Non-recurring tasks**: status moves to `done`, `completed_at` is set.
- **Recurring tasks**: `due_date` advances to the next occurrence, `last_completed_at` is set, status remains actionable (not `done`), `completed_at` stays `None`.

### Recurrence Advancement

| Type | Rule |
|---|---|
| `daily` | +1 day |
| `weekly` | +7 days |
| `monthly` | Same day next month (clamped to month end) |
| `interval_days` | +N days (from `recurrence_interval_days`) |

## Seed Data

Populate the database with sample data for local testing:

```bash
python -m app.seed
```

Future phases will expand this document with HTTP mutation routes, form payloads, and HTMX partial behaviors.