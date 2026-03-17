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
- `GET /today` shows overdue tasks and tasks due today (excludes done tasks and tasks without due dates).
- `GET /projects` lists non-archived projects with open and due-today task counts.
- `GET /projects/{project_id}` shows project details with tasks grouped by GTD status.
- `GET /tasks` shows all tasks with filtering and search support.
- `GET /tasks/{task_id}/edit` shows the task edit form.

## Mutation Routes

- `POST /tasks` creates a task (form fields: `title`, optional `project_id`). Redirects back to the referring page.
- `POST /tasks/{task_id}/update` updates a task from the edit form. Redirects back to the referring page.
- `POST /tasks/{task_id}/complete` completes a task. Redirects back to the referring page.
- `POST /tasks/{task_id}/reopen` reopens a task to inbox. Redirects back to the referring page.
- `POST /projects` creates a project (form field: `name`). Redirects to `/projects`.

See `docs/api.md` for full form field specifications.

## All Tasks Filtering and Search

The `GET /tasks` page accepts query parameters:

| Parameter | Values | Meaning |
|---|---|---|
| `q` | free text | Case-insensitive search across title and notes |
| `status` | `inbox`, `next_action`, `waiting_for`, `scheduled`, `someday_maybe`, `done` | Exact status match |
| `project_id` | integer or `none` | Filter by project; `none` for unassigned |
| `has_due_date` | `yes`, `no` | Has or lacks a due date |
| `is_recurring` | `yes`, `no` | Recurring or non-recurring |

Parameters combine with AND logic. Example: `/tasks?status=inbox&q=groceries`

## Today View Behavior

The Today page shows two sections:
1. **Overdue**: tasks with `due_date` before today, status not `done`.
2. **Due Today**: tasks with `due_date` equal to today, status not `done`.

Recurring tasks whose next due date is today appear automatically. Tasks without due dates are excluded.

## Project Views Behavior

- The projects list shows all non-archived projects with open task counts and due-today counts.
- The project detail page groups tasks by GTD status (Inbox, Next Action, Waiting For, Scheduled, Someday / Maybe, Done).
- A quick-add form on the project detail page creates tasks pre-assigned to that project.

## Visual Distinction

Tasks have CSS classes that indicate their state for any UI interaction or scraping:

- `.task-overdue` — overdue (due_date < today, not done)
- `.task-due-today` — due today (not done)
- `.task-done` — completed
- `.task-inbox` — inbox status

## General Conventions

- HTML page routes return server-rendered responses.
- Mutation routes accept form-encoded POST data and redirect on success.
- Not-found resources return HTTP 404.
- Empty titles are rejected on update (redirect back to edit form).
- SQLite persistence uses the database URL configured in `DATABASE_URL`.

## Troubleshooting

- If the app is unreachable, confirm the container or local process is running.
- If database startup fails, verify that the SQLite target directory is writable.
- If behavior changes, update `docs/api.md` and this skill file together.