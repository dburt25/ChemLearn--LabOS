# Experiment Schema (Draft)

Defines the canonical fields for representing experiments inside LabOS.

## Field Overview
- `experiment_id` (UUID) — immutable identifier.
- `title` — human-readable label.
- `purpose` — scientific or educational objective.
- `created_at` / `updated_at` — timezone-aware timestamps.
- `owner` — user or bot responsible.
- `inputs` — structured list of reagents, datasets, or parameters.
- `expected_outcomes` — hypotheses or success criteria.

## Constraints & Validation
- IDs must be unique across the platform.
- Times recorded in ISO 8601 with timezone offsets.
- Inputs reference versioned datasets/jobs only.

## Logging & Traceability
- Experiments link to child jobs, datasets, and audit entries.
- Changes recorded in append-only history per ALCOA+.
