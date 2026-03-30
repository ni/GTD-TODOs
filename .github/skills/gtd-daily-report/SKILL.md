---
name: gtd-daily-report
description: Generate a daily focus report, tomorrow's priorities, or a GTD review from live task data.
---
# GTD Daily Focus Report Skill

Use this skill when the user asks for a daily report, focus plan, tomorrow's priorities, or a GTD review.

## How to Generate the Report

### Step 1: Verify the app container is running

```bash
docker ps --filter name=gtd-todos-app --format '{{.Status}}'
```

If the container is not running, tell the user to start it with `docker compose up -d --build`.

### Step 2: Fetch all open tasks and projects

Query the SQLite database directly inside the container. This avoids HTTP auth (WebAuthn passkeys cannot be used programmatically) and requires no config changes.

```bash
docker exec gtd-todos-app python -c "
import sqlite3, json
conn = sqlite3.connect('/data/todo.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
tasks = [dict(r) for r in cur.execute('SELECT * FROM tasks').fetchall()]
projects = [dict(r) for r in cur.execute('SELECT * FROM projects').fetchall()]
conn.close()
print('===TASKS===')
print(json.dumps(tasks, indent=2, default=str))
print('===PROJECTS===')
print(json.dumps(projects, indent=2, default=str))
"
```

This returns all tasks and projects with all fields as JSON. Filter client-side.

> **Note:** Table names are `tasks` and `projects` (plural). The database path inside the container is `/data/todo.db`.

### Step 3: Determine the target date

If the user says "tomorrow", use today's date + 1. If they say "today" or give no date, use today. Use the current date from context.

### Step 4: Classify tasks using GTD methodology

From the open tasks (status != `done`), build these categories:

1. **Hard Landscape** — tasks with `due_date` equal to the target date. These are non-negotiable commitments.
2. **Overdue** — tasks with `due_date` before the target date. These need immediate attention.
3. **Urgent Next Actions** — tasks with status `next_action` due within 3 days of the target date.
4. **Other Next Actions** — remaining `next_action` tasks, sorted by `due_date`.
5. **Waiting For** — tasks with status `waiting_for`. Suggest follow-up nudges if they've been waiting more than 2 days.
6. **Someday / Maybe** — tasks with status `someday_maybe`. Mention only briefly.
7. **Inbox** — tasks with status `inbox`. Remind user to clarify these.

### Step 5: Build the report

Include these sections:

- **Do First**: Hard landscape + overdue items. These are the "must do" items.
- **Next Actions ranked by urgency**: Table with task title, project name, due date, and days remaining.
- **Waiting For**: Table with task, project, notes, and a follow-up recommendation.
- **GTD Recommendations**: 3-5 actionable bullet points advising how to spend the day. Reference specific tasks and projects. Consider time-sensitivity, dependencies, and quick wins.
- **Previous Day's Wins**: Count of tasks completed on the current date (tasks where `completed_at` matches today). Provides momentum context.

### Step 6: Resolve project names

Map `project_id` from tasks to the project `name` from the projects export. Show project names in the report, not IDs.

## Report Format

Use Markdown with:
- H2 for the report title (include the target date)
- H3 for each section
- Tables for task lists
- Blockquotes for the #1 priority callout
- Bold for due dates that are within 2 days

## GTD Principles to Apply

- **Two-minute rule**: If a task can be done in < 2 minutes, recommend doing it first.
- **Context batching**: Group similar tasks when recommending order of work.
- **Weekly Review prep**: If it's Friday, remind user to do a weekly review.
- **Project health**: Flag any active project that has zero next actions.
