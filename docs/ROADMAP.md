# Roadmap (High-Level)

Summarizes planned phases and focus areas for ChemLearn LabOS.

## Phase 0 — Bootstrap (Now)
- Establish repo scaffolding, docs, governance, and directories.

## Phase 1 — LabOS Core Builder
- Implement experiment/job/dataset registries.
- Stand up change logging + validation templates.

## Phase 2 — Data & Provenance Services
- Build ingestion APIs, dataset versioning, and provenance storage.
- Deliver unified CLI alpha.

## Phase 3 — Scientific Modules Go Live
- EI-MS and PChem pipelines runnable with provenance; OrgChem + Proteomics stubs executing with validation scaffolds.
- Primary subsystems: `modules.eims`, `modules.pchem`, `modules.org_chem`, `modules.proteomics`, CLI module runners, provenance overlays.
- Key bots: EI-MS Module Bot, PChem Module Bot, OrgChem Module Bot, Proteomics Module Bot, Import & Provenance Bot, Testing & Validation Bot.

## Phase 4 — Simulation/3D + ML Explainability Layers
- Simulation engine and 3D workspace/visualization aligned with module outputs; ML explainability/guardrails introduced.
- Primary subsystems: `modules.simulation`, `ui.workspace` (3D), `modules.ml_upgrade`, `ui.control_panel`, storage/provenance connectors.
- Key bots: Simulation Engine Bot, Workspace & Visualization Bot, UI Integration Bot, ML Upgrade Bot, Testing & Validation Bot.

## Phase 5 — Advanced Orchestration & Integrations
- Swarm orchestration/CI tightened, CLI/storage hardened, compliance dashboards prepared for external-facing runs.
- Primary subsystems: swarm orchestration docs, `cli`/automation, data/storage lifecycle policies, compliance + validation evidence.
- Key bots: Swarm Orchestrator Bot, CLI & Interface Bot, Data & Storage Bot, Compliance & Legal Bot, Testing & Validation Bot.

## Phase 6+ — Clinical Hardening
- SaMD readiness, external audits, deployment Runbooks.
