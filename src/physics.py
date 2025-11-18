import numpy as np
import pandas as pd

def calcular_geometria(diametro_mm, longitud_mm):
    """Calcula Área (mm2) y Momento Polar de Inercia J (mm4)"""
    radio = diametro_mm / 2.0
    area = np.pi * (radio ** 2)
    # J = pi * r^4 / 2 (para sección circular maciza)
    J = (np.pi * (radio ** 4)) / 2
    return area, J, radio

def modelo_material_completo(strain_array, E, Sy, Su, fracture_strain):
    """
    Genera la curva de esfuerzo (Stress) basada en la deformación (Strain)
    hasta el punto de ruptura.
    """
    stress = []
    epsilon_y = Sy / E # Deformación de fluencia
    
    # Si no hay esfuerzo último definido, asumimos un endurecimiento del 20%
    if not Su or Su < Sy:
        Su = Sy * 1.2
        
    for e in strain_array:
        if e <= epsilon_y:
            # 1. ZONA ELÁSTICA LINEAL
            s = E * e
        elif e <= fracture_strain:
            # 2. ZONA PLÁSTICA (Endurecimiento por deformación)
            # Usamos una función de potencia simple para conectar Sy con Su
            # Sigma = Sy + K * (e - ey)^n
            # Simplificación parabólica para simulación visual:
            
            progress = (e - epsilon_y) / (fracture_strain - epsilon_y)
            # Curva suave que va de Sy a Su
            s = Sy + (Su - Sy) * (2*progress - progress**2)
        else:
            # ROTO
            s = 0 
            
        stress.append(s)
    return np.array(stress)

def simular_ensayo_avanzado(props, tipo_ensayo, diametro, longitud):
    """
    Simula el ensayo completo hasta la ruptura.
    
    Args:
        props: Diccionario con propiedades (E, Sy, Su, Nu).
        tipo_ensayo: 'Tension', 'Compresion', 'Torsion'.
        diametro: mm.
        longitud: mm.
    
    Returns:
        DataFrame con datos de simulación (Fuerza, Desplazamiento, Esfuerzo, Deformación)
        Resumen de resultados (Fuerza Máxima, etc)
    """
    # 1. Obtener Propiedades y Geometría
    E = props['elastic_modulus']
    Sy = props['yield_strength']
    Su = props['ultimate_strength']
    Nu = props.get('poisson_ratio', 0.3) or 0.3
    
    Area, J, Radio = calcular_geometria(diametro, longitud)
    
    # Asumimos una deformación de ruptura (fracture strain) estándar si no está en DB
    # En un software real, esto debería ser un campo en la BD "elongation_at_break"
    fracture_strain = 0.20 # 20% de deformación al quiebre por defecto
    puntos = 200
    
    # Generar array de deformación (0 hasta ruptura)
    strain = np.linspace(0, fracture_strain, puntos)
    
    # --- LÓGICA SEGÚN TIPO DE ENSAYO ---
    
    if tipo_ensayo == 'Torsion':
        # CÁLCULO DE TORSIÓN
        # Relaciones aproximadas (Von Mises / Teoría de falla dúctil)
        # Módulo de corte G
        G = E / (2 * (1 + Nu))
        # Resistencia al corte (aprox 0.577 de la tensión)
        Ty = Sy * 0.577
        Tu = Su * 0.577 if Su else Ty * 1.2
        
        # El "strain" aquí es Gamma (deformación angular unitaria)
        # Reutilizamos la lógica del modelo material pero con G, Ty, Tu
        shear_stress = modelo_material_completo(strain, G, Ty, Tu, fracture_strain)
        
        # Convertir a Torque y Ángulo de giro
        # Tau = T * r / J  --> T = Tau * J / r
        torque = (shear_stress * J) / Radio # N.mm
        torque_Nm = torque / 1000 # N.m
        
        # Gamma = angle * r / L --> angle = Gamma * L / r
        angle_rad = (strain * longitud) / Radio
        angle_deg = np.degrees(angle_rad)
        
        df = pd.DataFrame({
            "Angulo de Giro (grados)": angle_deg,
            "Torque (N.m)": torque_Nm,
            "Esfuerzo Cortante (MPa)": shear_stress,
            "Deformacion Angular (rad)": strain
        })
        
        max_val = np.max(torque_Nm)
        label_max = "Torque Máximo de Ruptura"
        unit = "N.m"

    else:
        # CÁLCULO DE TENSIÓN / COMPRESIÓN
        stress = modelo_material_completo(strain, E, Sy, Su, fracture_strain)
        
        # Fuerza = Esfuerzo * Área
        force = stress * Area # Newtons
        
        # Desplazamiento (Delta L) = Strain * L0
        displacement = strain * longitud # mm
        
        if tipo_ensayo == 'Compresion':
            force = force * -1
            stress = stress * -1
            displacement = displacement * -1
            strain = strain * -1
            
        df = pd.DataFrame({
            "Desplazamiento (mm)": displacement,
            "Fuerza (N)": force,
            "Esfuerzo (MPa)": stress,
            "Deformacion Unit (mm/mm)": strain
        })
        
        max_val = np.max(np.abs(force))
        label_max = "Carga Máxima (Falla)"
        unit = "N"

    return df, max_val, label_max, unit