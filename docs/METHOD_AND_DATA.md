# Method & Data Provenance (Phase 2 Placeholder)

The `ModuleRegistry` keeps a lightweight record of each scientific stub so the Control Panel and future APIs can display "ⓘ Method & Data" details consistently.

## Purpose
- Centralize module descriptors (name, version, method summary) for provenance.
- Provide placeholders for citations and dataset sources until peer-reviewed references are selected.
- Ensure limitations are explicit so users treat the stubs as educational scaffolding.

## Required Fields per Module
Every module entry must declare:
- **Name & key:** Human-friendly `display_name` plus a stable `key` (e.g., `eims.fragmentation`).
- **Method name:** Short phrase users will recognize in provenance tooltips.
- **Citation:** Link text pointing to `CITATIONS.md` until real references are added.
- **Dataset sources:** Brief placeholder text noting expected data provenance.
- **Limitations:** Always state: "Method stub. Educational use only. Not validated for clinical decisions."

## Workflow Notes
- Update `CITATIONS.md` whenever a module gains or changes references; set `primary_citation` to point at the relevant section.
- Keep dataset provenance statements in sync with `dataset_citations` so audit logs can surface expected inputs.
- When modules move beyond placeholders, add validation evidence to `VALIDATION_LOG.md` and note user-visible changes in `CHANGELOG.md`.
