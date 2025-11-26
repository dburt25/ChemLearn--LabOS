# Quickstart Notebook Walk-through

This pseudo-notebook demonstrates how to explore ChemLearn LabOS from a fresh checkout using the internal API. Use it as a scripted onboarding path for interactive environments (e.g., Jupyter, VS Code notebooks) without relying on the CLI.

## Prerequisites
- Python 3.10+
- Editable install of the repository (from the repo root):
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```
- Start your notebook kernel inside the virtual environment.

## Notebook outline
The following cells can be pasted into a notebook in order. Each cell builds on the previous ones and uses only public LabOS helpers.

### 1) Imports and paths
```python
from pathlib import Path

from labos import runtime
from labos.core import audit, experiments, datasets, jobs
from labos.modules import registry as module_registry

# Point to the repository root (adjust if your notebook is elsewhere)
ROOT = Path.cwd()
DATA_DIR = ROOT / "data"
```

### 2) Initialize storage and audit log
```python
# Create data/ and registry/audit files if they do not exist
runtime.ensure_storage(DATA_DIR)

# Optionally set a deterministic audit actor for demo runs
AUDIT_ACTOR = "student"
```

### 3) Register an experiment and dataset
```python
experiment_id = experiments.create_experiment(
    title="Notebook Demo Week 1",
    user=AUDIT_ACTOR,
    purpose="Buffer prep walk-through",
)

# Minimal dataset stub for linking runs
sample_dataset_id = datasets.register_dataset(
    owner=AUDIT_ACTOR,
    dataset_type="experimental",
    uri="s3://placeholder/notebook-demo",
)
```

### 4) Discover available modules
```python
available_modules = module_registry.list_modules()
for module_id, descriptor in available_modules.items():
    print(f"{module_id}: {descriptor.operations}")
```

### 5) Run a module operation through the job runner
```python
# Choose a deterministic educational module
target_module = "eims.fragmentation"
operation = "compute"

params = {"precursor_mz": 250}

result = jobs.run_module_job(
    experiment_id=experiment_id,
    module_id=target_module,
    operation=operation,
    actor=AUDIT_ACTOR,
    params=params,
)

print("Job stored at:", result["job_path"])
print("Payload keys:", list(result.keys()))
```

### 6) Inspect lineage and audit entries
```python
# Read back experiment, dataset, and job provenance
loaded_experiment = experiments.load_experiment(experiment_id)
loaded_dataset = datasets.load_dataset(sample_dataset_id)
latest_audits = audit.tail(limit=5)

loaded_experiment, loaded_dataset, latest_audits
```

### 7) Extend with your own modules (optional)
```python
# Add external modules by import path (comma-separated string)
# os.environ["LABOS_MODULES"] = "custom.package.module,another.plugin"
# module_registry.reload()
```

### 8) Clean up (optional)
```python
# Remove demo artifacts if desired
import shutil

shutil.rmtree(DATA_DIR, ignore_errors=True)
```

## Tips
- Keep runs deterministic for reproducible demos.
- Use the audit tail to narrate notebook steps when presenting to others.
- For full CLI parity, compare with `labos --help` and mirror commands via the runtime helpers above.
