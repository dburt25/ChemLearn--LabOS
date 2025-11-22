"""Phase 2 import wizard helper utilities.

This module keeps the registration stub for the import wizard while providing
lightweight helpers for schema inference, dataset reference creation, and basic
provenance logging. The logic is intentionally in-memory and deterministic so
it can be used in educational settings without touching real files.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, MutableMapping, Sequence

from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef
from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "import.wizard"
MODULE_VERSION = "0.3.0"
DESCRIPTION = "Data import wizard utilities for small in-memory tables."


def infer_schema(df_or_records: object) -> dict:
    """Infer a lightweight column schema from a dataframe or records.

    The inference is deliberately shallow: it inspects available columns and a
    small sample of values to classify them into coarse types (integer, float,
    boolean, datetime, string, array, object, unknown).
    """

    def _infer_value_type(value: object) -> str:
        if value is None:
            return "unknown"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "integer"
        if isinstance(value, float):
            return "float"
        if isinstance(value, (datetime,)):
            return "datetime"
        if isinstance(value, (list, tuple, set)):
            return "array"
        if isinstance(value, Mapping):
            return "object"
        return "string"

    def _merge_types(types: Iterable[str]) -> str:
        unique = {t for t in types if t != "unknown"}
        if not unique:
            return "unknown"
        if len(unique) == 1:
            return unique.pop()
        if unique == {"integer", "float"}:
            return "float"
        return "mixed"

    def _from_dataframe(df: object) -> tuple[list[dict], int]:
        try:
            import pandas as pd  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise ValueError("pandas is required for dataframe schema inference") from exc
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Provided object is not a pandas.DataFrame")
        fields: list[dict] = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            if dtype.startswith("int"):
                inferred = "integer"
            elif dtype.startswith("float"):
                inferred = "float"
            elif dtype.startswith("bool"):
                inferred = "boolean"
            elif "datetime" in dtype:
                inferred = "datetime"
            else:
                inferred = "string"
            fields.append(
                {
                    "name": str(col),
                    "type": inferred,
                    "example": None if df[col].empty else df[col].iloc[0],
                }
            )
        return fields, len(df)

    def _from_records(records: Sequence[Mapping[str, object]]) -> tuple[list[dict], int]:
        if not records:
            return [], 0
        keys: set[str] = set().union(*records)
        fields: list[dict] = []
        for key in sorted(keys):
            sample_values = [row.get(key) for row in records][:50]
            value_types = [_infer_value_type(v) for v in sample_values]
            merged = _merge_types(value_types)
            example = next((v for v in sample_values if v is not None), None)
            fields.append({"name": key, "type": merged, "example": example})
        return fields, len(records)

    # Dispatch based on input type
    try:
        import pandas as pd  # type: ignore
    except Exception:  # pragma: no cover - pandas optional
        pd = None  # type: ignore

    if pd is not None and isinstance(df_or_records, pd.DataFrame):
        fields, rows = _from_dataframe(df_or_records)
    elif isinstance(df_or_records, Mapping):
        fields, rows = _from_records([df_or_records])
    elif isinstance(df_or_records, Sequence) and not isinstance(
        df_or_records, (str, bytes, bytearray)
    ):
        records_seq: list[Mapping[str, object]] = []
        for item in df_or_records:
            if isinstance(item, Mapping):
                records_seq.append(item)
        if not records_seq:
            raise ValueError("Sequences must contain mapping objects for schema inference")
        fields, rows = _from_records(records_seq)
    else:
        raise ValueError("Unsupported data type for schema inference")

    return {"fields": fields, "row_count": rows}


def create_dataset_ref_from_import(
    data: object,
    source: str | None = None,
    label: str | None = None,
    actor: str | None = None,
    source_type: str = "inline",
    logical_path: str | None = None,
) -> DatasetRef:
    """Create a DatasetRef based on imported data and inferred schema."""

    schema = infer_schema(data)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dataset_id = f"DS-IMPORT-{timestamp}"
    display_label = label or "Imported dataset"
    path_hint = logical_path or f"import/{source_type}/{dataset_id}.json"
    metadata = {
        "module_key": MODULE_KEY,
        "source": source or "labos://inline",
        "source_type": source_type,
        "imported_by": actor or "unknown",
        "schema": schema,
    }
    return DatasetRef(
        id=dataset_id,
        label=display_label,
        kind="table",
        path_hint=path_hint,
        metadata=metadata,
    )


def build_import_summary(
    data: object,
    source: str | None = None,
    actor: str | None = None,
    source_type: str = "inline",
    notes: MutableMapping[str, object] | None = None,
) -> dict[str, object]:
    """Create a structured summary containing dataset and audit metadata."""

    dataset_ref = create_dataset_ref_from_import(
        data=data,
        source=source,
        actor=actor,
        source_type=source_type,
    )
    schema = dataset_ref.metadata.get("schema", {})
    audit_event = AuditEvent(
        id=f"AUD-IMPORT-{dataset_ref.id}",
        actor=actor or "unknown",
        action="import",
        target=dataset_ref.id,
        details={
            "module_key": MODULE_KEY,
            "source": source or "labos://inline",
            "source_type": source_type,
            "schema": schema,
            "row_count": schema.get("row_count"),
            "notes": dict(notes or {}),
        },
    )
    preview_rows = []
    if isinstance(data, Mapping):
        preview_rows.append(data)
    elif isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
        for item in data[:5]:  # type: ignore[index]
            if isinstance(item, Mapping):
                preview_rows.append(item)

    summary = {
        "module_key": MODULE_KEY,
        "dataset": dataset_ref.to_dict(),
        "audit_events": [audit_event.to_dict()],
        "preview": preview_rows,
        "status": "imported",
        "schema": schema,
    }
    return summary


def run_import_stub(params: Mapping[str, object]) -> dict[str, object]:
    """Module operation entrypoint compatible with the module registry."""

    data = params.get("data")
    source = params.get("source") or params.get("path")
    actor = params.get("actor") or "labos.stub"
    source_type = params.get("source_type") or "inline"
    notes_param = params.get("notes")
    notes = notes_param if isinstance(notes_param, Mapping) else {}
    try:
        summary = build_import_summary(
            data=data,
            source=str(source) if source is not None else None,
            actor=str(actor) if actor is not None else None,
            source_type=str(source_type),
            notes=dict(notes),
        )
    except Exception as exc:
        return {
            "module_key": MODULE_KEY,
            "status": "failed",
            "message": str(exc),
            "inputs": dict(params),
        }

    summary["inputs"] = dict(params)
    return summary


def _register() -> None:
    descriptor = ModuleDescriptor(
        module_id=MODULE_KEY,
        version=MODULE_VERSION,
        description=DESCRIPTION,
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Infer schema and return dataset/audit metadata for imports.",
            handler=run_import_stub,
        )
    )
    register_descriptor(descriptor)


_register()
