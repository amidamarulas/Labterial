import numpy as np
import pandas as pd

# ==============================================================================
# FUNCIONES GENERADORAS (Modelos Matemáticos Vectoriales)
# ==============================================================================

def curva_tension_metal(E, Sy, Su, epsilon_ruptura, p=500):
    """
    Genera la curva Esfuerzo-Deformación para metales bajo tracción.

    Implementa un modelo fenomenológico de tres etapas para materiales dúctiles:
    1. **Elástica:** Lineal siguiendo la Ley de Hooke ($\sigma = E \cdot \epsilon$).
    2. **Endurecimiento:** Curva de potencia desde la fluencia ($S_y$) hasta el esfuerzo último ($S_u$).
    3. **Estricción (Necking):** Caída parabólica del esfuerzo ingenieril desde $S_u$ hasta la ruptura.

    Args:
        E (float): Módulo de Young (MPa).
        Sy (float): Límite de Fluencia (MPa).
        Su (float): Esfuerzo Último (MPa).
        epsilon_ruptura (float): Deformación unitaria en el punto de quiebre.
        p (int, optional): Número de puntos a generar. Default 500.

    Returns:
        tuple: Dos arrays de numpy ``(deformacion, esfuerzo)``. El último punto de esfuerzo es ``None`` para simular el corte visual.
    """
    εy = Sy / E
    
    # Caso Frágil (Sin zona plástica significativa)
    if epsilon_ruptura <= εy: 
        e = np.linspace(0, epsilon_ruptura, p)
        s = E * e
        e = np.append(e, epsilon_ruptura * 1.001); s = np.append(s, None)
        return e, s

    # Caso Dúctil
    # Estimamos que el pico (Su) ocurre al 60% del camino plástico
    εu = εy + (epsilon_ruptura - εy) * 0.6 
    
    p1 = max(2, int(p * (εy / epsilon_ruptura)))
    p2 = max(2, int(p * ((εu - εy) / epsilon_ruptura)))
    p3 = max(2, p - p1 - p2)

    # Fase 1: Elástica
    e1 = np.linspace(0, εy, p1); s1 = E * e1
    
    # Fase 2: Endurecimiento (Hasta Su)
    e2 = np.linspace(εy, εu, p2)
    if (εu > εy):
        # Interpolación de potencia (Hollomon simplificado)
        s2 = Sy + (Su - Sy) * (((e2 - εy) / (εu - εy)) ** 0.5)
    else: s2 = np.full_like(e2, Su)

    # Fase 3: Estricción (Post Su)
    e3 = np.linspace(εu, epsilon_ruptura, p3)
    Sf = Su * 0.85 # Asumimos caída al 85% de carga antes de romper
    if (epsilon_ruptura > εu):
        s3 = Su - (Su - Sf) * (((e3 - εu) / (epsilon_ruptura - εu)) ** 2)
    else: s3 = np.full_like(e3, Sf)

    deformacion = np.concatenate((e1, e2, e3))
    esfuerzo = np.concatenate((s1, s2, s3))
    
    # Corte visual
    deformacion = np.append(deformacion, epsilon_ruptura * 1.001)
    esfuerzo = np.append(esfuerzo, None)
    return deformacion, esfuerzo

def curva_tension_polimero(E, Sy, Su, epsilon_ruptura, p=500):
    """
    Genera la curva para polímeros en tracción, simulando el fenómeno de 'Cold Drawing'.

    Modela el comportamiento complejo de polímeros semicristalinos (como Nylon o PE):
    1. **Elástica:** Lineal inicial.
    2. **Pico de Fluencia (Yield Drop):** Subida a un pico y caída posterior (Ablandamiento).
    3. **Meseta (Cold Drawing):** Zona de esfuerzo constante donde el cuello se propaga.
    4. **Endurecimiento:** Alineación de cadenas poliméricas antes de la ruptura.

    Args:
        E (float): Módulo de Young (MPa).
        Sy (float): Límite de Fluencia (MPa).
        Su (float): Esfuerzo Último (MPa).
        epsilon_ruptura (float): Deformación total.
        p (int): Resolución.

    Returns:
        tuple: Arrays ``(deformacion, esfuerzo)``.
    """
    εy = Sy / E
    
    # Caso Frágil (Termoestables o Amorfos rígidos)
    if epsilon_ruptura <= εy * 1.5: 
        e = np.linspace(0, epsilon_ruptura, p)
        # Modelo ligeramente no lineal
        s = E * e - (E * 0.2 * e**2 / epsilon_ruptura)
        s = np.minimum(s, Su)
        e = np.append(e, epsilon_ruptura * 1.001); s = np.append(s, None)
        return e, s

    # Caso Dúctil (Semicristalinos)
    Su_draw = Sy * 0.8; ε_cold_draw_end = epsilon_ruptura * 0.75
    p1 = int(p*0.1); p2 = int(p*0.1); p3 = int(p*0.5); p4 = max(2, p-p1-p2-p3)

    # 1. Elástica
    e1 = np.linspace(0, εy, p1); s1 = E * e1
    
    # 2. Caída (Yield Drop)
    e2 = np.linspace(εy, εy*2.5, p2)
    if len(e2)>0: s2 = Sy - (Sy - Su_draw) * (((e2-e2[0])/(e2[-1]-e2[0]))**0.5)
    else: s2 = []
    
    # 3. Meseta
    e3 = np.linspace(e2[-1], ε_cold_draw_end, p3); s3 = np.full_like(e3, Su_draw)
    
    # 4. Endurecimiento
    e4 = np.linspace(ε_cold_draw_end, epsilon_ruptura, p4)
    if len(e4)>0: s4 = Su_draw + (Su - Su_draw) * (((e4-e4[0])/(e4[-1]-e4[0]))**1.5)
    else: s4 = []

    deformacion = np.concatenate((e1, e2, e3, e4))
    esfuerzo = np.concatenate((s1, s2, s3, s4))
    
    deformacion = np.append(deformacion, epsilon_ruptura * 1.001)
    esfuerzo = np.append(esfuerzo, None)
    return deformacion, esfuerzo

def curva_compresion(E, Sy, Su, max_strain, p=500):
    """
    Genera la curva de compresión para materiales dúctiles.

    **Diferencia Física:** En compresión no existe la estricción (necking) que causa la caída
    aparente del esfuerzo en tracción. Debido al aumento del área transversal (efecto Poisson)
    y al endurecimiento, la curva crece indefinidamente sin romper.

    Args:
        max_strain (float): Deformación máxima dictada por el slider (no hay ruptura intrínseca).

    Returns:
        tuple: Arrays ``(deformacion, esfuerzo)`` con signo negativo para el esfuerzo.
    """
    εy = Sy / E
    p1 = max(2, int(p * 0.1)); p2 = max(2, p - p1)
    
    e1 = np.linspace(0, εy, p1); s1 = E * e1
    e2 = np.linspace(εy, max_strain, p2)
    
    if len(e2) > 0:
        # Modelo constitutivo de endurecimiento continuo
        K = (Su - Sy) / (0.2 ** 0.5) # Calibración empírica
        s2 = Sy + K * ((e2 - εy) ** 0.5)
    else: s2 = []
    
    return np.concatenate((e1, e2)), -np.concatenate((s1, s2))

def curva_torsion(G, Ty, Tu, gamma_ruptura, is_brittle, p=500):
    """
    Genera la curva de Esfuerzo Cortante vs Deformación Angular.

    Args:
        G (float): Módulo de Cortante (Shear Modulus).
        Ty (float): Esfuerzo de Fluencia en Corte (Yield Shear).
        Tu (float): Esfuerzo Último en Corte.
        gamma_ruptura (float): Ángulo máximo de deformación (rad).
        is_brittle (bool): Si es True, comportamiento lineal hasta rotura.

    Returns:
        tuple: Arrays ``(gamma, tau)``.
    """
    gy = Ty / G
    
    # CASO 1: FRÁGIL (Lineal hasta rotura)
    if is_brittle or gamma_ruptura <= gy:
        g = np.linspace(0, gamma_ruptura, p)
        t = G * g
        g = np.append(g, gamma_ruptura * 1.001)
        t = np.append(t, None)
        return g, t

    # CASO 2: DÚCTIL (Gran deformación plástica sin estricción)
    p1 = max(2, int(p * 0.10)) 
    p2 = max(2, p - p1)
    
    g1 = np.linspace(0, gy, p1)
    t1 = G * g1
    
    g2 = np.linspace(gy, gamma_ruptura, p2)
    if len(g2) > 0:
        # Endurecimiento suave (casi plano) típico de torsión
        ratio = (g2 - gy) / (gamma_ruptura - gy)
        t2 = Ty + (Tu - Ty) * (ratio ** 0.2)
    else: t2 = []
        
    g_total = np.concatenate((g1, g2))
    t_total = np.concatenate((t1, t2))
    
    g_total = np.append(g_total, gamma_ruptura * 1.001)
    t_total = np.append(t_total, None)
    return g_total, t_total

# ==============================================================================
# ORQUESTADOR PRINCIPAL
# ==============================================================================

def simular_ensayo(material_props, tipo_ensayo, max_strain_machine=0.05, puntos=500):
    """
    Función principal que orquesta la simulación física.

    1.  **Extracción de Propiedades:** Lee el diccionario de material y convierte unidades a SI base.
    2.  **Cálculo de Ductilidad:** Estima el punto de ruptura intrínseco basado en la familia 
        del material (Metal, Polímero, Cerámico) y sus propiedades ($E, S_y, S_u$).
    3.  **Generación:** Despacha la tarea a la función generadora específica (ej. ``curva_tension_polimero``)
        según el tipo de ensayo.
    4.  **Recorte:** Filtra los datos generados para que coincidan con el límite visual de la máquina
        (slider), pero conservando el punto de ruptura si ocurre antes.

    Args:
        material_props (dict): Propiedades del material (elastic_modulus, yield_strength, etc).
        tipo_ensayo (str): 'Tension', 'Compresion', 'Torsion', 'Flexion'.
        max_strain_machine (float): Límite del eje X definido por el usuario.
        puntos (int): Resolución.

    Returns:
        pd.DataFrame: DataFrame con columnas ``Deformacion``, ``Esfuerzo (MPa)`` y ``Deformacion (%)``.
    """
    
    E = float(material_props['elastic_modulus'])
    Sy = float(material_props['yield_strength'])
    Su = material_props.get('ultimate_strength')
    Nu = material_props.get('poisson_ratio', 0.3)
    Cat = material_props.get('category', 'Metal')
    
    if Su is None or Su <= Sy: Su = Sy * 1.1

    # --- DUCTILIDAD BASE (Axial) ---
    rupture_strain = 0.01
    if Cat == 'Metal':
        ratio = (Su / Sy) - 1
        rupture_strain = min(0.60, max(0.01, 0.02 + (ratio * 0.5)))
    elif Cat == 'Polimero':
        # Heurística calibrada: E<500 -> Gomas (300%), E>2500 -> Rígidos
        if E < 500: rupture_strain = 3.0
        elif E < 2500: rupture_strain = 1200.0 / E 
        else: rupture_strain = 0.05 + (500.0 / E)
    elif Cat in ['Ceramico', 'Vidrio']:
        rupture_strain = (Sy / E) + 0.0005
    elif Cat == 'Compuesto':
        rupture_strain = (Su / E) * 1.2

    # --- AJUSTE PARA TORSIÓN (Ductilidad Angular Amplificada) ---
    if tipo_ensayo == 'Torsion':
        if Cat in ['Metal', 'Polimero'] and rupture_strain > 0.05:
            rupture_strain *= 6.0 
        else:
            rupture_strain *= 1.3

    # --- SIMULACIÓN SEGÚN TIPO ---
    strain_vec = np.array([])
    stress_vec = np.array([])
    
    if tipo_ensayo == 'Torsion':
        G = E / (2 * (1 + Nu))
        Ty = Sy * 0.577 # Von Mises
        Tu = Su * 0.7 
        is_brittle = (Cat in ['Ceramico', 'Vidrio']) or (rupture_strain < 0.05)
        strain_vec, stress_vec = curva_torsion(G, Ty, Tu, rupture_strain, is_brittle, puntos)
        
    elif tipo_ensayo == 'Tension':
        if Cat == 'Polimero':
            strain_vec, stress_vec = curva_tension_polimero(E, Sy, Su, rupture_strain, puntos)
        elif Cat in ['Ceramico', 'Vidrio', 'Compuesto']:
            strain_vec = np.linspace(0, rupture_strain, puntos)
            stress_vec = E * strain_vec
            strain_vec = np.append(strain_vec, rupture_strain*1.001)
            stress_vec = np.append(stress_vec, None)
        else:
            strain_vec, stress_vec = curva_tension_metal(E, Sy, Su, rupture_strain, puntos)
            
    elif tipo_ensayo == 'Compresion':
        limit = max(max_strain_machine * 1.2, rupture_strain)
        strain_vec, stress_vec = curva_compresion(E, Sy, Su, limit, puntos)
        stress_vec *= -1
        
    elif tipo_ensayo == 'Flexion':
        # Flexión 3 puntos: Usa modelo tracción metal con MOR (Módulo Ruptura)
        factor_mor = 1.2
        strain_vec, stress_vec = curva_tension_metal(E, Sy, Su*factor_mor, rupture_strain, puntos)

    # --- RECORTE DE DATOS (CLIPPING) ---
    df = pd.DataFrame({"e": strain_vec, "s": stress_vec})
    mask = (df["e"] <= max_strain_machine) | (df["s"].isna())
    df = df[mask].copy()
    
    # Limpieza de bordes si el corte visual quedó muy lejos
    if not df.empty and not pd.isna(df.iloc[-1]["s"]):
         if df.iloc[-1]["e"] > max_strain_machine * 1.01:
             df = df[df["e"] <= max_strain_machine]

    # Formateo final
    col_strain = "Deformacion (rad)" if tipo_ensayo == 'Torsion' else "Deformacion (mm/mm)"
    final = pd.DataFrame({
        col_strain: df["e"],
        "Esfuerzo (MPa)": df["s"]
    })
    
    if tipo_ensayo != 'Torsion': final["Deformacion (%)"] = final[col_strain] * 100
    else: final["Deformacion (%)"] = final[col_strain]

    return final
