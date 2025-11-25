"""Phase 2 calorimetry educational stub emitting deterministic metadata only."""

from __future__ import annotations

import math
from typing import Any, Mapping
from uuid import uuid4

from labos.modules import ModuleDescriptor, ModuleOperation, register_descriptor

MODULE_KEY = "pchem.calorimetry"
MODULE_VERSION = "0.2.0"
DESCRIPTION = "P-Chem calorimetry stub producing dataset/audit placeholders (no thermodynamics)."

R_IDEAL_GAS = 8.314462618  # J/(mol*K)


def run_calorimetry_stub(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Return deterministic calorimetry metadata for educational walkthroughs."""

    payload = dict(params or {})
    delta_t = float(payload.get("delta_t", 3.5))
    heat_capacity = float(payload.get("heat_capacity", 4.18))
    actor = str(payload.get("actor", "labos.stub"))
    sample_id = str(payload.get("sample_id", "SAMPLE-STUB"))

    sample_tag = sample_id.replace(" ", "-") or "SAMPLE-STUB"
    run_token = uuid4().hex[:8].upper()

    dataset_id = str(payload.get("dataset_id") or f"DS-PCHEM-{sample_tag}-{run_token}")

    dataset = {
        "id": dataset_id,
        "label": "Calorimetry trace (stub)",
        "kind": "timeseries",
        "path_hint": "data/stubs/pchem_calorimetry.csv",
        "metadata": {
            "module_key": MODULE_KEY,
            "delta_t_c": delta_t,
            "heat_capacity": heat_capacity,
            "stub": True,
            "sample_id": sample_id,
        },
    }

    audit = {
        "id": str(payload.get("audit_id") or f"AUD-PCHEM-{sample_tag}-{run_token}"),
        "actor": actor,
        "action": "simulate-calorimetry",
        "target": sample_id,
        "details": {
            "phase": "educational-stub",
            "notes": "No thermodynamics performed; metadata only.",
            "inputs": payload,
            "limitations": "Educational and development only. Not validated for clinical use.",
            "dataset_id": dataset_id,
        },
    }

    return {
        "module_key": MODULE_KEY,
        "dataset": dataset,
        "audit": audit,
        "status": "not-implemented",
        "message": "Calorimetry placeholder output for demos only.",
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
            description="Return calorimetry metadata without running physics.",
            handler=run_calorimetry_stub,
        )
    )
    register_descriptor(descriptor)


def _method_metadata(name: str, description: str, units: Mapping[str, str], limitations: list[str]) -> dict[str, object]:
    return {
        "name": name,
        "description": description,
        "units": dict(units),
        "limitations": list(limitations),
    }


def _pressure_to_pa(value: float, unit: str) -> float:
    match unit.lower():
        case "pa":
            return value
        case "kpa":
            return value * 1_000.0
        case "atm":
            return value * 101_325.0
        case _:
            raise ValueError(f"Unsupported pressure unit: {unit}")


def _pressure_from_pa(value_pa: float, unit: str) -> float:
    match unit.lower():
        case "pa":
            return value_pa
        case "kpa":
            return value_pa / 1_000.0
        case "atm":
            return value_pa / 101_325.0
        case _:
            raise ValueError(f"Unsupported pressure unit: {unit}")


def _volume_to_m3(value: float, unit: str) -> float:
    match unit.lower():
        case "m3" | "m^3":
            return value
        case "l" | "liter" | "liters":
            return value * 0.001
        case _:
            raise ValueError(f"Unsupported volume unit: {unit}")


def _volume_from_m3(value_m3: float, unit: str) -> float:
    match unit.lower():
        case "m3" | "m^3":
            return value_m3
        case "l" | "liter" | "liters":
            return value_m3 / 0.001
        case _:
            raise ValueError(f"Unsupported volume unit: {unit}")


def _temp_to_kelvin(value: float, unit: str) -> float:
    match unit.lower():
        case "k":
            return value
        case "c" | "celsius":
            return value + 273.15
        case _:
            raise ValueError(f"Unsupported temperature unit: {unit}")


def _temp_from_kelvin(value_k: float, unit: str) -> float:
    match unit.lower():
        case "k":
            return value_k
        case "c" | "celsius":
            return value_k - 273.15
        case _:
            raise ValueError(f"Unsupported temperature unit: {unit}")


def run_ideal_gas(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Solve the ideal gas law (PV = nRT) for one missing variable."""

    payload = dict(params or {})

    pressure = payload.get("pressure")
    volume = payload.get("volume")
    amount = payload.get("amount_mol")
    temperature = payload.get("temperature")

    pressure_unit = str(payload.get("pressure_unit", "Pa"))
    volume_unit = str(payload.get("volume_unit", "m3"))
    temperature_unit = str(payload.get("temperature_unit", "K"))

    present = {name: value for name, value in {
        "pressure": pressure,
        "volume": volume,
        "amount": amount,
        "temperature": temperature,
    }.items() if value is not None}

    missing = [name for name in ("pressure", "volume", "amount", "temperature") if name not in present]
    if len(missing) != 1:
        return {
            "module_key": "pchem.ideal_gas",
            "status": "error",
            "message": "Provide exactly three of pressure, volume, amount_mol, temperature.",
            "inputs": payload,
            "method": _method_metadata(
                "Ideal gas law",
                "Solves PV = nRT when exactly one variable is unknown.",
                {"pressure": "Pa|kPa|atm", "volume": "m^3|L", "temperature": "K|C", "amount": "mol"},
                ["Ideal gas assumption", "Requires exactly one unknown"],
            ),
        }

    try:
        pressure_pa = _pressure_to_pa(float(pressure), pressure_unit) if pressure is not None else None
        volume_m3 = _volume_to_m3(float(volume), volume_unit) if volume is not None else None
        temperature_k = _temp_to_kelvin(float(temperature), temperature_unit) if temperature is not None else None
        amount_mol = float(amount) if amount is not None else None
    except (TypeError, ValueError) as exc:
        return {
            "module_key": "pchem.ideal_gas",
            "status": "error",
            "message": f"Invalid input: {exc}",
            "inputs": payload,
            "method": _method_metadata(
                "Ideal gas law",
                "Solves PV = nRT when exactly one variable is unknown.",
                {"pressure": "Pa|kPa|atm", "volume": "m^3|L", "temperature": "K|C", "amount": "mol"},
                ["Ideal gas assumption", "Requires exactly one unknown"],
            ),
        }

    solved_for = missing[0]
    if solved_for == "pressure":
        pressure_pa = (amount_mol * R_IDEAL_GAS * temperature_k) / volume_m3  # type: ignore[arg-type]
    elif solved_for == "volume":
        volume_m3 = (amount_mol * R_IDEAL_GAS * temperature_k) / pressure_pa  # type: ignore[arg-type]
    elif solved_for == "amount":
        amount_mol = (pressure_pa * volume_m3) / (R_IDEAL_GAS * temperature_k)  # type: ignore[arg-type]
    elif solved_for == "temperature":
        temperature_k = (pressure_pa * volume_m3) / (amount_mol * R_IDEAL_GAS)  # type: ignore[arg-type]

    method = _method_metadata(
        "Ideal gas law",
        "Solves PV = nRT with lightweight unit conversion (Pa/kPa/atm, m^3/L, K/C).",
        {"pressure": pressure_unit, "volume": volume_unit, "temperature": temperature_unit, "amount": "mol"},
        ["Ideal gas assumption", "Single unknown only", "No non-ideal corrections"],
    )

    return {
        "module_key": "pchem.ideal_gas",
        "status": "ok",
        "message": f"Solved for {solved_for} using PV=nRT.",
        "inputs": payload,
        "solved_for": solved_for,
        "values": {
            "pressure": {"value": _pressure_from_pa(pressure_pa, pressure_unit), "unit": pressure_unit},
            "pressure_si": {"value": pressure_pa, "unit": "Pa"},
            "volume": {"value": _volume_from_m3(volume_m3, volume_unit), "unit": volume_unit},
            "volume_si": {"value": volume_m3, "unit": "m^3"},
            "amount_mol": amount_mol,
            "temperature": {"value": _temp_from_kelvin(temperature_k, temperature_unit), "unit": temperature_unit},
            "temperature_si": {"value": temperature_k, "unit": "K"},
        },
        "method": method,
    }


def run_delta_g_from_k(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Relate standard Gibbs free energy and equilibrium constant."""

    payload = dict(params or {})
    temperature_unit = str(payload.get("temperature_unit", "K"))

    equilibrium_constant = payload.get("equilibrium_constant")
    delta_g = payload.get("delta_g_j_per_mol")
    temperature = payload.get("temperature", 298.15)

    try:
        temperature_k = _temp_to_kelvin(float(temperature), temperature_unit)
        eq_constant = float(equilibrium_constant) if equilibrium_constant is not None else None
        delta_g_value = float(delta_g) if delta_g is not None else None
    except (TypeError, ValueError) as exc:
        return {
            "module_key": "pchem.delta_g_from_k",
            "status": "error",
            "message": f"Invalid input: {exc}",
            "inputs": payload,
            "method": _method_metadata(
                "ΔG° and K",
                "Relates ΔG° and equilibrium constant with ΔG° = -RT ln K.",
                {"temperature": temperature_unit, "delta_g": "J/mol"},
                ["Assumes standard state", "K must be positive"],
            ),
        }

    method = _method_metadata(
        "ΔG° and equilibrium constant",
        "Computes ΔG° from K or vice versa with ΔG° = -RT ln K.",
        {"temperature": temperature_unit, "delta_g": "J/mol", "equilibrium_constant": "dimensionless"},
        ["Assumes standard state", "K>0 when provided", "No activity corrections"],
    )

    if eq_constant is None and delta_g_value is None:
        return {
            "module_key": "pchem.delta_g_from_k",
            "status": "error",
            "message": "Provide either equilibrium_constant or delta_g_j_per_mol.",
            "inputs": payload,
            "method": method,
        }

    if eq_constant is not None and eq_constant <= 0:
        return {
            "module_key": "pchem.delta_g_from_k",
            "status": "error",
            "message": "Equilibrium constant must be positive.",
            "inputs": payload,
            "method": method,
        }

    if eq_constant is None:
        eq_constant = math.exp(-delta_g_value / (R_IDEAL_GAS * temperature_k))
    if delta_g_value is None:
        delta_g_value = -R_IDEAL_GAS * temperature_k * math.log(eq_constant)

    return {
        "module_key": "pchem.delta_g_from_k",
        "status": "ok",
        "message": "Related ΔG° and equilibrium constant via ΔG° = -RT ln K.",
        "inputs": payload,
        "values": {
            "equilibrium_constant": eq_constant,
            "delta_g_j_per_mol": delta_g_value,
            "temperature": {"value": _temp_from_kelvin(temperature_k, temperature_unit), "unit": temperature_unit},
            "temperature_si": {"value": temperature_k, "unit": "K"},
        },
        "method": method,
    }


def run_rate_law_simple(params: dict[str, Any] | None = None) -> dict[str, object]:
    """Evaluate zero- or first-order integrated rate laws."""

    payload = dict(params or {})
    order = str(payload.get("order", "first")).lower()

    try:
        initial_concentration = float(payload.get("initial_concentration"))
        rate_constant = float(payload.get("rate_constant"))
        time = float(payload.get("time"))
    except (TypeError, ValueError) as exc:
        return {
            "module_key": "pchem.rate_law_simple",
            "status": "error",
            "message": f"Invalid input: {exc}",
            "inputs": payload,
            "method": _method_metadata(
                "Integrated rate law",
                "Computes concentration vs. time for zero- or first-order kinetics.",
                {"concentration": "mol/L", "rate_constant": "varies", "time": "s"},
                ["Single-species decay", "Deterministic only"],
            ),
        }

    method = _method_metadata(
        "Integrated rate law",
        "Zero- and first-order concentration projection using analytical forms.",
        {"concentration": "mol/L", "rate_constant": "1/s or mol/(L*s)", "time": "s"},
        ["Single-species decay", "No temperature dependence", "Ideal kinetics only"],
    )

    if order not in {"zero", "first"}:
        return {
            "module_key": "pchem.rate_law_simple",
            "status": "error",
            "message": "Order must be 'zero' or 'first'.",
            "inputs": payload,
            "method": method,
        }

    if initial_concentration < 0 or rate_constant < 0 or time < 0:
        return {
            "module_key": "pchem.rate_law_simple",
            "status": "error",
            "message": "initial_concentration, rate_constant, and time must be non-negative.",
            "inputs": payload,
            "method": method,
        }

    if order == "zero":
        concentration = max(initial_concentration - rate_constant * time, 0.0)
    else:
        concentration = initial_concentration * math.exp(-rate_constant * time)

    half_life = None
    if order == "first" and rate_constant > 0:
        half_life = math.log(2.0) / rate_constant
    elif order == "zero" and rate_constant > 0:
        half_life = initial_concentration / (2.0 * rate_constant)

    return {
        "module_key": "pchem.rate_law_simple",
        "status": "ok",
        "message": f"Computed {order}-order concentration vs. time.",
        "inputs": payload,
        "values": {
            "order": order,
            "concentration": concentration,
            "initial_concentration": initial_concentration,
            "rate_constant": rate_constant,
            "time": time,
            "half_life": half_life,
        },
        "method": method,
    }


def _register_ideal_gas() -> None:
    descriptor = ModuleDescriptor(
        module_id="pchem.ideal_gas",
        version="0.1.0",
        description="Ideal gas law solver with lightweight unit conversions.",
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Solve PV = nRT with one unknown (Pa/kPa/atm, m^3/L, K/C).",
            handler=run_ideal_gas,
        )
    )
    register_descriptor(descriptor)


def _register_delta_g_from_k() -> None:
    descriptor = ModuleDescriptor(
        module_id="pchem.delta_g_from_k",
        version="0.1.0",
        description="Relates ΔG° and equilibrium constants via ΔG° = -RT ln K.",
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Compute ΔG° from K or infer K from ΔG° at a specified temperature.",
            handler=run_delta_g_from_k,
        )
    )
    register_descriptor(descriptor)


def _register_rate_law_simple() -> None:
    descriptor = ModuleDescriptor(
        module_id="pchem.rate_law_simple",
        version="0.1.0",
        description="Zero- and first-order integrated rate law evaluator.",
    )
    descriptor.register_operation(
        ModuleOperation(
            name="compute",
            description="Project concentration vs. time for zero or first order kinetics.",
            handler=run_rate_law_simple,
        )
    )
    register_descriptor(descriptor)


_register()
_register_ideal_gas()
_register_delta_g_from_k()
_register_rate_law_simple()
