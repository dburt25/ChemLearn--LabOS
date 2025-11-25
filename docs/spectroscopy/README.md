# Spectroscopy Stubs (NMR & IR)

These entries describe the placeholder spectroscopy module focused on schema
contracts for upcoming NMR and IR tooling. The module registers under the
`spectroscopy` identifier with two stub operations:

- `spectroscopy.nmr_stub`
- `spectroscopy.ir_stub`

## Design Goals

- Provide clear **input schemas** so future implementations can align on data
  contracts without guessing.
- Return **output schemas** that enumerate expected fields, including placeholder
  annotated peaks and metadata.
- Communicate **stub-only limitations** up front to prevent misuse as an
  analytical engine.

## Input Schema Overview

### NMR (`run_nmr_stub`)
- `sample_id` *(string, optional)*: Traceable identifier for the specimen.
- `chemical_formula` *(string, optional)*: Molecular formula (e.g., `C8H10N4O2`).
- `nucleus` *(string, optional)*: Observed nucleus label such as `1H` or `13C`.
- `solvent` *(string, optional)*: Acquisition solvent (e.g., `CDCl3`).
- `peak_list` *(list, optional)*: Peaks with fields:
  - `shift_ppm` *(float)*: Chemical shift in ppm.
  - `intensity` *(float)*: Relative intensity.
  - `multiplicity` *(string)*: Signal multiplicity (s, d, t, q, m, br, etc.).
  - `coupling_constants` *(list[float])*: J values in Hz.
  - `integration` *(float)*: Relative integration.
  - `notes` *(string, optional)*: Free-form annotations.
- `acquisition` *(mapping, optional)*: Acquisition parameters (frequency,
  temperature, pulse program, scans, etc.).

### IR (`run_ir_stub`)
- `sample_id` *(string, optional)*: Traceable identifier for the specimen.
- `chemical_formula` *(string, optional)*: Molecular formula.
- `peak_list` *(list, optional)*: Bands with fields:
  - `wavenumber_cm_1` *(number)*: Position in cm^-1.
  - `intensity` *(string|float)*: Qualitative or quantitative intensity.
  - `assignment` *(string)*: Tentative functional group label.
  - `confidence` *(float)*: Assignment confidence (0–1).
  - `notes` *(string, optional)*: Free-form annotations.
- `instrument` *(mapping, optional)*: Instrument settings (resolution, source,
  detector, beam splitter, scans, atmosphere, etc.).
- `processing` *(mapping, optional)*: Processing flags (baseline correction,
  smoothing, ATR correction, etc.).

## Output Schema Overview

Both stubs return structures with:

- `method_name`: Fully qualified key for registry lookups.
- `description`: Human-readable summary of the stub.
- `stub`: Boolean flag indicating placeholder behavior.
- `input_schema`: Echo of expected inputs for contracts and validation.
- `output_schema`: Declarative description of returned fields.
- `annotated_peaks`: Echoed peaks with placeholder annotations.
- `notes`: List of limitations and usage guidance.
- `metadata`: Module metadata (module id, version, and select input fields).
- `received_params`: Direct echo of user-supplied parameters to aid debugging.

## Limitations

- No spectral interpretation, validation, or peak picking is performed.
- Outputs are for **contract shaping only** and should not be treated as
  analytical results.
- Future implementations should replace placeholder annotations with real
  spectral reasoning, uncertainty estimates, and provenance links.
