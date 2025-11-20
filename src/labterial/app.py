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

# --- CONSTANTES Y DICCIONARIOS ---
MPA_TO_KSI = 0.1450377

# Diccionario para "Traducir" nombres de columnas a Español legible
LABEL_MAP = {
    "name": "Material",
    "category": "Categoría",
    "elastic_modulus": "Módulo de Young (E)",
    "yield_strength": "Límite Elástico (Sy)",
    "ultimate_strength": "Resistencia Máxima (Su)",
    "poisson_ratio": "Coeficiente Poisson (ν)"
}

# --- FUNCIONES AUXILIARES ---
def translate_df(df):
    """Renombra columnas del DataFrame para visualización."""
    return df.rename(columns=LABEL_MAP)

# --- FUNCIONES UI ---

def configure_page():
    st.set_page_config(page_title="Labterial", layout="wide", page_icon="🧪")
    st.title("🧪 Labterial: Suite de Ingeniería")

def load_data():
    return get_all_materials()

def render_sidebar(df_raw):
    st.sidebar.header("🔍 Filtros Globales")
    if isinstance(df_raw, pd.DataFrame) and 'category' in df_raw.columns:
        cats = df_raw['category'].unique().tolist()
        sel_cats = st.sidebar.multiselect("Filtrar por Categoría", cats, default=cats)
        if sel_cats:
            return df_raw[df_raw['category'].isin(sel_cats)]
    return df_raw

def render_tab_management(df_mats):
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📋 Inventario de Materiales")
        # Mostramos la tabla con nombres traducidos y bonitos
        st.dataframe(translate_df(df_mats), use_container_width=True, height=400)
    with c2:
        st.subheader("⚙️ Gestión")
        with st.expander("📥 Importar Materiales (CSV)", expanded=True):
            st.info("El archivo CSV debe usar los nombres internos (en inglés) para las columnas:")
            st.code("name, category, elastic_modulus, yield_strength")
            st.caption("Nota: 'elastic_modulus' es el Módulo de Young y 'yield_strength' es el Límite Elástico.")
            
            up = st.file_uploader("Seleccionar archivo", type=['csv'])
            if up and st.button("Procesar e Importar"):
                try:
                    df_new = pd.read_csv(up)
                    a, i, e = insert_from_dataframe(df_new)
                    if e: st.error(f"Error: {e}")
                    else: st.success(f"✅ Agregados: {a} | ⏭️ Omitidos (Duplicados): {i}"); st.rerun()
                except Exception as ex: st.error(f"Error crítico: {ex}")
        
        st.divider()
        try:
            from pathlib import Path
            pkg = __package__ if __package__ else 'labterial'
            db_path = Path.home() / f".{pkg}" / "materials.db"
            if not db_path.exists():
                db_path = Path(__file__).parent.parent.parent / 'data' / 'materials.db'
            if db_path.exists():
                with open(db_path, "rb") as fp:
                    st.download_button("💾 Descargar Respaldo (BD)", fp, "materials.db")
        except: pass

def render_tab_simulation(df_mats):
    if df_mats.empty: st.warning("⚠️ No hay datos disponibles con los filtros actuales."); return

    st.header("🔬 Simulación y Comparativa")
    
    col_ctrl, col_plot = st.columns([1, 3])

    with col_ctrl:
        st.subheader("1. Configuración")
        
        # Unidades
        units = st.radio("Sistema de Unidades", ["SI (MPa)", "Imperial (ksi)"], horizontal=True)
        is_imperial = "Imperial" in units
        unit_label = "ksi" if is_imperial else "MPa"
        factor = MPA_TO_KSI if is_imperial else 1.0

        st.divider()

        # Materiales
        mats_avail = df_mats['name'].unique()
        default_mat = [mats_avail[0]] if len(mats_avail) > 0 else None
        selected_mats = st.multiselect("2. Seleccionar Probetas", options=mats_avail, default=default_mat)
        
        st.divider()
        
        # Máquina
        modo = st.radio("3. Tipo de Ensayo", ["Tension", "Compresion", "Torsion"])
        
        lbl_limit = "Límite Deformación (%)" if modo != "Torsion" else "Ángulo Máx (rad)"
        max_v = 40.0 if modo != "Torsion" else 1.0
        def_v = 15.0 if modo != "Torsion" else 0.2
        
        slider_val = st.slider(lbl_limit, 0.1, max_v, def_v)
        machine_limit = slider_val / 100 if modo != "Torsion" else slider_val

    with col_plot:
        if not selected_mats:
            st.info("👈 Selecciona al menos un material para ver la simulación.")
        else:
            # --- GRAFICA 1: CURVAS ---
            fig = go.Figure()
            
            # Lista para la tabla resumen
            resumen_data = []

            for mat_name in selected_mats:
                dat = df_mats[df_mats['name'] == mat_name].iloc[0]
                props = dict(dat)
                props['category'] = dat.get('category', 'Metal')
                
                # Simulación
                df_sim = simular_ensayo(props, modo, max_strain_machine=machine_limit)
                
                # Conversión Unidades
                y_col_si = "Esfuerzo (MPa)"
                x_col = "Deformacion (%)" if modo != "Torsion" else "Deformacion (rad)"
                y_vals = df_sim[y_col_si] * factor
                
                fig.add_trace(go.Scatter(
                    x=df_sim[x_col], y=y_vals, mode='lines', name=mat_name, line=dict(width=3)
                ))
                
                # Datos para tabla (convirtiendo a la unidad elegida)
                resumen_data.append({
                    "Material": mat_name,
                    "Categoría": props['category'],
                    f"Módulo E ({unit_label})": dat['elastic_modulus'] * factor,
                    f"Límite Elástico Sy ({unit_label})": dat['yield_strength'] * factor,
                    f"Resistencia Máx Su ({unit_label})": dat['ultimate_strength'] * factor
                })

            title_map = {"Tension": "Tracción", "Compresion": "Compresión", "Torsion": "Torsión"}
            fig.update_layout(
                title=f"Curvas Esfuerzo-Deformación ({units}) - {title_map[modo]}",
                xaxis_title=x_col.replace("Deformacion", "Deformación"),
                yaxis_title=f"Esfuerzo ({unit_label})",
                hovermode="x unified",
                template="plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(range=[0, slider_val])
            
            # Añadir líneas de referencia (Solo si hay 1 material para no saturar)
            if len(selected_mats) == 1:
                dat_single = df_mats[df_mats['name'] == selected_mats[0]].iloc[0]
                val_sy = dat_single['yield_strength'] * factor
                val_su = dat_single['ultimate_strength'] * factor
                
                # Ajustes por tipo de ensayo
                signo = -1 if modo == "Compresion" else 1
                factor_shear = 0.577 if modo == "Torsion" else 1.0
                
                fig.add_hline(y=val_sy * factor_shear * signo, line_dash="dash", line_color="green", 
                              annotation_text=f"Límite Elástico (Sy)")
                
                if modo != "Compresion":
                    factor_su = 0.6 if modo == "Torsion" else 1.0
                    fig.add_hline(y=val_su * factor_su, line_dash="dot", line_color="red", 
                                  annotation_text=f"Resistencia Máxima (Su)")

            st.plotly_chart(fig, use_container_width=True)

            # --- SECCIÓN BARRAS ---
            st.divider()
            st.subheader("📊 Comparativa Numérica (Benchmarking)")
            
            df_subset = df_mats[df_mats['name'].isin(selected_mats)].copy()
            
            # Opciones traducidas para el selectbox
            opciones_prop = {
                "elastic_modulus": f"Rigidez - Módulo de Young ({unit_label})",
                "yield_strength": f"Resistencia a Fluencia - Sy ({unit_label})",
                "ultimate_strength": f"Resistencia a Rotura - Su ({unit_label})",
                "poisson_ratio": "Coeficiente de Poisson (-)"
            }
            
            c_sel, c_dummy = st.columns([1, 2])
            with c_sel:
                prop_key = st.selectbox("¿Qué propiedad quieres comparar?", list(opciones_prop.keys()), 
                                        format_func=lambda x: opciones_prop[x])
            
            y_vals_bar = df_subset[prop_key].values
            if prop_key != "poisson_ratio" and is_imperial:
                y_vals_bar = y_vals_bar * factor
                
            fig_bar = px.bar(
                df_subset, x='name', y=y_vals_bar, color='name',
                text_auto='.1f', title=f"Comparación: {opciones_prop[prop_key]}"
            )
            fig_bar.update_layout(
                yaxis_title=opciones_prop[prop_key], xaxis_title=None,
                showlegend=False, template="plotly_white"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            with st.expander("Ver Tabla de Datos Numéricos"):
                 st.dataframe(pd.DataFrame(resumen_data).style.format(precision=1), use_container_width=True)

def render_tab_reports(df_mats):
    st.header("📑 Generador de Reportes")
    if df_mats.empty: return

    c1, c2 = st.columns(2)
    with c1: sel_mats = st.multiselect("1. Materiales", df_mats['name'].unique(), default=df_mats['name'].iloc[:2].tolist() if len(df_mats)>0 else None)
    with c2: 
        # Usamos el diccionario LABEL_MAP para mostrar nombres bonitos en el selector
        # pero mantenemos las llaves originales para filtrar el DF
        cols_internas = [c for c in df_mats.columns if c != 'id']
        sel_cols = st.multiselect("2. Propiedades a Incluir", cols_internas, 
                                  default=['name', 'yield_strength'],
                                  format_func=lambda x: LABEL_MAP.get(x, x)) # Traducción visual

    if sel_mats and sel_cols:
        # Filtramos datos
        df_final = df_mats[df_mats['name'].isin(sel_mats)][sel_cols]
        
        # Creamos una copia visual traducida para mostrar
        df_visual = df_final.rename(columns=LABEL_MAP)
        
        st.subheader("Vista Previa")
        st.dataframe(df_visual, use_container_width=True)
        
        t_csv, t_tex = st.tabs(["📄 Exportar CSV", "📜 Exportar LaTeX"])
        with t_csv:
            st.caption("Descarga para Excel. Los encabezados se mantienen en inglés técnico para compatibilidad.")
            st.download_button("Descargar CSV", df_final.to_csv(index=False).encode('utf-8'), "reporte.csv", "text/csv")
        with t_tex:
            st.caption("Código LaTeX generado con nombres de columnas formateados.")
            try:
                # Para LaTeX usamos la versión con nombres bonitos
                latex = df_visual.to_latex(index=False, float_format="%.2f", caption="Tabla de Propiedades de Materiales", label="tab:mats")
                st.code(latex, language='latex')
            except: st.error("Error generando LaTeX")

def main():
    configure_page()
    try: df_raw = load_data()
    except Exception as e: st.error(f"Error BD: {e}"); return
    
    df_mats = render_sidebar(df_raw)
    
    tab1, tab2, tab3 = st.tabs(["📦 Base de Datos", "📈 Simulación", "📊 Reportes"])
    with tab1: render_tab_management(df_mats)
    with tab2: render_tab_simulation(df_mats)
    with tab3: render_tab_reports(df_mats)

if __name__ == "__main__":
    main()
