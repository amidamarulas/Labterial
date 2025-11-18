import unittest
import sys
import os

# Agregar src al path para poder importar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from physics import simular_ensayo

class TestPhysics(unittest.TestCase):
    def test_hooke_law_tension(self):
        props = {'elastic_modulus': 1000, 'yield_strength': 10}
        # Deformacion muy pequeña (zona elastica)
        df = simular_ensayo(props, 'Tension', max_strain=0.005)
        sigma = df['Esfuerzo (MPa)'].iloc[-1]
        epsilon = df['Deformacion (mm/mm)'].iloc[-1]
        
        # Sigma = E * epsilon -> 1000 * 0.005 = 5.0
        self.assertAlmostEqual(sigma, 5.0, places=2)

    def test_compression_sign(self):
        props = {'elastic_modulus': 1000, 'yield_strength': 10}
        df = simular_ensayo(props, 'Compresion', max_strain=0.005)
        sigma = df['Esfuerzo (MPa)'].iloc[-1]
        
        # En compresion el esfuerzo debe ser negativo
        self.assertTrue(sigma < 0)

if __name__ == '__main__':
    unittest.main()
