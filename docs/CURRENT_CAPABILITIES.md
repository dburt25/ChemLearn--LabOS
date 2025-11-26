# Current Capabilities – ChemLearn LabOS

This snapshot captures the LabOS surfaces that are functional today. Use it as a quick reference for what is stable enough to demo or build on.

## Core
- JSON-backed registries for experiments, datasets, and jobs with helpers that wire provenance between them.
- Audit logger emits chained JSONL events per `docs/AUDIT_LOG_FORMAT.md` and is invoked by workflow helpers and the job runner.
- File-backed storage setup via `LabOSConfig` creates `data/` subfolders for audit logs, experiments, datasets, jobs, and feedback/examples.
- Module registry exposes metadata (descriptors, citations, limitations) consumed by CLI and UI surfaces.

## Modules
- EI-MS fragmentation stub (`eims.fragmentation`) returning deterministic spectra payloads plus dataset/audit references.
- P-Chem calorimetry stub (`pchem.calorimetry`) emitting calorimetry placeholders for demos.
- Import Wizard stub (`import.wizard`) that infers schemas/previews, registers datasets, and provides fallback sample rows when input data is absent.
- Built-in module metadata defaults live in `labos/core/module_registry.py` and populate UI footers and provenance inspectors.

## UI
- Streamlit control panel (`app.py`, `labos/ui`) with Learner, Lab, and Builder modes.
- Panels for overview, experiments, jobs, datasets, modules, and workspace with provenance inspectors and Method & Data footers sourced from module metadata and recent audits.
- Workspace area supports notes, file uploads, and placeholders for future 3D visualization hooks (see `docs/THREED_VISUALIZATION_PLAN.md`).

## CLI
- `labos` entry point supports `init`, new experiment creation, dataset registration, and running registered module operations through the job runner.
- Job runner persists outputs under `data/jobs/` and records audit trails linking experiments, datasets, and jobs.
- CLI commands surface module metadata so operators can discover available operations and their limitations.

## API
- Python package exports Experiment, Job, DatasetRef, AuditEvent, Signature, workflow helpers, and storage utilities under `labos.core`.
- Module registry API enables registering additional modules via `LABOS_MODULES` environment variable for plugin-style discovery.

## Tests
- Unit tests cover core dataclasses, module registry metadata, scientific stubs, and import provenance helpers (`tests/test_*`).
- Streamlit imports in UI components are guarded to allow headless test runs without requiring the UI runtime.
- `VALIDATION_LOG.md` tracks manual smoke runs alongside automated `python -m unittest` evidence.
