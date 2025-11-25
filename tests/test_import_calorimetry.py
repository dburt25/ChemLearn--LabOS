"""Tests for calorimetry import helpers."""

from __future__ import annotations

import pytest

from labos.modules.imports.calorimetry import import_calorimetry_table


def test_import_calorimetry_table_resolves_synonym_columns() -> None:
    rows = [
        {"mass": 10.5, "cp": 4.18, "t_initial": 298.0, "t_final": 305.0, "Sample": "X1", "note": "start"},
        {"mass": 10.5, "cp": 4.18, "t_initial": 298.0, "t_final": 306.0, "Sample": "X1", "note": "mid"},
    ]

    result = import_calorimetry_table(rows)

    assert result["module_key"] == "import.calorimetry"
    assert result["column_mapping"]["mass"] == "mass_g"
    assert result["column_mapping"]["cp"] == "specific_heat_j_per_gk"
    assert result["column_mapping"]["t_initial"] == "t_initial_k"
    assert result["column_mapping"]["t_final"] == "t_final_k"
    assert result["column_mapping"]["note"] == "notes"
    assert result["unmatched_columns"] == []

    record = result["records"][0]
    assert set(record.keys()) >= {"mass_g", "specific_heat_j_per_gk", "t_initial_k", "t_final_k", "sample_id", "notes"}


def test_import_calorimetry_table_missing_required_columns_raises() -> None:
    with pytest.raises(ValueError, match="Required calorimetry columns not found"):
        import_calorimetry_table([{"Sample": "X2", "note": "test"}])


def test_import_calorimetry_table_invalid_float_values() -> None:
    rows = [{"mass": "not-a-number", "cp": 4.18, "t_initial": 298.0, "t_final": 305.0}]

    with pytest.raises(ValueError, match="expects a float"):
        import_calorimetry_table(rows)
