# Swarm Permissions Matrix

Defines what each bot role may modify during the build.

| Role | Allowed Areas | Restricted Areas | Notes |
| --- | --- | --- | --- |
| Core Builder Bot | `labos/`, `data/` schemas, core docs | `chemlearn_modules/` domain packs | Must coordinate with Compliance bot before schema changes |
| Scientific Module Bot | `chemlearn_modules/<domain>/` | `labos/` core, `ui/` | Needs validation evidence per module |
| UI Integration Bot | `ui/`, UX docs | Core orchestration, compliance docs | Accessibility reviews required |
| Compliance & Audit Bot | `docs/` governance, `compliance-notes.md`, logs | Runtime code (except docstrings) | Owns ALCOA+ adherence |
| Data & Artifact Bot | `data/`, LFS configs, provenance docs | UI, module internals | Enforces storage quotas, privacy |
| Test & Validation Bot | `tests/`, `VALIDATION_LOG.md` | Business logic (unless fixing tests) | Guards regression coverage |

Update this table whenever a new specialized role is introduced.
