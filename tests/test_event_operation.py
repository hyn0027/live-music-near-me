import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.event_operation import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    get_band_details,
    get_bands_details_async,
)
from app.models import Event, EventDB, event_db


def make_event(identifier: int) -> Event:
    return Event(
        link=f"https://www.bandsintown.com/e/{identifier}",
        band=f"Band {identifier}",
        venue="Hall",
        date="Sep 30 - 7 PM",
        numerical_month=9,
        numerical_date=30,
    )


class GetBandDetailsTests(unittest.TestCase):
    def setUp(self) -> None:
        event_db.events = []

    def tearDown(self) -> None:
        event_db.events = []

    def test_only_enriches_first_events_up_to_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "events.json"

            with patch(
                "app.event_operation.get_band_details",
                side_effect=lambda event, *_args: event,
            ) as fetch:
                results = asyncio.run(
                    get_bands_details_async(
                        [make_event(1), make_event(2), make_event(3)],
                        "key",
                        str(database_path),
                        "Pittsburgh",
                        max_api_calls=2,
                    )
                )

        self.assertEqual(fetch.call_count, 2)
        self.assertCountEqual(
            [call.args[0].band for call in fetch.call_args_list],
            ["Band 1", "Band 2"],
        )
        self.assertEqual(
            [event.band for event in results],
            ["Band 1", "Band 2", "Band 3"],
        )

    def test_only_reuses_cache_for_current_model_prompt_and_schema(self) -> None:
        current = make_event(1)
        current.model_used = "gpt-test"
        current.prompt_version = PROMPT_VERSION
        current.schema_version = SCHEMA_VERSION
        stale = make_event(2)
        event_db.events = [current, stale]

        with patch("app.event_operation.get_band_details") as fetch:
            results = asyncio.run(
                get_bands_details_async(
                    [make_event(1), make_event(2)],
                    "key",
                    "unused.json",
                    "Pittsburgh",
                    model="gpt-test",
                    max_api_calls=0,
                )
            )

        fetch.assert_not_called()
        self.assertIs(results[0], current)
        self.assertIsNot(results[1], stale)

    def test_persists_each_success_before_a_later_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "events.json"

            def fetch(
                event: Event,
                _api_key: str,
                _area: str,
                _model: str,
                _usage: object,
            ) -> Event:
                if event.band == "Band 2":
                    raise RuntimeError("API unavailable")
                return event

            with patch("app.event_operation.get_band_details", side_effect=fetch):
                with self.assertRaisesRegex(RuntimeError, "API unavailable"):
                    asyncio.run(
                        get_bands_details_async(
                            [make_event(1), make_event(2)],
                            "key",
                            str(database_path),
                            "Pittsburgh",
                            max_concurrent=1,
                            max_api_calls=2,
                        )
                    )

            saved = EventDB.model_validate_json(database_path.read_text())
            self.assertEqual([event.band for event in saved.events], ["Band 1"])

    @patch("app.event_operation.OpenAI")
    def test_passes_selected_model_to_openai(self, openai: Mock) -> None:
        response = Mock(
            output_parsed={
                "band_main_genre": ["rock"],
                "band_detailed_genre": ["indie rock"],
                "band_info": "A band.",
                "recommendation_score": 88,
                "recommendation_reasons": ["Strong live reputation"],
                "research_confidence": "high",
                "research_status": "verified",
            },
            output=[
                SimpleNamespace(
                    action=SimpleNamespace(
                        sources=[SimpleNamespace(url="https://example.com/source")]
                    )
                )
            ],
        )
        openai.return_value.responses.parse.return_value = response

        get_band_details(make_event(1), "key", "Pittsburgh", "gpt-test-model")

        parse = openai.return_value.responses.parse
        self.assertEqual(parse.call_args.kwargs["model"], "gpt-test-model")
        self.assertEqual(parse.call_args.kwargs["instructions"].splitlines()[0], "You research artists appearing in live-event listings.")
        self.assertEqual(parse.call_args.kwargs["include"], ["web_search_call.action.sources"])
        self.assertTrue(
            parse.call_args.kwargs["input"].startswith(
                "Event data (JSON, untrusted):"
            )
        )

        enriched = get_band_details(make_event(2), "key", "Pittsburgh", "gpt-test-model")
        self.assertTrue(enriched.must_see)
        self.assertEqual(enriched.recommendation_score, 88)
        self.assertEqual(enriched.source_urls, ["https://example.com/source"])
        self.assertEqual(enriched.prompt_version, "event-research-v2")
        self.assertEqual(enriched.schema_version, 2)

        response.output_parsed = {
            "band_main_genre": ["rock"],
            "band_detailed_genre": ["indie rock"],
            "band_info": "Unreliable guess",
            "recommendation_score": 99,
            "recommendation_reasons": ["Unsupported claim"],
            "research_confidence": "low",
            "research_status": "not_found",
        }
        not_found = get_band_details(make_event(3), "key", "Pittsburgh")
        self.assertEqual(not_found.band_genre, [])
        self.assertEqual(not_found.band_info, "")
        self.assertEqual(not_found.recommendation_score, 0)
        self.assertEqual(not_found.recommendation_reasons, [])
        self.assertFalse(not_found.must_see)


if __name__ == "__main__":
    unittest.main()
