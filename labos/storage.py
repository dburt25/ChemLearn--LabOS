"""Simple JSON storage primitives used by registry classes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from .core.errors import NotFoundError, RegistryError


class JSONFileStore:
    """Persist records as individual JSON files under a directory."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _record_path(self, record_id: str) -> Path:
        return self.base_dir / f"{record_id}.json"

    def save(self, record_id: str, payload: Dict[str, Any]) -> None:
        try:
            self._record_path(record_id).write_text(
                json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
            )
        except OSError as exc:  # pragma: no cover - disk failure scenario
            raise RegistryError(f"Failed to persist record {record_id}: {exc}") from exc

    def load(self, record_id: str) -> Dict[str, Any]:
        path = self._record_path(record_id)
        if not path.exists():
            raise NotFoundError(f"Record {record_id} missing under {self.base_dir}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_ids(self) -> Iterable[str]:
        for file in sorted(self.base_dir.glob("*.json")):
            yield file.stem
