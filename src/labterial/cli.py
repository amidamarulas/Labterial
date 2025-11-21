import sys
import os
from streamlit.web import cli as stcli

def main():
    """Punto de entrada para el comando de consola."""
    package_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(package_dir, "app.py")
    
    # Inyectamos el comando como si el usuario lo hubiera escrito
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
