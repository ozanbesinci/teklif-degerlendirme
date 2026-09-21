"""Small deterministic runtime helpers. No source text is copied into telemetry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import queue
import subprocess
import threading
import time


def output_text(value):
    if isinstance(value, list):
        return "\n".join(output_text(v) for v in value)
    if isinstance(value, dict):
        return output_text(value.get("text", value.get("output", "")))
    if isinstance(value, str):
        try:
            nested = json.loads(value)
        except ValueError:
            return value
        return output_text(nested) if isinstance(nested, (dict, list)) else value
    return ""


def read_native_session(path, limit=None, seal=None):
    path = Path(path)
    with path.open("rb") as stream:
        raw = stream.read() if limit is None else stream.read(limit)
    model = effort = session_id = cwd = None
    usage = None
    matched = None
    for line_number, line in enumerate(raw.splitlines(), 1):
        try:
            event = json.loads(line)
        except ValueError:
            continue  # A still-active log may have an incomplete trailing line.
        payload = event.get("payload", {})
        if event.get("type") == "session_meta":
            session_id, cwd = payload.get("id"), payload.get("cwd")
        if event.get("type") == "turn_context":
            model, effort = payload.get("model"), payload.get("effort")
        if payload.get("type") == "token_count" and payload.get("info"):
            usage = payload["info"].get("total_token_usage")
        if payload.get("type") in {"function_call_output", "custom_tool_call_output"}:
            for text in output_text(payload.get("output")).splitlines():
                if text.startswith("TEKLIF_RESULT_SEAL:"):
                    try:
                        marker = json.loads(text.split(":", 1)[1])
                    except ValueError:
                        continue
                    if seal is not None and marker == seal:
                        matched = (model, effort, event.get("timestamp"), line_number)
    if not all(isinstance(x, str) and x for x in (session_id, cwd, model, effort)):
        raise ValueError("Gerçek oturum kimliği/model/efor/çalışma dizini okunamadı.")
    if seal is not None:
        if not matched:
            raise ValueError("Bu artefaktı kabul eden gerçek araç sonucu oturumda yok; önce seal-result çalıştırın.")
        model, effort, seal_at, seal_line = matched
    return {"session_id": session_id, "cwd": cwd, "model": model, "reasoning_effort": effort,
            "log_path": str(path.resolve()), "log_bytes": len(raw),
            "log_prefix_sha256": hashlib.sha256(raw).hexdigest(), "usage_snapshot": usage,
            "seal": seal, "seal_at": matched[2] if matched else None, "seal_line": matched[3] if matched else None}


def native_receipt_valid(receipt):
    try:
        if not receipt.get("seal"):
            return False
        observed = read_native_session(receipt["log_path"], receipt["log_bytes"], receipt["seal"])
        return all(observed.get(k) == receipt.get(k) for k in
                   ("session_id", "model", "reasoning_effort", "log_prefix_sha256", "log_bytes", "seal_at", "seal_line"))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def stream_process(command, prompt, cwd, events_path, stderr_path, timeout_seconds=None):
    """Wait inside Python, not repeated model turns. Preserve minimal structured events."""
    started = time.monotonic()
    telemetry = {"status": "RUNNING", "session_id": None, "usage": None, "events": 0}
    event_queue = queue.Queue()
    with open(stderr_path, "w", encoding="utf-8") as errors, open(events_path, "w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=errors, text=True, encoding="utf-8", cwd=cwd,
                                   shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

        def collect():
            try:
                for line in process.stdout:
                    event_queue.put(line)
            finally:
                event_queue.put(None)

        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        try:
            process.stdin.write(prompt)
            process.stdin.close()
            eof = False
            while not eof:
                if timeout_seconds is not None and time.monotonic() - started > timeout_seconds:
                    process.terminate()
                    telemetry["status"] = "TIMED_OUT"
                    break
                try:
                    line = event_queue.get(timeout=0.25)
                except queue.Empty:
                    continue
                if line is None:
                    eof = True
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                safe = {"type": event.get("type")}
                if event.get("type") == "thread.started":
                    telemetry["session_id"] = event.get("thread_id")
                    safe["thread_id"] = telemetry["session_id"]
                if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                    telemetry["usage"] = telemetry["usage"] or {}
                    for name, value in event["usage"].items():
                        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                            telemetry["usage"][name] = telemetry["usage"].get(name, 0) + value
                    safe["usage"] = event["usage"]
                if event.get("type") == "turn.failed":
                    telemetry["status"] = "FAILED"
                if isinstance(event.get("item"), dict):
                    safe["item_type"] = event["item"].get("type")
                    safe["item_status"] = event["item"].get("status")
                log.write(json.dumps(safe, ensure_ascii=False) + "\n")
                log.flush()
                telemetry["events"] += 1
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait(timeout=5)
            telemetry["returncode"] = returncode
            if telemetry["status"] == "RUNNING":
                telemetry["status"] = "COMPLETED" if returncode == 0 else "FAILED"
        except KeyboardInterrupt:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
            telemetry.update(status="FAILED", returncode=130,
                             error="Görev kullanıcı tarafından kesildi; alt süreç sonlandırıldı.")
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=5)
            raise
        finally:
            process.stdout.close()
            reader.join(timeout=1)
            telemetry["duration_seconds"] = round(time.monotonic() - started, 3)
    return telemetry
