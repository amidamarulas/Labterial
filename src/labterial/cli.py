import sys
import os
from streamlit.web import cli as stcli

def main():
    """
    Función de entrada que busca donde está instalado app.py 
    y lo ejecuta con streamlit.
    """
    # Encontrar la ruta absoluta de app.py dentro del paquete instalado
    package_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(package_dir, "app.py")
    
    # Construir el comando simulado: "streamlit run /ruta/a/app.py"
    sys.argv = ["streamlit", "run", app_path]
    
    # Ejecutar
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
