"""Stdlib regression tests for the bounded teklif runtime."""
from __future__ import annotations

import json
import re
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
        # Tests must never invoke a real model process, including after runtime refactors.
        self.model_guard = patch.object(runtime, "stream_process", side_effect=AssertionError("Live model forbidden in unit tests"))
        self.model_guard.start(); self.addCleanup(self.model_guard.stop)
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
        p = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(self.out), "--allow-unprobed-model")
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

    def test_prepare_requires_fresh_model_preflight_before_writing(self) -> None:
        target = self.tmp / "no-preflight-output"
        result = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(target))
        self.assertEqual(result.returncode, 2)
        self.assertIn("preflight --run", result.stderr)
        self.assertFalse(target.exists())

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

    def complete_package(self):
        self.prepare()
        manifest = json.loads((self.out / "analysis-manifest.json").read_text(encoding="utf-8"))
        source = manifest["source_inventory"]["entries"][0]
        analysis = {"task_id": "analysis-task", "analysis_mode": "final", "decision_status": "ready", "report_requested": False, "competitors": ["A"], "exclusions": [], "critical_fact_ids": ["f1"],
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
             "status": "COMPLETED", "session_id": task, "phase": "work" if role == "coordinator" else "compare", "at": "2026-01-01T01:00:00Z",
             "result_sha256": manifest["artifacts"][artifact]["sha256"]}
            for task, role, artifact in (("analysis-task", "coordinator", "analysis_record"), ("review-task", "reviewer", "review_attestation"))]
        (self.out / "blind.md").write_text("independent fixture notes", encoding="utf-8")
        manifest["dispatches"].append({"dispatch_id": "blind-task", "session_id": "review-task", "role": "reviewer", "phase": "blind",
                                       "mode": "run", "status": "COMPLETED", "returncode": 0, "at": "2026-01-01T00:00:00Z", "result_file": "blind.md",
                                       "result_sha256": runtime.digest_file(self.out / "blind.md")})
        (self.out / "analysis-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        verified = self.invoke("verify", "--output-dir", str(self.out))
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(json.loads(verified.stdout)["status"], "FINAL_ALLOWED")
        return analysis

    def test_complete_attested_package_can_open_final_gate(self) -> None:
        analysis = self.complete_package()
        # A changed analysis may not reuse the previous source-bound reviewer receipt.
        analysis["facts"][0]["claim"] = "fiyat değişti"
        (self.out / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
        self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "analysis_record", "--artifact", str(self.out / "analysis.json"))
        self.assertEqual(self.invoke("verify", "--output-dir", str(self.out)).returncode, 2)

    def test_dispatch_runtime_records_result_hash_and_propagates_failure(self):
        self.out.mkdir(); prompt = self.out / "task.md"; prompt.write_text("fixture")
        def fake_run(command, prompt_text, cwd, events, stderr, timeout):
            dest = Path(command[command.index("--output-last-message") + 1])
            artifact = Path(cwd) / "fixture.json"
            artifact.write_text('{"fixture":true}', encoding="utf-8")
            dest.write_text(json.dumps({"artifact_path": str(artifact), "artifact_sha256": runtime.digest_file(artifact)}), encoding="utf-8")
            self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-sol")
            self.assertIn("--json", command)
            return {"returncode": 0, "status": "COMPLETED", "session_id": "fake-session", "usage": {"input_tokens": 12}}
        with patch.object(runtime, "resolve_codex_executable", return_value="codex.exe"), patch.object(runtime, "stream_process", side_effect=fake_run):
            event = runtime.run_dispatch("reviewer", self.out, prompt, True)
            self.assertEqual(event["status"], "COMPLETED", event)
            self.assertEqual(event["result_sha256"], runtime.digest_file(self.out / event["result_file"]))
            self.assertEqual(event["returncode"], 0)
        with patch.object(runtime, "resolve_codex_executable", return_value="codex.exe"), patch.object(runtime, "stream_process", return_value={"returncode": 1, "status": "FAILED"}):
            self.assertEqual(runtime.run_dispatch("reviewer", self.out, prompt, True)["status"], "FAILED")

    def test_dispatch_auto_records_result_and_resume_keeps_stable_task_id(self):
        self.prepare(); prompt = self.out / "task.md"; prompt.write_text("fixture", encoding="utf-8")
        def fake_run(command, prompt_text, cwd, events, stderr, timeout):
            task_id = re.search(r"stable task_id ([0-9a-f-]+)", prompt_text).group(1)
            artifact = Path(cwd) / "analysis-auto.json"
            artifact.write_text(json.dumps({"task_id": task_id, "facts": []}), encoding="utf-8")
            pointer = Path(command[command.index("--output-last-message") + 1])
            pointer.write_text(json.dumps({"artifact_path": str(artifact), "artifact_sha256": runtime.digest_file(artifact)}), encoding="utf-8")
            return {"returncode": 0, "status": "COMPLETED", "session_id": "stable-session",
                    "usage": {"input_tokens": 10, "output_tokens": 2}}
        args = ["dispatch", "--output-dir", str(self.out), "--caller-role", "controller", "--role", "coordinator", "--prompt-file", str(prompt), "--run"]
        with patch.object(runtime, "resolve_codex_executable", return_value="codex.exe"), patch.object(runtime, "stream_process", side_effect=fake_run):
            self.assertEqual(runtime.cmd_dispatch(runtime.parser().parse_args(args)), 0)
            first = runtime.read_json(self.out / "analysis-manifest.json")
            task_id = first["dispatches"][-1]["task_id"]
            self.assertEqual(first["artifacts"]["analysis_record"]["sha256"], first["dispatches"][-1]["result_sha256"])
            resumed = args + ["--resume-task", task_id, "--phase", "revision"]
            self.assertEqual(runtime.cmd_dispatch(runtime.parser().parse_args(resumed)), 0)
        final = runtime.read_json(self.out / "analysis-manifest.json")
        self.assertEqual({d["task_id"] for d in final["dispatches"]}, {task_id})
        self.assertEqual(len({d["dispatch_id"] for d in final["dispatches"]}), 2)

    def test_pre_review_qa_is_local_and_hash_bound(self):
        self.prepare(); manifest = runtime.read_json(self.out / "analysis-manifest.json")
        source = manifest["source_inventory"]["entries"][0]
        analysis = {"task_id": "a", "facts": [{"fact_id": "f1", "claim": "x", "evidence_status": "verified",
                    "source_id": source["source_id"], "source_sha256": source["sha256"], "location": "a.txt:1"}]}
        (self.out / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
        workbook_fixture(self.out / "qa.xlsx")
        with zipfile.ZipFile(self.out / "qa.xlsx", "a") as archive:
            archive.writestr("docProps/qa.xml", "<qa>SHA-256 " + "a" * 64 + "</qa>")
        for name, filename in (("analysis_record", "analysis.json"), ("workbook", "qa.xlsx")):
            self.assertEqual(self.invoke("record-artifact", "--output-dir", str(self.out), "--name", name, "--artifact", str(self.out / filename)).returncode, 0)
        result = self.invoke("pre-review-qa", "--output-dir", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        quality = runtime.read_json(self.out / "analysis-manifest.json")["quality_precheck"]
        self.assertEqual(quality["status"], "PASS")
        self.assertEqual(quality["report_sha256"], runtime.digest_file(self.out / "deterministic-qa.json"))

    def test_budget_exhaustion_blocks_new_model_dispatch(self):
        self.prepare(); manifest = runtime.read_json(self.out / "analysis-manifest.json")
        manifest["dispatches"] = [{"mode": "run", "phase": "work", "usage": {"input_tokens": 80000000, "output_tokens": 1}}]
        with self.assertRaises(runtime.ControlError):
            runtime.assert_budget_available(manifest, "work")

    def test_output_inside_source_rejected_without_writing(self):
        forbidden = self.source
        result = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(forbidden))
        self.assertEqual(result.returncode, 2)
        self.assertFalse((forbidden / "analysis-manifest.json").exists())

    def test_unknown_critical_is_preserved_and_preliminary_can_close(self):
        analysis = self.complete_package()
        analysis.update(analysis_mode="preliminary", decision_status="awaiting_supplier_input", recommendation=None)
        analysis["facts"][0].update(evidence_status="unverified", open_issue="Missing supplier price")
        (self.out / "analysis.json").write_text(json.dumps(analysis), encoding="utf-8")
        self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "analysis_record", "--artifact", str(self.out / "analysis.json"))
        m = runtime.read_json(self.out / "analysis-manifest.json")
        review = runtime.read_json(self.out / "review.json")
        review["analysis_sha256"] = m["artifacts"]["analysis_record"]["sha256"]
        review["control_attestations"]["cost_completeness"].update(status="UNVERIFIED", reason="Missing price")
        (self.out / "review.json").write_text(json.dumps(review), encoding="utf-8")
        self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "review_attestation", "--artifact", str(self.out / "review.json"))
        m = runtime.read_json(self.out / "analysis-manifest.json")
        for event in m["dispatches"]:
            artifact = {"analysis-task": "analysis_record", "review-task": "review_attestation"}.get(event["dispatch_id"])
            if artifact: event["result_sha256"] = m["artifacts"][artifact]["sha256"]
        runtime.atomic_json(self.out / "analysis-manifest.json", m)
        check = self.invoke("verify", "--output-dir", str(self.out))
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        m = runtime.read_json(self.out / "analysis-manifest.json")
        self.assertEqual(m["controls"]["cost_completeness"]["status"], "UNVERIFIED")
        self.assertEqual(m["controls"]["critical_facts_independently_checked"]["status"], "PASS")
        self.assertEqual(m["controls"]["critical_facts_resolved"]["status"], "UNVERIFIED")
        self.assertEqual(m["final_gate"]["status"], "BLOCKED")
        self.assertEqual(self.invoke("close", "--output-dir", str(self.out), "--preliminary").returncode, 0)
        self.assertEqual(runtime.read_json(self.out / "analysis-manifest.json")["lifecycle"]["status"], "PRELIMINARY_COMPLETE")

    def test_preliminary_all_pass_never_opens_final_gate(self):
        self.complete_package()
        path = self.out / "analysis-manifest.json"
        m = runtime.read_json(path)
        m.update(analysis_mode="preliminary", decision_status="awaiting_supplier_input", has_recommendation=False)
        runtime.save_manifest(path, m)
        self.assertEqual(m["delivery_gate"]["status"], "PRELIMINARY_ALLOWED")
        self.assertEqual(m["final_gate"]["status"], "BLOCKED")
        m["dispatches"].append({"status": "RUNNING"})
        runtime.save_manifest(path, m)
        self.assertEqual(m["delivery_gate"]["status"], "BLOCKED")
        self.assertEqual(self.invoke("close", "--output-dir", str(self.out), "--abort").returncode, 2)
        self.assertTrue((self.out / ".teklif-analysis.lock").exists())
        m["dispatches"].pop(); runtime.atomic_json(path, m)

    def test_dry_run_plans_do_not_count_as_self_review(self):
        self.complete_package()
        path = self.out / "analysis-manifest.json"
        m = runtime.read_json(path)
        m["dispatches"] += [{"dispatch_id": role + "-plan", "role": role, "mode": "dry-run", "session_id": None}
                            for role in ("coordinator", "reviewer")]
        runtime.atomic_json(path, m)
        self.assertEqual(self.invoke("verify", "--output-dir", str(self.out)).returncode, 0)

    def test_native_coordinator_requires_real_seal_and_records_without_cli(self):
        self.prepare()
        artifact = self.out / "native.json"
        artifact.write_text(json.dumps({"task_id": "native-session"}), encoding="utf-8")
        args = ["--output-dir", str(self.out), "--role", "coordinator", "--phase", "work", "--artifact", str(artifact)]
        seal = self.invoke("seal-result", *args).stdout.strip()
        log = self.tmp / "native.jsonl"
        events = [{"type": "session_meta", "payload": {"id": "native-session", "cwd": str(self.source)}},
                  {"type": "turn_context", "payload": {"model": "gpt-5.6-sol", "effort": "high"}}]
        def write(): log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        write()
        missing = self.invoke("register-session", *args, "--session-log", str(log))
        self.assertEqual(missing.returncode, 2)
        events.append({"type": "response_item", "timestamp": "2026-09-21T00:00:00Z", "payload": {"type": "function_call_output", "output": seal}})
        write()
        registered = self.invoke("register-session", *args, "--session-log", str(log))
        self.assertEqual(registered.returncode, 0, registered.stderr)
        self.assertEqual(json.loads(registered.stdout)["status"], "RESULT_RECORDED")
        self.assertTrue(runtime.receipt_valid(json.loads(registered.stdout)))

    def test_native_seal_cannot_accept_a_different_result_hash(self):
        event = {"mode": "native", "role": "coordinator", "phase": "work", "result_sha256": "new",
                 "seal_at": "2026-09-21T00:00:00Z", "seal": {"role": "coordinator", "phase": "work", "artifact_sha256": "old"}}
        with patch.object(runtime, "native_receipt_valid", return_value=True):
            self.assertFalse(runtime.receipt_valid(event))

    def test_native_blind_order_uses_actual_seals_not_registration_time(self):
        blind = {"mode": "native", "at": "1", "seal_at": "2026-09-21T00:00:02Z", "seal_line": 10}
        compare = {"mode": "native", "at": "2", "seal_at": "2026-09-21T00:00:01Z", "seal_line": 8}
        self.assertFalse(runtime.blind_precedes(blind, compare))
        compare.update(seal_at=blind["seal_at"], seal_line=11)
        self.assertTrue(runtime.blind_precedes(blind, compare))

    def test_terminal_checkpoint_recovers_running_without_model_call(self):
        self.prepare(); path = self.out / "analysis-manifest.json"
        m = runtime.read_json(path)
        m["dispatches"].append({"dispatch_id": "fixture-job", "mode": "run", "status": "RUNNING"})
        runtime.atomic_json(path, m)
        self.assertEqual(self.invoke("recover-dispatch", "--output-dir", str(self.out), "--dispatch-id", "fixture-job").returncode, 2)
        runtime.atomic_json(self.out / "dispatches" / "fixture-job" / "receipt.json",
                            {"run_id": m["run_id"], "event": {"dispatch_id": "fixture-job", "mode": "run", "status": "FAILED", "returncode": 1}})
        result = self.invoke("recover-dispatch", "--output-dir", str(self.out), "--dispatch-id", "fixture-job")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(runtime.read_json(path)["dispatches"][0]["status"], "FAILED")
        self.assertEqual(self.invoke("close", "--output-dir", str(self.out), "--abort").returncode, 0)

    def test_recovery_auto_records_completed_coordinator_artifact(self):
        self.prepare(); path = self.out / "analysis-manifest.json"
        m = runtime.read_json(path); task_id = "stable-recovery-task"; dispatch_id = "attempt-1"
        artifact = self.out / "recovered-analysis.json"
        artifact.write_text(json.dumps({"task_id": task_id, "facts": []}), encoding="utf-8")
        event = {"dispatch_id": dispatch_id, "task_id": task_id, "mode": "run", "role": "coordinator",
                 "phase": "work", "status": "COMPLETED", "returncode": 0, "session_id": "session-1",
                 "result_file": artifact.name, "result_sha256": runtime.digest_file(artifact)}
        m["dispatches"].append({**event, "status": "RUNNING", "returncode": None, "result_sha256": None})
        runtime.atomic_json(path, m)
        runtime.atomic_json(self.out / "dispatches" / dispatch_id / "receipt.json", {"run_id": m["run_id"], "event": event})
        result = self.invoke("recover-dispatch", "--output-dir", str(self.out), "--dispatch-id", dispatch_id)
        self.assertEqual(result.returncode, 0, result.stderr)
        recovered = runtime.read_json(path)
        self.assertEqual(recovered["artifacts"]["analysis_record"]["sha256"], event["result_sha256"])

    def test_operation_lock_waits_bounded_and_never_deletes_foreign_lock(self):
        self.prepare(); runtime.manifest_path(self.out)
        m = runtime.read_json(self.out / "analysis-manifest.json")
        runtime.OPERATION_LOCK.write_text('{"fixture":true}')
        with self.assertRaises(runtime.ControlError): runtime.acquire_operation(m["run_id"], "test", wait_seconds=0)
        self.assertTrue(runtime.OPERATION_LOCK.exists())
        runtime.OPERATION_LOCK.unlink()

    def test_verify_rereads_manifest_after_operation_lock(self):
        self.prepare()
        path = self.out / "analysis-manifest.json"
        original = runtime.acquire_operation
        def concurrent_update(run_id, operation):
            # Simulate a second writer finishing between our precheck and lock acquisition.
            m = runtime.read_json(path); m["concurrent_update"] = "must survive"
            runtime.atomic_json(path, m)
            return original(run_id, operation)
        with patch.object(runtime, "acquire_operation", side_effect=concurrent_update):
            runtime.cmd_verify(runtime.parser().parse_args(["verify", "--output-dir", str(self.out)]))
        self.assertEqual(runtime.read_json(path)["concurrent_update"], "must survive")

    def test_sources_exclude_prior_outputs_and_concurrent_runs_have_local_locks(self):
        (self.source / "analiz").mkdir()
        (self.source / "analiz" / "old.xlsx").write_bytes(b"old output")
        self.prepare()
        other = self.source / "analiz" / "new-run"
        p = self.invoke("prepare", "--source-dir", str(self.source), "--output-dir", str(other), "--allow-unprobed-model")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(runtime.read_json(other / "analysis-manifest.json")["source_inventory"]["entries"]), 2)
        self.assertTrue((self.out / ".teklif-analysis.lock").exists())
        self.assertTrue((other / ".teklif-analysis.lock").exists())
        self.invoke("close", "--output-dir", str(other), "--abort")

    def test_unchanged_artifact_keeps_controls_and_blind_tamper_blocks(self):
        self.complete_package()
        before = runtime.read_json(self.out / "analysis-manifest.json")
        self.invoke("record-artifact", "--output-dir", str(self.out), "--name", "workbook", "--artifact", str(self.out / "comparison.xlsx"))
        self.assertEqual(runtime.read_json(self.out / "analysis-manifest.json"), before)
        (self.out / "blind.md").write_text("changed")
        self.assertEqual(self.invoke("verify", "--output-dir", str(self.out)).returncode, 2)


if __name__ == "__main__": unittest.main()
