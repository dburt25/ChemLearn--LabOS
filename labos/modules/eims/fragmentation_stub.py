"""Phase 2 EI-MS fragmentation educational stub (deterministic metadata only).

LEGACY shim; prefer ``ei_ms.basic_analysis``.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor
from labos.modules.ei_ms.basic_analysis import run_basic_analysis

MODULE_KEY = "eims.fragmentation"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "ChemLearn EI-MS fragmentation stub that emits dataset/audit placeholders only."


def run_eims_stub(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Return deterministic EI-MS metadata for educational demos (no real spectra).

    This wrapper forwards spectrum analysis to ``ei_ms.basic_analysis`` while
    retaining the legacy dataset/audit envelope expected by older tests and
    integrations.
    """

    payload = dict(params or {})
    precursor_mz = float(payload.get("precursor_mz", 250.0))
    collision_energy = float(payload.get("collision_energy", 70.0))
    actor = str(payload.get("actor", "labos.stub"))
    experiment_id = str(payload.get("experiment_id", "EXP-STUB"))
    run_token = uuid4().hex[:8].upper()

    fragment_masses = payload.get("fragment_masses")
    if not fragment_masses:
        # Provide deterministic fallback peaks so the stub succeeds with minimal inputs.
        fragment_masses = [max(precursor_mz - delta, 5.0) for delta in (15.0, 28.0, 43.0)]
        payload["fragment_masses"] = fragment_masses

    if "fragment_intensities" not in payload:
        payload["fragment_intensities"] = [100.0, 65.0, 40.0][: len(fragment_masses)]

    analysis = run_basic_analysis(
        {
            "precursor_mass": precursor_mz,
            "fragment_masses": payload.get("fragment_masses"),
            "fragment_intensities": payload.get("fragment_intensities"),
            "annotations": payload.get("annotations"),
        }
    ).to_dict()

    dataset = {
        "id": f"DS-EIMS-{int(round(precursor_mz))}-{run_token}",
        "label": "EI-MS fragment spectrum (stub)",
        "kind": "spectrum",
        "path_hint": "data/stubs/eims_fragments.json",
        "metadata": {
            "module_key": MODULE_KEY,
            "precursor_mz": precursor_mz,
            "collision_energy": collision_energy,
            "stub": True,
            "analysis_summary": analysis["summary"],
        },
    }

    audit = {
        "id": f"AUD-EIMS-{experiment_id}-{run_token}",
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
        "status": analysis.get("status", "not-implemented"),
        "message": "EI-MS fragmentation placeholder output for demos only.",
        "inputs": payload,
        "analysis": analysis,
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
