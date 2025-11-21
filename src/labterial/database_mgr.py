import sqlite3
import pandas as pd
import os
from pathlib import Path

# Definir ruta segura para la base de datos (compatible con pip install)
USER_DATA_DIR = Path.home() / ".labterial"
DB_PATH = USER_DATA_DIR / 'materials.db'

def init_db():
    """
    Inicializa la conexión y puebla la base de datos con una lista maestra de materiales.
    """
    # Crear carpeta si no existe
    if not USER_DATA_DIR.exists():
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # Esquema Completo
    c.execute('''
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
    
    # --- SEMILLA MAESTRA DE DATOS ---
    c.execute('SELECT count(*) FROM materials')
    if c.fetchone()[0] == 0:
        # Lista consolidada de materiales estandar, exoticos, polimeros y biomateriales
        # Formato: (Nombre, Cat, E, Sy, Su, Poisson, Densidad, Costo, Tmax)
        master_data = [
            # METALES ESTANDAR
            ('Acero A36 Estructural', 'Metal', 200000, 250, 400, 0.26, 7.85, 0.8, 500),
            ('Aluminio 6061-T6', 'Metal', 68900, 276, 310, 0.33, 2.70, 2.5, 150),
            ('Acero Inoxidable 304', 'Metal', 193000, 215, 505, 0.29, 8.00, 4.0, 800),
            ('Cobre Recocido', 'Metal', 110000, 69, 220, 0.34, 8.96, 9.0, 200),
            ('Latón Amarillo', 'Metal', 105000, 150, 350, 0.34, 8.50, 7.0, 200),
            ('Titanio Ti-6Al-4V', 'Metal', 113800, 880, 950, 0.34, 4.43, 40.0, 400),
            
            # METALES EXÓTICOS Y ALTA RESISTENCIA
            ('Acero Maraging 300', 'Metal', 190000, 2000, 2100, 0.30, 8.00, 50.0, 400),
            ('Inconel 718', 'Metal', 200000, 1034, 1240, 0.29, 8.19, 80.0, 700),
            ('Tungsteno', 'Metal', 411000, 750, 980, 0.28, 19.25, 100.0, 1500),
            ('Plomo Puro', 'Metal', 16000, 14, 20, 0.44, 11.34, 2.5, 100),
            ('Oro Puro', 'Metal', 79000, 30, 100, 0.42, 19.30, 60000.0, 1064),
            ('Metal Amorfo (Bulk Glass)', 'Metal', 100000, 1500, 1800, 0.36, 6.00, 200.0, 400),
            
            # POLÍMEROS Y PLÁSTICOS
            ('Nylon 6/6', 'Polimero', 2800, 80, 85, 0.40, 1.15, 3.0, 90),
            ('Policarbonato', 'Polimero', 2400, 60, 70, 0.37, 1.20, 5.0, 120),
            ('PLA (Impresion 3D)', 'Polimero', 3500, 50, 60, 0.36, 1.24, 20.0, 55),
            ('PETG (Impresion 3D)', 'Polimero', 2100, 50, 55, 0.40, 1.27, 25.0, 75),
            ('TPU 95A (Flexible)', 'Polimero', 25, 10, 35, 0.48, 1.20, 35.0, 80),
            ('PTFE (Teflon)', 'Polimero', 500, 15, 25, 0.46, 2.20, 15.0, 260),
            ('Goma de Caucho', 'Polimero', 50, 20, 25, 0.49, 0.92, 2.0, 80),
            ('PEEK (Aeroespacial)', 'Polimero', 3600, 100, 110, 0.38, 1.32, 150.0, 250),

            # CERÁMICOS Y VIDRIOS
            ('Concreto Estandar', 'Ceramico', 30000, 3, 4, 0.20, 2.40, 0.05, 400),
            ('Alumina (Al2O3)', 'Ceramico', 370000, 250, 300, 0.22, 3.95, 20.0, 1500),
            ('Vidrio de Ventana', 'Ceramico', 70000, 30, 50, 0.22, 2.50, 1.0, 500),
            ('Diamante Sintetico', 'Ceramico', 1220000, 5000, 6000, 0.20, 3.52, 5000.0, 800),
            ('Carburo de Silicio', 'Ceramico', 410000, 400, 450, 0.14, 3.10, 50.0, 1600),
            ('Hielo (-10C)', 'Ceramico', 9000, 5, 6, 0.33, 0.92, 0.0, 0),

            # COMPUESTOS Y NATURALES
            ('Fibra de Carbono (Epoxy)', 'Compuesto', 230000, 800, 1500, 0.20, 1.60, 100.0, 120),
            ('Fibra de Vidrio (G10)', 'Compuesto', 24000, 240, 300, 0.15, 1.80, 30.0, 130),
            ('Madera de Roble', 'Compuesto', 11000, 40, 90, 0.30, 0.75, 3.0, 100),
            ('Madera de Balsa', 'Compuesto', 3500, 20, 30, 0.35, 0.15, 20.0, 100),
            ('Corcho Natural', 'Compuesto', 30, 1, 2, 0.00, 0.24, 15.0, 120),
            
            # BIOMATERIALES Y CURIOSIDADES
            ('Hueso Cortical', 'Biomaterial', 17000, 110, 130, 0.30, 1.90, 0.0, 60),
            ('Seda de Araña', 'Biomaterial', 10000, 1100, 1200, 0.28, 1.30, 1000.0, 100),
            ('Cabello Humano', 'Biomaterial', 3000, 150, 200, 0.38, 1.30, 0.0, 100),
            ('Espagueti Seco', 'Alimento', 3000, 10, 15, 0.30, 1.50, 1.5, 100)
        ]
        
        try:
            c.executemany('''
                INSERT INTO materials 
                (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio, density, cost, max_temp) 
                VALUES (?,?,?,?,?,?,?,?,?)
            ''', master_data)
            print(f"Base de datos inicializada con {len(master_data)} materiales.")
        except Exception as e:
            print(f"Error poblando base de datos: {e}")
        
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
        if r not in df.columns: return 0, 0, f"Falta columna requerida: {r}"
        
    for _, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO materials 
                (name, category, elastic_modulus, yield_strength, ultimate_strength, poisson_ratio, density, cost, max_temp) 
                VALUES (?,?,?,?,?,?,?,?,?)
            ''', (
                row['name'], row['category'], row['elastic_modulus'], row['yield_strength'], 
                row.get('ultimate_strength'), row.get('poisson_ratio'),
                row.get('density'), row.get('cost'), row.get('max_temp')
            ))
            added += 1
        except sqlite3.IntegrityError: ignored += 1
        except Exception as e: return added, ignored, str(e)
            
    conn.commit(); conn.close()
    return added, ignored, None
