import unittest
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import dinámico
try:
    from labterial.physics import simular_ensayo
except ImportError:
    from src.labterial.physics import simular_ensayo

class TestPhysicsEngine(unittest.TestCase):

    def test_tension_ductil(self):
        """Prueba un metal dúctil (Acero) en tensión."""
        props = {
            'elastic_modulus': 200000, 
            'yield_strength': 250, 
            'ultimate_strength': 400,
            'category': 'Metal'
        }
        # Slider al 30%, el acero rompe al ~18%
        df = simular_ensayo(props, 'Tension', max_strain_machine=0.30)
        
        # 1. Debe empezar en 0
        self.assertEqual(df['Esfuerzo (MPa)'].iloc[0], 0.0)
        
        # 2. Debe haber llegado a la rotura y luego tener valores nulos (corte)
        # Buscamos el pico maximo
        max_stress = df['Esfuerzo (MPa)'].max()
        self.assertAlmostEqual(max_stress, 400, delta=5) # Margen de error pequeño por interpolación
        
        # 3. Al final del array (30%) debe ser None o 0 porque ya rompió
        self.assertTrue(pd.isna(df['Esfuerzo (MPa)'].iloc[-1]) or df['Esfuerzo (MPa)'].iloc[-1] == 0)

    def test_compresion_signos(self):
        """Prueba que la compresión devuelva valores negativos."""
        props = {'elastic_modulus': 10000, 'yield_strength': 100, 'category': 'Polimero'}
        df = simular_ensayo(props, 'Compresion', max_strain_machine=0.10)
        
        # Tomar un punto intermedio
        mid_stress = df['Esfuerzo (MPa)'].iloc[50]
        self.assertLess(mid_stress, 0) # Debe ser negativo

    def test_fragilidad_ceramica(self):
        """Prueba que un cerámico rompa casi inmediatamente."""
        props = {
            'elastic_modulus': 300000, 
            'yield_strength': 200, 
            'ultimate_strength': 220,
            'category': 'Ceramico'
        }
        # Simulamos hasta 5%
        df = simular_ensayo(props, 'Tension', max_strain_machine=0.05)
        
        # Debería romper cerca del 0.1% (muy pronto)
        # Verificamos que al 2% (0.02) ya sea None
        idx_2_percent = int(len(df) * (0.02 / 0.05))
        val_at_2 = df['Esfuerzo (MPa)'].iloc[idx_2_percent]
        
        self.assertTrue(pd.isna(val_at_2))

if __name__ == '__main__':
    unittest.main()
