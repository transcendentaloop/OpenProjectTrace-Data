#!/usr/bin/env python3
"""Verify immutable private-automation checkout references without credentials."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / ".github" / "automation-source.json"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str) -> ValueError:
    return ValueError(f"private automation workflow contract failed: {message}")


def main() -> int:
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    expected_keys = {
        "schemaVersion",
        "ownerProject",
        "commit",
        "entrypoint",
        "workflows",
        "evidenceBoundary",
    }
    if set(source) != expected_keys:
        raise fail("automation-source.json has unexpected or missing fields")
    if source["schemaVersion"] != "open-project-trace-data.automation-source/v1":
        raise fail("automation-source.json schemaVersion is unsupported")
    if source["ownerProject"] != "open-project-trace":
        raise fail("the automation owner project changed without review")
    if source["entrypoint"] != "action.yml":
        raise fail("the private automation entrypoint changed without review")

    commit = source["commit"]
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        raise fail("commit must be one full lowercase immutable Git SHA-1")
    workflows = source["workflows"]
    if workflows != sorted(set(workflows)) or workflows != [
        ".github/workflows/lower-star-summaries.yml",
        ".github/workflows/refresh.yml",
    ]:
        raise fail("the exact two private-automation workflows must be declared")
    if not isinstance(source["evidenceBoundary"], str) or not source["evidenceBoundary"].strip():
        raise fail("evidenceBoundary must be non-empty")

    for relative in workflows:
        workflow = ROOT / relative
        text = workflow.read_text(encoding="utf-8")
        required_fragments = (
            "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "repository: ${{ secrets.AUTOMATION_REPOSITORY }}",
            f"ref: {commit}",
            "ssh-key: ${{ secrets.AUTOMATION_DEPLOY_KEY }}",
            "path: .automation",
            "fetch-depth: 1",
            "persist-credentials: false",
            "uses: ./.automation",
        )
        missing = [fragment for fragment in required_fragments if fragment not in text]
        if missing:
            raise fail(f"{relative} is missing required checkout contract: {missing}")
        refs = re.findall(r"(?m)^\s*ref:\s*([^\s#]+)", text)
        if refs != [commit]:
            raise fail(f"{relative} must contain exactly one reviewed automation ref")

    print(
        json.dumps(
            {
                "status": "ok",
                "automationCommit": commit,
                "entrypoint": source["entrypoint"],
                "workflows": workflows,
                "credentialAccess": "not-used",
                "privateSourceAccess": "not-used",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
