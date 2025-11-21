import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=300):
    
    E = float(material_props['elastic_modulus'])
    Sy = float(material_props['yield_strength'])
    Su = material_props.get('ultimate_strength')
    Nu = material_props.get('poisson_ratio', 0.3)
    Cat = material_props.get('category', 'Metal')
    
    if Su is None or Su <= Sy: Su = Sy * 1.05

    # --- DUCTILIDAD ---
    rupture_strain = 0.01
    
    if Cat == 'Metal':
        ratio = (Su / Sy) - 1
        rupture_strain = min(0.60, max(0.01, 0.02 + (ratio * 0.5)))
    elif Cat == 'Polimero':
        if E < 1000: rupture_strain = 1.5
        elif E < 3000: rupture_strain = 0.50
        else: rupture_strain = 0.05
    elif Cat in ['Ceramico', 'Vidrio']:
        rupture_strain = (Sy / E) + 0.0005
    elif Cat == 'Compuesto':
        rupture_strain = (Su / E) * 1.2

    # --- AJUSTE POR TIPO DE ENSAYO ---
    is_torsion = (tipo_ensayo == 'Torsion')
    is_compression = (tipo_ensayo == 'Compresion')
    is_flexion = (tipo_ensayo == 'Flexion')
    
    if is_torsion:
        Modulus = E / (2 * (1 + Nu))
        Yield_Point = Sy * 0.577
        Ultimate_Point = Su * 0.6
        rupture_strain *= 1.4 
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (rad)"
    elif is_flexion:
        # En flexión, el material suele resistir más que en tracción pura (Módulo de Ruptura)
        # especialmente en frágiles, porque el volumen sometido a tensión máxima es pequeño.
        factor_mor = 1.2 # Modulus of Rupture factor
        Modulus = E # La rigidez es la misma (E)
        Yield_Point = Sy * 1.1 
        Ultimate_Point = Su * factor_mor
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)" # Strain en la fibra externa
    else:
        # Tension / Compresion
        Modulus = E
        Yield_Point = Sy
        Ultimate_Point = Su
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)"

    # --- KEYPOINTS ---
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
            # En flexión la caída es más suave antes de la rotura final
            drop_factor = 0.95 if is_flexion else 0.85
            p_stress.append(Ultimate_Point * drop_factor)

    # --- INTERPOLACIÓN ---
    dense_strain = np.linspace(0, max_strain_machine, puntos)
    dense_stress = []
    
    try: f_interp = interp1d(p_strain, p_stress, kind='linear', fill_value="extrapolate")
    except: f_interp = lambda x: Modulus * x

    for e in dense_strain:
        val = 0.0
        if e > fracture_point and not is_compression:
            val = None
        elif e <= ey:
            val = Modulus * e
        else:
            if not is_brittle and not is_compression and e <= strain_at_peak:
                t = (e - ey) / (strain_at_peak - ey)
                if t < 0: t = 0
                val = Yield_Point + (Ultimate_Point - Yield_Point) * (t ** 0.5)
            else:
                val = float(f_interp(e))

        if is_compression and val is not None: val *= -1
        dense_stress.append(val)

    if is_compression: dense_strain = np.abs(dense_strain)

    df = pd.DataFrame({col_strain: dense_strain, col_stress: dense_stress})
    
    if not is_torsion: df["Deformacion (%)"] = df[col_strain] * 100
    else: df["Deformacion (%)"] = df[col_strain]

    return df
