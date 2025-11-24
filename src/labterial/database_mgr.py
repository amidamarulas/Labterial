import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path

# --- CONFIGURACIÓN DE PERSISTENCIA ---

# Ruta del directorio de usuario para guardar la DB (ej: C:\Users\Usuario\.labterial o /home/usuario/.labterial)
# Esto garantiza que los datos persistan incluso si se actualiza la librería.
USER_DATA_DIR = Path.home() / ".labterial"
DB_PATH = USER_DATA_DIR / 'materials.db'

# Ruta del archivo CSV interno (empaquetado) para restaurar datos por defecto
INTERNAL_CSV_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'materials_seed.csv')

def init_db():
    """
    Inicializa la infraestructura de la base de datos SQLite.

    Esta función es idempotente (se puede llamar muchas veces sin causar errores).
    Realiza el siguiente flujo de trabajo:
    
    1.  **Verificación de Directorio:** Comprueba si existe la carpeta oculta ``.labterial`` en el directorio *home* del usuario. Si no, la crea.
    2.  **Conexión/Creación:** Conecta con el archivo SQLite. Si no existe, SQLite lo crea automáticamente.
    3.  **Definición de Esquema (DDL):** Ejecuta la sentencia ``CREATE TABLE IF NOT EXISTS`` para asegurar que la tabla ``materials`` tenga la estructura correcta.
    4.  **Semilla de Datos (Seeding):** Si la base de datos está vacía (conteo = 0), busca el archivo ``materials_seed.csv`` dentro de los recursos del paquete e inserta los materiales por defecto.

    Raises:
        sqlite3.Error: Si hay problemas de permisos de escritura en el disco.
    """
    if not USER_DATA_DIR.exists():
        try:
            USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Error crítico: No se pudo crear directorio de datos: {e}")
            return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    # ESQUEMA MAESTRO (Versión simplificada mecánica)
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
    
    # Carga Inicial Automática
    c.execute('SELECT count(*) FROM materials')
    count = c.fetchone()[0]
    
    if count == 0:
        try:
            if os.path.exists(INTERNAL_CSV_PATH):
                df_seed = pd.read_csv(INTERNAL_CSV_PATH)
                # Insertar solo columnas mecánicas soportadas por el esquema actual
                # Usamos inserción fila por fila para mayor seguridad contra errores individuales
                inserted_count = 0
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
                        inserted_count += 1
                    except sqlite3.IntegrityError: 
                        pass # Ignorar duplicados silenciosamente en la carga inicial
                print(f"✅ Base de datos inicializada con {inserted_count} materiales por defecto.")
            else:
                print(f"⚠️ Advertencia: No se encontró el archivo semilla en {INTERNAL_CSV_PATH}")
        except Exception as e:
            print(f"Error no fatal poblando base de datos: {e}")
        
    conn.commit()
    conn.close()

def get_all_materials():
    """
    Recupera el inventario completo de la base de datos.

    Llama internamente a :func:`init_db` para asegurar que la base de datos exista antes de leer.

    Returns:
        pd.DataFrame: Un DataFrame de Pandas que contiene todas las columnas de la tabla ``materials``.
        Ideal para ser renderizado directamente por ``st.dataframe``.
    """
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query("SELECT * FROM materials", conn)
    except pd.io.sql.DatabaseError:
        # Si la tabla está corrupta o no existe, devolvemos DF vacío
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def insert_from_dataframe(df):
    """
    Importación masiva segura desde un DataFrame externo (ej. CSV subido por usuario).

    Realiza validaciones de estructura antes de intentar la inserción SQL para evitar
    errores de base de datos parciales.

    Args:
        df (pd.DataFrame): DataFrame de entrada. Debe contener al menos las columnas obligatorias:
            ``name``, ``category``, ``elastic_modulus``, ``yield_strength``.

    Returns:
        tuple: Una tupla con tres valores ``(added, ignored, error_msg)``:
        
        *   **added (int):** Cantidad de materiales insertados exitosamente.
        *   **ignored (int):** Cantidad de materiales ignorados porque el nombre ya existía (Constraint UNIQUE).
        *   **error_msg (str|None):** Mensaje de error si faltan columnas o hay problemas de datos. ``None`` si el proceso corrió bien.
    """
    init_db()
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    added = 0
    ignored = 0
    
    # Validación de columnas mínimas
    req = ['name', 'category', 'elastic_modulus', 'yield_strength']
    for r in req:
        if r not in df.columns: 
            conn.close()
            return 0, 0, f"Falta columna requerida en el archivo: '{r}'"
        
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
        except sqlite3.IntegrityError: 
            # El material ya existe (nombre duplicado)
            ignored += 1
        except Exception as e:
            conn.close()
            return added, ignored, str(e)
            
    conn.commit()
    conn.close()
    return added, ignored, None
