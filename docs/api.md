# API Overview

## Page Routes

- `GET /`: Redirects to `/inbox`.
- `GET /inbox`: Inbox page showing tasks with `inbox` status and a quick-add form.
- `GET /today`: Today page showing overdue tasks and tasks due today.
- `GET /projects`: Projects list showing all non-archived projects with task counts.
- `GET /projects/{project_id}`: Project detail page with tasks grouped by GTD status.
- `GET /tasks`: All tasks page with filtering and search.
- `GET /tasks/{task_id}/edit`: Edit form for a single task.

## Mutation Routes

- `POST /tasks`: Create a new task (defaults to `inbox` status). Accepts optional `project_id` for project quick-add. Redirects back to the referring page.
- `POST /tasks/{task_id}/update`: Update task fields from the edit form. Redirects to `/inbox`.
- `POST /tasks/{task_id}/complete`: Complete a task. Non-recurring tasks move to `done`; recurring tasks advance `due_date`. Redirects back to the referring page.
- `POST /tasks/{task_id}/reopen`: Reopen a completed task back to `inbox`. Redirects back to the referring page.
- `POST /projects`: Create a new project. Redirects to `/projects`.

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

### `POST /projects`

Form fields:

| Field | Required | Notes |
|---|---|---|
| `name` | Yes | Project name (empty names are ignored) |

Redirects to `/projects` on success.

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
search_tasks(session, status=..., project_id=...,
             no_project=..., q=..., has_due_date=...,
             is_recurring=...)                         -> list[Task]
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

Future phases will expand this document with filtering, search, and HTMX partial behaviors.

---

## Today View

### `GET /today`

Displays two sections:

1. **Overdue** — Tasks whose `due_date` is before today and `status` is not `done`. Sorted by `due_date` ascending, then `created_at`.
2. **Due Today** — Tasks whose `due_date` equals today and `status` is not `done`. Sorted by `created_at`.

Recurring tasks whose next due date is today appear alongside one-time tasks. Tasks without a due date do not appear. Done tasks are excluded.

Each task shows a complete button, title, due-date badge, project badge (if assigned), and recurrence indicator.

---

## Projects Views

### `GET /projects`

Lists all non-archived projects. Each project shows:

- Project name (links to detail page)
- Description (if present)
- Open task count (all non-done tasks)
- Due-today task count (if any)

### `GET /projects/{project_id}`

Shows project metadata and all tasks assigned to that project, grouped by GTD status:

- Inbox, Next Action, Waiting For, Scheduled, Someday / Maybe, Done

Each group appears as a section heading followed by its tasks. Includes a quick-add form scoped to the project.

Returns 404 if the project does not exist.

---

## All Tasks View

### `GET /tasks`

Displays all tasks with optional filtering and text search. Supports the following query parameters:

| Parameter | Values | Description |
|---|---|---|
| `q` | free text | Case-insensitive search across title and notes |
| `status` | `inbox`, `next_action`, `waiting_for`, `scheduled`, `someday_maybe`, `done` | Filter by exact GTD status |
| `project_id` | integer or `none` | Filter by project ID; use `none` for tasks without a project |
| `has_due_date` | `yes`, `no` | Filter by presence or absence of a due date |
| `is_recurring` | `yes`, `no` | Filter by recurring flag |

All parameters are optional and can be combined. Invalid `status` values are ignored (all tasks are returned).

Each task shows:

- Complete button (for non-done tasks)
- Title
- Status badge with per-status color
- Due-date badge (color-coded: overdue in red, due today in blue)
- Project badge (if assigned)
- Recurrence indicator (if recurring)
- Rendered Markdown notes (if present)

Visual CSS classes applied to task items:

- `.task-overdue` — task is overdue (due_date before today, not done)
- `.task-due-today` — task is due today (not done)
- `.task-done` — task status is done
- `.task-inbox` — task status is inbox

Example request: `GET /tasks?status=inbox&q=groceries&has_due_date=yes`