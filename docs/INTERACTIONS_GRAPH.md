# Interactions Graph

High-level view of how LabOS components communicate.

## Core flow (Phase 1–2 skeleton)

```
Experiment -> Job -> Module Operation -> Result Artifact
                          |                     |
                          v                     v
                    ModuleRegistry        DatasetRef/Result JSON
                          |                     |
                          v                     v
                    AuditEvent log   ->   DatasetRegistry entry
```

- **ExperimentRegistry** persists intent and purpose, linking user context to downstream jobs.
- **JobRunner/JobRegistry** creates jobs bound to a module operation, executes via `ModuleRegistry`, and persists result JSON paths.
- **ModuleRegistry** (scientific plugins) resolves operations; stubs return structured `dataset` + `audit` payloads for provenance.
- **DatasetRegistry** stores dataset metadata (owner, URI, tags, module provenance) when stubs or future modules emit DatasetRefs.
- **AuditLogger** records every registry write and job transition to maintain ALCOA+ traces.

## UI touchpoints

```
Control Panel (Learner/Lab/Builder)
    -> loads registries from LabOSRuntime
    -> displays experiments/jobs/datasets tables
    -> Module Inspector pulls ModuleRegistry + ModuleMetadata
```

- Mode banners/tips in the Streamlit Control Panel adjust copy but all rely on the same registries.
- The Module Inspector surfaces both executable operations (`ModuleDescriptor`) and provenance metadata (`ModuleMetadata`) for transparency.
- Draft experiment creation in UI is read-only until persisted via CLI/API, reinforcing separation between demo mode and audit-backed records.

## Module and import stubs

```
ModuleDescriptor (auto-registered)
    compute(params) -> {module_key, dataset, audit, status}
```

- EI-MS fragmentation, P-Chem calorimetry, and Import Wizard stubs are auto-loaded; each emits deterministic dataset/audit payloads tagged with `module_key` for downstream provenance.
- Stubs currently mark status as `not-implemented`, signaling educational/demo use only.

## Data and compliance surfaces

- **Storage**: JSONFileStore under `LabOSConfig` directories backs experiment/job/dataset registries; job results serialize module outputs for inspection.
- **AuditEvent linkage**: Registries attach audit IDs to records upon create/update, enabling traceability across Experiment → Job → Dataset transitions.
- **ModuleMetadata**: Separate from executable descriptors; supplies citations, limitations, and reference URLs for UI provenance panels.

## Planned extensions

- Enrich DatasetRef modeling so module outputs can be promoted into the DatasetRegistry automatically.
- Annotate interactions with protocols (CLI/REST/events) once Phase 2+ services and automation mature.
