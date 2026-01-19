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
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows PowerShell
   # OR: source .venv/bin/activate  # macOS/Linux
   ```
2. **Install in editable mode** (pulls dependencies from pyproject.toml)
   ```powershell
   pip install -e .
   ```
3. **Run tests**
   ```powershell
   python -m unittest discover -s tests
   ```
4. **Initialize storage and try the CLI**
   ```powershell
   python -m labos.cli.main experiment create --name "Week1"
   python -m labos.cli.main job run --module demo.calorimetry --params '{}'
   ```
5. **Launch Streamlit control panel**
   ```powershell
   streamlit run app.py
   ```
6. **Quick verification before commits**
   ```powershell
   .\scripts\verify-local.ps1
   ```

## Architecture at a glance
- **labos/core** – Workflow helpers, JSON-backed experiment/dataset/job registries, audit logging, and the runtime facade.
- **labos/modules** – Educational module stubs (EI-MS fragmentation, PChem calorimetry, Import Wizard) registered for demos and jobs.
- **labos/ui** – Streamlit panels (Learner, Lab, Builder) wired to registries and module metadata for control and review.
- **data/** – Local storage root for registries, audit logs, and job outputs created by the CLI and workflows.
- **tests/** – Coverage for registries, workflows, and module stubs to keep the skeleton stable during hardening.

## 3D scanner reference frame (skeleton)
Structure-from-Motion outputs are inherently arbitrary in origin, rotation, and scale until we apply explicit anchors. The new reference frame module introduces an explicit origin selection step with honest fallbacks: user-provided model-space origins, heuristic bounding-box centering, and placeholders for marker and geospatial anchors. Marker/GPS anchoring is recorded but not yet applied in v1, and aerial regimes only log warnings when falling back to heuristics.

## Docker setup (archived)
Docker configs preserved in `.archive/` for CI/deployment scenarios. Active development uses local `.venv` for speed.

## Environment & secrets
- Copy `.env.example` to `.env` if external services require credentials. This file is git-ignored.
- Every verification run must be noted in `VALIDATION_LOG.md` with timestamp and command evidence.

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

## Dependency management
- Runtime dependencies live in `pyproject.toml` under `[project.dependencies]`.
- Add new packages: `pip install <package>`, then update `pyproject.toml` manually with version constraint.
- Regenerate lockfile: `pip freeze > requirements.txt` (used for CI reproducibility).
- Always commit both `pyproject.toml` and `requirements.txt` after dependency changes.

## Verification workflow
- Run `.\scripts\verify-local.ps1` before commits. The script will:
   1. Execute `python -m unittest discover -s tests`
   2. Check import integrity
   3. Append results to `VALIDATION_LOG.md`
- Keep validation history intact for audit trail.

## Programmatic API
- Use `LabOSRuntime` from `labos.runtime` to access the config loader, audit logger, registries, and job runner as a single facade.
- See `docs/api/internal_usage.md` for examples of creating experiments, registering datasets, and running module operations in code.
