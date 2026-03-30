"""Display helpers — rich tables and plain-text fallback."""

from __future__ import annotations

import io
from datetime import date

from rich.console import Console
from rich.table import Table


def _today() -> date:
    return date.today()


def _due_style(due_str: str | None, status: str | None) -> str:
    """Return a rich style string based on due date vs today."""
    if not due_str or status == "done":
        return ""
    try:
        due = date.fromisoformat(due_str)
    except ValueError:
        return ""
    today = _today()
    if due < today:
        return "bold red"
    if due == today:
        return "bold blue"
    return ""


def render_task_table(tasks: list[dict], plain: bool = False) -> str:
    """Render tasks as a table. Returns string."""
    if plain:
        lines = ["ID\tTitle\tStatus\tDue Date\tProject\tRecurring"]
        for t in tasks:
            proj = t.get("project_name") or t.get("project_id") or ""
            rec = "yes" if t.get("is_recurring") else ""
            lines.append(
                f"{t['id']}\t{t['title']}\t{t.get('status', '')}\t"
                f"{t.get('due_date') or ''}\t{proj}\t{rec}"
            )
        return "\n".join(lines)

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Due Date")
    table.add_column("Project")
    table.add_column("⟳", width=3)

    for t in tasks:
        due_str = t.get("due_date") or ""
        style = _due_style(due_str, t.get("status"))
        proj = t.get("project_name") or (str(t["project_id"]) if t.get("project_id") else "")
        rec = "⟳" if t.get("is_recurring") else ""
        table.add_row(
            str(t["id"]),
            t["title"],
            t.get("status", ""),
            f"[{style}]{due_str}[/{style}]" if style else due_str,
            proj,
            rec,
        )

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    console.print(table)
    return buf.getvalue()


def render_project_table(
    projects: list[dict], task_counts: dict[int, int] | None = None, plain: bool = False
) -> str:
    """Render projects as a table."""
    if plain:
        lines = ["ID\tName\tDescription\tDue Date\tTasks"]
        for p in projects:
            count = task_counts.get(p["id"], 0) if task_counts else ""
            lines.append(
                f"{p['id']}\t{p['name']}\t{p.get('description') or ''}\t"
                f"{p.get('due_date') or ''}\t{count}"
            )
        return "\n".join(lines)

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Due Date")
    table.add_column("Open Tasks", justify="right")

    for p in projects:
        count = str(task_counts.get(p["id"], 0)) if task_counts else ""
        table.add_row(
            str(p["id"]),
            p["name"],
            p.get("description") or "",
            p.get("due_date") or "",
            count,
        )

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    console.print(table)
    return buf.getvalue()


def render_task_detail(task: dict, plain: bool = False) -> str:
    """Render a single task's full details including notes."""
    lines: list[str] = []
    lines.append(f"Task #{task['id']}: {task['title']}")
    lines.append(f"  Status:    {task.get('status', '')}")
    lines.append(f"  Due Date:  {task.get('due_date') or 'none'}")
    proj = task.get("project_name") or task.get("project_id") or "none"
    lines.append(f"  Project:   {proj}")
    lines.append(f"  Recurring: {'yes' if task.get('is_recurring') else 'no'}")
    if task.get("notes"):
        lines.append(f"  Notes:     {task['notes']}")
    return "\n".join(lines)
