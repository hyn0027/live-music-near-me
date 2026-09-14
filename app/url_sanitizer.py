import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_URL = re.compile(r"https?://[^\s\"'<>\)]+", re.IGNORECASE)


def sanitize_url(url: str) -> str:
    """Remove credentials and signatures from AWS presigned URLs."""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("x-amz-")
    ]
    return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))


def sanitize_urls_in_text(value: str) -> str:
    return _URL.sub(lambda match: sanitize_url(match.group()), value)
