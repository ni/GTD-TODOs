# GTD Daily Focus Report Skill

Use this skill when the user asks for a daily report, focus plan, tomorrow's priorities, or a GTD review.

## How to Generate the Report

### Step 1: Determine the app port and verify it is running

Read `docker-compose.yml` in the repo root to find the published host port from the `ports` mapping (the left side of the `"host:container"` pair). Fall back to port `8080` if the file is missing or unparseable.

```bash
curl -s http://localhost:<PORT>/health
```

Expect `{"status":"ok"}`. If not, tell the user to start the container first.

### Step 2: Fetch all open tasks and projects

Use the port discovered in Step 1 for all requests:

```bash
curl -s http://localhost:<PORT>/export/tasks.json
curl -s http://localhost:<PORT>/export/projects.json
```

These JSON export endpoints return every task/project with all fields. Filter client-side.

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
