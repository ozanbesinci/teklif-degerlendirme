"""Synthetic local processes only: no Codex/model or network calls."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from oturum_kaydi import read_native_session, native_receipt_valid, stream_process


class SessionTests(unittest.TestCase):
    def test_seal_binds_accepting_model_not_later_context(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "log.jsonl"
            seal = {"run_id": "fixture", "artifact_sha256": "a" * 64}
            events = [
                {"type": "session_meta", "payload": {"id": "session", "cwd": folder}},
                {"type": "turn_context", "payload": {"model": "gpt-6-astra", "effort": "high"}},
                {"type": "response_item", "payload": {"type": "function_call_output", "output": json.dumps({"output": "TEKLIF_RESULT_SEAL:" + json.dumps(seal)})}},
                {"type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "high"}}]
            path.write_text("\n".join(json.dumps(x) for x in events) + "\n", encoding="utf-8")
            receipt = read_native_session(path, seal=seal)
            self.assertEqual(receipt["model"], "gpt-6-astra")
            self.assertTrue(native_receipt_valid(receipt))
            with path.open("a", encoding="utf-8") as stream: stream.write('{"new":"event"}\n')
            self.assertTrue(native_receipt_valid(receipt))
            path.write_text(path.read_text().replace("gpt-6-astra", "fake-model"), encoding="utf-8")
            self.assertFalse(native_receipt_valid(receipt))

    def test_marker_in_prompt_is_not_tool_result(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "log.jsonl"
            events = [{"type": "session_meta", "payload": {"id": "session", "cwd": folder}},
                      {"type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "high"}},
                      {"type": "response_item", "payload": {"type": "message", "output": 'TEKLIF_RESULT_SEAL:{"fixture":true}'}}]
            path.write_text("\n".join(json.dumps(x) for x in events), encoding="utf-8")
            with self.assertRaises(ValueError): read_native_session(path, seal={"fixture": True})

    def test_stream_aggregates_usage_without_recording_source_text(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = [{"type": "thread.started", "thread_id": "synthetic"},
                      {"type": "item.completed", "item": {"type": "agent_message", "text": "PRIVATE_FIXTURE"}},
                      {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}},
                      {"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 3}}]
            code = "import sys,json;sys.stdin.read();events=" + repr(events) + ";[print(json.dumps(e),flush=True) for e in events]"
            result = stream_process([sys.executable, "-c", code], "synthetic", root, root / "events.jsonl", root / "stderr.txt")
            self.assertEqual(result["status"], "COMPLETED")
            self.assertEqual(result["usage"], {"input_tokens": 30, "output_tokens": 5})
            self.assertEqual(result["session_id"], "synthetic")
            self.assertNotIn("PRIVATE_FIXTURE", (root / "events.jsonl").read_text())

    def test_timeout_and_failure_are_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for code, timeout, expected in [("import time;time.sleep(3)", .1, "TIMED_OUT"), ("raise SystemExit(2)", None, "FAILED")]:
                result = stream_process([sys.executable, "-c", code], "", root, root / "events.jsonl", root / "stderr.txt", timeout)
                self.assertEqual(result["status"], expected)

    def test_keyboard_interrupt_returns_terminal_failure_for_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("oturum_kaydi.queue.Queue.get", side_effect=KeyboardInterrupt):
                result = stream_process([sys.executable, "-c", "import time;time.sleep(30)"], "", root,
                                        root / "events.jsonl", root / "stderr.txt")
            self.assertEqual(result["status"], "FAILED")
            self.assertEqual(result["returncode"], 130)


if __name__ == "__main__": unittest.main()
