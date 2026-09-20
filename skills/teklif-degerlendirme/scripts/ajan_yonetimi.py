#!/usr/bin/env python3
"""Deterministic runtime and final-control gate for teklif-degerlendirme.

This controller never interprets a source document.  It freezes byte-level inputs,
dispatches only policy-pinned Codex roles, and blocks FINAL when attestations or
required evidence are absent.  Caller identity is an assertion, not authentication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from cikti_denetimi import validate_xlsx, validate_pdf

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
SKILLS_ROOT = SKILL_ROOT.parent
POLICY_PATH = SKILL_ROOT / "config" / "ajan-politikasi.json"
ANALYSIS_LOCK = SKILLS_ROOT / ".teklif-analysis.lock"
UPDATE_LOCK = SKILLS_ROOT / ".teklif-update.lock"
OPERATION_LOCK = SKILLS_ROOT / ".teklif-analysis.operation.lock"
SCHEMA = "teklif-analysis-control/v1"
MANDATORY_CONTROLS = (
    "source_inventory_frozen", "skill_snapshot_frozen", "dataset_hash_verified",
    "source_hashes_verified", "skill_hashes_verified", "artifact_hashes_verified",
    "evidence_schema_verified", "critical_facts_independently_checked",
    "independent_reviewer_verified", "competitor_and_exclusion_reviewed",
    "numeric_reconciliation", "fair_comparison", "freshness_validity",
    "cost_completeness", "formula_recalculation", "parameter_change_test",
    "output_consistency", "visual_review",
)
REQUIRED_ARTIFACTS = ("analysis_record", "review_attestation", "workbook")
ALLOWED_MODELS = {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-6-astra"}


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


def acquire_operation(run_id: str, operation: str) -> None:
    if UPDATE_LOCK.exists(): raise ControlError(f"Güncelleme kilidi var: {UPDATE_LOCK}")
    if not ANALYSIS_LOCK.exists(): raise ControlError("Aktif analiz yaşam döngüsü kilidi yok.")
    lock = read_json(ANALYSIS_LOCK)
    if lock.get("run_id") != run_id: raise ControlError("Bu manifest başka aktif koşuya ait değil.")
    try: fd = os.open(OPERATION_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as e: raise ControlError("Başka bir analiz işlemi sürüyor.") from e
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "operation": operation, "pid": os.getpid(), "created_at": utc_now()}, f); f.flush(); os.fsync(f.fileno())
    if UPDATE_LOCK.exists():
        OPERATION_LOCK.unlink()
        raise ControlError("Güncelleme ile yarış oluştu; işlem durduruldu.")


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


def inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ControlError(f"Kaynak klasörü yok: {root}")
    entries: list[dict[str, Any]] = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
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


def skill_snapshot() -> dict[str, Any]:
    paths = [p for p in SKILL_ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    files = [{"relative_path": p.relative_to(SKILL_ROOT).as_posix(), "sha256": digest_file(p)} for p in sorted(paths)]
    version_path = SKILL_ROOT / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else None
    return {"root": str(SKILL_ROOT), "version": version, "files": files, "combined_sha256": stable_hash(files)}


def manifest_path(output_dir: Path) -> Path:
    return output_dir.resolve() / "analysis-manifest.json"


def default_controls() -> dict[str, Any]:
    return {cid: {"status": "PENDING", "evidence": [], "reason": None} for cid in MANDATORY_CONTROLS}


def gate(manifest: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
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
    manifest["updated_at"] = utc_now()
    atomic_json(path, manifest)


def cmd_prepare(args: argparse.Namespace) -> int:
    source = Path(args.source_dir).resolve(); output = Path(args.output_dir).resolve()
    try: output.relative_to(source)
    except ValueError: pass
    else: raise ControlError("İzole çıktı dizini kaynak dizininin içinde olamaz.")
    output.mkdir(parents=True, exist_ok=True)
    path = manifest_path(output)
    if path.exists():
        raise ControlError(f"Mevcut manifest üzerine yazılmaz: {path}")
    run_id = str(uuid.uuid4()); acquire_analysis_lock(run_id, "prepare")
    try:
        policy = load_policy()
        manifest = {"schema": SCHEMA, "run_id": run_id, "revision": 1, "created_at": utc_now(),
                    "policy": {"path": str(POLICY_PATH), "sha256": digest_file(POLICY_PATH), "version": policy.get("policy_version")},
                    "source_inventory": inventory(source), "skill_snapshot": skill_snapshot(),
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
    manifest["artifacts"][name] = {"relative_path": relative, "sha256": digest_file(path),
                                     "size_bytes": path.stat().st_size, "recorded_at": utc_now()}


def cmd_record_artifact(args: argparse.Namespace) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    acquire_operation(m["run_id"], "record-artifact")
    try:
        record_artifact(m, path.parent, args.name, Path(args.artifact)); m["revision"] += 1
        invalidate_checks(m); save_manifest(path, m)
    finally: release_operation(m["run_id"])
    return 0


def invalidate_checks(manifest):
    frozen = {key: manifest["controls"][key] for key in ("source_inventory_frozen", "skill_snapshot_frozen", "dataset_hash_verified")}
    manifest["controls"] = default_controls()
    manifest["controls"].update(frozen)


def run_dispatch(role: str, output: Path, prompt_file: Path, run: bool) -> dict[str, Any]:
    policy = load_policy(); role_data = policy["roles"].get(role)
    if not role_data: raise ControlError(f"Bilinmeyen rol: {role}")
    if role_data.get("conditional") and not run: pass  # recorded honestly in plan
    result = output / f"{role}-{uuid.uuid4()}-last-message.md"
    sandbox = "workspace-write" if role == "coordinator" else "read-only"
    agent_settings = ["-c", "agents.enabled=false"] if role != "coordinator" else ["-c", "agents.enabled=true", "-c", "agents.max_concurrent_threads_per_session=3", "-c", "agents.default_subagent_model='gpt-5.6-terra'"]
    command = ["codex", "exec", "--model", role_data["model"], "-c", f"model_reasoning_effort='{role_data['reasoning_effort']}'", *agent_settings,
               "--sandbox", "read-only", "--cd", str(output),
               "--output-last-message", str(result), "--skip-git-repo-check", "-"]
    command[command.index("read-only")] = sandbox
    dispatch_id = str(uuid.uuid4())
    event = {"dispatch_id": dispatch_id, "role": role, "model": role_data["model"], "reasoning_effort": role_data["reasoning_effort"],
             "command": command, "mode": "run" if run else "dry-run", "at": utc_now()}
    if run:
        if not prompt_file.is_file(): raise ControlError(f"Prompt dosyası yok: {prompt_file}")
        executable = resolve_codex_executable()
        command[0] = executable
        prompt = prompt_file.read_text(encoding="utf-8")
        if role == "reviewer":
            prompt += f"\n\nCONTROL CONTRACT: Return only one UTF-8 JSON object. Set reviewer.task_id exactly to {dispatch_id}; include checked_fact_ids covering every independently checked critical fact; bind this run's input hashes and record the required attestations.\n"
        elif role == "coordinator":
            prompt += f"\n\nCONTROL CONTRACT: This run has already been prepared; read analysis-manifest.json in this working directory. Do not call prepare again or write shared skill/controller state. Work only in the isolated output directory; source files are read-only. Use native subagents with explicit approved models/efforts as needed. Return only the completed analysis_record JSON as final message, task_id exactly {dispatch_id}. Do not invent reviewer identities or receipts. The external controller records this result before dispatching the independent reviewer and verifies the final gate afterwards. Do not close the run yourself.\n"
        completed = subprocess.run(command, input=prompt, text=True, encoding="utf-8", capture_output=True, cwd=output, check=False, shell=False)
        event["returncode"] = completed.returncode; event["result_file"] = result.name
        if result.is_file() and result.stat().st_size:
            event["result_sha256"] = digest_file(result)
        else:
            event["result_sha256"] = None
        if completed.returncode != 0 or not event["result_sha256"]:
            raise ControlError(f"{role} koşusu başarısız veya boş sonuç üretti (çıkış: {completed.returncode}).")
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
    acquire_operation(m["run_id"], "dispatch")
    held = True
    try:
        if args.role == "coordinator" and args.run:
            release_operation(m["run_id"]); held = False
            event = run_dispatch(args.role, output, Path(args.prompt_file), args.run)
            m = assert_manifest(path); acquire_operation(m["run_id"], "dispatch-result"); held = True
        else:
            event = run_dispatch(args.role, output, Path(args.prompt_file), args.run)
        event["caller_role"] = args.caller_role; event["max_concurrent_workers"] = policy["max_coordinator_workers"]
        m["dispatches"].append(event); m["revision"] += 1; invalidate_checks(m); save_manifest(path, m)
    finally:
        if held: release_operation(m["run_id"])
    print(json.dumps(event, ensure_ascii=False))
    return 0


def verify_artifacts(m: dict[str, Any], output: Path, reasons: list[str]) -> bool:
    ok = True
    for name, artifact in m.get("artifacts", {}).items():
        path = output / artifact.get("relative_path", "")
        if not path.is_file() or digest_file(path) != artifact.get("sha256") or path.stat().st_size != artifact.get("size_bytes"):
            reasons.append(f"Artefakt değişmiş/eksik: {name}"); ok = False
        elif name in {"workbook", "report_pdf"}:
            try:
                (validate_xlsx if name == "workbook" else validate_pdf)(path)
            except (ValueError, OSError) as exc:
                reasons.append(f"Çıktı yapısı doğrulanamadı: {name}: {exc}"); ok = False
    return ok


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
    reviewer = r.get("reviewer", {}) if isinstance(r.get("reviewer"), dict) else {}
    independent = (reviewer.get("role") == "reviewer" and reviewer.get("model") == "gpt-5.6-sol" and
                   reviewer.get("reasoning_effort") == "high" and reviewer.get("task_id") and
                   reviewer.get("task_id") != a.get("task_id") and r.get("all_critical_evidence_reviewed") is True and
                   r.get("all_competitors_reviewed") is True and r.get("all_exclusion_reasons_reviewed") is True)
    reviewer_receipt = any(d.get("role") == "reviewer" and d.get("mode") == "run" and d.get("returncode") == 0 and
                           d.get("model") == "gpt-5.6-sol" and d.get("reasoning_effort") == "high" and
                           d.get("dispatch_id") == reviewer.get("task_id") and d.get("result_sha256") == review.get("sha256")
                           for d in m.get("dispatches", []) if isinstance(d, dict))
    coordinator_receipt = any(d.get("role") == "coordinator" and d.get("mode") == "run" and d.get("returncode") == 0 and
                              d.get("model") == "gpt-5.6-sol" and d.get("reasoning_effort") == "high" and
                              d.get("dispatch_id") == a.get("task_id") and d.get("result_sha256") == analysis.get("sha256")
                              for d in m.get("dispatches", []) if isinstance(d, dict))
    if not reviewer_receipt: reasons.append("Reviewer için doğrulanmış başarılı CLI dispatch makbuzu yok.")
    if not coordinator_receipt: reasons.append("Analiz için doğrulanmış başarılı coordinator CLI dispatch makbuzu yok.")
    independent = independent and reviewer_receipt and coordinator_receipt
    if set(critical_ids or []) != observed_critical: critical_ok = False
    checked_ids = r.get("checked_fact_ids")
    if not isinstance(checked_ids, list) or set(checked_ids) != observed_critical:
        critical_ok = False
    for fact in facts if isinstance(facts, list) else []:
        if fact.get("critical") and fact.get("evidence_status") != "verified":
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
    attestations = r.get("control_attestations", {})
    semantic_controls = ("numeric_reconciliation", "fair_comparison", "freshness_validity", "cost_completeness",
                         "formula_recalculation", "parameter_change_test", "output_consistency", "visual_review")
    for control in semantic_controls:
        item = attestations.get(control) if isinstance(attestations, dict) else None
        valid = (isinstance(item, dict) and item.get("status") in {"PASS", "NA"} and
                 isinstance(item.get("evidence"), list) and bool(item["evidence"]) and
                 item.get("reviewed_by") == reviewer.get("task_id") and
                 (item.get("status") != "NA" or isinstance(item.get("reason"), str) and bool(item["reason"].strip())))
        # This is an attestation presence/identity check, never a semantic re-performance.
        semantic[control] = {"status": item["status"] if valid else "FAIL", "reason": item.get("reason") if valid else None}
        if not valid: reasons.append(f"Denetçi tasdiki eksik/geçersiz: {control}")
    return facts_ok and critical_ok, critical_ok, independent and isinstance(competitors, list) and isinstance(exclusions, list), semantic


def cmd_verify(args: argparse.Namespace) -> int:
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path); output = path.parent
    acquire_operation(m["run_id"], "verify")
    try:
        reasons: list[str] = []
        current_inventory = inventory(Path(m["source_inventory"]["root"]))
        sources_ok = current_inventory["dataset_sha256"] == m["source_inventory"].get("dataset_sha256") and current_inventory["entries"] == m["source_inventory"].get("entries")
        skills_ok = skill_snapshot()["combined_sha256"] == m["skill_snapshot"].get("combined_sha256") and skill_snapshot()["version"] == m["skill_snapshot"].get("version")
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
            m["controls"][cid] = {"status": status, "evidence": reasons if status == "FAIL" else ["verify"], "reason": supplied.get("reason") if supplied else None}
        m["revision"] += 1; save_manifest(path, m)
    finally: release_operation(m["run_id"])
    print(json.dumps(m["final_gate"], ensure_ascii=False)); return 0 if m["final_gate"]["status"] == "FINAL_ALLOWED" else 2


def cmd_close(args: argparse.Namespace) -> int:
    if not args.abort and cmd_verify(args) != 0:
        raise ControlError("Kapatma öncesi tazelik/teslim kontrolü geçmedi.")
    path = manifest_path(Path(args.output_dir)); m = assert_manifest(path)
    acquire_operation(m["run_id"], "close")
    try:
        if not args.abort and m.get("final_gate", {}).get("status") != "FINAL_ALLOWED":
            raise ControlError("FINAL kapısı açık değil; kapatmak için açık --abort gerekir.")
        release_analysis_lock(m["run_id"])
    finally:
        # The durable marker is gone, but this per-operation mutex belongs to this command.
        release_operation(m["run_id"])
    return 0


def cmd_inventory(args: argparse.Namespace) -> int:
    print(json.dumps(inventory(Path(args.source_dir)), ensure_ascii=False, indent=2)); return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Teklif değerlendirme bounded runtime/control gate")
    sub = p.add_subparsers(required=True)
    q = sub.add_parser("inventory"); q.add_argument("--source-dir", required=True); q.set_defaults(func=cmd_inventory)
    q = sub.add_parser("prepare"); q.add_argument("--source-dir", required=True); q.add_argument("--output-dir", required=True); q.set_defaults(func=cmd_prepare)
    q = sub.add_parser("record-artifact"); q.add_argument("--output-dir", required=True); q.add_argument("--name", choices=(*REQUIRED_ARTIFACTS, "report_pdf"), required=True); q.add_argument("--artifact", required=True); q.set_defaults(func=cmd_record_artifact)
    q = sub.add_parser("dispatch"); q.add_argument("--output-dir", required=True); q.add_argument("--caller-role", required=True); q.add_argument("--role", required=True, choices=sorted(load_policy()["roles"])); q.add_argument("--prompt-file", required=True); q.add_argument("--critical", action="store_true", help="Yalnız critical_adjudicator için açık koşul beyanı."); q.add_argument("--run", action="store_true", help="Varsayılan dry-run; yalnız bu bayrak Codex çalıştırır."); q.set_defaults(func=cmd_dispatch)
    q = sub.add_parser("verify"); q.add_argument("--output-dir", required=True); q.set_defaults(func=cmd_verify)
    q = sub.add_parser("close"); q.add_argument("--output-dir", required=True); q.add_argument("--abort", action="store_true", help="FINAL açık değilse koşuyu açıkça iptal eder."); q.set_defaults(func=cmd_close)
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
