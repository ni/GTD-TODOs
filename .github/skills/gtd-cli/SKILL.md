---
name: gtd-cli
description: Using the GTD CLI to manage tasks, projects, and generate reports from the command line.
---
# GTD CLI Skill

Use this skill when using the `gtd` command-line tool to manage tasks, projects, or generate reports instead of the HTTP API directly.

## Prerequisites

1. CLI installed: `gtd --version` should print the version.
2. Config initialized: `~/.gtd/config.toml` must exist with server URL and API key.
3. Server running: `gtd health` should report healthy.

If the CLI is not installed, run `./scripts/install-cli.sh` from the repo root.

## Quick Start

```bash
# First-time setup (prompts for server URL + API key)
gtd config init

# Verify connectivity
gtd health
```

## Common Workflows

### Add a task

```bash
gtd add "Buy groceries"
gtd add "Fix bug in auth" --project 1
```

### Check today's focus

```bash
gtd today
```

### Complete a task

```bash
gtd complete 42
```

### Change task status

```bash
gtd edit 42 --status next_action
```

### Search tasks

```bash
gtd tasks --search "groceries"
gtd tasks --status inbox
gtd tasks --project 1
```

### View a project

```bash
gtd projects          # list all projects with task counts
gtd project 1         # show project details + tasks grouped by status
```

## GTD Report Generation

The `gtd report` command produces a **structured data summary** — not an AI-generated report. It handles data fetching and deterministic task classification.

```bash
gtd report               # today's report
gtd report --tomorrow    # tomorrow's report
gtd report --date 2026-04-01  # specific date
```

### Agent workflow

1. Run `gtd report` to get the structured Markdown output.
2. Read the output (Do First, Next Actions, Waiting For, Inbox sections).
3. Layer on LLM-powered GTD recommendations: prioritization, two-minute rule, context batching, project health flags, follow-up nudges.

No API key needs to be stored in agent memory — the CLI reads credentials from `~/.gtd/config.toml`.

## Export Data

```bash
gtd export tasks                    # JSON to stdout
gtd export tasks --format csv       # CSV to stdout
gtd export tasks --output out.json  # write to file
gtd export tasks --status inbox     # filter by status
gtd export projects                 # export projects
gtd export projects --format csv    # CSV format
```

## Environment Variable Overrides

| Variable | Purpose |
|---|---|
| `GTD_SERVER_URL` | Override server URL (useful for CI / non-standard ports) |
| `GTD_API_KEY` | Override API key (useful for CI where config file may not exist) |
| `GTD_CONFIG_DIR` | Override config directory (default: `~/.gtd`) |

These take precedence over values in `~/.gtd/config.toml`.

## Output Formats

- **Rich tables** (default): colored, formatted terminal tables.
- **Plain text** (`--plain` flag): tab-separated output for scripting or piping.
- **JSON/CSV**: via `gtd export` commands.

Use `--plain` when parsing output programmatically.

## Error Handling

- `gtd health` returns exit code 1 if the server is unreachable.
- All commands show human-readable errors for HTTP failures (404, 500, connection errors).
- If the API key is invalid or missing, the server returns 401 — update with `gtd config set auth.api_key <key>`.

## Full Command Reference

| Command | Description |
|---|---|
| `gtd config init` | Interactive setup |
| `gtd config show` | Show config (masked key) |
| `gtd config set KEY VALUE` | Set a config value |
| `gtd health` | Check server connectivity |
| `gtd inbox` | List inbox tasks |
| `gtd today` | Show overdue + due-today tasks |
| `gtd tasks [options]` | List/filter/search tasks |
| `gtd add TITLE [--project ID]` | Create a task |
| `gtd complete ID` | Complete a task |
| `gtd reopen ID` | Reopen a task |
| `gtd edit ID [options]` | Edit task fields |
| `gtd projects` | List projects with counts |
| `gtd project ID` | Show project details |
| `gtd export tasks [--format --status --output]` | Export tasks |
| `gtd export projects [--format --output]` | Export projects |
| `gtd report [--date --tomorrow]` | GTD data summary |
| `gtd --help` | Full help with ASCII banner |
| `gtd --version` | Print version |

## Troubleshooting

- **"Cannot connect to server"**: Verify the server is running (`docker compose up`) and the URL in config matches.
- **401 errors**: API key is missing or revoked. Generate a new one from the Settings page and update with `gtd config set auth.api_key <key>`.
- **Stale data**: The CLI fetches live data on every invocation. If data seems stale, the server may be running an old database.
