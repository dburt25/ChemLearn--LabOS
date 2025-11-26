# LabOS CLI Usage

This guide shows how to run the two CLI surfaces exposed by LabOS:

- **Persistent CLI (`labos`)** – manages real experiment, dataset, and job records under the configured storage root.
- **Demo CLI (`python -m labos.cli.main`)** – Phase 2 in-memory preview useful for quick tours without writing to disk.

## Prerequisites
- Python 3.10+
- LabOS installed in editable mode (from repo root):
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```
- Optional: set `LABOS_ROOT` or pass `--root` to point at a different storage directory.

## Persistent CLI (`labos`)
Run `labos --help` to view all commands.

### Initialize storage
Creates `data/` with audit, registry, and job folders.
```bash
labos init
```

### Create an experiment
Non-interactive example (prompts are available when flags are omitted):
```bash
labos new-experiment --user student --title "Week1" --purpose "Buffer prep" --status draft
```

### Register a dataset
```bash
labos register-dataset --owner student --dataset-type experimental --uri s3://placeholder --tags "qc,ms"
```

### Run a module operation
Executes a registered module and records the resulting job.
```bash
labos run-module \
  --experiment-id EXP-0001 \
  --module-id eims.fragmentation \
  --operation compute \
  --actor student \
  --params-json '{"precursor_mz": 250}'
```
If a JSON file is preferred, use `--params-file path/to/params.json` instead of `--params-json`.

## Demo CLI (`python -m labos.cli.main`)
The demo CLI is non-persistent and emits educational examples only.

List modules, experiments, or run the in-memory demo job:
```bash
python -m labos.cli.main modules
python -m labos.cli.main experiments
python -m labos.cli.main demo-job
```

Use the demo commands when you want to showcase data structures without touching on-disk registries; use the persistent CLI for real records.
