import sqlite3
import pandas as pd
import os
from pathlib import Path

# Definir ruta segura en el directorio del usuario
USER_DATA_DIR = Path.home() / ".labterial"
DB_PATH = USER_DATA_DIR / 'materials.db'

def init_db():
    """
    Inicializa la DB en la carpeta del usuario (~/.labterial/).
    """
    # Crear carpeta si no existe
    if not USER_DATA_DIR.exists():
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
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
    
    # Semilla inicial
    c.execute('SELECT count(*) FROM materials')
    if c.fetchone()[0] == 0:
        # Datos por defecto
        try:
            data = [
                ('Acero A36', 'Metal', 200000, 250, 400, 0.26),
                ('Aluminio 6061', 'Metal', 68900, 276, 310, 0.33)
            ]
            c.executemany('INSERT INTO materials (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio) VALUES (?,?,?,?,?,?)', data)
        except: pass
        
    conn.commit()
    conn.close()

def get_all_materials():
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query("SELECT * FROM materials", conn)
    conn.close()
    return df

def insert_from_dataframe(df):
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    added = 0; ignored = 0
    
    req = ['name', 'category', 'elastic_modulus', 'yield_strength']
    for r in req:
        if r not in df.columns: return 0, 0, f"Falta columna: {r}"
        
    for _, row in df.iterrows():
        try:
            cursor.execute('INSERT INTO materials (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio) VALUES (?,?,?,?,?,?)', 
            (row['name'], row['category'], row['elastic_modulus'], row['yield_strength'], row.get('ultimate_strength'), row.get('poisson_ratio')))
            added += 1
        except sqlite3.IntegrityError: ignored += 1
        except Exception as e: return added, ignored, str(e)
            
    conn.commit(); conn.close()
    return added, ignored, None

def get_db_path():
    return str(DB_PATH)
