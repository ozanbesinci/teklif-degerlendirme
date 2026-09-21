#!/usr/bin/env python3
"""Deterministic runtime and final-control gate for teklif-degerlendirme.

This controller never interprets a source document.  It freezes byte-level inputs,
dispatches only policy-pinned Codex roles, and blocks FINAL when attestations or
required evidence are absent.  Caller identity is an assertion, not authentication.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from cikti_denetimi import validate_xlsx, validate_pdf
from oturum_kaydi import read_native_session, native_receipt_valid, stream_process

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SKILLS_ROOT = SKILL_ROOT.parent
POLICY_PATH = SKILL_ROOT / "config" / "ajan-politikasi.json"
ANALYSIS_LOCK = SKILLS_ROOT / ".teklif-analysis.lock"
UPDATE_LOCK = SKILLS_ROOT / ".teklif-update.lock"
OPERATION_LOCK = SKILLS_ROOT / ".teklif-analysis.operation.lock"
SCHEMA = "teklif-analysis-control/v2"
MANDATORY_CONTROLS = (
    "source_inventory_frozen", "skill_snapshot_frozen", "dataset_hash_verified",
    "source_hashes_verified", "skill_hashes_verified", "artifact_hashes_verified",
    "evidence_schema_verified", "critical_facts_independently_checked",
    "critical_facts_resolved",
    "independent_reviewer_verified", "competitor_and_exclusion_reviewed",
    "numeric_reconciliation", "fair_comparison", "freshness_validity",
    "cost_completeness", "formula_recalculation", "parameter_change_test",
    "output_consistency", "visual_review",
)
REQUIRED_ARTIFACTS = ("analysis_record", "review_attestation", "workbook")
ALLOWED_MODELS = {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-6-astra"}
EXCLUDED_DIRS = {"analiz", ".git", ".codex", ".agents", "__pycache__", "skill-snapshot", "reviews", "dispatches"}
SOURCE_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".eml", ".msg", ".zip", ".txt"}


def use_run_locks(output: Path) -> None:
    """A run owns only its own directory, never the shared installed skill tree."""
    global ANALYSIS_LOCK, OPERATION_LOCK
    ANALYSIS_LOCK = output.resolve() / ".teklif-analysis.lock"
    OPERATION_LOCK = output.resolve() / ".teklif-analysis.operation.lock"


class ControlError(RuntimeError):
    pass


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.write("\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ControlError(f"JSON okunamadı: {path}: {e}") from e
    if not isinstance(loaded, dict):
        raise ControlError(f"JSON nesnesi bekleniyordu: {path}")
    return loaded


def load_policy() -> dict[str, Any]:
    policy = read_json(POLICY_PATH)
    roles = policy.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise ControlError("Politikada roller yok.")
    for name, role in roles.items():
        if role.get("model") not in ALLOWED_MODELS or not role.get("reasoning_effort"):
            raise ControlError(f"Politikada izin verilmeyen model veya geçersiz rol: {name}")
    return policy


def acquire_analysis_lock(run_id: str, operation: str) -> None:
    body = {"run_id": run_id, "pid": os.getpid(), "operation": operation, "created_at": utc_now()}
    try:
        fd = os.open(ANALYSIS_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as e:
        raise ControlError(f"Etkin analiz kilidi var: {ANALYSIS_LOCK}; eski kilit otomatik silinmez.") from e
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False); f.flush(); os.fsync(f.fileno())
    if UPDATE_LOCK.exists():
        # A simultaneous updater must see our durable marker and refuse too.
        ANALYSIS_LOCK.unlink()
        raise ControlError(f"Güncelleme kilidi ile yarış oluştu; analiz başlatılamaz: {UPDATE_LOCK}")


def acquire_operation(run_id: str, operation: str, wait_seconds=30) -> None:
    if not ANALYSIS_LOCK.exists(): raise ControlError("Aktif analiz yaşam döngüsü kilidi yok.")
    lock = read_json(ANALYSIS_LOCK)
    if lock.get("run_id") != run_id: raise ControlError("Bu manifest başka aktif koşuya ait değil.")
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            fd = os.open(OPERATION_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError as e:
            if time.monotonic() >= deadline:
                raise ControlError("Başka bir analiz işlemi sürüyor; kilit otomatik silinmez.") from e
            time.sleep(0.1)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "operation": operation, "pid": os.getpid(), "created_at": utc_now()}, f); f.flush(); os.fsync(f.fileno())


def release_operation(run_id: str) -> None:
    if not OPERATION_LOCK.exists(): return
    if read_json(OPERATION_LOCK).get("run_id") != run_id: raise ControlError("Başka koşunun işlem kilidi kaldırılamaz.")
    OPERATION_LOCK.unlink()


def release_analysis_lock(run_id: str) -> None:
    if not ANALYSIS_LOCK.exists():
        return
    try:
        body = read_json(ANALYSIS_LOCK)
    except ControlError:
        raise ControlError("Analiz kilidi bozuk; otomatik silinmez.")
    if body.get("run_id") != run_id:
        raise ControlError("Başka koşunun analiz kilidi serbest bırakılamaz.")
    ANALYSIS_LOCK.unlink()


def inventory(root: Path, selected: list[str] | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ControlError(f"Kaynak klasörü yok: {root}")
    entries: list[dict[str, Any]] = []
    if selected is None:
        candidates = []
        for base, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if d.casefold() not in EXCLUDED_DIRS and not d.startswith(".")
                       and not Path(base, d).is_symlink() and not (hasattr(Path(base, d), "is_junction") and Path(base, d).is_junction())]
            candidates.extend(Path(base, n) for n in names if not n.startswith((".", "~$")) and Path(n).suffix.lower() in SOURCE_EXTENSIONS)
    else:
        if not isinstance(selected, list) or not selected or not all(isinstance(x, str) for x in selected) or len(set(selected)) != len(selected):
            raise ControlError("Kaynak listesi boş olmayan benzersiz göreli yol dizisi olmalı.")
        candidates = [root / name for name in selected]
    for path in sorted(candidates):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.resolve().is_relative_to(root) or not path.is_file() or ".." in Path(relative).parts:
            raise ControlError(f"Kaynak yok/bağlantı veya kök dışı: {relative}")
        relative = path.relative_to(root).as_posix()
        sha = digest_file(path)
        entries.append({"source_id": stable_hash({"path": relative, "sha256": sha})[:24],
                        "relative_path": relative, "sha256": sha, "size_bytes": path.stat().st_size})
    groups: dict[str, list[str]] = {}
    for entry in entries:
        groups.setdefault(entry["sha256"], []).append(entry["relative_path"])
    duplicates = [{"sha256": sha, "paths": paths} for sha, paths in sorted(groups.items()) if len(paths) > 1]
    canonical = [{k: e[k] for k in ("relative_path", "sha256", "size_bytes")} for e in entries]
    return {"root": str(root), "entries": entries, "duplicate_byte_groups": duplicates,
            "dataset_sha256": stable_hash(canonical)}


def skill_snapshot(root: Path = SKILL_ROOT) -> dict[str, Any]:
    paths = [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    files = [{"relative_path": p.relative_to(root).as_posix(), "sha256": digest_file(p)} for p in sorted(paths)]
    version_path = root / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else None
    return {"root": str(root), "version": version, "files": files, "combined_sha256": stable_hash(files)}


def manifest_path(output_dir: Path) -> Path:
    use_run_locks(output_dir)
    return output_dir.resolve() / "analysis-manifest.json"


def default_controls() -> dict[str, Any]:
    return {cid: {"status": "PENDING", "evidence": [], "reason": None} for cid in MANDATORY_CONTROLS}


def gate(manifest: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if manifest.get("analysis_mode") != "final" or manifest.get("decision_status") != "ready":
        reasons.append("Kayıt kesin karar/nihai sonuç modunda değil.")
    if any(d.get("status") == "RUNNING" for d in manifest.get("dispatches", [])):
        reasons.append("Çalışan görev tamamlanmadan teslim/kapanış yapılamaz.")
    if not manifest.get("source_inventory", {}).get("entries"):
        reasons.append("Kaynak envanteri boş.")
    for cid in MANDATORY_CONTROLS:
        item = manifest.get("controls", {}).get(cid, {})
        status = item.get("status")
        if status != "PASS":
            reasons.append(f"Kontrol geçmedi: {cid} ({status or 'yok'}).")
    for artifact in REQUIRED_ARTIFACTS:
        if artifact not in manifest.get("artifacts", {}):
            reasons.append(f"Zorunlu artefakt yok: {artifact}.")
    if manifest.get("report_requested") is True and "report_pdf" not in manifest.get("artifacts", {}):
        reasons.append("Rapor istendiği halde PDF artefaktı yok.")
    return ("FINAL_ALLOWED" if not reasons else "BLOCKED", reasons)


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    state, reasons = gate(manifest)
    manifest["final_gate"] = {"status": state, "reasons": reasons, "checked_at": utc_now()}
    preliminary = (manifest.get("analysis_mode") == "preliminary"
                   and manifest.get("decision_status") == "awaiting_supplier_input"
                   and manifest.get("has_recommendation") is False)
    for cid in MANDATORY_CONTROLS:
        status = manifest["controls"][cid]["status"]
        if status != "PASS" and not (cid in {"critical_facts_resolved", "cost_completeness"}
                                    and status == "UNVERIFIED" and manifest["controls"][cid].get("reason")):
            preliminary = False
    preliminary = preliminary and all(a in manifest.get("artifacts", {}) for a in REQUIRED_ARTIFACTS)
    preliminary = preliminary and (not manifest.get("report_requested") or "report_pdf" in manifest["artifacts"])
    preliminary = preliminary and not any(d.get("status") == "RUNNING" for d in manifest.get("dispatches", []))
    delivery = state if state == "FINAL_ALLOWED" else ("PRELIMINARY_ALLOWED" if preliminary else "BLOCKED")
    manifest["delivery_gate"] = {"status": delivery, "checked_at": utc_now()}
    manifest["budget"] = budget_state(manifest)
    manifest["updated_at"] = utc_now()
    atomic_json(path, manifest)


def budget_state(manifest: dict[str, Any]) -> dict[str, Any]:
    limits = load_policy().get("budgets", {})
    dispatches = [d for d in manifest.get("dispatches", []) if d.get("mode") == "run"]
    usage = {"input_tokens": 0, "output_tokens": 0}
    for event in dispatches:
        current = event.get("usage") or {}
        for key in usage:
            value = current.get(key, 0)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                usage[key] += value
    try:
        started = calendar.timegm(time.strptime(manifest.get("lifecycle", {}).get("started_at", ""), "%Y-%m-%dT%H:%M:%SZ"))
        wall = max(0, int(time.time() - started))
    except (TypeError, ValueError):
        wall = 0
    used = {**usage, "dispatches": len(dispatches),
            "revision_dispatches": sum(d.get("phase") == "revision" for d in dispatches),
            "wall_seconds": wall}
    reasons = []
    mapping = (("max_dispatches", "dispatches"), ("max_revision_dispatches", "revision_dispatches"),
               ("max_input_tokens", "input_tokens"), ("max_output_tokens", "output_tokens"),
               ("max_wall_seconds", "wall_seconds"))
    for limit_key, used_key in mapping:
        limit = limits.get(limit_key)
        if isinstance(limit, int) and used[used_key] >= limit:
            reasons.append(f"Bütçe sınırı doldu: {used_key}={used[used_key]} / {limit}.")
    return {"limits": limits, "used": used, "status": "EXHAUSTED" if reasons else "AVAILABLE", "reasons": reasons}


def assert_budget_available(manifest: dict[str, Any], phase: str) -> float:
    state = budget_state(manifest)
    reasons = list(state["reasons"])
    if phase == "revision" and state["used"]["revision_dispatches"] >= state["limits"].get("max_revision_dispatches", 4):
        reasons.append("Revizyon turu sınırı doldu; yeni kanıt veya kullanıcı kararı gerekli.")
    if reasons:
        raise ControlError(" ".join(dict.fromkeys(reasons)))
    remaining = state["limits"].get("max_wall_seconds", 5400) - state["used"]["wall_seconds"]
    return max(1.0, float(min(state["limits"].get("max_dispatch_seconds", 1200), remaining)))


def validate_preflight_receipt(receipt_path: Path, source_inventory: dict[str, Any], output: Path,
                               snapshot: dict[str, Any]) -> dict[str, Any]:
    receipt = read_json(receipt_path)
    expected = {"status": "MODEL_READY", "source_root": source_inventory["root"],
                "dataset_sha256": source_inventory["dataset_sha256"], "output_dir": str(output),
                "skill_sha256": snapshot["combined_sha256"], "policy_sha256": digest_file(POLICY_PATH)}
    if any(receipt.get(k) != v for k, v in expected.items()):
        raise ControlError("Model/ağ ön kontrol makbuzu kaynak, hedef, skill veya politikaya bağlı değil.")
    created = receipt.get("created_unix")
    if not isinstance(created, (int, float)) or time.time() - created > 1800 or created > time.time() + 60:
        raise ControlError("Model/ağ ön kontrol makbuzu 30 dakikalık tazelik sınırını geçti.")
    return receipt


def cmd_preflight(args: argparse.Namespace) -> int:
    source = Path(args.source_dir).resolve(); output = Path(args.output_dir).resolve()
    if output == source or output.is_relative_to(SKILL_ROOT):
        raise ControlError("Çalışma dizini kaynak kökü veya skill ağacı olamaz.")
    if (output / "analysis-manifest.json").exists():
        raise ControlError("Ön kontrol yeni koşu hedefi içindir; hedefte manifest var.")
    selected = None
    if getattr(args, "source_list", None):
        selected = json.loads(Path(args.source_list).read_text(encoding="utf-8"))
    frozen_sources = inventory(source, selected)
    if not frozen_sources["entries"]:
        raise ControlError("Analiz için kaynak belge bulunamadı.")
    snapshot = skill_snapshot(); policy = load_policy(); executable = resolve_codex_executable()
    status = "LOCAL_READY"; probe = None
    if args.run:
        role = policy["roles"]["coordinator"]
        with tempfile.TemporaryDirectory(prefix="teklif-model-preflight-") as folder:
            temp = Path(folder); last = temp / "last.txt"
            command = [executable, "exec", "--sandbox", "read-only", "--cd", str(temp),
                       "--model", role["model"], "-c", f"model_reasoning_effort='{role['reasoning_effort']}'",
                       "-c", "agents.enabled=false", "--json", "--output-last-message", str(last),
                       "--skip-git-repo-check", "-"]
            probe = stream_process(command, "Return only READY. Do not inspect or read any files.", temp,
                                   temp / "events.jsonl", temp / "stderr.log", 180)
        if probe.get("status") != "COMPLETED" or probe.get("returncode") != 0 or not probe.get("session_id"):
            raise ControlError("Dış model/ağ ön kontrolü geçmedi; koşu dizini oluşturulmadı.")
        status = "MODEL_READY"
    receipt = {"schema": "teklif-preflight/v1", "status": status, "created_at": utc_now(),
               "created_unix": time.time(), "source_root": frozen_sources["root"],
               "dataset_sha256": frozen_sources["dataset_sha256"], "output_dir": str(output),
               "skill_sha256": snapshot["combined_sha256"], "policy_sha256": digest_file(POLICY_PATH),
               "model": policy["roles"]["coordinator"]["model"], "probe": probe}
    if args.receipt:
        receipt_path = Path(args.receipt).resolve()
    else:
        fd, generated = tempfile.mkstemp(prefix="teklif-preflight-", suffix=".json")
        os.close(fd); receipt_path = Path(generated)
    atomic_json(receipt_path, receipt)
    print(receipt_path)
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    source = Path(args.source_dir).resolve(); output = Path(args.output_dir).resolve()
    if output == source or output.is_relative_to(SKILL_ROOT):
        raise ControlError("Çalışma dizini kaynak kökü veya skill ağacı olamaz.")
    selected = None
    if getattr(args, "source_list", None):
        selected = json.loads(Path(args.source_list).read_text(encoding="utf-8"))
    frozen_sources = inventory(source, selected)
    if not frozen_sources["entries"]:
        raise ControlError("Analiz için kaynak belge bulunamadı.")
    if any((source / item["relative_path"]).resolve().is_relative_to(output) for item in frozen_sources["entries"]):
        raise ControlError("Seçilen kaynak çalışma dizini içinde olamaz.")
    if UPDATE_LOCK.exists():
        raise ControlError("Güncelleme sürüyor; snapshot henüz alınamaz.")
    before = skill_snapshot()
    preflight = None
    if getattr(args, "preflight_receipt", None):
        preflight = validate_preflight_receipt(Path(args.preflight_receipt), frozen_sources, output, before)
    elif not getattr(args, "allow_unprobed_model", False):
        raise ControlError("Önce `preflight --run` çalıştırın ve --preflight-receipt verin; hedef henüz değiştirilmedi.")
    output.mkdir(parents=True, exist_ok=True)
    path = manifest_path(output)
    if path.exists():
        raise ControlError(f"Mevcut manifest üzerine yazılmaz: {path}")
    run_id = str(uuid.uuid4()); acquire_analysis_lock(run_id, "prepare")
    try:
        policy = load_policy()
        snapshot_root = output / "skill-snapshot"
        snapshot_root.mkdir(exist_ok=False)
        for item in before["files"]:
            target = snapshot_root / item["relative_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SKILL_ROOT / item["relative_path"], target)
        snapshot = skill_snapshot(snapshot_root)
        if UPDATE_LOCK.exists() or before["combined_sha256"] != snapshot["combined_sha256"] or before["combined_sha256"] != skill_snapshot()["combined_sha256"]:
            raise ControlError("Snapshot sırasında skill değişti; yeni koşu diziniyle tekrar hazırlayın.")
        manifest = {"schema": SCHEMA, "run_id": run_id, "revision": 1, "created_at": utc_now(),
                    "policy": {"path": str(POLICY_PATH), "sha256": digest_file(POLICY_PATH), "version": policy.get("policy_version")},
                    "source_inventory": frozen_sources, "skill_snapshot": snapshot,
                    "preflight": preflight or {"status": "EXPLICITLY_SKIPPED"},
                    "runner": str(snapshot_root / "scripts" / "ajan_yonetimi.py"),
                    "lifecycle": {"status": "RUNNING", "started_at": utc_now()},
                    "artifacts": {}, "controls": default_controls(), "dispatches": [],
                    "limitations": ["Artefakt varlığı/karma değeri görsel doğruluk kanıtı değildir.",
                                    "Çağıran kimliği kriptografik olarak doğrulanmaz."]}
        for cid in ("source_inventory_frozen", "skill_snapshot_frozen", "dataset_hash_verified"):
            manifest["controls"][cid] = {"status": "PASS", "evidence": ["prepare"], "reason": None}
        save_manifest(path, manifest)
    except Exception:
        release_analysis_lock(run_id); raise
    print(path)
    return 0


def assert_manifest(path: Path) -> dict[str, Any]:
    m = read_json(path)
    if m.get("schema") != SCHEMA:
        raise ControlError("Desteklenmeyen manifest şeması.")
    return m


def record_artifact(manifest: dict[str, Any], output: Path, name: str, artifact_path: Path) -> None:
    path = artifact_path.resolve()
    if not path.is_file():
        raise ControlError(f"Artefakt dosyası yok: {path}")
    try:
        relative = path.relative_to(output.resolve()).as_posix()
    except ValueError as e:
        raise ControlError("Artefakt izole çıktı dizininde olmalı.") from e
    old = manifest["artifacts"].get(name)
    current_sha = digest_file(path)
    if old and old["sha256"] == current_sha:
        return False
    semantics = None
    if name == "analysis_record":
        content = read_json(path)
        semantics = {f["fact_id"]: stable_hash(f) for f in content.get("facts", []) if isinstance(f, dict) and "fact_id" in f}
    if old:
        manifest.setdefault("artifact_history", []).append({"name": name, **old})
    manifest["artifacts"][name] = {"relative_path": relative, "sha256": current_sha,
                                     "fact_hashes": semantics,
                                     "size_bytes": path.stat().st_size, "recorded_at": utc_now()}
    if name == "analysis_record":
        previous = (old or {}).get("fact_hashes") or {}
        manifest.setdefault("revalidation", {})["changed_fact_ids"] = sorted(k for k in set(previous) | set(semantics) if previous.get(k) != semantics.get(k))
        manifest["revalidation"]["source_review"] = not old or bool(manifest["revalidation"]["changed_fact_ids"])
    if name in {"workbook", "report_pdf"}:
        manifest.setdefault("revalidation", {}).update({"visual_review": True, "mechanical_checks": True})
    if name in {"analysis_record", "workbook"}:
        manifest.pop("quality_precheck", None)
    return True


def cmd_record_artifact(args: argparse.Namespace) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    acquire_operation(m["run_id"], "record-artifact")
    try:
        m = assert_manifest(path)
        changed = record_artifact(m, path.parent, args.name, Path(args.artifact))
        if changed:
            m["revision"] += 1
            invalidate_checks(m); save_manifest(path, m)
    finally: release_operation(m["run_id"])
    return 0


def invalidate_checks(manifest):
    frozen = {key: manifest["controls"][key] for key in ("source_inventory_frozen", "skill_snapshot_frozen", "dataset_hash_verified")}
    manifest["controls"] = default_controls()
    manifest["controls"].update(frozen)


def run_dispatch(role: str, output: Path, prompt_file: Path, run: bool, *, task_id=None,
                 session_id=None, phase="work", timeout_seconds=None, on_start=None, working_dir=None) -> dict[str, Any]:
    output = output.resolve()
    policy = load_policy(); role_data = policy["roles"].get(role)
    if not role_data: raise ControlError(f"Bilinmeyen rol: {role}")
    if role_data.get("conditional") and not run: pass  # recorded honestly in plan
    dispatch_id = str(uuid.uuid4())
    task_id = task_id or str(uuid.uuid4())
    folder = output / "dispatches" / dispatch_id
    result = folder / "last-message.json"
    # Reviewers can write notes only in their own sandbox, not the analysis tree.
    cwd = Path(working_dir).resolve() if working_dir else (output if role == "coordinator" else output / "reviews" / dispatch_id)
    if not cwd.is_relative_to(output):
        raise ControlError("Görev çalışma alanı koşu dizininden çıkamaz.")
    sandbox = "workspace-write"
    agent_settings = ["-c", "agents.enabled=false"] if role != "coordinator" else ["-c", "agents.enabled=true", "-c", "agents.max_concurrent_threads_per_session=3", "-c", "agents.default_subagent_model='gpt-5.6-terra'"]
    command = ["codex", "exec", "--sandbox", sandbox, "--cd", str(cwd)]
    if session_id:
        command += ["resume"]
    command += ["--model", role_data["model"], "-c", f"model_reasoning_effort='{role_data['reasoning_effort']}'", *agent_settings,
                "--json", "--output-schema", str(SKILL_ROOT / "config" / "result-schema.json"),
                "--output-last-message", str(result), "--skip-git-repo-check"]
    command += [session_id, "-"] if session_id else ["-"]
    event = {"dispatch_id": dispatch_id, "task_id": task_id, "role": role, "model": role_data["model"], "reasoning_effort": role_data["reasoning_effort"],
             "command": command, "mode": "run" if run else "dry-run", "at": utc_now(),
             "phase": phase, "session_id": session_id, "cwd": str(cwd), "status": "PLANNED"}
    if run:
        if not prompt_file.is_file(): raise ControlError(f"Prompt dosyası yok: {prompt_file}")
        folder.mkdir(parents=True, exist_ok=False)
        cwd.mkdir(parents=True, exist_ok=True)
        executable = resolve_codex_executable()
        command[0] = executable
        prompt = prompt_file.read_text(encoding="utf-8")
        prompt += (f"\nCONTROL CONTRACT: run already prepared at {output}. Use its frozen skill-snapshot. "
                   f"Role {role}, phase {phase}, stable task_id {task_id}. Sources are read-only. "
                   f"Write only inside {cwd}. Never prepare, close, update shared skills, or invent receipts. "
                   "Write the complete role result to an artifact file. Return only its artifact_path "
                   "(absolute path) and artifact_sha256 computed with code; do not repeat its contents. ")
        if role == "reviewer" and phase == "blind":
            prompt += "Read only original sources and neutral requirements, not analysis, proposed outcomes or control expectations. Save immutable blind notes."
        elif role == "reviewer":
            prompt += ("Set reviewer.task_id to this task_id. Bind the new artifact hashes; independently assess all changed dependencies. "
                       f"Read the local deterministic QA report at {output / 'deterministic-qa.json'} and do not spend a model turn repeating its mechanical checks. "
                       "Preserve critical unknowns and explain non-PASS controls.")
        else:
            prompt += "Set analysis_record.task_id to this task_id. Critical unknowns stay critical:true with open_issue; never downgrade importance to pass a gate."
        event["status"] = "RUNNING"
        if on_start:
            on_start(event)
        started_at = time.monotonic()
        try:
            telemetry = stream_process(command, prompt, cwd, folder / "events.jsonl", folder / "stderr.log", timeout_seconds)
            event.update(telemetry)
            event["session_id"] = telemetry.get("session_id") or session_id
            event["completed_at"] = utc_now()
            if event.get("returncode") == 0 and event.get("status") == "COMPLETED" and event.get("session_id"):
                pointer = read_json(result)
                artifact = Path(pointer.get("artifact_path", ""))
                if not artifact.is_absolute():
                    artifact = cwd / artifact
                artifact = artifact.resolve()
                if not artifact.is_relative_to(cwd.resolve()) or not artifact.is_file() or digest_file(artifact) != pointer.get("artifact_sha256"):
                    raise ControlError("Sonuç yolu/hash'i görev alanıyla eşleşmiyor.")
                event.update(result_file=artifact.relative_to(output).as_posix(), result_sha256=digest_file(artifact))
            else:
                event["result_sha256"] = None
                if event.get("status") == "COMPLETED":
                    event.update(status="FAILED", error="Gerçek oturum kimliği alınamadı.")
        except KeyboardInterrupt:
            event.update(status="FAILED", error="Görev kullanıcı tarafından kesildi; süreç durduruldu.", returncode=130,
                         result_sha256=None, completed_at=utc_now())
        except (OSError, ValueError, ControlError) as exc:
            event.update(status="FAILED", error=str(exc), returncode=event.get("returncode") or 1, result_sha256=None, completed_at=utc_now())
        finally:
            event.setdefault("duration_seconds", round(time.monotonic() - started_at, 3))
            event.setdefault("usage", None)  # Unknown usage is never reported as zero.
    return event


def resolve_codex_executable() -> str:
    found = shutil.which("codex.exe") or shutil.which("codex")
    if found and (os.name != "nt" or Path(found).suffix.lower() in {".exe", ".com"}):
        return found
    # npm's Windows shim is not executed through a shell. Use its installed native binary.
    if found:
        npm_codex = Path(found).parent / "node_modules" / "@openai" / "codex"
        package = npm_codex / "package.json"
        if package.is_file() and read_json(package).get("name") == "@openai/codex":
            candidates = list((npm_codex / "node_modules" / "@openai").glob("codex-win32-*/vendor/*/bin/codex.exe"))
            if len(candidates) == 1 and candidates[0].is_file():
                return str(candidates[0])
    raise ControlError("Yerel Codex çalıştırılabilir dosyası bulunamadı; kabuk veya izin baypası kullanılmaz.")


def cmd_dispatch(args: argparse.Namespace) -> int:
    output = Path(args.output_dir).resolve(); path = manifest_path(output); m = assert_manifest(path)
    coordinator_bootstrap = args.role == "coordinator" and args.caller_role == "controller"
    if args.caller_role != "coordinator" and not coordinator_bootstrap:
        raise ControlError("Yalnız coordinator işçi dağıtabilir; coordinator başlatma çağıranı controller olmalıdır. Çağıran rol doğrulanmış kimlik değildir.")
    if args.role == "coordinator" and not coordinator_bootstrap:
        raise ControlError("Coordinator yalnız controller tarafından başlatılabilir.")
    if args.role == "critical_adjudicator" and not args.critical:
        raise ControlError("Critical adjudicator yalnız açık --critical koşuluyla çağrılır.")
    policy = load_policy()
    previous = None
    if getattr(args, "resume_task", None):
        previous = next((d for d in reversed(m["dispatches"])
                         if (d.get("task_id") or d.get("dispatch_id")) == args.resume_task or d.get("dispatch_id") == args.resume_task), None)
        if not previous or previous.get("role") != args.role or not previous.get("session_id"):
            raise ControlError("Aynı role ait kayıtlı oturum bulunamadı.")
        if previous.get("mode") != "run":
            raise ControlError("Yerleşik görev kendi oturumunda sürdürülür; CLI --resume-task yalnız CLI kaydını sürdürür.")
    if args.role == "coordinator" and not previous and any(d.get("role") == "coordinator" and d.get("mode") in {"run", "native"} for d in m["dispatches"]):
        raise ControlError("Koordinatör zaten kayıtlı; aynı oturumu --resume-task ile sürdürün.")
    phase = getattr(args, "phase", "work")
    timeout_cap = None
    if args.run:
        timeout_cap = assert_budget_available(m, phase)
        if getattr(args, "timeout_seconds", None) is not None:
            timeout_cap = min(timeout_cap, args.timeout_seconds)
    if args.role == "reviewer":
        if phase not in {"blind", "compare", "revision"}:
            raise ControlError("Denetçi için blind/compare/revision aşaması gerekli.")
        if phase != "blind" and (not previous or not any(d.get("role") == "reviewer" and d.get("phase") == "blind" and d.get("returncode") == 0 and d.get("session_id") == previous["session_id"] for d in m["dispatches"])):
            raise ControlError("Aynı bağımsız denetçinin önce kör incelemesi tamamlanmalı.")
        if args.run and phase in {"compare", "revision"}:
            acquire_operation(m["run_id"], "pre-review-qa")
            try:
                m = assert_manifest(path)
                current = m.get("quality_precheck", {})
                analysis_sha = m.get("artifacts", {}).get("analysis_record", {}).get("sha256")
                workbook_sha = m.get("artifacts", {}).get("workbook", {}).get("sha256")
                if current.get("status") != "PASS" or current.get("analysis_sha256") != analysis_sha or current.get("workbook_sha256") != workbook_sha:
                    report = run_pre_review_qa(m, output)
                    m["revision"] += 1; save_manifest(path, m)
                    if report["status"] != "PASS":
                        raise ControlError("Deterministik ön kalite kapısı geçmedi: " + "; ".join(report["failures"]))
            finally:
                release_operation(m["run_id"])
    def started(event):
        current = assert_manifest(path)
        acquire_operation(current["run_id"], "dispatch-start")
        try:
            current = assert_manifest(path)
            if event["role"] == "coordinator" and not previous and any(d.get("role") == "coordinator" and d.get("mode") in {"run", "native"} for d in current["dispatches"]):
                raise ControlError("Başka koordinatör zaten başladı.")
            current["dispatches"].append(event)
            save_manifest(path, current)
        finally:
            release_operation(current["run_id"])
    acquire_operation(m["run_id"], "dispatch")
    held = True
    try:
        release_operation(m["run_id"]); held = False
        event = run_dispatch(args.role, output, Path(args.prompt_file), args.run,
                             task_id=(previous.get("task_id") or previous.get("dispatch_id")) if previous else None,
                             session_id=previous.get("session_id") if previous else None, phase=phase,
                             timeout_seconds=timeout_cap, on_start=started,
                             working_dir=previous.get("cwd") if previous else None)
        artifact_name = None
        if args.run and event.get("status") == "COMPLETED":
            if args.role == "coordinator" and phase in {"work", "revision"}:
                artifact_name = "analysis_record"
            elif args.role == "reviewer" and phase in {"compare", "revision"}:
                artifact_name = "review_attestation"
            if artifact_name:
                body = read_json(output / event["result_file"])
                bound_task = body.get("task_id") if artifact_name == "analysis_record" else body.get("reviewer", {}).get("task_id")
                if bound_task != event["task_id"]:
                    event.update(status="FAILED", returncode=1, result_sha256=None,
                                 error="Sonuç sabit task_id ile bağlı değil; artefakt otomatik kaydedilmedi.")
                    artifact_name = None
        if args.run:
            atomic_json(output / "dispatches" / event["dispatch_id"] / "receipt.json", {"run_id": m["run_id"], "event": event})
        m = assert_manifest(path); acquire_operation(m["run_id"], "dispatch-result"); held = True
        m = assert_manifest(path)
        event["caller_role"] = args.caller_role; event["max_concurrent_workers"] = policy["max_coordinator_workers"]
        m["dispatches"] = [d for d in m["dispatches"] if d["dispatch_id"] != event["dispatch_id"]] + [event]
        if artifact_name:
            record_artifact(m, output, artifact_name, output / event["result_file"])
        m["revision"] += 1; save_manifest(path, m)
    finally:
        if held: release_operation(m["run_id"])
    print(json.dumps(event, ensure_ascii=False))
    return 2 if args.run and event.get("status") != "COMPLETED" else 0


def receipt_valid(event):
    if event.get("mode") == "native":
        seal = event.get("seal", {})
        return (seal.get("artifact_sha256") == event.get("result_sha256") and seal.get("role") == event.get("role")
                and seal.get("phase") == event.get("phase") and bool(event.get("seal_at")) and native_receipt_valid(event))
    return (event.get("mode") == "run" and event.get("returncode") == 0 and event.get("status") == "COMPLETED"
            and bool(event.get("session_id")) and bool(event.get("result_sha256")))


def event_task_id(event: dict[str, Any]) -> str | None:
    return event.get("task_id") or event.get("dispatch_id")


def blind_precedes(blind, result):
    if blind.get("mode") == "native" or result.get("mode") == "native":
        return (blind.get("mode") == result.get("mode") == "native"
                and bool(blind.get("seal_at")) and bool(result.get("seal_at"))
                and blind["seal_at"] <= result["seal_at"]
                and blind.get("seal_line", 0) < result.get("seal_line", 0))
    return blind.get("completed_at", blind.get("at", "z")) <= result.get("at", "")


def cmd_recover_dispatch(args):
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    if not any(d.get("dispatch_id") == args.dispatch_id and d.get("mode") == "run" and d.get("status") == "RUNNING" for d in m["dispatches"]):
        raise ControlError("Kurtarılacak RUNNING CLI görevi yok.")
    receipt_path = path.parent / "dispatches" / args.dispatch_id / "receipt.json"
    if not receipt_path.resolve().is_relative_to(path.parent):
        raise ControlError("Makbuz koşu alanından çıkamaz.")
    saved = read_json(receipt_path); event = saved.get("event", {})
    if saved.get("run_id") != m["run_id"] or event.get("dispatch_id") != args.dispatch_id or event.get("status") not in {"COMPLETED", "FAILED", "TIMED_OUT"}:
        raise ControlError("Çalıştırıcının terminal makbuzu geçersiz.")
    if event["status"] == "COMPLETED":
        artifact = (path.parent / event.get("result_file", "")).resolve()
        if not receipt_valid(event) or not artifact.is_relative_to(path.parent) or not artifact.is_file() or digest_file(artifact) != event.get("result_sha256"):
            raise ControlError("Tamamlanmış görev artefaktı değişmiş/eksik.")
        artifact_name = ("analysis_record" if event.get("role") == "coordinator" and event.get("phase") in {"work", "revision"}
                         else "review_attestation" if event.get("role") == "reviewer" and event.get("phase") in {"compare", "revision"}
                         else None)
        if artifact_name:
            body = read_json(artifact)
            bound_task = body.get("task_id") if artifact_name == "analysis_record" else body.get("reviewer", {}).get("task_id")
            if bound_task != event_task_id(event):
                raise ControlError("Kurtarılan sonuç sabit task_id ile bağlı değil.")
    else:
        artifact_name = None
    acquire_operation(m["run_id"], "recover-dispatch")
    try:
        m = assert_manifest(path)
        existing = next((d for d in m["dispatches"] if d.get("dispatch_id") == args.dispatch_id), None)
        if not existing or existing.get("status") != "RUNNING":
            raise ControlError("Görev durumu zaten değişmiş.")
        m["dispatches"] = [event if d is existing else d for d in m["dispatches"]]
        if artifact_name:
            record_artifact(m, path.parent, artifact_name, artifact)
        m["revision"] += 1; save_manifest(path, m)
    finally:
        release_operation(m["run_id"])
    return 0


def result_seal(m, output, args):
    artifact = Path(args.artifact).resolve()
    if not artifact.is_relative_to(output.resolve()) or not artifact.is_file():
        raise ControlError("Makbuz artefaktı çalışma alanında olmalı.")
    return {"run_id": m["run_id"], "role": args.role, "phase": args.phase,
            "artifact_path": artifact.relative_to(output.resolve()).as_posix(), "artifact_sha256": digest_file(artifact)}


def cmd_seal_result(args):
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    # This printed tool result is subsequently observed in the genuine session log.
    print("TEKLIF_RESULT_SEAL:" + json.dumps(result_seal(m, path.parent, args), ensure_ascii=False))
    return 0


def cmd_register_session(args):
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    observed = read_native_session(args.session_log, seal=result_seal(m, path.parent, args))
    expected = load_policy()["roles"][args.role]
    if observed["model"] != expected["model"] or observed["reasoning_effort"] != expected["reasoning_effort"]:
        raise ControlError("Yerleşik oturumun gerçek model/eforu role uygun değil.")
    allowed_cwds = [path.parent, Path(m["source_inventory"]["root"])]
    if not any(Path(observed["cwd"]).resolve().is_relative_to(p.resolve()) for p in allowed_cwds):
        raise ControlError("Oturum bu analiz alanına ait değil.")
    artifact = Path(args.artifact).resolve()
    if not artifact.is_relative_to(path.parent) or not artifact.is_file():
        raise ControlError("Makbuz artefaktı analiz çalışma alanında olmalı.")
    session_id = observed["session_id"]
    if args.role == "coordinator" and any(d.get("role") == "coordinator" and d.get("mode") in {"run", "native"} and d.get("session_id") != session_id for d in m["dispatches"]):
        raise ControlError("Farklı koordinatör zaten kayıtlı.")
    if any(d.get("mode") in {"run", "native"} and d.get("role") != args.role and d.get("session_id") == session_id for d in m["dispatches"]):
        raise ControlError("Koordinatör kendi denetçisi olamaz.")
    if args.phase != "blind":
        body = read_json(artifact)
        task_id = body.get("task_id") if args.role == "coordinator" else body.get("reviewer", {}).get("task_id")
        if task_id != session_id:
            raise ControlError("Yerleşik sonuç task_id gerçek oturum kimliği olmalı.")
    if args.role == "reviewer" and args.phase not in {"blind", "compare", "revision"}:
        raise ControlError("Denetçi aşaması blind/compare/revision olmalı.")
    if args.role == "reviewer" and args.phase != "blind" and not any(d.get("role") == "reviewer" and d.get("phase") == "blind" and d.get("session_id") == session_id and receipt_valid(d) for d in m["dispatches"]):
        raise ControlError("Aynı denetçinin kör aşama makbuzu yok.")
    event = {**observed, "dispatch_id": session_id, "task_id": session_id, "role": args.role, "phase": args.phase,
             "mode": "native", "status": "RESULT_RECORDED", "returncode": 0, "at": utc_now(),
             "result_file": artifact.relative_to(path.parent).as_posix(), "result_sha256": observed["seal"]["artifact_sha256"]}
    acquire_operation(m["run_id"], "register-session")
    try:
        m = assert_manifest(path)
        if args.role == "coordinator" and any(d.get("role") == "coordinator" and d.get("mode") in {"run", "native"} and d.get("session_id") != session_id for d in m["dispatches"]):
            raise ControlError("Başka koordinatör zaten kayıtlı.")
        if any(d.get("mode") in {"run", "native"} and d.get("role") != args.role and d.get("session_id") == session_id for d in m["dispatches"]):
            raise ControlError("Koordinatör kendi denetçisi olamaz.")
        if args.role == "reviewer" and args.phase != "blind" and not any(d.get("role") == "reviewer" and d.get("phase") == "blind" and d.get("session_id") == session_id and receipt_valid(d) and blind_precedes(d, event) for d in m["dispatches"]):
            raise ControlError("Kör inceleme mührü sonuç mühründen önce olmalı.")
        if event["result_sha256"] != digest_file(artifact):
            raise ControlError("Kayıt sırasında artefakt değişti.")
        m["dispatches"].append(event); m["revision"] += 1; save_manifest(path, m)
    finally:
        release_operation(m["run_id"])
    print(json.dumps(event, ensure_ascii=False)); return 0


def verify_artifacts(m: dict[str, Any], output: Path, reasons: list[str]) -> bool:
    ok = True
    for name, artifact in m.get("artifacts", {}).items():
        path = output / artifact.get("relative_path", "")
        if not path.resolve().is_relative_to(output.resolve()) or not path.is_file() or digest_file(path) != artifact.get("sha256") or path.stat().st_size != artifact.get("size_bytes"):
            reasons.append(f"Artefakt değişmiş/eksik: {name}"); ok = False
        elif name in {"workbook", "report_pdf"}:
            try:
                (validate_xlsx if name == "workbook" else validate_pdf)(path)
            except (ValueError, OSError) as exc:
                reasons.append(f"Çıktı yapısı doğrulanamadı: {name}: {exc}"); ok = False
    return ok


def workbook_precheck(path: Path) -> dict[str, Any]:
    structural = validate_xlsx(path)
    texts: list[str] = []
    broken_links: list[str] = []
    hyperlink_count = 0
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith((".xml", ".rels")):
                text_value = archive.read(name).decode("utf-8", errors="replace")
                texts.append(text_value)
                if "\ufffd" in text_value:
                    raise ControlError(f"Excel XML içinde bozuk Unicode karakteri var: {name}")
            if not name.endswith(".rels"):
                continue
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError as exc:
                raise ControlError(f"Excel ilişki XML'i bozuk: {name}") from exc
            for relation in root:
                if relation.get("TargetMode") != "External":
                    continue
                target = relation.get("Target", "")
                hyperlink_count += 1
                parsed = urlparse(target)
                if parsed.scheme.lower() != "file" and not (not parsed.scheme and not target.lower().startswith("file:")):
                    continue
                raw = unquote(parsed.path or parsed.netloc)
                if re.match(r"^/[A-Za-z]:/", raw):
                    raw = raw[1:]
                candidate = Path(raw.replace("/", os.sep)) if parsed.scheme else (path.parent / unquote(target)).resolve()
                if not candidate.exists():
                    broken_links.append(target)
    joined = "\n".join(texts)
    hash_labelled = "SHA-256" in joined and bool(re.search(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", joined))
    if broken_links:
        raise ControlError("Excel içinde hedefi bulunamayan dosya bağlantısı var: " + ", ".join(broken_links[:5]))
    if not hash_labelled:
        raise ControlError("Excel içinde açık SHA-256 etiketi ve 64 haneli değer birlikte bulunamadı.")
    return {**structural, "hyperlinks": hyperlink_count, "broken_file_hyperlinks": 0,
            "unicode_replacement_characters": 0, "labelled_sha256": True}


def run_pre_review_qa(manifest: dict[str, Any], output: Path) -> dict[str, Any]:
    failures: list[str] = []
    analysis_meta = manifest.get("artifacts", {}).get("analysis_record")
    workbook_meta = manifest.get("artifacts", {}).get("workbook")
    checks: dict[str, Any] = {}
    if not analysis_meta or not workbook_meta:
        failures.append("Ön inceleme için analysis_record ve workbook kayıtlı olmalı.")
    else:
        analysis_path = output / analysis_meta["relative_path"]
        workbook_path = output / workbook_meta["relative_path"]
        if digest_file(analysis_path) != analysis_meta["sha256"] or digest_file(workbook_path) != workbook_meta["sha256"]:
            failures.append("Ön inceleme artefakt hash'i değişmiş.")
        else:
            try:
                analysis = read_json(analysis_path)
                encoded = json.dumps(analysis, ensure_ascii=False)
                if "\ufffd" in encoded:
                    raise ControlError("Analiz kaydında bozuk Unicode karakteri var.")
                facts = analysis.get("facts")
                if not isinstance(facts, list) or not facts:
                    raise ControlError("Analiz olgu listesi boş/geçersiz.")
                ids = [f.get("fact_id") for f in facts if isinstance(f, dict)]
                if len(ids) != len(facts) or any(not x for x in ids) or len(ids) != len(set(ids)):
                    raise ControlError("Analiz olgu kimlikleri boş veya yinelenmiş.")
                uncovered = [f["fact_id"] for f in facts if f.get("evidence_status") == "verified" and not f.get("location")]
                if uncovered:
                    raise ControlError("Kaynak konumu olmayan kanıtlı olgular: " + ", ".join(uncovered[:10]))
                checks["analysis"] = {"facts": len(facts), "unique_fact_ids": True,
                                      "verified_source_locations": True, "unicode_replacement_characters": 0}
                checks["workbook"] = workbook_precheck(workbook_path)
            except (ControlError, OSError, ValueError, zipfile.BadZipFile) as exc:
                failures.append(str(exc))
    report = {"schema": "teklif-deterministic-qa/v1", "run_id": manifest["run_id"],
              "analysis_sha256": (analysis_meta or {}).get("sha256"),
              "workbook_sha256": (workbook_meta or {}).get("sha256"),
              "status": "PASS" if not failures else "FAIL", "checks": checks,
              "failures": failures, "checked_at": utc_now()}
    report_path = output / "deterministic-qa.json"
    atomic_json(report_path, report)
    manifest["quality_precheck"] = {"status": report["status"], "analysis_sha256": report["analysis_sha256"],
                                    "workbook_sha256": report["workbook_sha256"],
                                    "report_file": report_path.relative_to(output).as_posix(),
                                    "report_sha256": digest_file(report_path), "failures": failures,
                                    "checked_at": report["checked_at"]}
    return report


def cmd_pre_review_qa(args: argparse.Namespace) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    acquire_operation(m["run_id"], "pre-review-qa")
    try:
        m = assert_manifest(path)
        report = run_pre_review_qa(m, path.parent)
        m["revision"] += 1; save_manifest(path, m)
    finally:
        release_operation(m["run_id"])
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


def validate_evidence(m: dict[str, Any], output: Path, reasons: list[str]) -> tuple[bool, bool, bool, dict[str, dict[str, Any]]]:
    analysis = m.get("artifacts", {}).get("analysis_record"); review = m.get("artifacts", {}).get("review_attestation")
    if not analysis or not review: return False, False, False, {}
    try:
        a = read_json(output / analysis["relative_path"]); r = read_json(output / review["relative_path"])
    except ControlError as e:
        reasons.append(str(e)); return False, False, False, {}
    if a.get("report_requested") is True:
        m["report_requested"] = True
    facts = a.get("facts"); competitors = a.get("competitors"); exclusions = a.get("exclusions")
    facts_ok = isinstance(facts, list) and bool(facts) and isinstance(a.get("task_id"), str) and bool(a["task_id"].strip()); critical_ok = True
    m["analysis_mode"] = a.get("analysis_mode")
    m["decision_status"] = a.get("decision_status")
    m["has_recommendation"] = a.get("recommendation") is not None
    unknown = []
    source_hashes = {x["sha256"] for x in m["source_inventory"]["entries"]}
    source_ids = {x["source_id"]: x["sha256"] for x in m["source_inventory"]["entries"]}
    critical_ids = a.get("critical_fact_ids")
    if not isinstance(critical_ids, list) or not critical_ids or len(set(critical_ids)) != len(critical_ids): critical_ok = False
    observed_critical: set[str] = set()
    for fact in facts if isinstance(facts, list) else []:
        if not isinstance(fact, dict) or not all(fact.get(k) for k in ("fact_id", "claim", "evidence_status")):
            facts_ok = False; continue
        if fact.get("evidence_status") == "verified" and (not all(fact.get(k) for k in ("source_id", "source_sha256", "location")) or source_ids.get(fact["source_id"]) != fact["source_sha256"] or fact["source_sha256"] not in source_hashes): facts_ok = False
        if fact.get("critical"):
            observed_critical.add(fact.get("fact_id", ""))
            if fact.get("evidence_status") != "verified":
                unknown.append(fact.get("fact_id"))
                if not isinstance(fact.get("open_issue"), str) or not fact["open_issue"].strip():
                    facts_ok = False
    reviewer = r.get("reviewer", {}) if isinstance(r.get("reviewer"), dict) else {}
    independent = (reviewer.get("role") == "reviewer" and reviewer.get("model") == "gpt-5.6-sol" and
                   reviewer.get("reasoning_effort") == "high" and reviewer.get("task_id") and
                   reviewer.get("task_id") != a.get("task_id") and r.get("all_critical_evidence_reviewed") is True and
                   r.get("all_competitors_reviewed") is True and r.get("all_exclusion_reasons_reviewed") is True)
    reviewer_receipt = any(d.get("role") == "reviewer" and receipt_valid(d) and d.get("returncode") == 0 and
                           d.get("phase") in {"compare", "revision"} and
                           d.get("model") == "gpt-5.6-sol" and d.get("reasoning_effort") == "high" and
                           event_task_id(d) == reviewer.get("task_id") and d.get("result_sha256") == review.get("sha256")
                           for d in m.get("dispatches", []) if isinstance(d, dict))
    coordinator_receipt = any(d.get("role") == "coordinator" and receipt_valid(d) and d.get("returncode") == 0 and
                              d.get("model") == "gpt-5.6-sol" and d.get("reasoning_effort") == "high" and
                              event_task_id(d) == a.get("task_id") and d.get("result_sha256") == analysis.get("sha256")
                              for d in m.get("dispatches", []) if isinstance(d, dict))
    if not reviewer_receipt: reasons.append("Reviewer için gerçek oturuma bağlı sonuç makbuzu yok.")
    if not coordinator_receipt: reasons.append("Analiz için gerçek coordinator oturum makbuzu yok.")
    coordinator_sessions = {d.get("session_id") for d in m.get("dispatches", []) if d.get("role") == "coordinator" and d.get("mode") in {"run", "native"} and d.get("session_id")}
    reviewer_sessions = {d.get("session_id") for d in m.get("dispatches", []) if d.get("role") == "reviewer" and d.get("mode") in {"run", "native"} and d.get("session_id")}
    if coordinator_sessions & reviewer_sessions:
        independent = False
    review_events = [d for d in m.get("dispatches", []) if d.get("role") == "reviewer" and event_task_id(d) == reviewer.get("task_id") and d.get("phase") in {"compare", "revision"}]
    blind_ok = False
    for event in review_events:
        for blind in m.get("dispatches", []):
            note = output / blind.get("result_file", "")
            if (blind.get("role") == "reviewer" and blind.get("phase") == "blind"
                    and blind.get("session_id") and blind.get("session_id") == event.get("session_id")
                    and receipt_valid(blind) and blind_precedes(blind, event)
                    and note.resolve().is_relative_to(output.resolve()) and note.is_file()
                    and digest_file(note) == blind.get("result_sha256")):
                blind_ok = True
    if not blind_ok:
        independent = False
        reasons.append("Denetçinin önce tamamlanmış, değişmemiş kör inceleme kaydı yok.")
    independent = independent and reviewer_receipt and coordinator_receipt
    if set(critical_ids or []) != observed_critical: critical_ok = False
    checked_ids = r.get("checked_fact_ids")
    if not isinstance(checked_ids, list) or set(checked_ids) != observed_critical:
        critical_ok = False
    required_bindings = {"run_id": m["run_id"], "dataset_sha256": m["source_inventory"]["dataset_sha256"],
                         "analysis_sha256": analysis["sha256"], "workbook_sha256": m.get("artifacts", {}).get("workbook", {}).get("sha256")}
    if m.get("report_requested"):
        required_bindings["report_pdf_sha256"] = m.get("artifacts", {}).get("report_pdf", {}).get("sha256")
    if any(r.get(k) != v for k, v in required_bindings.items()):
        independent = False; reasons.append("Reviewer tasdiki run/dataset/analysis/workbook hash'lerine bağlı değil.")
    if not facts_ok: reasons.append("Kanıt şeması veya özgün kaynak bağı geçmedi.")
    if not critical_ok: reasons.append("Kritik olgu bağımsız doğrulanmamış/varsayımdır.")
    if not independent: reasons.append("Bağımsız Sol/high reviewer tasdiki eksik veya self-review var.")
    semantic: dict[str, dict[str, Any]] = {}
    semantic["critical_facts_resolved"] = {"status": "UNVERIFIED" if unknown else "PASS",
                                          "reason": "Açık kritik konular: " + ", ".join(unknown) if unknown else None}
    attestations = r.get("control_attestations", {})
    semantic_controls = ("numeric_reconciliation", "fair_comparison", "freshness_validity", "cost_completeness",
                         "formula_recalculation", "parameter_change_test", "output_consistency", "visual_review")
    for control in semantic_controls:
        item = attestations.get(control) if isinstance(attestations, dict) else None
        valid = (isinstance(item, dict) and item.get("status") in {"PASS", "FAIL", "UNVERIFIED", "NA"} and
                 isinstance(item.get("evidence"), list) and bool(item["evidence"]) and
                 item.get("reviewed_by") == reviewer.get("task_id") and
                 (item.get("status") == "PASS" or isinstance(item.get("reason"), str) and bool(item["reason"].strip())))
        # This is an attestation presence/identity check, never a semantic re-performance.
        semantic[control] = {"status": item["status"] if valid else "FAIL", "reason": item.get("reason") if valid else "Tasdik şeması/kimliği geçersiz.",
                             "evidence": item.get("evidence", []) if valid else []}
        if not valid: reasons.append(f"Denetçi tasdiki eksik/geçersiz: {control}")
    return facts_ok and critical_ok, critical_ok, independent and isinstance(competitors, list) and isinstance(exclusions, list), semantic


def cmd_verify(args: argparse.Namespace, lock_held=False) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path); output = path.parent
    if not lock_held:
        acquire_operation(m["run_id"], "verify")
    try:
        m = assert_manifest(path)
        reasons: list[str] = []
        current_inventory = inventory(Path(m["source_inventory"]["root"]), [e["relative_path"] for e in m["source_inventory"]["entries"]])
        sources_ok = current_inventory["dataset_sha256"] == m["source_inventory"].get("dataset_sha256") and current_inventory["entries"] == m["source_inventory"].get("entries")
        frozen_skill = skill_snapshot(Path(m["skill_snapshot"]["root"]))
        skills_ok = frozen_skill["combined_sha256"] == m["skill_snapshot"].get("combined_sha256") and frozen_skill["version"] == m["skill_snapshot"].get("version")
        if not sources_ok: reasons.append("Kaynak envanteri/dataset hash değişmiş.")
        if not skills_ok: reasons.append("Skill sürümü veya dosya hash'i değişmiş.")
        artifact_ok = verify_artifacts(m, output, reasons)
        evidence_ok, critical_ok, reviewer_ok, semantic = validate_evidence(m, output, reasons)
        statuses = {"source_hashes_verified": sources_ok, "skill_hashes_verified": skills_ok,
                    "artifact_hashes_verified": artifact_ok, "evidence_schema_verified": evidence_ok,
                    "critical_facts_independently_checked": critical_ok, "independent_reviewer_verified": reviewer_ok,
                    "competitor_and_exclusion_reviewed": reviewer_ok}
        statuses.update(semantic)
        for cid, value in statuses.items():
            supplied = value if isinstance(value, dict) else None
            status = supplied["status"] if supplied else ("PASS" if value else "FAIL")
            m["controls"][cid] = {"status": status, "evidence": supplied.get("evidence", []) if supplied else (reasons if status == "FAIL" else ["verify"]), "reason": supplied.get("reason") if supplied else None}
        m["revision"] += 1; save_manifest(path, m)
    finally:
        if not lock_held:
            release_operation(m["run_id"])
    print(json.dumps({**m["delivery_gate"], "final_gate": m["final_gate"]}, ensure_ascii=False)); return 0 if m["delivery_gate"]["status"] != "BLOCKED" else 2


def cmd_close(args: argparse.Namespace) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    if m.get("lifecycle", {}).get("closed_at"):
        # A prior close may have committed the durable lifecycle record and then
        # been interrupted before lock cleanup. Repeating close only finalizes cleanup.
        if OPERATION_LOCK.exists() and read_json(OPERATION_LOCK).get("run_id") == m["run_id"]:
            OPERATION_LOCK.unlink()
        release_analysis_lock(m["run_id"])
        return 0
    acquire_operation(m["run_id"], "close")
    try:
        m = assert_manifest(path)
        if any(d.get("status") == "RUNNING" for d in m["dispatches"]):
            raise ControlError("Çalışan görev varken kapanış/iptal kaydı yazılamaz; önce görevi durdurun.")
        if not args.abort and cmd_verify(args, lock_held=True) != 0:
            raise ControlError("Kapatma öncesi tazelik/teslim kontrolü geçmedi.")
        m = assert_manifest(path)
        expected = "PRELIMINARY_ALLOWED" if getattr(args, "preliminary", False) else "FINAL_ALLOWED"
        if not args.abort and m.get("delivery_gate", {}).get("status") != expected:
            raise ControlError("İstenen teslim kapısı açık değil; ön sonuç için --preliminary kullanın.")
        m["lifecycle"] = {**m.get("lifecycle", {}), "status": "CANCELLED" if args.abort else ("PRELIMINARY_COMPLETE" if args.preliminary else "FINAL_COMPLETE"),
                          "closed_at": utc_now(), "reason": getattr(args, "reason", None)}
        save_manifest(path, m)
        release_analysis_lock(m["run_id"])
    finally:
        # The durable marker is gone, but this per-operation mutex belongs to this command.
        release_operation(m["run_id"])
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    print(json.dumps(inventory(Path(args.source_dir)), ensure_ascii=False, indent=2)); return 0


def cmd_status(args):
    m = assert_manifest(manifest_path(Path(args.output_dir)))
    print(json.dumps({"run_id": m["run_id"], "lifecycle": m["lifecycle"], "delivery_gate": m["delivery_gate"],
                      "revalidation": m.get("revalidation", {}), "budget": budget_state(m),
                      "quality_precheck": m.get("quality_precheck"),
                      "dispatches": [{k: d.get(k) for k in ("dispatch_id", "task_id", "role", "phase", "status", "session_id", "duration_seconds", "usage")} for d in m["dispatches"]]}, ensure_ascii=False))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Teklif değerlendirme bounded runtime/control gate")
    sub = p.add_subparsers(required=True)
    q = sub.add_parser("recover-dispatch"); q.add_argument("--output-dir", required=True); q.add_argument("--dispatch-id", required=True); q.set_defaults(func=cmd_recover_dispatch)
    q = sub.add_parser("inventory"); q.add_argument("--source-dir", required=True); q.set_defaults(func=cmd_inventory)
    q = sub.add_parser("preflight"); q.add_argument("--source-dir", required=True); q.add_argument("--output-dir", required=True); q.add_argument("--source-list"); q.add_argument("--receipt"); q.add_argument("--run", action="store_true", help="Kaynakları paylaşmadan gerçek dış model/ağ erişimini sınar."); q.set_defaults(func=cmd_preflight)
    q = sub.add_parser("prepare"); q.add_argument("--source-dir", required=True); q.add_argument("--output-dir", required=True); q.add_argument("--source-list"); q.add_argument("--preflight-receipt"); q.add_argument("--allow-unprobed-model", action="store_true", help="Yalnız dış model erişimi bu süreçte zaten doğrulandıysa açıkça kullanılır."); q.set_defaults(func=cmd_prepare)
    q = sub.add_parser("record-artifact"); q.add_argument("--output-dir", required=True); q.add_argument("--name", choices=(*REQUIRED_ARTIFACTS, "report_pdf"), required=True); q.add_argument("--artifact", required=True); q.set_defaults(func=cmd_record_artifact)
    q = sub.add_parser("dispatch"); q.add_argument("--output-dir", required=True); q.add_argument("--caller-role", required=True); q.add_argument("--role", required=True, choices=sorted(load_policy()["roles"])); q.add_argument("--prompt-file", required=True); q.add_argument("--critical", action="store_true", help="Yalnız critical_adjudicator için açık koşul beyanı."); q.add_argument("--run", action="store_true", help="Varsayılan dry-run; yalnız bu bayrak Codex çalıştırır."); q.set_defaults(func=cmd_dispatch)
    q.add_argument("--resume-task"); q.add_argument("--phase", choices=("work", "blind", "compare", "revision"), default="work")
    q.add_argument("--timeout-seconds", type=float)
    q = sub.add_parser("register-session"); q.add_argument("--output-dir", required=True); q.add_argument("--session-log", required=True); q.add_argument("--artifact", required=True); q.add_argument("--role", choices=("coordinator", "reviewer"), required=True); q.add_argument("--phase", choices=("work", "blind", "compare", "revision"), required=True); q.set_defaults(func=cmd_register_session)
    q = sub.add_parser("seal-result"); q.add_argument("--output-dir", required=True); q.add_argument("--artifact", required=True); q.add_argument("--role", choices=("coordinator", "reviewer"), required=True); q.add_argument("--phase", choices=("work", "blind", "compare", "revision"), required=True); q.set_defaults(func=cmd_seal_result)
    q = sub.add_parser("status"); q.add_argument("--output-dir", required=True); q.set_defaults(func=cmd_status)
    q = sub.add_parser("pre-review-qa"); q.add_argument("--output-dir", required=True); q.set_defaults(func=cmd_pre_review_qa)
    q = sub.add_parser("verify"); q.add_argument("--output-dir", required=True); q.set_defaults(func=cmd_verify)
    q = sub.add_parser("close"); q.add_argument("--output-dir", required=True); group = q.add_mutually_exclusive_group(); group.add_argument("--abort", action="store_true"); group.add_argument("--preliminary", action="store_true"); q.add_argument("--reason"); q.set_defaults(func=cmd_close)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except (ControlError, KeyError, TypeError, ValueError) as e: print(f"BLOKE: {e}", file=sys.stderr); return 2

if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
