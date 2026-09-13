import tempfile
import unittest
from pathlib import Path

from app.generate_html import generate_html
from app.models import Event


class GenerateHtmlTests(unittest.TestCase):
    def test_includes_browser_local_event_shortlist(self) -> None:
        event = Event(
            link="https://www.bandsintown.com/e/123-test",
            band="Test Band",
            venue="Test Hall",
            date="Sep 30 - 7 PM",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.html"
            generate_html([event], str(path), "Pittsburgh")
            html = path.read_text()

        self.assertIn('class="save-event"', html)
        self.assertIn('id="saved-only"', html)
        self.assertIn('id="export-saved"', html)
        self.assertIn('id="event-search"', html)
        self.assertIn('id="events-per-row"', html)
        self.assertIn("localStorage", html)
        self.assertIn("matchesSearch", html)
        self.assertIn("loadColumnPreference", html)
        self.assertIn(event.link, html)

    def test_renders_safe_markdown_links_in_cards(self) -> None:
        event = Event(
            link="https://www.bandsintown.com/e/123-test",
            band="Test Band",
            venue="Test Hall",
            date="Sep 30 - 7 PM",
            band_info=(
                "Read the [artist biography](https://example.com/bio). "
                "<script>alert('unsafe')</script>"
            ),
            recommendation_reasons=[
                "Praised by [Music Review](https://example.com/review)."
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.html"
            generate_html([event], str(path), "Pittsburgh")
            html = path.read_text()

        self.assertIn(
            '<a href="https://example.com/bio" rel="noopener noreferrer" target="_blank">artist biography</a>',
            html,
        )
        self.assertIn(">Music Review</a>", html)
        self.assertNotIn("<script>alert", html)


if __name__ == "__main__":
    unittest.main()
