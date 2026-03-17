"""Page routes."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import TaskStatus
from app.routes import templates
from app.services.project_service import (
    create_project,
    get_project,
    get_project_task_counts,
    list_projects,
)
from app.services.task_service import (
    list_tasks,
    list_tasks_due_today,
    list_tasks_overdue,
)

router = APIRouter(tags=["pages"])

STATUS_LABELS: dict[str, str] = {
    "inbox": "Inbox",
    "next_action": "Next Action",
    "waiting_for": "Waiting For",
    "scheduled": "Scheduled",
    "someday_maybe": "Someday / Maybe",
    "done": "Done",
}


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/inbox", status_code=302)


@router.get("/inbox", response_class=HTMLResponse)
def inbox(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    settings = get_settings()
    tasks = list_tasks(session, status=TaskStatus.INBOX)
    projects_map = {p.id: p.name for p in list_projects(session)}
    return templates.TemplateResponse(
        request,
        "inbox.html",
        {
            "app_name": settings.app_name,
            "tasks": tasks,
            "projects": projects_map,
        },
    )


@router.get("/today", response_class=HTMLResponse)
def today(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    settings = get_settings()
    overdue = list_tasks_overdue(session)
    due_today = list_tasks_due_today(session)
    projects_map = {p.id: p.name for p in list_projects(session)}
    return templates.TemplateResponse(
        request,
        "today.html",
        {
            "app_name": settings.app_name,
            "overdue": overdue,
            "due_today": due_today,
            "projects": projects_map,
        },
    )


@router.get("/projects", response_class=HTMLResponse)
def projects_list(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    settings = get_settings()
    projects = list_projects(session)
    counts = {p.id: get_project_task_counts(session, p.id) for p in projects}  # type: ignore[arg-type]
    return templates.TemplateResponse(
        request,
        "projects_list.html",
        {
            "app_name": settings.app_name,
            "projects": projects,
            "counts": counts,
        },
    )


@router.post("/projects")
def create_project_route(
    name: str = Form(""),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    if name.strip():
        create_project(session, name=name.strip())
    return RedirectResponse("/projects", status_code=303)


@router.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(
    request: Request,
    project_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    project = get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    settings = get_settings()
    tasks = list_tasks(session, project_id=project_id)

    # Group tasks by status
    grouped: dict[str, list] = {}
    for task in tasks:
        label = STATUS_LABELS.get(task.status.value, task.status.value)
        grouped.setdefault(label, []).append(task)

    return templates.TemplateResponse(
        request,
        "project_detail.html",
        {
            "app_name": settings.app_name,
            "project": project,
            "grouped_tasks": grouped,
            "status_labels": STATUS_LABELS,
        },
    )