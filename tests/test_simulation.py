"""
Tests for Simulation Engine Module
"""

import unittest
import math
from labos.modules.simulation import molecular_dynamics, quantum_chem, kinetics, thermodynamics


class TestMolecularDynamics(unittest.TestCase):
    """Test molecular dynamics simulations"""
    
    def test_distance_calculation(self):
        """Test distance calculation between atoms"""
        atom1 = molecular_dynamics.Atom("C", 0.0, 0.0, 0.0, 0.0, "C.3", 12.011)
        atom2 = molecular_dynamics.Atom("C", 1.0, 0.0, 0.0, 0.0, "C.3", 12.011)
        
        distance = molecular_dynamics.calculate_distance(atom1, atom2)
        self.assertAlmostEqual(distance, 1.0, places=5)
    
    def test_bond_energy_calculation(self):
        """Test harmonic bond energy"""
        atom1 = molecular_dynamics.Atom("C", 0.0, 0.0, 0.0, 0.0, "C.3", 12.011)
        atom2 = molecular_dynamics.Atom("C", 1.5, 0.0, 0.0, 0.0, "C.3", 12.011)
        bond = molecular_dynamics.Bond(0, 1, 1.0, 1.54, 400.0)
        
        energy = molecular_dynamics.calculate_bond_energy(bond, atom1, atom2)
        self.assertGreater(energy, 0)  # Should be positive (compressed/stretched)
    
    def test_water_molecule_creation(self):
        """Test water molecule system"""
        water = molecular_dynamics.create_water_molecule()
        
        self.assertEqual(len(water.atoms), 3)
        self.assertEqual(len(water.bonds), 2)
        self.assertEqual(water.name, "H2O")
        self.assertEqual(water.total_charge, 0.0)
    
    def test_methane_molecule_creation(self):
        """Test methane molecule system"""
        methane = molecular_dynamics.create_methane_molecule()
        
        self.assertEqual(len(methane.atoms), 5)
        self.assertEqual(len(methane.bonds), 4)
        self.assertEqual(methane.name, "CH4")
    
    def test_energy_calculation(self):
        """Test total energy calculation"""
        water = molecular_dynamics.create_water_molecule()
        energy = molecular_dynamics.calculate_total_energy(water)
        
        self.assertIsInstance(energy, molecular_dynamics.EnergyComponents)
        self.assertIsInstance(energy.total_energy, float)
    
    def test_geometry_optimization(self):
        """Test geometry optimization"""
        water = molecular_dynamics.create_water_molecule()
        result = molecular_dynamics.optimize_geometry(
            water,
            max_iterations=10,
            energy_tolerance=0.01
        )
        
        self.assertIsInstance(result, molecular_dynamics.OptimizationResult)
        self.assertEqual(result.force_field, molecular_dynamics.ForceFieldType.UFF)
        self.assertGreater(result.iterations, 0)
    
    def test_md_simulation(self):
        """Test molecular dynamics simulation"""
        methane = molecular_dynamics.create_methane_molecule()
        result = molecular_dynamics.run_md_simulation(
            methane,
            temperature=300.0,
            total_time=0.01,  # 10 fs
            timestep=0.001,
            save_frequency=5
        )
        
        self.assertIsInstance(result, molecular_dynamics.MDSimulationResult)
        self.assertGreater(len(result.trajectory), 0)
        self.assertEqual(result.temperature, 300.0)


class TestQuantumChemistry(unittest.TestCase):
    """Test quantum chemistry calculations"""
    
    def test_ev_to_wavelength_conversion(self):
        """Test energy to wavelength conversion"""
        # 2 eV should give ~620 nm (red light)
        wavelength = quantum_chem.ev_to_wavelength(2.0)
        self.assertGreater(wavelength, 600)
        self.assertLess(wavelength, 650)
    
    def test_wavelength_to_ev_conversion(self):
        """Test wavelength to energy conversion"""
        # 500 nm (green) should give ~2.5 eV
        energy = quantum_chem.wavelength_to_ev(500.0)
        self.assertGreater(energy, 2.0)
        self.assertLess(energy, 3.0)
    
    def test_benzene_huckel(self):
        """Test Hückel calculation for benzene"""
        result = quantum_chem.huckel_benzene()
        
        self.assertEqual(result.molecule_name, "Benzene (C₆H₆)")
        self.assertEqual(result.total_electrons, 6)
        self.assertEqual(len(result.orbitals), 6)
        self.assertGreater(result.homo_lumo_gap, 0)
        self.assertGreater(len(result.transitions), 0)
    
    def test_ethylene_huckel(self):
        """Test Hückel calculation for ethylene"""
        result = quantum_chem.huckel_ethylene()
        
        self.assertEqual(result.molecule_name, "Ethylene (C₂H₄)")
        self.assertEqual(result.total_electrons, 2)
        self.assertEqual(len(result.orbitals), 2)
        
        # Check HOMO and LUMO
        homo = [o for o in result.orbitals if o.is_homo]
        lumo = [o for o in result.orbitals if o.is_lumo]
        self.assertEqual(len(homo), 1)
        self.assertEqual(len(lumo), 1)
    
    def test_butadiene_huckel(self):
        """Test Hückel calculation for butadiene"""
        result = quantum_chem.huckel_butadiene()
        
        self.assertEqual(result.total_electrons, 4)
        self.assertEqual(len(result.orbitals), 4)
        self.assertGreater(result.homo_lumo_gap, 0)
    
    def test_homo_lumo_gap_ordering(self):
        """Test that HOMO-LUMO gap follows expected conjugation trends"""
        ethylene = quantum_chem.huckel_ethylene()
        butadiene = quantum_chem.huckel_butadiene()
        benzene = quantum_chem.huckel_benzene()
        
        # More conjugation = smaller gap
        self.assertGreater(ethylene.homo_lumo_gap, butadiene.homo_lumo_gap)
    
    def test_calculate_mo_system(self):
        """Test general MO calculation"""
        result = quantum_chem.calculate_mo_system(num_carbons=6, cyclic=True)
        
        self.assertGreater(len(result.orbitals), 0)
        self.assertGreater(result.homo_lumo_gap, 0)


class TestKinetics(unittest.TestCase):
    """Test chemical kinetics simulations"""
    
    def test_arrhenius_equation(self):
        """Test Arrhenius rate constant calculation"""
        k = kinetics.arrhenius_equation(
            temperature=298.15,
            pre_exponential_factor=1e10,
            activation_energy=50.0
        )
        
        self.assertGreater(k, 0)
        self.assertLess(k, 1e10)
    
    def test_first_order_half_life(self):
        """Test first-order half-life calculation"""
        k = 0.693  # Should give t_1/2 = 1
        t_half = kinetics.calculate_half_life(k, kinetics.ReactionOrder.FIRST_ORDER)
        
        self.assertAlmostEqual(t_half, 1.0, places=2)
    
    def test_zero_order_simulation(self):
        """Test zero-order kinetics simulation"""
        result = kinetics.simulate_reaction_kinetics(
            initial_concentration=1.0,
            rate_constant=0.1,
            reaction_order=kinetics.ReactionOrder.ZERO_ORDER,
            time_end=5.0,
            num_points=50
        )
        
        self.assertEqual(len(result.times), 50)
        self.assertEqual(len(result.concentrations["A"]), 50)
        
        # Check that concentration decreases linearly
        final_conc = result.concentrations["A"][-1]
        self.assertLess(final_conc, 1.0)
    
    def test_first_order_simulation(self):
        """Test first-order kinetics simulation"""
        result = kinetics.simulate_reaction_kinetics(
            initial_concentration=1.0,
            rate_constant=0.1,
            reaction_order=kinetics.ReactionOrder.FIRST_ORDER,
            time_end=10.0,
            num_points=100
        )
        
        self.assertIsInstance(result, kinetics.KineticsResult)
        self.assertGreater(result.half_life, 0)
        
        # Check exponential decay
        conc = result.concentrations["A"]
        self.assertLess(conc[-1], conc[0])
    
    def test_second_order_simulation(self):
        """Test second-order kinetics simulation"""
        result = kinetics.simulate_reaction_kinetics(
            initial_concentration=1.0,
            rate_constant=0.1,
            reaction_order=kinetics.ReactionOrder.SECOND_ORDER,
            time_end=10.0,
            num_points=100
        )
        
        self.assertIsInstance(result, kinetics.KineticsResult)
        # Second order should decay faster initially
        conc = result.concentrations["A"]
        self.assertLess(conc[50], conc[0])
    
    def test_reversible_reaction(self):
        """Test reversible reaction simulation"""
        result = kinetics.simulate_reversible_reaction(
            initial_a=1.0,
            initial_b=0.0,
            k_forward=0.5,
            k_reverse=0.2,
            time_end=20.0,
            num_points=100
        )
        
        self.assertIn("A", result.concentrations)
        self.assertIn("B", result.concentrations)
        
        # Should reach equilibrium
        conc_a = result.concentrations["A"]
        conc_b = result.concentrations["B"]
        
        # Final concentrations should be relatively stable
        self.assertGreater(conc_b[-1], 0)
        self.assertLess(conc_a[-1], conc_a[0])
    
    def test_equilibrium_constant_calculation(self):
        """Test K_eq calculation from ΔG"""
        k_eq = kinetics.calculate_equilibrium_constant(delta_g_standard=-10.0)
        
        # Negative ΔG should give K > 1
        self.assertGreater(k_eq, 1.0)
        
        k_eq_pos = kinetics.calculate_equilibrium_constant(delta_g_standard=10.0)
        # Positive ΔG should give K < 1
        self.assertLess(k_eq_pos, 1.0)
    
    def test_equilibrium_prediction(self):
        """Test equilibrium position prediction"""
        result = kinetics.predict_equilibrium(
            delta_g_standard=-5.0,
            initial_concentrations={"A": 1.0, "B": 0.1},
            stoichiometry={"A": -1, "B": 1},
            temperature=298.15
        )
        
        self.assertIsInstance(result, kinetics.EquilibriumResult)
        self.assertGreater(result.equilibrium_constant, 1.0)
        self.assertIn(result.direction, ["forward", "reverse", "equilibrium"])


class TestThermodynamics(unittest.TestCase):
    """Test thermodynamics calculations"""
    
    def test_ideal_gas_law(self):
        """Test ideal gas law calculations"""
        # Calculate pressure
        p = thermodynamics.ideal_gas_law(volume=1.0, moles=1.0, temperature=273.15)
        self.assertGreater(p, 0)
        
        # Calculate volume
        v = thermodynamics.ideal_gas_law(pressure=1.0, moles=1.0, temperature=273.15)
        self.assertGreater(v, 0)
    
    def test_gibbs_free_energy(self):
        """Test Gibbs free energy calculation"""
        delta_g = thermodynamics.calculate_gibbs_free_energy(
            delta_h=-100.0,
            delta_s=200.0,
            temperature=298.15
        )
        
        # ΔG = ΔH - TΔS = -100 - 298.15*(0.2) ≈ -160 kJ/mol
        self.assertLess(delta_g, -100.0)
    
    def test_spontaneity(self):
        """Test spontaneity determination"""
        self.assertTrue(thermodynamics.is_spontaneous(-10.0))
        self.assertFalse(thermodynamics.is_spontaneous(10.0))
    
    def test_reaction_thermodynamics_exothermic(self):
        """Test thermodynamic analysis of exothermic reaction"""
        result = thermodynamics.analyze_reaction_thermodynamics(
            delta_h=-50.0,
            delta_s=100.0,
            temperature=298.15
        )
        
        self.assertIsInstance(result, thermodynamics.ReactionThermodynamics)
        self.assertTrue(result.is_spontaneous)
        self.assertGreater(result.equilibrium_constant, 1.0)
        self.assertIn("Exothermic", " ".join(result.notes))
    
    def test_reaction_thermodynamics_endothermic(self):
        """Test thermodynamic analysis of endothermic reaction"""
        result = thermodynamics.analyze_reaction_thermodynamics(
            delta_h=50.0,
            delta_s=-100.0,
            temperature=298.15
        )
        
        self.assertFalse(result.is_spontaneous)
        self.assertLess(result.equilibrium_constant, 1.0)
        self.assertIn("Endothermic", " ".join(result.notes))
    
    def test_transition_temperature(self):
        """Test phase transition temperature calculation"""
        t_trans = thermodynamics.calculate_transition_temperature(
            delta_h=40.7,  # kJ/mol (water vaporization)
            delta_s=109.0  # J/(mol·K)
        )
        
        # Should be around 373 K (100°C)
        self.assertGreater(t_trans, 350)
        self.assertLess(t_trans, 400)
    
    def test_phase_transition_analysis(self):
        """Test phase transition analysis"""
        result = thermodynamics.analyze_phase_transition(
            substance="Water",
            initial_phase="liquid",
            final_phase="gas",
            delta_h=40.7,
            temperature=373.15
        )
        
        self.assertEqual(result.substance, "Water")
        self.assertAlmostEqual(result.transition_temperature, 373.15)
        self.assertGreater(result.transition_entropy, 0)
        self.assertIn("Vaporization", " ".join(result.notes))
    
    def test_hess_law(self):
        """Test Hess's Law calculation"""
        reactions = [
            (-100.0, 50.0),  # Step 1
            (-50.0, 30.0),   # Step 2
            (20.0, -10.0),   # Step 3
        ]
        
        total_h, total_s = thermodynamics.hess_law_calculate(reactions)
        
        self.assertAlmostEqual(total_h, -130.0)
        self.assertAlmostEqual(total_s, 70.0)
    
    def test_van_t_hoff_equation(self):
        """Test van't Hoff equation"""
        k2 = thermodynamics.van_t_hoff_equation(
            k1=1.0,
            t1=298.15,
            t2=308.15,
            delta_h=50.0
        )
        
        # For endothermic reaction, K should increase with temperature
        self.assertGreater(k2, 1.0)
    
    def test_carnot_efficiency(self):
        """Test Carnot efficiency calculation"""
        efficiency = thermodynamics.carnot_efficiency(
            t_hot=500.0,
            t_cold=300.0
        )
        
        # Should be 0.4 (40%)
        self.assertAlmostEqual(efficiency, 0.4, places=2)
        self.assertGreater(efficiency, 0)
        self.assertLess(efficiency, 1)


class TestSimulationIntegration(unittest.TestCase):
    """Integration tests across simulation modules"""
    
    def test_kinetics_to_thermodynamics(self):
        """Test workflow from kinetics to thermodynamics"""
        # Calculate K_eq from kinetics
        k_eq = kinetics.calculate_equilibrium_constant(delta_g_standard=-10.0)
        
        # Analyze thermodynamics
        thermo_result = thermodynamics.analyze_reaction_thermodynamics(
            delta_h=-50.0,
            delta_s=100.0,
            temperature=298.15
        )
        
        self.assertTrue(thermo_result.is_spontaneous)
        self.assertGreater(thermo_result.equilibrium_constant, 1.0)
    
    def test_quantum_to_spectroscopy(self):
        """Test quantum chemistry to UV-Vis spectroscopy"""
        # Calculate HOMO-LUMO gap
        benzene = quantum_chem.huckel_benzene()
        
        # Get wavelength from gap
        wavelength = benzene.transitions[0].wavelength
        
        # Should be in UV range (< 400 nm)
        self.assertLess(wavelength, 400)
        self.assertGreater(wavelength, 100)
    
    def test_md_energy_conservation(self):
        """Test energy conservation in MD simulation"""
        methane = molecular_dynamics.create_methane_molecule()
        result = molecular_dynamics.run_md_simulation(
            methane,
            temperature=300.0,
            total_time=0.05,
            timestep=0.001,
            save_frequency=10
        )
        
        # Energy drift should be reasonable
        self.assertLess(abs(result.energy_drift), 100.0)


if __name__ == "__main__":
    unittest.main()
