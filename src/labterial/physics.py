import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=300):
    """
    Motor físico v3.0:
    Implementación estricta del modelo de comportamiento de polímeros con:
    1. Elasticidad Lineal.
    2. Caída post-fluencia (Softening).
    3. Meseta de estiramiento en frío (Cold Drawing Plateau).
    4. Endurecimiento final (Strain Hardening).
    """
    
    # --- 1. EXTRACCIÓN DE PROPIEDADES ---
    E = float(material_props['elastic_modulus'])
    Sy = float(material_props['yield_strength'])
    Su = material_props.get('ultimate_strength')
    Nu = material_props.get('poisson_ratio', 0.3)
    Cat = material_props.get('category', 'Metal')
    
    if Su is None or Su <= Sy: Su = Sy * 1.1

    # --- 2. CÁLCULO DE DUCTILIDAD (Punto de Ruptura) ---
    rupture_strain = 0.01
    
    if Cat == 'Metal':
        ratio = (Su / Sy) - 1
        rupture_strain = min(0.60, max(0.01, 0.02 + (ratio * 0.5)))
    elif Cat == 'Polimero':
        # Ajuste para asegurar que Nylon y similares tengan gran elongación
        if E < 1000: rupture_strain = 2.0 # Gomas
        elif E < 5000: rupture_strain = 0.80 # Nylon, PE, PP (80%)
        else: rupture_strain = 0.10 # Rígidos
    elif Cat in ['Ceramico', 'Vidrio']:
        rupture_strain = (Sy / E) + 0.0005
    elif Cat == 'Compuesto':
        rupture_strain = (Su / E) * 1.2

    # --- 3. AJUSTE POR TIPO DE ENSAYO ---
    is_torsion = (tipo_ensayo == 'Torsion')
    is_compression = (tipo_ensayo == 'Compresion')
    is_flexion = (tipo_ensayo == 'Flexion')
    # Detectamos explícitamente el caso que queremos corregir
    is_polymer_tension = (Cat == 'Polimero' and tipo_ensayo == 'Tension')
    
    if is_torsion:
        Modulus = E / (2 * (1 + Nu))
        Yield_Point = Sy * 0.577
        Ultimate_Point = Su * 0.6
        rupture_strain *= 1.4 
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (rad)"
    elif is_flexion:
        factor_mor = 1.2 
        Modulus = E 
        Yield_Point = Sy * 1.1 
        Ultimate_Point = Su * factor_mor
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)" 
    else:
        Modulus = E
        Yield_Point = Sy
        Ultimate_Point = Su
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)"

    # Vector de deformación base
    dense_strain = np.linspace(0, max_strain_machine, puntos)
    dense_stress = []

    # ==============================================================================
    # LÓGICA ESPECÍFICA PARA POLÍMEROS (Basada en curva_tension_polimero)
    # ==============================================================================
    if is_polymer_tension:
        # 1. Definir parámetros clave del modelo de 4 fases
        ey = Yield_Point / Modulus  # Punto donde termina la linealidad pura
        
        # El esfuerzo de "plateau" suele ser menor al Yield (ej. 80% de Sy)
        S_draw = Yield_Point * 0.8 
        
        # Definimos dónde termina la caída y empieza la meseta
        e_drop_end = ey * 2.0 
        
        # Definimos dónde termina la meseta y empieza a endurecer
        e_draw_end = rupture_strain * 0.75 

        for e in dense_strain:
            val = 0.0
            
            # A. ROTURA
            if e > rupture_strain:
                val = None 
            
            # B. ZONA ELÁSTICA (Fase 1)
            elif e <= ey:
                val = Modulus * e
            
            # C. ZONA DE CAÍDA / SOFTENING (Fase 2)
            # Simulamos la bajada desde Sy hasta S_draw
            elif e <= e_drop_end:
                # Fórmula basada en el ejemplo: Sy - (Sy - S_draw) * factor
                # El factor va de 0 a 1 basado en la posición relativa
                rel_pos = (e - ey) / (e_drop_end - ey)
                # Usamos raiz cuadrada para que caiga rápido al principio
                val = Yield_Point - (Yield_Point - S_draw) * (rel_pos ** 0.5)
            
            # D. MESETA / PLATEAU (Fase 3)
            # Mantener constante S_draw hasta que empiece el endurecimiento
            elif e <= e_draw_end:
                val = S_draw
            
            # E. ENDURECIMIENTO / HARDENING (Fase 4)
            # Subida lineal desde S_draw hasta Su
            else:
                # Normalizar posición en la zona de endurecimiento (0 a 1)
                rel_pos = (e - e_draw_end) / (rupture_strain - e_draw_end)
                val = S_draw + (Ultimate_Point - S_draw) * rel_pos
            
            # Corrección de seguridad (nunca bajar de 0 ni subir de Su + margen)
            if val is not None:
                val = max(0, val)
                
            dense_stress.append(val)

    # ==============================================================================
    # LÓGICA ESTÁNDAR (Metales, Compresión, etc.)
    # ==============================================================================
    else:
        # Puntos Clave para interpolación
        p_strain = [0.0]
        p_stress = [0.0]
        
        ey = Yield_Point / Modulus
        p_strain.append(ey)
        p_stress.append(Yield_Point)
        
        is_brittle = rupture_strain < 0.02
        
        if is_brittle:
            p_strain.append(rupture_strain)
            p_stress.append(Ultimate_Point)
            fracture_point = rupture_strain
        else:
            strain_at_peak = ey + (rupture_strain - ey) * 0.75
            
            if is_compression:
                fracture_point = max_strain_machine * 2
                p_strain.append(max_strain_machine)
                p_stress.append(Ultimate_Point * 1.2)
            else:
                fracture_point = rupture_strain
                p_strain.append(strain_at_peak)
                p_stress.append(Ultimate_Point)
                p_strain.append(fracture_point)
                drop_factor = 0.95 if is_flexion else 0.85
                p_stress.append(Ultimate_Point * drop_factor)

        try: f_interp = interp1d(p_strain, p_stress, kind='linear', fill_value="extrapolate")
        except: f_interp = lambda x: Modulus * x

        for e in dense_strain:
            val = 0.0
            if e > fracture_point and not is_compression:
                val = None
            elif e <= ey:
                val = Modulus * e
            else:
                # Zona Plástica Metales (Curva suave)
                if not is_brittle and not is_compression and e <= strain_at_peak:
                    t = (e - ey) / (strain_at_peak - ey)
                    if t < 0: t = 0
                    val = Yield_Point + (Ultimate_Point - Yield_Point) * (t ** 0.5)
                else:
                    val = float(f_interp(e))

            if is_compression and val is not None: val *= -1
            dense_stress.append(val)

    # --- DATAFRAME FINAL ---
    if is_compression: dense_strain = np.abs(dense_strain)

    df = pd.DataFrame({col_strain: dense_strain, col_stress: dense_stress})
    
    if not is_torsion: df["Deformacion (%)"] = df[col_strain] * 100
    else: df["Deformacion (%)"] = df[col_strain]

    return df
