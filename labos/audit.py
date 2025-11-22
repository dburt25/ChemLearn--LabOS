"""Append-only audit log writer with chained checksums."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .config import LabOSConfig
from .core.errors import AuditError
from .core.utils import utc_now


@dataclass(slots=True)
class AuditEvent:
    event_id: str
    timestamp: str
    actor: str
    event_type: str
    payload: Dict[str, Any]
    prev_checksum: str
    checksum: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditLogger:
    """Writes audit events as JSON lines grouped per UTC day."""

    def __init__(self, config: LabOSConfig) -> None:
        self.config = config
        self.config.audit_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, timestamp: str) -> Path:
        day = timestamp.split("T", 1)[0]
        return self.config.audit_dir / f"{day}.jsonl"

    def _last_checksum(self, path: Path) -> str:
        if not path.exists():
            return "0" * 64
        try:
            with path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                if size == 0:
                    return "0" * 64
                # Seek backwards up to 4096 bytes to capture the final line.
                handle.seek(max(size - 4096, 0))
                tail = handle.read().decode("utf-8")
        except OSError as exc:  # pragma: no cover - disk failure scenario
            raise AuditError(f"Unable to read audit log {path}: {exc}") from exc
        lines = [line for line in tail.splitlines() if line.strip()]
        if not lines:
            return "0" * 64
        try:
            last_record = json.loads(lines[-1])
            return last_record.get("checksum", "0" * 64)
        except json.JSONDecodeError as exc:  # pragma: no cover - corruption scenario
            raise AuditError(f"Audit log {path} is corrupted: {exc}") from exc

    def record(self, event_type: str, actor: str, payload: Dict[str, Any]) -> AuditEvent:
        timestamp = utc_now()
        log_path = self._log_path(timestamp)
        prev_checksum = self._last_checksum(log_path)
        event_dict: Dict[str, Any] = {
            "event_id": hashlib.sha256(f"{timestamp}{event_type}{actor}".encode("utf-8")).hexdigest(),
            "timestamp": timestamp,
            "actor": actor,
            "event_type": event_type,
            "payload": payload,
            "prev_checksum": prev_checksum,
        }
        checksum = hashlib.sha256(
            (prev_checksum + json.dumps(event_dict, sort_keys=True)).encode("utf-8")
        ).hexdigest()
        event = AuditEvent(checksum=checksum, **event_dict)
        try:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event.to_dict(), sort_keys=True))
                handle.write("\n")
        except OSError as exc:  # pragma: no cover - disk failure scenario
            raise AuditError(f"Unable to append audit event: {exc}") from exc
        return event

    def verify(self, day: Optional[str] = None) -> bool:
        """Verify the checksum chain for a log file. Returns True when valid."""

        path = self._log_path(day or utc_now())
        if not path.exists():
            return True
        prev = "0" * 64
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                expected = hashlib.sha256(
                    (prev + json.dumps({k: record[k] for k in record if k != "checksum"}, sort_keys=True)).encode(
                        "utf-8"
                    )
                ).hexdigest()
                if expected != record.get("checksum"):
                    return False
                prev = record["checksum"]
        except json.JSONDecodeError as exc:  # pragma: no cover - corruption scenario
            raise AuditError(f"Audit log {path} is corrupted: {exc}") from exc
        return True
