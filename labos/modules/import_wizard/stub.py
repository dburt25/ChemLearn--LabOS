"""Phase 1 Data Import Wizard placeholder."""

from __future__ import annotations

from uuid import uuid4
from typing import Any, Mapping

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_ID = "import.wizard.stub"
MODULE_VERSION = "0.1.0"
DESCRIPTION = "Data import wizard placeholder for structured dataset ingestion."


def compute_stub(inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(inputs or {})
    audit_event = AuditEvent(
        id=f"AUD-IM-{uuid4().hex[:8]}",
        actor=str(payload.get("actor", "labos.stub")),
        action="simulate-import",
        target=str(payload.get("source", "unknown")),
        details={
            "phase": "stub",
            "notes": "Import wizard placeholder run",
            "inputs": payload,
        },
    )
    dataset_ref = DatasetRef(
        id=f"DS-IM-{uuid4().hex[:6]}",
        label="Imported dataset stub",
        kind="table",
        path_hint="data/stubs/import_wizard_output.parquet",
        metadata={
            "generator": MODULE_ID,
            "source_type": payload.get("source_type", "unspecified"),
        },
    )
    return {
        "status": "not-implemented",
        "module_id": MODULE_ID,
        "message": "Data Import Wizard placeholder (Phase 1).",
        "audit_event": audit_event.to_dict(),
        "dataset": dataset_ref.to_dict(),
        "inputs": payload,
    }


def _register() -> None:
    descriptor = ModuleDescriptor(
        module_id=MODULE_ID,
        version=MODULE_VERSION,
        description=DESCRIPTION,
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Data import wizard stub producing audit + dataset references.",
            handler=compute_stub,
        )
    )
    register_descriptor(descriptor)


_register()
