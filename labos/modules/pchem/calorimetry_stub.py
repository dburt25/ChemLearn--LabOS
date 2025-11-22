"""Phase 1 physical chemistry calorimetry placeholder."""

from __future__ import annotations

from uuid import uuid4
from typing import Any, Mapping

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_ID = "pchem.calorimetry.stub"
MODULE_VERSION = "0.1.0"
DESCRIPTION = "P-Chem calorimetry calculator placeholder (returns metadata only)."


def compute_stub(inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(inputs or {})
    audit_event = AuditEvent(
        id=f"AUD-PCHEM-{uuid4().hex[:8]}",
        actor=str(payload.get("actor", "labos.stub")),
        action="simulate-calorimetry",
        target=str(payload.get("sample_id", payload.get("experiment_id", "unknown"))),
        details={
            "phase": "stub",
            "notes": "Calorimetry calculator placeholder",
            "inputs": payload,
        },
    )
    dataset_ref = DatasetRef(
        id=f"DS-PCHEM-{uuid4().hex[:6]}",
        label="Calorimetry placeholder dataset",
        kind="timeseries",
        path_hint="data/stubs/pchem_calorimetry.csv",
        metadata={
            "generator": MODULE_ID,
            "units": "kJ/mol (placeholder)",
        },
    )
    return {
        "status": "not-implemented",
        "module_id": MODULE_ID,
        "message": "P-Chem calorimetry placeholder (Phase 1).",
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
            description="Calorimetry stub that records audit + dataset metadata only.",
            handler=compute_stub,
        )
    )
    register_descriptor(descriptor)


_register()
