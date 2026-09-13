from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .html_view import build_page_context
from .models import Event


_TEMPLATES = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(("html", "xml")),
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate_html(events: list[Event], path: str, area: str) -> None:
    """Render events as a self-contained HTML page at ``path``."""
    template = _TEMPLATES.get_template("events.html")
    output = template.render(build_page_context(events, area))

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")
