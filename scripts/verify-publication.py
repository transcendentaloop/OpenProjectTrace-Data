#!/usr/bin/env python3
"""Verify a fetched public data snapshot without invoking private automation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    ".nojekyll",
    "catalog.json",
    "facets.json",
    "meta.json",
    "search-index.json",
}
JSON_FILES = REQUIRED_FILES - {".nojekyll"}


def git(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout


def parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("meta.json generated_at is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("meta.json generated_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="origin/data")
    parser.add_argument("--max-age-hours", type=float, default=48.0)
    args = parser.parse_args()
    if args.max_age_hours <= 0:
        parser.error("--max-age-hours must be positive")

    revision = str(git("rev-parse", "--verify", f"{args.ref}^{{commit}}")).strip()
    tree = set(str(git("ls-tree", "--name-only", args.ref)).splitlines())
    missing = sorted(REQUIRED_FILES - tree)
    if missing:
        raise ValueError(f"published snapshot is missing required files: {', '.join(missing)}")

    documents: dict[str, object] = {}
    sizes: dict[str, int] = {}
    for path in sorted(REQUIRED_FILES):
        size = int(str(git("cat-file", "-s", f"{args.ref}:{path}")).strip())
        sizes[path] = size
        if path in JSON_FILES:
            raw = git("show", f"{args.ref}:{path}", text=False)
            documents[path] = json.loads(raw)

    meta = documents["meta.json"]
    if not isinstance(meta, dict) or meta.get("schema_version") != 3:
        raise ValueError("meta.json must be an object using schema_version 3")
    candidate_count = meta.get("candidate_count")
    if not isinstance(candidate_count, int) or candidate_count <= 0:
        raise ValueError("meta.json candidate_count must be a positive integer")
    generated_at = parse_timestamp(meta.get("generated_at"))
    age_hours = (datetime.now(timezone.utc) - generated_at).total_seconds() / 3600
    if age_hours < -1:
        raise ValueError("meta.json generated_at is unexpectedly in the future")
    if age_hours > args.max_age_hours:
        raise ValueError(
            f"published snapshot is stale: {age_hours:.1f}h exceeds {args.max_age_hours:.1f}h"
        )

    summary = {
        "status": "ok",
        "ref": args.ref,
        "revision": revision,
        "generated_at": generated_at.isoformat(),
        "age_hours": round(age_hours, 1),
        "candidate_count": candidate_count,
        "summary_ready_count": meta.get("summary_ready_count"),
        "required_blob_sizes": sizes,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (json.JSONDecodeError, subprocess.CalledProcessError, ValueError) as error:
        print(f"publication verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)
