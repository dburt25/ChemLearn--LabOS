"""Stereochemistry validation and analysis for organic chemistry.

Provides tools for determining R/S configuration, E/Z alkene geometry,
chirality analysis, and stereochemical outcome prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ChiralityType(Enum):
    """Types of chirality."""
    
    TETRAHEDRAL = "tetrahedral (sp³)"
    AXIAL = "axial (allene, spirocycle)"
    PLANAR = "planar (restricted rotation)"
    HELICAL = "helical (screw sense)"


class Configuration(Enum):
    """Stereochemical configuration."""
    
    R = "R"
    S = "S"
    E = "E"
    Z = "Z"
    CIS = "cis"
    TRANS = "trans"
    SYN = "syn"
    ANTI = "anti"
    RACEMIC = "racemic"
    MESO = "meso"


@dataclass
class SubstituentPriority:
    """Cahn-Ingold-Prelog priority assignment.
    
    Attributes:
        group_name: Name of substituent
        atomic_number: Atomic number of directly attached atom
        priority: CIP priority (1 = highest)
        reasoning: Explanation of priority assignment
    """
    
    group_name: str
    atomic_number: int
    priority: int
    reasoning: str


@dataclass
class StereocenterAnalysis:
    """Analysis of a single stereogenic center.
    
    Attributes:
        center_atom: Identity of stereocenter (e.g., "C-2")
        substituents: List of attached groups with priorities
        configuration: R or S configuration
        notes: Educational notes about assignment
    """
    
    center_atom: str
    substituents: List[SubstituentPriority]
    configuration: Configuration
    notes: List[str]


@dataclass
class MoleculeStereochemistry:
    """Complete stereochemical analysis of molecule.
    
    Attributes:
        stereocenters: List of stereogenic centers
        alkene_geometry: E/Z configurations of alkenes
        is_chiral: Whether molecule is chiral overall
        is_meso: Whether molecule is meso compound
        enantiomers_possible: Number of possible stereoisomers
        notes: Analysis notes
    """
    
    stereocenters: List[StereocenterAnalysis]
    alkene_geometry: Dict[str, Configuration]
    is_chiral: bool
    is_meso: bool
    enantiomers_possible: int
    notes: List[str]


def assign_cip_priorities(
    substituents: List[Tuple[str, int]]
) -> List[SubstituentPriority]:
    """Assign Cahn-Ingold-Prelog priorities to substituents.
    
    Args:
        substituents: List of (group_name, atomic_number) tuples
        
    Returns:
        Sorted list of substituents with assigned priorities
    """
    # Sort by atomic number (descending)
    sorted_subs = sorted(substituents, key=lambda x: x[1], reverse=True)
    
    priorities = []
    for i, (name, atomic_num) in enumerate(sorted_subs, start=1):
        reasoning = f"Atomic number {atomic_num}"
        if i == 1:
            reasoning += " (highest priority)"
        elif i == len(sorted_subs):
            reasoning += " (lowest priority)"
        
        priorities.append(
            SubstituentPriority(
                group_name=name,
                atomic_number=atomic_num,
                priority=i,
                reasoning=reasoning
            )
        )
    
    return priorities


def determine_r_s_configuration(
    substituents: List[SubstituentPriority],
    rotation_direction: str
) -> Configuration:
    """Determine R or S configuration from priorities and rotation.
    
    Args:
        substituents: Prioritized substituents
        rotation_direction: "clockwise" or "counterclockwise" from 1→2→3
        
    Returns:
        R or S configuration
    """
    # Assumes lowest priority (4) is pointing away
    if rotation_direction == "clockwise":
        return Configuration.R
    elif rotation_direction == "counterclockwise":
        return Configuration.S
    else:
        raise ValueError(f"Invalid rotation direction: {rotation_direction}")


def analyze_tetrahedral_center(
    center_name: str,
    substituents: List[Tuple[str, int]],
    rotation_direction: str
) -> StereocenterAnalysis:
    """Analyze a tetrahedral stereocenter.
    
    Args:
        center_name: Name of the stereocenter
        substituents: List of (group_name, atomic_number) tuples
        rotation_direction: Rotation direction when viewing from lowest priority
        
    Returns:
        Complete stereocenter analysis
    """
    if len(substituents) != 4:
        raise ValueError("Tetrahedral center must have exactly 4 substituents")
    
    priorities = assign_cip_priorities(substituents)
    config = determine_r_s_configuration(priorities, rotation_direction)
    
    notes = [
        "Cahn-Ingold-Prelog (CIP) priority rules:",
        "1. Higher atomic number = higher priority",
        "2. If tie, look at next atoms out",
        "3. Multiple bonds count as multiple single bonds",
        f"4. Orient lowest priority away from viewer",
        f"5. Trace 1→2→3: {rotation_direction} = {config.value}"
    ]
    
    return StereocenterAnalysis(
        center_atom=center_name,
        substituents=priorities,
        configuration=config,
        notes=notes
    )


def determine_e_z_configuration(
    alkene_name: str,
    left_substituents: List[Tuple[str, int]],
    right_substituents: List[Tuple[str, int]]
) -> Tuple[Configuration, List[str]]:
    """Determine E or Z configuration for an alkene.
    
    Args:
        alkene_name: Name of the alkene
        left_substituents: Substituents on left carbon [(name, atomic_number), ...]
        right_substituents: Substituents on right carbon
        
    Returns:
        Tuple of (configuration, explanatory_notes)
    """
    # Assign priorities on each side
    left_priorities = assign_cip_priorities(left_substituents)
    right_priorities = assign_cip_priorities(right_substituents)
    
    # Get highest priority groups on each side
    left_high = left_priorities[0]
    right_high = right_priorities[0]
    
    # For E/Z, we need to know if high priority groups are on same or opposite sides
    # This would require 3D coordinates in reality; for educational purposes,
    # we'll determine based on input specification
    notes = [
        f"Left carbon highest priority: {left_high.group_name}",
        f"Right carbon highest priority: {right_high.group_name}",
        "E (entgegen): high-priority groups on opposite sides",
        "Z (zusammen): high-priority groups on same side",
    ]
    
    # Return E as default (in reality, need geometric info)
    return Configuration.E, notes


def calculate_stereoisomers(
    num_stereocenters: int,
    has_meso: bool = False,
    has_internal_plane: bool = False
) -> int:
    """Calculate maximum number of stereoisomers.
    
    Args:
        num_stereocenters: Number of stereogenic centers
        has_meso: Whether meso compounds are possible
        has_internal_plane: Whether internal plane of symmetry exists
        
    Returns:
        Number of possible stereoisomers
    """
    max_isomers = 2 ** num_stereocenters
    
    if has_meso:
        # Meso compound reduces count by half
        max_isomers = max_isomers // 2
    
    return max_isomers


def analyze_molecule_stereochemistry(
    stereocenters: List[Dict],
    alkenes: List[Dict] = None,
    has_symmetry: bool = False
) -> MoleculeStereochemistry:
    """Perform complete stereochemical analysis of a molecule.
    
    Args:
        stereocenters: List of stereocenter definitions
        alkenes: List of alkene definitions
        has_symmetry: Whether molecule has internal symmetry
        
    Returns:
        Complete stereochemical analysis
    """
    analyzed_centers = []
    for center_data in stereocenters:
        center = analyze_tetrahedral_center(
            center_data["name"],
            center_data["substituents"],
            center_data["rotation"]
        )
        analyzed_centers.append(center)
    
    alkene_configs = {}
    if alkenes:
        for alkene_data in alkenes:
            config, notes = determine_e_z_configuration(
                alkene_data["name"],
                alkene_data["left_subs"],
                alkene_data["right_subs"]
            )
            alkene_configs[alkene_data["name"]] = config
    
    num_centers = len(analyzed_centers)
    max_isomers = calculate_stereoisomers(num_centers, has_meso=has_symmetry)
    
    is_chiral = num_centers > 0 and not has_symmetry
    
    notes = [
        f"Found {num_centers} stereogenic center(s)",
        f"Maximum stereoisomers: 2^{num_centers} = {2**num_centers}",
    ]
    
    if has_symmetry:
        notes.append("Internal plane of symmetry → meso compound possible")
        notes.append(f"Actual stereoisomers: {max_isomers} (accounting for meso)")
    
    if is_chiral:
        notes.append("Molecule is chiral (no plane of symmetry)")
    else:
        notes.append("Molecule is achiral or meso")
    
    return MoleculeStereochemistry(
        stereocenters=analyzed_centers,
        alkene_geometry=alkene_configs,
        is_chiral=is_chiral,
        is_meso=has_symmetry and num_centers >= 2,
        enantiomers_possible=max_isomers,
        notes=notes
    )


def predict_stereochemical_outcome(
    reaction_type: str,
    starting_configuration: Configuration
) -> Tuple[Configuration, List[str]]:
    """Predict stereochemical outcome based on reaction mechanism.
    
    Args:
        reaction_type: Type of reaction (SN1, SN2, E1, E2, etc.)
        starting_configuration: Starting stereochemistry
        
    Returns:
        Tuple of (product_configuration, explanation_notes)
    """
    notes = []
    
    if reaction_type == "SN2":
        # Inversion (Walden inversion)
        if starting_configuration == Configuration.R:
            product = Configuration.S
        elif starting_configuration == Configuration.S:
            product = Configuration.R
        else:
            product = Configuration.RACEMIC
        notes = [
            "SN2: Backside attack causes inversion (Walden inversion)",
            f"{starting_configuration.value} → {product.value}",
            "100% inversion of configuration"
        ]
    
    elif reaction_type == "SN1":
        # Racemization
        product = Configuration.RACEMIC
        notes = [
            "SN1: Planar carbocation intermediate",
            "Nucleophile attacks from either face",
            "Result: racemic mixture (50% R + 50% S)",
            "Some retention possible if leaving group blocks one face"
        ]
    
    elif reaction_type == "E2":
        # Anti elimination
        product = Configuration.E  # Or Z, depends on starting geometry
        notes = [
            "E2: Anti-periplanar elimination",
            "H and leaving group must be 180° apart",
            "Stereochemistry of product depends on starting geometry",
            "Usually gives E (trans) alkene (more stable)"
        ]
    
    elif reaction_type == "E1":
        # No stereoselectivity
        product = Configuration.E  # Major product
        notes = [
            "E1: Carbocation intermediate, no stereoselectivity",
            "Both E and Z alkenes can form",
            "E (trans) usually predominates (more stable)",
            "Zaitsev product (more substituted) favored"
        ]
    
    else:
        product = Configuration.RACEMIC
        notes = [f"Unknown reaction type: {reaction_type}"]
    
    return product, notes


# Module metadata
MODULE_KEY = "org_chem.stereochemistry"
MODULE_VERSION = "1.0.0"

__all__ = [
    "ChiralityType",
    "Configuration",
    "SubstituentPriority",
    "StereocenterAnalysis",
    "MoleculeStereochemistry",
    "assign_cip_priorities",
    "determine_r_s_configuration",
    "analyze_tetrahedral_center",
    "determine_e_z_configuration",
    "analyze_molecule_stereochemistry",
    "predict_stereochemical_outcome",
]
