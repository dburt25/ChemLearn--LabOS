"""Reaction mechanism library for organic chemistry education.

Provides detailed mechanisms for common organic reactions including
substitution, elimination, addition, and functional group transformations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ReactionType(Enum):
    """Classification of organic reaction types."""
    
    SUBSTITUTION_SN1 = "SN1 Substitution"
    SUBSTITUTION_SN2 = "SN2 Substitution"
    ELIMINATION_E1 = "E1 Elimination"
    ELIMINATION_E2 = "E2 Elimination"
    ADDITION_ELECTROPHILIC = "Electrophilic Addition"
    ADDITION_NUCLEOPHILIC = "Nucleophilic Addition"
    OXIDATION = "Oxidation"
    REDUCTION = "Reduction"
    REARRANGEMENT = "Carbocation Rearrangement"
    SUBSTITUTION_AROMATIC = "Aromatic Electrophilic Substitution"


class SubstrateType(Enum):
    """Classification of substrate structure."""
    
    METHYL = "methyl"
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    ALLYLIC = "allylic"
    BENZYLIC = "benzylic"
    VINYL = "vinyl"
    ARYL = "aryl"


@dataclass
class ReactionConditions:
    """Reaction conditions affecting mechanism pathway.
    
    Attributes:
        temperature: Reaction temperature (C, H for hot, RT for room temp)
        solvent: Solvent type (polar protic, polar aprotic, nonpolar)
        base_or_acid: Base or acid catalyst present
        concentration: Reagent concentration (dilute, concentrated)
    """
    
    temperature: str = "RT"
    solvent: str = "polar protic"
    base_or_acid: Optional[str] = None
    concentration: str = "moderate"


@dataclass
class MechanismStep:
    """Single step in a reaction mechanism.
    
    Attributes:
        step_number: Ordinal step in mechanism
        description: What happens in this step
        electron_movement: Arrow-pushing description
        intermediate_formed: Name of intermediate (carbocation, carbanion, etc.)
        rate_determining: Whether this is the RDS
    """
    
    step_number: int
    description: str
    electron_movement: str
    intermediate_formed: Optional[str] = None
    rate_determining: bool = False


@dataclass
class ReactionMechanism:
    """Complete reaction mechanism with steps and analysis.
    
    Attributes:
        reaction_type: Classification of reaction
        steps: List of mechanism steps
        overall_equation: Summary equation
        rate_law: Expected rate law
        stereochemistry: Stereochemical outcome (retention, inversion, racemization)
        competing_reactions: Alternative pathways that might occur
        notes: Educational notes about mechanism
    """
    
    reaction_type: ReactionType
    steps: List[MechanismStep]
    overall_equation: str
    rate_law: str
    stereochemistry: str
    competing_reactions: List[str]
    notes: List[str]


def predict_substitution_mechanism(
    substrate_type: SubstrateType,
    nucleophile_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Predict whether SN1 or SN2 mechanism will predominate.
    
    Args:
        substrate_type: Structure of alkyl halide
        nucleophile_strength: "strong" or "weak"
        conditions: Reaction conditions
        
    Returns:
        Predicted mechanism with steps
    """
    # SN2 favored conditions
    sn2_favored = (
        substrate_type in (SubstrateType.METHYL, SubstrateType.PRIMARY)
        and nucleophile_strength == "strong"
        and conditions.solvent == "polar aprotic"
    )
    
    # SN1 favored conditions
    sn1_favored = (
        substrate_type in (SubstrateType.TERTIARY, SubstrateType.BENZYLIC, SubstrateType.ALLYLIC)
        and conditions.solvent == "polar protic"
    )
    
    if sn2_favored:
        return _build_sn2_mechanism(substrate_type, nucleophile_strength, conditions)
    elif sn1_favored:
        return _build_sn1_mechanism(substrate_type, nucleophile_strength, conditions)
    else:
        # Mixed or competing
        return _build_mixed_substitution_mechanism(substrate_type, nucleophile_strength, conditions)


def _build_sn2_mechanism(
    substrate_type: SubstrateType,
    nucleophile_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Build SN2 mechanism details."""
    
    steps = [
        MechanismStep(
            step_number=1,
            description="Nucleophile attacks carbon from backside while leaving group departs",
            electron_movement="Nucleophile lone pair → C-X σ* orbital; C-X bond breaks",
            intermediate_formed=None,  # Concerted, no intermediate
            rate_determining=True
        )
    ]
    
    competing = []
    if substrate_type == SubstrateType.SECONDARY:
        competing.append("E2 elimination (if strong base present)")
    if conditions.temperature == "H":
        competing.append("E2 elimination favored at higher temperature")
    
    notes = [
        "SN2: Concerted, single-step mechanism",
        "Backside attack leads to inversion of configuration (Walden inversion)",
        "Rate = k[substrate][nucleophile] (second order)",
        "Favored by: strong nucleophile, polar aprotic solvent, unhindered substrate",
        "Steric hindrance: methyl > 1° > 2° >>> 3° (3° essentially unreactive)"
    ]
    
    return ReactionMechanism(
        reaction_type=ReactionType.SUBSTITUTION_SN2,
        steps=steps,
        overall_equation="R-X + Nu⁻ → R-Nu + X⁻",
        rate_law="rate = k[R-X][Nu⁻]",
        stereochemistry="inversion (Walden inversion)",
        competing_reactions=competing,
        notes=notes
    )


def _build_sn1_mechanism(
    substrate_type: SubstrateType,
    nucleophile_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Build SN1 mechanism details."""
    
    steps = [
        MechanismStep(
            step_number=1,
            description="Leaving group departs, forming carbocation intermediate",
            electron_movement="C-X bond breaks heterolytically; X takes both electrons",
            intermediate_formed="carbocation",
            rate_determining=True
        ),
        MechanismStep(
            step_number=2,
            description="Nucleophile attacks planar carbocation from either face",
            electron_movement="Nucleophile lone pair → empty p orbital on carbocation",
            intermediate_formed=None,
            rate_determining=False
        )
    ]
    
    competing = ["E1 elimination (β-hydrogen present)", "Carbocation rearrangement (if more stable carbocation accessible)"]
    if substrate_type == SubstrateType.TERTIARY:
        competing.append("Rearrangement via 1,2-hydride or 1,2-methyl shift")
    
    notes = [
        "SN1: Two-step mechanism via carbocation intermediate",
        "Planar carbocation can be attacked from either face → racemization",
        "Rate = k[substrate] (first order, nucleophile concentration irrelevant)",
        "Favored by: polar protic solvent (stabilizes carbocation), weak nucleophile",
        "Carbocation stability: 3° > 2° > 1° > methyl",
        "Watch for rearrangements! Carbocations can rearrange to more stable forms"
    ]
    
    return ReactionMechanism(
        reaction_type=ReactionType.SUBSTITUTION_SN1,
        steps=steps,
        overall_equation="R-X → R⁺ + X⁻; R⁺ + Nu⁻ → R-Nu",
        rate_law="rate = k[R-X]",
        stereochemistry="racemization (if chiral center involved)",
        competing_reactions=competing,
        notes=notes
    )


def _build_mixed_substitution_mechanism(
    substrate_type: SubstrateType,
    nucleophile_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Build explanation for competing SN1/SN2."""
    
    steps = [
        MechanismStep(
            step_number=1,
            description="Both SN1 and SN2 mechanisms compete",
            electron_movement="Variable based on conditions",
            intermediate_formed="depends on pathway",
            rate_determining=False
        )
    ]
    
    notes = [
        "MIXED: Both SN1 and SN2 pathways compete",
        f"Substrate type: {substrate_type.value} (borderline reactivity)",
        "Secondary substrates show mixed behavior",
        "Product distribution depends on exact conditions",
        "To favor SN2: use strong nucleophile + polar aprotic solvent",
        "To favor SN1: use weak nucleophile + polar protic solvent + heat"
    ]
    
    return ReactionMechanism(
        reaction_type=ReactionType.SUBSTITUTION_SN2,  # Default to SN2 for secondary
        steps=steps,
        overall_equation="R-X + Nu⁻ → R-Nu + X⁻ (mixed mechanism)",
        rate_law="rate = k₁[R-X] + k₂[R-X][Nu⁻]",
        stereochemistry="partial inversion + partial racemization",
        competing_reactions=["SN1", "SN2", "E1", "E2"],
        notes=notes
    )


def predict_elimination_mechanism(
    substrate_type: SubstrateType,
    base_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Predict whether E1 or E2 mechanism will predominate.
    
    Args:
        substrate_type: Structure of alkyl halide
        base_strength: "strong" or "weak"
        conditions: Reaction conditions
        
    Returns:
        Predicted mechanism with steps
    """
    # E2 favored: strong base
    e2_favored = base_strength == "strong"
    
    # E1 favored: weak base, polar protic solvent, heat
    e1_favored = (
        base_strength == "weak"
        and conditions.solvent == "polar protic"
        and conditions.temperature == "H"
    )
    
    if e2_favored:
        return _build_e2_mechanism(substrate_type, base_strength, conditions)
    elif e1_favored:
        return _build_e1_mechanism(substrate_type, base_strength, conditions)
    else:
        return _build_e2_mechanism(substrate_type, base_strength, conditions)  # Default E2


def _build_e2_mechanism(
    substrate_type: SubstrateType,
    base_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Build E2 mechanism details."""
    
    steps = [
        MechanismStep(
            step_number=1,
            description="Base abstracts β-hydrogen while leaving group departs (concerted)",
            electron_movement="Base → H; C-H electrons → C=C π bond; C-X bond breaks",
            intermediate_formed=None,  # Concerted
            rate_determining=True
        )
    ]
    
    notes = [
        "E2: Concerted, single-step elimination",
        "Requires antiperiplanar geometry (H and X on opposite sides, 180°)",
        "Rate = k[substrate][base] (second order)",
        "Favored by: strong base, high temperature",
        "Zaitsev's rule: more substituted alkene favored (more stable)",
        "Hofmann elimination: bulky base gives less substituted alkene",
        "Stereochemistry: anti elimination (E isomer if possible)"
    ]
    
    competing = []
    if substrate_type in (SubstrateType.METHYL, SubstrateType.PRIMARY):
        competing.append("SN2 substitution (competes with E2)")
    
    return ReactionMechanism(
        reaction_type=ReactionType.ELIMINATION_E2,
        steps=steps,
        overall_equation="R-CH₂-CH₂-X + Base → R-CH=CH₂ + HBase⁺ + X⁻",
        rate_law="rate = k[R-X][Base]",
        stereochemistry="anti elimination (antiperiplanar transition state)",
        competing_reactions=competing,
        notes=notes
    )


def _build_e1_mechanism(
    substrate_type: SubstrateType,
    base_strength: str,
    conditions: ReactionConditions
) -> ReactionMechanism:
    """Build E1 mechanism details."""
    
    steps = [
        MechanismStep(
            step_number=1,
            description="Leaving group departs, forming carbocation",
            electron_movement="C-X bond breaks heterolytically",
            intermediate_formed="carbocation",
            rate_determining=True
        ),
        MechanismStep(
            step_number=2,
            description="Base abstracts β-hydrogen, forming double bond",
            electron_movement="Base → H; C-H electrons → C=C π bond",
            intermediate_formed=None,
            rate_determining=False
        )
    ]
    
    notes = [
        "E1: Two-step elimination via carbocation",
        "Rate = k[substrate] (first order)",
        "Favored by: weak base, polar protic solvent, heat",
        "Same carbocation as SN1, so E1 competes with SN1",
        "Zaitsev's rule: more substituted alkene favored",
        "Carbocation can rearrange before elimination"
    ]
    
    competing = ["SN1 substitution", "Carbocation rearrangement"]
    
    return ReactionMechanism(
        reaction_type=ReactionType.ELIMINATION_E1,
        steps=steps,
        overall_equation="R-CH₂-CH₂-X → R⁺-CH₂-CH₂ + X⁻; R⁺-CH₂-CH₂ → R-CH=CH₂ + H⁺",
        rate_law="rate = k[R-X]",
        stereochemistry="no stereochemistry (carbocation intermediate)",
        competing_reactions=competing,
        notes=notes
    )


# Module metadata
MODULE_KEY = "org_chem.mechanisms"
MODULE_VERSION = "1.0.0"

__all__ = [
    "ReactionType",
    "SubstrateType",
    "ReactionConditions",
    "MechanismStep",
    "ReactionMechanism",
    "predict_substitution_mechanism",
    "predict_elimination_mechanism",
]
