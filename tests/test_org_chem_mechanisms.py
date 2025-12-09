"""Tests for organic chemistry reaction mechanisms module."""

import pytest

from labos.modules.org_chem.mechanisms import (
    ReactionType,
    SubstrateType,
    ReactionConditions,
    MechanismStep,
    predict_substitution_mechanism,
    predict_elimination_mechanism,
)


class TestSubstitutionPrediction:
    """Test SN1/SN2 mechanism prediction."""

    def test_sn2_methyl_substrate(self):
        """Methyl substrates strongly favor SN2."""
        conditions = ReactionConditions(solvent="polar aprotic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.METHYL,
            "strong",
            conditions
        )
        
        assert mechanism.reaction_type == ReactionType.SUBSTITUTION_SN2
        assert mechanism.stereochemistry == "inversion (Walden inversion)"
        assert "backside" in mechanism.steps[0].description.lower()

    def test_sn2_primary_substrate(self):
        """Primary substrates favor SN2 with strong nucleophile."""
        conditions = ReactionConditions(solvent="polar aprotic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.PRIMARY,
            "strong",
            conditions
        )
        
        assert mechanism.reaction_type == ReactionType.SUBSTITUTION_SN2
        assert len(mechanism.steps) == 1  # Concerted
        assert mechanism.rate_law == "rate = k[R-X][Nu⁻]"

    def test_sn1_tertiary_substrate(self):
        """Tertiary substrates favor SN1."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert mechanism.reaction_type == ReactionType.SUBSTITUTION_SN1
        assert len(mechanism.steps) == 2  # Two-step
        assert mechanism.stereochemistry == "racemization (if chiral center involved)"
        assert mechanism.steps[0].rate_determining is True
        assert "carbocation" in mechanism.steps[0].intermediate_formed

    def test_sn1_rate_law(self):
        """SN1 rate law is first order."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert mechanism.rate_law == "rate = k[R-X]"

    def test_secondary_substrate_mixed(self):
        """Secondary substrates show mixed behavior."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.SECONDARY,
            "weak",
            conditions
        )
        
        # Should indicate mixed or competing pathways
        assert len(mechanism.competing_reactions) > 0

    def test_sn1_competing_reactions(self):
        """SN1 mechanisms should list competing reactions."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert "E1 elimination" in mechanism.competing_reactions[0]
        assert "Carbocation rearrangement" in mechanism.competing_reactions[1]


class TestEliminationPrediction:
    """Test E1/E2 mechanism prediction."""

    def test_e2_strong_base(self):
        """Strong base favors E2 mechanism."""
        conditions = ReactionConditions(temperature="H")
        mechanism = predict_elimination_mechanism(
            SubstrateType.SECONDARY,
            "strong",
            conditions
        )
        
        assert mechanism.reaction_type == ReactionType.ELIMINATION_E2
        assert len(mechanism.steps) == 1  # Concerted
        assert mechanism.stereochemistry == "anti elimination (antiperiplanar transition state)"

    def test_e2_rate_law(self):
        """E2 rate law is second order."""
        conditions = ReactionConditions()
        mechanism = predict_elimination_mechanism(
            SubstrateType.SECONDARY,
            "strong",
            conditions
        )
        
        assert mechanism.rate_law == "rate = k[R-X][Base]"

    def test_e1_weak_base(self):
        """Weak base with heat favors E1."""
        conditions = ReactionConditions(solvent="polar protic", temperature="H")
        mechanism = predict_elimination_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert mechanism.reaction_type == ReactionType.ELIMINATION_E1
        assert len(mechanism.steps) == 2  # Two-step via carbocation
        assert mechanism.steps[0].intermediate_formed == "carbocation"

    def test_e1_rate_law(self):
        """E1 rate law is first order."""
        conditions = ReactionConditions(solvent="polar protic", temperature="H")
        mechanism = predict_elimination_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert mechanism.rate_law == "rate = k[R-X]"

    def test_e2_antiperiplanar(self):
        """E2 requires antiperiplanar geometry."""
        conditions = ReactionConditions()
        mechanism = predict_elimination_mechanism(
            SubstrateType.SECONDARY,
            "strong",
            conditions
        )
        
        assert "antiperiplanar" in mechanism.notes[1].lower()

    def test_e1_competing_with_sn1(self):
        """E1 competes with SN1."""
        conditions = ReactionConditions(solvent="polar protic", temperature="H")
        mechanism = predict_elimination_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert "SN1" in mechanism.competing_reactions[0]


class TestReactionConditions:
    """Test ReactionConditions dataclass."""

    def test_default_conditions(self):
        """Test default reaction conditions."""
        conditions = ReactionConditions()
        
        assert conditions.temperature == "RT"
        assert conditions.solvent == "polar protic"
        assert conditions.base_or_acid is None
        assert conditions.concentration == "moderate"

    def test_custom_conditions(self):
        """Test custom reaction conditions."""
        conditions = ReactionConditions(
            temperature="H",
            solvent="polar aprotic",
            base_or_acid="NaOH",
            concentration="dilute"
        )
        
        assert conditions.temperature == "H"
        assert conditions.solvent == "polar aprotic"
        assert conditions.base_or_acid == "NaOH"
        assert conditions.concentration == "dilute"


class TestMechanismSteps:
    """Test mechanism step structures."""

    def test_sn2_single_step(self):
        """SN2 should have single concerted step."""
        conditions = ReactionConditions(solvent="polar aprotic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.PRIMARY,
            "strong",
            conditions
        )
        
        assert len(mechanism.steps) == 1
        assert mechanism.steps[0].rate_determining is True
        assert mechanism.steps[0].intermediate_formed is None  # No intermediate

    def test_sn1_two_steps(self):
        """SN1 should have two discrete steps."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        assert len(mechanism.steps) == 2
        assert mechanism.steps[0].step_number == 1
        assert mechanism.steps[1].step_number == 2
        assert mechanism.steps[0].rate_determining is True
        assert mechanism.steps[1].rate_determining is False


class TestEducationalNotes:
    """Test that mechanisms include educational notes."""

    def test_sn2_notes_present(self):
        """SN2 mechanism should include educational notes."""
        conditions = ReactionConditions(solvent="polar aprotic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.PRIMARY,
            "strong",
            conditions
        )
        
        assert len(mechanism.notes) > 0
        # Check for key teaching points
        notes_text = " ".join(mechanism.notes).lower()
        assert "concerted" in notes_text
        assert "inversion" in notes_text
        assert "second order" in notes_text

    def test_sn1_notes_present(self):
        """SN1 mechanism should include educational notes."""
        conditions = ReactionConditions(solvent="polar protic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.TERTIARY,
            "weak",
            conditions
        )
        
        notes_text = " ".join(mechanism.notes).lower()
        assert "carbocation" in notes_text
        assert "racemization" in notes_text
        assert "first order" in notes_text

    def test_e2_zaitsev_mentioned(self):
        """E2 notes should mention Zaitsev's rule."""
        conditions = ReactionConditions()
        mechanism = predict_elimination_mechanism(
            SubstrateType.SECONDARY,
            "strong",
            conditions
        )
        
        notes_text = " ".join(mechanism.notes)
        assert "Zaitsev" in notes_text or "zaitsev" in notes_text.lower()


class TestOverallEquations:
    """Test that mechanisms include proper equations."""

    def test_sn2_equation(self):
        """SN2 should have proper overall equation."""
        conditions = ReactionConditions(solvent="polar aprotic")
        mechanism = predict_substitution_mechanism(
            SubstrateType.PRIMARY,
            "strong",
            conditions
        )
        
        assert "R-X" in mechanism.overall_equation
        assert "Nu" in mechanism.overall_equation
        assert "→" in mechanism.overall_equation

    def test_e2_equation(self):
        """E2 should show elimination equation."""
        conditions = ReactionConditions()
        mechanism = predict_elimination_mechanism(
            SubstrateType.SECONDARY,
            "strong",
            conditions
        )
        
        assert "CH₂" in mechanism.overall_equation or "CH2" in mechanism.overall_equation
        assert "CH=" in mechanism.overall_equation
