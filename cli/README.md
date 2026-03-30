# GTD CLI

Command-line interface for the [GTD TODOs](../README.md) application. Communicates with the running server over HTTP using API key authentication.

## Install

### Quick Install (recommended)

```bash
./scripts/install-cli.sh
```

This auto-detects `pipx` or `uv` and installs the `gtd` command globally.

### Manual Install

```bash
# Using pipx
pipx install ./cli

# Using uv
uv tool install ./cli

# For development
cd cli && uv sync
```

### Uninstall

```bash
pipx uninstall gtd-cli
# or
uv tool uninstall gtd-cli
```

## First-Time Setup

```bash
gtd config init
```

This prompts for the server URL and API key, then writes `~/.gtd/config.toml` with restricted permissions (`0600`).

Generate an API key from the Settings page (gear icon) in the GTD TODOs web UI.

## Usage

```bash
gtd --help               # show ASCII banner + full command list
gtd health               # check server connectivity

# Views
gtd today                # overdue + due-today tasks
gtd inbox                # inbox tasks

# Task management
gtd tasks                # list all tasks
gtd tasks --status inbox # filter by status
gtd tasks --search milk  # search by text
gtd add "Buy groceries"  # create a task
gtd add "Fix bug" --project 1  # create in a project
gtd complete 42          # complete a task
gtd reopen 42            # reopen a task
gtd edit 42 --status next_action  # change status
gtd edit 42 --due 2026-04-01     # set due date
gtd edit 42 --title "New title"  # change title

# Projects
gtd projects             # list projects with task counts
gtd project 1            # show project details + tasks

# Export
gtd export tasks                  # JSON to stdout
gtd export tasks --format csv     # CSV to stdout
gtd export tasks --output out.json  # write to file
gtd export projects               # export projects

# GTD Report
gtd report               # today's structured GTD summary
gtd report --tomorrow    # tomorrow's summary
gtd report --date 2026-04-01  # specific date
```

## Configuration

Config file: `~/.gtd/config.toml`

```toml
[server]
url = "http://localhost:8080"

[auth]
api_key = "gtd_your_key_here"
```

### Environment Variable Overrides

| Variable | Purpose |
|---|---|
| `GTD_SERVER_URL` | Override server URL |
| `GTD_API_KEY` | Override API key |
| `GTD_CONFIG_DIR` | Override config directory (default: `~/.gtd`) |

### Config Commands

```bash
gtd config show                          # show current config (key masked)
gtd config set server.url http://host:8080  # change server URL
gtd config set auth.api_key gtd_newkey      # change API key
```

## Output Formats

- **Rich tables** (default) — colored, formatted tables in the terminal.
- **Plain text** (`--plain`) — tab-separated output for scripting/piping.
- **JSON/CSV** (`gtd export`) — full data exports.

## GTD Report

The `gtd report` command produces a structured Markdown data summary:

- **Do First**: overdue + hard-landscape (due today) tasks.
- **Next Actions**: ranked by urgency with days remaining.
- **Waiting For**: with days-waiting count.
- **Inbox**: tasks needing clarification.
- **Previous Day**: yesterday's completion count.

This is designed for consumption by an LLM agent which adds prioritization advice, two-minute rule suggestions, and GTD recommendations on top.
