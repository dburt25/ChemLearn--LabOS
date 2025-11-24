# Physical chemistry utilities

This module extends the PChem toolkit beyond calorimetry with deterministic, unit-aware helpers.

## Available operations

### `pchem.ideal_gas`
- **Function**: `run_ideal_gas(params: dict) -> dict`
- **Purpose**: Solve one missing variable in the ideal gas law (PV = nRT).
- **Units**: Supports pressure (Pa, kPa, atm), volume (m³ or L), temperature (K or °C), and amount (mol).
- **Limitations**: Ideal-gas assumption only; requires exactly one unknown and does not include non-ideal corrections.

### `pchem.delta_g_from_k`
- **Function**: `run_delta_g_from_k(params: dict) -> dict`
- **Purpose**: Relate standard Gibbs free energy and equilibrium constants using ΔG° = -RT ln K.
- **Units**: Temperature in K or °C, ΔG° in J·mol⁻¹, equilibrium constant dimensionless.
- **Limitations**: Assumes standard-state activities; K must be positive; no activity coefficients or ionic strength corrections.

### `pchem.rate_law_simple`
- **Function**: `run_rate_law_simple(params: dict) -> dict`
- **Purpose**: Evaluate zero- or first-order integrated rate laws for concentration over time.
- **Units**: Concentration in mol·L⁻¹, time in seconds, rate constants in 1/s (first order) or mol·L⁻¹·s⁻¹ (zero order).
- **Limitations**: Single-species decay, deterministic evaluation without temperature dependence or complex mechanisms.

All operations return method metadata containing names, descriptions, units, and limitations to aid downstream UI or audit layers.
