"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


def default_audit_log_path() -> str:
    """Always resolve to <repo>/outputs/… (safe when cwd is src/)."""
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / "outputs" / "audit_log.json")


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, float] = {}
        self._pending: dict[str, dict] = {}
        self._counter = 0

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """Store input + start timestamp keyed by request_id/user_id."""
        self._counter += 1
        request_id = request_id or f"{user_id}-{self._counter}"
        self._open[request_id] = time.monotonic()
        self._pending[request_id] = {
            "user_id": user_id,
            "input": text,
            "input_at": utc_now_iso(),
        }
        return request_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ):
        """Store output, layer decision, latency; append to self.logs."""
        start = self._open.pop(request_id, None) if request_id else None
        latency_ms = (time.monotonic() - start) * 1000 if start is not None else None
        pending = self._pending.pop(request_id, {}) if request_id else {}

        entry = {
            "request_id": request_id,
            "user_id": user_id,
            "input": pending.get("input"),
            "output": text,
            "blocked": blocked,
            "layer": layer,
            "latency_ms": latency_ms,
            "input_at": pending.get("input_at"),
            "output_at": utc_now_iso(),
        }
        self.logs.append(entry)
        return entry

    def export_json(self, filepath: str | None = None):
        """Write logs to disk (JSON array) under repo-root ``outputs/`` by default."""
        path = Path(filepath or default_audit_log_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
