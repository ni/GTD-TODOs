"""Application routes package."""

from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from starlette.requests import Request

from app.config import get_settings
from app.markdown import render_markdown

_template_dir = str(Path(__file__).resolve().parent.parent / "templates")
templates = Jinja2Templates(directory=_template_dir)
templates.env.globals["render_markdown"] = render_markdown


def _show_logout() -> bool:
    return not get_settings().auth_disabled


def _csrf_hidden_input(request: Request) -> Markup:
    """Return an HTML hidden input carrying the current CSRF token."""
    token = getattr(request.state, "csrf_token", "")
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


templates.env.globals["show_logout"] = _show_logout
templates.env.globals["csrf_hidden_input"] = _csrf_hidden_input