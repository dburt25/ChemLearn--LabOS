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

## Phase 2 Demo Commands (Wave 3)
The initial CLI shipped as an educational preview. Commands run entirely in-memory and do **not** persist any records:

- `labos-cli modules` – list module registry entries (key, display name, method name, limitations summary).
- `labos-cli experiments` – print example experiments for Learner/Lab/Builder modes with a "demo only" disclaimer.
- `labos-cli demo-job` – create an in-memory Experiment + Job pair using core helpers and show their dictionaries.

Example invocations (from the repo root):

```bash
python -m labos.cli.main modules
python -m labos.cli.main experiments
python -m labos.cli.main demo-job
```

These are Phase 2 demonstration commands; persistence, authentication, and structured audit logging will arrive in later phases.
