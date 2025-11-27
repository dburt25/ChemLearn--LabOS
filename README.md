# ChemLearn LabOS

ChemLearn LabOS is a faith-aligned laboratory operating system that coordinates experiments, jobs, datasets, and scientific learning tools across a unified stack. The current release is **Phase 2.5.3 (hardening)**, focusing on stabilizing the working skeleton and tightening validation around the existing workflows.

## What works in Phase 2.5.3
- Core experiment, job, dataset, and audit pipeline backed by JSON registries and workflow helpers.
- Deterministic PChem and EI-MS tools plus the Import Wizard stub, each registered as modules you can run through the CLI or workflows.
- Streamlit control panel with Learner, Lab, and Builder modes that surface registries, module metadata, and recent audit context.
- Basic CLI commands for initializing storage, creating experiments, registering datasets, and running module jobs.

> External API and ML integrations remain stubs in this phase, and the project is intended for educational/research use only—not for clinical workflows.

## Getting started
1. **Create and activate a virtual environment (Python 3.10+)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -e .
   ```
3. **Run tests**
   ```bash
   pytest
   ```
4. **Initialize storage and run a simple CLI sequence** (creates `data/` with registry, audit, and job folders)
   ```bash
   labos init
   labos new-experiment --user student --title "Week1" --purpose "Buffer prep"
   labos run-module --experiment-id EXP-001 --module-id eims.fragmentation --operation compute --actor student --params-json '{"precursor_mz": 250}'
   ```
   Replace `EXP-001` with the identifier printed by `new-experiment` if your sequence starts at a different index.
5. **Launch the Streamlit control panel**
   ```bash
   streamlit run app.py
   ```
6. **Demo CLI (in-memory, no persistence)**
   ```bash
   python -m labos.cli.main experiment create --name "Kinetic sweep"
   python -m labos.cli.main job run --module demo.calorimetry --params '{"temp": 298}'
   ```

## Architecture at a glance
- **labos/core** – Workflow helpers, JSON-backed experiment/dataset/job registries, audit logging, and the runtime facade.
- **labos/modules** – Educational module stubs (EI-MS fragmentation, PChem calorimetry, Import Wizard) registered for demos and jobs.
- **labos/ui** – Streamlit panels (Learner, Lab, Builder) wired to registries and module metadata for control and review.
- **data/** – Local storage root for registries, audit logs, and job outputs created by the CLI and workflows.
- **tests/** – Coverage for registries, workflows, and module stubs to keep the skeleton stable during hardening.

## CLI usage
- Persistent CLI: see [`docs/cli/USAGE.md`](docs/cli/USAGE.md) for `labos` commands that manage on-disk experiments, datasets, and jobs.
- Demo CLI: run `python -m labos.cli.main` commands to explore in-memory examples without touching storage.

## Key documentation
- Project direction: [`docs/VISION.md`](docs/VISION.md), [`docs/DEVELOPMENT_VISION_GUIDE.md`](docs/DEVELOPMENT_VISION_GUIDE.md)
- Developer workflow & on-ramp: [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md)
- Architecture and modules: [`docs/README_ARCHITECTURE.md`](docs/README_ARCHITECTURE.md), [`docs/MODULARITY_GUIDELINES.md`](docs/MODULARITY_GUIDELINES.md)
- Phase/state snapshots: [`docs/SWARM_STATUS.md`](docs/SWARM_STATUS.md), [`docs/PHASES_OVERVIEW.md`](docs/PHASES_OVERVIEW.md), [`docs/CURRENT_CAPABILITIES.md`](docs/CURRENT_CAPABILITIES.md)
- Swarm governance & permissions: [`docs/SWARM_GOVERNANCE.md`](docs/SWARM_GOVERNANCE.md), [`docs/BOT_PERMISSIONS_MATRIX.md`](docs/BOT_PERMISSIONS_MATRIX.md)
- Compliance and provenance: [`docs/COMPLIANCE_CHECKLIST.md`](docs/COMPLIANCE_CHECKLIST.md), [`docs/METHOD_AND_DATA.md`](docs/METHOD_AND_DATA.md), [`docs/AUDIT_LOG_FORMAT.md`](docs/AUDIT_LOG_FORMAT.md)
- Notebook onboarding: [`docs/quickstart_notebook.md`](docs/quickstart_notebook.md)

## Notes
- Modules can also be auto-discovered via `LABOS_MODULES` (comma-separated import paths) when you want to load external plugins.
- All outputs are educational only until validation dossiers are produced; keep audit logs current and prefer deterministic examples for demos.

## Programmatic API
- Use `LabOSRuntime` from `labos.runtime` to access the config loader, audit logger, registries, and job runner as a single facade.
- See `docs/api/internal_usage.md` for examples of creating experiments, registering datasets, and running module operations in code.
