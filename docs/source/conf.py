import os
import sys

# --- RUTA CRÍTICA ---
# Apuntamos a src/labterial para que Sphinx pueda hacer 'import app' directamente
sys.path.insert(0, os.path.abspath('../../src/labterial'))
# También apuntamos a src por si acaso
sys.path.insert(0, os.path.abspath('../../src'))

project = 'Material Database'
copyright = '2025, Labterial Team'
author = 'Dev'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

# Mocking: Simulamos estas librerías para que Sphinx no falle si no están instaladas
autodoc_mock_imports = [
    "pandas", "numpy", "scipy", "plotly", "streamlit", "sqlite3"
]

# Configuración Napoleon (Google Style)
napoleon_google_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

html_theme = 'sphinx_rtd_theme'
