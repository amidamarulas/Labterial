import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# --- SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .database_mgr import get_all_materials, insert_from_dataframe
    from .physics import simular_ensayo
except ImportError:
    from database_mgr import get_all_materials, insert_from_dataframe
    from physics import simular_ensayo

MPA_TO_KSI = 0.1450377

LABEL_MAP = {
    "name": "Material", "category": "Categoría",
    "elastic_modulus": "Módulo de Young (E)", "yield_strength": "Límite Elástico (Sy)",
    "ultimate_strength": "Resistencia Máxima (Su)", "poisson_ratio": "Coeficiente Poisson (ν)",
    "density": "Densidad", "cost": "Costo", "max_temp": "Temp. Máx"
}

def translate_df(df):
    """Ayuda interna para renombrar columnas técnicas a nombres legibles en Español."""
    return df.rename(columns=LABEL_MAP)

def configure_page():
    """
    Configura los parámetros iniciales de la aplicación Streamlit.
    
    Establece el título de la pestaña, el favicon y el modo 'wide' para aprovechar
    toda la pantalla.
    """
    st.set_page_config(page_title="Labterial Edu", layout="wide", page_icon="🧪")
    st.title("🧪 Labterial: Suite de Ingeniería")

def load_data():
    """Wrapper para cargar la base de datos completa."""
    return get_all_materials()

def render_sidebar(df_raw):
    """
    Renderiza la barra lateral de navegación y configuración global.

    Incluye:
    
    *   Filtros por Categoría de material.
    *   Controles del **Modo Profesor** (Checkbox para ecuaciones).

    Args:
        df_raw (pd.DataFrame): DataFrame base con todos los materiales.

    Returns:
        tuple: (DataFrame filtrado, booleano show_math).
    """
    st.sidebar.header("🔍 Filtros")
    st.sidebar.divider()
    st.sidebar.subheader("👨‍🏫 Modo Profesor")
    show_math = st.sidebar.checkbox("Mostrar Explicación Física", value=True)
    st.sidebar.divider()
    if isinstance(df_raw, pd.DataFrame) and 'category' in df_raw.columns:
        cats = df_raw['category'].unique().tolist()
        sel_cats = st.sidebar.multiselect("Categoría", cats, default=cats)
        if sel_cats: return df_raw[df_raw['category'].isin(sel_cats)], show_math
    return df_raw, show_math

def render_tab_management(df_mats):
    """
    Renderiza la Pestaña 1: Gestión de Inventario.

    Permite visualizar la tabla de materiales, cargar nuevos datos vía CSV
    y descargar copias de seguridad de la base de datos SQLite.

    Args:
        df_mats (pd.DataFrame): Datos a mostrar.
    """
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📋 Inventario")
        st.dataframe(translate_df(df_mats), use_container_width=True, height=400)
    with c2:
        st.subheader("Gestión")
        with st.expander("📥 Importar CSV"):
            up = st.file_uploader("Archivo", type=['csv'])
            if up and st.button("Cargar"):
                try:
                    df_new = pd.read_csv(up)
                    a, i, e = insert_from_dataframe(df_new)
                    if e: st.error(e)
                    else: st.success(f"Ok: {a}"); st.rerun()
                except Exception as ex: st.error(ex)
        try:
            from pathlib import Path
            pkg = __package__ if __package__ else 'labterial'
            db_path = Path.home() / f".{pkg}" / "materials.db"
            if not db_path.exists(): db_path = Path(__file__).parent.parent.parent / 'data' / 'materials.db'
            if db_path.exists():
                with open(db_path, "rb") as fp: st.download_button("💾 Backup BD", fp, "materials.db")
        except: pass

def render_math_explainer(dat, modo, units, factor, unit_label, geom_params=None):
    """
    Componente pedagógico que renderiza explicaciones físicas y matemáticas dinámicas.

    Se adapta según el tipo de ensayo (Tensión, Flexión, etc.) para mostrar
    las fórmulas correctas (Hooke, Von Mises, Escuadría) y explicar los fenómenos
    físicos subyacentes.

    Args:
        dat (Series): Propiedades del material seleccionado.
        modo (str): Tipo de ensayo actual.
        units (str): Nombre del sistema de unidades.
        factor (float): Factor de conversión de unidades.
        geom_params (tuple, optional): Dimensiones (L, b, d) si es Flexión.
    """
    E = dat['elastic_modulus'] * factor
    Sy = dat['yield_strength'] * factor
    
    st.info(f"📘 **Fundamentos Físicos: {modo}**")
    t1, t2 = st.tabs(["1. Mecánica Elástica", "2. Análisis de Falla"])
    
    if modo == "Flexion":
        L, b, d = geom_params if geom_params else (100, 10, 5)
        I = (b * d**3) / 12
        with t1:
            c_txt, c_eq = st.columns([3, 2])
            with c_txt:
                st.markdown("**Flexión de 3 Puntos:**")
                st.markdown(f"La pendiente depende de la geometría ($I$):")
                st.caption(f"Inercia I = {I:.1f} mm⁴")
            with c_eq:
                st.markdown("#### Relación Fuerza-Esfuerzo")
                st.latex(r"F = \frac{2 \cdot \sigma \cdot b \cdot d^2}{3 \cdot L}")
        with t2:
            st.markdown("**Deflexión ($\delta$):**")
            st.latex(r"\delta = \frac{\epsilon \cdot L^2}{6 \cdot d}")

    elif modo == "Torsion":
        G = E / (2 * (1 + dat.get('poisson_ratio', 0.3)))
        with t1:
            st.markdown("**Cizalladura:** Deslizamiento de planos.")
            st.caption(f"Módulo de Corte G ≈ {G:,.0f} {unit_label}")
            st.latex(r"\tau = G \cdot \gamma")
        with t2:
            st.markdown("Criterio Von Mises:")
            st.latex(r"\tau_{y} \approx 0.577 \cdot \sigma_{y}")

    elif modo == "Compresion":
        with t1:
            st.markdown("**Acortamiento:**")
            st.latex(r"\sigma = - E \cdot \epsilon")
        with t2:
            st.markdown("Sin estricción, el esfuerzo aparente sube indefinidamente.")

    else: # Tension
        with t1:
            st.markdown("**Tracción Uniaxial:**")
            st.latex(r"\sigma = E \cdot \epsilon")
        with t2:
            st.markdown("Ley de Hollomon:")
            st.latex(r"\sigma = K \cdot \epsilon^n")

def render_tab_simulation(df_mats, show_math):
    """
    Renderiza la Pestaña 2: Laboratorio Virtual.

    Esta función es el núcleo de la aplicación. Gestiona:
    
    1.  **Configuración:** Selección de unidades, materiales y tipo de ensayo.
    2.  **Motor de Simulación:** Llama a ``physics.py`` para cada material.
    3.  **Visualización:** Genera gráficas interactivas con Plotly.
    4.  **Benchmarking:** Genera gráficas de barras comparativas.
    5.  **Pedagogía:** Llama al explicador matemático si está activo.

    Args:
        df_mats (pd.DataFrame): Materiales disponibles.
        show_math (bool): Si es True, muestra el panel educativo.
    """
    if df_mats.empty: st.warning("Sin datos."); return
    st.header("🔬 Laboratorio Virtual")
    col_ctrl, col_plot = st.columns([1, 3])
    geom = None

    with col_ctrl:
        st.subheader("Configuración")
        units = st.radio("Unidades", ["SI (MPa)", "Imperial (ksi)"], horizontal=True)
        is_imperial = "Imperial" in units
        unit_label = "ksi" if is_imperial else "MPa"
        factor = MPA_TO_KSI if is_imperial else 1.0
        
        st.divider()
        mats_avail = df_mats['name'].unique()
        sel = st.multiselect("Probetas", options=mats_avail, default=[mats_avail[0]] if len(mats_avail)>0 else None)
        
        st.divider()
        modo = st.radio("Ensayo", ["Tension", "Compresion", "Torsion", "Flexion"])
        
        slider_max_def = 15.0
        
        if modo == "Flexion":
            st.info("📏 Geometría (mm)")
            c_L, c_dim = st.columns(2)
            with c_L: L_val = st.number_input("Largo (L)", value=200.0)
            with c_dim: 
                b_val = st.number_input("Ancho (b)", value=20.0)
                d_val = st.number_input("Espesor (d)", value=10.0)
            geom = (L_val, b_val, d_val)
            slider_max_def = 5.0 
        
        lbl = "Límite Carrera (%)" if (modo!="Torsion") else "Ángulo (rad)"
        max_v = 40.0 if modo!="Torsion" else 1.0
        slider = st.slider(lbl, 0.1, max_v, slider_max_def)
        limit = slider/100 if modo!="Torsion" else slider

    with col_plot:
        if not sel: st.info("Selecciona material."); return
        fig = go.Figure()
        export_data = []

        for mat in sel:
            dat = df_mats[df_mats['name'] == mat].iloc[0]
            props = dict(dat); props['category'] = dat.get('category', 'Metal')
            
            df_sim = simular_ensayo(props, modo, max_strain_machine=limit)
            
            if modo == "Flexion":
                sigma_si = df_sim["Esfuerzo (MPa)"]
                epsilon_si = df_sim["Deformacion (mm/mm)"]
                F_val = (2 * sigma_si * b_val * (d_val**2)) / (3 * L_val)
                Delta_val = (epsilon_si * (L_val**2)) / (6 * d_val)
                x_vals = Delta_val; y_vals = F_val
                x_title = "Deflexión (mm)"; y_title = "Fuerza (N)"
                if is_imperial:
                    x_vals *= 0.0393701; y_vals *= 0.224809
                    x_title = "Deflexión (in)"; y_title = "Fuerza (lbf)"
            else:
                y_vals = df_sim["Esfuerzo (MPa)"] * factor
                x_col = "Deformacion (%)" if modo!="Torsion" else "Deformacion (rad)"
                x_vals = df_sim[x_col]
                x_title = x_col.replace("Deformacion", "Deformación")
                y_title = f"Esfuerzo ({unit_label})"

            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name=mat, line=dict(width=3)))
            
            df_tmp = pd.DataFrame({x_title: x_vals, y_title: y_vals, 'Material': mat})
            export_data.append(df_tmp)

        title_map = {"Tension": "Tracción", "Compresion": "Compresión", "Torsion": "Torsión", "Flexion": "Ensayo de Flexión"}
        fig.update_layout(title=f"Curvas ({units}) - {title_map[modo]}", 
                          xaxis_title=x_title, yaxis_title=y_title, 
                          hovermode="x unified", template="plotly_white")
        if modo != "Flexion": fig.update_xaxes(range=[0, slider])
        st.plotly_chart(fig, use_container_width=True)
        
        if export_data:
            df_exp = pd.concat(export_data)
            st.download_button("💾 Descargar Datos (CSV)", df_exp.to_csv(index=False).encode('utf-8'), "simulacion.csv")

        if show_math and len(sel) == 1:
            render_math_explainer(df_mats[df_mats['name'] == sel[0]].iloc[0], modo, units, factor, unit_label, geom)
            
        st.divider()
        st.subheader("📊 Benchmarking")
        df_sub = df_mats[df_mats['name'].isin(sel)].copy()
        opts = {"yield_strength": f"Resistencia (Sy)", "elastic_modulus": f"Rigidez (E)", "density": "Densidad", "cost": "Costo"}
        opts = {k:v for k,v in opts.items() if k in df_sub.columns}
        if opts:
            prop = st.selectbox("Comparar:", list(opts.keys()), format_func=lambda x: opts[x])
            vals = df_sub[prop].values
            if is_imperial and prop in ["yield_strength", "elastic_modulus"]: vals = vals * factor
            fig_bar = px.bar(df_sub, x='name', y=vals, color='name', text_auto='.1f', title=opts[prop])
            fig_bar.update_layout(showlegend=False, template="plotly_white", yaxis_title=opts[prop])
            st.plotly_chart(fig_bar, use_container_width=True)

def render_tab_reports(df_mats):
    """Renderiza la Pestaña 3: Reportes y exportación LaTeX."""
    st.header("📑 Reportes")
    if df_mats.empty: return
    c1, c2 = st.columns(2)
    with c1: sel = st.multiselect("Materiales", df_mats['name'].unique())
    with c2: cols = st.multiselect("Propiedades", [c for c in df_mats.columns if c!='id'], default=['name','yield_strength'], format_func=lambda x: LABEL_MAP.get(x, x))
    if sel and cols:
        df = df_mats[df_mats['name'].isin(sel)][cols]
        st.dataframe(df, use_container_width=True)
        t1, t2 = st.tabs(["CSV", "LaTeX"])
        with t1: st.download_button("Descargar CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
        with t2: st.code(df.to_latex(index=False, float_format="%.2f"), language='latex')

def main():
    """Punto de entrada principal de la aplicación."""
    configure_page()
    try: df_raw = load_data()
    except: return
    df_mats, show_math = render_sidebar(df_raw)
    t1, t2, t3 = st.tabs(["📦 Base de Datos", "📈 Simulación", "📑 Reportes"])
    with t1: render_tab_management(df_mats)
    with t2: render_tab_simulation(df_mats, show_math)
    with t3: render_tab_reports(df_mats)

if __name__ == "__main__":
    main()
