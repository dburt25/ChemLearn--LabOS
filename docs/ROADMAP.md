# Roadmap (High-Level)

Summarizes planned phases and focus areas for ChemLearn LabOS.

## Phase 0 — Bootstrap (Complete)
- Repo scaffolding, governance docs, and baseline directories established.

## Phase 1 — LabOS Core Builder (Complete)
- Experiment/job/dataset registries plus JSON storage + audit scaffolding landed.
- CHANGELOG + VALIDATION_LOG workflows in place.

## Phase 2 — Data & Provenance Services

### Phase 2.5.1 — Working Lab Skeleton (Complete)
- EI-MS, P-Chem, and Import Wizard deterministic stubs emit dataset/audit payloads; Control Panel exposes provenance-aware inspectors.
- CLI entry point (`labos/cli.py`) supports init/experiment/dataset/module commands; JSON file-store backs registries.
- CLI/registry skeleton, audit hooks, and learner/lab/builder UI copy are in place for downstream hardening.

### Phase 2.5.3 — Hardening & Contract Enforcement (Current)
- Workflow stabilization across CLI, registries, ModuleRegistry, and UI job runners.
- Module consolidation (EI-MS, spectroscopy) with metadata completion and contract enforcement.
- UI wiring for Run buttons plus CLI/API parity.
- Fixtures & compliance evidence to keep datasets/jobs/audits traceable.

## Phase 3 (Draft) — UX & Module Expansion
- Planning focus on richer UI/UX, learner modes, and broader module coverage; scheduling pending Phase 2.5.3 exit criteria.
- Target surfaces include enhanced control panel flows, learner guidance, and expanded scientific module catalogues.

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
