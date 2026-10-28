# Nucleo de contabilidad

Codigo original sin dependencias externas. Sintaxis compatible con Python 2.7 y
Python 3; esto **no confirma** que pueda cargarse en el runtime de World of Tanks.
No contiene hooks del cliente ni una pantalla nativa.

## Registro

`EconomyLedger.upsert_result(result)` recibe este esquema:

```json
{
  "region": "NA",
  "account_id": "123",
  "battle_id": "456",
  "occurred_at": "2026-10-17T15:00:00Z",
  "status": "final",
  "credits": {
    "gross": 100000,
    "expenses": {"repair": 10000, "ammo": 20000, "consumables": 5000, "other": 0}
  },
  "resources": {"bonds": {"earned": 10, "spent": 0}}
}
```

- La identidad es `(region, account_id, battle_id)`. Region se normaliza a
  mayusculas y los IDs a texto. Repetir un registro identico devuelve `unchanged`;
  un resultado corregido devuelve `updated` y reemplaza al anterior.
- `gross` debe ser el ingreso **antes** de los gastos. El neto se calcula una
  sola vez como `gross - repair - ammo - consumables - other`. Nunca enviar un
  subtotal neto como bruto. No se aceptan campos ambiguos como `net` o `subtotal`.
- Cada gasto es un costo real atribuible a esa partida; un precio de catalogo de
  un objeto del inventario no equivale a un gasto real. El adaptador debe resolver
  esa diferencia y evitar atribuir una misma reposicion a dos partidas.
- Los importes deben ser enteros no negativos; se rechazan booleanos, flotantes
  y cadenas. El neto calculado puede ser negativo.
- `pending` queda excluido de importes, promedios y metas. Puede omitir `credits`
  hasta disponer del desglose completo. Un `final` requiere todos los campos de
  creditos. Una notificacion `pending` tardia no degrada un resultado `final`;
  devuelve `ignored_pending`. Las correcciones `final` reemplazan al anterior;
  el productor debe evitar reenviar una version final antigua tras una corregida.
- `resources` es opcional. Cada recurso distinto de `credits` usa `earned` y
  `spent` reales. Omitir un recurso en una partida equivale a cero movimiento
  **solo si el productor sabe que no lo hubo**. El nucleo no descubre recursos ni
  valida que un identificador corresponda a una moneda del juego.
- Todas las fechas y cortes son UTC estrictos `YYYY-MM-DDTHH:MM:SSZ`.

## Resumen y metas

```python
from core import EconomyLedger

ledger = EconomyLedger()
ledger.upsert_result(result)
summary = ledger.summary("NA", "123")
status = ledger.goal_status({
    "region": "NA", "account_id": "123", "resource": "credits",
    "mode": "net_earnings", "target": 1000000,
    "since_utc": "2026-10-17T15:00:00Z"
})
```

`net_earnings` mide ganancia neta de las partidas finales en o despues del corte
UTC obligatorio. No confunde ese total con el saldo de la cuenta.

`balance` compara la meta con un saldo real que el llamante pasa mediante
`external_balance=...`; ese saldo debe corresponder a la cuenta, region y recurso
de la meta. Este nucleo no lo consulta ni lo deduce de las partidas. Un corte UTC
opcional controla las partidas usadas para el promedio.

`progress` se limita a 0..1; `current` conserva las perdidas. `estimated_battles`
es `None` si no hay partidas o el promedio neto no es positivo; una meta ya
alcanzada devuelve 0. La estimacion redondea hacia arriba usando el promedio de
las partidas finales del periodo; es una extrapolacion, no una garantia.

## Persistencia y limites

`ledger.save(path)` y `EconomyLedger.load(path)` escriben/leen JSON UTF-8 version
1. El directorio debe existir. La escritura usa un temporal en el mismo directorio,
flush + fsync. Python 3 usa reemplazo atomico. El Python 2 del cliente no incluye
`_ctypes`: se usa una secuencia recuperable de renombrados con respaldo `.previous`.
Si el destino falta al cargar, se recupera ese respaldo antes de leer. Si falla el
segundo renombrado, se restaura el anterior y se propaga el error. Esta secuencia
no promete la atomicidad estricta de una unica operacion del sistema.
Un JSON corrupto o una identidad duplicada se rechaza al cargar.

Usar un solo escritor por archivo. No hay bloqueo entre procesos, recuperacion de
archivos corruptos, retencion automatica, consulta al servidor ni almacenamiento
de metas (son configuracion del llamante). La atomicidad depende del sistema de
archivos y no promete recuperacion frente a fallos fisicos del dispositivo.

Pruebas desde la carpeta del proyecto:

```text
python -m unittest discover -s tests -v
```
