# Contabilidad de créditos — 0.22.14

La versión **0.22.14** amplía la visibilidad durante la búsqueda a las colas nativas de los otros modos: eventos Halloween/Torre Oscura y Last Stand, Topografía y torneos de Cazador de Acero, además de la cola común usada por Aleatorias y Asedio y la de Fortalezas. Reconoce sus clases y variantes sin cargar modos inactivos. Conserva la posición, el estado del widget y la meta al cancelar. Se oculta al entrar a batalla y en las demás páginas del garaje. La comprobación visual en cada modo disponible está pendiente.

La versión **0.22.13** inicia una meta editable de **100.000 créditos adicionales** desde el saldo sincronizado, tanto en una cuenta nueva como al reiniciar el historial o comenzar otra jornada del servidor. Las metas positivas guardadas y su avance se conservan. Corrige los ceros vacíos que dejaron reinicios anteriores; escribir 0 expresamente sigue desactivando la meta durante esa jornada. La búsqueda de partida conserva la visibilidad del widget. La comprobación visual de esta corrección en el juego está pendiente.

La versión **0.22.12** mantiene el widget visible durante la búsqueda de partida, incluidas las colas nativas de batalla y de Fortalezas. Cancelar la búsqueda conserva el estado, la posición, la meta y el historial. Se oculta al entrar en batalla y sigue oculto en el árbol tecnológico, la hoja de servicio y las demás pantallas. La comprobación visual de esta corrección dentro del juego está pendiente.

Toda la superficie del círculo se resalta al pasar el ratón, incluido su contorno. Pulsa cualquier parte del círculo para abrir el resumen y usa «Mover» para arrastrarlo. El resaltado no cambia el porcentaje real de tu meta.

La versión 0.22.11 incorpora el círculo aprobado: aro verde más grueso, porcentaje y cantidad de la meta en el centro, con la etiqueta «Meta». El círculo mide 112 × 112 px; su ventana transparente incluye espacio para el botón «Mover», que aparece al pasar el ratón o navegar con teclado y se mantiene visible al arrastrar. Pulsa el centro para abrir el resumen. La primera meta de una cuenta nueva es de **100.000 créditos adicionales**, desde su saldo sincronizado. Las metas ya guardadas, incluido el valor 0, se conservan. A partir de 0.22.13 los reinicios de historial comienzan una meta editable de 100.000 créditos. Las barras de progreso también son más gruesas y verdes. El usuario confirmó en el juego el círculo y su resaltado completo en 0.22.11. Esta versión se distribuye sin etiqueta beta e incluye el instalador dentro del ZIP.

La versión 0.22.8 unifica el mod y el instalador con una cuadrícula de 8 píxeles: espacios de 8, 16, 24 y 32 px, tarjetas alineadas, controles más cómodos y un widget más despejado. Conserva las metas, el historial y los cálculos. Pasaron 432 pruebas de Python, 117 comprobaciones de la interfaz y 32 del instalador. La comprobación posterior del círculo de 0.22.11 está confirmada por el usuario; las confirmaciones conectadas que se describen a continuación corresponden a versiones anteriores.

Para **World of Tanks PC de Wargaming: América (NA), Europa (EU) y Asia (ASIA), clientes 2.4.1.0 y 2.4.1.1**.

Esta entrega corrige la visibilidad: el widget y los detalles aparecen únicamente en la vista del garaje. Se ocultan al abrir el árbol tecnológico, la hoja de servicio u otra pantalla y regresan automáticamente al volver al garaje. Conserva los clientes **2.4.1.0 y 2.4.1.1** de NA, EU y ASIA. Pasaron 432 pruebas; siete contratos nativos de navegación son idénticos en las instalaciones 2.4.1.1 de las tres regiones. Las pruebas reales anteriores de contabilidad fueron en NA, EU y ASIA con 2.4.1.0; el jugador ya confirmó esta corrección en 2.4.1.1 al entrar al árbol tecnológico, la hoja de servicio y regresar al garaje. Esta confirmación no representa nuevas pruebas conectadas de las tres regiones. Lesta/Mir Tankov y Blitz no están cubiertos.

El mod registra ingresos, gastos y resultados después de gastos de tus partidas, con un widget permanente en el garaje y un panel **Ver detalles**. Usa los resultados financieros nativos y el saldo sincronizado de tu cuenta. No modifica los créditos reales.

## Cambios de esta entrega

- Solo se muestra en el garaje real, incluidas sus variantes de modo. La navegación nativa oculta la ventana de inmediato y la restaura al regresar, conservando el modo minimizado y las posiciones guardadas. La contabilidad sigue activa mientras consultas otras pantallas; no reinicia la meta ni el historial.
- Paquete para **WoT 2.4.1.1** con compatibilidad para **2.4.1.0**. El ZIP incluye el mismo archivo en las dos carpetas; el juego solo carga su versión activa.
- Compatibilidad regional para **NA, EU y ASIA**. El historial y las capturas se mantienen separados por región y cuenta; el reinicio diario usa el calendario nativo del servidor conectado.
- **Historial por día** tiene un control dorado **[+] / [−]**: **+** abre el historial y **−** lo recoge. Se puede pulsar el símbolo o toda la cabecera, también con teclado. El estado y las ayudas se adaptan a español o inglés.
- Iconos de modo más grandes: 40 px en los filtros y el detalle, y 24 px en las filas de partidas. Se conserva la lista de hasta cinco partidas con rueda y barra, tanto en el periodo actual como en el historial por día.
- El modo nativo 14 se muestra como **Batalla de torneo**, y el 15 como **Torneo de clanes**, con el emblema de batalla especial del cliente. Los nombres aparecen en español e inglés en los filtros, las partidas y el historial por día, también para partidas guardadas antes de esta corrección. Sus importes e identificadores se conservan.
- La felicitación espera a que el garaje, el vehículo y el widget estén visibles y terminen de cargar. Después de 1,5 segundos estables, muestra la celebración completa durante 2,8 segundos. Si se interrumpe la carga o se oculta la vista, queda pendiente para mostrarse de nuevo al estar lista.
- Al completar una meta aparece durante unos **tres segundos** un mensaje verde de felicitación con pequeñas chispas dentro del widget. Después vuelve a su aspecto normal.
- Si tienes los detalles abiertos, el aviso aparece en la zona de la meta. La celebración conserva el tamaño de la ventana y permite seguir usando sus controles y el garaje.
- Un logro ya mostrado no se repite al actualizar, cambiar de idioma o volver al garaje. Una meta nueva vuelve a habilitarlo; una cantidad mayor puede producir otra celebración al alcanzarla.
- Interfaz en **español e inglés**, con español por defecto. El selector junto a **Volver al widget** cambia el idioma al instante y guarda la elección, sin reiniciar el juego.
- Se traducen los textos del panel, el widget, las confirmaciones, los estados de carga, los mensajes y las ayudas. Los nombres propios de tanques y misiones conservan el idioma que proporciona el juego.
- Los importes usan **1.000.000** y **45,5 %** en español; **1,000,000** y **45.5%** en inglés. Cambia la presentación, no la cantidad real.
- **Días anteriores** pasa a llamarse **Historial por día**, plegado al final del panel.
- Cambiar el idioma conserva la meta, el borrador escrito, los filtros, la partida elegida y las estadísticas. Si no se puede guardar el idioma, el panel informa del error y permite reintentarlo.

## Idioma

Abre **Ver detalles** y elige **Español** o **English** junto al botón para volver al widget. La elección se conserva en este equipo para futuras sesiones. Una instalación sin preferencia guardada inicia en español; una preferencia inválida también utiliza español.

En inglés, el historial se presenta como **Daily battle history**. Los modos usan su nombre en inglés, mientras las imágenes, niveles e identificadores de vehículos siguen siendo los del resultado nativo. La [guía en inglés](README-en.md) explica las mismas funciones para jugadores de habla inglesa.

## Uso diario

**Ver detalles → Desglose de batallas** permite combinar modo y tanque, por ejemplo **Escaramuza + Pz. Neu (Nivel XI)**. Los filtros cambian el resultado y el desglose de partidas; el saldo, la meta, el widget y la conciliación corresponden a toda la cuenta. Las listas conservan los emblemas del modo, la imagen del vehículo y su nivel real, incluidas las imágenes nativas de los vehículos de Torre oscura.

Los totales se calculan con todas las partidas del periodo elegido. Cada consulta muestra sus **100 partidas más recientes**, con **hasta cinco filas completas** antes de desplazar la lista mediante rueda o barra. Los resultados negativos son rojos, los positivos verdes y los ceros neutros. Las partidas con varios vehículos conservan un resultado conjunto: no se atribuye ese mismo importe a cada tanque.

**Ingresos brutos** incluye las bonificaciones de reservas personal y del clan. Las reservas se muestran como filas del desglose, pero **no se suman otra vez**. Si una captura antigua carece de ese detalle, muestra un guion; eso no elimina sus ingresos, gastos ni resultado conocidos. Una reserva comprobada en 0 muestra 0.

La meta expresa créditos **adicionales** que quieres ganar desde el saldo al activarla. Por ejemplo, con 22.000.000 de saldo y una meta de 3.000.000, comienzas en 0 % y completas al llegar a 25.000.000. El campo agrupa miles con puntos y sus flechas ajustan 100.000. **Actualizar meta** conserva la base y el avance; escribir 0 la desactiva sin perder esa referencia durante la jornada. **Reiniciar meta** inicia solo la meta desde el saldo actual, sin borrar partidas.

El widget aparece al volver al garaje. El círculo de su esquina lo minimiza a un aro con el porcentaje de la meta. Pulsa cualquier parte del círculo para volver al resumen y usa el botón «Mover», visible al pasar el ratón, para cambiar su posición. El resumen amplio se mueve por su cabecera y permite usar el garaje fuera de su superficie. No aparece durante la batalla. Las tres vistas conservan sus posiciones y los borradores durante actualizaciones normales.

Al alcanzar una meta nueva, el texto **«¡Meta alcanzada! ¡Buen trabajo!»** se muestra durante 2,8 segundos con un efecto pequeño y localizado. Empieza después de 1,5 segundos de garaje y widget visibles, con el vehículo cargado y sin la espera de carga del juego. Solo se confirma como mostrado al terminar: si la ventana se oculta o vuelves a una batalla antes de acabar, se conserva pendiente. Las cifras y el saldo siguen siendo los reales. El efecto termina solo y no ocupa toda la pantalla. Si el widget está minimizado, espera hasta que muestres una vista; no la abre por ti. Las metas que ya estaban completas al instalar esta función se reconocen sin reproducir una celebración antigua. Cuando el entorno informa de una preferencia de movimiento reducido, se conserva el mensaje estático.

## Reinicios y días anteriores

Cada nuevo **día de juego del servidor** inicia un periodo con partidas, ganancias, pérdidas y estadísticas por tanque en 0. La conciliación toma el saldo actual sincronizado. La meta empieza en **100.000 créditos adicionales**, al 0 %, desde el saldo y la fecha de ese nuevo período. Puedes modificar la cantidad o escribir 0 para desactivarla durante la jornada. Se descarta el borrador anterior de la meta al aplicar ese reinicio completo.

El calendario se obtiene del ajuste regional nativo `starting_time_of_a_new_game_day` y de `helpers.time_utils.getServerUTCTime()` después de sincronizar el garaje de esta cuenta. No se sustituye por las 06:00 de Windows. Una reconexión o un mantenimiento dentro de la misma jornada no provoca otro reinicio. Si estuviste varios días sin entrar, se aplica una vez al primer saldo sincronizado al regresar. Si falta el reloj nativo o el saldo, espera sin inventarlos.

La actualización adapta las antiguas elecciones de horario al reinicio integrado. No vacía inmediatamente el periodo actual al migrar; una jornada del servidor ya armada conserva su fecha para no saltarse un reinicio pendiente. El botón **Reiniciar historial** realiza el reinicio completo cuando lo confirmas, sin desactivar la integración diaria.

**Historial por día** está plegado al final de los detalles y solo consulta datos al abrirlo y elegir un día. Muestra partidas, ingresos brutos, reservas conocidas, gastos y resultado después de gastos. Se puede filtrar por modo y tanque, con sus imágenes y niveles. Los abonos adicionales identificados se mantienen separados como total del día, porque no es seguro atribuirlos a un tanque o modo. Consultar el archivo no cambia el saldo actual, la meta ni las estadísticas de hoy.

Las jornadas usan el límite UTC del servidor y se presentan con una fecha en la zona local del equipo. Si temporalmente falta el reloj nativo, el último ciclo guardado sirve como límite conocido, sin avanzar el calendario basándose en el reloj del PC. No se limita el catálogo a 30 días ni se borran jornadas antiguas. Las listas de partidas siguen limitadas a 100 por consulta; los totales incluyen todas las registradas.

El archivo contiene **solo las partidas y recompensas capturadas por el mod**, no una descarga de toda la historia de la cuenta. Un reinicio manual cambia el periodo diario visible, pero conserva la evidencia necesaria para consultar las jornadas anteriores y evitar resultados duplicados. Una captura pendiente de cálculo no se presenta como una ganancia de 0.

## Misiones y conciliación

Los recibos nativos aportan importes reales e identificadores. El mod intenta resolver nombres de misiones, Crisol, campañas y aperturas normales de cupones del Pase de batalla. Los premios incluidos en una batalla se anotan sin sumarlos dos veces. Las compras, ventas o movimientos sin recibo identificado permanecen en **Otros movimientos / por identificar**. La meta sigue el cambio del saldo real, incluidos esos movimientos.

El resultado **−113.508 créditos** de una partida fue comparado y confirmado con el informe financiero por el usuario. También se confirmó una reserva del clan de **16.819**, con ingresos brutos de **42.608** y resultado después de gastos de **26.895**. Estas comprobaciones reales son distintas de las pruebas automatizadas.

## Instalación y actualización

Cierra el juego, extrae el ZIP en una carpeta aparte y abre `CreditLedger-Setup-0.22.14.exe`. El instalador detecta la versión activa, instala una sola copia y retira Credit Ledger de las carpetas de clientes anteriores; elimina esas carpetas solo si quedan vacías. Conserva los demás archivos y tus datos.

Para instalar manualmente, copia únicamente el paquete de la versión que usa tu juego a la ruta correspondiente:

```text
<CARPETA_DEL_JUEGO>\mods\2.4.1.1\local.credit_ledger.wotmod
<CARPETA_DEL_JUEGO>\mods\2.4.1.0\local.credit_ledger.wotmod
```

La misma descarga sirve para NA, EU y ASIA con los clientes 2.4.1.0 y 2.4.1.1. El ZIP ofrece ambos paquetes compatibles; el instalador utiliza solo la versión activa. La limpieza automática de versiones anteriores la realiza el `.exe`. Los datos locales se guardan bajo `mods\configs\credit_ledger`; las capturas se separan en `captures\<REGION>\<cuenta>`. Conserva un único paquete del mod dentro de la carpeta de versión activa. Los datos y otros mods se conservan.

El paquete público se actualiza descargando nuevas versiones de su ficha del portal oficial. No incluye cuentas, historiales ajenos, servicios, tareas programadas ni actualizador externo. Para desinstalarlo, elimina solo el archivo `.wotmod` con el juego cerrado; los datos locales se conservan. El paquete usa referencias a recursos locales del cliente y no incluye arte extraído del juego.

En el entorno de desarrollo original existe un actualizador local independiente, que comprueba el cierre del juego y verifica SHA-256 antes de instalar. Ese ayudante y sus rutas locales no forman parte de la descarga pública.

## Desarrollo y verificación

El código es original, compatible con el Python 2.7 del cliente instalado. El constructor compila con esa DLL en un proceso separado; no la distribuye ni incluye código descompilado del juego.

```console
python -m unittest discover -s tests -v
python build_release.py --game-root C:\Games\World_of_Tanks_NA --output RUTA_DE_SALIDA
```

Las pruebas automatizadas de lógica, captura e interfaz se complementan con casos regionales de NA, EU y ASIA. Incluyen contabilidad, consultas nativas, respuestas desfasadas, reinicios por cuenta, archivo por jornada, filtros combinados y diseño Gameface. Esta entrega comprueba además el regreso de batalla con garaje y vehículo en carga, la espera de visibilidad estable, la duración completa sin nuevos cambios de saldo, las interrupciones y la confirmación al terminar, además de minimizar, movimiento reducido, cambio de idioma y reinicio de metas. Los informes de compilación e instalación distinguen estas pruebas de las comprobaciones aún pendientes dentro del cliente real.
