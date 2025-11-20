import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# --- SETUP DE IMPORTACIONES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .database_mgr import get_all_materials, insert_from_dataframe
    from .physics import simular_ensayo
except ImportError:
    from database_mgr import get_all_materials, insert_from_dataframe
    from physics import simular_ensayo

# --- FUNCIONES DE UI ---

def configure_page():
    st.set_page_config(page_title="Labterial", layout="wide", page_icon="🧪")
    st.title("🧪 Labterial: Suite de Ingeniería de Materiales")

def load_data():
    return get_all_materials()

def render_sidebar(df_raw):
    st.sidebar.header("Filtros de Base de Datos")
    if isinstance(df_raw, pd.DataFrame) and 'category' in df_raw.columns:
        cats = df_raw['category'].unique().tolist()
        sel_cats = st.sidebar.multiselect("Categoría", cats, default=cats)
        if sel_cats:
            return df_raw[df_raw['category'].isin(sel_cats)]
    return df_raw

def render_tab_management(df_mats):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Inventario de Materiales")
        st.dataframe(df_mats, use_container_width=True, height=400)
    with c2:
        st.subheader("Gestión")
        with st.expander("📥 Importar Materiales (CSV)", expanded=True):
            st.markdown("""
            Sube un archivo con columnas:
            `name`, `category`, `elastic_modulus`, `yield_strength`
            """)
            up = st.file_uploader("Seleccionar archivo", type=['csv'])
            if up and st.button("Procesar e Importar"):
                try:
                    df_new = pd.read_csv(up)
                    a, i, e = insert_from_dataframe(df_new)
                    if e: st.error(f"Error: {e}")
                    else: st.success(f"✅ Agregados: {a} | ⏭️ Omitidos: {i}"); st.rerun()
                except Exception as ex:
                    st.error(f"Error de lectura: {ex}")
        
        st.divider()
        
        # Backup Lógica
        try:
            from pathlib import Path
            pkg = __package__ if __package__ else 'labterial'
            db_path = Path.home() / f".{pkg}" / "materials.db"
            if not db_path.exists():
                db_path = Path(__file__).parent.parent.parent / 'data' / 'materials.db'
            
            if db_path.exists():
                with open(db_path, "rb") as fp:
                    st.download_button("💾 Descargar Copia de Seguridad (DB)", fp, "materials.db")
        except: pass

def render_tab_simulation(df_mats):
    """
    Versión Mejorada: Permite comparación de múltiples materiales.
    """
    if df_mats.empty: st.warning("No hay datos disponibles."); return

    st.header("🔬 Simulación Multi-Material")
    
    # Layout: Controles a la izquierda, Gráfica grande a la derecha
    col_ctrl, col_plot = st.columns([1, 3])

    with col_ctrl:
        st.subheader("Configuración del Ensayo")
        
        # 1. Selección Múltiple
        mats_avail = df_mats['name'].unique()
        # Por defecto seleccionamos el primero
        default_mat = [mats_avail[0]] if len(mats_avail) > 0 else None
        
        selected_mats = st.multiselect("Seleccionar Probetas (Comparar)", 
                                       options=mats_avail, 
                                       default=default_mat)
        
        st.divider()
        
        # 2. Parámetros de Máquina
        modo = st.radio("Tipo de Carga", ["Tension", "Compresion", "Torsion"])
        
        lbl_limit = "Límite de Deformación (%)" if modo != "Torsion" else "Ángulo Máximo (rad)"
        max_val_slider = 40.0 if modo != "Torsion" else 1.0
        default_val = 15.0 if modo != "Torsion" else 0.2
        
        slider_val = st.slider(lbl_limit, 0.1, max_val_slider, default_val)
        machine_limit = slider_val / 100 if modo != "Torsion" else slider_val

    with col_plot:
        if not selected_mats:
            st.info("👈 Selecciona al menos un material para comenzar la simulación.")
        else:
            # Inicializar figura vacía
            fig = go.Figure()
            
            # Iterar sobre cada material seleccionado y añadir su traza
            for mat_name in selected_mats:
                # Obtener datos
                dat = df_mats[df_mats['name'] == mat_name].iloc[0]
                props = dict(dat)
                props['category'] = dat.get('category', 'Metal')
                
                # Simular
                df_sim = simular_ensayo(props, modo, max_strain_machine=machine_limit)
                
                # Definir ejes
                y_col = "Esfuerzo (MPa)"
                x_col = "Deformacion (%)" if modo != "Torsion" else "Deformacion (rad)"
                
                # Añadir curva a la figura
                fig.add_trace(go.Scatter(
                    x=df_sim[x_col],
                    y=df_sim[y_col],
                    mode='lines',
                    name=mat_name,
                    line=dict(width=3)
                ))

            # Configurar Diseño de la Gráfica
            title_map = {"Tension": "Tracción", "Compresion": "Compresión", "Torsion": "Torsión"}
            
            fig.update_layout(
                title=f"Ensayo Comparativo de {title_map[modo]}",
                xaxis_title=x_col,
                yaxis_title="Esfuerzo (MPa)",
                hovermode="x unified", # Tooltip comparativo genial
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                template="plotly_white"
            )
            
            # Forzar rango del eje X (Zoom)
            fig.update_xaxes(range=[0, slider_val])
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla resumen rápida debajo de la gráfica
            if len(selected_mats) > 1:
                with st.expander("Ver Comparativa de Propiedades"):
                    st.dataframe(
                        df_mats[df_mats['name'].isin(selected_mats)][
                            ['name', 'category', 'elastic_modulus', 'yield_strength', 'ultimate_strength']
                        ],
                        use_container_width=True
                    )

def render_tab_reports(df_mats):
    st.header("📑 Generador de Reportes")
    if df_mats.empty: return

    c1, c2 = st.columns(2)
    with c1: 
        sel_mats = st.multiselect("Filtrar Materiales", df_mats['name'].unique(), 
                                  default=df_mats['name'].iloc[:3].tolist() if len(df_mats)>0 else None)
    with c2: 
        cols = [c for c in df_mats.columns if c != 'id']
        sel_cols = st.multiselect("Columnas a exportar", cols, 
                                  default=['name', 'category', 'yield_strength', 'elastic_modulus'])

    st.divider()
    
    if sel_mats and sel_cols:
        df_final = df_mats[df_mats['name'].isin(sel_mats)][sel_cols]
        st.dataframe(df_final, use_container_width=True)
        
        t_csv, t_tex = st.tabs(["📄 Exportar CSV", "📜 Exportar LaTeX"])
        
        with t_csv:
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar CSV", csv, "reporte_materiales.csv", "text/csv")
            
        with t_tex:
            st.caption("Código para copiar en Overleaf / LaTeX:")
            try:
                latex = df_final.to_latex(index=False, float_format="%.2f", caption="Tabla de Materiales", label="tab:mats")
                st.code(latex, language='latex')
            except: st.error("Error generando LaTeX")

def main():
    configure_page()
    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"Error crítico de base de datos: {e}")
        return
    
    df_mats = render_sidebar(df_raw)
    
    tab1, tab2, tab3 = st.tabs(["📦 Base de Datos", "📈 Simulación", "📊 Reportes"])
    
    with tab1: render_tab_management(df_mats)
    with tab2: render_tab_simulation(df_mats)
    with tab3: render_tab_reports(df_mats)

if __name__ == "__main__":
    main()
