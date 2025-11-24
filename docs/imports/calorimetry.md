# Calorimetry Import Schema

The calorimetry import helpers normalize user-supplied tabular data into a
canonical schema suitable for P-Chem workflows. The importer works purely
in-memory on `pandas.DataFrame` objects or sequences of mapping objects.

## Canonical columns

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `time_s` | float | Yes | Elapsed time in seconds. |
| `temperature_c` | float | Yes | Temperature in degrees Celsius. |
| `heat_flow_mw` | float | No | Heat flow signal in milliwatts. |
| `sample_id` | string | No | Sample or experiment identifier. |
| `run_id` | string | No | Run or injection identifier for grouped traces. |
| `event_label` | string | No | Optional annotation for events or steps. |

Synonyms such as `time`, `temp`, `heat_flow`, and `sample` are automatically
resolved, and explicit mappings can override the defaults.

## Helper usage

```python
from labos.modules.imports import import_calorimetry_table

rows = [
    {"Time": 0, "Temp": 21.3, "Heat Flow": 1.2, "Sample": "A1"},
    {"Time": 5, "Temp": 22.0, "Heat Flow": 1.1, "Sample": "A1"},
]

result = import_calorimetry_table(rows, source="Inline example")
print(result["records"])  # canonical columns
print(result["dataset"])  # DatasetRef-compatible metadata
```

Validation errors are raised when required columns are missing or when numeric
columns cannot be coerced to floats. Extra columns are preserved in the
`extras` block unless `drop_unknown=True` is supplied.
