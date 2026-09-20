"""Stdlib regression tests for the bounded teklif runtime."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path
from test_cikti_denetimi import workbook_fixture
import ajan_yonetimi as runtime

SCRIPT = Path(__file__).with_name("ajan_yonetimi.py")
PYTHON = __import__("sys").executable


class AjanYonetimiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="teklif-control-"))
        self.source = self.tmp / "source"; self.source.mkdir()
        (self.source / "a.txt").write_text("aynı veri", encoding="utf-8")
        (self.source / "b.txt").write_text("aynı veri", encoding="utf-8")
        self.out = self.tmp / "isolated-output"

    def tearDown(self) -> None:
        if (self.out / "analysis-manifest.json").exists():
            self.invoke("close", "--output-dir", str(self.out), "--abort")
        shutil.rmtree(self.tmp)

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([PYTHON, str(SCRIPT), *args], text=True, encoding="utf-8", capture_output=True, check=False)

    def test_cli_preserves_unicode_paths(self) -> None:
        (self.source / "Türkçe-şartname-📋.txt").write_text("ölçü", encoding="utf-8")
        result = self.invoke("inventory", "--source-dir", str(self.source))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Türkçe-şartname-📋.txt", result.stdout)

    def prepare(self) -> Path:
        p = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(self.out))
        self.assertEqual(p.returncode, 0, p.stderr)
        return self.out / "analysis-manifest.json"

    def test_inventory_reports_byte_duplicates_and_empty_manifest_blocks_final(self) -> None:
        p = self.invoke("inventory", "--source-dir", str(self.source))
        self.assertEqual(p.returncode, 0)
        inv = json.loads(p.stdout); self.assertEqual(inv["duplicate_byte_groups"][0]["paths"], ["a.txt", "b.txt"])
        manifest = self.prepare()
        verify = self.invoke("verify", "--output-dir", str(self.out))
        self.assertEqual(verify.returncode, 2)
        self.assertEqual(json.loads(verify.stdout)["status"], "BLOCKED")
        self.assertTrue(manifest.exists())

    def test_modified_source_blocks_gate(self) -> None:
        self.prepare(); (self.source / "a.txt").write_text("değişti", encoding="utf-8")
        p = self.invoke("verify", "--output-dir", str(self.out))
        m = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(p.returncode, 2); self.assertEqual(m["controls"]["source_hashes_verified"]["status"], "FAIL")

    def test_dispatch_is_dry_run_pinned_and_blocks_non_coordinator(self) -> None:
        self.prepare(); prompt = self.tmp / "prompt.txt"; prompt.write_text("yalnız plan", encoding="utf-8")
        blocked = self.invoke("dispatch", "--output-dir", str(self.out), "--caller-role", "financial", "--role", "financial", "--prompt-file", str(prompt))
        self.assertEqual(blocked.returncode, 2)
        p = self.invoke("dispatch", "--output-dir", str(self.out), "--caller-role", "coordinator", "--role", "financial", "--prompt-file", str(prompt))
        self.assertEqual(p.returncode, 0, p.stderr)
        event = json.loads(p.stdout); self.assertEqual(event["mode"], "dry-run")
        self.assertEqual(event["model"], "gpt-5.6-terra"); self.assertIn("agents.enabled=false", event["command"])

    def test_missing_controls_never_default_to_pass(self) -> None:
        self.prepare(); m = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["controls"]["independent_reviewer_verified"]["status"], "PENDING")
        self.assertEqual(m["final_gate"]["status"], "BLOCKED")

    def test_complete_attested_package_can_open_final_gate(self) -> None:
        self.prepare()
        manifest = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        source = manifest["source_inventory"]["entries"][0]
        analysis = {"task_id": "analysis-task", "report_requested": False, "competitors": ["A"], "exclusions": [], "critical_fact_ids": ["f1"],
                    "facts": [{"fact_id": "f1", "claim": "fiyat", "source_id": source["source_id"],
                               "source_sha256": source["sha256"], "location": "a.txt:1", "evidence_status": "verified",
                               "critical": True, "independent_check": {"checked_by": "review-task"}}]}
        attested = {name: {"status": "PASS", "evidence": ["independent worksheet check"], "reviewed_by": "review-task"}
                    for name in ("numeric_reconciliation", "fair_comparison", "freshness_validity", "cost_completeness",
                                 "formula_recalculation", "parameter_change_test", "output_consistency", "visual_review")}
        (self.out / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
        workbook_fixture(self.out / "comparison.xlsx")
        for name, file in (("analysis_record", "analysis.json"), ("workbook", "comparison.xlsx")):
            self.assertEqual(self.invoke("record-artifact", "--output-dir", str(self.out), "--name", name, "--artifact", str(self.out / file)).returncode, 0)
        manifest = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        review = {"reviewer": {"role": "reviewer", "model": "gpt-5.6-sol", "reasoning_effort": "high", "task_id": "review-task"},
                  "run_id": manifest["run_id"], "dataset_sha256": manifest["source_inventory"]["dataset_sha256"],
                  "analysis_sha256": manifest["artifacts"]["analysis_record"]["sha256"], "workbook_sha256": manifest["artifacts"]["workbook"]["sha256"],
                  "all_critical_evidence_reviewed": True, "all_competitors_reviewed": True,
                  "all_exclusion_reasons_reviewed": True, "checked_fact_ids": ["f1"], "control_attestations": attested}
        (self.out / "review.json").write_text(json.dumps(review), encoding="utf-8")
        self.assertEqual(self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "review_attestation", "--artifact", str(self.out / "review.json")).returncode, 0)
        # A made-up review object alone must fail; fixture receipts below simulate the runtime.
        unexecuted = self.invoke("verify", "--output-dir", str(self.out))
        self.assertEqual(unexecuted.returncode, 2)
        self.assertEqual(json.loads(unexecuted.stdout)["status"], "BLOCKED")
        manifest = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        manifest["dispatches"] = [
            {"dispatch_id": task, "role": role, "model": "gpt-5.6-sol", "reasoning_effort": "high", "mode": "run", "returncode": 0,
             "result_sha256": manifest["artifacts"][artifact]["sha256"]}
            for task, role, artifact in (("analysis-task", "coordinator", "analysis_record"), ("review-task", "reviewer", "review_attestation"))]
        (self.out / "analysis-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        verified = self.invoke("verify", "--output-dir", str(self.out))
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["status"], "FINAL_ALLOWED")

        # A changed analysis may not reuse the previous source-bound reviewer receipt.
        analysis["facts"][0]["claim"] = "fiyat değişti"
        (self.out / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
        self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "analysis_record", "--artifact", str(self.out / "analysis.json"))
        self.assertEqual(self.invoke("verify", "--output-dir", str(self.out)).returncode, 2)

    def test_dispatch_runtime_records_result_hash_and_propagates_failure(self):
        self.out.mkdir(); prompt = self.out / "task.md"; prompt.write_text("fixture")
        def fake_run(command, **kwargs):
            dest = Path(command[command.index("--output-last-message") + 1])
            dest.write_text('{"fixture":true}', encoding="utf-8")
            self.assertFalse(kwargs["shell"])
            self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-sol")
            return subprocess.CompletedProcess(command, 0)
        with patch.object(runtime, "resolve_codex_executable", return_value="codex.exe"), patch.object(runtime.subprocess, "run", side_effect=fake_run):
            event = runtime.run_dispatch("reviewer", self.out, prompt, True)
            self.assertEqual(event["result_sha256"], runtime.digest_file(self.out / event["result_file"]))
            self.assertEqual(event["returncode"], 0)
        with patch.object(runtime, "resolve_codex_executable", return_value="codex.exe"), patch.object(runtime.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(runtime.ControlError): runtime.run_dispatch("reviewer", self.out, prompt, True)

    def test_output_inside_source_rejected_without_writing(self):
        forbidden = self.source / "output"
        result = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(forbidden))
        self.assertEqual(result.returncode, 2)
        self.assertFalse(forbidden.exists())


if __name__ == "__main__": unittest.main()
