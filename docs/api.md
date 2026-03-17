# API Overview

## Page Routes

- `GET /`: Redirects to `/inbox`.
- `GET /inbox`: Inbox page showing tasks with `inbox` status and a quick-add form.
- `GET /tasks/{task_id}/edit`: Edit form for a single task.

## Mutation Routes

- `POST /tasks`: Create a new task (defaults to `inbox` status). Redirects to `/inbox`.
- `POST /tasks/{task_id}/update`: Update task fields from the edit form. Redirects to `/inbox`.
- `POST /tasks/{task_id}/complete`: Complete a task. Non-recurring tasks move to `done`; recurring tasks advance `due_date`. Redirects to `/inbox`.
- `POST /tasks/{task_id}/reopen`: Reopen a completed task back to `inbox`. Redirects to `/inbox`.

## Operational Routes

- `GET /health`: Returns JSON health status.

### `GET /health`

Response:

```json
{
  "status": "ok"
}
```

### `POST /tasks`

Form fields:

| Field | Required | Notes |
|---|---|---|
| `title` | Yes | Task title (empty titles are rejected) |

Redirects to `/inbox` on success.

### `POST /tasks/{task_id}/update`

Form fields:

| Field | Required | Notes |
|---|---|---|
| `title` | Yes | Task title |
| `notes` | No | Raw Markdown text |
| `status` | No | One of: `inbox`, `next_action`, `waiting_for`, `scheduled`, `someday_maybe`, `done` |
| `due_date` | No | ISO format date (`YYYY-MM-DD`) or empty to clear |
| `is_recurring` | No | Checkbox value (`on` when checked) |
| `recurrence_type` | No | One of: `daily`, `weekly`, `monthly`, `interval_days` |
| `recurrence_interval_days` | No | Integer, used with `interval_days` recurrence |
| `project_id` | No | Integer project ID or empty for no project |

Redirects to `/inbox` on success. Returns 404 if task not found.

### `POST /tasks/{task_id}/complete`

No form fields required. Redirects to `/inbox`. Returns 404 if task not found.

### `POST /tasks/{task_id}/reopen`

No form fields required. Redirects to `/inbox`. Returns 404 if task not found.

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

Future phases will expand this document with Today view, project detail pages, filtering, and HTMX partial behaviors.