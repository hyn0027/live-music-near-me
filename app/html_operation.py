import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .models import Event

logger = logging.getLogger(__name__)

_EVENT_PATH = re.compile(r"/e/\d+(?:-|$)")


def read_and_parse_html(file_path: str) -> BeautifulSoup:
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    return soup


def print_soup(soup: BeautifulSoup, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(soup.prettify())


def _is_event_link(tag: Tag) -> bool:
    href = tag.get("href")
    return isinstance(href, str) and _EVENT_PATH.match(urlparse(href).path) is not None


def _parse_event_link(link: Tag) -> Event:
    """Parse a card without relying on Bandsintown's generated CSS classes."""
    content_blocks = link.find_all("div", recursive=False)
    if not content_blocks:
        raise ValueError("event link has no content block")

    fields = content_blocks[0].find_all("div", recursive=False)
    if len(fields) < 3:
        raise ValueError(f"expected band, date, and venue fields; found {len(fields)}")

    band, date, venue = (field.get_text(" ", strip=True) for field in fields[:3])
    if not all((band, date, venue)):
        raise ValueError("band, date, or venue is empty")

    return (
        Event(link=str(link["href"]), band=band, venue=venue, date=date)
        .compute_month_and_date()
        .clean_link()
    )


def extract_live_music_data(soup: BeautifulSoup) -> list[Event]:
    """Extract unique event cards from a saved Bandsintown results page."""
    links = soup.find_all(_is_event_link)
    if not links:
        raise ValueError("No Bandsintown event links found; the page format may have changed")

    events: list[Event] = []
    seen_links: set[str] = set()
    for link in links:
        try:
            event = _parse_event_link(link)
        except (KeyError, TypeError, ValueError) as error:
            logger.warning("Skipping malformed Bandsintown event card: %s", error)
            continue
        if event.link not in seen_links:
            seen_links.add(event.link)
            events.append(event)

    if not events:
        raise ValueError("Bandsintown event links were found, but none could be parsed")
    logger.info("Extracted %d unique Bandsintown events", len(events))
    return events
