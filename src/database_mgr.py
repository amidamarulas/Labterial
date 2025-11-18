import sqlite3
import pandas as pd
import os

# Ruta absoluta para asegurar que encuentre la DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'materials.db')

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            elastic_modulus REAL NOT NULL,
            yield_strength REAL NOT NULL,
            ultimate_strength REAL,
            poisson_ratio REAL
        )
    ''')
    
    # Insertar datos iniciales si la tabla esta vacia
    c.execute('SELECT count(*) FROM materials')
    if c.fetchone()[0] == 0:
        datos_ejemplo = [
            ('Acero Estructural A36', 200000, 250, 400, 0.26),
            ('Aluminio 6061-T6', 68900, 276, 310, 0.33),
            ('Titanio Ti-6Al-4V', 113800, 880, 950, 0.34),
            ('Cobre Recocido', 110000, 69, 220, 0.34)
        ]
        c.executemany('''
            INSERT INTO materials (name, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio)
            VALUES (?, ?, ?, ?, ?)
        ''', datos_ejemplo)
        print("Base de datos inicializada con datos de ejemplo.")
    
    conn.commit()
    conn.close()

def get_all_materials():
    """Retorna un DataFrame con todos los materiales."""
    init_db() # Asegurar que existe
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM materials", conn)
    conn.close()
    return df


# Seccion para añadir materiales

def add_material(name, e_modulus, y_strength, u_strength, poisson):
    """Inserta un solo material. Retorna True si tuvo éxito."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO materials (name, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, e_modulus, y_strength, u_strength, poisson))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def import_materials_from_df(df):
    """
    Recibe un DataFrame y guarda los materiales en la BD.
    Retorna: (cantidad_importada, cantidad_duplicada, mensaje_error)
    """
    # 1. Validar columnas obligatorias
    required = ['name', 'elastic_modulus', 'yield_strength']
    if not all(col in df.columns for col in required):
        return 0, 0, f"Faltan columnas obligatorias. Se requiere: {', '.join(required)}"

    # 2. Rellenar columnas opcionales si no vienen
    if 'ultimate_strength' not in df.columns:
        df['ultimate_strength'] = None
    if 'poisson_ratio' not in df.columns:
        df['poisson_ratio'] = None # SQLite aceptará NULL

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    imported = 0
    duplicates = 0
    
    for _, row in df.iterrows():
        try:
            c.execute('''
                INSERT INTO materials (name, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                str(row['name']), 
                float(row['elastic_modulus']), 
                float(row['yield_strength']), 
                # Manejo seguro de nulos para float
                float(row['ultimate_strength']) if pd.notnull(row['ultimate_strength']) else None,
                float(row['poisson_ratio']) if pd.notnull(row['poisson_ratio']) else None
            ))
            imported += 1
        except sqlite3.IntegrityError:
            duplicates += 1
        except ValueError:
            continue # Saltar filas con datos corruptos (textos en vez de numeros)

    conn.commit()
    conn.close()
    
    return imported, duplicates, None