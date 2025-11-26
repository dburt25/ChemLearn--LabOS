"""Simple JSON storage primitives used by registry classes.

Storage layout
==============
- Each record is stored as an individual ``<id>.json`` file beneath a
  caller-specified base directory.
- Callers are expected to treat the base directory as a flat namespace;
  subdirectories are not traversed.

File format
===========
- Files contain a single JSON object.
- ``save`` writes prettified JSON and uses a temporary file + replace to
  avoid partially written records when the process is interrupted.

Error handling expectations
===========================
- Missing directories are created automatically.
- Missing files raise ``NotFoundError`` when explicitly loaded.
- Bulk iteration helpers skip malformed or partial files with a logged
  warning so callers can tolerate corrupted state while continuing to load
  valid records.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, TypeVar

from .core.errors import NotFoundError, RegistryError


logger = logging.getLogger(__name__)
T = TypeVar("T")


class JSONFileStore:
    """Persist records as individual JSON files under a directory."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, record_id: str) -> Path:
        return self.base_dir / f"{record_id}.json"

    def save(self, record_id: str, payload: Dict[str, Any]) -> None:
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            destination = self._record_path(record_id)
            tmp_path = destination.with_suffix(destination.suffix + ".tmp")
            tmp_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
            tmp_path.replace(destination)
        except OSError as exc:  # pragma: no cover - disk failure scenario
            raise RegistryError(f"Failed to persist record {record_id}: {exc}") from exc

    def load(self, record_id: str) -> Dict[str, Any]:
        path = self._record_path(record_id)
        if not path.exists():
            raise NotFoundError(f"Record {record_id} missing under {self.base_dir}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RegistryError(f"Record {record_id} is corrupted: {exc}") from exc

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self.base_dir.glob("*.json")):
            yield file.stem

    def load_all(self, loader: Callable[[Dict[str, Any]], T | None] | None = None) -> List[T | Dict[str, Any]]:
        """Load all JSON payloads in the base directory.

        A ``loader`` callable may be provided to validate/convert each raw
        mapping. When supplied, any record that raises an exception or returns
        ``None`` is skipped after emitting a warning.
        """

        records: List[T | Dict[str, Any]] = []
        for file in sorted(self.base_dir.glob("*.json")):
            try:
                payload: Dict[str, Any] = json.loads(file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                logger.warning("Skipping corrupted record %s: %s", file, exc)
                continue

            if loader is None:
                records.append(payload)
                continue

            try:
                processed = loader(payload)
            except Exception as exc:  # pragma: no cover - validation guardrail
                logger.warning("Skipping record %s due to loader error: %s", file, exc)
                continue
            if processed is None:
                logger.warning("Skipping record %s due to validation failure", file)
                continue
            records.append(processed)
        return records
