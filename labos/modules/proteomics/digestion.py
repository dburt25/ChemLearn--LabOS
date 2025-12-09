"""
Protein Digestion Simulation Module

Simulates enzymatic digestion of proteins, generates peptide fragments,
and predicts cleavage sites based on enzyme specificity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Set, Optional, Tuple
import re


class Enzyme(Enum):
    """Common proteolytic enzymes with cleavage specificity"""
    TRYPSIN = "trypsin"
    CHYMOTRYPSIN = "chymotrypsin"
    PEPSIN = "pepsin"
    ELASTASE = "elastase"
    THERMOLYSIN = "thermolysin"
    LYSYL_ENDOPEPTIDASE = "lys_c"
    ARGINYL_ENDOPEPTIDASE = "arg_c"
    GLUTAMYL_ENDOPEPTIDASE = "glu_c"
    ASPARTIC_ACID_ENDOPEPTIDASE = "asp_n"
    CNBR = "cnbr"  # Chemical cleavage


# Enzyme cleavage rules: (cleavage_after_residues, exceptions, cleavage_side)
# cleavage_side: 'C' = C-terminal side, 'N' = N-terminal side
ENZYME_SPECIFICITY: Dict[Enzyme, Tuple[Set[str], Set[str], str]] = {
    Enzyme.TRYPSIN: ({"K", "R"}, {"P"}, "C"),  # Cleaves after K or R, not before P
    Enzyme.CHYMOTRYPSIN: ({"F", "W", "Y", "L"}, {"P"}, "C"),  # Large hydrophobic residues
    Enzyme.PEPSIN: ({"F", "L", "W", "Y"}, set(), "C"),  # Hydrophobic residues
    Enzyme.ELASTASE: ({"A", "V", "S", "G", "L", "I"}, {"P"}, "C"),  # Small neutral residues
    Enzyme.THERMOLYSIN: ({"L", "I", "V", "A", "M", "F"}, set(), "N"),  # N-terminal side of hydrophobic
    Enzyme.LYSYL_ENDOPEPTIDASE: ({"K"}, {"P"}, "C"),  # Specific for lysine
    Enzyme.ARGINYL_ENDOPEPTIDASE: ({"R"}, {"P"}, "C"),  # Specific for arginine
    Enzyme.GLUTAMYL_ENDOPEPTIDASE: ({"E"}, {"P"}, "C"),  # Specific for glutamic acid
    Enzyme.ASPARTIC_ACID_ENDOPEPTIDASE: ({"D"}, set(), "N"),  # N-terminal to aspartic acid
    Enzyme.CNBR: ({"M"}, set(), "C"),  # Chemical cleavage at methionine
}


@dataclass
class CleavageSite:
    """Represents a potential cleavage site in a protein sequence"""
    position: int  # 0-indexed position in sequence
    residue: str  # Amino acid at cleavage position
    enzyme: Enzyme
    is_cleaved: bool  # Whether this site is actually cleaved (may be blocked)
    reason: str  # Explanation for cleavage/blocking


@dataclass
class Peptide:
    """Represents a peptide fragment from digestion"""
    sequence: str
    start_position: int  # 0-indexed
    end_position: int  # 0-indexed (inclusive)
    mass: float  # Monoisotopic mass in Da
    charge_states: List[int]  # Possible charge states for MS
    missed_cleavages: int  # Number of missed cleavage sites within peptide
    n_terminus: str  # N-terminal modification state
    c_terminus: str  # C-terminal modification state


@dataclass
class DigestionResult:
    """Complete results of an enzymatic digestion simulation"""
    protein_sequence: str
    enzyme: Enzyme
    peptides: List[Peptide]
    cleavage_sites: List[CleavageSite]
    total_cleavage_sites: int
    cleaved_sites: int
    missed_cleavages: int
    digestion_efficiency: float  # Percentage of sites cleaved
    notes: List[str]


# Amino acid monoisotopic masses (Da)
AA_MASSES = {
    "A": 71.03711, "C": 103.00919, "D": 115.02694, "E": 129.04259,
    "F": 147.06841, "G": 57.02146, "H": 137.05891, "I": 113.08406,
    "K": 128.09496, "L": 113.08406, "M": 131.04049, "N": 114.04293,
    "P": 97.05276, "Q": 128.05858, "R": 156.10111, "S": 87.03203,
    "T": 101.04768, "V": 99.06841, "W": 186.07931, "Y": 163.06333,
}

# Water mass (added for intact peptide)
WATER_MASS = 18.01056


def validate_protein_sequence(sequence: str) -> Tuple[bool, str]:
    """
    Validate that a protein sequence contains only valid amino acid codes.
    
    Args:
        sequence: Protein sequence string
        
    Returns:
        (is_valid, error_message)
    """
    if not sequence:
        return False, "Sequence cannot be empty"
    
    sequence = sequence.upper().strip()
    valid_aa = set(AA_MASSES.keys())
    invalid_chars = set(sequence) - valid_aa
    
    if invalid_chars:
        return False, f"Invalid amino acid codes: {', '.join(sorted(invalid_chars))}"
    
    return True, ""


def calculate_peptide_mass(sequence: str) -> float:
    """
    Calculate monoisotopic mass of a peptide sequence.
    
    Args:
        sequence: Peptide sequence string
        
    Returns:
        Monoisotopic mass in Daltons
    """
    mass = sum(AA_MASSES[aa] for aa in sequence.upper())
    return mass + WATER_MASS  # Add water for intact peptide


def predict_charge_states(sequence: str, max_charge: int = 4) -> List[int]:
    """
    Predict likely charge states for a peptide based on basic residues.
    
    Args:
        sequence: Peptide sequence
        max_charge: Maximum charge state to consider
        
    Returns:
        List of likely charge states (most common first)
    """
    # Count basic residues (K, R, H) and N-terminus
    basic_count = sequence.count("K") + sequence.count("R") + sequence.count("H")
    max_possible = basic_count + 1  # Include N-terminus
    
    # Likely charges depend on peptide length and basic residues
    likely_charges = []
    
    if len(sequence) <= 7:
        # Short peptides typically +1 or +2
        likely_charges = [1, 2] if basic_count >= 1 else [1]
    elif len(sequence) <= 20:
        # Medium peptides +2 or +3
        if basic_count >= 2:
            likely_charges = [2, 3]
        elif basic_count >= 1:
            likely_charges = [2, 1]
        else:
            likely_charges = [1]
    else:
        # Long peptides can be +3 or higher
        if basic_count >= 3:
            likely_charges = [3, 2, 4]
        elif basic_count >= 2:
            likely_charges = [2, 3]
        else:
            likely_charges = [2, 1]
    
    # Filter to max_charge and max_possible
    likely_charges = [z for z in likely_charges if z <= max_charge and z <= max_possible]
    
    return likely_charges if likely_charges else [1]


def find_cleavage_sites(
    sequence: str,
    enzyme: Enzyme,
    allow_missed_cleavages: bool = True
) -> List[CleavageSite]:
    """
    Identify all potential cleavage sites for an enzyme in a sequence.
    
    Args:
        sequence: Protein sequence
        enzyme: Enzyme to use for digestion
        allow_missed_cleavages: Whether to allow some sites to be missed
        
    Returns:
        List of CleavageSite objects
    """
    sequence = sequence.upper()
    cleavage_residues, exceptions, cleavage_side = ENZYME_SPECIFICITY[enzyme]
    
    sites = []
    
    for i, aa in enumerate(sequence):
        is_cleavage_residue = aa in cleavage_residues
        
        if not is_cleavage_residue:
            continue
        
        # Check for exceptions
        is_blocked = False
        reason = f"Cleavage after {aa} at position {i}"
        
        if cleavage_side == "C":
            # Check if next residue blocks cleavage
            if i + 1 < len(sequence) and sequence[i + 1] in exceptions:
                is_blocked = True
                reason = f"Blocked: {sequence[i + 1]} follows {aa} at position {i}"
        elif cleavage_side == "N":
            # For N-terminal cleavage, check previous residue
            if i > 0 and sequence[i - 1] in exceptions:
                is_blocked = True
                reason = f"Blocked: {sequence[i - 1]} precedes {aa} at position {i}"
        
        # In real digestion, not all sites are cleaved (missed cleavages)
        is_cleaved = not is_blocked
        
        sites.append(CleavageSite(
            position=i,
            residue=aa,
            enzyme=enzyme,
            is_cleaved=is_cleaved,
            reason=reason
        ))
    
    return sites


def generate_peptides(
    sequence: str,
    cleavage_sites: List[CleavageSite],
    missed_cleavages: int = 0
) -> List[Peptide]:
    """
    Generate peptide fragments from cleavage sites.
    
    Args:
        sequence: Protein sequence
        cleavage_sites: List of cleavage sites
        missed_cleavages: Maximum number of missed cleavages to allow (0-3 typical)
        
    Returns:
        List of Peptide objects
    """
    sequence = sequence.upper()
    
    # Get positions of cleaved sites
    cleaved_positions = sorted([site.position for site in cleavage_sites if site.is_cleaved])
    
    # Add sequence boundaries
    boundaries = [0] + [pos + 1 for pos in cleaved_positions] + [len(sequence)]
    
    peptides = []
    
    # Generate peptides with 0 to missed_cleavages
    for mc in range(missed_cleavages + 1):
        for i in range(len(boundaries) - 1 - mc):
            start = boundaries[i]
            end = boundaries[i + mc + 1] - 1  # Inclusive end
            
            if start > end:
                continue
            
            pep_seq = sequence[start:end + 1]
            
            # Skip very short peptides (< 5 aa) typically not detected
            if len(pep_seq) < 5:
                continue
            
            # Skip very long peptides (> 50 aa) typically not well-ionized
            if len(pep_seq) > 50:
                continue
            
            mass = calculate_peptide_mass(pep_seq)
            charges = predict_charge_states(pep_seq)
            
            peptides.append(Peptide(
                sequence=pep_seq,
                start_position=start,
                end_position=end,
                mass=mass,
                charge_states=charges,
                missed_cleavages=mc,
                n_terminus="free",
                c_terminus="free"
            ))
    
    return peptides


def simulate_digestion(
    protein_sequence: str,
    enzyme: Enzyme = Enzyme.TRYPSIN,
    missed_cleavages: int = 1,
    min_length: int = 5,
    max_length: int = 50
) -> DigestionResult:
    """
    Simulate enzymatic digestion of a protein sequence.
    
    Args:
        protein_sequence: Protein sequence to digest
        enzyme: Enzyme to use for digestion
        missed_cleavages: Maximum number of missed cleavages (0-3 typical)
        min_length: Minimum peptide length to include
        max_length: Maximum peptide length to include
        
    Returns:
        DigestionResult with peptides and cleavage information
    """
    # Validate sequence
    is_valid, error_msg = validate_protein_sequence(protein_sequence)
    if not is_valid:
        raise ValueError(f"Invalid protein sequence: {error_msg}")
    
    sequence = protein_sequence.upper().strip()
    
    # Find cleavage sites
    cleavage_sites = find_cleavage_sites(sequence, enzyme)
    
    # Generate peptides
    peptides = generate_peptides(sequence, cleavage_sites, missed_cleavages)
    
    # Filter by length
    peptides = [p for p in peptides if min_length <= len(p.sequence) <= max_length]
    
    # Calculate statistics
    total_sites = len(cleavage_sites)
    cleaved_sites = sum(1 for site in cleavage_sites if site.is_cleaved)
    total_missed = sum(p.missed_cleavages for p in peptides if p.missed_cleavages == 0)
    
    efficiency = (cleaved_sites / total_sites * 100) if total_sites > 0 else 0
    
    notes = [
        f"Digestion with {enzyme.value}",
        f"Generated {len(peptides)} peptides",
        f"Allowed up to {missed_cleavages} missed cleavages",
        f"Peptide length range: {min_length}-{max_length} aa"
    ]
    
    return DigestionResult(
        protein_sequence=sequence,
        enzyme=enzyme,
        peptides=peptides,
        cleavage_sites=cleavage_sites,
        total_cleavage_sites=total_sites,
        cleaved_sites=cleaved_sites,
        missed_cleavages=total_missed,
        digestion_efficiency=efficiency,
        notes=notes
    )


def predict_observable_peptides(
    digestion_result: DigestionResult,
    min_mz: float = 400.0,
    max_mz: float = 2000.0
) -> List[Tuple[Peptide, int, float]]:
    """
    Predict which peptides would be observable in mass spectrometry.
    
    Args:
        digestion_result: Result from simulate_digestion
        min_mz: Minimum m/z ratio for MS detection
        max_mz: Maximum m/z ratio for MS detection
        
    Returns:
        List of (peptide, charge, mz) tuples for observable ions
    """
    observable = []
    
    for peptide in digestion_result.peptides:
        for charge in peptide.charge_states:
            mz = (peptide.mass + charge * 1.007276) / charge  # Add proton mass
            
            if min_mz <= mz <= max_mz:
                observable.append((peptide, charge, mz))
    
    # Sort by m/z
    observable.sort(key=lambda x: x[2])
    
    return observable


def calculate_sequence_coverage(
    digestion_result: DigestionResult,
    observable_peptides: List[Tuple[Peptide, int, float]] = None
) -> Tuple[float, List[int]]:
    """
    Calculate sequence coverage from peptides.
    
    Args:
        digestion_result: Result from simulate_digestion
        observable_peptides: If provided, use only observable peptides
        
    Returns:
        (coverage_percentage, covered_positions_list)
    """
    sequence_length = len(digestion_result.protein_sequence)
    covered = set()
    
    peptides_to_use = digestion_result.peptides
    if observable_peptides:
        peptides_to_use = [pep for pep, _, _ in observable_peptides]
    
    for peptide in peptides_to_use:
        for pos in range(peptide.start_position, peptide.end_position + 1):
            covered.add(pos)
    
    coverage = len(covered) / sequence_length * 100 if sequence_length > 0 else 0
    
    return coverage, sorted(covered)
