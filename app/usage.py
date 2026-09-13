import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass
class TokenTotals:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    @property
    def uncached_input_tokens(self) -> int:
        return max(
            0,
            self.input_tokens
            - self.cached_input_tokens
            - self.cache_write_input_tokens,
        )

    @property
    def visible_output_tokens(self) -> int:
        return max(0, self.output_tokens - self.reasoning_tokens)

    def add(self, other: "TokenTotals") -> None:
        for name in asdict(self):
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def report(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "uncached_input_tokens": self.uncached_input_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_write_input_tokens": self.cache_write_input_tokens,
            "output_tokens": self.output_tokens,
            "visible_output_tokens": self.visible_output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class RunUsage:
    model: str
    parsed_events: int = 0
    cached_events: int = 0
    deferred_events: int = 0
    api_requests: int = 0
    successful_api_responses: int = 0
    failed_api_requests: int = 0
    web_search_calls: int = 0
    tokens: TokenTotals = field(default_factory=TokenTotals)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def start_request(self) -> None:
        with self._lock:
            self.api_requests += 1

    def record_failure(self) -> None:
        with self._lock:
            self.failed_api_requests += 1

    def record_response(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        input_details = getattr(usage, "input_tokens_details", None)
        output_details = getattr(usage, "output_tokens_details", None)
        response_tokens = TokenTotals(
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            cached_input_tokens=getattr(input_details, "cached_tokens", 0) or 0,
            cache_write_input_tokens=(
                getattr(input_details, "cache_write_tokens", 0) or 0
            ),
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            reasoning_tokens=getattr(output_details, "reasoning_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
        )
        search_calls = sum(
            getattr(item, "type", None) == "web_search_call"
            for item in getattr(response, "output", [])
        )
        with self._lock:
            self.successful_api_responses += 1
            self.web_search_calls += search_calls
            self.tokens.add(response_tokens)

    def _average(self, denominator: int) -> dict[str, float]:
        if denominator == 0:
            return {name: 0.0 for name in self.tokens.report()}
        return {
            name: round(value / denominator, 2)
            for name, value in self.tokens.report().items()
        }

    def report(self) -> dict[str, object]:
        return {
            "model": self.model,
            "events": {
                "parsed": self.parsed_events,
                "cached": self.cached_events,
                "api_enriched": self.successful_api_responses,
                "deferred_unenriched": self.deferred_events,
            },
            "api": {
                "requests": self.api_requests,
                "successful_responses": self.successful_api_responses,
                "failed_requests": self.failed_api_requests,
                "web_search_calls": self.web_search_calls,
            },
            "token_totals": self.tokens.report(),
            "average_tokens_per_api_event": self._average(
                self.successful_api_responses
            ),
            "average_tokens_per_parsed_event": self._average(self.parsed_events),
            "pricing_notes": [
                "Reasoning tokens are included in output_tokens; do not add them twice.",
                "Cached and cache-write tokens are included in input_tokens.",
                "Web-search calls may have a separate per-call fee.",
                "Apply current rates for the model; prices are not hard-coded.",
            ],
        }

    def write(self, path: str) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.report(), indent=2) + "\n",
            encoding="utf-8",
        )
