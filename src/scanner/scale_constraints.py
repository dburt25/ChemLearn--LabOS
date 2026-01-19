"""Scan regime definitions and default constraints."""

from __future__ import annotations

from enum import Enum


class ScanRegime(str, Enum):
    """Supported scan regimes for reference frame defaults."""

    SMALL_OBJECT = "small_object"
    ROOM_BUILDING = "room_building"
    AERIAL = "aerial"


def default_allow_heuristics(regime: ScanRegime) -> bool:
    """Return the default heuristic policy for a scan regime."""

    if regime == ScanRegime.SMALL_OBJECT:
        return False
    return True
