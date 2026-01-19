"""Tests for reference frame selection helpers."""

from __future__ import annotations

from scanner.pipeline import default_anchor_inputs
from scanner.reference_frame import compute_bbox_center, translate_points
from scanner.scale_constraints import ScanRegime


def test_bbox_center_computed_correctly() -> None:
    points = [(0.0, 0.0, 0.0), (2.0, 4.0, 6.0), (4.0, 2.0, 2.0)]
    center = compute_bbox_center(points)
    assert center == (2.0, 2.0, 3.0)


def test_translation_applied_correctly() -> None:
    points = [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]
    translated = translate_points(points, (1.0, 1.0, 1.0))
    assert translated == [(0.0, 1.0, 2.0), (3.0, 4.0, 5.0)]


def test_small_object_defaults_disable_heuristics() -> None:
    inputs = default_anchor_inputs(ScanRegime.SMALL_OBJECT)
    assert inputs.resolved_allow_heuristics() is False

    overridden = default_anchor_inputs(ScanRegime.SMALL_OBJECT, allow_heuristics=True)
    assert overridden.resolved_allow_heuristics() is True
