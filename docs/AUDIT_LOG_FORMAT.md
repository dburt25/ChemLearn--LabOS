# Audit Log Format

Defines the append-only record layout for every LabOS event.

## Entry Structure
- `event_id` (UUID)
- `timestamp` (ISO 8601, timezone-aware)
- `actor_id` and `actor_role`
- `action_type` and `action_scope`
- `references` (experiment/job/dataset IDs)
- `payload_hash` (optional integrity check)
- `prev_checksum` (hash of the previous line for chain integrity)
- `checksum` (SHA-256 of `prev_checksum + entry` to prevent tampering)

## Constraints
- Logs are append-only and cryptographically verifiable when possible.
- All timestamps captured in UTC with offset preserved.
- References must point to existing registry entries; otherwise log entry is rejected.

## Retention & Rotation
- Minimum retention: 10 years or per regulatory mandate.
- Rotation policies documented in `DATA_ARCHITECTURE.md` once storage layers finalize.
- Archived logs remain searchable with audit trail of transfers.
- Chain verification is performed by recomputing checksums per file.
