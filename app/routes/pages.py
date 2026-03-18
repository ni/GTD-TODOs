"""Page routes."""

from datetime import date
from urllib.parse import quote, urlparse

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
    update_project,
)
from app.services.task_service import (
    get_nav_counts,
    list_tasks,
    list_tasks_due_today,
    list_tasks_overdue,
    search_tasks,
)

router = APIRouter(tags=["pages"])

STATUS_LABELS: dict[str, str] = {s.value: s.label for s in TaskStatus}


def _base_context(session: Session) -> dict[str, object]:
    return {
        "app_name": get_settings().app_name,
        "nav_counts": get_nav_counts(session),
    }


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse("/inbox", status_code=302)


@router.get("/inbox", response_class=HTMLResponse)
def inbox(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    tasks = list_tasks(session, status=TaskStatus.INBOX)
    projects_map = {p.id: p.name for p in list_projects(session, include_completed=True)}
    ctx = _base_context(session)
    ctx.update({"tasks": tasks, "projects": projects_map})
    return templates.TemplateResponse(request, "inbox.html", ctx)


@router.get("/today", response_class=HTMLResponse)
def today(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    overdue = list_tasks_overdue(session)
    due_today = list_tasks_due_today(session)
    projects_map = {p.id: p.name for p in list_projects(session, include_completed=True)}
    ctx = _base_context(session)
    ctx.update({"overdue": overdue, "due_today": due_today, "projects": projects_map})
    return templates.TemplateResponse(request, "today.html", ctx)


@router.get("/projects", response_class=HTMLResponse)
def projects_list(
    request: Request, session: Session = Depends(get_session)
) -> HTMLResponse:
    projects = list_projects(session, include_completed=True)
    counts = {p.id: get_project_task_counts(session, p.id) for p in projects}  # type: ignore[arg-type]
    ctx = _base_context(session)
    ctx.update({"projects": projects, "counts": counts, "today": date.today()})
    return templates.TemplateResponse(request, "projects_list.html", ctx)


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
    project = get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    completed = complete_project(session, project_id)
    if completed is None:
        raise HTTPException(status_code=409, detail="Project has open tasks")
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

    completable = can_complete_project(session, project_id)
    ctx = _base_context(session)
    ctx.update({
        "project": project,
        "grouped_tasks": grouped,
        "status_labels": STATUS_LABELS,
        "can_complete": completable,
        "today": date.today(),
    })
    return templates.TemplateResponse(request, "project_detail.html", ctx)


# Paths that are safe redirect targets from the referer header.
_SAFE_REFERER_PREFIXES = ("/inbox", "/today", "/projects", "/tasks")


def _redirect_back(request: Request, fallback: str = "/projects") -> str:
    """Extract a safe redirect path from the Referer header."""
    referer = request.headers.get("referer", "")
    if referer:
        path = urlparse(referer).path
        if any(path.startswith(prefix) for prefix in _SAFE_REFERER_PREFIXES):
            return path
    return fallback


@router.get("/projects/{project_id}/edit", response_class=HTMLResponse)
def edit_project_page(
    request: Request,
    project_id: int,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    project = get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    back_url = request.query_params.get("back_url") or _redirect_back(request)
    ctx = _base_context(session)
    ctx.update({"project": project, "back_url": back_url})
    return templates.TemplateResponse(request, "project_edit.html", ctx)


@router.post("/projects/{project_id}/update")
def update_project_route(
    project_id: int,
    name: str = Form(...),
    description: str = Form(""),
    notes: str = Form(""),
    due_date: str = Form(""),
    action: str = Form("save"),
    back_url: str = Form("/projects"),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    project = get_project(session, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    if not name.strip():
        return RedirectResponse(f"/projects/{project_id}/edit", status_code=303)

    parsed_due = date.fromisoformat(due_date) if due_date else None
    update_project(
        session,
        project_id,
        name=name.strip(),
        description=description.strip() if description.strip() else None,
        notes=notes.strip() if notes.strip() else None,
        due_date=parsed_due,
    )

    if action == "close":
        safe_back = back_url
        if not any(safe_back.startswith(p) for p in _SAFE_REFERER_PREFIXES):
            safe_back = f"/projects/{project_id}"
        return RedirectResponse(safe_back, status_code=303)
    # Preserve back_url through the Save redirect so it survives round-trips
    safe_back = back_url
    if not any(safe_back.startswith(p) for p in _SAFE_REFERER_PREFIXES):
        safe_back = f"/projects/{project_id}"
    return RedirectResponse(
        f"/projects/{project_id}/edit?back_url={quote(safe_back)}", status_code=303
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
    projects_list_all = list_projects(session, include_completed=True)
    projects_map = {p.id: p.name for p in projects_list_all}

    # Parse filters
    status_filter = None
    exclude_done = False
    if status == "all_in_work":
        exclude_done = True
    else:
        try:
            if status:
                status_filter = TaskStatus(status)
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

    ctx = _base_context(session)
    ctx.update({
        "tasks": tasks,
        "projects": projects_map,
        "projects_list": projects_list_all,
        "status_labels": STATUS_LABELS,
        "today": date.today(),
        # Current filter values for the form
        "f_status": status,
        "f_project_id": project_id,
        "f_q": q,
        "f_has_due_date": has_due_date,
        "f_is_recurring": is_recurring,
    })
    return templates.TemplateResponse(request, "tasks_list.html", ctx)