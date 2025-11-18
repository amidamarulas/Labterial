import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'materials.db')

def init_db():
    """Inicializa la DB si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            elastic_modulus REAL NOT NULL,
            yield_strength REAL NOT NULL,
            ultimate_strength REAL,
            poisson_ratio REAL
        )
    ''')
    
    # Datos semilla
    c.execute('SELECT count(*) FROM materials')
    if c.fetchone()[0] == 0:
        datos_ejemplo = [
            ('Acero Estructural A36', 'Metal', 200000, 250, 400, 0.26),
            ('Aluminio 6061-T6', 'Metal', 68900, 276, 310, 0.33),
            ('Nylon 6/6', 'Polimero', 2000, 80, 85, 0.40),
            ('Fibra de Carbono (Epoxy)', 'Compuesto', 230000, 800, 1500, 0.20)
        ]
        c.executemany('''
            INSERT INTO materials (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', datos_ejemplo)
        print("Base de datos inicializada.")
    
    conn.commit()
    conn.close()

def get_all_materials():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM materials", conn)
    conn.close()
    return df

def insert_from_dataframe(df):
    """
    Inserta materiales desde un DataFrame.
    Retorna: (agregados, duplicados_ignorados, error_msg)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added = 0
    ignored = 0
    
    # Validar columnas obligatorias
    required_cols = ['name', 'category', 'elastic_modulus', 'yield_strength']
    for col in required_cols:
        if col not in df.columns:
            conn.close()
            return 0, 0, f"El archivo CSV debe tener la columna: '{col}'"

    # Rellenar opcionales si no existen
    if 'ultimate_strength' not in df.columns: df['ultimate_strength'] = None
    if 'poisson_ratio' not in df.columns: df['poisson_ratio'] = None

    # Iterar e insertar
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO materials (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['name'], row['category'], row['elastic_modulus'], row['yield_strength'], row['ultimate_strength'], row['poisson_ratio']))
            added += 1
        except sqlite3.IntegrityError:
            # El nombre ya existe (UNIQUE constraint)
            ignored += 1
        except Exception as e:
            conn.close()
            return added, ignored, str(e)
            
    conn.commit()
    conn.close()
    return added, ignored, None
