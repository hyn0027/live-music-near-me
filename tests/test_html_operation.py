import unittest

from bs4 import BeautifulSoup

from app.html_operation import extract_live_music_data
from app.models import Event


class ExtractLiveMusicDataTests(unittest.TestCase):
    def test_extracts_new_card_format_and_removes_tracking_query(self) -> None:
        soup = BeautifulSoup(
            """
            <a href="https://www.bandsintown.com/e/123-test?came_from=257">
              <div><div>Test Band</div><div>Wed, Sep 30 • 7:00 PM</div><div>Test Hall</div></div>
              <div><img alt="Test Band"></div>
            </a>
            """,
            "html.parser",
        )

        [event] = extract_live_music_data(soup)

        self.assertEqual(event.band, "Test Band")
        self.assertEqual(event.venue, "Test Hall")
        self.assertEqual(event.link, "https://www.bandsintown.com/e/123-test")
        self.assertEqual((event.numerical_month, event.numerical_date), (9, 30))

    def test_ignores_non_event_links(self) -> None:
        soup = BeautifulSoup(
            '<a href="https://www.bandsintown.com/artist/123">Artist</a>',
            "html.parser",
        )
        with self.assertRaisesRegex(ValueError, "No Bandsintown event links"):
            extract_live_music_data(soup)

    def test_deduplicates_event_links(self) -> None:
        card = """
            <a href="/e/123-test">
              <div><div>Band</div><div>Sep 30 - 7 PM</div><div>Hall</div></div>
            </a>
        """
        events = extract_live_music_data(BeautifulSoup(card + card, "html.parser"))
        self.assertEqual(len(events), 1)


class EventDateTests(unittest.TestCase):
    def test_accepts_old_and_new_date_formats(self) -> None:
        for date in ("Sep 30 - 7:00 PM", "Wed, Sep 30 • 7:00 PM", "September 30th"):
            with self.subTest(date=date):
                event = Event(link="/e/1", band="Band", venue="Hall", date=date)
                event.compute_month_and_date()
                self.assertEqual((event.numerical_month, event.numerical_date), (9, 30))


if __name__ == "__main__":
    unittest.main()
