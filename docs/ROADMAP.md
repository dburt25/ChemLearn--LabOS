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
- Bring OrgChem + Proteomics stubs online with validation scaffolds while adding CLI/Control Panel triggers that emit Jobs/Datasets.
- Primary subsystems: `modules.eims`, `modules.pchem`, `modules.import_wizard`, `modules.org_chem`, `modules.proteomics`, provenance overlays.
- Key bots: EI-MS Module, PChem Module, OrgChem Module, Proteomics Module, Import & Provenance, Testing & Validation.

## Phase 4 — Control Surfaces, Simulation, and ML Explainability
- Expand Workspace/3D visualization, add task dashboards, wire Clinical Boundary defaults, and introduce simulation + ML guardrails.
- Primary subsystems: `ui.control_panel`, `ui.workspace` (3D), `modules.simulation`, `modules.ml_upgrade`, CLI run controls, storage/provenance connectors.
- Key bots: Simulation Engine, Workspace & Visualization, UI Integration, ML Upgrade, Testing & Validation.

## Phase 5 — Advanced Orchestration & Integrations
- Swarm orchestration/CI tightened, CLI/storage hardened, compliance dashboards prepared for external-facing runs.
- Focus on data/storage lifecycle policies, automation hooks, and governance documentation to support deployment planning.
- Key bots: Swarm Orchestrator, CLI & Interface, Data & Storage Integrity, Compliance & Legal, Testing & Validation.

## Phase 6+ — Clinical Hardening
- Enforce Clinical Boundary Mode, prepare QMS integrations, and finalize external audit playbooks.
