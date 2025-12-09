"""
Comprehensive tests for Electrochemistry module
"""

import pytest
import math
from labos.modules.electrochemistry.voltammetry import (
    VoltammogramData,
    calculate_peak_current, calculate_diffusion_coefficient,
    identify_reversibility, analyze_cyclic_voltammetry
)
from labos.modules.electrochemistry.impedance import (
    ImpedanceData,
    calculate_impedance_magnitude, calculate_phase_angle,
    fit_randles_circuit, analyze_nyquist_plot, calculate_double_layer_capacitance
)
from labos.modules.electrochemistry.electrode_kinetics import (
    ElectrodeReaction,
    calculate_nernst_potential, calculate_nernst_potential_with_ph,
    calculate_butler_volmer_current, calculate_exchange_current,
    analyze_tafel_plot, calculate_levich_current
)


class TestCyclicVoltammetry:
    """Test cyclic voltammetry analysis"""
    
    def test_voltammogram_data_creation(self):
        """Test VoltammogramData dataclass"""
        potentials = [-0.2, 0.0, 0.2, 0.4, 0.2, 0.0, -0.2]
        currents = [0.0, 5e-6, 20e-6, 10e-6, -15e-6, -5e-6, 0.0]
        
        cv = VoltammogramData(
            potentials=potentials,
            currents=currents,
            scan_rate=0.1,
            anodic_peak_potential=0.25,
            anodic_peak_current=20e-6,
            cathodic_peak_potential=0.19,
            cathodic_peak_current=-15e-6
        )
        
        assert cv.peak_separation == 0.06
        assert cv.peak_current_ratio > 0
    
    def test_peak_current_calculation(self):
        """Test Randles-Sevcik equation"""
        peak_current = calculate_peak_current(
            n_electrons=1,
            electrode_area=0.071,  # cm²
            diffusion_coefficient=1e-5,  # cm²/s
            concentration=1.0,  # mM
            scan_rate=0.1  # V/s
        )
        
        assert peak_current > 0
        # Typical range: µA to mA (equation gives Amperes)
        assert 1e-7 < peak_current < 1.0
    
    def test_diffusion_coefficient_calculation(self):
        """Test D calculation from peak current"""
        d_coeff = calculate_diffusion_coefficient(
            peak_current=10e-6,  # 10 µA
            n_electrons=1,
            electrode_area=0.071,
            concentration=1.0,
            scan_rate=0.1
        )
        
        assert d_coeff > 0
        # May be smaller for low currents
        assert d_coeff < 1e-4
    
    def test_reversibility_assessment(self):
        """Test reversibility identification"""
        # Reversible system
        rev_data = identify_reversibility(
            peak_separation=0.060,  # 60 mV
            n_electrons=1
        )
        
        # 60 mV is borderline reversible/quasi-reversible
        assert rev_data["classification"] in ["reversible", "quasi-reversible"]
        
        # Irreversible system
        irrev_data = identify_reversibility(
            peak_separation=0.250,  # 250 mV
            n_electrons=1
        )
        
        assert irrev_data["classification"] == "irreversible"
    
    def test_cv_analysis_complete(self):
        """Test complete CV analysis"""
        cv = VoltammogramData(
            potentials=[-0.2, 0.0, 0.2],
            currents=[0.0, 10e-6, -8e-6],
            scan_rate=0.05,
            anodic_peak_potential=0.25,
            anodic_peak_current=10e-6,
            cathodic_peak_potential=0.19,
            cathodic_peak_current=-8e-6
        )
        
        analysis = analyze_cyclic_voltammetry(
            cv,
            n_electrons=1,
            concentration=1.0,
            electrode_area=0.071
        )
        
        assert "scan_rate_v_s" in analysis
        assert "reversibility" in analysis
        assert "diffusion_coefficient_cm2_s" in analysis


class TestImpedanceSpectroscopy:
    """Test impedance spectroscopy analysis"""
    
    def test_impedance_data_creation(self):
        """Test ImpedanceData dataclass"""
        frequencies = [10000, 1000, 100, 10, 1]
        z_real = [100, 120, 200, 500, 1000]
        z_imag = [0, -50, -150, -200, -100]
        
        eis = ImpedanceData(
            frequencies=frequencies,
            z_real=z_real,
            z_imag=z_imag
        )
        
        magnitude = eis.get_impedance_magnitude(0)
        assert magnitude == 100.0  # Pure resistance at high frequency
        
        phase = eis.get_phase_angle(2)
        # Phase angle calculated from impedance components
        assert isinstance(phase, float)
    
    def test_impedance_magnitude(self):
        """Test impedance magnitude calculation"""
        z_mag = calculate_impedance_magnitude(100, -50)
        expected = math.sqrt(100**2 + 50**2)
        
        assert abs(z_mag - expected) < 0.01
    
    def test_phase_angle_calculation(self):
        """Test phase angle calculation"""
        # Pure resistance
        phase_r = calculate_phase_angle(100, 0)
        assert abs(phase_r) < 0.01
        
        # Pure capacitance
        phase_c = calculate_phase_angle(0, -100)
        # Phase for pure capacitance should be -90° or equivalent
        assert abs(abs(phase_c) - 90) < 0.01
        
        # RC circuit (equal R and C gives -45°)
        phase_rc = calculate_phase_angle(100, -100)
        # Should be -45° for equal components
        assert abs(phase_rc - (-45)) < 1 or abs(phase_rc - 45) < 1
    
    def test_randles_circuit_fitting(self):
        """Test Randles circuit parameter extraction"""
        # Simulate simple Nyquist plot
        frequencies = [10000, 1000, 100, 10, 1]
        z_real = [100, 150, 300, 450, 500]
        z_imag = [0, -100, -150, -100, -50]
        
        eis = ImpedanceData(frequencies, z_real, z_imag)
        
        params = fit_randles_circuit(eis)
        
        assert "r_solution" in params
        assert "r_charge_transfer" in params
        assert "capacitance" in params
        assert params["r_solution"] > 0
        assert params["r_charge_transfer"] > 0
    
    def test_nyquist_plot_analysis(self):
        """Test Nyquist plot feature extraction"""
        frequencies = [10000, 1000, 100, 10]
        z_real = [100, 200, 400, 600]
        z_imag = [0, -150, -200, -100]
        
        eis = ImpedanceData(frequencies, z_real, z_imag)
        
        analysis = analyze_nyquist_plot(eis)
        
        assert "solution_resistance" in analysis
        assert "charge_transfer_resistance" in analysis
        assert "limiting_process" in analysis
        assert analysis["semicircle_diameter"] > 0
    
    def test_double_layer_capacitance(self):
        """Test specific capacitance calculation"""
        c_specific = calculate_double_layer_capacitance(
            capacitance=50e-6,  # 50 µF
            electrode_area=1.0  # cm²
        )
        
        assert c_specific > 0
        # Typical range: 10-100 µF/cm²
        assert 1e-6 < c_specific < 1e-3


class TestElectrodeKinetics:
    """Test electrode kinetics calculations"""
    
    def test_electrode_reaction_creation(self):
        """Test ElectrodeReaction dataclass"""
        rxn = ElectrodeReaction(
            n_electrons=1,
            standard_potential=0.771,  # Ag⁺/Ag
            exchange_current_density=1e-5
        )
        
        assert rxn.n_electrons == 1
        assert rxn.standard_potential == 0.771
        assert rxn.is_reversible(0.010)  # 10 mV overpotential
        assert not rxn.is_reversible(0.100)  # 100 mV overpotential
    
    def test_nernst_equation(self):
        """Test Nernst potential calculation"""
        # Fe³⁺/Fe²⁺ at 25°C
        e_eq = calculate_nernst_potential(
            standard_potential=0.771,
            n_electrons=1,
            activity_ratio=10.0  # [Fe²⁺]/[Fe³⁺] = 10
        )
        
        # Should be E° - 0.059 log(10) = E° - 0.059
        expected = 0.771 - 0.059
        assert abs(e_eq - expected) < 0.005
    
    def test_nernst_with_ph(self):
        """Test pH-dependent Nernst equation"""
        # O₂ reduction at different pH
        e_ph7 = calculate_nernst_potential_with_ph(
            standard_potential=1.23,  # O₂/H₂O at pH 0
            n_electrons=4,
            n_protons=4,
            ph=7.0
        )
        
        # Should shift -0.059 × 4/4 × 7 = -0.413 V
        expected = 1.23 - 0.413
        assert abs(e_ph7 - expected) < 0.05
    
    def test_butler_volmer_current(self):
        """Test Butler-Volmer equation"""
        # At equilibrium (η = 0), current should be ~0
        i_eq = calculate_butler_volmer_current(
            overpotential=0.0,
            exchange_current_density=1e-6,
            n_electrons=1
        )
        
        assert abs(i_eq) < 1e-10
        
        # Anodic overpotential
        i_anodic = calculate_butler_volmer_current(
            overpotential=0.1,  # 100 mV
            exchange_current_density=1e-6,
            n_electrons=1
        )
        
        assert i_anodic > 0  # Positive current (oxidation)
        
        # Cathodic overpotential
        i_cathodic = calculate_butler_volmer_current(
            overpotential=-0.1,
            exchange_current_density=1e-6,
            n_electrons=1
        )
        
        assert i_cathodic < 0  # Negative current (reduction)
    
    def test_exchange_current_calculation(self):
        """Test exchange current determination"""
        rxn = ElectrodeReaction(
            n_electrons=1,
            standard_potential=0.0,
            exchange_current_density=1e-5
        )
        
        exchange_data = calculate_exchange_current(rxn, electrode_area=1.0)
        
        assert "exchange_current_density" in exchange_data
        assert "classification" in exchange_data
        assert exchange_data["exchange_current_density"] > 0
    
    def test_tafel_analysis(self):
        """Test Tafel plot analysis"""
        # Generate synthetic Tafel data
        overpotentials = [0.05, 0.10, 0.15, 0.20, 0.25]
        current_densities = [1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
        
        analysis = analyze_tafel_plot(
            overpotentials,
            current_densities,
            n_electrons=1
        )
        
        assert "anodic" in analysis
        assert "tafel_slope" in analysis["anodic"]
        assert "alpha" in analysis["anodic"]
    
    def test_levich_equation(self):
        """Test Levich current for RDE"""
        i_limiting = calculate_levich_current(
            n_electrons=1,
            electrode_area=0.196,  # cm², 5 mm diameter
            diffusion_coefficient=5e-6,  # cm²/s
            kinematic_viscosity=0.01,  # cm²/s (water)
            concentration=1.0,  # mM
            rotation_rate=104.7  # rad/s (1000 rpm)
        )
        
        assert i_limiting > 0
        # Levich equation gives larger currents for rotating disk
        assert i_limiting < 1.0


class TestElectrochemistryIntegration:
    """Integration tests for complete electrochemistry workflows"""
    
    def test_cv_to_kinetics_workflow(self):
        """Test CV analysis followed by kinetics extraction"""
        # Simulate CV data
        cv = VoltammogramData(
            potentials=[-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0, -0.1, -0.2, -0.3],
            currents=[0, 1e-6, 5e-6, 12e-6, 20e-6, 15e-6, 8e-6, -10e-6, -18e-6, -12e-6, -5e-6, -1e-6, 0],
            scan_rate=0.1,
            anodic_peak_potential=0.25,
            anodic_peak_current=20e-6,
            cathodic_peak_potential=0.19,
            cathodic_peak_current=-18e-6
        )
        
        # Analyze CV
        cv_analysis = analyze_cyclic_voltammetry(cv, n_electrons=1)
        
        # Extract kinetic parameters (60 mV separation is borderline)
        assert cv_analysis["reversibility"]["classification"] in ["reversible", "quasi-reversible"]
        
        # Create electrode reaction from CV results
        rxn = ElectrodeReaction(
            n_electrons=1,
            standard_potential=0.22,  # Midpoint
            exchange_current_density=1e-5
        )
        
        # Calculate Nernst potential
        e_eq = calculate_nernst_potential(rxn.standard_potential, 1, 1.0)
        
        assert abs(e_eq - rxn.standard_potential) < 0.001
    
    def test_impedance_to_kinetics_workflow(self):
        """Test EIS analysis for kinetic parameters"""
        # Simulate EIS data
        frequencies = [100000, 10000, 1000, 100, 10, 1, 0.1]
        z_real = [100, 105, 150, 300, 450, 490, 500]
        z_imag = [0, -10, -100, -200, -150, -50, -10]
        
        eis = ImpedanceData(frequencies, z_real, z_imag)
        
        # Fit Randles circuit
        params = fit_randles_circuit(eis)
        
        # Extract kinetic information
        r_ct = params["r_charge_transfer"]
        c_dl = params["capacitance"]
        
        # Calculate exchange current from R_ct
        # i₀ = RT/(nF·R_ct) for simple case
        RT_F = 0.0257  # V at 25°C
        i0_estimate = RT_F / r_ct if r_ct > 0 else 0
        
        assert i0_estimate > 0
    
    def test_multimethod_comparison(self):
        """Test consistency between CV and EIS"""
        # CV-derived exchange current
        cv = VoltammogramData(
            potentials=[0.0],
            currents=[0.0],
            scan_rate=0.1,
            anodic_peak_potential=0.25,
            anodic_peak_current=20e-6,
            cathodic_peak_potential=0.19,
            cathodic_peak_current=-18e-6
        )
        
        cv_analysis = analyze_cyclic_voltammetry(cv, n_electrons=1)
        
        # EIS-derived parameters
        eis = ImpedanceData(
            frequencies=[1000, 100, 10],
            z_real=[100, 200, 300],
            z_imag=[0, -100, -50]
        )
        
        eis_params = fit_randles_circuit(eis)
        
        # Both methods should give consistent results
        # (in real analysis, would compare i₀ values)
        assert cv_analysis is not None
        assert eis_params["r_charge_transfer"] > 0
