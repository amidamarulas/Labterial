import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

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
    "name": "Material",
    "category": "Categoría",
    "elastic_modulus": "Módulo de Young (E)",
    "yield_strength": "Límite Elástico (Sy)",
    "ultimate_strength": "Resistencia Máxima (Su)",
    "poisson_ratio": "Coeficiente Poisson (ν)"
}

def translate_df(df):
    return df.rename(columns=LABEL_MAP)

def configure_page():
    st.set_page_config(page_title="Labterial Edu", layout="wide", page_icon="🎓")
    st.title("🎓 Labterial: Laboratorio Educativo")

def load_data():
    return get_all_materials()

def render_sidebar(df_raw):
    st.sidebar.header("🔍 Filtros")
    
    # --- SECCIÓN PEDAGÓGICA EN SIDEBAR ---
    st.sidebar.divider()
    st.sidebar.subheader("👨‍🏫 Modo Profesor")
    show_math = st.sidebar.checkbox("Mostrar Ecuaciones", value=True, help="Muestra la matemática detrás de la curva.")
    
    st.sidebar.divider()
    if isinstance(df_raw, pd.DataFrame) and 'category' in df_raw.columns:
        cats = df_raw['category'].unique().tolist()
        sel_cats = st.sidebar.multiselect("Categoría", cats, default=cats)
        if sel_cats:
            return df_raw[df_raw['category'].isin(sel_cats)], show_math
    return df_raw, show_math

def render_tab_management(df_mats):
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

def render_math_explainer(dat, modo, units, factor, unit_label):
    """
    Renderiza un bloque educativo con fórmulas LaTeX dinámicas.
    """
    st.info("💡 **Explicación Matemática del Comportamiento**")
    
    # Valores numéricos
    E = dat['elastic_modulus'] * factor
    Sy = dat['yield_strength'] * factor
    Su = dat['ultimate_strength'] * factor
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 1. Zona Elástica (Ley de Hooke)")
        st.markdown("Mientras el esfuerzo sea menor a $S_y$, el material actúa como un resorte:")
        st.latex(r"\sigma = E \cdot \epsilon")
        st.markdown(f"Donde **E** es la pendiente de la recta.")
        st.markdown(f"**Para este material:** $E = {E:.0f} \\text{{ {unit_label} }}$")
        
    with c2:
        st.markdown("#### 2. Zona Plástica (Endurecimiento)")
        st.markdown("Al superar $S_y$, usamos la Ley de Potencia (Modelo de Hollomon):")
        st.latex(r"\sigma = S_y + K \cdot (\epsilon_{plastica})^n")
        st.markdown(f"El material fluye desde **Sy** ({Sy:.0f}) hasta **Su** ({Su:.0f}).")

def render_tab_simulation(df_mats, show_math):
    if df_mats.empty: st.warning("Sin datos."); return

    st.header("🔬 Laboratorio Virtual")
    
    col_ctrl, col_plot = st.columns([1, 3])

    with col_ctrl:
        st.subheader("Configuración")
        units = st.radio("Unidades", ["SI (MPa)", "Imperial (ksi)"], horizontal=True)
        is_imperial = "Imperial" in units
        unit_label = "ksi" if is_imperial else "MPa"
        factor = MPA_TO_KSI if is_imperial else 1.0
        
        st.divider()
        mats_avail = df_mats['name'].unique()
        default_mat = [mats_avail[0]] if len(mats_avail) > 0 else None
        selected_mats = st.multiselect("Probetas", options=mats_avail, default=default_mat)
        
        st.divider()
        modo = st.radio("Ensayo", ["Tension", "Compresion", "Torsion"])
        lbl = "Límite (%)" if modo!="Torsion" else "Ángulo (rad)"
        max_v = 40.0 if modo!="Torsion" else 1.0
        slider_val = st.slider(lbl, 0.1, max_v, 15.0)
        limit = slider_val/100 if modo!="Torsion" else slider_val

    with col_plot:
        if not selected_mats:
            st.info("Selecciona material.")
        else:
            fig = go.Figure()
            for mat in selected_mats:
                dat = df_mats[df_mats['name'] == mat].iloc[0]
                props = dict(dat)
                props['category'] = dat.get('category', 'Metal')
                df_sim = simular_ensayo(props, modo, max_strain_machine=limit)
                
                y_vals = df_sim["Esfuerzo (MPa)"] * factor
                x_col = "Deformacion (%)" if modo!="Torsion" else "Deformacion (rad)"
                
                fig.add_trace(go.Scatter(x=df_sim[x_col], y=y_vals, mode='lines', name=mat, line=dict(width=3)))

            title_map = {"Tension": "Tracción", "Compresion": "Compresión", "Torsion": "Torsión"}
            fig.update_layout(
                title=f"Curvas ({units}) - {title_map[modo]}",
                xaxis_title=x_col.replace("Deformacion", "Deformación"),
                yaxis_title=f"Esfuerzo ({unit_label})",
                hovermode="x unified", template="plotly_white",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            fig.update_xaxes(range=[0, slider_val])
            st.plotly_chart(fig, use_container_width=True)
            
            # --- COMPONENTE PEDAGÓGICO ---
            if show_math and len(selected_mats) == 1:
                # Solo mostramos la explicación matemática si hay 1 solo material seleccionado
                # para no confundir con múltiples números
                dat_single = df_mats[df_mats['name'] == selected_mats[0]].iloc[0]
                render_math_explainer(dat_single, modo, units, factor, unit_label)
            elif show_math and len(selected_mats) > 1:
                st.caption("ℹ️ Selecciona un único material para ver el desglose matemático detallado.")

            st.divider()
            st.subheader("📊 Benchmarking")
            df_sub = df_mats[df_mats['name'].isin(selected_mats)].copy()
            
            opts = {
                "yield_strength": f"Resistencia (Sy) [{unit_label}]",
                "elastic_modulus": f"Rigidez (E) [{unit_label}]"
            }
            prop = st.selectbox("Comparar:", list(opts.keys()), format_func=lambda x: opts[x])
            y_bar = df_sub[prop].values * (factor if is_imperial else 1.0)
            
            fig_bar = px.bar(df_sub, x='name', y=y_bar, color='name', text_auto='.1f', title=opts[prop])
            fig_bar.update_layout(showlegend=False, template="plotly_white", yaxis_title=opts[prop])
            st.plotly_chart(fig_bar, use_container_width=True)

def render_tab_reports(df_mats):
    st.header("📑 Reportes")
    if df_mats.empty: return
    c1, c2 = st.columns(2)
    with c1: sel = st.multiselect("Materiales", df_mats['name'].unique())
    with c2: cols = st.multiselect("Propiedades", [c for c in df_mats.columns if c!='id'], default=['name','yield_strength'])
    if sel and cols:
        df = df_mats[df_mats['name'].isin(sel)][cols]
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("CSV", csv, "data.csv", "text/csv")

def main():
    configure_page()
    try: df_raw = load_data()
    except: return
    
    # Desempaquetar tupla porque render_sidebar ahora devuelve 2 cosas
    df_mats, show_math = render_sidebar(df_raw)
    
    tab1, tab2, tab3 = st.tabs(["Base de Datos", "Simulación", "Reportes"])
    with tab1: render_tab_management(df_mats)
    # Pasamos la variable show_math a la simulación
    with tab2: render_tab_simulation(df_mats, show_math)
    with tab3: render_tab_reports(df_mats)

if __name__ == "__main__":
    main()
