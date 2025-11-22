# Swarm Status — Phase 2 Kickoff (2025-11-22)

## Current Phase Snapshot
- **Phase:** 2 (Working Lab Tool Skeleton)
- **Phase 1 highlights:** Core registries + audit hooks shipped; Control Panel renders mode-aware sections; ModuleRegistry carries placeholder EI-MS / P-Chem / import stubs with citations; tests cover dataclass serialization and registry wiring; CHANGELOG/VALIDATION logs active.

## Phase 2 Objectives
1. **Scientific Module Stubs (Scope A):** Flesh out EI-MS fragmentation, P-Chem calorimetry, and Import Wizard stubs with deterministic `run_*` helpers that emit `DatasetRef` + `AuditEvent` payloads and reference their module keys.
2. **Provenance Wiring (Scope B):** Ensure ModuleMetadata drives provenance everywhere—jobs/datasets display producing module IDs, and the Method & Data footer renders method name, citations, limitations sourced from the registry.
3. **Mode-Specific UI (Scope C):** Deepen Learner explanations/tooltips, streamline Lab mode for execution, and expose debug/raw data views in Builder mode.
4. **Tests & Validation (Scope D):** Add tests for the stubs and registry metadata, run them via unittest/pytest, and log new entries in `VALIDATION_LOG.md` + `CHANGELOG.md`.

## Bot / Role Focus
| Role | Phase 2 mandate | Notes |
| --- | --- | --- |
| Core Builder Bot | Light schema touches so jobs/datasets persist module provenance | Avoid breaking backward compatibility |
| Scientific Module Bot | Implement deterministic stub runners returning structured outputs | Keep parameters realistic + documented |
| UI Integration Bot | Render provenance + mode-specific UX cues in `labos/ui/control_panel.py` | Use expanders/tooltips to contain verbosity |
| Compliance & Academic Integrity Bot | Maintain citations (`CITATIONS.md`, `docs/REFERENCES.md`), update compliance logs | Ensure ModuleMetadata entries list citations + limitations |
| Testing & Validation Bot | Extend tests for stubs/registry and log runs in `VALIDATION_LOG.md` | Prefer deterministic fixtures |

## Outstanding Doc-Driven Tasks
1. **Scientific References:** `docs/REFERENCES.md` still carries a TODO; replace placeholders once real literature is selected. Keep `CITATIONS.md` synchronized.
2. **Development Guide Gap:** `DEVELOPMENT_GUIDE.md` is referenced but missing—either write it or clarify references.
3. **CLI Planning:** `UNIFIED_CLI_SPEC.md` defers the CLI until after Phase 2; keep requirements in view for future work.

## Near-Term Wave Plan
1. **Wave 2.1 – Metadata prep:** Verify whether ModuleMetadata needs extra fields for Phase 2 (e.g., `operation_examples`), and backfill any missing citation links.
2. **Wave 2.2 – Stub implementations:** Implement deterministic `run_*` helpers in EI-MS/P-Chem/Import stubs that return `DatasetRef` + `AuditEvent` dicts and reference module keys.
3. **Wave 2.3 – Provenance UI + tests:** Surface module provenance in Jobs/Datasets tables + footer; add tests that call each stub and assert structured outputs, then update `CHANGELOG.md` and `VALIDATION_LOG.md`.
