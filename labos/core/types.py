"""Shared enums and dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Mapping
from uuid import uuid4

from .utils import utc_now


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DatasetType(str, Enum):
    REFERENCE = "reference"
    EXPERIMENTAL = "experimental"
    TRAINING = "training"
    INFERENCE = "inference"


@dataclass(slots=True)
class BaseRecord:
    record_id: str
    created_at: str
    updated_at: str

    @classmethod
    def new_id(cls) -> str:
        return str(uuid4())

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MetadataRecord(BaseRecord):
    metadata: Mapping[str, Any]
