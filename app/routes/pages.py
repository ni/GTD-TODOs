"""Page routes."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import TaskStatus
from app.routes import templates
from app.services.project_service import (
    can_complete_project,
    complete_project,
    create_project,
    get_project,
    get_project_task_counts,
    list_projects,
)
from app.services.task_service import (
    get_nav_counts,
    list_tasks,
    list_tasks_due_today,
    list_tasks_overdue,
    search_tasks,
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
    nav_counts = get_nav_counts(session)
    return templates.TemplateResponse(
        request,
        "inbox.html",
        {
            "app_name": settings.app_name,
            "tasks": tasks,
            "projects": projects_map,
            "nav_counts": nav_counts,
        },
    )


@router.get("/today", response_class=HTMLResponse)
def today(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    settings = get_settings()
    overdue = list_tasks_overdue(session)
    due_today = list_tasks_due_today(session)
    projects_map = {p.id: p.name for p in list_projects(session)}
    nav_counts = get_nav_counts(session)
    return templates.TemplateResponse(
        request,
        "today.html",
        {
            "app_name": settings.app_name,
            "overdue": overdue,
            "due_today": due_today,
            "projects": projects_map,
            "nav_counts": nav_counts,
        },
    )


@router.get("/projects", response_class=HTMLResponse)
def projects_list(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    settings = get_settings()
    projects = list_projects(session)
    counts = {p.id: get_project_task_counts(session, p.id) for p in projects}  # type: ignore[arg-type]
    nav_counts = get_nav_counts(session)
    return templates.TemplateResponse(
        request,
        "projects_list.html",
        {
            "app_name": settings.app_name,
            "projects": projects,
            "counts": counts,
            "nav_counts": nav_counts,
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


@router.post("/projects/{project_id}/complete")
def complete_project_route(
    project_id: int,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    project = complete_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found or has open tasks")
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


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

    # Group tasks by status, ordered to match the STATUS_LABELS dropdown
    grouped: dict[str, list] = {}
    for label in STATUS_LABELS.values():
        grouped[label] = []
    for task in tasks:
        label = STATUS_LABELS.get(task.status.value, task.status.value)
        grouped.setdefault(label, []).append(task)
    # Drop empty groups
    grouped = {k: v for k, v in grouped.items() if v}

    nav_counts = get_nav_counts(session)
    completable = can_complete_project(session, project_id)
    return templates.TemplateResponse(
        request,
        "project_detail.html",
        {
            "app_name": settings.app_name,
            "project": project,
            "grouped_tasks": grouped,
            "status_labels": STATUS_LABELS,
            "nav_counts": nav_counts,
            "can_complete": completable,
        },
    )


@router.get("/tasks", response_class=HTMLResponse)
def all_tasks(
    request: Request,
    status: str = "all_in_work",
    project_id: str = "",
    q: str = "",
    has_due_date: str = "",
    is_recurring: str = "",
    session: Session = Depends(get_session),
) -> HTMLResponse:
    from datetime import date as _date

    from app.models import TaskStatus as _TS

    settings = get_settings()
    projects_list_all = list_projects(session)
    projects_map = {p.id: p.name for p in projects_list_all}

    # Parse filters
    status_filter = None
    exclude_done = False
    if status == "all_in_work":
        exclude_done = True
    else:
        try:
            if status:
                status_filter = _TS(status)
        except ValueError:
            pass

    pid: int | None = None
    no_project = False
    if project_id == "none":
        no_project = True
    elif project_id:
        try:
            pid = int(project_id)
        except ValueError:
            pass

    due_filter: bool | None = None
    if has_due_date == "yes":
        due_filter = True
    elif has_due_date == "no":
        due_filter = False

    recurring_filter: bool | None = None
    if is_recurring == "yes":
        recurring_filter = True
    elif is_recurring == "no":
        recurring_filter = False

    tasks = search_tasks(
        session,
        status=status_filter,
        exclude_done=exclude_done,
        project_id=pid,
        no_project=no_project,
        q=q.strip() if q else None,
        has_due_date=due_filter,
        is_recurring=recurring_filter,
    )

    today = _date.today()
    nav_counts = get_nav_counts(session)

    return templates.TemplateResponse(
        request,
        "tasks_list.html",
        {
            "app_name": settings.app_name,
            "tasks": tasks,
            "projects": projects_map,
            "projects_list": projects_list_all,
            "status_labels": STATUS_LABELS,
            "today": today,
            "nav_counts": nav_counts,
            # Current filter values for the form
            "f_status": status,
            "f_project_id": project_id,
            "f_q": q,
            "f_has_due_date": has_due_date,
            "f_is_recurring": is_recurring,
        },
    )