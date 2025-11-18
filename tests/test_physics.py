import unittest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from physics import simular_ensayo

class TestPhysics(unittest.TestCase):
    def test_torsion_calculation(self):
        """Prueba que el modulo G se calcule bien: G = E / 2(1+v)"""
        E = 200000
        Nu = 0.3
        Sy = 250
        # G debería ser 200000 / 2.6 = 76923.07
        
        props = {'elastic_modulus': E, 'yield_strength': Sy, 'poisson_ratio': Nu}
        df = simular_ensayo(props, 'Torsion', max_strain=0.001)
        
        # Obtener esfuerzo y deformacion
        gamma = df.iloc[1]['Deformacion_Angular_rad']
        tau = df.iloc[1]['Esfuerzo_Cortante_MPa']
        
        # Calcular pendiente simulada
        G_simulado = tau / gamma
        G_teorico = E / (2 * (1 + Nu))
        
        self.assertAlmostEqual(G_simulado, G_teorico, places=0)

    def test_tension(self):
        props = {'elastic_modulus': 1000, 'yield_strength': 10, 'poisson_ratio': 0.3}
        df = simular_ensayo(props, 'Tension', max_strain=0.005)
        # Verificar que columna correcta existe
        self.assertIn('Esfuerzo_Normal_MPa', df.columns)

if __name__ == '__main__':
    unittest.main()
