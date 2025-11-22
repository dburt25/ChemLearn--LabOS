"""Dataset registry implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence

from .audit import AuditLogger
from .config import LabOSConfig
from .core.errors import ValidationError
from .core.types import BaseRecord, DatasetType
from .core.utils import utc_now
from .storage import JSONFileStore


@dataclass(slots=True)
class Dataset(BaseRecord):
    owner: str
    dataset_type: DatasetType
    uri: str
    tags: Sequence[str]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        owner: str,
        dataset_type: DatasetType,
        uri: str,
        tags: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "Dataset":
        now = utc_now()
        return cls(
            record_id=BaseRecord.new_id(),
            created_at=now,
            updated_at=now,
            owner=owner,
            dataset_type=dataset_type,
            uri=uri,
            tags=tuple(tags or ()),
            metadata=dict(metadata or {}),
        )


class DatasetRegistry:
    """File-backed dataset registry that emits audit events."""

    def __init__(self, config: LabOSConfig, audit: AuditLogger) -> None:
        self.store = JSONFileStore(config.datasets_dir)
        self.audit = audit

    def add(self, dataset: Dataset) -> Dataset:
        if not dataset.owner:
            raise ValidationError("Dataset owner is required")
        self.store.save(dataset.record_id, dataset.to_dict())
        event = self.audit.record(
            event_type="dataset.created",
            actor="labos.core",
            payload={"dataset_id": dataset.record_id, "owner": dataset.owner},
        )
        dataset.attach_audit_event(event)
        return dataset

    def get(self, dataset_id: str) -> Dataset:
        data = self.store.load(dataset_id)
        return Dataset(**data)

    def list_ids(self) -> Iterable[str]:
        return self.store.list_ids()
