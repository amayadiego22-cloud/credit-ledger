# Compilador local de Python 2.7

`compile_py27.ps1` y `Python27Compiler.cs` compilan únicamente fuentes propias con la DLL Python 2.7 de una instalación compatible de WoT. Se invocan automáticamente desde `build_release.py`.

Requiere Windows y PowerShell de 64 bits. El intérprete se carga en un proceso hijo breve, con `site`, el sitio del usuario y la escritura automática de bytecode desactivados. La compilación normal no ejecuta el módulo que recibe. Comprueba el encabezado Python 2.7 y el round-trip del payload marshal.

La DLL y los archivos nativos del juego no están incluidos. Las carpetas de trabajo `runtime_home` y `selftest with spaces` se generan localmente y se ignoran en Git.

Consulta [la guía de construcción](../docs/BUILD.md).
