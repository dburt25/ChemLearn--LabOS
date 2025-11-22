"""Phase 2 EI-MS fragmentation educational stub (deterministic metadata only)."""

from __future__ import annotations

from typing import Any, Mapping

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "eims.fragmentation"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "ChemLearn EI-MS fragmentation stub that emits dataset/audit placeholders only."


def run_eims_stub(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Return deterministic EI-MS metadata for educational demos (no real spectra)."""

    payload = dict(params or {})
    precursor_mz = float(payload.get("precursor_mz", 250.0))
    collision_energy = float(payload.get("collision_energy", 70.0))
    actor = str(payload.get("actor", "labos.stub"))
    experiment_id = str(payload.get("experiment_id", "EXP-STUB"))

    dataset = {
        "id": f"DS-EIMS-{int(round(precursor_mz))}",
        "label": "EI-MS fragment spectrum (stub)",
        "kind": "spectrum",
        "path_hint": "data/stubs/eims_fragments.json",
        "metadata": {
            "module_key": MODULE_KEY,
            "precursor_mz": precursor_mz,
            "collision_energy": collision_energy,
            "stub": True,
        },
    }

    audit = {
        "id": f"AUD-EIMS-{experiment_id}",
        "actor": actor,
        "action": "simulate-fragmentation",
        "target": experiment_id,
        "details": {
            "phase": "educational-stub",
            "notes": "No real EI-MS physics; deterministic metadata only.",
            "inputs": payload,
            "limitations": "Educational and development only. Not validated for clinical use.",
        },
    }

    return {
        "module_key": MODULE_KEY,
        "dataset": dataset,
        "audit": audit,
        "status": "not-implemented",
        "message": "EI-MS fragmentation placeholder output for demos only.",
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
            description="Return EI-MS fragment metadata without running chemistry.",
            handler=run_eims_stub,
        )
    )
    register_descriptor(descriptor)


_register()
