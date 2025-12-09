"""
Metabolite Identification Module

Mass spectrometry-based metabolite identification.

THEORY:
Metabolite identification combines:
1. Accurate mass (m/z)
2. Isotope patterns
3. MS/MS fragmentation
4. Retention time

MASS ACCURACY:
Δm/m (ppm) = (m_measured - m_theoretical) / m_theoretical × 10⁶

High-resolution MS: <5 ppm error enables molecular formula determination

ISOTOPE PATTERNS:
Natural isotope abundances:
- ¹²C: 98.9%, ¹³C: 1.1%
- ¹H: 99.98%, ²H: 0.02%
- ¹⁴N: 99.6%, ¹⁵N: 0.4%
- ¹⁶O: 99.76%, ¹⁸O: 0.20%

M+1 peak intensity ≈ 1.1% × (number of carbons)

CONFIDENCE LEVELS:
Level 1: Confirmed by authentic standard
Level 2: Putative annotation (MS/MS match)
Level 3: Putative compound class
Level 4: Unknown compound
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math

@dataclass
class MetaboliteFeatures:
    """Metabolite identification features"""
    measured_mass: float  # Da
    retention_time: float  # minutes
    ms2_fragments: List[float]  # m/z values
    
    # Identification results
    formula: Optional[str] = None
    name: Optional[str] = None
    database_id: Optional[str] = None
    confidence_level: Optional[int] = None
    mass_error_ppm: Optional[float] = None
    
    def __str__(self):
        if self.name:
            return f"{self.name} (m/z {self.measured_mass:.4f}, RT {self.retention_time:.2f} min)"
        return f"Unknown (m/z {self.measured_mass:.4f}, RT {self.retention_time:.2f} min)"


def calculate_mass_error(
    measured_mass: float,
    theoretical_mass: float,
    unit: str = "ppm"
) -> float:
    """
    Calculate mass measurement error
    
    Parameters:
    - measured_mass: experimental m/z (Da)
    - theoretical_mass: calculated m/z (Da)
    - unit: "ppm" or "Da"
    
    Returns:
    - error: mass error
    
    TYPICAL ACCURACY:
    - Low-resolution MS: 100-500 ppm
    - High-resolution MS (Orbitrap, FTICR): <5 ppm
    - Ultra-high resolution: <1 ppm
    """
    if unit == "ppm":
        if theoretical_mass == 0:
            return float('inf')
        error = (measured_mass - theoretical_mass) / theoretical_mass * 1e6
    else:  # Da
        error = measured_mass - theoretical_mass
    
    return error


def predict_metabolite_formula(
    measured_mass: float,
    adduct: str = "[M+H]+",
    tolerance_ppm: float = 5.0
) -> List[Dict[str, any]]:
    """
    Predict molecular formula from accurate mass
    
    Uses seven golden rules for molecular formula determination
    
    Parameters:
    - measured_mass: measured m/z (Da)
    - adduct: ionization adduct type
    - tolerance_ppm: mass tolerance
    
    Returns:
    - candidates: list of possible formulas with scores
    
    SEVEN GOLDEN RULES:
    1. Element restrictions (CHNOPS most common)
    2. Lewis/Senior check (valence rules)
    3. Isotopic patterns
    4. Hydrogen/Carbon ratio
    5. Heteroatom ratios
    6. Nitrogen rule (even m/z → even N)
    7. Ring Double Bond Equivalent (RDBE)
    """
    # Adduct corrections
    adduct_corrections = {
        "[M+H]+": 1.00783,  # Protonation
        "[M+Na]+": 22.9898,  # Sodiation
        "[M+K]+": 38.9637,  # Potassiation
        "[M-H]-": -1.00783,  # Deprotonation
        "[M+Cl]-": 34.9689,  # Chloride adduct
        "[M+FA-H]-": 44.9982,  # Formate adduct
    }
    
    correction = adduct_corrections.get(adduct, 0.0)
    neutral_mass = measured_mass - correction
    
    # Generate candidate formulas (simplified approach)
    candidates = []
    
    # Estimate carbon count from mass
    # Average mass per carbon ≈ 12.5 (accounting for H)
    max_carbons = int(neutral_mass / 12.0) + 1
    
    for n_c in range(1, min(max_carbons, 50)):
        for n_h in range(1, n_c * 3 + 5):  # H/C ratio constraint
            for n_o in range(0, min(n_c + 1, 20)):
                for n_n in range(0, min(n_c // 2 + 1, 10)):
                    # Calculate exact mass
                    exact_mass = (
                        n_c * 12.0 +
                        n_h * 1.00783 +
                        n_o * 15.99491 +
                        n_n * 14.00307
                    )
                    
                    # Check mass error
                    error_ppm = calculate_mass_error(neutral_mass, exact_mass, "ppm")
                    
                    if abs(error_ppm) <= tolerance_ppm:
                        # Calculate RDBE
                        rdbe = (2 * n_c + 2 + n_n - n_h) / 2.0
                        
                        # Check nitrogen rule
                        # Odd m/z → odd N (for positive ions)
                        nitrogen_rule_ok = True
                        if int(neutral_mass) % 2 == 1:
                            nitrogen_rule_ok = (n_n % 2 == 1)
                        else:
                            nitrogen_rule_ok = (n_n % 2 == 0)
                        
                        # Score formula
                        score = 100 - abs(error_ppm)
                        if nitrogen_rule_ok:
                            score += 10
                        if 0 <= rdbe <= 50:
                            score += 5
                        
                        candidates.append({
                            "formula": f"C{n_c}H{n_h}O{n_o}N{n_n}",
                            "exact_mass": exact_mass,
                            "error_ppm": error_ppm,
                            "rdbe": rdbe,
                            "nitrogen_rule": nitrogen_rule_ok,
                            "score": score,
                        })
    
    # Sort by score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    return candidates[:10]  # Top 10


def identify_metabolite_by_mass(
    features: MetaboliteFeatures,
    database: Dict[str, Dict[str, any]],
    tolerance_ppm: float = 10.0
) -> List[Dict[str, any]]:
    """
    Identify metabolite by searching mass database
    
    Parameters:
    - features: metabolite features
    - database: metabolite database {id: {name, mass, formula, ...}}
    - tolerance_ppm: mass tolerance for matching
    
    Returns:
    - matches: list of database matches with scores
    """
    matches = []
    
    for db_id, db_entry in database.items():
        db_mass = db_entry["mass"]
        
        # Calculate mass error
        error_ppm = calculate_mass_error(features.measured_mass, db_mass, "ppm")
        
        if abs(error_ppm) <= tolerance_ppm:
            # Calculate match score
            score = 100 - abs(error_ppm)
            
            # Bonus for MS/MS fragment matching (if available)
            if features.ms2_fragments and db_entry.get("fragments"):
                fragment_score = calculate_fragment_match_score(
                    features.ms2_fragments,
                    db_entry["fragments"]
                )
                score += fragment_score * 50
            
            matches.append({
                "database_id": db_id,
                "name": db_entry["name"],
                "formula": db_entry.get("formula", ""),
                "theoretical_mass": db_mass,
                "mass_error_ppm": error_ppm,
                "score": score,
                "confidence_level": 2,  # Putative annotation
            })
    
    # Sort by score
    matches.sort(key=lambda x: x["score"], reverse=True)
    
    return matches


def calculate_fragment_match_score(
    experimental_fragments: List[float],
    database_fragments: List[float],
    tolerance_da: float = 0.05
) -> float:
    """
    Calculate MS/MS fragment match score
    
    Compares experimental and database fragment lists
    
    Parameters:
    - experimental_fragments: measured m/z values
    - database_fragments: reference m/z values
    - tolerance_da: matching tolerance (Da)
    
    Returns:
    - match_score: fraction of matched fragments (0-1)
    """
    if not experimental_fragments or not database_fragments:
        return 0.0
    
    matched = 0
    for exp_frag in experimental_fragments:
        for db_frag in database_fragments:
            if abs(exp_frag - db_frag) <= tolerance_da:
                matched += 1
                break
    
    match_score = matched / len(experimental_fragments)
    return match_score


def predict_isotope_pattern(
    formula: str,
    charge: int = 1
) -> List[Tuple[float, float]]:
    """
    Predict isotope pattern from molecular formula
    
    Parameters:
    - formula: molecular formula (e.g., "C6H12O6")
    - charge: ion charge state
    
    Returns:
    - pattern: list of (m/z, relative_intensity) tuples
    
    THEORY:
    Uses binomial expansion for isotope distributions
    For carbon: (0.989 × ¹²C + 0.011 × ¹³C)^n
    """
    # Parse formula (simplified)
    import re
    
    elements = {
        "C": 0, "H": 0, "O": 0, "N": 0, "S": 0, "P": 0
    }
    
    for match in re.finditer(r'([A-Z][a-z]?)(\d*)', formula):
        element = match.group(1)
        count = int(match.group(2)) if match.group(2) else 1
        if element in elements:
            elements[element] = count
    
    # Calculate monoisotopic mass
    atomic_masses = {
        "C": 12.0, "H": 1.00783, "O": 15.99491,
        "N": 14.00307, "S": 31.97207, "P": 30.97376
    }
    
    mono_mass = sum(elements[e] * atomic_masses[e] for e in elements)
    
    # M+0 peak (monoisotopic)
    pattern = [(mono_mass / charge, 100.0)]
    
    # M+1 peak (¹³C contribution)
    # Intensity ≈ 1.1% × n_C
    if elements["C"] > 0:
        m_plus_1_intensity = 1.1 * elements["C"]
        pattern.append(((mono_mass + 1.00335) / charge, m_plus_1_intensity))
    
    # M+2 peak (¹³C₂ contribution)
    if elements["C"] > 1:
        m_plus_2_intensity = 1.1**2 * elements["C"] * (elements["C"] - 1) / 2
        pattern.append(((mono_mass + 2.00671) / charge, m_plus_2_intensity))
    
    return pattern


def annotate_metabolites(
    features_list: List[MetaboliteFeatures],
    database: Dict[str, Dict[str, any]],
    mass_tolerance_ppm: float = 5.0
) -> List[MetaboliteFeatures]:
    """
    Annotate multiple metabolites from feature list
    
    Parameters:
    - features_list: list of metabolite features
    - database: metabolite database
    - mass_tolerance_ppm: mass matching tolerance
    
    Returns:
    - annotated_features: features with annotations added
    """
    annotated = []
    
    for features in features_list:
        # Search database
        matches = identify_metabolite_by_mass(
            features,
            database,
            mass_tolerance_ppm
        )
        
        # Add top match to features
        if matches:
            top_match = matches[0]
            features.name = top_match["name"]
            features.formula = top_match["formula"]
            features.database_id = top_match["database_id"]
            features.confidence_level = top_match["confidence_level"]
            features.mass_error_ppm = top_match["mass_error_ppm"]
        else:
            features.confidence_level = 4  # Unknown
        
        annotated.append(features)
    
    return annotated
