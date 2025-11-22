# ChemLearn LabOS

ChemLearn LabOS is a faith-aligned lab operating system that coordinates experiments, jobs, datasets, and scientific learning tools across a unified stack. The repository is currently in **Phase 0 (Bootstrap)**, which means only scaffolding, governance docs, and placeholders are being created—no production logic exists yet.

## Three-Layer Architecture
- **LabOS Core:** Orchestrates experiments, jobs, datasets, audit logging, and provenance workflows.
- **Scientific Modules:** Plug-in domain packs (PChem, EI-MS, proteomics, etc.) that extend the core with discipline-specific capabilities.
- **UI Layer:** Control panel and presentation shells for learners, lab operators, and builders.

## Phase 0 Scope
- Establish directory layout (`labos/`, `chemlearn_modules/`, `ui/`, `data/`, `docs/`, `tests/`).
- Draft governance documents (vision, invariants, swarm guides, schemas, compliance notes).
- Defer all executable logic, pipelines, and UI flows to later phases.

## Next Steps (Phase 1+ Preview)
1. Implement the LabOS Core package with experiment/job/dataset registries.
2. Define structured data stores and provenance tracking under `data/`.
3. Prototype the control panel shell and connect initial scientific modules.

## Binary Assets
Large artifacts exported from CODEX or similar tools must be tracked through Git Large File Storage (LFS). Install Git LFS locally, keep binaries under `artifacts/` or `datasets/`, and follow `docs/BINARY_ASSET_HANDLING.md` to stay within GitHub limits.