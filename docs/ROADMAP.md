# Roadmap (High-Level)

Summarizes planned phases and focus areas for ChemLearn LabOS.

## Phase 0 — Bootstrap (Complete)
- Repo scaffolding, governance docs, and baseline directories established.

## Phase 1 — LabOS Core Builder (Complete)
- Experiment/job/dataset registries plus JSON storage + audit scaffolding landed.
- CHANGELOG + VALIDATION_LOG workflows in place.

## Phase 2 — Data & Provenance Services (In Progress)
- EI-MS, P-Chem, and Import Wizard deterministic stubs emit dataset/audit payloads; Control Panel exposes provenance-aware inspectors.
- CLI entry point (`labos/cli.py`) supports init/experiment/dataset/module commands; JSON file-store backs registries.
- Outstanding: enable full `python -m unittest` by installing/mocking `streamlit`, add Run buttons/CLI-to-UI bridge, and harden dataset promotion workflows.

## Phase 3 — Scientific Module Wave 1 (Next)
- Promote EI-MS/P-Chem/import flows into runnable pipelines with provenance links created by `labos/core/provenance.py`.
- Add CLI/Control Panel triggers that execute modules and emit Jobs/Datasets with validation fixtures.

## Phase 4 — Control Panel & Modes
- Expand Workspace/3D visualization, add task dashboards, and wire Clinical Boundary defaults into UI + CLI experiences.

## Phase 5 — Advanced Capabilities
- Ship proteomics + simulation modules, connect visualization layers, and activate ML upgrade plan.

## Phase 6+ — Clinical Hardening
- Enforce Clinical Boundary Mode, prepare QMS integrations, and finalize external audit playbooks.
