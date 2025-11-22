# Swarm Playbook

Operating procedures for coordinating multiple ChemLearn LabOS bots.

## Role Declaration
- Each bot states its role, scope, and forbidden zones before editing.
- Roles link to `SWARM_PERMISSIONS_MATRIX.md` for quick reference.

## Collaboration Cycle
1. Read latest docs and open issues.
2. Draft a plan with scoped tasks and compliance considerations.
3. Execute minimal, reviewable changes.
4. Update CHANGELOG, validation notes, and relevant docs.

## Communication Norms
- Prefer deterministic, reproducible instructions.
- Highlight blockers and dependencies explicitly.
- Assume concurrent bots: avoid massive refactors without coordination.

## Safety Rules
- No deletion of artifacts without audit trail.
- All code changes accompanied by tests (once phases allow).
- Sensitive data never leaves secure storage paths.

## Bot Roster

| Bot Name | Purpose | Subsystems Owned | Primary Docs | Allowed Code Areas |
| --- | --- | --- | --- | --- |
| Core Builder Bot | Maintain core experiment/job/dataset registries and provenance helpers without breaking compatibility. | core.labos, core.provenance | `VISION.md`, `DATA_ARCHITECTURE.md`, `EXPERIMENT_SCHEMA.md`, `JOB_SCHEMA.md`, `WORKFLOWS_OVERVIEW.md` | `labos/core/*`, `labos/experiments.py`, `labos/jobs.py`, `labos/datasets.py` |
| UI Integration Bot | Advance the Streamlit Control Panel (Learner/Lab/Builder) and provenance displays. | ui.control_panel | `VISION.md`, `PHASES_OVERVIEW.md`, `WORKFLOWS_OVERVIEW.md` | `labos/ui/*` |
| Workspace & Visualization Bot | Grow workspace/drawing tools and future 3D visualization pathways. | ui.workspace | `THREED_VISUALIZATION_PLAN.md`, `VISION.md` | `labos/ui/drawing_tool.py`, planned `ui/workspace/*` |
| EI-MS Module Bot | Own EI-MS fragmentation stubs and future production engine. | modules.eims | `MODULARITY_GUIDELINES.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md` | `labos/modules/eims/*`, `chemlearn_modules/eims/*` |
| PChem Module Bot | Deliver calorimetry and thermodynamic tooling with validation packs. | modules.pchem | `MODULARITY_GUIDELINES.md`, `PHASES_OVERVIEW.md` | `labos/modules/pchem/*`, `chemlearn_modules/pchem/*` |
| Import & Provenance Bot | Maintain Import Wizard helpers plus dataset/audit linkage tooling. | modules.import_wizard, core.provenance | `DATA_ARCHITECTURE.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md`, `METHOD_AND_DATA.md` | `labos/modules/import_wizard/*`, `labos/core/provenance.py`, `labos/core/module_registry.py` |
| Proteomics Module Bot | Plan and implement proteomics workflows once storage + validation ready. | modules.proteomics | `PROTEOMICS_MODULE_PLAN.md`, `MODULARITY_GUIDELINES.md` | `labos/modules/proteomics/*`, `chemlearn_modules/proteomics/*` |
| OrgChem Module Bot | Build organic chemistry design/teaching module safely. | modules.org_chem | `ORG_CHEM_DESIGN_MODULE.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md` | `labos/modules/org_chem/*`, `chemlearn_modules/org_chem/*` |
| Simulation Engine Bot | Architect simulation services and link them to experiments/jobs. | modules.simulation | `SIMULATION_ENGINE_VISION.md`, `WORKFLOWS_OVERVIEW.md` | `labos/modules/simulation/*`, supporting `labos/runtime.py` hooks |
| ML Upgrade Bot | Coordinate explainable ML improvements and guardrails. | modules.ml_upgrade | `ML_UPGRADE_PLAN.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md` | `labos/modules/ml/*`, ML tooling directories |
| CLI & Interface Bot | Build Unified CLI and related docs/tests. | cli.unified | `UNIFIED_CLI_SPEC.md`, `SWARM_BOOT_PROCEDURE.md` | `labos/cli.py`, `cli/*`, CLI tests |
| Compliance & Legal Bot | Keep compliance docs, citations, and validation evidence synchronized. | compliance.docs, swarm.orchestration | `COMPLIANCE_CHECKLIST.md`, `compliance-notes.md`, `SWARM_GOVERNANCE.md` | `docs/` governance set, `CHANGELOG.md`, `VALIDATION_LOG.md` |
| Testing & Validation Bot | Extend unit/integration tests and ensure logs capture results. | tests infrastructure across subsystems | `REPO_HEALTH_CHECKLIST.md`, `VALIDATION_LOG.md`, `SWARM_STATUS.md` | `tests/*`, `CHANGELOG.md`, `VALIDATION_LOG.md` |
| Data & Storage Bot | Manage dataset folders, storage tier docs, and provenance artifacts. | data architecture | `DATA_ARCHITECTURE.md`, `FUTURE_DISCOVERIES_PIPELINE.md` | `data/*`, `docs/DATA_ARCHITECTURE.md`, storage configs |
| Swarm Orchestrator Bot | Coordinates scheduling, permissions, and wave planning. | swarm.orchestration | `SWARM_GOVERNANCE.md`, `SWARM_PERMISSIONS_MATRIX.md`, `SWARM_STATUS.md` | `docs/` swarm files only |

### Wave 2 Assignments

| Bot | Wave 2 Focus | Directory Scope |
| --- | --- | --- |
| Import & Provenance Bot | Wire stub outputs (EI-MS/P-Chem/Import) into job/dataset records, expand provenance helpers/docstrings. | `labos/modules/import_wizard/*`, `labos/core/provenance.py`, `labos/core/module_registry.py`, `labos/core/workflows.py` |
| UI Integration Bot | Expose provenance details (dataset/audit previews, method footer) across Control Panel sections. | `labos/ui/control_panel.py` (coordinate with Workspace Bot), `labos/ui/__init__.py` |
| Workspace & Visualization Bot | Keep workspace/drawing tool generic while adding hints for future 3D tools; prep data structures for upcoming visualization modules. | `labos/ui/drawing_tool.py`, related docs |
| Testing & Validation Bot | Extend tests covering provenance wiring and module stubs; log results in validation docs. | `tests/*`, `VALIDATION_LOG.md`, supporting fixtures |

Each bot should reference the prompts in the Wave 2 planning section (below) before editing.
