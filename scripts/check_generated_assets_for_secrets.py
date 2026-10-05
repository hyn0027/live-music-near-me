#!/usr/bin/env python3
"""Fail when generated assets contain common AWS credential markers."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


DEFAULT_PATHS = (".asset/event_db.json", ".asset/generated_page.html")
PATTERNS = (
    re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(r"x-amz-(?:credential|signature|security-token)", re.IGNORECASE),
    re.compile(r"aws_(?:secret_access_key|session_token)\s*[:=]", re.IGNORECASE),
)


def staged_content(path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or b"\0" in result.stdout:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def working_content(path: str) -> str | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    data = file_path.read_bytes()
    return None if b"\0" in data else data.decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()

    contaminated = []
    read = staged_content if args.staged else working_content
    for path in args.paths:
        content = read(path)
        if content is not None and any(pattern.search(content) for pattern in PATTERNS):
            contaminated.append(path)

    if contaminated:
        print("AWS credential material detected; refusing to continue:", file=sys.stderr)
        for path in contaminated:
            print(f"  {path}", file=sys.stderr)
        print("Run music-finder with the current code to regenerate clean assets.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
