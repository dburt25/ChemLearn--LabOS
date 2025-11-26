# Method & Data Provenance (Phase 2.5.3)

The `ModuleRegistry` is the canonical source for Method & Data entries that surface in UI tooltips and audit payloads. Each registry record pairs a stable key with user-facing naming, citations, and explicit limitations so downstream workflows can reason about provenance consistently.

## Required Fields per Module
Every module entry must declare:
- **Name & key:** Human-friendly `display_name` plus a stable `key` (e.g., `ei_ms.basic_analysis`).
- **Method name:** Short phrase users will recognize in provenance tooltips.
- **Citation:** Link text pointing to `CITATIONS.md` until peer-reviewed references are selected.
- **Dataset sources:** Brief placeholder text noting expected data provenance.
- **Limitations:** Always state: "Method stub. Educational use only. Not validated for clinical decisions."

## Current Registry Entries
| Key | Human name | Summary | Primary citation | Educational / limitations note |
| --- | --- | --- | --- | --- |
| `pchem.calorimetry` | P-Chem Calorimetry | Emits deterministic calorimetry metadata for demos; no thermodynamics are computed. | See CITATIONS.md (P-Chem calorimetry placeholder). | Stub output only; educational/demo use. |
| `pchem.ideal_gas` | Ideal Gas Solver | Solves PV = nRT with light unit handling for one missing variable. | See CITATIONS.md (Ideal gas placeholder). | Assumes ideal gas behavior; educational only. |
| `ei_ms.basic_analysis` | EI-MS Basic Analysis | Heuristic EI-MS tagging for base peaks, major fragments, and neutral losses without physics modeling. | See CITATIONS.md (Mass spectrometry placeholder). | Deterministic heuristic; not validated; no instrument response modeling. |
| `spectroscopy.nmr` | NMR Schema Stub | NMR contract stub returning schemas and echoed peaks for future spectral reasoning. | See CITATIONS.md (Spectroscopy placeholder). | Schema scaffold only; no spectral interpretation. |
| `spectroscopy.ir` | IR Schema Stub | IR contract stub describing peak/band schema and placeholder annotations. | See CITATIONS.md (Spectroscopy placeholder). | Schema scaffold only; no vibrational analysis. |
| `import.wizard` | Import Wizard | Schema-guided dataset onboarding that emits DatasetRefs and AuditEvents for ingests. | See CITATIONS.md (Data import placeholder). | Educational stub; provenance wiring only; no persistence yet. |

## Workflow Notes
- Update `CITATIONS.md` whenever a module gains or changes references; set `primary_citation` to point at the relevant section.
- Keep dataset provenance statements in sync with `dataset_citations` so audit logs can surface expected inputs.
- When modules move beyond placeholders, add validation evidence to `VALIDATION_LOG.md` and note user-visible changes in `CHANGELOG.md`.

## Workspace Artifacts (Phase 2 Hook)
- Workspace notes, uploads, and experiment tags count as "Method & Context" data that should be linked to Experiments/Jobs when persistence arrives.
- During Phase 2, the Streamlit UI exposes hooks to capture notes, reference images, and Experiment IDs, but storage and lineage APIs are not wired yet.
- When persistence lands, those captured tags will be stored alongside Dataset/Experiment metadata so 3D overlays and future viewers can pull the right annotations.
