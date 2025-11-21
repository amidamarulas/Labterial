Manual de Usuario
=================

Bienvenido a **Labterial v1.2**. Esta guía explica cómo utilizar las herramientas avanzadas de simulación.

Nuevas Funcionalidades
----------------------

1. **Simulación de Flexión (3 Puntos):**
   Ahora puedes simular vigas sometidas a flexión.
   * Selecciona *Flexión* en el menú de ensayo.
   * Ingresa las dimensiones geométricas: **Largo (L)**, **Ancho (b)** y **Espesor (d)**.
   * La gráfica mostrará automáticamente **Fuerza (N)** vs **Deflexión (mm)**.

2. **Modo Profesor (Pedagógico):**
   Activa la casilla "Mostrar Explicación Física" en la barra lateral.
   * Verás las ecuaciones exactas usadas (Hooke, Von Mises, Escuadría).
   * Se explicará el fenómeno físico (cizalladura, estricción, etc.).

3. **Benchmarking (Comparativa):**
   En la pestaña de simulación, selecciona múltiples materiales.
   * Verás las curvas superpuestas.
   * Abajo aparecerá un gráfico de barras comparando propiedades clave (Rigidez, Costo, Densidad).

4. **Sistema de Unidades:**
   Usa el selector "SI (MPa)" o "Imperial (ksi)" para cambiar todas las gráficas y tablas instantáneamente.

Flujo de Trabajo Básico
-----------------------

1. **Importar:** Ve a la pestaña *Base de Datos* y carga tu archivo CSV o usa los datos por defecto.
2. **Simular:** Ve a *Simulación*, elige tus probetas y analiza los resultados.
3. **Exportar:**
   * Usa el icono de cámara en la gráfica para guardar una imagen PNG de alta calidad.
   * Usa el botón "Descargar Datos (CSV)" para obtener los puntos X-Y y procesarlos externamente.
   * Ve a la pestaña *Reportes* para generar código LaTeX para tu informe.
