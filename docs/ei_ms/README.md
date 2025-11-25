# EI-MS Basic Heuristic Analysis Stub

This module implements a deterministic, heuristic EI-MS fragment tagging helper. It is intended for education and quick demos rather than instrument-grade interpretation.

## API

```python
from labos.modules.ei_ms.basic_analysis import run_ei_ms_analysis

result = run_ei_ms_analysis({
    "precursor_mass": 250.0,
    "fragment_masses": [77.0, 105.0, 133.0, 167.0],
    "fragment_intensities": [35, 80, 20, 15],
    "annotations": {105.0: "tropylium-like"},
})
```

### Parameters
- `precursor_mass` *(float)*: Parent ion mass.
- `fragment_masses` *(list[float])*: Observed fragment masses.
- `fragment_intensities` *(list[float], optional)*: Relative intensities; otherwise heuristic scaling is applied.
- `annotations` *(mapping, optional)*: User-provided notes keyed by fragment mass.

### Output
The function returns a deterministic dictionary with:
- `module_key`: `"ei_ms.basic_analysis"`.
- `method`: Metadata (name, description, version, limitations).
- `inputs`: Echoed, normalized inputs.
- `fragments`: List of entries containing mass, relative intensity, classification (`base_peak`, `major_fragment`, or `minor_fragment`), labels (including `candidate_fragment`), detected neutral losses, and any matching annotations.
- `summary`: Base peak mass, major fragment masses, and unique neutral loss suggestions.
- `message`: Reminder that the logic is heuristic only.

## Module Registration

The module self-registers under the key `ei_ms.basic_analysis` with the operation `analyze` when imported. Add `labos.modules.ei_ms.basic_analysis` to `LABOS_MODULES` for autodiscovery or import the module directly to access `run_ei_ms_analysis`.

## Limitations
- Neutral loss detection is pattern-based using a small set of common losses.
- No attempt is made to simulate fragmentation pathways or instrument response.
- Deterministic heuristic only; not a validated predictor for experimental planning.
