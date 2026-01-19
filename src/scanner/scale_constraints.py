"""Regime definitions for scan anchoring and scaling."""

from __future__ import annotations

from enum import Enum


class ScanRegime(str, Enum):
    SMALL_OBJECT = "small_object"
    ROOM_BUILDING = "room_building"
    AERIAL = "aerial"

    @classmethod
    def from_string(cls, value: str) -> "ScanRegime":
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(f"Unknown scan regime: {value}")
