# Swarm Status – ChemLearn LabOS
This document summarizes where the bot swarm left LabOS: current phase, shipped surfaces, remaining Phase 2 work, and how to scope new agents safely. For a concise view of what is runnable today, see [`CURRENT_CAPABILITIES.md`](./CURRENT_CAPABILITIES.md).

## Current Phase
**Phase:** 2.5.3 – Hardening & Contract Enforcement (file-backed registries, CLI job runner, educational modules, Streamlit control panel)
- Bots 1–40 completed Phase 2.5.1 (working lab skeleton landed and promoted out of the experimental lane).
- Phase 2.5.3 wave is active; all bots must enforce the permissions matrix while tightening contracts.
- LabOS core models (Experiment, Job, DatasetRef, AuditEvent, ModuleMetadata) exist with JSON-backed storage and audit hooks.
- Deterministic EI-MS, P-Chem, and Import Wizard stubs return dataset/audit payloads and register via the ModuleRegistry metadata.
- Streamlit control panel + workspace shell deliver Learner/Lab/Builder modes with provenance previews and Method & Data footer fed by module metadata and audits.

### Phase 2.5.3 Objectives
- Workflow stabilization
- Module consolidation (EI-MS, spectroscopy)
- Metadata completion
- UI wiring for Run buttons
- CLI/API parity
- Fixtures & compliance

## Snapshot: What Exists Right Now
### Core (LabOS Engine)
- `labos.core` exports Experiment, Job, DatasetRef, AuditEvent, Signature, workflow helpers, and JSON storage for registries and job results.
- File-backed storage (`labos/storage.py`) and `LabOSConfig` create directories under `data/` (audit, experiments, jobs, datasets, feedback/examples).
- ModuleRegistry + metadata tables standardize module descriptors, citations, and limitations that feed UI footers and provenance inspectors.
- CLI entry point (`labos` command) supports init, experiment creation, dataset registration, and invoking registered module operations via the job runner.
- Audit logger + `record_event` helper produce chained JSONL logs per `docs/AUDIT_LOG_FORMAT.md`.

### Scientific Modules
- EI-MS fragmentation stub (`eims.fragmentation`) emits deterministic spectra metadata with dataset + audit references.
- P-Chem calorimetry stub (`pchem.calorimetry`) returns calorimetry placeholders for demos and provenance exercises.
- Import Wizard stub (`import.wizard`) infers schemas/previews, creates DatasetRefs, and falls back to deterministic sample rows when no data is supplied.
- Module metadata defaults live in `labos/core/module_registry.py`, aligning method names, citations, and limitations with UI display.

### UI / Control Panel
- Streamlit control panel renders Overview, Experiments, Jobs, Datasets, Modules, and Workspace tabs with Learner/Lab/Builder copy.
- Provenance inspectors show dataset/job tables, expandable JSON payloads, and Method & Data footer referencing ModuleMetadata + recent audits.
- Workspace / drawing tool offers mode-aware notes, file uploads, and hooks for future 3D visualization contracts documented in `THREED_VISUALIZATION_PLAN.md`.
- Run-button placeholders and TODO cues exist in Modules & Operations area while execution wiring stabilizes.

### Tests, Validation, and Compliance
- Unit suites cover core dataclasses, module registry metadata, scientific stubs, and import provenance helpers (see `tests/test_*`).
- `VALIDATION_LOG.md` records manual UI runs plus `python -m unittest` evidence; CHANGELOG mirrors major increments.
- Compliance artifacts (`COMPLIANCE_CHECKLIST.md`, `compliance-notes.md`, CLINICAL_BOUNDARY_MODE) document ALCOA expectations and research-only boundaries.
- Streamlit imports are guarded (control panel, workspace, provenance footer) so tests run headless; targeted smoke tests rely on mocked session state.

## Open Tasks for This Phase
- Complete end-to-end Experiment → Job → Module → Dataset/Audit wiring with helper APIs that persist job results back into registries.
- Consolidate EI-MS and spectroscopy descriptors/metadata so ModuleRegistry, audits, and UI footers stay aligned.
- Wire Run buttons + CLI pathways so UI actions and CLI commands consistently submit jobs and update registries.
- Harden JSON storage (locking, backups, checksum validation) and document dataset/URI conventions.
- Enforce Learner/Lab/Builder behavior (tooltips vs compact tables vs debug JSON) and ensure copy remains governance-aligned.
- Expand tests to cover workflows (`run_import_workflow`, provenance traces) and Streamlit rendering via harnesses or dependency injection.
- Install or vendor Streamlit in CI to unblock full `python -m unittest` without manual mocks.
- Centralize Getting Started instructions for students/lab operators pointing to CLI + UI entry points.
- Keep compliance docs + VALIDATION_LOG synchronized each time modules/UI/provenance behavior change.

## Active Bot Slots (Max 6 at a Time)

**Hard rule:**
At any given time, no more than **six** bots/agents should be running on this repo.
Each bot must be constrained to specific paths and responsibilities, and must NOT edit outside its lane.

| Bot Slot | Intent / Name (Example)       | Allowed Paths                                         | Forbidden Paths                         | Typical Tasks                                                |
| --- | --- | --- | --- | --- |
| 1 | Core Schema / Workflow Bot   | `labos/core/**`                                      | `labos/ui/**`, `labos/modules/**`               | Experiments/Jobs/Datasets/Audit models & orchestration      |
| 2 | EI-MS Module Bot             | `labos/modules/eims/**`, `docs/ei_ms/**`            | `labos/ui/**`, `labos/core/**`               | EI-MS fragmentation logic, helpers, docs                     |
| 3 | PChem Module Bot             | `labos/modules/pchem/**`, `docs/pchem/**`            | `labos/ui/**`, `labos/core/**`               | PChem calculators, error propagation, docs                   |
| 4 | UI / Control Panel Bot       | `labos/ui/**`                                        | `labos/core/**`, `labos/modules/**`               | Layout, modes (Learner/Lab/Builder), panels, workspace UX    |
| 5 | Testing & Validation Bot     | `tests/**`, `VALIDATION_LOG.md`, `BINARY_ASSET_HANDLING.md` | `labos/ui/**` (unless UI tests), core/module logic | Add/extend tests, record validation runs, test coverage      |
| 6 | Docs & Compliance Bot        | `README.md`, `docs/**`, `COMPLIANCE_CHECKLIST*.md`, `compliance-notes.md`, `DEVELOPMENT_GUIDE.md`, `VISION.md` | Any `*.py` files                                    | Update docs, checklists, dev guides, high-level notes        |


## Historical Notes
- Phase 0 bots created the repo scaffold, governance docs, compliance notes, and initial CHANGELOG/VALIDATION_LOG processes.
- Phase 1 delivered the LabOS core package, JSON audit logger, CLI skeleton, and placeholder tests for exported dataclasses.
- Early Phase 2 introduced deterministic EI-MS, P-Chem, and Import Wizard stubs plus ModuleMetadata feeding the Method & Data footer.
- Phase 2 Wave 2 expanded provenance helpers, Control Panel inspectors, and workspace hooks while documenting 3D visualization plans and Run-button TODOs.
- Phase 2 Wave 3 work-in-progress adds CLI refinements, storage abstraction, CI workflow, and import provenance tests to keep datasets/jobs traceable.
