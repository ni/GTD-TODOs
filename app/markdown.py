"""Markdown rendering helpers."""

import bleach
from markdown_it import MarkdownIt

markdown_parser = MarkdownIt("commonmark", {"html": False, "linkify": True})

SAFE_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {"p", "pre", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "span"}
)
SAFE_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": ["href", "title", "rel"],
    "code": ["class"],
}


def render_markdown(text: str | None) -> str:
    if not text:
        return ""
    rendered = markdown_parser.render(text)
    return bleach.clean(rendered, tags=SAFE_TAGS, attributes=SAFE_ATTRIBUTES)