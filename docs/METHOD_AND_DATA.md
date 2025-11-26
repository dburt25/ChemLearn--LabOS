# Method & Data Provenance (Phase 2 Placeholder)

The `ModuleRegistry` keeps a lightweight record of each scientific stub so the Control Panel and future APIs can display "ⓘ Method & Data" details consistently. It is the single source of truth for footers and provenance badges across EI-MS, P-Chem, spectroscopy, and import helpers.

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

### Built-in keys tracked in Phase 2

- `eims.fragmentation` — EI-MS fragmentation placeholder
- `ei_ms.basic_analysis` — EI-MS heuristic peak tagging
- `pchem.calorimetry` — constant-pressure calorimetry stub
- `pchem.ideal_gas` — PV = nRT solver with single unknown
- `spectroscopy.nmr` — NMR schema annotator (stub)
- `spectroscopy.ir` — IR schema annotator (stub)
- `import.wizard` — schema-guided import helper

## Workflow Notes
- Update `CITATIONS.md` whenever a module gains or changes references; set `primary_citation` to point at the relevant section.
- Keep dataset provenance statements in sync with `dataset_citations` so audit logs can surface expected inputs.
- When modules move beyond placeholders, add validation evidence to `VALIDATION_LOG.md` and note user-visible changes in `CHANGELOG.md`.

## Workspace Artifacts (Phase 2 Hook)
- Workspace notes, uploads, and experiment tags count as "Method & Context" data that should be linked to Experiments/Jobs when persistence arrives.
- During Phase 2, the Streamlit UI exposes hooks to capture notes, reference images, and Experiment IDs, but storage and lineage APIs are not wired yet.
- When persistence lands, those captured tags will be stored alongside Dataset/Experiment metadata so 3D overlays and future viewers can pull the right annotations.
