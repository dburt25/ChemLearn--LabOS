# Audit Log Format

Defines the append-only record layout for every LabOS event.

## Entry Structure
- `event_id` (UUID)
- `timestamp` (ISO 8601, timezone-aware)
- `actor_id` and `actor_role`
- `action_type` and `action_scope`
- `module_key` (e.g., `pchem.calorimetry`, `ei_ms.basic_analysis`, `spectroscopy.nmr`, `import.wizard`)
- `references` (experiment/job/dataset IDs)
- `payload_hash` (optional integrity check)
- `prev_checksum` (hash of the previous line for chain integrity)
- `checksum` (SHA-256 of `prev_checksum + entry` to prevent tampering)

## Constraints
- Logs are append-only and cryptographically verifiable when possible.
- All timestamps captured in UTC with offset preserved.
- References must point to existing registry entries; otherwise log entry is rejected.
- Include the module key from the ModuleRegistry so provenance tooling can join audit streams to method metadata.

## Retention & Rotation
- Minimum retention: 10 years or per regulatory mandate.
- Rotation policies documented in `DATA_ARCHITECTURE.md` once storage layers finalize.
- Archived logs remain searchable with audit trail of transfers.
- Chain verification is performed by recomputing checksums per file.

## Minimal Examples
```
# EI-MS analysis
{
  "event_id": "...",
  "action_type": "analyze",
  "action_scope": "ei_ms.basic_analysis",
  "module_key": "ei_ms.basic_analysis",
  "references": {"dataset_id": "DS-MS-001"}
}

# Import wizard ingest
{
  "event_id": "...",
  "action_type": "ingest",
  "action_scope": "import",
  "module_key": "import.wizard",
  "references": {"dataset_id": "DS-IMPORT-ABC"}
}
```
