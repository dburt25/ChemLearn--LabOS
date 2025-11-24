# Compliance Notes

## Current Focus
- Reinforce provenance capture across module registry entries (method source, dataset lineage, versioned configs).
- Emphasize DatasetRef + AuditEvent usage to preserve ALCOA-compliant trails for transformations and outputs.
- Keep all outputs labeled research/education-only; future clinical considerations must remain clearly non-clinical for now.

## Source Attribution & Licensing
- Cite external methods/datasets with persistent identifiers (DOI/URL) and list license terms where available.
- Prefer summarizing third-party content rather than copying verbatim; include links to upstream documentation.
- Track compatibility of external licenses with repository distribution.

## Dataset Handling
- Record dataset origin, consent/usage limits, preprocessing steps, and downstream consumers in audit logs.
- Require DatasetRef attachments for ingestion, training, and evaluation steps; store hash/signatures when feasible.
- Note any synthetic or simulated data explicitly and avoid implying real-world validation.

## Future Clinical Use (non-clinical now)
- No diagnostic or treatment claims; clearly state research-only scope.
- Document what additional validation/regulatory reviews would be required before any clinical use.
- Add cautionary language near outputs that resemble clinical assessments to prevent misuse.

## Action Items
- Update COMPLIANCE_CHECKLIST.md when new modules/datasets are added to track provenance requirements.
- Cross-link VALIDATION_LOG.md entries with compliance updates where tests and documentation move together.
- Keep citations centralized (see docs/PROVENANCE_GUIDE.md) and ensure module registry metadata references them.
