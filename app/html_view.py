from calendar import month_name
from dataclasses import dataclass

from .markdown_renderer import render_card_markdown
from .models import Event
from .url_sanitizer import sanitize_url


PAGE_SIZE = 21


@dataclass(frozen=True)
class EventView:
    event: Event
    genres_data: str
    detailed_genres_data: str
    must_see_data: str
    band_info_html: str
    recommendation_reasons_html: list[str]
    source_urls: list[str]


def _sort_key(event: Event) -> tuple[int, int, str]:
    return (event.numerical_month or 99, event.numerical_date or 99, event.date)


def _clean_genres(genres: list[str]) -> list[str]:
    return [genre.strip() for genre in genres if genre.strip()]


def _all_genres(events: list[Event], attribute: str) -> list[str]:
    genres = {
        genre
        for event in events
        for genre in _clean_genres(getattr(event, attribute))
    }
    return sorted(genres, key=str.casefold)


def _format_event_date(event: Event) -> str:
    month, day = event.numerical_month, event.numerical_date
    if month is None or day is None:
        return ""
    name = month_name[month] if 1 <= month <= 12 else str(month)
    return f"{name} {day}"


def _time_span(events: list[Event]) -> str:
    dates = [_format_event_date(event) for event in events]
    dates = [date for date in dates if date]
    if not dates:
        return "Time span unavailable"
    return dates[0] if len(dates) == 1 else f"{dates[0]} – {dates[-1]}"


def _event_view(event: Event) -> EventView:
    return EventView(
        event=event,
        genres_data="|".join(genre.lower() for genre in _clean_genres(event.band_genre)),
        detailed_genres_data="|".join(
            genre.lower() for genre in _clean_genres(event.detailed_genre)
        ),
        must_see_data="unknown" if event.must_see is None else str(event.must_see).lower(),
        band_info_html=render_card_markdown(event.band_info),
        recommendation_reasons_html=[
            render_card_markdown(reason) for reason in event.recommendation_reasons
        ],
        source_urls=[sanitize_url(url) for url in event.source_urls],
    )


def build_page_context(events: list[Event], area: str) -> dict[str, object]:
    sorted_events = sorted(events, key=_sort_key)
    return {
        "area": area,
        "event_count": len(sorted_events),
        "events": [_event_view(event) for event in sorted_events],
        "genres": _all_genres(sorted_events, "band_genre"),
        "detailed_genres": _all_genres(sorted_events, "detailed_genre"),
        "page_size": PAGE_SIZE,
        "time_span": _time_span(sorted_events),
    }
