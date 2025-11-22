"""Phase 1 EI-MS fragmentation placeholder."""

from __future__ import annotations

from uuid import uuid4
from typing import Any, Mapping

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_ID = "eims.fragmentation.stub"
MODULE_VERSION = "0.1.0"
DESCRIPTION = "ChemLearn EI-MS fragmentation engine placeholder (no real chemistry)."


def compute_stub(inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic payload describing the placeholder run."""
    payload = dict(inputs or {})
    audit_event = AuditEvent(
        id=f"AUD-EIMS-{uuid4().hex[:8]}",
        actor=str(payload.get("actor", "labos.stub")),
        action="simulate-fragmentation",
        target=str(payload.get("experiment_id", "unknown")),
        details={
            "phase": "stub",
            "reason": "EI-MS placeholder run",
            "inputs": payload,
        },
    )
    dataset_ref = DatasetRef(
        id=f"DS-EIMS-{uuid4().hex[:6]}",
        label="EI-MS preliminary fragments bundle",
        kind="spectrum",
        path_hint="data/stubs/eims_fragments.json",
        metadata={
            "generator": MODULE_ID,
            "source": "Phase 1 placeholder",
        },
    )
    return {
        "status": "not-implemented",
        "module_id": MODULE_ID,
        "message": "EI-MS fragmentation engine placeholder (no chemistry yet).",
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
            description="Generate EI-MS placeholder audit + dataset references.",
            handler=compute_stub,
        )
    )
    register_descriptor(descriptor)


_register()
