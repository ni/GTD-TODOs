"""Task mutation and edit routes."""

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import RecurrenceType, Task, TaskStatus
from app.routes import templates
from app.services.project_service import list_projects
from app.services.task_service import complete_task, create_task, reopen_task

STATUS_OPTIONS = [
    ("inbox", "Inbox"),
    ("next_action", "Next Action"),
    ("waiting_for", "Waiting For"),
    ("scheduled", "Scheduled"),
    ("someday_maybe", "Someday / Maybe"),
    ("done", "Done"),
]

RECURRENCE_OPTIONS = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("interval_days", "Custom Interval (days)"),
]

router = APIRouter(tags=["tasks"])


@router.post("/tasks")
def create_task_route(
    title: str = Form(""),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    if not title.strip():
        return RedirectResponse("/inbox", status_code=303)
    create_task(session, title=title.strip())
    return RedirectResponse("/inbox", status_code=303)


@router.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def edit_task_page(
    request: Request,
    task_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    settings = get_settings()
    projects = list_projects(session)
    return templates.TemplateResponse(
        request,
        "task_edit.html",
        {
            "app_name": settings.app_name,
            "task": task,
            "projects": projects,
            "statuses": STATUS_OPTIONS,
            "recurrence_types": RECURRENCE_OPTIONS,
        },
    )


@router.post("/tasks/{task_id}/update")
def update_task_route(
    task_id: int,
    title: str = Form(...),
    notes: str = Form(""),
    status: str = Form("inbox"),
    due_date: str = Form(""),
    is_recurring: str = Form(""),
    recurrence_type: str = Form(""),
    recurrence_interval_days: str = Form(""),
    project_id: str = Form(""),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = title
    task.notes = notes if notes.strip() else None
    task.status = TaskStatus(status)
    task.due_date = date.fromisoformat(due_date) if due_date else None
    task.is_recurring = is_recurring in ("on", "true", "1")
    task.recurrence_type = RecurrenceType(recurrence_type) if recurrence_type else None
    task.recurrence_interval_days = (
        int(recurrence_interval_days) if recurrence_interval_days else None
    )
    task.project_id = int(project_id) if project_id else None
    task.updated_at = datetime.now(UTC)

    session.add(task)
    session.commit()
    return RedirectResponse("/inbox", status_code=303)


@router.post("/tasks/{task_id}/complete")
def complete_task_route(
    task_id: int,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    task = complete_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/inbox", status_code=303)


@router.post("/tasks/{task_id}/reopen")
def reopen_task_route(
    task_id: int,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    task = reopen_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return RedirectResponse("/inbox", status_code=303)
