"""Shared route helpers — redirect safety, filter parsing, base context."""

from urllib.parse import urlparse

from fastapi import Request
from sqlmodel import Session

from app.config import get_settings
from app.models import TaskStatus
from app.services.task_service import get_nav_counts

SAFE_REFERER_PREFIXES = ("/inbox", "/today", "/projects", "/tasks")


def redirect_back(request: Request, fallback: str = "/inbox") -> str:
    """Extract a safe redirect path from the Referer header."""
    referer = request.headers.get("referer", "")
    if referer:
        path = urlparse(referer).path
        if any(path.startswith(prefix) for prefix in SAFE_REFERER_PREFIXES):
            return path
    return fallback


def safe_back_url(back_url: str, fallback: str) -> str:
    """Return *back_url* if it starts with a safe prefix, otherwise *fallback*."""
    if any(back_url.startswith(p) for p in SAFE_REFERER_PREFIXES):
        return back_url
    return fallback


def base_context(session: Session) -> dict[str, object]:
    """Build the common template context (app name + nav badge counts)."""
    return {
        "app_name": get_settings().app_name,
        "nav_counts": get_nav_counts(session),
    }


def parse_status_filter(status: str) -> TaskStatus | None:
    """Parse a status query-param string into a TaskStatus, or None."""
    if not status:
        return None
    try:
        return TaskStatus(status)
    except ValueError:
        return None


def parse_bool_filter(value: str) -> bool | None:
    """Parse a ``yes``/``no`` query-param into True/False/None."""
    if value == "yes":
        return True
    if value == "no":
        return False
    return None
