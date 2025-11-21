import unittest
import pandas as pd
import sqlite3
import sys
import os
from unittest.mock import patch

# Configuración de Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from labterial import database_mgr
except ImportError:
    from src.labterial import database_mgr

# --- CLASE HELPER PARA PYTHON 3.12 ---
class UnclosableConnection:
    """
    Envuelve una conexión SQLite real pero ignora la orden .close().
    Necesario porque en Python 3.12+ el método close es read-only.
    """
    def __init__(self, conn):
        self.conn = conn
    
    def __getattr__(self, name):
        # Delega cualquier llamada (cursor, commit, etc) a la conexión real
        return getattr(self.conn, name)
    
    def close(self):
        # ¡No hacemos nada! La conexión sigue viva.
        pass

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        # 1. Crear conexión real en memoria
        self.real_conn = sqlite3.connect(':memory:')
        self.cursor = self.real_conn.cursor()
        
        # 2. Crear esquema
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                elastic_modulus REAL NOT NULL,
                yield_strength REAL NOT NULL,
                ultimate_strength REAL,
                poisson_ratio REAL,
                density REAL,
                cost REAL,
                max_temp REAL
            )
        ''')
        self.real_conn.commit()
        
        # 3. Crear el objeto "inmortal" que usará el código
        self.safe_conn = UnclosableConnection(self.real_conn)

    def tearDown(self):
        # Cerrar la conexión real manualmente al final del test
        self.real_conn.close()

    @patch('sqlite3.connect')
    def test_insert_valid_material(self, mock_connect):
        # El mock devuelve nuestra conexión protegida
        mock_connect.return_value = self.safe_conn
        
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
        
        # Verificar en la DB real
        curr = self.real_conn.cursor()
        curr.execute("SELECT name FROM materials WHERE name='Vibranium'")
        self.assertEqual(curr.fetchone()[0], 'Vibranium')

    @patch('sqlite3.connect')
    def test_insert_duplicate(self, mock_connect):
        mock_connect.return_value = self.safe_conn
        
        # Insertar primero
        self.cursor.execute("INSERT INTO materials (name, category, elastic_modulus, yield_strength) VALUES ('Adamantium', 'Metal', 1, 1)")
        self.real_conn.commit()
        
        # Intentar duplicar
        df = pd.DataFrame({'name': ['Adamantium'], 'category': ['Metal'], 'elastic_modulus': [1], 'yield_strength': [1]})
        
        added, ignored, error = database_mgr.insert_from_dataframe(df)
        
        self.assertEqual(added, 0)
        self.assertEqual(ignored, 1)

    @patch('sqlite3.connect')
    def test_missing_columns(self, mock_connect):
        mock_connect.return_value = self.safe_conn
        
        df = pd.DataFrame({'name': ['MalaData'], 'elastic_modulus': [100]})
        added, ignored, error = database_mgr.insert_from_dataframe(df)
        
        self.assertIn("Falta columna", str(error))
        self.assertEqual(added, 0)

if __name__ == '__main__':
    unittest.main()
