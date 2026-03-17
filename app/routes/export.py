"""Data export routes for CSV and JSON."""

from __future__ import annotations

import csv
import io
import logging
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlmodel import Session

from app.db import get_session
from app.models import TaskStatus
from app.services.export_service import export_projects, export_tasks

logger = logging.getLogger("app")

router = APIRouter(prefix="/export", tags=["export"])


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.get("/tasks.csv")
def export_tasks_csv(
    status: str = "",
    session: Session = Depends(get_session),
) -> StreamingResponse:
    """Export tasks as CSV."""
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            pass

    rows = export_tasks(session, status=status_filter)
    output = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else _task_csv_headers()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    content = output.getvalue()

    logger.info("Exported %d tasks as CSV", len(rows))
    filename = f"tasks-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/tasks.json")
def export_tasks_json(
    status: str = "",
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Export tasks as JSON."""
    status_filter = None
    if status:
        try:
            status_filter = TaskStatus(status)
        except ValueError:
            pass

    rows = export_tasks(session, status=status_filter)
    logger.info("Exported %d tasks as JSON", len(rows))
    filename = f"tasks-{date.today().isoformat()}.json"
    return JSONResponse(
        content=rows,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@router.get("/projects.csv")
def export_projects_csv(
    session: Session = Depends(get_session),
) -> StreamingResponse:
    """Export projects as CSV."""
    rows = export_projects(session)
    output = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else _project_csv_headers()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    content = output.getvalue()

    logger.info("Exported %d projects as CSV", len(rows))
    filename = f"projects-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/projects.json")
def export_projects_json(
    session: Session = Depends(get_session),
) -> JSONResponse:
    """Export projects as JSON."""
    rows = export_projects(session)
    logger.info("Exported %d projects as JSON", len(rows))
    filename = f"projects-{date.today().isoformat()}.json"
    return JSONResponse(
        content=rows,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task_csv_headers() -> list[str]:
    return [
        "id", "title", "notes", "status", "due_date",
        "is_recurring", "recurrence_type", "recurrence_interval_days",
        "last_completed_at", "project_id", "created_at", "updated_at", "completed_at",
    ]


def _project_csv_headers() -> list[str]:
    return ["id", "name", "description", "created_at", "updated_at", "archived_at"]
