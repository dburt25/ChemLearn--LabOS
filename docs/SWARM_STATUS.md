# Swarm Status — Phase 2 Alignment (2025-11-22)

## Current Phase Snapshot
- **Phase:** 2 — Scientific stubs, provenance wiring, and mode-aware UI hardening.
- **Status:** Experiments/Jobs/Datasets/Audit registries operational; ModuleMetadata feeds Control Panel; EI-MS, P-Chem, and Import Wizard stubs emit deterministic dataset/audit payloads; CHANGELOG + VALIDATION_LOG carry Phase 2 entries; tests cover registries and stub outputs.

### Done So Far
- LabOS Core (experiments, jobs, datasets, audit) stabilized with ALCOA-friendly helpers.
- Streamlit Control Panel ships Learner/Lab/Builder modes, Workspace panel, and module metadata table.
- EI-MS, P-Chem, and Import Wizard stubs registered with provenance metadata plus unit tests.
- Swarm governance docs, permissions, and compliance logs actively maintained.

## Upcoming Phases

| Phase | Goal | Primary Subsystems |
| --- | --- | --- |
| 3 – Scientific Module Wave 1 | Promote EI-MS/PChem/import stubs into runnable pipelines, begin proteomics/org-chem prototyping. | modules.eims, modules.pchem, modules.import_wizard, modules.org_chem, modules.proteomics, core.labos |
| 4 – UI Control Surfaces | Expand Control Panel + Workspace (3D viz), add task-focused dashboards and CLI parity. | ui.control_panel, ui.workspace, cli.unified, swarm.orchestration |
| 5 – Advanced Modules & ML Upgrades | Introduce simulation engine, ML upgrade path, and advanced provenance dashboards. | modules.simulation, modules.ml_upgrade, knowledge feeds, compliance |
| 6 – Clinical Hardening | Enforce Clinical Boundary Mode defaults, external audit readiness, QMS integration. | compliance.docs, core.labos, data/storage |

## Phase 2 Wave Plan

- **Wave 1 (Complete):** Bots — Core Builder, Scientific Module, UI Integration, Testing & Validation. Delivered deterministic stubs + metadata UI.
- **Wave 2 (In Flight):** Bots — Import & Provenance, UI Integration, Workspace & Visualization, Testing & Validation. Objectives: wire stub outputs into jobs/datasets, expose provenance across UI, harden workspace hooks, and expand regression coverage.
- **Wave 3 (Queued):** Bots — CLI & Interface, Swarm Orchestrator, Data & Storage, Testing & Validation. Objectives: add Run buttons + CLI hooks, ensure data ingestion paths promote datasets, expand validation coverage.

### Concurrency Guidance (Phase 2)
- Waves 1–2 can run up to four bots in parallel so long as only one bot edits a given path as defined in `SWARM_PERMISSIONS_MATRIX.md` (e.g., UI Integration vs Workspace Bot coordinate before touching `labos/ui/*`).
- Compliance & Legal Bot runs serially at the end of each wave to close logs and check regulatory impacts.

## Phase 3 Preview — Scientific Module Wave 1

- **Wave A (Kickoff):** Bots — EI-MS Module, PChem Module, Import & Provenance, Testing & Validation. Goal: promote stubs into runnable workflows, capture datasets/jobs/audits end-to-end.
- **Wave B:** Bots — Proteomics Module, OrgChem Module, Simulation Engine. Goal: baseline new domain plans with schemas + validation scaffolds.
- **Wave C:** Bots — UI Integration, CLI & Interface, Compliance & Legal. Goal: surface new module controls, document governance, update permissions per new domains.

Keep this status document synchronized with `MASTER_BLUEPRINT_INDEX.md`, `SWARM_PLAYBOOK.md`, and `SWARM_PERMISSIONS_MATRIX.md` whenever roles or schedules change.

## Wave 2 Execution Blueprint

| Bot | Directory Scope | Tasks | Human Verification |
| --- | --- | --- | --- |
| Import & Provenance Bot | `labos/modules/import_wizard/*`, `labos/core/provenance.py`, `labos/core/module_registry.py`, `labos/core/workflows.py`, `tests/test_scientific_modules.py` | 1) Add helpers to promote module stub outputs into Jobs/Datasets with provenance links; 2) Ensure Import Wizard summary returns both legacy `audit` and new richer schema preview; 3) Update module metadata/provenance docs as needed. | `& .venv/Scripts/python.exe -m unittest tests.test_scientific_modules tests.test_module_registry`; review updated datasets/jobs JSON if generated. |
| UI Integration Bot | `labos/ui/control_panel.py`, `labos/ui/__init__.py`, provenance footer helper (if added) | 1) Surface provenance details (dataset/audit preview, module metadata) in Jobs/Datasets panels; 2) Add TODO placeholders for Run buttons; 3) Keep mode-specific copy aligned with governance docs. | `& .venv/Scripts/python.exe -m unittest tests.test_module_registry`; optional `streamlit run app.py` smoke check. |
| Workspace & Visualization Bot | `labos/ui/drawing_tool.py`, `docs/THREED_VISUALIZATION_PLAN.md`, `docs/METHOD_AND_DATA.md` | 1) Keep workspace generic but add hooks for linking scratchpad notes/files to experiments; 2) Document upcoming 3D visualization data contract; 3) Avoid altering other UI sections without coordination. | Manual review via `streamlit run app.py` (Workspace tab) and lint doc changes. |
| Testing & Validation Bot | `tests/*`, `VALIDATION_LOG.md`, `CHANGELOG.md` (test notes) | 1) Expand tests covering provenance helpers and UI shims (Streamlit harness); 2) Ensure deterministic fixtures for Import Wizard / Control Panel; 3) Log executed suites and evidence in `VALIDATION_LOG.md`. | After bot completes, rerun `& .venv/Scripts/python.exe -m unittest tests.test_scientific_modules tests.test_module_registry`; verify validation log entries. |

### Wave 2 Prompts (for Codex bots)
1. **Import & Provenance Bot Prompt:** “Phase 2 – Wave 2: Wire stub outputs (EI-MS, P-Chem, Import Wizard) into job/dataset provenance. Touch only `labos/modules/import_wizard`, `labos/core/provenance.py`, `labos/core/workflows.py`, `labos/core/module_registry.py`, and relevant tests. Ensure `run_import_stub` stays backward compatible while exposing richer helper(s). Add tests proving datasets/audit linkage.”
2. **UI Integration Bot Prompt:** “Phase 2 – Wave 2 UI: In `labos/ui/control_panel.py` (and helpers) surface dataset/audit provenance for Jobs and Datasets tables, enhance the Method & Data footer, and leave TODO cues for Run buttons. Coordinate with Workspace Bot; do not modify drawing_tool.py. Update tests if Control Panel imports change.”
3. **Workspace & Visualization Bot Prompt:** “Phase 2 – Wave 2 Workspace: Keep `labos/ui/drawing_tool.py` generic while adding hooks to link scratchpad uploads/notes to experiments for future provenance. Document the visualization contract in `THREED_VISUALIZATION_PLAN.md` or `METHOD_AND_DATA.md`. Avoid changes outside workspace scope.”
4. **Testing & Validation Bot Prompt:** “Phase 2 – Wave 2 Testing: Extend `tests/*` to cover provenance helpers and Control Panel stubs, refresh Streamlit harness if needed, and document executed suites in `VALIDATION_LOG.md`. Do not modify runtime logic except where tests require helper shims.”

### Post-Wave Validation Sequence
1. Run targeted tests: `& .venv/Scripts/python.exe -m unittest tests.test_scientific_modules tests.test_module_registry`.
2. Launch Control Panel (`streamlit run app.py`) to verify provenance UI changes.
3. Review Workspace tab manually for new hooks/notes.
4. Confirm `VALIDATION_LOG.md` reflects executed suites and `CHANGELOG.md` captures Wave 2 highlights (via Testing Bot or follow-up Compliance Bot).
