import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path

# Ruta segura usuario
USER_DATA_DIR = Path.home() / ".labterial"
DB_PATH = USER_DATA_DIR / 'materials.db'

# Ruta CSV interno
INTERNAL_CSV_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'materials_seed.csv')

def init_db():
    """
    Inicializa la DB con esquema MECÁNICO (sin costo/densidad).
    Carga datos semilla si está vacía.
    """
    if not USER_DATA_DIR.exists():
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # ESQUEMA SIMPLIFICADO (Solo props de simulación)
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
    
    # Carga Inicial
    c.execute('SELECT count(*) FROM materials')
    count = c.fetchone()[0]
    
    if count == 0:
        try:
            if os.path.exists(INTERNAL_CSV_PATH):
                df_seed = pd.read_csv(INTERNAL_CSV_PATH)
                # Insertar solo columnas mecánicas
                for _, row in df_seed.iterrows():
                    try:
                        c.execute('''
                            INSERT INTO materials 
                            (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio) 
                            VALUES (?,?,?,?,?,?)
                        ''', (
                            row['name'], row['category'], row['elastic_modulus'], row['yield_strength'], 
                            row.get('ultimate_strength'), row.get('poisson_ratio')
                        ))
                    except sqlite3.IntegrityError: pass
                print(f"✅ Base de datos poblada con {len(df_seed)} materiales base.")
            else:
                print(f"⚠️ No se encontró semilla: {INTERNAL_CSV_PATH}")
        except Exception as e:
            print(f"Error inicializando DB: {e}")
        
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
            cursor.execute('''
                INSERT INTO materials 
                (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio) 
                VALUES (?,?,?,?,?,?)
            ''', (
                row['name'], row['category'], row['elastic_modulus'], row['yield_strength'], 
                row.get('ultimate_strength'), row.get('poisson_ratio')
            ))
            added += 1
        except sqlite3.IntegrityError: ignored += 1
        except Exception as e: return added, ignored, str(e)
            
    conn.commit(); conn.close()
    return added, ignored, None
