# ChemLearn LabOS

ChemLearn LabOS is a faith-aligned laboratory operating system that coordinates experiments, jobs, datasets, and scientific learning tools across a unified stack. The repository is now in **Phase 2.5.1 (Working Lab Skeleton)**: file-backed registries, a runnable CLI, educational scientific stubs, and the Streamlit control panel are all present, while execution wiring and validation are still being hardened.

## What works today
- Deterministic EI-MS fragmentation, P-Chem calorimetry, and import wizard stubs that register with the module registry and run through the CLI and workflows.
- JSON-backed experiment/dataset/job registries with workflow helpers that stitch module runs into lineage and audit trails.
- Learner, Lab, and Builder modes in the Streamlit control panel that surface registries, module metadata, and recent audit context.

## What ships today
- **LabOS Core** (`labos/core`, `labos/`): JSON-backed registries for experiments, datasets, and jobs; audit logging; runtime facade; job runner that persists results under `data/jobs/`; and workflow helpers for linking experiments, datasets, and jobs with audit events.
- **Scientific modules** (`labos/modules`): built-in educational stubs for EI-MS fragmentation (`eims.fragmentation`), P-Chem calorimetry (`pchem.calorimetry`), and the Import Wizard (`import.wizard`). Each registers a `compute` operation that returns deterministic dataset/audit payloads for demos.
- **UI layer** (`labos/ui`, `app.py`): Streamlit control panel with **Learner**, **Lab**, and **Builder** modes. Panels surface experiments, jobs, datasets, module descriptors, and Method & Data provenance footers sourced from module metadata and recent audits.

## Quick start
1. **Install** (Python 3.10+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. **Initialize storage** (creates `data/` + audit/registry folders):
   ```bash
   labos init
   ```
3. **Create records**:
   ```bash
   labos new-experiment --user student --title "Week1" --purpose "Buffer prep"
   labos register-dataset --owner student --dataset-type experimental --uri s3://placeholder
   ```
4. **Run a stub module via the job runner** (stores JSON results under `data/jobs/`):
   ```bash
   labos run-module --experiment-id <exp-id> --module-id eims.fragmentation --operation compute --actor student --params-json '{"precursor_mz": 250}'
   ```
5. **Launch the control panel** (optional UI):
   ```bash
   streamlit run app.py
   ```

## CLI usage
- Persistent CLI: see [`docs/cli/USAGE.md`](docs/cli/USAGE.md) for `labos` commands that manage on-disk experiments, datasets, and jobs.
- Demo CLI: run `python -m labos.cli.main` commands to explore in-memory examples without touching storage.

## Key documentation
- Project direction: [`docs/VISION.md`](docs/VISION.md), [`docs/DEVELOPMENT_VISION_GUIDE.md`](docs/DEVELOPMENT_VISION_GUIDE.md)
- Developer workflow & on-ramp: [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md)
- Architecture and modules: [`docs/README_ARCHITECTURE.md`](docs/README_ARCHITECTURE.md), [`docs/MODULARITY_GUIDELINES.md`](docs/MODULARITY_GUIDELINES.md)
- Phase/state snapshots: [`docs/SWARM_STATUS.md`](docs/SWARM_STATUS.md), [`docs/PHASES_OVERVIEW.md`](docs/PHASES_OVERVIEW.md)
- Swarm governance & permissions: [`docs/SWARM_GOVERNANCE.md`](docs/SWARM_GOVERNANCE.md), [`docs/BOT_PERMISSIONS_MATRIX.md`](docs/BOT_PERMISSIONS_MATRIX.md)
- Compliance and provenance: [`docs/COMPLIANCE_CHECKLIST.md`](docs/COMPLIANCE_CHECKLIST.md), [`docs/METHOD_AND_DATA.md`](docs/METHOD_AND_DATA.md), [`docs/AUDIT_LOG_FORMAT.md`](docs/AUDIT_LOG_FORMAT.md)
- Notebook onboarding: [`docs/quickstart_notebook.md`](docs/quickstart_notebook.md)

## Notes
- Modules can also be auto-discovered via `LABOS_MODULES` (comma-separated import paths) when you want to load external plugins.
- All outputs are educational only until validation dossiers are produced; keep audit logs current and prefer deterministic examples for demos.

## Programmatic API
- Use `LabOSRuntime` from `labos.runtime` to access the config loader, audit logger, registries, and job runner as a single facade.
- See `docs/api/internal_usage.md` for examples of creating experiments, registering datasets, and running module operations in code.
