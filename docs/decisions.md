# Architecture Decisions

## ADR-0001: Multiview backend interface
**Decision**: Use a backend interface with a COLMAP implementation. 
**Rationale**: Multiview reconstruction is mandatory; a backend interface allows swapping COLMAP for alternative pipelines later.

## ADR-0002: Metadata-aware reporting
**Decision**: Always emit run.json and reconstruction_metrics.json with metadata completeness and scale confidence.
**Rationale**: Phase 0 must remain honest about limitations and capture missing metadata explicitly.

## ADR-0003: Failure handling
**Decision**: Fail loudly with actionable guidance while still writing reports.
**Rationale**: Users need clear next steps (e.g., install COLMAP) and artifact outputs for debugging.
