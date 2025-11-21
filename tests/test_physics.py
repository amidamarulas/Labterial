import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from labterial.physics import simular_ensayo
except ImportError:
    from src.labterial.physics import simular_ensayo

class TestPhysicsEngine(unittest.TestCase):

    def test_ductilidad_dinamica_metal(self):
        """Verifica ductilidad variable."""
        # Cobre (Dúctil)
        props_d = {'elastic_modulus': 110000, 'yield_strength': 69, 'ultimate_strength': 220, 'category': 'Metal'}
        df_d = simular_ensayo(props_d, 'Tension', max_strain_machine=0.60)
        
        # Acero Duro (Frágil)
        props_f = {'elastic_modulus': 210000, 'yield_strength': 900, 'ultimate_strength': 950, 'category': 'Metal'}
        df_f = simular_ensayo(props_f, 'Tension', max_strain_machine=0.60)
        
        def get_rupture(df):
            valid = df[df['Esfuerzo (MPa)'].notna() & (df['Esfuerzo (MPa)'] > 0)]
            if valid.empty: return 0
            return valid['Deformacion (mm/mm)'].max()

        self.assertGreater(get_rupture(df_d), get_rupture(df_f))

    def test_flexion_calculo(self):
        """
        Prueba Flexión y MOR.
        CORRECCIÓN: Aumentamos max_strain_machine a 0.5 (50%) para asegurar
        que la simulación alcance el pico máximo antes de detenerse.
        """
        props = {'elastic_modulus': 200000, 'yield_strength': 250, 'ultimate_strength': 400, 'category': 'Metal'}
        
        # Simulación Flexión con rango amplio
        df_flexion = simular_ensayo(props, 'Flexion', max_strain_machine=0.5)
        max_stress_flexion = df_flexion['Esfuerzo (MPa)'].max()
        
        # El esfuerzo maximo debe ser aprox 1.2 * 400 = 480
        self.assertAlmostEqual(max_stress_flexion, 480.0, delta=15)

    def test_torsion_shear_modulus(self):
        E = 200000; Nu = 0.3
        G_teorico = E / (2 * (1 + Nu))
        props = {'elastic_modulus': E, 'yield_strength': 250, 'poisson_ratio': Nu, 'category': 'Metal'}
        
        df = simular_ensayo(props, 'Torsion', max_strain_machine=0.001)
        gamma = df['Deformacion (rad)'].iloc[1]
        tau = df['Esfuerzo (MPa)'].iloc[1]
        
        self.assertAlmostEqual(tau/gamma, G_teorico, delta=100)

if __name__ == '__main__':
    unittest.main()
