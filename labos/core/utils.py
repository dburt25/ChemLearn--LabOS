"""Utility helpers shared across LabOS modules."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> str:
    """Return an ISO-8601 timestamp in UTC with timezone information."""

    return datetime.now(timezone.utc).isoformat()
