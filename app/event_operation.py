from typing import Optional, List
from .models import Event, event_db
from pydantic import BaseModel
from openai import OpenAI
import logging

import asyncio
from tqdm.asyncio import tqdm_asyncio

logger = logging.getLogger(__name__)


async def get_bands_details_async(
    events: List[Event],
    api_key: str,
    event_db_path: str,
    area: str,
    max_concurrent: int = 20,
) -> List[Event]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_details(event: Event) -> Event:
        async with semaphore:
            return await asyncio.to_thread(
                get_band_details,
                event,
                api_key,
                area,
            )

    results: list[Event | None] = [None] * len(events)
    events_to_fetch: list[tuple[int, Event]] = []

    for i, event in enumerate(events):
        cached_event = event_db.get_event(event.link)
        if cached_event is not None:
            results[i] = cached_event
        else:
            events_to_fetch.append((i, event))

    logger.info(
        f"{len(events) - len(events_to_fetch)} events found in cache, {len(events_to_fetch)} events to fetch from API."
    )

    fetched_events = await tqdm_asyncio.gather(
        *(fetch_details(event) for _, event in events_to_fetch),
        desc="Fetching band details",
        total=len(events_to_fetch),
    )

    for (i, _), fetched_event in zip(events_to_fetch, fetched_events):
        event_db.add_event(fetched_event.clean_genre().clean_link())
        results[i] = fetched_event

    if events_to_fetch:
        event_db.save_to_file(event_db_path)

    return [event for event in results if event is not None]


def get_band_details(event: Event, api_key: str, area: str) -> Event:
    prompt = f"""For a given band and its upcoming event details, please provide the band's genre and a very concise introduction about the band.

Band name: {event.band}
Venue: {event.venue} near {area}
Date: {event.date}
Link to the event page: {event.link}"""

    class ModelResponse(BaseModel):
        band_genre: Optional[list[str]]
        band_info: Optional[str]
        confident: bool

    client = OpenAI(api_key=api_key)
    response = client.responses.parse(
        model="gpt-5-mini",
        input=prompt,
        text_format=ModelResponse,
        tools=[{"type": "web_search"}],
        reasoning={"effort": "low"},
        top_p=0,
        prompt_cache_key="get_band_details",
        prompt_cache_retention="24h",
        max_tool_calls=5,
    )
    parsed_response = ModelResponse.model_validate(response.output_parsed)
    event.band_genre = parsed_response.band_genre or []
    event.band_info = parsed_response.band_info or ""
    event.band_details_trustworthy = parsed_response.confident
    return event
