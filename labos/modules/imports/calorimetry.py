"""Calorimetry data import helpers for the P-Chem module.

This module is an educational stub: it keeps all logic in-memory and assumes
small, clean inputs. The intent is to illustrate provenance wiring rather than
provide a production ETL. It normalizes user-provided column names, validates
lightweight schemas, and emits DatasetRef + AuditEvent records that match the
core LabOS provenance model.

The canonical schema focuses on bulk calorimetry runs (mass, heat capacity,
and temperature changes). Time-series traces can be layered on later, but the
schema below captures the minimal energetic inputs needed to compute heat
transfer in a consistent set of units.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping, Sequence

from labos.core import storage
from labos.core.audit import AuditEvent
from labos.core.datasets import DatasetRef

CALORIMETRY_SCHEMA: list[dict[str, object]] = [
    {
        "name": "sample_id",
        "type": "string",
        "required": False,
        "description": "Identifier for the sample or experiment",
    },
    {
        "name": "mass_g",
        "type": "float",
        "required": False,
        "description": "Sample mass in grams",
    },
    {
        "name": "specific_heat_j_per_gk",
        "type": "float",
        "required": False,
        "description": "Specific heat capacity in J/(g*K)",
    },
    {
        "name": "t_initial_k",
        "type": "float",
        "required": False,
        "description": "Initial temperature in Kelvin",
    },
    {
        "name": "t_final_k",
        "type": "float",
        "required": False,
        "description": "Final temperature in Kelvin",
    },
    {
        "name": "calorimeter_constant_j_per_k",
        "type": "float",
        "required": False,
        "description": "Calorimeter heat capacity term in J/K (optional)",
    },
    {
        "name": "solvent_volume_ml",
        "type": "float",
        "required": False,
        "description": "Solvent or solution volume in milliliters (optional)",
    },
    {
        "name": "notes",
        "type": "string",
        "required": False,
        "description": "Freeform notes about the run or calculation context",
    },
    {
        "name": "time_s",
        "type": "float",
        "required": False,
        "description": "Timestamp for the sample or event in seconds",
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
        "required": True,
        "description": "Heat flow reading (typically mW) from the instrument",
    },
    {
        "name": "event_label",
        "type": "string",
        "required": False,
        "description": "Label or annotation describing the event",
    },
]


_SCHEMA_LOOKUP: dict[str, dict[str, object]] = {field["name"]: field for field in CALORIMETRY_SCHEMA}


# Normalization helpers: compare keys case-insensitively and ignore whitespace/underscores
# so that "Mass (g)", "mass_g", and "MASS" all map to the canonical "mass_g" column.
def _normalize_key(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


_SYNONYMS: dict[str, list[str]] = {
    "sample_id": ["sample", "sampleid", "sample name", "id", "identifier"],
    "mass_g": ["mass", "mass(g)", "mass_in_g", "sample_mass", "weight_g"],
    "specific_heat_j_per_gk": [
        "specific_heat",
        "specificheat",
        "cp",
        "heat_capacity",
        "specific_heat_capacity",
    ],
    "t_initial_k": ["t_initial", "initial_temperature", "ti", "start_temp", "t0"],
    "t_final_k": ["t_final", "final_temperature", "tf", "end_temp", "t1"],
    "calorimeter_constant_j_per_k": [
        "calorimeter_constant",
        "instrument_constant",
        "cal_constant",
        "heat_capacity_constant",
    ],
    "solvent_volume_ml": ["volume_ml", "solution_volume", "solvent_volume", "vol_ml"],
    "notes": ["note", "comment", "remarks"],
    "time_s": [
        "time",
        "times",
        "time_s",
        "time_sec",
        "time_seconds",
        "seconds",
        "time(s)",
    ],
    "temperature_c": [
        "temperature",
        "temp",
        "temp_c",
        "temp c",
        "temp_deg_c",
        "temperature_c",
        "temperature(c)",
    ],
    "heat_flow_mw": [
        "heatflow",
        "heat_flow",
        "heat flow",
        "heatflow_mw",
        "heat_flow_mw",
        "qdot",
        "power_mw",
    ],
    "event_label": ["event", "label", "event_label", "annotation", "note", "notes"],
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
    missing = [
        name
        for name, details in _SCHEMA_LOOKUP.items()
        if details.get("required") and (name not in record or record[name] is None)
    ]
    if missing:
        raise ValueError(
            "Missing required calorimetry columns: " + ", ".join(sorted(missing))
        )


def _validate_required_headers(resolution: ColumnResolution) -> None:
    mapped = set(resolution.mapping.values())
    missing_headers = [
        name
        for name, details in _SCHEMA_LOOKUP.items()
        if details.get("required") and name not in mapped
    ]
    if missing_headers:
        raise ValueError(
            "Required calorimetry columns not found in input headers: "
            + ", ".join(sorted(missing_headers))
        )


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

    for idx, record in enumerate(records):
        resolved, extras = _apply_mapping(record, resolution.mapping, drop_unknown)
        try:
            if coerce_types:
                _coerce_record_types(resolved)
            _validate_required_fields(resolved)
        except ValueError as exc:
            raise ValueError(f"Row {idx}: {exc}") from exc
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
            kind="tabular",
            path_hint=f"imports/calorimetry/{timestamp}.json",
            metadata={
                "module_key": MODULE_KEY,
                "schema": canonical_calorimetry_schema(),
                "source": source or "labos://inline",
                "row_count": len(normalized_records),
                "unmatched_columns": resolution.unmatched,
                "column_mapping": dict(resolution.mapping),
            },
        )
        storage.save_dataset_record(dataset_ref, content=normalized_records)

        audit_event = AuditEvent(
            id=f"AUD-CAL-{timestamp}",
            actor="labos.importer",
            action="import",
            target=dataset_ref.id,
            details={
                "module_key": MODULE_KEY,
                "source": source or "labos://inline",
                "label": dataset_ref.label,
                "row_count": len(normalized_records),
                "column_mapping": dict(resolution.mapping),
                "unmatched_columns": resolution.unmatched,
            },
        )
        result["dataset"] = dataset_ref.to_dict()
        result["audit"] = audit_event.to_dict()
        result["audit_events"] = [audit_event.to_dict()]

    return result
