# Phases Overview

A staged roadmap describing how ChemLearn LabOS evolves from documentation to a fully operational lab operating system.

## Phase 0 — Bootstrap (Current)
- Establish repository structure, governance docs, and data directories.
- No executable logic beyond placeholders.

## Phase 1 — LabOS Core Foundations
- Implement experiment/job/dataset registries and provenance utilities.
- Stand up change/validation logging workflows.

## Phase 2 — Data & Provenance Services
- Formalize dataset ingestion, storage tiers, and audit pipelines.
- Introduce REPL/CLI tooling for orchestrating jobs end-to-end.

## Phase 3 — Scientific Modules Go Live
- Promote EI-MS and PChem stubs into runnable workflows and capture provenance across datasets/jobs.
- Bring OrgChem and Proteomics stubs online with validation scaffolds.
- Primary subsystems: `modules.eims`, `modules.pchem`, `modules.org_chem`, `modules.proteomics`, `core.labos`, CLI hooks for module execution.
- Key bots: EI-MS Module Bot, PChem Module Bot, OrgChem Module Bot, Proteomics Module Bot, Import & Provenance Bot, Testing & Validation Bot.

## Phase 4 — Simulation/3D + ML Explainability Layers
- Add simulation engine hooks plus 3D visualization/workspace pathways and align UI controls with new module outputs.
- Introduce ML explainability and guardrails that reuse module outputs and provenance streams.
- Primary subsystems: `modules.simulation`, `ui.workspace` (3D/visualization), `modules.ml_upgrade`, `ui.control_panel`, provenance overlays.
- Key bots: Simulation Engine Bot, Workspace & Visualization Bot, UI Integration Bot, ML Upgrade Bot, Testing & Validation Bot.

## Phase 5 — Advanced Orchestration & Integrations
- Tighten orchestration/CI for module pipelines, expand validation gates, and prepare optional external integrations.
- Harden CLI/automation, storage lifecycle policies, and compliance dashboards for multi-module runs.
- Primary subsystems: swarm orchestration docs, `cli`/automation, storage/persistence configs, compliance + validation evidence.
- Key bots: Swarm Orchestrator Bot, CLI & Interface Bot, Data & Storage Bot, Compliance & Legal Bot, Testing & Validation Bot.

## Phase 6+ — Clinical Deployment & SaMD Hardening
- Enforce Clinical Boundary Mode defaults, quality management hooks, and external audit readiness.
