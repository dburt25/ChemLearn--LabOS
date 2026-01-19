"""Tests for Charuco capability detection."""

from __future__ import annotations

from scanner.calibration.charuco import aruco_capability


def test_aruco_capability_detection() -> None:
    ready, message = aruco_capability()
    if ready:
        assert message == ""
    else:
        assert "opencv" in message.lower()
