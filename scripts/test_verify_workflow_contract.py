#!/usr/bin/env python3
"""Regression tests for the immutable automation checkout contract."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify-workflow-contract.py"
SPEC = importlib.util.spec_from_file_location("verify_workflow_contract", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WorkflowContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for relative in (
            ".github/automation-source.json",
            ".github/workflows/lower-star-summaries.yml",
            ".github/workflows/refresh.yml",
        ):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.previous_root = MODULE.ROOT
        self.previous_source_path = MODULE.SOURCE_PATH
        MODULE.ROOT = self.root
        MODULE.SOURCE_PATH = self.root / ".github" / "automation-source.json"

    def tearDown(self) -> None:
        MODULE.ROOT = self.previous_root
        MODULE.SOURCE_PATH = self.previous_source_path
        self.temp.cleanup()

    def test_current_contract_passes_without_private_access(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(MODULE.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["credentialAccess"], "not-used")
        self.assertEqual(result["privateSourceAccess"], "not-used")

    def test_branch_reference_fails_closed(self) -> None:
        workflow = self.root / ".github" / "workflows" / "refresh.yml"
        commit = json.loads(MODULE.SOURCE_PATH.read_text(encoding="utf-8"))["commit"]
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                f"ref: {commit}",
                "ref: main",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing required checkout contract"):
            MODULE.main()

    def test_abbreviated_source_commit_fails_closed(self) -> None:
        source = json.loads(MODULE.SOURCE_PATH.read_text(encoding="utf-8"))
        source["commit"] = source["commit"][:12]
        MODULE.SOURCE_PATH.write_text(json.dumps(source), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "full lowercase immutable Git SHA-1"):
            MODULE.main()


if __name__ == "__main__":
    unittest.main()
