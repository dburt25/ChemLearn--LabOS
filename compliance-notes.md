# Compliance Notes

## Global Forbidden Rules
- No bot may create, modify, or commit binary files of any kind (.png, .jpg, .pdf, .zip, .db, .exe, .so, .dll, .mp4, or any base64-encoded binary blobs).
- No bot may introduce new external dependencies.

## Shared Path Access Rules
- If multiple bots share read access to a path, exactly one bot is allowed to perform write operations in a given wave. Coordinate bot responsibilities before editing to avoid stomp conflicts.

## Module Registration Guardrails
- Bots modifying modules must not change module import paths or registry keys; keep existing keys stable.
- Any new key added to `ModuleRegistry` must be lowercase, namespaced (e.g., `pchem.delta_g`), and version-stable so downstream workflows do not break.

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
