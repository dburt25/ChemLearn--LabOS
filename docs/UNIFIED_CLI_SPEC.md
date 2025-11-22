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
