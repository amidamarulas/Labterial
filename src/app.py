import streamlit as st
import pandas as pd
import plotly.express as px
import os

try:
    from database_mgr import get_all_materials, insert_from_dataframe
    from physics import simular_ensayo
except ImportError:
    from src.database_mgr import get_all_materials, insert_from_dataframe
    from src.physics import simular_ensayo

st.set_page_config(page_title="Lab Materiales", layout="wide")
st.title("🏗️ Simulador Universal de Ensayos")

# SIDEBAR
df_raw = get_all_materials()
cats = df_raw['category'].unique().tolist()
sel_cats = st.sidebar.multiselect("Filtros", cats, default=cats)
df_mats = df_raw[df_raw['category'].isin(sel_cats)] if sel_cats else df_raw

tab1, tab2, tab3 = st.tabs(["Base de Datos", "Simulación", "Reportes"])

with tab1:
    c1, c2 = st.columns([3,1])
    with c1: st.dataframe(df_mats, use_container_width=True)
    with c2:
        with st.expander("Importar CSV"):
            up = st.file_uploader("Archivo", type=['csv'])
            if up and st.button("Cargar"):
                a, i, e = insert_from_dataframe(pd.read_csv(up))
                if e: st.error(e)
                else: st.success(f"Ok: {a}"); st.rerun()
        
        # Botón de descarga de DB (Backup)
        st.divider()
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'materials.db')
        try:
            with open(db_path, "rb") as fp:
                st.download_button("💾 Backup BD", fp, "materials.db")
        except: pass

with tab2:
    st.header("Ensayo Mecánico")
    if df_mats.empty: st.stop()
    
    conf, graf = st.columns([1, 3])
    
    with conf:
        st.subheader("Máquina")
        mat = st.selectbox("Probeta", df_mats['name'].unique())
        modo = st.radio("Modo", ["Tension", "Compresion", "Torsion"])
        
        lbl = "Límite de Carrera (%)" if modo != "Torsion" else "Límite Angular (rad)"
        max_v = 40.0 if modo != "Torsion" else 0.8
        slider_val = st.slider(lbl, 0.1, max_v, 20.0)
        
        machine_limit = slider_val / 100 if modo != "Torsion" else slider_val
        
        dat = df_mats[df_mats['name'] == mat].iloc[0]
        st.divider()
        st.caption(f"Material: {dat['category']}")
        st.write(f"**Sy:** {dat['yield_strength']} MPa")

    with graf:
        props = dict(dat)
        props['category'] = dat['category'] 
        
        df_sim = simular_ensayo(props, modo, max_strain_machine=machine_limit)
        
        y_col = "Esfuerzo (MPa)"
        x_col = "Deformacion (%)" if modo != "Torsion" else "Deformacion (rad)"
        
        fig = px.line(df_sim, x=x_col, y=y_col, title=f"Curva {modo}: {mat}", markers=True)
        
        # Forzar zoom correcto
        if modo != "Torsion":
            fig.update_xaxes(range=[0, slider_val]) 
        else:
            fig.update_xaxes(range=[0, slider_val])

        clr = "royalblue" if modo == "Tension" else ("firebrick" if modo == "Compresion" else "orange")
        fig.update_traces(line=dict(color=clr, width=3), connectgaps=False)
        
        signo = -1 if modo == "Compresion" else 1
        f_sy = 0.577 if modo == "Torsion" else 1.0
        
        fig.add_hline(y=dat['yield_strength']*f_sy*signo, line_dash="dash", line_color="green", annotation_text="Sy")
        
        if modo != "Compresion":
             f_su = 0.6 if modo == "Torsion" else 1.0
             fig.add_hline(y=dat['ultimate_strength']*f_su, line_dash="dot", line_color="red", annotation_text="Su")

        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not df_mats.empty:
        s = st.multiselect("Materiales", df_mats['name'].unique())
        if s: st.dataframe(df_mats[df_mats['name'].isin(s)])
