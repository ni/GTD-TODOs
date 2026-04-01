---
name: gtd-daily-report
description: Generate a daily focus report, tomorrow's priorities, or a GTD review from live task data.
---
# GTD Daily Focus Report Skill

Use this skill when the user asks for a daily report, focus plan, tomorrow's priorities, or a GTD review.

## How to Generate the Report

> **Important:** Always use the `gtd` CLI to fetch data. Do NOT query the SQLite database directly via `docker exec`, and do NOT use `curl` against the HTTP API. The CLI handles authentication and connectivity automatically via `~/.gtd/config.toml`.

### Step 1: Verify connectivity

```bash
gtd health
```

If the CLI is not installed, run `./scripts/install-cli.sh` from the repo root. If the server is unreachable, tell the user to start it with `docker compose up -d --build`.

### Step 2: Fetch the structured report

```bash
gtd report               # today's report
gtd report --tomorrow    # tomorrow's report
gtd report --date YYYY-MM-DD  # specific date
```

`gtd report` returns a pre-classified Markdown summary with Do First, Next Actions, Waiting For, Inbox, and Previous Day sections. Use this as the foundation.

### Step 3: Fetch supplementary data if needed

```bash
gtd tasks --status inbox          # check inbox count
gtd projects                      # check project health (open task counts)
```

### Step 4: Determine the target date

If the user says "tomorrow", use today's date + 1. If they say "today" or give no date, use today. Use the current date from context.

### Step 5: Classify tasks using GTD methodology

The `gtd report` output already classifies most of these. Verify and supplement from the open tasks (status != `done`):

1. **Hard Landscape** — tasks with `due_date` equal to the target date. These are non-negotiable commitments.
2. **Overdue** — tasks with `due_date` before the target date. These need immediate attention.
3. **Urgent Next Actions** — tasks with status `next_action` due within 3 days of the target date.
4. **Other Next Actions** — remaining `next_action` tasks, sorted by `due_date`.
5. **Waiting For** — tasks with status `waiting_for`. Suggest follow-up nudges if they've been waiting more than 2 days.
6. **Someday / Maybe** — tasks with status `someday_maybe`. Mention only briefly.
7. **Inbox** — tasks with status `inbox`. Remind user to clarify these.

### Step 6: Build the report

Include these sections:

- **Do First**: Hard landscape + overdue items. These are the "must do" items.
- **Next Actions ranked by urgency**: Table with task title, project name, due date, and days remaining.
- **Waiting For**: Table with task, project, notes, and a follow-up recommendation.
- **GTD Recommendations**: 3-5 actionable bullet points advising how to spend the day. Reference specific tasks and projects. Consider time-sensitivity, dependencies, and quick wins.
- **Previous Day's Wins**: Count of tasks completed on the current date (tasks where `completed_at` matches today). Provides momentum context.

### Step 7: Resolve project names

The CLI output already includes project names. If any are missing, use `gtd project <id>` to look them up.

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
