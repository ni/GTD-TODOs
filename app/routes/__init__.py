"""Application routes package."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.markdown import render_markdown

_template_dir = str(Path(__file__).resolve().parent.parent / "templates")
templates = Jinja2Templates(directory=_template_dir)
templates.env.globals["render_markdown"] = render_markdown