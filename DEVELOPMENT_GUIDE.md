# Development Guide (Phase 2.5+)

This guide is the on-ramp for contributors working on ChemLearn LabOS while we stabilize the Phase 2.5 working lab skeleton. It summarizes the current layout, day-to-day workflows, and how to extend LabOS safely.

## Repository layout (high level)
- `labos/` – Python package root with config, audit logging, registries, CLI entry point, job runner, and UI helpers.
- `labos/core/` – Core dataclasses, workflow helpers, and JSON-backed storage utilities for experiments, datasets, and jobs.
- `labos/modules/` – Built-in educational stubs (`eims.fragmentation`, `pchem.calorimetry`, `import.wizard`) plus the module registry that auto-loads descriptors (including optional `LABOS_MODULES` plugins).
- `labos/ui/` & `app.py` – Streamlit control panel (Learner/Lab/Builder modes) showing experiments, jobs, datasets, modules, and the Method & Data provenance footer.
- `data/` – Created at runtime; holds audit logs, registry JSON files, job results, and example/demo payloads.
- `docs/` – Architecture, compliance, and roadmap references (start with `VISION.md`, `DEVELOPMENT_VISION_GUIDE.md`, `COMPLIANCE_CHECKLIST.md`).

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
If you add new tests, keep them headless (Streamlit is optional) and ensure deterministic outputs for stub modules.

## Working with the CLI and runtime
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
1. Create a new package under `labos/modules/<domain>/` and implement pure, deterministic functions (educational-safe by default).
2. Define a `ModuleDescriptor` and one or more `ModuleOperation`s in the module, then register it via `register_descriptor()` so `labos.modules.get_registry()` can find it.
3. Expose a concise `module_id` and `operation` name (e.g., `compute`) that the CLI and UI can invoke.
4. Update provenance/metadata if needed:
   - Add method metadata in `labos/core/module_registry.py` so the Method & Data footer shows citations/limitations.
   - Document limitations in `docs/METHOD_AND_DATA.md` and, if applicable, update compliance notes.
5. Keep outputs JSON-serializable; the job runner writes results to timestamped files for traceability.

## Wiring a job or workflow
- The `LabOSRuntime` in `labos/runtime.py` wires together configuration, audit logging, registries, and the `JobRunner`.
- `JobRunner.run()` records a job, executes a registered module operation, persists the result JSON under `data/jobs/`, and writes audit events. Use it directly or via the CLI `run-module` command.
- For more complex flows, use the helpers in `labos/core/workflows.py` to create experiments, attach datasets, and link audit events without bypassing the registries.

## Documentation & compliance expectations
- Every change should update `CHANGELOG.md` and, when tests run, append evidence to `VALIDATION_LOG.md`.
- Keep `compliance-notes.md` current when adding data handling, UI behaviors, or module capabilities.
- When extending UI or modules, re-check `docs/SWARM_STATUS.md` and `docs/MODULARITY_GUIDELINES.md` so paths and bot boundaries stay accurate.
