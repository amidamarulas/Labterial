import os
import sys

# Apuntar a la raíz del código fuente y al paquete específico
sys.path.insert(0, os.path.abspath('../../src'))
sys.path.insert(0, os.path.abspath('../../src/labterial'))

project = 'Labterial'
copyright = '2025, Equipo de Ingeniería'
author = 'Dev Team'
release = '1.2' # Versión actualizada

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

# Mocking crítico para evitar errores de importación en ReadTheDocs/Local
autodoc_mock_imports = [
    "pandas", "numpy", "scipy", "plotly", "streamlit", "sqlite3"
]

# Configuración Napoleon
napoleon_google_docstring = True
html_theme = 'sphinx_rtd_theme'
