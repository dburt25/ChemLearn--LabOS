"""Tests for calorimetry import helpers."""

from __future__ import annotations

import pytest

from labos.core import storage
from labos.modules.imports.calorimetry import import_calorimetry_table


def test_import_calorimetry_table_resolves_synonym_columns() -> None:
    rows = [
        {"Time (s)": 0, "Temp C": 25.5, "heatflow": 1.2, "Sample": "X1", "note": "start"},
        {"Time (s)": 10, "Temp C": 26.0, "heatflow": 1.0, "Sample": "X1", "note": "mid"},
    ]

    result = import_calorimetry_table(rows)

    assert result["module_key"] == "import.calorimetry"
    assert result["column_mapping"]["Time (s)"] == "time_s"
    assert result["column_mapping"]["Temp C"] == "temperature_c"
    assert result["column_mapping"]["heatflow"] == "heat_flow_mw"
    assert result["column_mapping"]["note"] == "event_label"
    assert result["unmatched_columns"] == []

    record = result["records"][0]
    assert set(record.keys()) >= {"time_s", "temperature_c", "heat_flow_mw", "sample_id", "event_label"}


def test_import_calorimetry_table_missing_required_columns_raises() -> None:
    with pytest.raises(ValueError, match="Missing required calorimetry columns"):
        import_calorimetry_table([{"Temp": 25.0, "Sample": "X2"}], column_mapping={"Temp": "temperature_c"})


def test_import_calorimetry_table_invalid_float_values() -> None:
    rows = [{"time": "not-a-number", "temperature": 22.0}]

    with pytest.raises(ValueError, match="expects a float"):
        import_calorimetry_table(rows)


def test_import_calorimetry_table_emits_dataset_and_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LABOS_USE_STORE", "1")
    monkeypatch.setattr(storage, "_ACTIVE_STORES", None)

    rows = [{"time": 0, "temperature_c": 25.0, "heat_flow_mw": 1.5}]

    result = import_calorimetry_table(rows, source="labos://unit-test", label="Cal run")

    dataset = result["dataset"]
    assert dataset["id"].startswith("DS-CAL-")
    stores = storage.get_active_stores()
    assert stores is not None
    assert dataset["id"] in stores.datasets.list_datasets()

    audit = result["audit"]
    assert audit["details"]["module_key"] == "import.calorimetry"
    assert audit["target"] == dataset["id"]
