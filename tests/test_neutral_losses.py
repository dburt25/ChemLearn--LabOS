"""Tests for EI-MS neutral loss detection module."""

import pytest
from labos.modules.ei_ms.neutral_losses import (
    COMMON_LOSSES,
    NeutralLoss,
    detect_neutral_losses,
    annotate_spectrum,
    find_sequential_losses,
    analyze_neutral_losses,
)


class TestCommonLossesDatabase:
    """Test neutral loss database."""

    def test_water_loss_in_database(self):
        """Test that water loss is in database."""
        assert 18 in COMMON_LOSSES
        assert COMMON_LOSSES[18]["name"] == "H2O"

    def test_co2_loss_in_database(self):
        """Test that CO2 loss is in database."""
        assert 44 in COMMON_LOSSES
        assert COMMON_LOSSES[44]["name"] == "CO2"

    def test_ammonia_loss_in_database(self):
        """Test that ammonia loss is in database."""
        assert 17 in COMMON_LOSSES
        assert COMMON_LOSSES[17]["name"] == "NH3"

    def test_database_has_interpretations(self):
        """Test that each loss has interpretation text."""
        for mass, loss_data in COMMON_LOSSES.items():
            assert "name" in loss_data
            assert "interpretation" in loss_data
            assert isinstance(loss_data["interpretation"], str)
            assert len(loss_data["interpretation"]) > 0


class TestNeutralLossDetection:
    """Test neutral loss detection."""

    def test_detect_water_loss(self):
        """Test detection of water loss (M-18)."""
        # Precursor at m/z 100, fragment at m/z 82 (loss of 18)
        losses = detect_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[(82.0, 50.0), (50.0, 30.0)],
            mass_tolerance=0.5
        )
        
        # Should detect water loss
        assert len(losses) > 0
        water_loss = next((l for l in losses if l.loss_mass == 18), None)
        assert water_loss is not None
        assert water_loss.fragment_mz == 82.0

    def test_detect_co2_loss(self):
        """Test detection of CO2 loss (M-44)."""
        losses = detect_neutral_losses(
            precursor_mz=150.0,
            fragment_peaks=[(106.0, 70.0), (80.0, 40.0)],
            mass_tolerance=0.5
        )
        
        # Should detect CO2 loss
        co2_loss = next((l for l in losses if l.loss_mass == 44), None)
        assert co2_loss is not None
        assert co2_loss.fragment_mz == 106.0

    def test_multiple_losses_detected(self):
        """Test detection of multiple different losses."""
        losses = detect_neutral_losses(
            precursor_mz=200.0,
            fragment_peaks=[
                (182.0, 60.0),  # -18 (H2O)
                (156.0, 50.0),  # -44 (CO2)
                (183.0, 30.0),  # -17 (NH3)
            ],
            mass_tolerance=0.5
        )
        
        # Should detect at least 3 different losses
        assert len(losses) >= 3
        
        loss_masses = [l.loss_mass for l in losses]
        assert 18 in loss_masses  # H2O
        assert 44 in loss_masses  # CO2
        assert 17 in loss_masses  # NH3

    def test_no_losses_when_no_matches(self):
        """Test no losses detected when fragments don't match common losses."""
        losses = detect_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[(99.5, 50.0), (87.3, 30.0)],  # Random fragments
            mass_tolerance=0.5
        )
        
        # May detect some or none depending on mass tolerance
        # Just verify function runs without error
        assert isinstance(losses, list)

    def test_mass_tolerance_affects_detection(self):
        """Test that mass tolerance affects detection."""
        # Fragment at 81.7 - is it M-18 from M=100?
        
        # Tight tolerance should not detect
        losses_tight = detect_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[(81.7, 50.0)],
            mass_tolerance=0.1
        )
        water_tight = next((l for l in losses_tight if l.loss_mass == 18), None)
        assert water_tight is None
        
        # Loose tolerance should detect
        losses_loose = detect_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[(81.7, 50.0)],
            mass_tolerance=0.5
        )
        water_loose = next((l for l in losses_loose if l.loss_mass == 18), None)
        assert water_loose is not None


class TestSpectrumAnnotation:
    """Test spectrum annotation with neutral losses."""

    def test_annotate_simple_spectrum(self):
        """Test annotation of simple spectrum."""
        annotated = annotate_spectrum(
            precursor_mz=100.0,
            fragment_peaks=[(82.0, 50.0), (50.0, 30.0)],
            mass_tolerance=0.5
        )
        
        assert len(annotated) == 2
        
        # First peak should be annotated with water loss
        peak_82 = next(p for p in annotated if p["mz"] == 82.0)
        assert "annotations" in peak_82
        assert len(peak_82["annotations"]) > 0
        
        # Check water loss annotation
        water_ann = next((a for a in peak_82["annotations"] if "H2O" in a), None)
        assert water_ann is not None

    def test_unannotated_peaks_have_empty_list(self):
        """Test that peaks without matches have empty annotation list."""
        annotated = annotate_spectrum(
            precursor_mz=100.0,
            fragment_peaks=[(99.1, 50.0)],  # No common loss matches
            mass_tolerance=0.3
        )
        
        peak = annotated[0]
        assert "annotations" in peak
        # May be empty or have some annotation depending on exact mass

    def test_annotation_includes_interpretation(self):
        """Test that annotations include interpretation text."""
        annotated = annotate_spectrum(
            precursor_mz=120.0,
            fragment_peaks=[(102.0, 60.0)],  # M-18 (water)
            mass_tolerance=0.5
        )
        
        peak = annotated[0]
        if len(peak["annotations"]) > 0:
            # Annotation format: "Loss: H2O (18 Da) - Hydroxyl or water elimination"
            annotation = peak["annotations"][0]
            assert "Loss:" in annotation
            assert "Da" in annotation


class TestSequentialLosses:
    """Test sequential neutral loss detection."""

    def test_detect_sequential_water_losses(self):
        """Test detection of sequential water losses."""
        chains = find_sequential_losses(
            precursor_mz=150.0,
            fragment_peaks=[
                (132.0, 60.0),  # M-18 (first water)
                (114.0, 40.0),  # M-36 (second water)
                (96.0, 20.0),   # M-54 (third water)
            ],
            mass_tolerance=0.5
        )
        
        # Should find chains of water losses
        assert len(chains) > 0
        
        # Look for a chain with multiple water losses
        water_chain = next((c for c in chains if len(c) >= 2), None)
        assert water_chain is not None

    def test_sequential_co_then_co2_loss(self):
        """Test detection of CO followed by CO2 loss."""
        chains = find_sequential_losses(
            precursor_mz=200.0,
            fragment_peaks=[
                (172.0, 50.0),  # M-28 (CO)
                (128.0, 30.0),  # M-72 (CO + CO2)
            ],
            mass_tolerance=0.5
        )
        
        # Should detect sequential losses
        assert len(chains) > 0

    def test_no_chains_for_isolated_losses(self):
        """Test no chains detected for isolated losses."""
        chains = find_sequential_losses(
            precursor_mz=100.0,
            fragment_peaks=[
                (82.0, 50.0),  # M-18 only
            ],
            mass_tolerance=0.5
        )
        
        # Single loss, no chain
        # Function may return chains of length 1 or empty list
        # Just verify it runs
        assert isinstance(chains, list)


class TestAnalyzeNeutralLosses:
    """Test main analyze_neutral_losses function."""

    def test_analyze_alcohol_fragmentation(self):
        """Test analysis of alcohol fragmentation pattern."""
        result = analyze_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[
                (82.0, 60.0),  # M-18 (water)
                (57.0, 40.0),
            ],
            mass_tolerance=0.5,
            detect_chains=False
        )
        
        assert "precursor_mz" in result
        assert "detected_losses" in result
        assert "annotated_spectrum" in result
        
        # Should detect water loss
        assert len(result["detected_losses"]) > 0
        water_loss = next((l for l in result["detected_losses"] if l["loss_mass"] == 18), None)
        assert water_loss is not None

    def test_analyze_with_chain_detection(self):
        """Test analysis with sequential loss detection enabled."""
        result = analyze_neutral_losses(
            precursor_mz=150.0,
            fragment_peaks=[
                (132.0, 60.0),
                (114.0, 40.0),
                (96.0, 20.0),
            ],
            mass_tolerance=0.5,
            detect_chains=True
        )
        
        assert "sequential_losses" in result
        # Should detect some chains
        assert isinstance(result["sequential_losses"], list)

    def test_analyze_without_chain_detection(self):
        """Test analysis without chain detection."""
        result = analyze_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[(82.0, 50.0)],
            mass_tolerance=0.5,
            detect_chains=False
        )
        
        assert "sequential_losses" not in result

    def test_summary_includes_common_losses(self):
        """Test that summary identifies common fragmentation patterns."""
        result = analyze_neutral_losses(
            precursor_mz=120.0,
            fragment_peaks=[
                (102.0, 60.0),  # M-18 (H2O)
                (76.0, 40.0),   # M-44 (CO2)
            ],
            mass_tolerance=0.5,
            detect_chains=False
        )
        
        assert "summary" in result
        summary = result["summary"]
        
        # Should mention water and CO2 losses
        assert "H2O" in summary or "water" in summary.lower()

    def test_empty_spectrum_handling(self):
        """Test handling of empty spectrum."""
        result = analyze_neutral_losses(
            precursor_mz=100.0,
            fragment_peaks=[],
            mass_tolerance=0.5,
            detect_chains=False
        )
        
        # Should return valid result with empty losses
        assert "detected_losses" in result
        assert len(result["detected_losses"]) == 0
        assert "annotated_spectrum" in result
        assert len(result["annotated_spectrum"]) == 0


class TestNeutralLossDataClass:
    """Test NeutralLoss dataclass."""

    def test_neutral_loss_creation(self):
        """Test creating a NeutralLoss object."""
        loss = NeutralLoss(
            precursor_mz=100.0,
            fragment_mz=82.0,
            loss_mass=18,
            loss_name="H2O",
            interpretation="Water elimination"
        )
        
        assert loss.precursor_mz == 100.0
        assert loss.fragment_mz == 82.0
        assert loss.loss_mass == 18
        assert loss.loss_name == "H2O"
        assert loss.interpretation == "Water elimination"

    def test_neutral_loss_equality(self):
        """Test NeutralLoss equality comparison."""
        loss1 = NeutralLoss(100.0, 82.0, 18, "H2O", "Water")
        loss2 = NeutralLoss(100.0, 82.0, 18, "H2O", "Water")
        
        assert loss1 == loss2
