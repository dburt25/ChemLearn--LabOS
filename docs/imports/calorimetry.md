# Calorimetry Import Schema

The calorimetry import helpers normalize user-supplied tabular data into a
canonical schema suitable for P-Chem workflows. The importer works purely
in-memory on `pandas.DataFrame` objects or sequences of mapping objects.

## Canonical columns

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `sample_id` | string | No | Sample or experiment identifier. |
| `mass_g` | float | Yes | Sample mass in grams. |
| `specific_heat_j_per_gk` | float | Yes | Specific heat capacity in J/(g*K). |
| `t_initial_k` | float | Yes | Initial temperature in Kelvin. |
| `t_final_k` | float | Yes | Final temperature in Kelvin. |
| `calorimeter_constant_j_per_k` | float | No | Heat capacity term for the instrument. |
| `solvent_volume_ml` | float | No | Solvent or solution volume in milliliters. |
| `notes` | string | No | Freeform annotations about the run. |

Synonyms such as `mass`, `cp`, `start_temp`, and `sample` are automatically
resolved, and explicit mappings can override the defaults.

## Helper usage

```python
from labos.modules.imports import import_calorimetry_table

rows = [
    {
        "Sample": "A1",
        "Mass (g)": 1.23,
        "Cp": 4.18,
        "T initial (K)": 298.15,
        "T final (K)": 304.2,
        "Notes": "Calibration run",
    }
]

result = import_calorimetry_table(rows, source="Inline example")
print(result["records"])  # canonical columns
print(result["dataset"])  # DatasetRef-compatible metadata
```

Validation errors are raised when required columns are missing or when numeric
columns cannot be coerced to floats. Extra columns are preserved in the
`extras` block unless `drop_unknown=True` is supplied.
