"""Calorimetry data import helpers for the P-Chem module.

This module keeps the logic in-memory and focuses on small tables passed in as
lists of mappings or pandas DataFrames. It normalizes user-provided column
names, validates a lightweight schema, and optionally emits DatasetRef
metadata for downstream pipeline wiring.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping, Sequence

from labos.core.datasets import DatasetRef

CALORIMETRY_SCHEMA: list[dict[str, object]] = [
    {
        "name": "time_s",
        "type": "float",
        "required": True,
        "description": "Elapsed time in seconds for the calorimetry trace",
    },
    {
        "name": "temperature_c",
        "type": "float",
        "required": True,
        "description": "Measured temperature in degrees Celsius",
    },
    {
        "name": "heat_flow_mw",
        "type": "float",
        "required": False,
        "description": "Heat flow signal in milliwatts (optional)",
    },
    {
        "name": "sample_id",
        "type": "string",
        "required": False,
        "description": "Identifier for the sample or experiment",
    },
    {
        "name": "run_id",
        "type": "string",
        "required": False,
        "description": "Run or injection identifier when multiple traces are present",
    },
    {
        "name": "event_label",
        "type": "string",
        "required": False,
        "description": "Optional annotation for phase changes or dosing events",
    },
]


_SCHEMA_LOOKUP: dict[str, dict[str, object]] = {field["name"]: field for field in CALORIMETRY_SCHEMA}


# Normalization helpers: we compare keys case-insensitively and ignore whitespace/underscores
# so that "Time (s)", "time_s", and "TIME" all map to the canonical "time_s" column.
def _normalize_key(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


_SYNONYMS: dict[str, list[str]] = {
    "time_s": ["time", "t", "elapsed_time", "seconds", "time_seconds"],
    "temperature_c": ["temp", "temperature", "temp_c", "temperature_c", "t_deg_c"],
    "heat_flow_mw": ["heat_flow", "heatflow", "power_mw", "heat_flow_mw", "heatflowmw"],
    "sample_id": ["sample", "sampleid", "sample name", "id"],
    "run_id": ["run", "runid", "injection", "experiment"],
    "event_label": ["event", "note", "annotation", "step"],
}


@dataclass(frozen=True)
class ColumnResolution:
    """Result of resolving user columns to canonical names."""

    mapping: dict[str, str]
    unmatched: list[str]


def canonical_calorimetry_schema() -> list[dict[str, object]]:
    """Return a copy of the canonical calorimetry schema."""

    return [dict(field) for field in CALORIMETRY_SCHEMA]


def resolve_calorimetry_columns(
    user_columns: Iterable[str],
    explicit_mapping: Mapping[str, str] | None = None,
) -> ColumnResolution:
    """Resolve user-facing column names to canonical calorimetry columns.

    explicit_mapping: optional mapping from user column -> canonical column.
    Any canonical columns not present in the user input remain unresolved and
    will be validated later when rows are processed.
    """

    explicit_mapping = explicit_mapping or {}
    resolution: dict[str, str] = {}
    unmatched: list[str] = []

    normalized_to_canonical: dict[str, str] = {}
    for canonical, synonyms in _SYNONYMS.items():
        normalized_to_canonical[_normalize_key(canonical)] = canonical
        for synonym in synonyms:
            normalized_to_canonical[_normalize_key(synonym)] = canonical

    for raw_col in user_columns:
        if raw_col in explicit_mapping:
            resolution[raw_col] = explicit_mapping[raw_col]
            continue

        normalized = _normalize_key(raw_col)
        canonical = normalized_to_canonical.get(normalized)
        if canonical:
            resolution[raw_col] = canonical
        else:
            unmatched.append(raw_col)

    return ColumnResolution(mapping=resolution, unmatched=unmatched)


def _coerce_float(value: object, column: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"Column '{column}' expects a float but received a boolean")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Column '{column}' expects a float; unable to convert '{value}'") from exc


def _coerce_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _apply_mapping(
    record: Mapping[str, object],
    mapping: Mapping[str, str],
    drop_unknown: bool,
) -> tuple[dict[str, object], dict[str, object]]:
    resolved: dict[str, object] = {}
    extras: dict[str, object] = {}
    for key, value in record.items():
        canonical = mapping.get(key)
        if canonical:
            resolved[canonical] = value
        elif not drop_unknown:
            extras[key] = value
    return resolved, extras


def _prepare_records(table_like: object) -> list[Mapping[str, object]]:
    try:
        import pandas as pd  # type: ignore
    except Exception:  # pragma: no cover - pandas optional
        pd = None  # type: ignore

    if pd is not None and isinstance(table_like, pd.DataFrame):
        return table_like.to_dict(orient="records")

    if isinstance(table_like, Mapping):
        return [table_like]

    if isinstance(table_like, Sequence) and not isinstance(table_like, (str, bytes, bytearray)):
        rows: list[Mapping[str, object]] = []
        for item in table_like:
            if not isinstance(item, Mapping):
                raise ValueError("Sequences passed to import_calorimetry_table must contain mappings")
            rows.append(item)
        return rows

    raise ValueError("Unsupported table_like type; expected DataFrame, mapping, or sequence of mappings")


def _validate_required_fields(record: Mapping[str, object]) -> None:
    missing = [name for name, details in _SCHEMA_LOOKUP.items() if details.get("required") and name not in record]
    if missing:
        raise ValueError(f"Missing required calorimetry columns: {', '.join(sorted(missing))}")


def _coerce_record_types(record: MutableMapping[str, object]) -> None:
    for key, details in _SCHEMA_LOOKUP.items():
        if key not in record:
            continue
        expected_type = details.get("type")
        if expected_type == "float":
            record[key] = _coerce_float(record[key], key)
        elif expected_type == "string":
            record[key] = _coerce_string(record[key])


MODULE_KEY = "import.calorimetry"


def import_calorimetry_table(
    table_like: object,
    column_mapping: Mapping[str, str] | None = None,
    drop_unknown: bool = False,
    coerce_types: bool = True,
    include_dataset_ref: bool = True,
    source: str | None = None,
    label: str | None = None,
) -> dict[str, object]:
    """Normalize a calorimetry table into canonical columns with light validation.

    Args:
        table_like: pandas.DataFrame, mapping, or sequence of mappings.
        column_mapping: optional explicit mapping from user column -> canonical column.
        drop_unknown: if True, ignores unmapped columns instead of collecting them under
            the "extras" key.
        coerce_types: if True, performs float/string coercions based on the canonical schema.
        include_dataset_ref: if True, attaches a DatasetRef with import metadata.
        source: logical source string for provenance (e.g., filename or URL).
        label: label to attach to the DatasetRef.

    Returns:
        dict containing normalized records, schema, column mapping, unmatched columns,
        and optionally a DatasetRef-compatible dictionary.
    """

    records = _prepare_records(table_like)
    resolution = resolve_calorimetry_columns(records[0].keys() if records else [], column_mapping)

    normalized_records: list[dict[str, object]] = []
    extras_blocks: list[dict[str, object]] = []

    for record in records:
        resolved, extras = _apply_mapping(record, resolution.mapping, drop_unknown)
        _validate_required_fields(resolved)
        if coerce_types:
            _coerce_record_types(resolved)
        normalized_records.append(resolved)
        if extras:
            extras_blocks.append(extras)

    result: dict[str, object] = {
        "module_key": MODULE_KEY,
        "schema": canonical_calorimetry_schema(),
        "records": normalized_records,
        "column_mapping": dict(resolution.mapping),
        "unmatched_columns": resolution.unmatched,
    }
    if extras_blocks:
        result["extras"] = extras_blocks

    if include_dataset_ref:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        dataset_ref = DatasetRef(
            id=f"DS-CAL-{timestamp}",
            label=label or "Calorimetry import",
            kind="timeseries",
            path_hint=f"imports/calorimetry/{timestamp}.json",
            metadata={
                "module_key": MODULE_KEY,
                "schema": canonical_calorimetry_schema(),
                "source": source or "labos://inline",
                "row_count": len(normalized_records),
                "unmatched_columns": resolution.unmatched,
            },
        )
        result["dataset"] = dataset_ref.to_dict()

    return result
