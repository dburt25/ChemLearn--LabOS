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

## Container workflow
- **Build the image** (run from the repo root):
   ```bash
   docker build -t labos-dev .
   ```
- **Run ad-hoc commands** inside a container (the Dockerfile now launches Streamlit by default; pass another command for shells or tests):
   - macOS/Linux:
      ```bash
      ./scripts/docker-run.sh "streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
      ```
   - Windows PowerShell:
      ```powershell
      ./scripts/docker-run.ps1 "streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
      ```
   The helper scripts rebuild the image, mount the repo into `/labos`, forward port `8501`, and execute the provided command (omit the quoted command to stick with the default Streamlit launch).
- **Use Docker Compose** to boot the Streamlit UI directly:
   ```bash
   docker compose up --build
   ```
   Compose maps port `8501` and watches the local workspace through a bind mount, so code edits are reflected on refresh. Provide `DOCKER_HUB_USER` / `DOCKER_HUB_PAT` values in a local `.env` (copy from `.env.example`) when you want to use the bundled `docker-scout` service for CVE scans, or rely on your host `~/.docker/config.json` which is mounted automatically. Use `docker compose down` to stop the container.

### Environment setup & secrets
- Copy `.env.example` to `.env` and set any credentials required by helper services (e.g., Docker Hub PAT). This file is git-ignored for safety.
- Run `docker login` locally so both the host CLI and the compose-based `docker-scout` helper can reuse your registry session.
- Until peer reviewers are available, every verification run (tests + scanners) must be noted in `VALIDATION_LOG.md` with the tag **self reviewed**—include the command set you ran and whether any issues surfaced.

## Docker AI ("Gordon") and Docker Scout
- Review the workflow captured in [`docs/docker_ai_gordon.md`](docs/docker_ai_gordon.md) for Gordon prompts that analyze running containers, rate the Dockerfile, and suggest docker-compose optimizations.
- Quickly scan built images for CVEs with Docker Scout directly from the repo: `docker compose run --rm docker-scout cves labos-dev:latest --only-severity critical,high`. Store your Docker Hub credentials in a local `.env` file (`DOCKER_HUB_USER`, `DOCKER_HUB_PAT`) so the helper container can authenticate without interactive prompts.
- Use Docker Desktop's **Ask Gordon** tab (✨ icon) for live monitoring, and periodically run `docker ai "Check for updates to Docker Desktop and my images"` to stay current.

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
- The active virtual environment is tracked via `.venv/`. When you add or upgrade packages, run `pip install <package>` inside the venv and then refresh the lockfile:
   ```powershell
   Set-Location "C:/Users/<you>/Dev/1. LabOS"
   . ./.venv/Scripts/Activate.ps1
   pip freeze > requirements.txt
   ```
- The `requirements.txt` file is fully pinned; Docker builds and CI use it to guarantee reproducible installs. Always commit the updated file after regenerating it.

## Verification workflow
- Run `pwsh ./scripts/verify.ps1` before opening a PR or handing changes to another agent. The helper will:
   1. Build the container image
   2. Execute `python -m unittest`
   3. Call Docker Gordon for both "rate" and "analyze" prompts
   4. Scan the freshly built image with Docker Scout
   5. Record results under `logs/verify/<timestamp>/`
- Each execution appends a "self reviewed" block to `VALIDATION_LOG.md`; keep this history intact so future contributors can audit the verification trail until formal peer review starts.

## Programmatic API
- Use `LabOSRuntime` from `labos.runtime` to access the config loader, audit logger, registries, and job runner as a single facade.
- See `docs/api/internal_usage.md` for examples of creating experiments, registering datasets, and running module operations in code.
