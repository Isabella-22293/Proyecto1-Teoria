# Proyecto1-Teoria
Descripción
El proyecto consiste en la implementación de los algoritmos básicos para construcción de autómatas
finitos a partir de expresiones regulares. El programa aceptará como entrada una expresión regular
r y una cadena w. A partir de la expresión regular r se transformará su notación infix a postfix y luego
se construirá un AFN; posteriormente, se transformará el AFN a AFD. Luego, este AFD deberá
minimizarse. Con dichos autómatas (AFN y AFD) se determinará si la cadena w pertenece o no a L(r).
Objetivos
• Generales
  o Implementación de algoritmos básicos de autómatas finitos y expresiones (lenguajes) regulares.
• Específicos
  o Implementación del Algoritmo de Shunting Yard de conversión infix a postfix.
  o Implementación del Algoritmo de Construcción de Thompson.
  o Implementación del Algoritmo de Construcción de Subconjuntos.
  o Implementación del Algoritmo para minimización de AFD’s.
  o Implementación de simulación de AFN.
  o Implementación de simulación de AFD.
Video
https://youtu.be/IGf81CqiVms

# Uso
1. Input: Se debe tener un archivo input.txt en el mismo directorio del script con las expresiones regulares que se quieren procesar.
2. Ejecutar el Script: Se ejecuta el archivo proyecto1.py para procesar las expresiones y generar las visualizaciones.
3. Ingresar Cadenas: Se debe ingresar una cadena para verificar si es aceptada por los autómatas generado.

# Requisitos
Python 3.x
Biblioteca Graphviz y su entorno de ejecución.
