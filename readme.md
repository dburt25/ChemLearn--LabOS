# ChemLearn LabOS

ChemLearn LabOS is a multi-layer lab operating system for managing experiments, jobs, and datasets while coordinating scientific modules and user interfaces. This repository is currently in **Phase 0: Bootstrap**, focused on establishing structure and documentation only.

## Architecture Layers
- **LabOS Core**: orchestrates experiments, jobs, datasets, and auditability.
- **Scientific Modules**: domain-specific extensions (e.g., PChem, EI-MS, proteomics) that plug into the core.
- **UI Layer**: presentation shell to serve learners, lab operators, and builders.

## Current Status
This phase lays down folders, placeholder packages, and governance documentation. No scientific logic, data processing, or UI features are implemented yet.

## Legacy Note
The repository previously served as a lightweight lab scratchpad. Prior notes and workflows can be referenced from historical commits as needed.

## Binary Assets
Large artifacts exported from CODEX or similar tools must be tracked through Git Large File Storage (LFS). Install Git LFS locally, keep binaries under `artifacts/` or `datasets/`, and follow the workflow documented in `docs/BINARY_ASSET_HANDLING.md` to stay within GitHub limits.