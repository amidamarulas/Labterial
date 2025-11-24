Manual de Usuario
=================

Bienvenido a **Labterial**, tu laboratorio virtual de materiales.

Inicio Rápido (Instalación)
---------------------------

Para empezar a utilizar el software en cualquier computadora con Python instalado:

1. **Instalar el paquete:**
   Abre tu terminal (consola) y ejecuta el siguiente comando:

   .. code-block:: bash

      pip install labterial-sim

2. **Iniciar el programa:**
   Una vez instalado, simplemente escribe:

   .. code-block:: bash

      material-lab

   *Esto abrirá automáticamente una pestaña en tu navegador web con la aplicación.*

---

Funcionalidades Principales
---------------------------

1. **Simulación de Flexión (3 Puntos):**
   Ahora puedes simular vigas sometidas a flexión.
   * Selecciona *Flexión* en el menú de ensayo.
   * Ingresa las dimensiones geométricas: **Largo (L)**, **Ancho (b)** y **Espesor (d)**.
   * La gráfica mostrará automáticamente **Fuerza (N)** vs **Deflexión (mm)**.

2. **Modo Profesor (Pedagógico):**
   Activa la casilla "Mostrar Explicación Física" en la barra lateral.
   * Verás las ecuaciones exactas usadas (Hooke, Von Mises, Escuadría).
   * Se explicará el fenómeno físico (cizalladura, estricción, etc.) adaptado a cada ensayo.

3. **Benchmarking (Comparativa):**
   En la pestaña de simulación, selecciona múltiples materiales.
   * Verás las curvas superpuestas.
   * Abajo aparecerá un gráfico de barras comparando propiedades clave (Rigidez, Costo, Densidad).

4. **Sistema de Unidades:**
   Usa el selector "SI (MPa)" o "Imperial (ksi)" para cambiar todas las gráficas y tablas instantáneamente.

Flujo de Trabajo Típico
-----------------------

1. **Importar:** Ve a la pestaña *Base de Datos* y carga tu archivo CSV o usa los datos por defecto que ya vienen incluidos.
2. **Simular:** Ve a *Simulación*, elige tus probetas y analiza los resultados gráficos y numéricos.
3. **Exportar:**
   * Usa el icono de cámara en la gráfica para guardar una imagen PNG de alta calidad.
   * Usa el botón "Descargar Datos (CSV)" para obtener los puntos X-Y y procesarlos externamente.
   * Ve a la pestaña *Reportes* para generar código LaTeX para tu informe o paper.
