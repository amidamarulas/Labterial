import os
import sys

# --- CONFIGURACIÓN DE RUTA ---
# conf.py está en docs/source/
# src/ está en ../../src/
sys.path.insert(0, os.path.abspath('../../src/labterial'))

# --- INFORMACIÓN DEL PROYECTO ---
project = 'Material Database'
copyright = '2025, Equipo de Ingenieria'
author = 'Dev Team'
release = '1.0'

# --- EXTENSIONES ---
extensions = [
    'sphinx.ext.autodoc',      # Generar doc de docstrings
    'sphinx.ext.napoleon',     # Soporte para estilo Google/Numpy
    'sphinx.ext.viewcode',     # Enlaces al código fuente
    'sphinx.ext.githubpages',
]

# --- MOCKING (LA SOLUCIÓN AL PROBLEMA) ---
# Simula estas librerías para que Sphinx no falle si no las encuentra
autodoc_mock_imports = [
    "pandas", 
    "numpy", 
    "scipy", 
    "plotly", 
    "streamlit", 
    "sqlite3"
]

# Configuración de Napoleon (para que se vea bonita la doc de Google Style)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# --- TEMA VISUAL ---
templates_path = ['_templates']
exclude_patterns = []
html_theme = 'sphinx_rtd_theme'
html_static_path = []
