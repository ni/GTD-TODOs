"""Markdown rendering helpers."""

import nh3
from markdown_it import MarkdownIt

markdown_parser = MarkdownIt("commonmark", {"html": False, "linkify": True})

SAFE_TAGS = {
    "a", "abbr", "acronym", "b", "blockquote", "code", "em", "i", "li", "ol",
    "strong", "ul", "p", "pre", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "span",
}
SAFE_ATTRIBUTES = {
    "a": {"href", "title"},
    "abbr": {"title"},
    "acronym": {"title"},
    "code": {"class"},
}


def render_markdown(text: str | None) -> str:
    if not text:
        return ""
    rendered = markdown_parser.render(text)
    return nh3.clean(rendered, tags=SAFE_TAGS, attributes=SAFE_ATTRIBUTES)