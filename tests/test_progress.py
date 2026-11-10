import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parents[1] / "skills" / "lzl-weaver-evolve"
          / "scripts" / "progress.py")
SPEC = importlib.util.spec_from_file_location("progress", SCRIPT)
progress = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(progress)


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name) / "state.json"

    def update(self, revision, sources):
        return progress.update_state(self.state, {
            "expected_revision": revision, "sources": sources
        })

    def candidate(self, status="pending", **extra):
        return {"id": "session-a:decision-1", "status": status,
                "evidence": "session-a#message-5", **extra}

    def initial(self):
        return self.update(0, [{
            "id": "codex:project-a", "coverage": "complete", "cursor": {"offset": 100},
            "candidates": [self.candidate()]
        }])

    def test_show_missing_is_read_only_even_when_parent_missing(self):
        missing = self.state.parent / "absent" / "state.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "show", "--state", str(missing)],
            check=True, text=True, capture_output=True
        )
        self.assertEqual(json.loads(result.stdout), progress.empty_state())
        self.assertFalse(missing.parent.exists())

    def test_pending_survives_cursor_advance_and_omission(self):
        self.initial()
        state = self.update(1, [{
            "id": "codex:project-a", "coverage": "complete", "cursor": {"offset": 200}
        }])
        self.assertEqual(state["sources"]["codex:project-a"]["cursor"], {"offset": 200})
        self.assertEqual(state["candidates"]["session-a:decision-1"]["status"], "pending")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "show", "--state", str(self.state)],
            check=True, text=True, capture_output=True
        )
        self.assertEqual(json.loads(result.stdout), state)

    def test_unavailable_source_does_not_block_other_source(self):
        self.initial()
        state = self.update(1, [
            {"id": "codex:project-a", "coverage": "unavailable"},
            {"id": "codex:project-b", "coverage": "complete", "cursor": "session-b"}
        ])
        self.assertEqual(state["sources"]["codex:project-a"], {
            "coverage": "unavailable", "cursor": {"offset": 100}
        })
        self.assertEqual(state["sources"]["codex:project-b"]["cursor"], "session-b")
        self.assertIn("session-a:decision-1", state["candidates"])

    def test_incomplete_coverage_cannot_advance_cursor_and_entire_batch_is_atomic(self):
        self.initial()
        original = self.state.read_bytes()
        for coverage in ("partial", "unavailable"):
            with self.subTest(coverage=coverage):
                with self.assertRaisesRegex(progress.ProgressError, "cannot change cursor"):
                    self.update(1, [
                        {"id": "codex:project-b", "coverage": "complete", "cursor": 7},
                        {"id": "codex:project-a", "coverage": coverage,
                         "cursor": {"offset": 200}}
                    ])
                self.assertEqual(self.state.read_bytes(), original)

    def test_partial_scan_can_preserve_cursor_and_add_pending(self):
        self.initial()
        state = self.update(1, [{
            "id": "codex:project-a", "coverage": "partial", "cursor": {"offset": 100},
            "candidates": [{"id": "session-a:decision-2", "status": "pending",
                            "evidence": "session-a#message-8"}]
        }])
        self.assertEqual(len(state["candidates"]), 2)
        self.assertEqual(state["sources"]["codex:project-a"]["cursor"], {"offset": 100})

    def test_opaque_cursor_distinguishes_boolean_from_number(self):
        self.update(0, [{"id": "source-a", "coverage": "complete", "cursor": 1}])
        with self.assertRaisesRegex(progress.ProgressError, "cannot change cursor"):
            self.update(1, [{"id": "source-a", "coverage": "partial", "cursor": True}])
        state = self.update(1, [{"id": "source-a", "coverage": "complete", "cursor": True}])
        self.assertIs(state["sources"]["source-a"]["cursor"], True)
        self.assertEqual(state["revision"], 2)

    def test_repeated_candidate_is_idempotent(self):
        first = self.initial()
        original = self.state.read_bytes()
        second = self.update(1, [{
            "id": "codex:project-a", "coverage": "complete", "cursor": {"offset": 100},
            "candidates": [self.candidate(), self.candidate()]
        }])
        self.assertEqual(second, first)
        self.assertEqual(self.state.read_bytes(), original)

    def test_candidate_identity_cannot_change_source_or_evidence(self):
        self.initial()
        original = self.state.read_bytes()
        for source, candidate in (
            ("codex:project-b", self.candidate()),
            ("codex:project-a", self.candidate(evidence="other-session#message-5"))
        ):
            with self.subTest(source=source, evidence=candidate["evidence"]):
                with self.assertRaisesRegex(progress.ProgressError, "identity conflict"):
                    self.update(1, [{"id": source, "coverage": "complete",
                                     "candidates": [candidate]}])
                self.assertEqual(self.state.read_bytes(), original)

    def test_terminal_status_cannot_return_to_pending(self):
        self.initial()
        for terminal in ("applied", "excluded"):
            with self.subTest(status=terminal):
                state = progress.read_state(self.state)
                state = self.update(state["revision"], [{
                    "id": "codex:project-a", "coverage": "complete",
                    "candidates": [self.candidate(terminal, target="docs/decision.md#choice")]
                }])
                original = self.state.read_bytes()
                with self.assertRaisesRegex(progress.ProgressError, "cannot reopen"):
                    self.update(state["revision"], [{
                        "id": "codex:project-a", "coverage": "complete",
                        "candidates": [self.candidate()]
                    }])
                self.assertEqual(self.state.read_bytes(), original)

    def test_stale_revision_fails_before_any_changes(self):
        self.initial()
        original = self.state.read_bytes()
        with self.assertRaisesRegex(progress.ProgressError, "revision conflict"):
            self.update(0, [{"id": "codex:project-b", "coverage": "complete"}])
        self.assertEqual(self.state.read_bytes(), original)

    def test_failed_replace_preserves_old_file_and_cleans_temporary_and_lock(self):
        self.initial()
        original = self.state.read_bytes()
        with patch.object(progress.os, "replace", side_effect=OSError("disk write failure")):
            with self.assertRaisesRegex(OSError, "disk write failure"):
                self.update(1, [{"id": "codex:project-b", "coverage": "complete"}])
        self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(list(self.state.parent.iterdir()), [self.state])

    def test_existing_lock_fails_without_altering_state_or_lock(self):
        self.initial()
        original = self.state.read_bytes()
        lock = self.state.with_name(self.state.name + ".lock")
        lock.write_text('{"pid": 1234}', encoding="utf-8")
        with self.assertRaisesRegex(progress.ProgressError, "state is locked"):
            self.update(1, [])
        self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(lock.read_text(encoding="utf-8"), '{"pid": 1234}')

    def test_symlink_state_refuses_update(self):
        target = self.state.parent / "target.json"
        target.write_text(json.dumps(progress.empty_state()), encoding="utf-8")
        original = target.read_bytes()
        try:
            self.state.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable on this platform")
        with self.assertRaisesRegex(progress.ProgressError, "symlink"):
            self.update(0, [{"id": "codex:project-a", "coverage": "complete"}])
        self.assertEqual(target.read_bytes(), original)
        self.assertFalse(self.state.with_name(self.state.name + ".lock").exists())

    def test_cli_update_and_revision_failure_return_structured_output_and_clear_error(self):
        batch_path = self.state.parent / "batch.json"
        batch_path.write_text(json.dumps({"expected_revision": 0, "sources": [
            {"id": "codex:project-a", "coverage": "complete", "cursor": "message-10",
             "candidates": [self.candidate()]}
        ]}), encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "update", "--state", str(self.state),
                   "--batch", str(batch_path)]
        success = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(json.loads(success.stdout)["revision"], 1)
        conflict = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(conflict.returncode, 1)
        self.assertIn("revision conflict", conflict.stderr)
        self.assertEqual(conflict.stdout, "")

    def test_unknown_fields_and_malformed_input_fail_without_creating_state(self):
        for source in (
            {"id": "source-a", "coverage": "complete", "transcript": "not stored"},
            {"id": "source-a", "coverage": "complete", "candidates": [{
                "id": "candidate-1", "status": "pending", "evidence": "msg-1", "body": "not stored"
            }]}
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(progress.ProgressError, "unknown fields"):
                    self.update(0, [source])
                self.assertFalse(self.state.exists())
        self.state.write_text("broken JSON", encoding="utf-8")
        with self.assertRaisesRegex(progress.ProgressError, "cannot read JSON"):
            self.update(0, [])
        self.assertEqual(self.state.read_text(encoding="utf-8"), "broken JSON")

    def test_malformed_status_and_coverage_are_clear_validation_errors(self):
        for source in (
            {"id": "source-a", "coverage": []},
            {"id": "source-a", "coverage": "complete", "candidates": [{
                "id": "candidate-1", "status": {}, "evidence": "msg-1"
            }]}
        ):
            with self.subTest(source=source):
                with self.assertRaises(progress.ProgressError):
                    self.update(0, [source])
                self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
