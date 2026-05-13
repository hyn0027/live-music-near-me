# use beautifulsoup4
from bs4 import BeautifulSoup
import logging

from .models import Event

logger = logging.getLogger(__name__)


def read_and_parse_html(file_path: str) -> BeautifulSoup:
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    return soup


def print_soup(soup: BeautifulSoup, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(soup.prettify())


def extract_live_music_data(soup: BeautifulSoup) -> list[Event]:
    # find div with class infinite-scroll-component
    div = soup.find("div", class_="infinite-scroll-component")
    div_first_child = div.find("div")
    # find all child of div_first_child
    event_list = div_first_child.find_all("div", recursive=False)[1:-1]
    results = []
    for event in event_list:
        event = event.find_all("a", recursive=False)[0]  # has an href attribute
        link = event["href"]
        event = event.find_all("div", recursive=False)[1]
        band_and_venue = event.find_all("div", recursive=False)[0]
        date = event.find_all("div", recursive=False)[1]
        band = band_and_venue.find_all("div", recursive=False)[0]
        venue = band_and_venue.find_all("div", recursive=False)[1]
        results.append(
            Event(
                link=link,
                band=band.text.strip(),
                venue=venue.text.strip(),
                date=date.text.strip(),
            )
            .compute_month_and_date()
            .clean_link()
        )
    return results
