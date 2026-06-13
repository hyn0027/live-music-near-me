from pydantic import BaseModel
from typing import Optional, List
import time
import os
import logging

logger = logging.getLogger(__name__)


class Event(BaseModel):
    link: str
    band: str
    venue: str
    date: str  # e.g. May 12 - 2:00 PM
    numerical_month: Optional[int] = None
    numerical_date: Optional[int] = None
    band_genre: list[str] = []
    must_see: Optional[bool] = None
    detailed_genre: list[str] = []
    band_info: str = ""
    band_details_trustworthy: Optional[bool] = None

    def compute_month_and_date(self) -> "Event":
        month, date_time = self.date.split(" ", 1)
        date = date_time.split(" ")[0]
        numerical_month = time.strptime(month, "%b").tm_mon
        numerical_date = int(date)
        self.numerical_month = numerical_month
        self.numerical_date = numerical_date
        return self

    def clean_link(self) -> "Event":
        # remove query parameters from the link
        self.link = self.link.split("?")[0]
        return self

    def _clean_genre_str(self, genre_str: str) -> str:
        genre_str = genre_str.strip().lower()
        genre_str = genre_str.replace("\n", " ")
        genre_str = genre_str.replace("\r", " ")
        genre_str = genre_str.replace("\t", " ")
        substitution = {
            "‑": " ",
            "-": " ",
            "&amp;": "&",
            "r & b": "r&b",
            "rnb": "r&b",
            "Alt ": "alternative ",
            "Alt.": "alternative ",
            "rock & roll": "rock and roll",
            "rock n roll": "rock and roll",
            "rock'n'roll": "rock and roll",
            "rock 'n' roll": "rock and roll",
        }
        for old, new in substitution.items():
            if old in genre_str:
                genre_str = genre_str.replace(old, new)
        return genre_str

    def clean_genre(self) -> "Event":
        self.band_genre = [self._clean_genre_str(g) for g in self.band_genre]
        self.detailed_genre = [self._clean_genre_str(g) for g in self.detailed_genre]
        self.band_genre = list(set(self.band_genre))
        self.detailed_genre = list(set(self.detailed_genre))
        return self


class EventDB(BaseModel):
    # events are considered the same iff they have the same link
    events: list[Event] = []

    def clean_events(self) -> "EventDB":
        for event in self.events:
            event.compute_month_and_date().clean_link().clean_genre()
        return self

    def get_event(self, link: str) -> Optional[Event]:
        for event in self.events:
            if event.link == link:
                return event
        return None

    def event_exists(self, event: Event) -> bool:
        return any(e.link == event.link for e in self.events)

    def add_event(self, event: Event) -> None:
        if not any(e.link == event.link for e in self.events):
            self.events.append(event)
        else:
            logger.info(
                f"Event with link {event.link} already exists in the database. Skipping."
            )

    def remove_prior_events(self) -> None:
        self.events = [event for event in self.events if not self.event_is_past(event)]

    def event_is_past(self, event: Event) -> bool:
        current_month = time.localtime().tm_mon
        current_date = time.localtime().tm_mday
        if event.numerical_month is None or event.numerical_date is None:
            logger.warning(
                f"Event {event.link} does not have numerical month or date. Cannot determine if it's a past event."
            )
            return False
        if event.numerical_month < current_month:
            logger.info(f"Event {event.link} is a past event. Its on {event.numerical_month}, {event.numerical_date}.")
            return True
        if (
            event.numerical_month == current_month
            and event.numerical_date < current_date
        ):
            logger.info(f"Event {event.link} is a past event. Its on {event.numerical_month}, {event.numerical_date}.")
            return True 
        return False

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=4))

    def load_from_file(self, file_path: str) -> None:
        if file_path is None or not os.path.exists(file_path):
            logger.warning(
                f"Event database file '{file_path}' does not exist. Starting with an empty database."
            )
            self.events = []
            return
        with open(file_path, "r", encoding="utf-8") as file:
            data = file.read()
            loaded_db = EventDB.model_validate_json(data)
            self.events = loaded_db.events


event_db = EventDB()
