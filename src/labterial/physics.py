import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=300):
    """
    Simula el ensayo calculando dinámicamente el punto de ruptura (Ductilidad)
    basado en la relación entre Sy (Fluencia) y Su (Último).
    """
    
    # --- 1. EXTRACCIÓN Y VALIDACIÓN DE PROPIEDADES ---
    E = float(material_props['elastic_modulus'])
    Sy = float(material_props['yield_strength'])
    Su = material_props.get('ultimate_strength')
    Nu = material_props.get('poisson_ratio', 0.3)
    Cat = material_props.get('category', 'Metal')
    
    # Si no existe Su, lo estimamos levemente superior a Sy para evitar errores
    if Su is None or Su <= Sy: 
        Su = Sy * 1.05

    # --- 2. CÁLCULO INTELIGENTE DE LA DUCTILIDAD (Punto de Ruptura) ---
    # Esto define en qué % de deformación se rompe el material realmente.
    
    rupture_strain = 0.01 # Valor base
    
    if Cat == 'Metal':
        # Heurística: Cuanto mayor es la diferencia entre Su y Sy, más dúctil suele ser.
        # Ratio de endurecimiento
        hardening_ratio = (Su / Sy) - 1  # Ej: (400/250)-1 = 0.6
        
        # Fórmula empírica ajustada para simulación visual:
        # Un ratio de 0 (Sy=Su) da 2% de elongación post-yield.
        # Un ratio de 1.0 (Su=2*Sy) da ~40% de elongación.
        plastic_strain = 0.02 + (hardening_ratio * 0.5)
        
        # Límites realistas para metales
        rupture_strain = min(0.60, max(0.01, plastic_strain))
        
    elif Cat == 'Polimero':
        # Los polímeros dependen mucho de su rigidez (E).
        # E bajo (Goma) -> Ruptura muy alta (100%+)
        # E alto (Epoxy) -> Ruptura baja (2-5%)
        if E < 1000: # Gomas / Elastomeros
            rupture_strain = 1.5 # 150%
        elif E < 3000: # Plásticos ingeniería (Nylon)
            rupture_strain = 0.50 # 50%
        else: # Termoestables rígidos
            rupture_strain = 0.05 # 5%
            
    elif Cat == 'Ceramico' or Cat == 'Vidrio':
        # Rompen en cuanto termina la zona elástica
        elastic_strain = Sy / E
        rupture_strain = elastic_strain + 0.0005 # Rompe casi inmediato

    elif Cat == 'Compuesto':
        # Suelen ser rígidos y poco dúctiles (Fibra de Carbono ~1.5%)
        rupture_strain = (Su / E) * 1.2

    # --- 3. CONFIGURACIÓN SEGÚN TIPO DE ENSAYO ---
    is_torsion = (tipo_ensayo == 'Torsion')
    is_compression = (tipo_ensayo == 'Compresion')
    
    if is_torsion:
        # Conversión Von Mises / Tresca
        Modulus = E / (2 * (1 + Nu))
        Yield_Point = Sy * 0.577
        Ultimate_Point = Su * 0.6
        # En torsión los materiales aguantan más deformación antes de romper
        rupture_strain *= 1.4 
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (rad)"
    else:
        Modulus = E
        Yield_Point = Sy
        Ultimate_Point = Su
        col_stress = "Esfuerzo (MPa)"
        col_strain = "Deformacion (mm/mm)"

    # --- 4. CONSTRUCCIÓN DE LA CURVA (Keypoints) ---
    p_strain = [0.0]
    p_stress = [0.0]
    
    # A. Límite Elástico (Yield)
    ey = Yield_Point / Modulus
    p_strain.append(ey)
    p_stress.append(Yield_Point)
    
    # Determinar si es frágil para la forma de la curva
    is_brittle = rupture_strain < 0.02
    
    if is_brittle:
        # Comportamiento lineal hasta rotura
        p_strain.append(rupture_strain)
        p_stress.append(Ultimate_Point)
        fracture_point = rupture_strain
    else:
        # Comportamiento Dúctil (Curva + Necking)
        
        # El pico (Su) ocurre ANTES de la ruptura.
        # Generalmente al 70-80% del camino en tracción.
        strain_at_peak = ey + (rupture_strain - ey) * 0.75
        
        if is_compression:
            # En compresión NO hay estricción (necking). Sigue subiendo.
            # Simulamos que aguanta mucho más allá del límite de tracción
            fracture_point = max_strain_machine * 2 # Nunca rompe visualmente
            
            p_strain.append(max_strain_machine)     # Punto lejano
            p_stress.append(Ultimate_Point * 1.2)   # Sigue endureciendo
        else:
            # Tensión / Torsión
            fracture_point = rupture_strain
            
            # Pico máximo
            p_strain.append(strain_at_peak)
            p_stress.append(Ultimate_Point)
            
            # Punto de rotura (Caída de esfuerzo)
            p_strain.append(fracture_point)
            p_stress.append(Ultimate_Point * 0.85) # Cae al 85% de Su al romper

    # --- 5. INTERPOLACIÓN Y GENERACIÓN DE DATOS ---
    # Generamos puntos hasta el límite que pide la MÁQUINA (Slider), no el material.
    dense_strain = np.linspace(0, max_strain_machine, puntos)
    dense_stress = []
    
    # Interpolador lineal básico para unir los puntos clave
    # (Podríamos usar splines, pero linear es robusto y predecible para esta demo)
    try:
        f_interp = interp1d(p_strain, p_stress, kind='linear', fill_value="extrapolate")
    except:
        f_interp = lambda x: Modulus * x

    for e in dense_strain:
        val = 0.0
        
        # Lógica de Corte (Ruptura)
        if e > fracture_point and not is_compression:
            val = None # El material ya rompió
        
        elif e <= ey:
            val = Modulus * e # Zona Elástica exacta
        
        else:
            # Zona Plástica
            if not is_brittle and not is_compression and e <= strain_at_peak:
                # Curva parabólica suave entre Yield y Peak
                # t = 0 en yield, t = 1 en peak
                t = (e - ey) / (strain_at_peak - ey)
                if t < 0: t = 0
                
                # Interpolación cuadrática para simular endurecimiento
                # Sigma = Sy + (Su-Sy) * t^n (donde n < 1 hace la panza hacia arriba)
                val = Yield_Point + (Ultimate_Point - Yield_Point) * (t ** 0.5)
            else:
                # Post-Peak (Necking) o Compresión Linealizada
                val = float(f_interp(e))

        # Signo correcto para compresión
        if is_compression and val is not None:
            val *= -1
            
        dense_stress.append(val)

    # Preparar DataFrame
    if is_compression: dense_strain = np.abs(dense_strain)

    df = pd.DataFrame({
        col_strain: dense_strain,
        col_stress: dense_stress
    })
    
    # Columna auxiliar de porcentaje
    if not is_torsion:
        df["Deformacion (%)"] = df[col_strain] * 100
    else:
        df["Deformacion (%)"] = df[col_strain]

    return df
