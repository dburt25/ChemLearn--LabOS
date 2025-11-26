from __future__ import annotations

import math

import pytest

from labos.modules.pchem.calorimetry_stub import run_calorimetry_stub, run_ideal_gas
from labos.modules.ei_ms.basic_analysis import run_ei_ms_analysis
from labos.ui.control_panel import _validate_text_fields


def test_calorimetry_stub_rejects_nan_delta_t() -> None:
    with pytest.raises(ValueError):
        run_calorimetry_stub({"delta_t": math.nan, "heat_capacity": 4.18, "sample_id": "S-1"})


def test_ideal_gas_rejects_non_positive_volume() -> None:
    with pytest.raises(ValueError):
        run_ideal_gas({"pressure": 101_325, "volume": 0, "amount_mol": 1.0, "temperature": 298.15})


def test_ei_ms_analysis_requires_fragments() -> None:
    with pytest.raises(ValueError):
        run_ei_ms_analysis({"precursor_mass": 100.0, "fragment_masses": []})


def test_ei_ms_analysis_accepts_structured_spectrum() -> None:
    result = run_ei_ms_analysis(
        {
            "precursor_mass": 120.0,
            "spectrum": [{"mz": 60.0, "intensity": 25.0}, {"m/z": 30.0, "intensity": 10.0}],
        }
    )

    assert result["status"] == "ok"
    assert any(frag["mass"] == 60.0 for frag in result["fragments"])


def test_validate_text_fields_flags_missing_entries() -> None:
    assert _validate_text_fields({"Sample": ""}) is not None
    assert _validate_text_fields({"Sample": "S-1"}) is None
