# Feedback and Telemetry (Local Only)

This project includes local-only scaffolding for capturing telemetry and user
feedback. All data stays on the developer machine; there are **no** outbound
network calls, remote analytics, or integrations with third-party services.

## What is recorded

The `labos.core.telemetry` module defines lightweight helpers for common events:

- Experiments: `experiment_started`, `experiment_completed`
- Jobs: `job_started`, `job_completed`
- Errors: `error`
- Custom events via `log_event(name, payload)`

Each event includes a generated identifier, timestamp, name, and structured
payload supplied by the caller. Payloads should avoid secrets, tokens, PHI, or
other sensitive information.

## Where data is stored

Telemetry is stored locally using JSON Lines (`telemetry-events.jsonl`) under the
LabOS feedback directory (by default `data/feedback/`). Developers can inspect
or delete these files at any time. Events are also kept in memory within the
process for quick inspection.

## How to record telemetry

```python
from labos.core import telemetry

telemetry.record_experiment_started("exp-123", {"model": "demo"})
telemetry.record_job_completed("job-456", status="succeeded")
telemetry.record_error("training", "out of memory", {"gpu": 0})
```

## Future shipping (opt-in only)

Future versions may introduce optional exporters that can ship events to
centralized systems (e.g., self-hosted storage, offline batch uploads). Any such
feature must:

- Be **explicitly opt-in** and disabled by default.
- Clearly document what data leaves the local machine and why.
- Allow easy review and deletion of locally buffered events before sending.
- Respect privacy expectations—never collect credentials, PHI, or proprietary
  model artifacts without consent.

Until such features exist, telemetry remains strictly local to support developer
workflows and debugging.
