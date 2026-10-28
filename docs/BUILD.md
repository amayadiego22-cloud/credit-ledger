# Compilar y probar Credit Ledger

Los comandos se ejecutan desde la raíz del repositorio. Se necesita Windows de 64 bits, PowerShell de 64 bits y Python 3 para construir el mod. No necesitas modificar la instalación del juego para ejecutar las pruebas con datos sintéticos.

## Pruebas de Python

```powershell
python -m unittest discover -s tests
python demo.py
```

## Construir el mod

Necesitas una instalación local de WoT 2.4.1.0 o 2.4.1.1 de NA, EU o ASIA. Cambia la ruta del ejemplo por la tuya:

```powershell
python build_release.py --game-root 'C:\Games\World_of_Tanks_NA' --output '.\dist'
```

El constructor lee `version.xml` y la DLL Python 2.7 del cliente local; no redistribuye esa DLL. Compila el código original y produce `dist/local.credit_ledger.0.22.11.wotmod`, el informe y el manifiesto de actualización local. No instala el mod automáticamente.

Con el juego cerrado, conserva una copia de tu `.wotmod` anterior y copia el nuevo con el nombre estable `local.credit_ledger.wotmod` dentro de `mods/<version-del-cliente>/`. Mantén una sola copia de este mod en esa carpeta. No borres `mods/configs/credit_ledger`.

El informe incluye observaciones históricas de la versión. Generar un paquete no vuelve a ejecutar ni confirma esas pruebas: ejecuta los conjuntos relevantes y valida la modificación en el cliente antes de distribuirla.

## Pruebas de interfaz

Se requiere Node.js y Playwright. Instala las dependencias y Chromium:

```powershell
npm install
npx playwright install chromium
npm run test:ui
```

Para usar un Chrome ya instalado, define `CREDIT_LEDGER_CHROME` con la ruta a su ejecutable. La suite genera capturas sintéticas y un perfil local dentro de `ui/qa/`; Git los ignora. Estas pruebas simulan el puente nativo y no sustituyen la comprobación dentro de Gameface.

## Construir el instalador

El instalador de la versión estable verifica el SHA-256 exacto del payload. Extrae el `.wotmod` de la distribución 0.22.11 y pásalo explícitamente:

```powershell
.\installer\build.ps1 -PayloadPath '.\dist\local.credit_ledger.0.22.11.wotmod' -OutputDirectory '.\dist\installer'
```

SHA-256 esperado del mod estable 0.22.11:

```text
f9e8923e0051a1d1a23091f1478e0431fb01218b8ce6c27830083c787e7afd27
```

El script usa el compilador C# de .NET Framework de Windows y ejecuta las pruebas del instalador en carpetas sintéticas. El programa no requiere un servicio ni un actualizador externo. El ZIP de distribución al jugador debe incluir el instalador.

Al publicar una versión modificada, revisa y actualiza de forma coordinada la versión y el hash en `installer/InstallerEngine.cs`, `installer/build.ps1` y la información de versión del formulario. Una recompilación puede cambiar el hash: no desactives la verificación para ocultar una discrepancia.

El directorio `updater/` del entorno de desarrollo original no se distribuye en este repositorio público ni en el ZIP del jugador: contiene herramientas locales de despliegue que no son necesarias para usar o compilar el mod.
