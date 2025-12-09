"""
Peptide Analysis Module

Provides functions for analyzing peptide properties, predicting fragmentation,
and generating theoretical mass spectra.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


class FragmentType(Enum):
    """Types of peptide fragment ions"""
    # N-terminal ions
    A_ION = "a"  # [M+H - CO - NH3]+
    B_ION = "b"  # [M+H - NH3]+
    C_ION = "c"  # [M+H]+
    
    # C-terminal ions
    X_ION = "x"  # [M+H - CO2]+
    Y_ION = "y"  # [M+H]+
    Z_ION = "z"  # [M+H - NH2]+
    
    # Special ions
    IMMONIUM = "immonium"
    PRECURSOR = "precursor"
    NEUTRAL_LOSS = "neutral_loss"


@dataclass
class FragmentIon:
    """Represents a fragment ion from peptide fragmentation"""
    ion_type: FragmentType
    position: int  # Position of fragmentation (1-indexed from N or C terminus)
    mass: float  # m/z value
    charge: int
    sequence: str  # Fragment sequence
    intensity: float  # Relative intensity (0-100)
    label: str  # Ion label (e.g., "b3", "y2")


@dataclass
class TheoreticalSpectrum:
    """Theoretical MS/MS spectrum for a peptide"""
    peptide_sequence: str
    precursor_mz: float
    precursor_charge: int
    fragment_ions: List[FragmentIon]
    base_peak_mz: float  # Most intense peak
    base_peak_intensity: float
    total_ions: int
    notes: List[str]


@dataclass
class PeptideProperties:
    """Physical and chemical properties of a peptide"""
    sequence: str
    monoisotopic_mass: float
    average_mass: float
    length: int
    molecular_formula: str
    isoelectric_point: float  # pI
    hydrophobicity: float  # GRAVY score
    charge_at_ph7: float
    extinction_coefficient: float  # at 280 nm (M^-1 cm^-1)
    instability_index: float
    aliphatic_index: float
    aromaticity: float
    composition: Dict[str, int]  # Amino acid counts


# Amino acid properties
AA_MASSES = {
    "A": 71.03711, "C": 103.00919, "D": 115.02694, "E": 129.04259,
    "F": 147.06841, "G": 57.02146, "H": 137.05891, "I": 113.08406,
    "K": 128.09496, "L": 113.08406, "M": 131.04049, "N": 114.04293,
    "P": 97.05276, "Q": 128.05858, "R": 156.10111, "S": 87.03203,
    "T": 101.04768, "V": 99.06841, "W": 186.07931, "Y": 163.06333,
}

# Atomic masses for formula calculation
ATOMIC_MASSES = {
    "H": 1.007825, "C": 12.000000, "N": 14.003074,
    "O": 15.994915, "S": 31.972071
}

# Amino acid formulas (without H2O)
AA_FORMULAS = {
    "A": {"C": 3, "H": 5, "N": 1, "O": 1},
    "C": {"C": 3, "H": 5, "N": 1, "O": 1, "S": 1},
    "D": {"C": 4, "H": 5, "N": 1, "O": 3},
    "E": {"C": 5, "H": 7, "N": 1, "O": 3},
    "F": {"C": 9, "H": 9, "N": 1, "O": 1},
    "G": {"C": 2, "H": 3, "N": 1, "O": 1},
    "H": {"C": 6, "H": 7, "N": 3, "O": 1},
    "I": {"C": 6, "H": 11, "N": 1, "O": 1},
    "K": {"C": 6, "H": 12, "N": 2, "O": 1},
    "L": {"C": 6, "H": 11, "N": 1, "O": 1},
    "M": {"C": 5, "H": 9, "N": 1, "O": 1, "S": 1},
    "N": {"C": 4, "H": 6, "N": 2, "O": 2},
    "P": {"C": 5, "H": 7, "N": 1, "O": 1},
    "Q": {"C": 5, "H": 8, "N": 2, "O": 2},
    "R": {"C": 6, "H": 12, "N": 4, "O": 1},
    "S": {"C": 3, "H": 5, "N": 1, "O": 2},
    "T": {"C": 4, "H": 7, "N": 1, "O": 2},
    "V": {"C": 5, "H": 9, "N": 1, "O": 1},
    "W": {"C": 11, "H": 10, "N": 2, "O": 1},
    "Y": {"C": 9, "H": 9, "N": 1, "O": 2},
}

# Hydrophobicity scale (Kyte-Doolittle)
HYDROPHOBICITY = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}

# pKa values for ionizable groups
PKA_VALUES = {
    "N_terminus": 9.6,
    "C_terminus": 2.3,
    "K": 10.5,  # Lysine side chain
    "R": 12.5,  # Arginine side chain
    "H": 6.0,   # Histidine side chain
    "D": 3.9,   # Aspartic acid side chain
    "E": 4.3,   # Glutamic acid side chain
    "C": 8.3,   # Cysteine side chain
    "Y": 10.1,  # Tyrosine side chain
}


def calculate_molecular_formula(sequence: str) -> Dict[str, int]:
    """
    Calculate molecular formula of a peptide.
    
    Args:
        sequence: Peptide sequence
        
    Returns:
        Dictionary of element counts
    """
    formula = {"C": 0, "H": 0, "N": 0, "O": 0, "S": 0}
    
    for aa in sequence.upper():
        if aa in AA_FORMULAS:
            for element, count in AA_FORMULAS[aa].items():
                formula[element] += count
    
    # Add H2O for intact peptide
    formula["H"] += 2
    formula["O"] += 1
    
    return {k: v for k, v in formula.items() if v > 0}


def formula_to_string(formula: Dict[str, int]) -> str:
    """Convert formula dict to string representation"""
    elements_order = ["C", "H", "N", "O", "S"]
    parts = []
    for elem in elements_order:
        if elem in formula and formula[elem] > 0:
            count = formula[elem]
            parts.append(f"{elem}{count if count > 1 else ''}")
    return "".join(parts)


def calculate_average_mass(sequence: str) -> float:
    """
    Calculate average mass using average isotopic weights.
    This is a simplified calculation.
    """
    # For educational purposes, use monoisotopic + small offset
    mono = sum(AA_MASSES[aa] for aa in sequence.upper())
    return mono + 18.01056 + (len(sequence) * 0.0005)  # Approximate isotope effect


def calculate_isoelectric_point(sequence: str) -> float:
    """
    Calculate theoretical pI using simplified Henderson-Hasselbalch.
    
    Args:
        sequence: Peptide sequence
        
    Returns:
        Estimated pI value
    """
    # Count ionizable groups
    n_term = 1
    c_term = 1
    lys_count = sequence.count("K")
    arg_count = sequence.count("R")
    his_count = sequence.count("H")
    asp_count = sequence.count("D")
    glu_count = sequence.count("E")
    cys_count = sequence.count("C")
    tyr_count = sequence.count("Y")
    
    # Binary search for pH where net charge = 0
    ph_min, ph_max = 0.0, 14.0
    
    for _ in range(50):  # Iterate to convergence
        ph = (ph_min + ph_max) / 2
        
        # Calculate charges at this pH
        charge = 0.0
        
        # Positive charges
        charge += 1 / (1 + 10 ** (ph - PKA_VALUES["N_terminus"]))
        charge += lys_count / (1 + 10 ** (ph - PKA_VALUES["K"]))
        charge += arg_count / (1 + 10 ** (ph - PKA_VALUES["R"]))
        charge += his_count / (1 + 10 ** (ph - PKA_VALUES["H"]))
        
        # Negative charges
        charge -= 1 / (1 + 10 ** (PKA_VALUES["C_terminus"] - ph))
        charge -= asp_count / (1 + 10 ** (PKA_VALUES["D"] - ph))
        charge -= glu_count / (1 + 10 ** (PKA_VALUES["E"] - ph))
        charge -= cys_count / (1 + 10 ** (PKA_VALUES["C"] - ph))
        charge -= tyr_count / (1 + 10 ** (PKA_VALUES["Y"] - ph))
        
        if abs(charge) < 0.01:
            return ph
        
        if charge > 0:
            ph_min = ph
        else:
            ph_max = ph
    
    return (ph_min + ph_max) / 2


def calculate_charge_at_ph(sequence: str, ph: float = 7.0) -> float:
    """Calculate net charge at specified pH"""
    # Same calculation as pI but at fixed pH
    charge = 0.0
    
    charge += 1 / (1 + 10 ** (ph - PKA_VALUES["N_terminus"]))
    charge += sequence.count("K") / (1 + 10 ** (ph - PKA_VALUES["K"]))
    charge += sequence.count("R") / (1 + 10 ** (ph - PKA_VALUES["R"]))
    charge += sequence.count("H") / (1 + 10 ** (ph - PKA_VALUES["H"]))
    
    charge -= 1 / (1 + 10 ** (PKA_VALUES["C_terminus"] - ph))
    charge -= sequence.count("D") / (1 + 10 ** (PKA_VALUES["D"] - ph))
    charge -= sequence.count("E") / (1 + 10 ** (PKA_VALUES["E"] - ph))
    charge -= sequence.count("C") / (1 + 10 ** (PKA_VALUES["C"] - ph))
    charge -= sequence.count("Y") / (1 + 10 ** (PKA_VALUES["Y"] - ph))
    
    return charge


def calculate_hydrophobicity(sequence: str) -> float:
    """
    Calculate GRAVY (Grand Average of Hydropathy) score.
    
    Args:
        sequence: Peptide sequence
        
    Returns:
        GRAVY score
    """
    if not sequence:
        return 0.0
    
    total = sum(HYDROPHOBICITY.get(aa, 0) for aa in sequence.upper())
    return total / len(sequence)


def calculate_extinction_coefficient(sequence: str) -> float:
    """
    Calculate extinction coefficient at 280 nm (M^-1 cm^-1).
    Based on Trp, Tyr, and Cys content.
    """
    trp_count = sequence.count("W")
    tyr_count = sequence.count("Y")
    cys_count = sequence.count("C")
    
    # Extinction coefficients: W=5500, Y=1490, C-C=125
    return trp_count * 5500 + tyr_count * 1490 + (cys_count // 2) * 125


def analyze_peptide_properties(sequence: str) -> PeptideProperties:
    """
    Comprehensive analysis of peptide properties.
    
    Args:
        sequence: Peptide sequence
        
    Returns:
        PeptideProperties object with all calculated properties
    """
    sequence = sequence.upper().strip()
    
    # Calculate masses
    mono_mass = sum(AA_MASSES[aa] for aa in sequence) + 18.01056
    avg_mass = calculate_average_mass(sequence)
    
    # Calculate formula
    formula = calculate_molecular_formula(sequence)
    formula_str = formula_to_string(formula)
    
    # Calculate composition
    composition = {aa: sequence.count(aa) for aa in set(sequence)}
    
    # Calculate properties
    pi = calculate_isoelectric_point(sequence)
    hydro = calculate_hydrophobicity(sequence)
    charge = calculate_charge_at_ph(sequence, 7.0)
    extinction = calculate_extinction_coefficient(sequence)
    
    # Simplified instability index (educational approximation)
    instability = 40.0 if "W" in sequence or "P" in sequence else 30.0
    
    # Aliphatic index
    aliphatic = (sequence.count("A") + 2.9 * sequence.count("V") + 
                 3.9 * (sequence.count("I") + sequence.count("L"))) / len(sequence) * 100
    
    # Aromaticity
    aromatic = (sequence.count("F") + sequence.count("W") + sequence.count("Y")) / len(sequence)
    
    return PeptideProperties(
        sequence=sequence,
        monoisotopic_mass=mono_mass,
        average_mass=avg_mass,
        length=len(sequence),
        molecular_formula=formula_str,
        isoelectric_point=round(pi, 2),
        hydrophobicity=round(hydro, 3),
        charge_at_ph7=round(charge, 2),
        extinction_coefficient=extinction,
        instability_index=round(instability, 2),
        aliphatic_index=round(aliphatic, 2),
        aromaticity=round(aromatic, 3),
        composition=composition
    )


def generate_b_ions(sequence: str, charge: int = 1) -> List[FragmentIon]:
    """Generate b-ion series (N-terminal fragments)"""
    ions = []
    cumulative_mass = 0.0
    
    for i, aa in enumerate(sequence[:-1], 1):  # Don't include last residue
        cumulative_mass += AA_MASSES[aa]
        mz = (cumulative_mass + charge * 1.007276) / charge
        
        # Intensity decreases for larger fragments (simplified model)
        intensity = 100 * (1 - i / len(sequence)) ** 0.5
        
        ions.append(FragmentIon(
            ion_type=FragmentType.B_ION,
            position=i,
            mass=mz,
            charge=charge,
            sequence=sequence[:i],
            intensity=intensity,
            label=f"b{i}" + (f"^{charge}+" if charge > 1 else "+")
        ))
    
    return ions


def generate_y_ions(sequence: str, charge: int = 1) -> List[FragmentIon]:
    """Generate y-ion series (C-terminal fragments)"""
    ions = []
    cumulative_mass = 18.01056  # Start with H2O for C-terminal
    
    for i, aa in enumerate(reversed(sequence[1:]), 1):  # Don't include first residue
        cumulative_mass += AA_MASSES[aa]
        mz = (cumulative_mass + charge * 1.007276) / charge
        
        # y-ions typically more intense than b-ions
        intensity = 100 * (0.7 + 0.3 * (1 - i / len(sequence)) ** 0.5)
        
        ions.append(FragmentIon(
            ion_type=FragmentType.Y_ION,
            position=i,
            mass=mz,
            charge=charge,
            sequence=sequence[-i:],
            intensity=intensity,
            label=f"y{i}" + (f"^{charge}+" if charge > 1 else "+")
        ))
    
    return ions


def generate_theoretical_spectrum(
    sequence: str,
    precursor_charge: int = 2,
    include_b_ions: bool = True,
    include_y_ions: bool = True,
    max_fragment_charge: int = 2
) -> TheoreticalSpectrum:
    """
    Generate theoretical MS/MS spectrum for a peptide.
    
    Args:
        sequence: Peptide sequence
        precursor_charge: Charge state of precursor ion
        include_b_ions: Include b-ion series
        include_y_ions: Include y-ion series
        max_fragment_charge: Maximum charge for fragment ions
        
    Returns:
        TheoreticalSpectrum with predicted fragment ions
    """
    sequence = sequence.upper().strip()
    
    # Calculate precursor m/z
    precursor_mass = sum(AA_MASSES[aa] for aa in sequence) + 18.01056
    precursor_mz = (precursor_mass + precursor_charge * 1.007276) / precursor_charge
    
    fragment_ions = []
    
    # Generate fragment ions
    for charge in range(1, min(max_fragment_charge, precursor_charge) + 1):
        if include_b_ions:
            fragment_ions.extend(generate_b_ions(sequence, charge))
        if include_y_ions:
            fragment_ions.extend(generate_y_ions(sequence, charge))
    
    # Add precursor ion
    fragment_ions.append(FragmentIon(
        ion_type=FragmentType.PRECURSOR,
        position=0,
        mass=precursor_mz,
        charge=precursor_charge,
        sequence=sequence,
        intensity=20.0,  # Lower intensity for precursor
        label=f"[M+{precursor_charge}H]^{precursor_charge}+"
    ))
    
    # Find base peak
    if fragment_ions:
        base_peak = max(fragment_ions, key=lambda x: x.intensity)
        base_peak_mz = base_peak.mass
        base_peak_int = base_peak.intensity
    else:
        base_peak_mz = precursor_mz
        base_peak_int = 100.0
    
    notes = [
        f"Theoretical spectrum for {sequence}",
        f"Precursor: {precursor_mz:.2f} m/z (z={precursor_charge})",
        f"Generated {len(fragment_ions)} fragment ions",
    ]
    
    return TheoreticalSpectrum(
        peptide_sequence=sequence,
        precursor_mz=precursor_mz,
        precursor_charge=precursor_charge,
        fragment_ions=fragment_ions,
        base_peak_mz=base_peak_mz,
        base_peak_intensity=base_peak_int,
        total_ions=len(fragment_ions),
        notes=notes
    )
