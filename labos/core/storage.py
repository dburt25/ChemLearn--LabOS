"""Storage abstractions for LabOS data assets.

Phase 2 focuses on defining the interface and conventions only. Real
backends (databases, object stores, etc.) will arrive in later phases.
"""

from __future__ import annotations

from typing import Dict, List, Protocol, runtime_checkable

from .datasets import DatasetRef


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol describing minimal storage operations.

    Implementations are intentionally lightweight for Phase 2. They
    should focus on interface compatibility rather than persistence
    guarantees.
    """

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:
        """Persist a dataset and return a dataset identifier."""

    def load_dataset(self, dataset_id: str) -> object:
        """Retrieve a dataset by identifier."""

    def list_datasets(self) -> List[str]:
        """Return known dataset identifiers."""


class NullStorageBackend:
    """Placeholder backend that refuses all storage operations."""

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:  # pragma: no cover - placeholder
        raise NotImplementedError("No storage backend configured")

    def load_dataset(self, dataset_id: str) -> object:  # pragma: no cover - placeholder
        raise NotImplementedError("No storage backend configured")

    def list_datasets(self) -> List[str]:  # pragma: no cover - placeholder
        raise NotImplementedError("No storage backend configured")


class InMemoryStorageBackend:
    """Ephemeral, in-memory storage for local experimentation.

    This is suitable for unit tests or notebook exploration where
    durability is not required.
    """

    def __init__(self) -> None:
        self._store: Dict[str, object] = {}

    def save_dataset(self, dataset_ref: DatasetRef, content: object) -> str:
        self._store[dataset_ref.id] = content
        return dataset_ref.id

    def load_dataset(self, dataset_id: str) -> object:
        try:
            return self._store[dataset_id]
        except KeyError as exc:  # pragma: no cover - guardrail
            raise KeyError(f"Dataset '{dataset_id}' not found in memory") from exc

    def list_datasets(self) -> List[str]:
        return list(self._store.keys())
