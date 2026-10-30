<p align="center">
  <img src="docs/cover-0.22.11-302x170.png" alt="Credit Ledger — Contabilidad de créditos" width="302" height="170">
</p>

# Credit Ledger / Contabilidad de créditos

Mod para **World of Tanks PC de Wargaming** que muestra cuánto ganas o pierdes en créditos, tus gastos y el progreso de una meta personal.

**Versión estable: 0.22.14 · Español / English**

[English guide](README-en.md) · [Guía de uso](LEEME.md) · [Compilar el proyecto](docs/BUILD.md) · [WGMods](https://wgmods.net/8056/)

## Así se ve

![Widget del garaje y círculo de progreso de Credit Ledger](docs/01-widget-circle-0.22.11.png)

Elige entre el panel ampliado y el círculo de progreso. El control para moverlo aparece al pasar el cursor.

<details>
<summary><strong>Ver las capturas: detalles, filtros e historial</strong></summary>

### Detalles en español

![Meta de créditos y detalles en español](docs/02-details-es-0.22.11.png)

### Detalles en inglés

![Meta de créditos y detalles en inglés](docs/03-details-en-0.22.11.png)

### Desglose y filtros de batallas

![Filtros por modo y vehículo, imágenes de tanques y desglose de ingresos y gastos](docs/04-battle-filters-0.22.11.png)

### Historial por día

![Historial por día con partidas y filtros](docs/05-daily-history-0.22.11.png)

</details>

*Las mismas vistas de presentación de 0.22.11 publicadas en WGMods; los importes son datos de demostración.*

## Funciones

- Widget del garaje con un círculo de progreso que puedes mover y expandir; permanece visible durante la búsqueda de partida en las colas nativas compatibles y se oculta al entrar a batalla o abrir otras páginas.
- Meta editable de 100.000 créditos adicionales para cuentas nuevas y cada nueva jornada o reinicio del historial. Escribir 0 la desactiva durante esa jornada; actualizar el importe conserva el avance.
- Desglose de ingresos, reparaciones, munición, consumibles y reservas personales y del clan, sin contar las bonificaciones dos veces.
- Historial filtrable por modo de juego y vehículo, con imagen y nivel nativos del tanque.
- Archivo por día, reinicio automático según el día del servidor y botón de reinicio manual.
- Español e inglés al instante, y una celebración breve al completar la meta.
- Instalador para Windows incluido en el ZIP, con barra de progreso y botón «Finalizar». Detecta y retira copias anteriores de Credit Ledger; limpia las carpetas de clientes antiguos solo si quedan vacías.

## Novedades de 0.22.14

- Búsqueda de partida: reconoce las colas nativas comunes, Fortalezas, eventos Halloween/Torre Oscura y Last Stand, Topografía y torneos de Cazador de Acero sin cargar modos inactivos. La comprobación visual en cada modo disponible sigue pendiente.
- Meta predeterminada: 100.000 créditos adicionales para cada nueva cuenta o período; conserva metas positivas y reconoce el 0 elegido expresamente por el usuario.
- Instalador **0.22.14.3**: progreso por etapas, 100 % solo al completar, «Finalizar» para cerrar y reintento si falla. Elimina copias antiguas y deshabilitadas identificadas como Credit Ledger, incluidas las de clientes anteriores, con respaldo y restauración si hay un error.
- Verificación: **450 pruebas de Python, 44 del motor del instalador y 13 del formulario**. Las pruebas automatizadas y los contratos nativos no equivalen a una prueba conectada en cada modo y región.

## Compatibilidad de esta versión

WoT **2.4.1.0 y 2.4.1.1**, regiones **NA, EU y ASIA**. La compatibilidad con otras versiones debe revisarse antes de instalar. Lesta/Mir Tankov, Blitz y el cliente de prueba común no están cubiertos.

Las pruebas conectadas anteriores de contabilidad de EU (+49.640) y ASIA (+64.197) se realizaron en **2.4.1.0**. En 2.4.1.1 el usuario confirmó las correcciones del garaje y el círculo; esto no equivale a una nueva prueba conectada en las tres regiones.

## Descargar e instalar

Descarga el ZIP de la versión desde [Releases](https://github.com/amayadiego22-cloud/credit-ledger/releases) o desde [la ficha de WGMods](https://wgmods.net/8056/) cuando esa versión esté disponible allí. La publicación en GitHub es independiente de la revisión de WGMods.

1. Cierra World of Tanks por completo.
2. Extrae el ZIP en una carpeta.
3. Ejecuta `CreditLedger-Setup-0.22.14.exe`, selecciona tu instalación y pulsa «Instalar / Actualizar».
4. Espera el 100 % y pulsa «Finalizar» para cerrar el instalador.
5. Abre el juego y entra al garaje.

El instalador utiliza la carpeta de la versión activa. Retira los paquetes de Credit Ledger de las versiones de cliente anteriores y borra esas carpetas únicamente si quedan vacías; conserva los demás mods, tus datos y las carpetas de versiones futuras. Para la alternativa manual, copia solo el `.wotmod` de la versión que usa tu juego.

El ZIP de GitHub **Code → Download ZIP** contiene el código fuente; el ZIP de **Releases** contiene el mod listo para instalar, con su instalador dentro.

## Organización del código

| Carpeta | Contenido |
| --- | --- |
| `capture/` | Eventos del cliente, resultados, saldo, metas, filtros e historial |
| `core/` | Cálculos y registro de contabilidad |
| `game/` | Punto de entrada que carga WoT |
| `ui/` | Interfaz HTML, CSS y JavaScript para Gameface |
| `resources/` | Manifiesto de la vista |
| `installer/` | Código C# del instalador y sus pruebas |
| `build_tools/` | Compilador local compatible con Python 2.7 |
| `tests/` | Pruebas con datos sintéticos |

El juego usa Python 2.7. Las herramientas de construcción y las pruebas se ejecutan con Python 3. No se incluyen archivos del cliente, DLL de Wargaming, imágenes nativas por separado, capturas de cuentas ni credenciales.

## Probar el código

Con Python 3 instalado, desde la raíz del proyecto:

```powershell
python -m unittest discover -s tests
python demo.py
```

La demostración utiliza datos ficticios y no se conecta al juego. Consulta [la guía de construcción](docs/BUILD.md) para generar un `.wotmod`, probar la interfaz y compilar el instalador.

## Datos locales

El mod guarda sus datos en la instalación del juego, bajo `mods/configs/credit_ledger`, separados por región y cuenta. Esos archivos no forman parte de este repositorio. No adjuntes tus capturas o registros completos a una incidencia sin revisarlos primero.

Proyecto de **ROLO / amayadiego22-cloud**. World of Tanks y sus recursos pertenecen a sus respectivos titulares.
