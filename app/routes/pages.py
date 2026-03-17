"""Page routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import TaskStatus
from app.routes import templates
from app.services.project_service import list_projects
from app.services.task_service import list_tasks

router = APIRouter(tags=["pages"])


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