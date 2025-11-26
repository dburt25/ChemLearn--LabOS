# Compliance Checklist

Use this checklist to keep documentation aligned with governance, provenance, and non-clinical boundaries. Update status and dates when items change.

## Provenance & Module Registry
- [ ] Document module registry entries with explicit provenance metadata (source, method version, dataset lineage).
- [ ] Ensure DatasetRef linkage is recorded for every module output and stored in audit events.
- [ ] Validate that provenance fields are populated before registering new modules or scientific methods.
- [ ] Confirm each new module records `method_name`, `primary_citation` (including handbook/textbook sources when used), and
      `dataset_citations` with DOIs/links and version notes.

## Dataset Handling
- [ ] Confirm datasets include source attribution, usage restrictions, and licensing notes.
- [ ] Record dataset ingestion steps and transformations in AuditEvent/Workflow logs.
- [ ] Verify consent or public availability before incorporating datasets; note any access controls.

## Source Attribution & Licensing
- [ ] Cite external methods, models, or datasets with formal references and URLs.
- [ ] Capture license terms for third-party materials and verify compatibility with repository use.
- [ ] Avoid copying proprietary content without explicit permission; prefer summaries with citations.

## Future Clinical Considerations (non-clinical now)
- [ ] Clearly label all features as research/education-only; no diagnostic claims.
- [ ] Identify any pathways that could enable clinical use in the future and document required validations.
- [ ] Ensure risk/limitation statements accompany any outputs that might be interpreted clinically.

## Safety & Claims Boundaries
- [ ] Avoid language implying diagnostic, treatment, or patient-management capability.
- [ ] Include limitations, uncertainties, and intended-use statements in user-facing docs.
- [ ] Flag any outputs that rely on unvalidated assumptions or simulated data.

## UI & User Data Security
- [ ] Sanitize and encode user inputs before rendering in UI components or persisting to logs/storage.
- [ ] Reject or neutralize unsafe content (scripts, embedded HTML, serialized objects) in uploads and free-text fields.
- [ ] Avoid `eval`/`exec` or other dynamic execution of user-derived strings; use constrained parsers instead.

## Auditability
- [ ] Maintain chain-of-custody via AuditEvent checksums and timestamps.
- [ ] Store reviewer notes and validation evidence in VALIDATION_LOG.md and compliance-notes.md.
- [ ] Cross-reference provenance records with tests or manual reviews when modules change.
