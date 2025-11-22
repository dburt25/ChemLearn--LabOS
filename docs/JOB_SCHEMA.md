# Job Schema (Draft)

Jobs are executable steps derived from experiments.

## Field Overview
- `job_id` (UUID)
- `experiment_id` (foreign key)
- `status` (queued/running/completed/failed/aborted)
- `parameters` (structured JSON with deterministic ordering)
- `artifacts` (references to datasets or binary outputs tracked via LFS)
- `logs` (pointer to audit entries)
- `runtime_metrics` (duration, resource usage)

## Constraints
- Status transitions follow approved workflow (see `WORKFLOWS_OVERVIEW.md`).
- Parameters must include provenance metadata (seed, software versions).

## Traceability
- Each job writes to `AUDIT_LOG_FORMAT.md` schema upon state changes.
- Failures require RCA entries in `compliance-notes.md`.
