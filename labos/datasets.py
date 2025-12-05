"""Dataset registry implementation."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Iterable, Mapping, Optional, Sequence

from .audit import AuditLogger
from .config import LabOSConfig
from .core.errors import ValidationError
from .core.types import BaseRecord, DatasetType
from .core.utils import utc_now
from .storage import JSONFileStore


@dataclass(slots=True)
class Dataset(BaseRecord):
    owner: str = "unknown"
    dataset_type: DatasetType = DatasetType.EXPERIMENTAL
    uri: str = ""
    tags: Sequence[str] = field(default_factory=tuple)
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], fallback_id: Optional[str] = None) -> "Dataset":
        data: dict[str, Any] = dict(payload)

        record_id = data.get("record_id") or data.get("id") or fallback_id or BaseRecord.new_id()
        data["record_id"] = record_id

        created_at = data.get("created_at") or data.get("createdAt")
        if not created_at:
            created_at = utc_now()
        data["created_at"] = created_at

        updated_at = data.get("updated_at") or data.get("updatedAt") or created_at
        data["updated_at"] = updated_at

        data["audit_trail"] = list(data.get("audit_trail") or [])
        data.setdefault("last_audit_event_id", data.get("last_audit_event_id"))
        data.setdefault("signature", data.get("signature"))

        owner = data.get("owner") or data.get("user_id") or "unknown"
        data["owner"] = owner

        dataset_type = data.get("dataset_type") or data.get("kind")
        if isinstance(dataset_type, str):
            try:
                data["dataset_type"] = DatasetType(dataset_type)
            except ValueError:
                try:
                    data["dataset_type"] = DatasetType(dataset_type.lower())
                except ValueError:
                    data["dataset_type"] = DatasetType.EXPERIMENTAL
        elif not isinstance(dataset_type, DatasetType):
            data["dataset_type"] = DatasetType.EXPERIMENTAL

        uri = data.get("uri") or data.get("path") or data.get("path_hint") or ""
        data["uri"] = uri

        tags = data.get("tags")
        if isinstance(tags, Sequence) and not isinstance(tags, (str, bytes)):
            data["tags"] = tuple(tags)
        else:
            data["tags"] = tuple()

        metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}
        metadata = dict(metadata)
        label = data.get("label")
        if label and "label" not in metadata:
            metadata["label"] = label
        kind_hint = data.get("kind")
        if kind_hint and "kind" not in metadata:
            metadata["kind"] = kind_hint
        path_hint = data.get("path_hint")
        if path_hint and "path_hint" not in metadata:
            metadata["path_hint"] = path_hint
        data["metadata"] = metadata

        allowed_fields = {field.name for field in fields(cls)}
        cleaned = {key: value for key, value in data.items() if key in allowed_fields}
        return cls(**cleaned)


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
        return Dataset.from_dict(data, fallback_id=dataset_id)

    def list_ids(self) -> Iterable[str]:
        return self.store.list_ids()
