"""Stub electronic signature object for Phase 1 compliance planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class Signature:
    
    """Placeholder signature container (no real cryptography yet)."""

    signer: str
    intent: str
    method: str = "labos-stub"
    signed_at: str = field(default_factory=_now_iso)
    evidence: Dict[str, Any] = field(default_factory=dict)
    signature_id: str = field(default_factory=lambda: f"SIG-{uuid4().hex[:8]}")
    stub_token: str = field(default_factory=lambda: f"stub-{uuid4().hex}")

    def summary(self) -> str:
        return f"{self.signature_id}:{self.signer}:{self.intent}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
