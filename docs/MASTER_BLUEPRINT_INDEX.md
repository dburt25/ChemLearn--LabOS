# Master Blueprint Index

This index connects every LabOS macro-plan so future swarm agents can find the right reference quickly.

## Core Strategy Docs
- `VISION.md` — north star intents and beneficiaries.
- `ChemLearn-The-Universal-Chemistry-Learning-and-Discovery-Engine.md` — high-level overview for new collaborators.
- `INVARIANTS.md` — non-negotiable rules the system must obey.
- `PHASES_OVERVIEW.md` — staged roadmap for the entire build.
- `DEVELOPMENT_VISION_GUIDE.md` — execution principles derived from the vision.

## Governance & Swarm Ops
- `SWARM_PLAYBOOK.md`
- `SWARM_PERMISSIONS_MATRIX.md`
- `SWARM_GOVERNANCE.md`
- `SWARM_BOOT_PROCEDURE.md`
- `COMPLIANCE_CHECKLIST.md`

## Architecture & Schemas
- `README_ARCHITECTURE.md`
- `DATA_ARCHITECTURE.md`
- `EXPERIMENT_SCHEMA.md`
- `JOB_SCHEMA.md`
- `AUDIT_LOG_FORMAT.md`

## Specialized Plans
- Capability and module plans under `docs/*PLAN.md`
- Compliance artifacts (`compliance-notes.md`, `RESEARCH_USE_ONLY.md`, etc.)
- CHANGELOG/VALIDATION_LOG at repo root capture incremental evidence.

## Usage Notes
- Keep this index alphabetized within each section when adding new blueprints.
- Link out to external references in `REFERENCES.md` instead of duplicating content here.

## Subsystem Catalog

| Subsystem ID | Description | Primary Docs | Primary Code Directories |
| --- | --- | --- | --- |
| core.labos | Experiment, job, dataset, and audit registries plus runtime glue. | `DATA_ARCHITECTURE.md`, `EXPERIMENT_SCHEMA.md`, `JOB_SCHEMA.md`, `WORKFLOWS_OVERVIEW.md` | `labos/core/*`, `labos/experiments.py`, `labos/jobs.py`, `labos/datasets.py` |
| core.provenance | Module metadata registry and provenance services feeding Method & Data surfaces. | `MODULARITY_GUIDELINES.md`, `METHOD_AND_DATA.md`, `SWARM_STATUS.md` | `labos/core/module_registry.py`, `labos/core/provenance.py` |
| ui.control_panel | Streamlit Control Panel covering Learner/Lab/Builder modes, module inspector, and provenance footer. | `VISION.md`, `PHASES_OVERVIEW.md`, `WORKFLOWS_OVERVIEW.md` | `labos/ui/control_panel.py`, `labos/ui/__init__.py` |
| ui.workspace | Workspace / drawing scratchpad and upcoming 3D visualization shell. | `THREED_VISUALIZATION_PLAN.md`, `VISION.md` | `labos/ui/drawing_tool.py`, future `ui/workspace/*` |
| modules.eims | EI-MS fragmentation educational stub + future mass-spectrometry engine. | `MODULARITY_GUIDELINES.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md`, `ORG_CHEM_DESIGN_MODULE.md` | `labos/modules/eims/*`, future `chemlearn_modules/eims/*` |
| modules.pchem | Calorimetry + thermodynamic tooling. | `MODULARITY_GUIDELINES.md`, `PHASES_OVERVIEW.md` | `labos/modules/pchem/*`, future `chemlearn_modules/pchem/*` |
| modules.import_wizard | Data onboarding helpers, schema inference, and provenance logging. | `DATA_ARCHITECTURE.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md` | `labos/modules/import_wizard/*` |
| modules.org_chem | Organic chemistry design/teaching module under development. | `ORG_CHEM_DESIGN_MODULE.md` | planned `labos/modules/org_chem/*`, `chemlearn_modules/org_chem/*` |
| modules.proteomics | Proteomics analysis workflows (digestion planning, spectra scoring). | `PROTEOMICS_MODULE_PLAN.md` | planned `labos/modules/proteomics/*`, `chemlearn_modules/proteomics/*` |
| modules.simulation | Future simulation engine bridging experiments and modeling. | `SIMULATION_ENGINE_VISION.md`, `PHASES_OVERVIEW.md` | planned `labos/modules/simulation/*`, `chemlearn_modules/simulation/*` |
| modules.ml_upgrade | Machine-learning upgrade path for future adaptive features. | `ML_UPGRADE_PLAN.md`, `SCIENTIFIC_KNOWLEDGE_FEED_PLAN.md` | planned `labos/modules/ml/*`, `ml/` services |
| cli.unified | Unified CLI entry point for experiments/jobs/modules. | `UNIFIED_CLI_SPEC.md`, `SWARM_BOOT_PROCEDURE.md` | `labos/cli.py`, future `cli/*` |
| swarm.orchestration | Bot governance, permissions, and scheduling artifacts. | `SWARM_GOVERNANCE.md`, `SWARM_PLAYBOOK.md`, `SWARM_PERMISSIONS_MATRIX.md`, `SWARM_STATUS.md` | `docs/` governance set |
| compliance.docs | Regulatory, audit, and legal alignment references. | `COMPLIANCE_CHECKLIST.md`, `compliance-notes.md`, `VALIDATION_LOG.md`, `CHANGELOG.md` | `docs/`, root logs |
