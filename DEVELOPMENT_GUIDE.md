# Development Guide (Phase 2.5.3)

This guide is the on-ramp for contributors working on ChemLearn LabOS during the Phase 2.5.3 hardening wave. It summarizes the current layout, day-to-day workflows, and how to extend LabOS safely.

## Repository layout (high level)
- `labos/` – Python package root with config, audit logging, registries, CLI entry point, job runner, workflows, and UI helpers.
- `labos/core/` – Core dataclasses, workflow helpers, and JSON-backed storage utilities for experiments, datasets, and jobs.
- `labos/modules/` – Built-in educational stubs (`eims.fragmentation`, `pchem.calorimetry`, `import.wizard`) plus the module registry that auto-loads descriptors (including optional `LABOS_MODULES` plugins).
- `labos/ui/` & `app.py` – Streamlit control panel (Learner/Lab/Builder modes) showing experiments, jobs, datasets, modules, and the Method & Data provenance footer.
- `data/` – Created at runtime; holds audit logs, registry JSON files, job results, and example/demo payloads.
- `docs/` – Architecture, compliance, and roadmap references (start with `VISION.md`, `DEVELOPMENT_VISION_GUIDE.md`, `COMPLIANCE_CHECKLIST.md`).
- Workflows and orchestration helpers live in `labos/core/workflows.py`; UI surfaces for them reside in `labos/ui/**` and are summarized in `docs/WORKFLOWS_OVERVIEW.md` and `docs/README_ARCHITECTURE.md`.

## Environment setup
1. Install dependencies in editable mode (Python 3.10+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. Initialize the workspace directories and audit/registry stores:
   ```bash
   labos init
   ```
3. Optional: point `LABOS_ROOT` (or `--root`) to isolate local runs; other paths (e.g., `LABOS_DATA_DIR`, `LABOS_AUDIT_DIR`) inherit from it.

## Running tests
Use the standard library test runner so we avoid optional UI dependencies during CI:
```bash
python -m unittest discover -s tests
```
- Run `labos init` first if you need local `data/` scaffolding; most tests operate purely in-memory with temporary paths.
- Keep tests headless (no Streamlit/browser dependencies) and deterministic so registry/job assertions remain stable.
- Prefer `python -m unittest tests.test_<area>` while iterating to focus on a single surface.

## Working with the CLI and runtime
Working CLI commands (Bot 48) share the same registries and storage as the UI: `labos init`, `labos new-experiment`, `labos register-dataset`, and `labos run-module`.

- Create an experiment:
  ```bash
  labos new-experiment --user <user> --title "Titration" --purpose "demo"
  ```
- Register a dataset placeholder:
  ```bash
  labos register-dataset --owner <user> --dataset-type experimental --uri s3://placeholder
  ```
- Run a module job (result JSON stored under `data/jobs/`):
  ```bash
  labos run-module --experiment-id <exp-id> --module-id import.wizard --operation compute --actor <user> --params-json '{"source":"demo"}'
  ```
- Launch the Streamlit control panel (reads/writes the same registries):
  ```bash
  streamlit run app.py
  ```

## Adding a module
1. Create a new package under `labos/modules/<domain>/` with a `stub.py` (or similar) that exposes pure, deterministic functions—default to educational-safe behavior and avoid side effects.
2. Construct a `ModuleDescriptor` with a stable `module_id`, semantic-ish `version`, and human-readable `description`.
3. For each callable surface, create a `ModuleOperation` (e.g., `compute`) pointing at the handler function, then call `descriptor.register_operation()` to attach it.
4. Call `labos.modules.register_descriptor(descriptor)` at import time so `get_registry()` discovers it automatically (the CLI, runtime, and workflows rely on this registry).
5. Keep outputs JSON-serializable; the job runner writes results to timestamped files for traceability.
6. Add or update metadata:
   - Populate method metadata in `labos/core/module_registry.py` so the Method & Data footer shows citations/limitations.
   - Document limitations in `docs/METHOD_AND_DATA.md` and, if applicable, update compliance notes.

## Registering a module with the registry
- **Built-ins:** Place the descriptor in a module under `labos/modules/**` and register it when the module imports; `labos.modules.get_registry()` will import built-in stub paths automatically.
- **Plugins:** Export the descriptor from an external package and set `LABOS_MODULES="your.module.path"` (comma-separated) so `ModuleRegistry.auto_discover()` imports and registers it at startup.
- **Validation:** Confirm the registry entry by invoking `labos run-module --module-id <id> --operation compute` with demo params or by calling `labos.modules.get_registry().ensure_module_loaded(<id>)` in a Python shell.

## Wiring a job or workflow
- The `LabOSRuntime` in `labos/runtime.py` wires together configuration, audit logging, registries, and the `JobRunner`.
- `JobRunner.run()` records a job, executes a registered module operation, persists the result JSON under `data/jobs/`, and writes audit events. Use it directly or via the CLI `run-module` command.
- For more complex flows, use the helpers in `labos/core/workflows.py` to create experiments, attach datasets, and link audit events without bypassing the registries.

## How workflows and modes fit together
- **Workflows:** `labos/core/workflows.py` provides orchestration helpers that create an Experiment (or reuse one), run a registered module operation via the registry, emit audit events, and persist Job/Dataset lineage. Use these helpers when composing multi-step flows so experiments, jobs, datasets, and audits stay linked.
- **Runtime & CLI:** `LabOSRuntime` and `labos run-module` are thin facades over the same registries and job runner; they share the module registry used by workflows.
- **Modes:** Experiments carry a mode (`Learner`, `Lab`, `Builder`) that influences UI copy and guardrails. The Streamlit control panel reads the same registries and shows mode-aware messaging, but the data model and workflow helpers remain consistent across modes.

## Documentation & compliance expectations
- Every change should update `CHANGELOG.md` and, when tests run, append evidence to `VALIDATION_LOG.md`.
- Keep `compliance-notes.md` current when adding data handling, UI behaviors, or module capabilities.
- When extending UI or modules, re-check `docs/SWARM_STATUS.md` and `docs/MODULARITY_GUIDELINES.md` so paths and bot boundaries stay accurate.
