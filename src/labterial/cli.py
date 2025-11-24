import sys
import os
from streamlit.web import cli as stcli

def main():
    """
    Punto de entrada principal de la aplicación para la línea de comandos.

    Esta función se ejecuta cuando el usuario escribe ``material-lab`` en su terminal
    después de instalar el paquete.

    **Funcionamiento Técnico:**

    Como Streamlit no es una librería estándar de Python que se ejecuta simplemente importándola,
    este script actúa como un "Lanzador" (Launcher):

    1.  **Localización:** Encuentra dinámicamente la ruta absoluta donde se instaló
        el paquete ``labterial`` en el sistema operativo del usuario.
    2.  **Enrutamiento:** Construye la ruta hacia el archivo ``app.py`` interno.
    3.  **Inyección de Argumentos:** Manipula ``sys.argv`` para simular que el usuario
        escribió manualmente: ``streamlit run /ruta/de/instalacion/app.py``.
    4.  **Delegación:** Pasa el control al ejecutable interno de Streamlit (``stcli.main()``).

    Note:
        Este método permite distribuir aplicaciones de Streamlit como paquetes de PyPI
        estándar sin obligar al usuario a conocer la ubicación de los archivos.
    """
    # 1. Encontrar el directorio donde vive este archivo (dentro de site-packages)
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Apuntar al archivo de la GUI
    app_path = os.path.join(package_dir, "app.py")
    
    # 3. Construir el comando simulado
    # sys.argv[0] es el nombre del programa, los siguientes son argumentos
    sys.argv = ["streamlit", "run", app_path]
    
    # 4. Ejecutar Streamlit
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
