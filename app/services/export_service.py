"""Export service for serializing tasks and projects to dicts."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models import Project, Task, TaskStatus


def export_tasks(
    session: Session,
    *,
    status: TaskStatus | None = None,
) -> list[dict[str, object]]:
    """Return all tasks (optionally filtered) as plain dicts for export."""
    stmt = select(Task).order_by(Task.id)  # type: ignore[arg-type]
    if status is not None:
        stmt = stmt.where(Task.status == status)
    tasks = list(session.exec(stmt).all())
    return [_task_to_dict(t) for t in tasks]


def export_projects(session: Session) -> list[dict[str, object]]:
    """Return all projects as plain dicts for export."""
    stmt = select(Project).order_by(Project.id)  # type: ignore[arg-type]
    projects = list(session.exec(stmt).all())
    return [_project_to_dict(p) for p in projects]


def _task_to_dict(task: Task) -> dict[str, object]:
    return {
        "id": task.id,
        "title": task.title,
        "notes": task.notes or "",
        "status": task.status.value if task.status else "",
        "due_date": task.due_date.isoformat() if task.due_date else "",
        "is_recurring": task.is_recurring,
        "recurrence_type": task.recurrence_type.value if task.recurrence_type else "",
        "recurrence_interval_days": task.recurrence_interval_days or "",
        "last_completed_at": task.last_completed_at.isoformat() if task.last_completed_at else "",
        "project_id": task.project_id or "",
        "created_at": task.created_at.isoformat() if task.created_at else "",
        "updated_at": task.updated_at.isoformat() if task.updated_at else "",
        "completed_at": task.completed_at.isoformat() if task.completed_at else "",
    }


def _project_to_dict(project: Project) -> dict[str, object]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "created_at": project.created_at.isoformat() if project.created_at else "",
        "updated_at": project.updated_at.isoformat() if project.updated_at else "",
        "archived_at": project.archived_at.isoformat() if project.archived_at else "",
    }
