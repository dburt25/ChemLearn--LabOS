# Internal Runtime Usage

The internal runtime facade (`labos.runtime.LabOSRuntime`) bundles the default
configuration loader, audit logger, registries, and job runner into a single
object. It is a light convenience layer for bots or utilities that need to
orchestrate experiments, datasets, and module runs without manually wiring
registries.

## Getting started

```python
from labos.runtime import LabOSRuntime
from labos.core.types import DatasetType

runtime = LabOSRuntime()
runtime.ensure_initialized()  # creates data/ + registry/audit folders when absent
```

`ensure_initialized()` is safe to call multiple times and will create the
`data/` directory structure expected by the registries.

## Create an experiment

```python
experiment = runtime.create_experiment(
    user_id="student",
    title="Buffer prep",
    purpose="Week 1 lab demo",
)
print(experiment.id)
```

Experiments can also be tagged or started in a non-draft status by passing the
`tags` or `status` arguments to `create_experiment()`.

## Register a dataset

```python
dataset = runtime.register_dataset(
    owner="student",
    dataset_type=DatasetType.EXPERIMENTAL,
    uri="s3://placeholder",
    metadata={"instrument": "LC-MS"},
)
print(dataset.id)
```

The runtime constructs a `Dataset` record and persists it through the
`DatasetRegistry`, attaching audit context automatically.

## Run a module operation

```python
job = runtime.run_module_operation(
    experiment_id=experiment.id,
    module_id="eims.fragmentation",
    operation="compute",
    actor="student",
    parameters={"precursor_mz": 250},
)
print(job.id, job.result)
```

`run_module_operation()` resolves the registered module, executes the requested
operation through the job runner, and stores the resulting job and dataset
artifacts under `data/jobs/`.

## Components

`LabOSRuntime` exposes the underlying components through the `components`
attribute, which contains:

- `config`: loaded `LabOSConfig`
- `audit`: `AuditLogger`
- `datasets`: `DatasetRegistry`
- `experiments`: `ExperimentRegistry`
- `jobs`: `JobRunner`

Use the components directly when you need lower-level control while preserving
consistent audit and storage behavior.
