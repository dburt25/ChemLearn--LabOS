"""Unit tests for P-Chem calorimetry and thermodynamics helpers."""

from __future__ import annotations

import math

import pytest

from labos.modules.pchem.calorimetry_stub import (
    run_calorimetry_stub,
    run_delta_g_from_k,
    run_ideal_gas,
    run_rate_law_simple,
)


def test_calorimetry_stub_propagates_inputs() -> None:
    payload = run_calorimetry_stub({"delta_t": 5.0, "heat_capacity": 3.14, "sample_id": "DEMO"})

    assert payload["status"] == "not-implemented"
    dataset = payload["dataset"]
    assert dataset["metadata"]["delta_t_c"] == 5.0
    assert dataset["metadata"]["heat_capacity"] == 3.14
    assert dataset["id"].endswith("DEMO")
    assert payload["inputs"]["sample_id"] == "DEMO"


def test_ideal_gas_solves_for_pressure_with_unit_conversions() -> None:
    result = run_ideal_gas(
        {
            "volume": 2.0,
            "amount_mol": 1.5,
            "temperature": 25.0,
            "temperature_unit": "C",
            "volume_unit": "L",
        }
    )

    assert result["status"] == "ok"
    assert result["solved_for"] == "pressure"
    pressure = result["values"]["pressure_si"]["value"]
    expected_pressure = (1.5 * 8.314462618 * (25 + 273.15)) / 0.002
    assert math.isclose(pressure, expected_pressure, rel_tol=1e-6)


def test_ideal_gas_requires_exactly_one_unknown() -> None:
    result = run_ideal_gas({"pressure": 101_325, "volume": 1.0})

    assert result["status"] == "error"
    assert "exactly three" in result["message"]


def test_delta_g_from_k_round_trip() -> None:
    result = run_delta_g_from_k({"equilibrium_constant": 10.0, "temperature": 310.0, "temperature_unit": "K"})

    assert result["status"] == "ok"
    delta_g = result["values"]["delta_g_j_per_mol"]
    expected = -8.314462618 * 310.0 * math.log(10.0)
    assert math.isclose(delta_g, expected, rel_tol=1e-6)

    back_calc = run_delta_g_from_k(
        {
            "delta_g_j_per_mol": delta_g,
            "temperature": 310.0,
            "temperature_unit": "K",
        }
    )
    assert back_calc["status"] == "ok"
    assert math.isclose(back_calc["values"]["equilibrium_constant"], 10.0, rel_tol=1e-6)


def test_delta_g_from_k_rejects_non_positive_k() -> None:
    result = run_delta_g_from_k({"equilibrium_constant": 0})

    assert result["status"] == "error"
    assert "must be positive" in result["message"]


def test_rate_law_simple_first_order_half_life() -> None:
    result = run_rate_law_simple({"initial_concentration": 0.5, "rate_constant": 0.2, "time": 10.0, "order": "first"})

    assert result["status"] == "ok"
    values = result["values"]
    expected_conc = 0.5 * math.exp(-0.2 * 10.0)
    assert math.isclose(values["concentration"], expected_conc, rel_tol=1e-6)
    assert math.isclose(values["half_life"], math.log(2.0) / 0.2, rel_tol=1e-6)


def test_rate_law_simple_invalid_order() -> None:
    result = run_rate_law_simple({"initial_concentration": 1.0, "rate_constant": 0.1, "time": 5.0, "order": "second"})

    assert result["status"] == "error"
    assert "Order must" in result["message"]
