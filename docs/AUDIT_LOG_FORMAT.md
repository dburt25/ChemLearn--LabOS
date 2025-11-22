# Audit Log Format (Draft)

Outlines the structure and expectations for audit logs produced by LabOS actions.

## Entry Structure
- Event ID and timestamp
- Actor (human or bot) and role
- Action type and scope
- References to experiments, jobs, and datasets

## Constraints
- Entries must be append-only.
- Timestamps use a consistent, timezone-aware format.

## Retention
Retention periods and rotation policies will be defined in later phases.
