"""Phase 2 import wizard educational stub (deterministic metadata only)."""

from __future__ import annotations

from typing import Any, Mapping

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "import.wizard"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "Data import wizard stub emitting dataset/audit placeholders (no ingestion)."


def run_import_stub(data_or_path: str | dict[str, Any] | None = None) -> dict[str, object]:
    """Return deterministic import metadata for educational demos only."""

    if isinstance(data_or_path, str):
        payload = {"source": data_or_path}
    else:
        payload = dict(data_or_path or {})
    source = str(payload.get("source", "labos://stub"))
    actor = str(payload.get("actor", "labos.stub"))
    source_type = str(payload.get("source_type", "csv"))

    dataset = {
        "id": f"DS-IMPORT-{source_type.upper()}",
        "label": "Imported dataset (stub)",
        "kind": "table",
        "path_hint": f"data/stubs/{source_type}_import.parquet",
        "metadata": {
            "module_key": MODULE_KEY,
            "source": source,
            "source_type": source_type,
            "stub": True,
        },
    }

    audit = {
        "id": f"AUD-IMPORT-{source_type.upper()}",
        "actor": actor,
        "action": "simulate-import",
        "target": source,
        "details": {
            "phase": "educational-stub",
            "notes": "No real ingestion performed; metadata only.",
            "inputs": payload,
            "limitations": "Educational and development only. Not validated for clinical use.",
        },
    }

    return {
        "module_key": MODULE_KEY,
        "dataset": dataset,
        "audit": audit,
        "status": "not-implemented",
        "message": "Import wizard placeholder output for demos only.",
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
            description="Return import metadata without touching files.",
            handler=run_import_stub,
        )
    )
    register_descriptor(descriptor)


_register()
