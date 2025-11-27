# Workflows Overview

Describes the canonical flows that LabOS will support.

## Experiment Lifecycle
1. Define experiment metadata.
2. Attach jobs and datasets.
3. Execute jobs via CLI/UI.
4. Record outcomes and audit logs (including module keys from the ModuleRegistry).

## Job Lifecycle
- Queue → Run → Complete/Fail → Archive.
- Status transitions must be auditable and deterministic.

## Dataset Lifecycle
- Ingest → Validate → Version → Publish → Retire.
- All datasets linked back to originating experiments and jobs.
- Import Wizard ingests create both `DatasetRef` and `AuditEvent` records so provenance is captured up front.

## Feedback Loop
- Learner/lab feedback stored under `data/feedback/` and reviewed for roadmap updates.
- Feedback linked to module keys (e.g., `pchem.ideal_gas`, `spectroscopy.ir`) to trace which methods drove the experience.
