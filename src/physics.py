import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=300):
    """
    max_strain_machine: Es el tope del slider (hasta dónde llega la máquina).
    La rotura del material es INTRÍNSECA y no depende de este valor.
    """
    # --- 1. EXTRAER PROPIEDADES ---
    E = material_props['elastic_modulus']
    Sy = material_props['yield_strength']
    Su = material_props.get('ultimate_strength')
    Nu = material_props.get('poisson_ratio', 0.3)
    Cat = material_props.get('category', 'Metal') 
    
    if Su is None or Su < Sy: Su = Sy * 1.1

    # --- 2. DEFINIR EL PUNTO DE ROTURA REAL (INTRÍNSECO) ---
    intrinsic_rupture_strain = 0.01 
    
    if Cat == 'Ceramico' or Cat == 'Vidrio':
        intrinsic_rupture_strain = (Su / E) * 1.1 
    elif Cat == 'Polimero':
        intrinsic_rupture_strain = 0.60 
    elif Cat == 'Compuesto':
        intrinsic_rupture_strain = 0.025
    else:
        # Metales (Default)
        intrinsic_rupture_strain = 0.18

    # --- 3. AJUSTE SEGÚN TIPO DE ENSAYO ---
    is_torsion = (tipo_ensayo == 'Torsion')
    is_compression = (tipo_ensayo == 'Compresion')
    
    if is_torsion:
        Modulus = E / (2 * (1 + Nu))
        Yield_Point = Sy * 0.577
        Ultimate_Point = Su * 0.6
        intrinsic_rupture_strain *= 1.5 
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (rad)"
    else:
        Modulus = E
        Yield_Point = Sy
        Ultimate_Point = Su
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)"

    # --- 4. PUNTOS CLAVE DE LA CURVA ---
    p_strain = [0.0]
    p_stress = [0.0]
    
    ey = Yield_Point / Modulus
    p_strain.append(ey)
    p_stress.append(Yield_Point)
    
    is_brittle = intrinsic_rupture_strain < 0.05
    fracture_strain = intrinsic_rupture_strain
    
    if is_brittle:
        p_strain.append(fracture_strain)
        p_stress.append(Ultimate_Point)
    else:
        strain_at_Su = ey + (fracture_strain - ey) * 0.7
        p_strain.append(strain_at_Su)
        p_stress.append(Ultimate_Point)
        
        if is_compression:
            fracture_strain = max_strain_machine * 2 
            p_strain.append(max_strain_machine * 1.5)
            p_stress.append(Ultimate_Point * 1.5)
        else:
            p_strain.append(fracture_strain)
            p_stress.append(Ultimate_Point * 0.85)

    # --- 5. GENERAR LA CURVA ---
    dense_strain = np.linspace(0, max_strain_machine, puntos)
    dense_stress = []
    
    try:
        f_interp = interp1d(p_strain, p_stress, kind='linear', fill_value="extrapolate")
    except:
        f_interp = lambda x: Modulus * x

    for e in dense_strain:
        val = 0.0
        if e > fracture_strain and not is_compression:
            val = None
        elif e <= ey:
            val = Modulus * e
        else:
            if not is_brittle and e <= p_strain[2]:
                ratio = (e - ey) / (p_strain[2] - ey)
                if ratio < 0: ratio = 0
                val = Yield_Point + (Ultimate_Point - Yield_Point) * (ratio ** 0.4)
            else:
                val = float(f_interp(e))

        if is_compression and val is not None:
            val *= -1
            
        dense_stress.append(val)

    if is_compression:
        dense_strain = np.abs(dense_strain)

    df = pd.DataFrame({
        col_strain: dense_strain,
        col_stress: dense_stress
    })
    
    if not is_torsion:
        df["Deformacion (%)"] = df[col_strain] * 100
    else:
        df["Deformacion (%)"] = df[col_strain]

    return df
