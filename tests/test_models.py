import tempfile
import unittest
from pathlib import Path

from app.models import Event, EventDB


class EventDBSecurityTests(unittest.TestCase):
    def test_never_persists_aws_presigned_credentials(self) -> None:
        signed_url = (
            "https://example.s3.amazonaws.com/bio?language=en"
            "&X-Amz-Credential=secret&X-Amz-Signature=signature"
        )
        database = EventDB(
            events=[
                Event(
                    link="https://www.bandsintown.com/e/123",
                    band="Test Band",
                    venue="Test Hall",
                    date="Sep 30 - 7 PM",
                    band_info=f"Read [more]({signed_url}).",
                    recommendation_reasons=[f"Source: {signed_url}"],
                    source_urls=[signed_url],
                )
            ]
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            database.save_to_file(str(path))
            stored = path.read_text()

        self.assertNotIn("X-Amz-", stored)
        self.assertNotIn("secret", stored)
        self.assertIn("language=en", stored)


if __name__ == "__main__":
    unittest.main()
