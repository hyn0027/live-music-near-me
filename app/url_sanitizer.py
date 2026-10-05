import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_URL = re.compile(r"https?://[^\s\"'<>\)]+", re.IGNORECASE)
_AWS_ACCESS_KEY_ID = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
_REDACTED_ACCESS_KEY_ID = "[REDACTED_AWS_ACCESS_KEY_ID]"


def contains_aws_access_key_id(value: str) -> bool:
    return _AWS_ACCESS_KEY_ID.search(value) is not None


def redact_aws_credentials(value: str) -> str:
    return _AWS_ACCESS_KEY_ID.sub(_REDACTED_ACCESS_KEY_ID, value)


def sanitize_url(url: str) -> str:
    """Remove credentials and signatures from AWS presigned URLs."""
    parts = urlsplit(url)
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("x-amz-")
        and not contains_aws_access_key_id(value)
    ]
    cleaned = urlunsplit(parts._replace(query=urlencode(query, doseq=True)))
    return redact_aws_credentials(cleaned)


def sanitize_urls_in_text(value: str) -> str:
    cleaned = _URL.sub(lambda match: sanitize_url(match.group()), value)
    return redact_aws_credentials(cleaned)


def sanitize_url_data(value):
    """Recursively remove AWS signing parameters from JSON-compatible data."""
    if isinstance(value, str):
        return sanitize_urls_in_text(value)
    if isinstance(value, list):
        return [sanitize_url_data(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_url_data(item) for key, item in value.items()}
    return value
