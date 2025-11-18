import streamlit as st
import pandas as pd
import plotly.express as px

# Importacion relativa o directa dependiendo de como se ejecute
try:
    from database_mgr import get_all_materials, add_material, import_materials_from_df 
    from physics import simular_ensayo_avanzado
except ImportError:
    from src.database_mgr import get_all_materials, add_material, import_materials_from_df
    from src.physics import simular_ensayo_avanzado

st.set_page_config(page_title="Banco de Materiales", layout="wide")
st.title("🔩 Software de Materiales Interactivo")

tab1, tab2, tab3 = st.tabs(["📋 Materiales", "📈 Simulación", "📊 Tablas"])

# --- TAB 1: GESTIÓN DE MATERIALES ---
with tab1:
    st.header("📦 Inventario de Materiales")
    
    # 1. Mostrar Tabla Actual
    df_materials = get_all_materials()
    st.dataframe(df_materials, use_container_width=True)
    
    st.divider()
    
    col_manual, col_csv = st.columns(2)
    
    # --- COLUMNA IZQUIERDA: AGREGAR UNO A UNO ---
    with col_manual:
        st.subheader("Agregar Material Manualmente")
        with st.form("form_add_mat"):
            name = st.text_input("Nombre", placeholder="Ej. Acero 1020")
            e_mod = st.number_input("Módulo Young (MPa)", value=200000.0)
            sy = st.number_input("Límite Fluencia (MPa)", value=250.0)
            su = st.number_input("Esfuerzo Último (MPa)", value=400.0)
            nu = st.number_input("Poisson", value=0.3, max_value=0.5)
            
            if st.form_submit_button("💾 Guardar Material"):
                if add_material(name, e_mod, sy, su, nu):
                    st.success(f"✅ {name} guardado.")
                    import time
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Error: Ese nombre ya existe.")

    # --- COLUMNA DERECHA: IMPORTAR CSV ---
    with col_csv:
        st.subheader("Importar desde CSV")
        st.write("Carga múltiples materiales masivamente.")
        
        # Generar plantilla para descargar
        df_template = pd.DataFrame({
            'name': ['Acero Inoxidable 304', 'Latón C260'],
            'elastic_modulus': [193000, 105000],
            'yield_strength': [215, 300],
            'ultimate_strength': [505, 400],
            'poisson_ratio': [0.29, 0.34]
        })
        csv = df_template.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            "⬇️ Descargar Plantilla CSV",
            data=csv,
            file_name="plantilla_materiales.csv",
            mime="text/csv",
            help="Usa este archivo como base para llenar tus datos."
        )
        
        uploaded_file = st.file_uploader("Subir archivo .csv", type="csv")
        
        if uploaded_file:
            if st.button("Procesar Archivo"):
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    imported, dups, err = import_materials_from_df(df_upload)
                    
                    if err:
                        st.error(err)
                    else:
                        msg = f"✅ Se importaron {imported} materiales."
                        if dups > 0:
                            msg += f" (Se omitieron {dups} duplicados)."
                        st.success(msg)
                        
                        if imported > 0:
                            import time
                            time.sleep(1.5)
                            st.rerun()
                except Exception as e:
                    st.error(f"Error leyendo el archivo: {e}")

# --- TAB 2: SIMULACIÓN DE LABORATORIO ---
with tab2:
    st.header("🔬 Laboratorio Virtual: Máquina Universal")
    
    # --- DEFINICIÓN DE PROBETA ESTÁNDAR (CONSTANTES) ---
    # Usamos dimensiones típicas de una probeta estándar (ej. similar a ASTM E8)
    STD_DIAMETRO = 12.5  # mm (aprox 0.5 pulgadas)
    STD_LONGITUD = 50.0  # mm (longitud calibrada, aprox 2 pulgadas)
    
    col_config, col_plot = st.columns([1, 3])
    
    with col_config:
        st.subheader("1. Configuración del Ensayo")
        
        # Selector de Material
        lista_nombres = df_materials['name'].tolist()
        nombre_seleccionado = st.selectbox("Seleccionar Material", lista_nombres)
        
        st.divider()
        
        st.subheader("2. Datos de la Probeta")
        st.info("ℹ️ Se utilizará una probeta estandarizada para todos los ensayos.")
        
        # Mostrar las dimensiones fijas como métricas visuales (solo lectura)
        c_d, c_l = st.columns(2)
        c_d.metric("Diámetro", f"{STD_DIAMETRO} mm")
        c_l.metric("Longitud", f"{STD_LONGITUD} mm")
        
        st.divider()
        
        st.subheader("3. Método de Carga")
        tipo_ensayo = st.radio("Tipo de Ensayo", ["Tension", "Compresion", "Torsion"])
        
        # Botón de acción
        run_sim = st.button("▶️ Iniciar Ensayo", type="primary")
    
    with col_plot:
        if run_sim:
            # Obtener datos del material
            mat_data = df_materials[df_materials['name'] == nombre_seleccionado].iloc[0]
            props = {
                'elastic_modulus': mat_data['elastic_modulus'],
                'yield_strength': mat_data['yield_strength'],
                'ultimate_strength': mat_data['ultimate_strength'],
                'poisson_ratio': mat_data['poisson_ratio']
            }
            
            # Llamar a la simulación pasando las CONSTANTES definidas arriba
            try:
                df_sim, max_val, label_max, unit = simular_ensayo_avanzado(
                    props, 
                    tipo_ensayo, 
                    STD_DIAMETRO,  # <--- Valor Fijo
                    STD_LONGITUD   # <--- Valor Fijo
                )
                
                # Configuración de gráficas
                if tipo_ensayo == 'Torsion':
                    x_col = "Angulo de Giro (grados)"
                    y_col = "Torque (N.m)"
                    title_chart = f"Diagrama Torque vs Ángulo - {nombre_seleccionado}"
                    color_line = "orange"
                elif tipo_ensayo == 'Compresion':
                    x_col = "Desplazamiento (mm)"
                    y_col = "Fuerza (N)"
                    title_chart = f"Diagrama Fuerza vs Desplazamiento - {nombre_seleccionado} (Compresión)"
                    color_line = "red"
                else: # Tension
                    x_col = "Desplazamiento (mm)"
                    y_col = "Fuerza (N)"
                    title_chart = f"Diagrama Fuerza vs Desplazamiento - {nombre_seleccionado} (Tracción)"
                    color_line = "blue"

                # 1. Gráfica Principal (Fuerza vs Desplazamiento)
                fig = px.line(df_sim, x=x_col, y=y_col, title=title_chart)
                fig.update_traces(line_color=color_line, line_width=3)
                
                # Añadir área sombreada bajo la curva
                fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
                st.plotly_chart(fig, use_container_width=True)
                
                # 2. Resultados Numéricos
                st.subheader("Resultados del Ensayo")
                m1, m2, m3 = st.columns(3)
                
                m1.metric(label=label_max, value=f"{max_val:.2f} {unit}")
                
                if tipo_ensayo != 'Torsion':
                    # Calcular elongación porcentual final
                    deformacion_max = df_sim["Deformacion Unit (mm/mm)"].abs().max()
                    m2.metric(label="Elongación Máxima", value=f"{deformacion_max*100:.1f} %")
                    
                    esfuerzo_max = df_sim["Esfuerzo (MPa)"].abs().max()
                    m3.metric(label="Esfuerzo Máximo", value=f"{esfuerzo_max:.0f} MPa")
                else:
                    angulo_max = df_sim["Angulo de Giro (grados)"].max()
                    m2.metric(label="Ángulo Máximo", value=f"{angulo_max:.1f} °")
                    
                    tau_max = df_sim["Esfuerzo Cortante (MPa)"].max()
                    m3.metric(label="Esfuerzo Cortante Máx", value=f"{tau_max:.0f} MPa")

                # 3. Curva Ingeniería (Oculta por defecto)
                with st.expander("Ver Curva de Ingeniería (Esfuerzo-Deformación)"):
                    if tipo_ensayo == 'Torsion':
                        fig_eng = px.line(df_sim, x="Deformacion Angular (rad)", y="Esfuerzo Cortante (MPa)", 
                                          title="Esfuerzo de Corte vs Deformación Angular")
                    else:
                        fig_eng = px.line(df_sim, x="Deformacion Unit (mm/mm)", y="Esfuerzo (MPa)", 
                                          title="Esfuerzo Normal vs Deformación Unitaria")
                    st.plotly_chart(fig_eng, use_container_width=True)

            except Exception as e:
                st.error(f"Error en la simulación: {e}")
        else:
            st.info("👈 Presiona 'Iniciar Ensayo' para someter la probeta a carga.")

# --- TAB 3: TABLAS ---
with tab3:
    st.header("Reportes Personalizados")
    mats = st.multiselect("Materiales", df_materials['name'].unique(), default=df_materials['name'].iloc[0])
    cols = st.multiselect("Propiedades", [c for c in df_materials.columns if c != 'id'], default=['name', 'yield_strength'])
    
    if mats and cols:
        df_custom = df_materials[df_materials['name'].isin(mats)][cols]
        st.dataframe(df_custom, use_container_width=True)
