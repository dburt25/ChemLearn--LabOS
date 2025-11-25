# Physical chemistry utilities

This module extends the PChem toolkit beyond calorimetry with deterministic, unit-aware helpers.

## Available operations

### `pchem.ideal_gas`
- **Function**: `run_ideal_gas(params: dict) -> dict`
- **Inputs**:
  - `pressure`, `pressure_unit` (Pa, kPa, atm)
  - `volume`, `volume_unit` (m³, L)
  - `amount_mol`
  - `temperature`, `temperature_unit` (K, C)
  - Exactly one of pressure/volume/amount/temperature may be omitted and will be solved for.
- **Output**: Value dictionary for all four state variables plus a `dataset` block with calculation metadata and a `method` block with units, limitations, and citations.
- **Limitations**: Ideal-gas assumption only; requires exactly one unknown and does not include non-ideal corrections.

### `pchem.delta_g_from_k`
- **Function**: `run_delta_g_from_k(params: dict) -> dict`
- **Inputs**: Either `equilibrium_constant` or `delta_g_j_per_mol`, plus `temperature` and optional `temperature_unit` (K, C).
- **Output**: Equilibrium constant, ΔG° (J·mol⁻¹), temperature (SI and requested units), a dataset metadata block, and detailed method metadata with citations.
- **Limitations**: Assumes standard-state activities; K must be positive; no activity coefficients or ionic strength corrections.

### `pchem.rate_law_simple`
- **Function**: `run_rate_law_simple(params: dict) -> dict`
- **Inputs**: `order` ("zero" or "first"), `initial_concentration` (mol·L⁻¹), `rate_constant` (appropriate to the order), and `time` (s).
- **Output**: Concentration at `time`, half-life, echoed inputs, dataset metadata, and method metadata including citations.
- **Limitations**: Single-species decay, deterministic evaluation without temperature dependence or complex mechanisms.

All operations return method metadata containing names, descriptions, units, limitations, and citations to aid downstream UI or audit layers, alongside DatasetRef-style dictionaries for provenance-aware workflows.
