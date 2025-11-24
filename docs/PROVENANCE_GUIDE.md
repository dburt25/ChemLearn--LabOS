# Provenance Guide

This guide explains how to record citations, track dataset lineage, and set expectations for contributors.

## Recording Method Citations
- Include formal references (DOI/URL) for external methods or algorithms used in modules.
- Add citation details to module registry metadata and cross-link them in `CITATIONS.md` when appropriate.
- Prefer concise summaries of external work and avoid copying proprietary text; always include licensing notes.

## DatasetRef and AuditEvent
- Use `DatasetRef` to attach dataset identifiers, hashes, and source metadata to experiments and jobs.
- Emit `AuditEvent` entries whenever datasets are ingested, transformed, or consumed; include timestamps, actors, and checksum chains to maintain ALCOA compliance.
- Link `AuditEvent` records to module registry entries so outputs and downstream artifacts retain traceable lineage.

## Expectations for Contributors
- Keep new modules or workflows annotated with provenance metadata: method version, dataset lineage, and configuration parameters.
- Document any external data or methods with licensing details and intended-use boundaries (research/education-only; future clinical work would require additional validation).
- Update `COMPLIANCE_CHECKLIST.md` and `compliance-notes.md` whenever provenance requirements change, and log accompanying test/documentation updates in `VALIDATION_LOG.md`.
