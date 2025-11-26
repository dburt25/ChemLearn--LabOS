# Provenance Guide

This guide explains how to record citations, track dataset lineage, and set expectations for contributors. The `ModuleRegistry` now acts as the authoritative catalog for built-in methods (EI-MS, P-Chem, spectroscopy, Import Wizard), and UI footers pull provenance fields directly from it.

## Recording Method Citations
- Include formal references (DOI/URL) for external methods or algorithms used in modules.
- Add citation details to module registry metadata and cross-link them in `CITATIONS.md` when appropriate.
- Prefer concise summaries of external work and avoid copying proprietary text; always include licensing notes.

### Module-level provenance fields
- `method_name`: Human-readable label for the scientific technique or algorithm implemented; align it with how the method is referred to in the primary literature or handbook.
- `primary_citation`: The canonical reference for the method implementation (DOI/URL + full citation). When using a textbook or handbook (e.g., a Physical Chemistry manual) as the basis for equations or procedures, cite that book as the primary source and note edition/page ranges when possible.
- `dataset_citations`: List of formal citations (DOI/URL, accession, or publisher link) for every dataset consumed or produced by the module. Include dataset version/refresh date and any access constraints.
- Store these fields alongside module registry metadata and ensure modules emit them in provenance payloads so downstream records inherit the context.
- Cross-reference module-level citations in `CITATIONS.md` and dataset lineage tables where applicable to keep repository-wide attribution consistent.

## ModuleRegistry as the authoritative source
- The `ModuleRegistry` is the authoritative list of Method & Data entries (e.g., `pchem.calorimetry`, `pchem.ideal_gas`, `ei_ms.basic_analysis`, `spectroscopy.nmr`, `spectroscopy.ir`, `import.wizard`).
- Registry metadata should be treated as the single source of truth for UI tooltips, audit payloads, and search.
- When a module is added or renamed, update the registry entry first so downstream provenance (audit logs, DatasetRef) can rely on consistent identifiers.

## DatasetRef and AuditEvent
- Use `DatasetRef` to attach dataset identifiers, hashes, and source metadata to experiments and jobs.
- Emit `AuditEvent` entries whenever datasets are ingested, transformed, or consumed; include timestamps, actors, and checksum chains to maintain ALCOA compliance.
- Link `AuditEvent` records to module registry entries so outputs and downstream artifacts retain traceable lineage.
- Import flows (e.g., the Import Wizard) must emit both a `DatasetRef` for the ingested table and an `AuditEvent` describing the ingest action so provenance is captured even before persistence arrives.

## Expectations for Contributors
- Keep new modules or workflows annotated with provenance metadata: method version, dataset lineage, and configuration parameters.
- Treat external textbooks, handbooks, or lab manuals as primary sources when they drive algorithmic steps or formulas; record them in `primary_citation` and include any derivative references (papers, datasheets) in supporting notes.
- Document any external data or methods with licensing details and intended-use boundaries (research/education-only; future clinical work would require additional validation).
- Update `COMPLIANCE_CHECKLIST.md` and `compliance-notes.md` whenever provenance requirements change, and log accompanying test/documentation updates in `VALIDATION_LOG.md`.
