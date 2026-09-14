from bs4 import BeautifulSoup
import bleach
from markdown import markdown

from .url_sanitizer import sanitize_url


ALLOWED_TAGS = {"a", "blockquote", "br", "code", "em", "li", "ol", "p", "strong", "ul"}


def render_card_markdown(value: str) -> str:
    """Render a small, sanitized Markdown subset for generated card content."""
    rendered = markdown(value, extensions=["sane_lists"])
    cleaned = bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes={"a": ["href", "title"]},
        protocols={"http", "https", "mailto"},
        strip=True,
    )
    soup = BeautifulSoup(cleaned, "html.parser")
    for link in soup.find_all("a"):
        link["href"] = sanitize_url(link.get("href", ""))
        link["target"] = "_blank"
        link["rel"] = "noopener noreferrer"
    return str(soup)
