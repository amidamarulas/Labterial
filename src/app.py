import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Intentos de importación para manejar ejecución local vs Sphinx
try:
    from database_mgr import get_all_materials, insert_from_dataframe
    from physics import simular_ensayo
except ImportError:
    from src.database_mgr import get_all_materials, insert_from_dataframe
    from src.physics import simular_ensayo

def configure_page():
    """
    Configura los parámetros generales de la página de Streamlit.
    
    Establece el título de la pestaña del navegador, el layout 'wide' 
    y muestra el título principal de la aplicación.
    """
    st.set_page_config(page_title="Lab Materiales", layout="wide")
    st.title("🏗️ Simulador Universal de Ensayos")

def load_data():
    """
    Carga los datos iniciales desde la base de datos.

    Returns:
        pd.DataFrame: DataFrame con todos los materiales crudos.
    """
    return get_all_materials()

def render_sidebar(df_raw):
    """
    Renderiza la barra lateral de filtros.

    Args:
        df_raw (pd.DataFrame): El DataFrame completo de materiales.

    Returns:
        pd.DataFrame: Un nuevo DataFrame filtrado según las categorías seleccionadas por el usuario.
    """
    st.sidebar.header("Base de Datos")
    cats = df_raw['category'].unique().tolist()
    sel_cats = st.sidebar.multiselect("Filtros", cats, default=cats)
    
    if sel_cats:
        return df_raw[df_raw['category'].isin(sel_cats)]
    return df_raw

def render_tab_management(df_mats):
    """
    Renderiza el contenido de la Pestaña 1: Gestión de Base de Datos.

    Incluye la tabla de visualización de materiales, el cargador de archivos CSV
    y el botón de descarga de la base de datos.

    Args:
        df_mats (pd.DataFrame): DataFrame de materiales filtrados a mostrar.
    """
    c1, c2 = st.columns([3,1])
    with c1: 
        st.dataframe(df_mats, use_container_width=True)
    with c2:
        with st.expander("Importar CSV"):
            up = st.file_uploader("Archivo", type=['csv'])
            if up and st.button("Cargar"):
                a, i, e = insert_from_dataframe(pd.read_csv(up))
                if e: st.error(e)
                else: st.success(f"Ok: {a}"); st.rerun()
        
        st.divider()
        # Botón de descarga
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'materials.db')
            with open(db_path, "rb") as fp:
                st.download_button("💾 Backup BD", fp, "materials.db")
        except: pass

def render_tab_simulation(df_mats):
    """
    Renderiza el contenido de la Pestaña 2: Simulación Mecánica.

    Maneja la lógica de selección de probeta, configuración de la máquina (Slider),
    llamada al motor físico (physics.py) y graficación con Plotly.

    Args:
        df_mats (pd.DataFrame): DataFrame de materiales disponibles para seleccionar.
    """
    if df_mats.empty: 
        st.warning("No hay materiales disponibles para simular.")
        return
    
    st.header("Ensayo Mecánico")
    conf, graf = st.columns([1, 3])
    
    with conf:
        st.subheader("Máquina")
        mat_name = st.selectbox("Probeta", df_mats['name'].unique())
        modo = st.radio("Modo", ["Tension", "Compresion", "Torsion"])
        
        # Configuración del Slider (Límite de la máquina)
        lbl = "Límite de Carrera (%)" if modo != "Torsion" else "Límite Angular (rad)"
        max_v = 40.0 if modo != "Torsion" else 0.8
        slider_val = st.slider(lbl, 0.1, max_v, 20.0)
        
        machine_limit = slider_val / 100 if modo != "Torsion" else slider_val
        
        # Datos del material seleccionado
        dat = df_mats[df_mats['name'] == mat_name].iloc[0]
        st.divider()
        st.caption(f"Material: {dat['category']}")
        st.write(f"**Sy:** {dat['yield_strength']} MPa")

    with graf:
        # Preparar propiedades para física
        props = dict(dat)
        props['category'] = dat['category'] 
        
        # Ejecutar simulación
        df_sim = simular_ensayo(props, modo, max_strain_machine=machine_limit)
        
        # Graficar
        y_col = "Esfuerzo (MPa)"
        x_col = "Deformacion (%)" if modo != "Torsion" else "Deformacion (rad)"
        
        fig = px.line(df_sim, x=x_col, y=y_col, title=f"Curva {modo}: {mat_name}", markers=True)
        
        if modo != "Torsion": fig.update_xaxes(range=[0, slider_val]) 
        else: fig.update_xaxes(range=[0, slider_val])

        clr = "royalblue" if modo == "Tension" else ("firebrick" if modo == "Compresion" else "orange")
        fig.update_traces(line=dict(color=clr, width=3), connectgaps=False)
        
        # Líneas de referencia
        signo = -1 if modo == "Compresion" else 1
        f_sy = 0.577 if modo == "Torsion" else 1.0
        fig.add_hline(y=dat['yield_strength']*f_sy*signo, line_dash="dash", line_color="green", annotation_text="Sy")
        
        if modo != "Compresion":
             f_su = 0.6 if modo == "Torsion" else 1.0
             fig.add_hline(y=dat['ultimate_strength']*f_su, line_dash="dot", line_color="red", annotation_text="Su")

        st.plotly_chart(fig, use_container_width=True)

def render_tab_reports(df_mats):
    """
    Renderiza el contenido de la Pestaña 3: Reportes y Tablas.

    Args:
        df_mats (pd.DataFrame): DataFrame base para generar reportes.
    """
    if not df_mats.empty:
        s = st.multiselect("Filtrar Materiales Específicos", df_mats['name'].unique())
        if s: 
            st.dataframe(df_mats[df_mats['name'].isin(s)])
        else:
            st.info("Selecciona materiales para ver detalles.")

def main():
    """
    Función principal que orquesta la aplicación.
    
    Llama a las funciones de configuración, carga de datos y renderizado de pestañas.
    """
    configure_page()
    df_raw = load_data()
    df_mats = render_sidebar(df_raw)
    
    tab1, tab2, tab3 = st.tabs(["Base de Datos", "Simulación", "Reportes"])
    
    with tab1: render_tab_management(df_mats)
    with tab2: render_tab_simulation(df_mats)
    with tab3: render_tab_reports(df_mats)

if __name__ == "__main__":
    main()
