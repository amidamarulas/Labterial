import unittest
import pandas as pd
import sqlite3
import sys
import os
from unittest.mock import patch, MagicMock

# Importar módulo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Importación robusta (Paquete o Módulo)
try:
    from labterial import database_mgr
except ImportError:
    try:
        import database_mgr
    except:
        from src.labterial import database_mgr

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        """
        Configuración previa a CADA test.
        Creamos una BD en memoria real, pero modificamos su comportamiento.
        """
        # 1. Crear conexión real en RAM
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # 2. Crear tabla idéntica a la real
        self.cursor.execute('''
            CREATE TABLE materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                elastic_modulus REAL NOT NULL,
                yield_strength REAL NOT NULL,
                ultimate_strength REAL,
                poisson_ratio REAL
            )
        ''')
        self.conn.commit()

        # --- EL TRUCO MAESTRO ---
        # Guardamos la función 'close' original para usarla al final
        self.real_close = self.conn.close
        
        # Reemplazamos 'close' por una función lambda que NO HACE NADA.
        # Así, cuando init_db() llame a conn.close(), la conexión sigue viva.
        self.conn.close = lambda: None

    def tearDown(self):
        """Limpieza después de CADA test."""
        # Restauramos la función original para poder cerrar de verdad
        self.conn.close = self.real_close
        self.conn.close()

    @patch('sqlite3.connect')
    def test_insert_valid_material(self, mock_connect):
        # El mock siempre devuelve nuestra conexión "inmortal"
        mock_connect.return_value = self.conn
        
        data = {
            'name': ['Vibranium'],
            'category': ['Metal'],
            'elastic_modulus': [500000],
            'yield_strength': [1000]
        }
        df = pd.DataFrame(data)
        
        added, ignored, error = database_mgr.insert_from_dataframe(df)
        
        self.assertEqual(added, 1)
        self.assertEqual(ignored, 0)
        self.assertIsNone(error)
        
        # Verificar que realmente se guardó
        curr = self.conn.cursor()
        curr.execute("SELECT name FROM materials WHERE name='Vibranium'")
        result = curr.fetchone()
        self.assertEqual(result[0], 'Vibranium')

    @patch('sqlite3.connect')
    def test_insert_duplicate(self, mock_connect):
        mock_connect.return_value = self.conn
        
        # Insertar primero manualmente
        self.cursor.execute("INSERT INTO materials (name, category, elastic_modulus, yield_strength) VALUES ('Adamantium', 'Metal', 1, 1)")
        self.conn.commit()
        
        # Intentar insertar lo mismo vía función
        df = pd.DataFrame({'name': ['Adamantium'], 'category': ['Metal'], 'elastic_modulus': [1], 'yield_strength': [1]})
        
        added, ignored, error = database_mgr.insert_from_dataframe(df)
        
        self.assertEqual(added, 0)
        self.assertEqual(ignored, 1)
        self.assertIsNone(error)

    @patch('sqlite3.connect')
    def test_missing_columns(self, mock_connect):
        mock_connect.return_value = self.conn
        
        df = pd.DataFrame({'name': ['MalaData'], 'elastic_modulus': [100]})
        
        added, ignored, error = database_mgr.insert_from_dataframe(df)
        
        self.assertIn("Falta columna", error)
        self.assertEqual(added, 0)

if __name__ == '__main__':
    unittest.main()
