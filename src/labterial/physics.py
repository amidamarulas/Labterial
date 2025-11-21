import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=300):
    """
    Simula el comportamiento mecánico de un material bajo diferentes tipos de carga.

    Esta función actúa como el "motor físico" del software. Utiliza un modelo fenomenológico
    basado en propiedades mecánicas estándar ($E, S_y, S_u$) para generar curvas de
    Esfuerzo-Deformación realistas.

    Incluye lógica avanzada para:
    
    *   **Ductilidad Dinámica:** Calcula el punto de ruptura basándose en la relación $S_u/S_y$.
    *   **Torsión:** Aplica criterio de Von Mises ($\tau = \sigma / \sqrt{3}$).
    *   **Flexión:** Aplica un factor de corrección para el Módulo de Ruptura (MOR).
    *   **Compresión:** Simula el abarrilamiento sin fractura en materiales dúctiles.

    Args:
        material_props (dict): Diccionario con las propiedades del material. 
            Debe contener: ``elastic_modulus``, ``yield_strength``, ``ultimate_strength`` (opcional), 
            ``poisson_ratio`` (opcional) y ``category``.
        tipo_ensayo (str): El modo de carga. Opciones:
            ``'Tension'``, ``'Compresion'``, ``'Torsion'``, ``'Flexion'``.
        max_strain_machine (float, optional): El límite máximo de deformación (eje X) configurado 
            en la máquina virtual. Por defecto 0.05.
        puntos (int, optional): Resolución de la simulación (número de filas). Por defecto 300.

    Returns:
        pd.DataFrame: DataFrame con los resultados de la simulación.
        
        Columnas generadas:
        
        *   ``Esfuerzo (MPa)``: Eje Y.
        *   ``Deformacion (mm/mm)`` o ``(rad)``: Eje X base.
        *   ``Deformacion (%)``: Columna auxiliar para visualización.
    """
    
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
