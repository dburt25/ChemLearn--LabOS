"""Phase 2 calorimetry educational stub emitting deterministic metadata only."""

from __future__ import annotations

from typing import Any, Mapping

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "pchem.calorimetry"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "P-Chem calorimetry stub producing dataset/audit placeholders (no thermodynamics)."


def run_calorimetry_stub(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Return deterministic calorimetry metadata for educational walkthroughs."""

    payload = dict(params or {})
    delta_t = float(payload.get("delta_t", 3.5))
    heat_capacity = float(payload.get("heat_capacity", 4.18))
    actor = str(payload.get("actor", "labos.stub"))
    sample_id = str(payload.get("sample_id", "SAMPLE-STUB"))

    dataset = {
        "id": f"DS-PCHEM-{sample_id}",
        "label": "Calorimetry trace (stub)",
        "kind": "timeseries",
        "path_hint": "data/stubs/pchem_calorimetry.csv",
        "metadata": {
            "module_key": MODULE_KEY,
            "delta_t_c": delta_t,
            "heat_capacity": heat_capacity,
            "stub": True,
        },
    }

    audit = {
        "id": f"AUD-PCHEM-{sample_id}",
        "actor": actor,
        "action": "simulate-calorimetry",
        "target": sample_id,
        "details": {
            "phase": "educational-stub",
            "notes": "No thermodynamics performed; metadata only.",
            "inputs": payload,
            "limitations": "Educational and development only. Not validated for clinical use.",
        },
    }

    return {
        "module_key": MODULE_KEY,
        "dataset": dataset,
        "audit": audit,
        "status": "not-implemented",
        "message": "Calorimetry placeholder output for demos only.",
        "inputs": payload,
    }


def _register() -> None:
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description=DESCRIPTION,
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Return calorimetry metadata without running physics.",
            handler=run_calorimetry_stub,
        )
    )
    register_descriptor(descriptor)


_register()
