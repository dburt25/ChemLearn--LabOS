# Unified CLI Spec (Draft)

Defines goals for a single command-line entry point once LabOS Core is available.

## Objectives
- Provide deterministic automation for experiments, jobs, datasets, and audits.
- Offer modes for Learner, Lab Operator, and Builder personas.
- Integrate authentication and permissions aligned with Clinical Boundary Mode.

## Early Command Ideas
- `labos init` — scaffold new experiments/jobs.
- `labos run` — execute jobs with validated parameters.
- `labos audit` — query audit trails.
- `labos module` — manage scientific plugins.

## Implementation Notes
- CLI deferred until Phase 1 completion.
- Commands must emit structured logs for ALCOA+ compliance.
- Testing harness required (unit + e2e) before general availability.

## Phase 2+ Persistent CLI commands
The current CLI aligns with the internal workflow helpers and reads/writes JSON
records under ``LABOS_ROOT``:

- `labos list-modules` – show module keys with their method names from the default ``ModuleRegistry``.
- `labos list-experiments` – print experiment id, name, and creation time from on-disk records.
- `labos list-datasets` – list dataset ids with any experiment/job provenance hints found in metadata.
- `labos run-module <module_key>` – invoke ``run_module_job`` with inline JSON parameters or a params file and print the ``WorkflowResult`` as JSON.

Example invocations (from the repo root):

```bash
python -m labos.cli list-modules
python -m labos.cli list-experiments --root /tmp/labos-demo
python -m labos.cli run-module pchem.calorimetry --params-json '{"delta_t": 2.5}'
```
