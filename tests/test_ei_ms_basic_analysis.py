"""Tests for EI-MS heuristic analysis stub."""

from __future__ import annotations

from labos.modules.ei_ms.basic_analysis import run_basic_analysis


def test_run_basic_analysis_detects_base_peak() -> None:
    result = run_basic_analysis(
        {
            "precursor_mass": 200.0,
            "fragment_masses": [50.0, 120.0, 80.0],
            "fragment_intensities": [10.0, 95.0, 20.0],
        }
    )

    assert result.status == "ok"
    fragments = result.fragments
    assert fragments[1].classification == "base_peak"
    assert result.summary["base_peak_mass"] == 120.0
    assert all(fragment.classification == "minor_peak" for i, fragment in enumerate(fragments) if i != 1)


def test_run_basic_analysis_tags_neutral_losses() -> None:
    result = run_basic_analysis(
        {
            "precursor_mass": 150.0,
            "fragment_masses": [132.1, 100.0],
            "fragment_intensities": [50.0, 80.0],
        }
    )

    fragments = result.fragments
    water_loss = fragments[0].neutral_losses[0]
    assert water_loss.label.lower().startswith("water")

    unmatched_loss = fragments[1].neutral_losses[0]
    assert unmatched_loss.label == "Unassigned neutral loss"
    assert unmatched_loss.mass_difference == round(50.0, 3)
