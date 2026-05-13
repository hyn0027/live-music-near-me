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

    def clean_genre(self) -> "Event":
        self.band_genre = [genre.strip() for genre in self.band_genre]
        self.band_genre = [genre.capitalize() for genre in self.band_genre]
        subtitution = {
            "R & B": "R&B",
            "RnB": "R&B",
            "R & b": "R&B",
            "R&b": "R&B",
            "r&b": "R&B",
            "r & b": "R&B",
            "Hip Hop": "Hip-Hop",
        }
        for i in range(len(self.band_genre)):
            for old, new in subtitution.items():
                if old in self.band_genre[i]:
                    self.band_genre[i] = self.band_genre[i].replace(old, new)
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
        for event in self.events:
            if self.event_is_past(event):
                logger.info(
                    f"Event {event.link} is a past event and will be removed from the database."
                )
                self.events.remove(event)

    def event_is_past(self, event: Event) -> bool:
        current_month = time.localtime().tm_mon
        current_date = time.localtime().tm_mday
        if event.numerical_month is None or event.numerical_date is None:
            logger.warning(
                f"Event {event.link} does not have numerical month or date. Cannot determine if it's a past event."
            )
            return False
        if event.numerical_month < current_month:
            return True
        if (
            event.numerical_month == current_month
            and event.numerical_date < current_date
        ):
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
