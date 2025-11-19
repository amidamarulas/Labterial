Guía de Usuario
===============

Bienvenido a **Labterial**, tu laboratorio virtual de materiales.

Inicio Rápido
-------------

1. **Abrir el programa:**
   Ejecuta en tu terminal:
   
   .. code-block:: bash
   
      material-lab

2. **Pestaña 1: Base de Datos**
   Aquí puedes ver los materiales disponibles.
   
   * **Importar Datos:** Usa el panel derecho para subir archivos .
   * **Formato CSV:** El archivo debe tener las columnas: name, category, elastic_modulus, yield_strength.
   * **Backup:** Usa el botón "Backup BD" para descargar tus datos.

3. **Pestaña 2: Simulación**
   * Selecciona una **Probeta** del menú desplegable.
   * Elige el tipo de ensayo (Tensión, Compresión, Torsión).
   * Usa el **Slider** para definir hasta dónde llega la máquina.
   * *Nota:* Si el material es frágil, la gráfica se cortará antes de llegar al límite del slider.

4. **Pestaña 3: Reportes**
   * Filtra los materiales que te interesan.
   * Descarga la tabla en **Excel (CSV)** o copia el código **LaTeX** para tu informe.

Solución de Problemas
---------------------
Si la aplicación no abre, asegúrate de haber instalado las dependencias con:

.. code-block:: bash

   pip install .
