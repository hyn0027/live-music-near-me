import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.usage import RunUsage


class RunUsageTests(unittest.TestCase):
    def test_reports_detailed_totals_and_averages(self) -> None:
        usage = RunUsage(model="gpt-test", parsed_events=4, cached_events=2)
        usage.start_request()
        usage.record_response(
            SimpleNamespace(
                usage=SimpleNamespace(
                    input_tokens=100,
                    input_tokens_details=SimpleNamespace(
                        cached_tokens=20,
                        cache_write_tokens=10,
                    ),
                    output_tokens=40,
                    output_tokens_details=SimpleNamespace(reasoning_tokens=15),
                    total_tokens=140,
                ),
                output=[SimpleNamespace(type="web_search_call")],
            )
        )

        report = usage.report()
        self.assertEqual(report["token_totals"]["uncached_input_tokens"], 70)
        self.assertEqual(report["token_totals"]["visible_output_tokens"], 25)
        self.assertEqual(report["api"]["web_search_calls"], 1)
        self.assertEqual(
            report["average_tokens_per_api_event"]["total_tokens"],
            140.0,
        )
        self.assertEqual(
            report["average_tokens_per_parsed_event"]["total_tokens"],
            35.0,
        )

    def test_writes_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "usage.json"
            RunUsage(model="gpt-test").write(str(path))
            report = json.loads(path.read_text())

        self.assertEqual(report["model"], "gpt-test")
        self.assertEqual(report["token_totals"]["total_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
