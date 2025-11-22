# Changelog

All notable changes will be documented in this file per `CHANGE_TYPES.md`.

## [0.1.0] - 2025-11-22
### Added
- LabOS Core Python package with configuration loader, audit logger, registries, runtime facade, and CLI entry point.
- JSONL audit log implementation with chained checksums as described in `docs/AUDIT_LOG_FORMAT.md`.
- File-backed dataset, experiment, and job registries plus a job runner that enforces experiment/job pairing.
- Minimal CLI commands: `labos init`, `labos new-experiment`, `labos register-dataset`, and `labos run-module`.
- Foundational documentation set (Development Vision Guide, Compliance Checklist, universal overview) to satisfy global context requirements.
- Editable packaging (`pyproject.toml`) and unit tests covering registries and job execution.

## [0.1.1] - 2025-11-22
### Fixed
- Ensured `render_control_panel()` executes when `streamlit run app.py` is invoked so the Control Panel always renders.
- Added a placeholder core smoke test that instantiates the exported Phase 0 dataclasses to guard against regressions.

## [0.1.2] - 2025-11-22
### Added
- `audit.record_event()` helper so bots can emit ALCOA-friendly JSONL entries without wiring an `AuditLogger` manually.
- Stub `Signature` dataclass plus BaseRecord hooks to capture intent/time/evidence for future electronic signatures.
### Changed
- Registries now attach audit event IDs back onto Experiment, Dataset, and Job records for traceability.
- Compliance docs (checklist, notes, validation log) updated to reflect ModuleRegistry provenance expectations and Phase 1 workflow.

## [0.1.3] - 2025-11-22
### Added
- `docs/SWARM_STATUS.md` capturing the Phase 1 documentation review (vision, compliance, provenance) plus outstanding tasks for references, development guide authorship, and future CLI work.

## [0.1.4] - 2025-11-22
### Added
- Workspace / Drawing Tool section in the Control Panel with a new `labos/ui/drawing_tool.py` module providing a mode-aware scratchpad and file upload placeholder for future canvas integration.

## [0.2.0] - 2025-11-22
### Added
- Phase 2 Wave 1: deterministic EI-MS, P-Chem, and Import Wizard stubs under `labos/modules/**` that emit structured dataset/audit metadata and register as module operations.
- Module metadata defaults (including Import Wizard) surfaced in the Control Panel to show method names, placeholder citations, and limitations for each stub.
### Changed
- `tests/test_module_registry.py` now asserts the Phase 2 metadata entries and provides a lightweight Streamlit stub so registry tests run without UI dependencies.

## [0.2.1] - 2025-11-22
### Added
- Reworked `CITATIONS.md` with explicit placeholder sections for EI-MS, P-Chem/calorimetry, and data import handling.
- Added `docs/METHOD_AND_DATA.md` describing ModuleRegistry provenance expectations and required metadata fields.
### Changed
- Updated module metadata defaults to reference `CITATIONS.md` and standardized limitations to the educational-only disclaimer.
- Data Import Wizard helpers that infer schemas for in-memory tables, emit DatasetRef metadata, and generate audit events for imports.
- Provenance utilities to link imported datasets to experiments and trace lineage in-memory.
- Workflow helpers for pairing experiments, jobs, datasets, and audit events via `labos/core/workflows.py`.

## [0.2.2] - 2025-11-22
### Added
- Phase 2 – Wave 2 UI updates: Jobs table shows linked dataset previews and audit context, and Datasets table surfaces schema/module hints with mode-aware explanations.
- Method & Data footer now renders ModuleMetadata alongside recent audits with learner/lab/builder-specific messaging.
- Disabled Run buttons and TODO hooks placed near module and job controls in preparation for execution wiring.
