# Experiment templates

Experiment templates provide reusable defaults for common LabOS experiments.
A template points to a scientific module and captures the default parameters
needed to launch a run quickly.

## Template structure

Templates are defined with the `Template` dataclass in
`labos/core/experiment_templates.py` and include:

- `name`: Unique template name, e.g., `pchem.calorimetry.basic`.
- `description`: Short summary of the experimental intent.
- `module_key`: Registry key of the scientific module to execute.
- `default_params`: Parameter dictionary sent to the module's operation.

The registry offers two helpers for simple access:

```python
from labos.core.experiment_templates import get_template, list_templates

calorimetry = get_template("pchem.calorimetry.basic")
all_templates = list_templates()
```

Each template exposes `to_dict()` for downstream serialization when needed.

## Included templates

The default registry ships with two starter templates:

- **PChem calorimetry basic** (`pchem.calorimetry.basic`): Constant-pressure
  calorimetry setup with mass, heat capacity, and ΔT defaults.
- **EI-MS basic analysis** (`eims.analysis.basic`): Electron ionization mass
  spectrometry starter for fragment prediction and spectral matching.

Use these entries as examples when adding new templates for other modules.
