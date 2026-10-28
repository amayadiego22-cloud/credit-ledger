/* Original credit-ledger UI. ES5, native Wulf model bridge, no network calls. */
(function () {
    'use strict';
    // Spanish source phrases form a reversible catalog for pending status messages.
    var translations = {
        "Contabilidad de cr\u00e9ditos": "Credit ledger",
        "META DE CR\u00c9DITOS": "CREDIT GOAL",
        "CONTABILIDAD DE CR\u00c9DITOS": "CREDIT LEDGER",
        "CONTABILIDAD DE CR\u00c9DITOS \u00b7 ARRASTRA PARA MOVER": "CREDIT LEDGER \u00b7 DRAG TO MOVE",
        "Econom\u00eda de tu cuenta": "Your credit overview",
        "Ver detalles": "View details",
        "Volver al widget": "Back to widget",
        "Arrastra para mover": "Drag to move",
        "Mover": "Move",
        "Meta": "Goal",
        "Arrastra el borde para mover": "Drag the edge to move",
        "Arrastra para mover el widget": "Drag to move the widget",
        "Arrastra la barra para mover el widget": "Drag the bar to move the widget",
        "Arrastra el t\u00edtulo para mover la ventana": "Drag the title to move the window",
        "Mostrar contabilidad de cr\u00e9ditos": "Show credit ledger",
        "Minimizar contabilidad de cr\u00e9ditos": "Minimize credit ledger",
        "Contabilidad de cr\u00e9ditos minimizada": "Credit ledger minimized",
        "Minimizar": "Minimize",
        "Avance de la meta de cr\u00e9ditos": "Credit goal progress",
        "Avance desde el saldo base": "Progress from your starting balance",
        "Esperando tu cuenta": "Waiting for your account",
        "El progreso aparecer\u00e1 cuando se sincronice tu saldo.": "Progress will appear once your balance is synced.",
        "Esperando los datos de tu cuenta...": "Waiting for your account data...",
        "Esperando los datos de tu cuenta\u2026": "Waiting for your account data\u2026",
        "Actualizar": "Refresh",
        "Actualizando\u2026": "Refreshing\u2026",
        "Ganancia o p\u00e9rdida total": "Total profit or loss",
        "Ganancia o p\u00e9rdida del veh\u00edculo": "Vehicle profit or loss",
        "Ganancia o p\u00e9rdida del modo": "Game mode profit or loss",
        "Partidas registradas": "Recorded battles",
        "Despu\u00e9s de descontar los gastos": "After all battle costs",
        "Saldo al iniciar la meta": "Goal starting balance",
        "Sin meta iniciada": "No goal started",
        "Saldo guardado al comenzar": "Balance saved when you started",
        "Saldo actual de cr\u00e9ditos": "Current credit balance",
        "Cr\u00e9ditos que faltan": "Credits remaining",
        "Sin meta activa": "No active goal",
        "Se actualiza autom\u00e1ticamente": "Updates automatically",
        "Tu meta empieza desde el saldo actual": "Your goal starts from your current balance",
        "Cr\u00e9ditos adicionales que quiero ganar": "Additional credits I want to earn",
        "Sumar 100.000 cr\u00e9ditos": "Add 100,000 credits",
        "Restar 100.000 cr\u00e9ditos": "Subtract 100,000 credits",
        "Las flechas ajustan 100.000 cr\u00e9ditos. Escribe 0 para usar la contabilidad sin meta.": "The arrows adjust by 100,000 credits. Enter 0 to track credits without a goal.",
        "Inicia tu meta desde el saldo actual, en 0 %.": "Start your goal at 0% from your current balance.",
        "Iniciar meta": "Start goal",
        "Actualizar meta": "Update goal",
        "Reactivar meta": "Resume goal",
        "Reiniciar meta": "Reset goal",
        "Desactivar meta": "Disable goal",
        "Guardar sin meta": "Save without a goal",
        "Guardando...": "Saving...",
        "Reiniciando...": "Resetting...",
        "Empieza desde tu saldo actual, en 0 %. Conserva el historial.": "Start again at 0% from your current balance. Your battle history is kept.",
        "Sin meta disponible": "No goal available",
        "Desglose de batallas \u00b7 cr\u00e9ditos": "Battle credit breakdown",
        "Filtrar por modo de juego": "Filter by game mode",
        "Filtrar por veh\u00edculo": "Filter by vehicle",
        "Todos los modos": "All game modes",
        "Todos los veh\u00edculos": "All vehicles",
        "Desplazar modos de juego": "Scroll game modes",
        "Desplazar veh\u00edculos": "Scroll vehicles",
        "El filtro se aplica a las partidas y su resultado. El saldo y la meta corresponden a toda tu cuenta.": "Filters apply to battles and their earnings. Your balance and goal cover your entire account.",
        "Reintentar": "Retry",
        "Todas las partidas": "All battles",
        "Desplazar historial": "Scroll battle history",
        "Modo de juego: Modo no identificado": "Game mode: Unknown mode",
        "Ingresos brutos": "Gross earnings",
        "Reserva personal": "Personal reserve bonus",
        "Reserva del clan": "Clan reserve bonus",
        "Reparaciones": "Repairs",
        "Munici\u00f3n": "Ammunition",
        "Consumibles y directivas": "Consumables and directives",
        "Otros gastos de batalla": "Other battle costs",
        "Ganancia o p\u00e9rdida despu\u00e9s de gastos": "Profit or loss after costs",
        "Sin desglose de reservas disponible.": "Reserve breakdown unavailable.",
        "Las partidas finalizadas aparecer\u00e1n aqu\u00ed.": "Completed battles will appear here.",
        "Conciliaci\u00f3n con tu saldo de cuenta": "Account balance reconciliation",
        "Esperando un saldo sincronizado...": "Waiting for a synced balance...",
        "Saldo al iniciar el seguimiento": "Starting tracked balance",
        "Neto de batallas posteriores": "Net earnings from subsequent battles",
        "Recompensas y abonos adicionales": "Rewards and other credits received",
        "Otros movimientos / por identificar": "Other / unidentified transactions",
        "Saldo actual conciliado": "Reconciled current balance",
        "La meta sigue el saldo real: incluye misiones, recompensas, compras y ventas.": "Your goal follows your actual balance, including missions, rewards, purchases and sales.",
        "Misiones y recompensas identificadas": "Identified missions and rewards",
        "Los importes marcados \u00abIncluido en partida\u00bb ya forman parte de sus ingresos.": "Amounts marked \u201cIncluded in battle\u201d are already included in battle earnings.",
        "Desplazar recompensas": "Scroll rewards",
        "Reiniciar el per\u00edodo actual": "Reset the current period",
        "Deja las partidas, ganancias y gastos en 0 y desactiva la meta. Tu saldo de cuenta y los d\u00edas anteriores se conservan.": "Clear current battles, earnings and costs, and disable your goal. Your account balance and previous days are kept.",
        "Reiniciar historial": "Reset battle history",
        "Empezar de nuevo": "Start over",
        "El historial actual queda en 0 y la meta se desactiva. Tu saldo y los d\u00edas anteriores se conservan.": "Current battle history will be cleared and your goal disabled. Your balance and previous days are kept.",
        "Confirmar reinicio": "Confirm reset",
        "Cancelar": "Cancel",
        "Historial por d\u00eda": "Daily battle history",
        "Mostrar historial por d\u00eda": "Show daily battle history",
        "Ocultar historial por d\u00eda": "Hide daily battle history",
        "Consulta jornadas anteriores por modo o veh\u00edculo. Esta vista no cambia tu per\u00edodo actual ni tu meta.": "Browse previous days by game mode or vehicle. This does not change your current period or goal.",
        "Jornada": "Day",
        "Seleccionar d\u00eda": "Select a day",
        "Desplazar jornada": "Scroll days",
        "Modo de juego": "Game mode",
        "Desplazar modo de juego": "Scroll game modes",
        "Veh\u00edculo": "Vehicle",
        "Desplazar veh\u00edculo": "Scroll vehicles",
        "Desplazar partidas anteriores": "Scroll previous battles",
        "Todas las partidas del d\u00eda": "All battles for this day",
        "Datos guardados en este equipo para tu cuenta. Los movimientos anteriores al seguimiento permanecen en el saldo base.": "Data is saved on this computer for your account. Transactions before tracking began are included in the starting balance.",
        "Desplazar panel": "Scroll panel",
        "Esc para volver al widget": "Esc to return to the widget",
        "Batallas del per\u00edodo ": "Battles this period ",
        "Ganancia o p\u00e9rdida de las partidas despu\u00e9s de gastos": "Battle profit or loss after costs",
        "Configura tu meta en Ver detalles.": "Set your goal in View details.",
        "Meta: ": "Goal: ",
        " cr\u00e9ditos": " credits",
        " cr\u00e9ditos.": " credits.",
        "Esperando el saldo actual para calcular el avance.": "Waiting for your current balance to calculate progress.",
        "Meta alcanzada.": "Goal reached.",
        "\u00a1Meta alcanzada! \u00a1Buen trabajo!": "Goal reached! Well done!",
        "Tu saldo est\u00e1 por debajo de la base de la meta.": "Your balance is below the goal's starting balance.",
        "Avance desde el saldo base de tu meta.": "Progress from your goal's starting balance.",
        "Faltan ": "Remaining: ",
        "No se pudo actualizar. Revisa los detalles.": "Could not update. Open the details for more information.",
        "Progreso pendiente de sincronizar": "Progress waiting to sync",
        " partida": " battle",
        " partidas": " battles",
        " \u00b7 Partidas pendientes": " \u00b7 Battles pending",
        "Saldo pendiente": "Balance pending",
        "Saldo ": "Balance ",
        "La meta m\u00e1xima es 9.007.199.254.740.991 cr\u00e9ditos.": "The maximum goal is 9,007,199,254,740,991 credits.",
        "Escribe una cantidad entera; usa 0 si no quieres una meta.": "Enter a whole number, or 0 to track without a goal.",
        "Reiniciando tu meta desde el saldo actual\u2026": "Resetting your goal from your current balance\u2026",
        "Guardando tu meta\u2026": "Saving your goal\u2026",
        "Guardar 0 desactiva el objetivo. Conserva la base, el avance y el historial.": "Saving 0 disables the goal. Your starting balance, progress and history are kept.",
        "Cambios sin guardar. ": "Unsaved changes. ",
        "Conserva lo que ya has acumulado y recalcula el porcentaje.": "Keeps your progress and recalculates the percentage.",
        "Cambios sin guardar. El progreso muestra la meta guardada.": "Unsaved changes. Progress reflects your saved goal.",
        "Escribe una cantidad o 0 para continuar sin meta.": "Enter an amount, or 0 to continue without a goal.",
        "Partida": "Battle",
        "No se pudo cargar la lista de partidas. Puedes reintentar; los importes del veh\u00edculo ya est\u00e1n disponibles.": "Could not load the battle list. You can retry; vehicle earnings are already available.",
        "La lista de partidas est\u00e1 tardando. Los importes est\u00e1n disponibles; puedes reintentar.": "The battle list is taking longer than expected. Earnings are available; you can retry.",
        "El veh\u00edculo ya no tiene partidas en este modo.": "This vehicle no longer has recorded battles in this mode.",
        "No se pudo filtrar el veh\u00edculo. Puedes reintentar.": "Could not load this vehicle's battles. You can retry.",
        "Cargando la lista de partidas. Los importes del veh\u00edculo ya est\u00e1n disponibles.": "Loading the battle list. Vehicle earnings are already available.",
        "Reiniciando historial...": "Resetting battle history...",
        "El historial actual queda en 0 y la meta se desactiva. Puedes escribir una nueva desde tu saldo actual. Tu saldo y los d\u00edas anteriores se conservan.": "Current history will be cleared and your goal disabled. You can start a new goal from your current balance. Your balance and previous days are kept.",
        "Historial reiniciado.": "Battle history reset.",
        "Nuevo historial. Puedes iniciar una meta desde tu saldo actual.": "New tracking period. You can start a goal from your current balance.",
        "No se reinici\u00f3 el historial. Puedes volver a intentarlo.": "Battle history could not be reset. You can try again.",
        "El juego no proporcion\u00f3 el detalle de reservas de estas partidas. Sus cr\u00e9ditos ya est\u00e1n incluidos en los ingresos brutos.": "The game did not provide reserve details for these battles. Those credits are already included in gross earnings.",
        "El detalle de reservas aparecer\u00e1 si el juego lo proporciona. Los ingresos y gastos se actualizan por separado.": "Reserve details will appear if provided by the game. Earnings and costs update independently.",
        "Ya incluidas en los ingresos brutos.": "Already included in gross earnings.",
        " Desglose disponible en ": " Breakdown available for ",
        " de ": " of ",
        " partidas.": " battles.",
        "No hay partidas registradas para este veh\u00edculo y modo.": "No battles recorded for this vehicle and game mode.",
        "No hay partidas registradas en este modo.": "No battles recorded in this game mode.",
        " cr. (incluido en el ingreso bruto)": " cr. (included in gross earnings)",
        "Nivel ": "Tier ",
        "Nivel sin identificar": "Unknown tier",
        "Veh\u00edculo sin identificar": "Unknown vehicle",
        "Varios veh\u00edculos": "Multiple vehicles",
        "Modo no identificado": "Unknown mode",
        "Modo de juego: ": "Game mode: ",
        "Sin imagen": "No image",
        "Partidas de ": "Battles with ",
        "Todas las partidas de ": "All battles in ",
        "No se pudo cargar la jornada. Puedes reintentar.": "Could not load this day. You can retry.",
        "Esta jornada est\u00e1 tardando en cargar. Puedes reintentar.": "This day is taking longer than expected to load. You can retry.",
        "No hay datos para esta selecci\u00f3n. Elige otro d\u00eda, modo o veh\u00edculo.": "No data for this selection. Choose another day, game mode or vehicle.",
        "No se pudo leer esta jornada. Puedes reintentar.": "Could not read this day's data. You can retry.",
        "Cargando la jornada seleccionada\u2026": "Loading the selected day\u2026",
        "Las jornadas anteriores estar\u00e1n disponibles al sincronizar la cuenta.": "Previous days will be available once your account is synced.",
        "A\u00fan no hay jornadas anteriores guardadas.": "No previous days have been saved yet.",
        "Partidas pendientes de cargar": "Battle list waiting to load",
        " \u00b7 Se muestran las \u00faltimas ": " \u00b7 Showing the latest ",
        "Todas las partidas de esta selecci\u00f3n": "All battles in this selection",
        "Resultado de ": "Results for ",
        "Selecciona una jornada": "Select a day",
        "Las reservas ya est\u00e1n incluidas en los ingresos brutos.": "Reserve bonuses are already included in gross earnings.",
        "El detalle de reservas no est\u00e1 disponible para todas las partidas. Sus cr\u00e9ditos ya forman parte de los ingresos brutos.": "Reserve details are unavailable for some battles. Those credits are already included in gross earnings.",
        "Abonos adicionales de toda la jornada: ": "Additional credits received throughout the day: ",
        " cr\u00e9ditos. Se muestran por separado del resultado de las batallas.": " credits. Shown separately from battle earnings.",
        "Tu meta de cr\u00e9ditos": "Your credit goal",
        "Meta opcional de cr\u00e9ditos": "Optional credit goal",
        "La contabilidad sigue activa sin objetivo. Puedes reactivar la meta conservando tu avance.": "Credit tracking continues without a goal. You can resume the goal and keep your progress.",
        "La contabilidad sigue activa sin objetivo. Puedes iniciar una meta cuando quieras.": "Credit tracking continues without a goal. You can start a goal at any time.",
        "Meta guardada: ": "Saved goal: ",
        "Saldo pendiente de sincronizar.": "Balance waiting to sync.",
        "El progreso aparecer\u00e1 cuando la cuenta est\u00e9 lista.": "Progress will appear once your account is ready.",
        "Progreso pendiente de actualizar.": "Progress waiting to update.",
        " al promedio registrado": " at your recorded average",
        "\u00daltima meta iniciada: ": "Last goal started: ",
        "Meta iniciada: ": "Goal started: ",
        "Inicio de la meta: pendiente de sincronizar.": "Goal start time is waiting to sync.",
        "\u00daltimo saldo base: ": "Last starting balance: ",
        "Saldo base: ": "Starting balance: ",
        " | Saldo al completar: ": " | Balance at completion: ",
        "Al iniciar una meta, tu saldo actual se guardar\u00e1 como base del 0 %.": "When you start a goal, your current balance becomes the 0% starting point.",
        "Avance conservado: pendiente de sincronizar el saldo.": "Saved progress is waiting for your balance to sync.",
        "Avance conservado: ": "Saved progress: ",
        " cr\u00e9ditos desde el saldo base.": " credits from the starting balance.",
        "Seguimiento desde ": "Tracking since ",
        "Inicio del seguimiento: pendiente de sincronizar.": "Tracking start time is waiting to sync.",
        "Incluido en partida": "Included in battle",
        "Movimiento adicional": "Additional transaction",
        "Los nuevos recibos de misiones y recompensas aparecer\u00e1n aqu\u00ed.": "New mission and reward receipts will appear here.",
        "Se registra el nombre cuando el juego permite identificarlo.": "Names are recorded when the game provides them.",
        "Datos de tu cuenta actual": "Current account data",
        "Datos en vivo | ": "Live data | ",
        " resultado pendiente": " result pending",
        " resultados pendientes": " results pending",
        " partida registrada": " recorded battle",
        " partidas registradas": " recorded battles",
        "Partidas pendientes de filtrar": "Battle list waiting to filter",
        "Base de tu meta actual": "Your current goal's starting balance",
        "\u00daltima meta \u00b7 sin meta activa": "Last goal \u00b7 no active goal",
        "Pendiente": "Pending",
        "Meta alcanzada": "Goal reached",
        "Para completar la meta": "To reach your goal",
        "No se pudieron leer los datos del panel. Pulsa Actualizar.": "Could not read the panel data. Click Refresh.",
        "No se reinici\u00f3 la meta. Conservas tu avance; puedes volver a intentarlo.": "The goal could not be reset. Your progress is safe; you can try again.",
        "Meta reiniciada desde tu saldo actual, en 0 %. El historial se conserva.": "Goal reset to 0% from your current balance. Battle history is kept.",
        "La meta cambi\u00f3 durante el reinicio. Revisa la cantidad y vuelve a intentarlo.": "The goal changed during the reset. Check the amount and try again.",
        "Sin meta activa. Tu contabilidad contin\u00faa.": "No active goal. Credit tracking continues.",
        "Meta guardada.": "Goal saved.",
        "No se guard\u00f3 la meta. Puedes volver a intentarlo.": "The goal could not be saved. You can try again.",
        "No se pudo cambiar la vista. Puedes volver a intentarlo.": "Could not change the view. You can try again.",
        "El juego no pudo completar la acci\u00f3n. Pulsa Actualizar para intentarlo de nuevo.": "The game could not complete this action. Click Refresh to try again.",
        "El panel a\u00fan no est\u00e1 conectado al juego.": "The panel is not connected to the game yet.",
        "Usa cr\u00e9ditos enteros: por ejemplo 1.000.000. No se admiten decimales.": "Enter whole credits, such as 1,000,000. Decimal amounts are not supported.",
        "No se peg\u00f3 la cantidad. Usa un entero como 1.000.000, sin decimales.": "Amount not pasted. Use a whole number such as 1,000,000, with no decimals.",
        "Usa un entero como 1.000.000, sin decimales.": "Use a whole number such as 1,000,000, with no decimals.",
        "No se pudo conectar la interfaz con el juego.": "Could not connect the interface to the game.",
        "Esperando la conexi\u00f3n del juego.": "Waiting for the game connection.",
        "Idioma": "Language",
        "Guardando idioma\u2026": "Saving language\u2026",
        "Idioma guardado.": "Language saved.",
        "No se pudo guardar el idioma. Puedes reintentar.": "Could not save the language. You can retry.",
        "El idioma no se guard\u00f3 a tiempo. Puedes reintentar.": "The language was not saved in time. You can retry.",
        "Batalla aleatoria": "Random Battle",
        "Entrenamiento en equipo": "Team Training",
        "Batalla especial": "Special Battle",
        "Batalla de torneo": "Tournament Battle",
        "Torneo de clanes": "Clan Tournament",
        "Batalla de equipo": "Team Battle",
        "Modo de juego especial": "Special game mode",
        "Mapa global": "Global Map",
        "Dominaci\u00f3n": "Domination",
        "Cacer\u00eda de acero": "Steel Hunt",
        "Escaramuza": "Skirmish",
        "Avance": "Advance",
        "Batalla clasificatoria": "Ranked Battle",
        "Gran batalla": "Grand Battle",
        "L\u00ednea del frente": "Frontline",
        "Cazador de acero": "Steel Hunter",
        "Misi\u00f3n de reconocimiento": "Recon Mission",
        "Topograf\u00eda": "Topography",
        "Asedio": "Onslaught",
        "Entrada en calor": "Warm-Up",
        "Asedio ligero": "Onslaught Light",
        "Torre oscura \u00b7 Normal": "Babylon: Dark Tower \u00b7 Normal",
        "Torre oscura \u00b7 Dif\u00edcil": "Babylon: Dark Tower \u00b7 Hard",
        "Torre oscura \u00b7 Pesadilla": "Babylon: Dark Tower \u00b7 Nightmare",
        "Introduce una cantidad entera igual o mayor que cero.": "Enter a whole number greater than or equal to zero.",
        "La meta debe estar entre 0 y 9.007.199.254.740.991 cr\u00e9ditos.": "The goal must be between 0 and 9,007,199,254,740,991 credits.",
        "Actualiza el panel para iniciar una meta desde tu saldo.": "Refresh the panel to start a goal from your current balance.",
        "Espera que se sincronice tu cuenta antes de guardar la meta.": "Wait for your account to sync before saving the goal.",
        "Espera que se sincronice tu saldo antes de iniciar la meta.": "Wait for your balance to sync before starting a goal.",
        "La configuraci\u00f3n de la meta guardada no es v\u00e1lida.": "The saved goal settings are invalid.",
        "La cantidad de la meta guardada no es v\u00e1lida.": "The saved goal amount is invalid.",
        "El contador de reinicios de la meta no es v\u00e1lido.": "The saved goal reset counter is invalid.",
        "La base o la fecha de la meta guardada no es v\u00e1lida.": "The saved goal's starting balance or date is invalid.",
        "La fecha de inicio de la meta no es v\u00e1lida.": "The goal's start date is invalid.",
        "La suma del saldo y la meta supera el l\u00edmite permitido.": "Your balance plus the goal exceeds the supported limit.",
        "Introduce una cantidad mayor que cero para reiniciar la meta.": "Enter an amount greater than zero to reset the goal.",
        "El contador de reinicios de la meta supera el l\u00edmite admitido.": "The goal reset counter exceeds the supported limit.",
        "La fecha del reinicio no es una fecha UTC v\u00e1lida.": "The reset date is not a valid UTC date.",
        "Espera que se sincronice tu cuenta antes de cambiar el historial.": "Wait for your account to sync before changing the history.",
        "Las opciones del historial no son v\u00e1lidas.": "The history settings are invalid.",
        "Selecciona reinicio manual, diario o del servidor.": "Choose manual, daily, or server reset.",
        "La hora de reinicio debe estar entre 0 y 23.": "The reset hour must be between 0 and 23.",
        "La opci\u00f3n de conservar la meta no es v\u00e1lida.": "The keep-goal option is invalid.",
        "Espera que se sincronice tu saldo antes de reiniciar el historial.": "Wait for your balance to sync before resetting the history.",
        "El tipo de reinicio no es v\u00e1lido.": "The reset type is invalid.",
        "La opci\u00f3n de reiniciar la meta no es v\u00e1lida.": "The reset-goal option is invalid.",
        "El contador de reinicios supera el l\u00edmite admitido.": "The reset counter exceeds the supported limit.",
        "Espera que se sincronice el horario del servidor antes de reiniciar.": "Wait for the server time to sync before resetting.",
        "La solicitud del filtro no es v\u00e1lida.": "The filter request is invalid.",
        "El modo seleccionado no es v\u00e1lido.": "The selected game mode is invalid.",
        "El veh\u00edculo seleccionado no es v\u00e1lido.": "The selected vehicle is invalid.",
        "La cuenta cambi\u00f3. Vuelve a elegir el veh\u00edculo.": "The account changed. Select the vehicle again.",
        "No se pudo cargar el veh\u00edculo. Vuelve a intentarlo.": "The vehicle could not be loaded. Please try again.",
        "La cuenta cambi\u00f3. Vuelve a elegir el d\u00eda.": "The account changed. Select the day again.",
        "El d\u00eda seleccionado no es v\u00e1lido.": "The selected day is invalid.",
        "No se pudo cargar el d\u00eda. Vuelve a intentarlo.": "The selected day could not be loaded. Please try again.",
        "El reinicio diario del servidor es autom\u00e1tico y permanece activo.": "The daily server reset runs automatically and stays enabled.",
        "No se pudieron guardar los ajustes del historial.": "The history settings could not be saved.",
        "Confirma el reinicio del historial en el panel.": "Confirm the history reset in the panel.",
        "Espera que se sincronice tu cuenta antes de reiniciar el historial.": "Wait for your account to sync before resetting the history.",
        "No se pudo reiniciar el historial. Los datos anteriores se conservan.": "The history could not be reset. Your previous data has been kept.",
        "No se pudo guardar la meta. Revisa el archivo game.log.": "The goal could not be saved. Check game.log for details.",
        "Espera que se sincronice tu cuenta antes de reiniciar la meta.": "Wait for your account to sync before resetting the goal.",
        "No se pudo reiniciar la meta. Tu meta anterior se conserva.": "The goal could not be reset. Your previous goal has been kept.",
        "Contabilidad: no se pudo abrir el panel. Revisa game.log.": "Credit Ledger: the panel could not be opened. Check game.log for details.",
        "Selecciona el resumen o los detalles de contabilidad.": "Choose the accounting summary or details view.",
        "No se pudo guardar la vista de contabilidad.": "The accounting view could not be saved.",
        "Esperando que se sincronice tu cuenta del juego.": "Waiting for your game account to sync.",
        "Saldo pendiente de sincronizar; el historial ya est\u00e1 disponible.": "Your balance is still syncing; your battle history is already available.",
        "Tu pr\u00f3xima batalla finalizada aparecer\u00e1 aqu\u00ed.": "Your next completed battle will appear here.",
        "Jornada diaria del servidor; horario mostrado en la zona local del equipo.": "Server day; times are shown in your computer's local time zone.",
        "Solo se muestran partidas y recompensas registradas por el mod; los importes de batallas ya descuentan sus gastos.": "Only battles and rewards recorded by the mod are shown. Battle amounts already include their expenses.",
        "Contabilidad de cr\u00e9ditos: captura activa. El widget aparece en el garaje; pulsa el c\u00edrculo para abrir el resumen.": "Credit Ledger: recording is active. The widget is available in the Garage; click the circle to open the summary.",
        "Contabilidad: resultado guardado; desglose pendiente de conciliaci\u00f3n.": "Credit Ledger: result saved; the breakdown is waiting for reconciliation.",
        " | Sin meta activa.": " | No active goal.",
        " | Meta alcanzada.": " | Goal reached.",
        " | Meta: saldo pendiente de sincronizar.": " | Goal: waiting for your balance to sync.",
        "Selecciona espa\u00f1ol o ingl\u00e9s.": "Choose Spanish or English.",
        "No se pudo guardar el idioma. La selecci\u00f3n anterior se conserva.": "The language could not be saved. Your previous selection has been kept."
    };
    var modeNames = {1:'Batalla aleatoria', 2:'Entrenamiento en equipo', 4:'Batalla especial', 5:'Batalla especial',
        7:'Batalla de equipo', 9:'Modo de juego especial', 13:'Mapa global', 14:'Batalla de torneo', 15:'Torneo de clanes',
        18:'Dominaci\u00f3n', 19:'Cacer\u00eda de acero',
        20:'Escaramuza', 21:'Avance', 22:'Batalla clasificatoria', 24:'Gran batalla', 27:'L\u00ednea del frente',
        29:'Cazador de acero', 37:'Misi\u00f3n de reconocimiento', 38:'Topograf\u00eda', 43:'Asedio', 44:'Entrada en calor',
        49:'Asedio ligero', 101:'Torre oscura \u00b7 Normal', 102:'Torre oscura \u00b7 Dif\u00edcil', 103:'Torre oscura \u00b7 Pesadilla'};
    var reverseTranslations = {}, translationKey;
    for (translationKey in translations) {
        if (translations.hasOwnProperty(translationKey)) { reverseTranslations[translations[translationKey]] = translationKey; }
    }
    var MAX_DIGITS = '9007199254740991';
    var state = {
        payload: null, connected: false, dirty: false, pendingSave: false, pendingGoalReset: null,
        language: 'es', savedLanguage: 'es', languageLoaded: false, languagePending: null,
        languageRequestId: 0, languageAcceptedId: 0, languageTimer: null, languageFeedback: '', languageRetry: null,
        viewMode: 'widget', pendingViewMode: null, chosenViewMode: null, viewModeError: '',
        celebration: null, celebrationTimer: null, celebrationAckTimer: null, celebrationWatchTimer: null,
        celebrationWaitTimer: null, celebrationWaiting: null, celebrationSeen: {}, celebrationContext: null,
        pendingRefresh: false, draftDigits: '', draftMode: 'balance_growth',
        savedDigits: '', savedMode: 'balance_growth', invalid: '', selected: null,
        pickerOpen: false, localError: '', feedback: '', disposed: false,
        modeFilter: 'all', modePickerOpen: false, modeAccountContext: null,
        vehicleFilter: 'all', vehiclePickerOpen: false, vehicleTimer: null, vehicleAttempts: 0,
        vehicleRequestId: 0, vehicleRequest: null, vehicleExpected: null, vehicleSelection: null, vehicleFeedback: '',
        callbackId: null, pasteExpected: false, pasteSelection: null, rejectedRaw: null,
        domWait: null, startScheduled: false, engineReady: false, domReady: !!window.isDomBuilt,
        headerDrag: null, circleHovered: false, circleHideTimer: null, circleKeyboard: false,
        nativeGeometry: '', announcedGeometry: '', windowPosition: null,
        lastClient: null, nativeVerified: false, sizingTimer: null,
        sizingAttempts: 0, sizingGeneration: 0,
        archiveOpen: false, archivePicker: null, archiveDay: null, archiveMode: 'all', archiveVehicle: 'all',
        archiveRequestId: 0, archiveRequest: null, archiveExpected: null, archiveSelection: null, archiveSelected: null,
        archiveTimer: null, archiveAttempts: 0, archiveFeedback: '', archiveContext: null, archiveModeGroups: [], archiveVehicleGroups: [],
        historySaved: null,
        historyPendingReset: false, historyConfirm: false, historyFeedback: '', historyGeneration: null
    };
    var root = document.getElementById('credit-ledger-view');
    var nodes = {};
    var ids = ['language-es', 'language-en', 'language-status', 'language-retry', 'language-controls',
        'close', 'refresh', 'message', 'backend-error', 'net-label',
        'net-total', 'battle-count', 'goal-base', 'goal-base-status', 'balance', 'goal-remaining', 'goal-remaining-status', 'base-note',
        'target', 'target-up', 'target-down', 'save-goal', 'reset-goal', 'draft-status', 'input-error', 'progress-text', 'goal-title', 'goal-accumulated',
        'percent', 'meter', 'fill', 'remaining', 'estimate', 'goal-since',
        'goal-progress', 'celebration-sparks', 'goal-celebration-sparks',
        'history-toggle', 'history-label', 'history-options', 'history-list', 'history-menu', 'gross', 'repair',
        'mode-toggle', 'mode-label', 'mode-icon', 'mode-options', 'mode-list', 'mode-menu',
        'vehicle-toggle', 'vehicle-label', 'vehicle-icon', 'vehicle-options', 'vehicle-list', 'vehicle-menu', 'vehicle-status', 'vehicle-retry',
        'reserve-personal', 'reserve-clan', 'reserve-note',
        'history-settings-status', 'history-reset', 'history-confirmation', 'history-confirm-note',
        'history-confirm', 'history-cancel',
        'ammo', 'consumables', 'other', 'other-row', 'detail-net', 'history-empty', 'detail-rewards', 'detail-vehicles', 'detail-mode',
        'wallet-period', 'wallet-base', 'wallet-battles', 'wallet-external', 'wallet-other', 'wallet-total',
        'rewards-list', 'content', 'window', 'drag-bar', 'details', 'back-widget',
        'widget', 'widget-drag-bar', 'widget-details', 'widget-close', 'widget-chart',
        'widget-percent', 'widget-progress', 'widget-status', 'widget-meter', 'widget-fill', 'widget-period', 'widget-balance',
        'minimized', 'minimized-drag-bar', 'minimized-restore', 'minimized-move', 'minimized-target', 'minimized-goal-label',
        'archive-toggle', 'archive-chevron', 'archive-panel', 'archive-status', 'archive-filters', 'archive-count', 'archive-retry',
        'archive-battles', 'archive-battle-options', 'archive-battle-list', 'archive-detail-title', 'archive-reserve-note', 'archive-extra',
        'archive-gross', 'archive-personal', 'archive-clan', 'archive-repair', 'archive-ammo', 'archive-consumables', 'archive-other', 'archive-net'];
    var archiveKinds = ['day', 'mode', 'vehicle'], archiveIndex, archivePart;
    for (archiveIndex = 0; archiveIndex < archiveKinds.length; archiveIndex += 1) {
        for (archivePart = 0; archivePart < 6; archivePart += 1) {
            ids.push('archive-' + archiveKinds[archiveIndex] + '-' + ['toggle', 'icon', 'label', 'menu', 'options', 'list'][archivePart]);
        }
    }
    var i;
    for (i = 0; i < ids.length; i += 1) {
        nodes[ids[i]] = document.getElementById('lc-' + ids[i]);
    }
    var bridgeEngine = window.engine || null;
    var bridgeViewEnv = window.viewEnv || null;
    // Match the native Gameface bootstrap: DOM dimensions must be committed
    // immediately when Wulf asks the view to calculate its initial size.
    if (bridgeEngine && typeof bridgeEngine.enableImmediateLayout === 'function') {
        bridgeEngine.enableImmediateLayout(true);
    }
    var scrollers = [];
    var layoutPending = false;

    function nativeView() { return !!(bridgeViewEnv && typeof bridgeViewEnv.resizeViewPx === 'function'); }
    function nativeSize() {
        var value;
        if (state.engineReady && bridgeViewEnv && typeof bridgeViewEnv.getViewSizePx === 'function') {
            try {
                value = bridgeViewEnv.getViewSizePx();
                return {width:Number(value.width || value.x || value[0] || 0),
                    height:Number(value.height || value.y || value[1] || 0)};
            } catch (ignore) { /* No native surface has been assigned yet. */ }
        }
        return {width:0,height:0};
    }
    function sameSize(size, width, height) {
        return size && Math.abs(size.width - width) <= 1 && Math.abs(size.height - height) <= 1;
    }
    function clientSize() {
        var value;
        if (state.engineReady && bridgeViewEnv && typeof bridgeViewEnv.getClientSizePx === 'function') {
            try {
                value = bridgeViewEnv.getClientSizePx();
                var width = value.width || value.x || value[0];
                var height = value.height || value.y || value[1];
                if (width >= 280 && height >= 180) {
                    state.lastClient = {width:width,height:height};
                    return state.lastClient;
                }
            } catch (ignore) { /* The native view is not ready yet. */ }
        }
        // A native view starts at 0/256px. Its viewport is not the game client.
        if (nativeView()) { return state.lastClient || {width:1280,height:1080}; }
        return {width:window.innerWidth || document.documentElement.clientWidth || 1100,
            height:window.innerHeight || document.documentElement.clientHeight || 850};
    }
    function fitWindow(forceNative) {
        var client = clientSize();
        var widget = state.viewMode === 'widget';
        var minimized = state.viewMode === 'minimized';
        var width = minimized ? 184 : Math.max(280, Math.min(widget ? 624 : 1040, client.width - (widget ? 32 : 48)));
        var height = minimized ? 144 : widget ? Math.max(156, Math.min(width < 480 ? 232 : 208, client.height - 32)) : Math.max(260, Math.min(976, client.height - 48));
        var geometry = [state.viewMode, client.width, client.height, width, height].join(':');
        var actual = nativeSize();
        var nativeWindow = state.payload && state.payload.window;
        var announcement;
        renderViewMode();
        nodes.window.style.width = width + 'px';
        nodes.window.style.height = height + 'px';
        if (nativeView()) {
            // Give C++ an intrinsic size before onDomBuilt or its size timeout.
            // Do not let a 100% root depend on the still unmeasured viewport.
            document.documentElement.style.width = width + 'px';
            document.documentElement.style.height = height + 'px';
            document.body.style.width = width + 'px';
            document.body.style.height = height + 'px';
            root.style.width = width + 'px'; root.style.height = height + 'px';
        } else {
            document.documentElement.style.width = '100%'; document.documentElement.style.height = '100%';
            document.body.style.width = '100%'; document.body.style.height = '100%';
            root.style.width = '100%'; root.style.height = '100%';
        }
        if (state.engineReady && nativeView() && (forceNative === true || state.nativeGeometry !== geometry ||
                !sameSize(actual, width, height) || (nativeWindow && nativeWindow.ready && !sameSize(nativeWindow, width, height)))) {
            state.nativeGeometry = geometry;
            // The native window is bounded by its content, rather than a
            // fullscreen transparent surface intercepting the garage.
            bridgeViewEnv.resizeViewPx(width, height);
            actual = nativeSize();
        }
        state.nativeVerified = !!(nativeWindow && nativeWindow.ready && sameSize(actual, width, height) && sameSize(nativeWindow, width, height));
        announcement = [geometry, state.nativeVerified, actual.width, actual.height].join(':');
        if (state.connected && nativeView() && state.announcedGeometry !== announcement) {
            state.announcedGeometry = announcement;
            invoke('onLayoutReady', {clientWidth:client.width,clientHeight:client.height,width:width,height:height,
                nativeWidth:actual.width,nativeHeight:actual.height,phase:state.nativeVerified ? 'verified' : 'requested',viewMode:state.viewMode});
        } else if (!nativeView() && state.windowPosition) { movePreview(state.windowPosition.x, state.windowPosition.y); }
        fitSummaryGrid();
        updateScrollers();
        renderGoalCompletion();
    }
    function fitSummaryGrid() {
        var summary = root.querySelector('.lc-summary');
        if (!summary || !summary.clientWidth) { return; }
        var cards = summary.querySelectorAll('.lc-stat');
        var outerWidth = nodes.window.clientWidth;
        var columns = outerWidth <= 600 ? 1 : outerWidth <= 1000 ? 2 : 4;
        var gap = 16;
        var width = (summary.clientWidth - gap * (columns - 1)) / columns;
        var index;
        for (index = 0; index < cards.length; index += 1) {
            cards[index].style.width = width + 'px';
            cards[index].style.marginLeft = index % columns ? gap + 'px' : '0px';
            cards[index].style.marginBottom = columns < 4 ? '16px' : '0px';
        }
    }
    function nextSizingFrame(callback) {
        if (typeof window.requestAnimationFrame === 'function') { window.requestAnimationFrame(callback); }
        else { window.setTimeout(callback, 16); }
    }
    function queueNativeSizeCheck() {
        if (state.disposed || !state.connected || !state.domReady || !nativeView() ||
                state.nativeVerified || state.sizingTimer !== null || state.sizingAttempts >= 32) { return; }
        state.sizingTimer = window.setTimeout(function () {
            state.sizingTimer = null;
            if (state.disposed) { return; }
            state.sizingAttempts += 1;
            fitWindow();
            queueNativeSizeCheck();
        }, 250);
    }
    function settleNativeSize() {
        if (state.disposed || !state.connected || !state.domReady || !nativeView()) { return; }
        state.sizingAttempts = 0;
        state.sizingGeneration += 1;
        var generation = state.sizingGeneration;
        var passes = 0;
        function reassert() {
            if (state.disposed || generation !== state.sizingGeneration) { return; }
            fitWindow(true);
            passes += 1;
            if (passes < 3) { nextSizingFrame(reassert); }
        }
        // Wulf can ignore a resize issued before its first measured frame.
        // Reaffirm after two layout frames, then verify the real C++ surface.
        nextSizingFrame(function () { nextSizingFrame(reassert); });
        queueNativeSizeCheck();
    }
    function onNativeLoaded() { fitWindow(true); settleNativeSize(); }
    function onNativeTextureReady() { fitWindow(); queueNativeSizeCheck(); }
    function onClientSizeChanged() { fitWindow(true); settleNativeSize(); }
    function movePreview(x, y) {
        var client = clientSize();
        var rect = nodes.window.getBoundingClientRect();
        x = Math.max(0, Math.min(Math.max(0, client.width - rect.width), x));
        y = Math.max(0, Math.min(Math.max(0, client.height - rect.height), y));
        state.windowPosition = {x:x,y:y};
        nodes.window.style.position = 'absolute';
        nodes.window.style.left = x + 'px';
        nodes.window.style.top = y + 'px';
    }
    function nativeMove(on) {
        // Wulf's own decorator uses GFViewEventProxy MOVE (16).
        bridgeViewEnv.handleViewEvent({__Type:'GFViewEventProxy',type:16,isMouseEvent:true,on:on});
    }
    function clearCircleHideTimer() {
        if (state.circleHideTimer !== null) { window.clearTimeout(state.circleHideTimer); state.circleHideTimer = null; }
    }
    function renderCircleHandle() {
        setClass(nodes.minimized, 'lc-circle-hover', state.circleHovered);
        setClass(nodes.minimized, 'lc-circle-dragging', !!state.headerDrag && state.viewMode === 'minimized');
        setClass(nodes.minimized, 'lc-circle-keyboard', state.circleKeyboard);
    }
    function enterCircle() {
        clearCircleHideTimer(); state.circleHovered = true; renderCircleHandle();
    }
    function leaveCircle() {
        clearCircleHideTimer();
        // Bridge the short gap between the disk and its move handle.
        state.circleHideTimer = window.setTimeout(function () {
            state.circleHideTimer = null; state.circleHovered = false; renderCircleHandle();
        }, 160);
    }
    function clearCircleInteraction() {
        stopWindowMove();
        clearCircleHideTimer(); state.circleHovered = false; state.circleKeyboard = false; renderCircleHandle();
    }
    function startWindowMove(event) {
        var rect;
        if ((event.button !== undefined && event.button !== 0) || inside(event.target, nodes.close) ||
                inside(event.target, nodes['widget-close']) || inside(event.target, nodes['widget-details']) ||
                inside(event.target, nodes['back-widget']) || inside(event.target, nodes['language-controls']) ||
                inside(event.target, nodes['minimized-restore'])) { return; }
        event.preventDefault(); event.stopPropagation();
        rect = nodes.window.getBoundingClientRect();
        state.headerDrag = {native:!!(bridgeViewEnv && typeof bridgeViewEnv.handleViewEvent === 'function'),
            x:event.clientX,y:event.clientY,left:rect.left,top:rect.top};
        renderCircleHandle();
        if (state.headerDrag.native) {
            if (typeof bridgeViewEnv.setTrackMouseOnStage === 'function') { bridgeViewEnv.setTrackMouseOnStage(true); }
            nativeMove(true);
            if (typeof bridgeViewEnv.setEventHandled === 'function') { bridgeViewEnv.setEventHandled(); }
        }
    }
    function updateWindowMove(event) {
        var drag = state.headerDrag;
        if (drag && !drag.native) { movePreview(drag.left + event.clientX - drag.x, drag.top + event.clientY - drag.y); }
    }
    function stopWindowMove() {
        var drag = state.headerDrag;
        state.headerDrag = null;
        renderCircleHandle();
        if (drag && drag.native) {
            try { nativeMove(false); } finally {
                if (typeof bridgeViewEnv.setTrackMouseOnStage === 'function') { bridgeViewEnv.setTrackMouseOnStage(false); }
            }
        }
    }
    function updateScrollers() {
        var index;
        for (index = 0; index < scrollers.length; index += 1) { scrollers[index].update(); }
    }
    function queueLayout() {
        if (layoutPending || state.disposed) { return; }
        layoutPending = true;
        function done() { layoutPending = false; updateScrollers(); }
        if (typeof window.requestAnimationFrame === 'function') {
            window.requestAnimationFrame(function () { window.requestAnimationFrame(done); });
        } else { done(); }
    }
    function scrollControl(viewport, track, thumb) {
        var drag = null;
        var controller = {};
        function maximum() { return Math.max(0, viewport.scrollHeight - viewport.clientHeight); }
        function metrics() {
            var rect = track.getBoundingClientRect();
            var height = rect.height || track.clientHeight;
            var size = Math.min(height, Math.max(26, height * viewport.clientHeight / Math.max(1, viewport.scrollHeight)));
            return {height: height, size: size, range: Math.max(0, height - size)};
        }
        function update() {
            var max = maximum();
            var sizes = metrics();
            show(track, max > 1 && viewport.clientHeight > 0);
            thumb.style.height = sizes.size + 'px';
            thumb.style.top = (max > 0 ? sizes.range * viewport.scrollTop / max : 0) + 'px';
            track.setAttribute('aria-valuemin', '0');
            track.setAttribute('aria-valuemax', String(Math.round(max)));
            track.setAttribute('aria-valuenow', String(Math.round(viewport.scrollTop)));
        }
        function move(value) { viewport.scrollTop = Math.max(0, Math.min(maximum(), value)); update(); }
        function wheel(event) {
            // The raw wheel event in this WoT Gameface host has the opposite
            // deltaY sign to Chromium. Legacy wheelDelta already means up.
            var delta = typeof event.deltaY === 'number' ? (nativeView() ? -event.deltaY : event.deltaY) : -event.wheelDelta;
            if (!isFinite(delta) || delta === 0) { return; }
            if (event.deltaMode === 1) { delta *= 28; }
            if (event.deltaMode === 2) { delta *= viewport.clientHeight; }
            if (nativeView() && Math.abs(delta) < 28) { delta = delta < 0 ? -42 : 42; }
            event.preventDefault();
            event.stopPropagation();
            move(viewport.scrollTop + delta);
        }
        viewport.addEventListener('wheel', wheel, false);
        track.addEventListener('wheel', wheel, false);
        if (!('onwheel' in viewport)) { viewport.addEventListener('mousewheel', wheel, false); track.addEventListener('mousewheel', wheel, false); }
        viewport.addEventListener('scroll', update, false);
        thumb.addEventListener('mousedown', function (event) {
            event.preventDefault(); event.stopPropagation();
            drag = {y: event.clientY, top: viewport.scrollTop};
        });
        track.addEventListener('mousedown', function (event) {
            if (event.target === thumb) { return; }
            var sizes = metrics();
            var y = event.clientY - track.getBoundingClientRect().top - sizes.size / 2;
            event.preventDefault(); event.stopPropagation();
            move(sizes.range > 0 ? y / sizes.range * maximum() : 0);
        });
        function mouseMove(event) {
            var sizes;
            if (!drag) { return; }
            sizes = metrics();
            event.preventDefault();
            move(drag.top + (event.clientY - drag.y) * maximum() / Math.max(1, sizes.range));
        }
        function mouseUp() { drag = null; }
        function key(event) {
            if (event.target !== viewport && event.target !== track) { return; }
            var name = keyName(event);
            var delta = name === 'ArrowDown' ? 36 : name === 'ArrowUp' ? -36 : name === 'PageDown' ? viewport.clientHeight : name === 'PageUp' ? -viewport.clientHeight : null;
            if (delta !== null || name === 'Home' || name === 'End') {
                event.preventDefault(); event.stopPropagation();
                move(name === 'Home' ? 0 : name === 'End' ? maximum() : viewport.scrollTop + delta);
            }
        }
        document.addEventListener('mousemove', mouseMove, false);
        document.addEventListener('mouseup', mouseUp, false);
        track.addEventListener('keydown', key, false);
        viewport.addEventListener('keydown', key, false);
        controller.update = update;
        controller.dispose = function () {
            document.removeEventListener('mousemove', mouseMove, false);
            document.removeEventListener('mouseup', mouseUp, false);
        };
        scrollers.push(controller);
        return controller;
    }

    function validLanguage(value) { return value === 'es' || value === 'en'; }
    function t(source, parameters) {
        var key = source, output, name;
        if (typeof source !== 'string') { return source; }
        // Pending feedback may have been created before the language changed.
        if (!translations.hasOwnProperty(key) && reverseTranslations.hasOwnProperty(source)) {
            key = reverseTranslations[source];
        }
        output = state.language === 'en' && translations.hasOwnProperty(key) ? translations[key] : key;
        if (parameters) {
            for (name in parameters) {
                if (parameters.hasOwnProperty(name)) { output = output.split('{' + name + '}').join(String(parameters[name])); }
            }
        }
        return output;
    }
    function setText(node, value, properName) { node.textContent = properName ? value : t(value); }
    function renderLanguage() {
        var elements = document.querySelectorAll('[data-l10n], [data-l10n-title], [data-l10n-aria-label]');
        var index, element, key;
        document.documentElement.setAttribute('lang', state.language);
        document.title = t('Contabilidad de cr\u00e9ditos');
        for (index = 0; index < elements.length; index += 1) {
            element = elements[index]; key = element.getAttribute('data-l10n');
            if (key !== null) { element.textContent = t(key); }
            key = element.getAttribute('data-l10n-title');
            if (key !== null) { element.setAttribute('title', t(key)); }
            key = element.getAttribute('data-l10n-aria-label');
            if (key !== null) { element.setAttribute('aria-label', t(key)); }
        }
        setClass(nodes['language-es'], 'lc-language-active', state.language === 'es');
        setClass(nodes['language-en'], 'lc-language-active', state.language === 'en');
        nodes['language-es'].setAttribute('aria-pressed', state.language === 'es' ? 'true' : 'false');
        nodes['language-en'].setAttribute('aria-pressed', state.language === 'en' ? 'true' : 'false');
        nodes['language-controls'].setAttribute('aria-busy', state.languagePending ? 'true' : 'false');
        disable(nodes['language-es'], !state.connected);
        disable(nodes['language-en'], !state.connected);
        setText(nodes['language-status'], state.languagePending ? 'Guardando idioma\u2026' : state.languageFeedback);
        show(nodes['language-status'], !!state.languagePending || !!state.languageFeedback);
        show(nodes['language-retry'], state.languageRetry !== null && !state.languagePending);
        disable(nodes['language-retry'], !state.connected || !!state.languagePending);
    }
    function setLanguage(language) {
        var selection = caretInfo(nodes.target), raw = nodes.target.value;
        var start = digitsBefore(raw, selection.start), end = digitsBefore(raw, selection.end);
        state.language = validLanguage(language) ? language : 'es';
        if (!state.invalid && /^[0-9.,]*$/.test(raw)) {
            nodes.target.value = groupDigits(raw.replace(/[^0-9]/g, ''));
            setCaret(nodes.target, caretAfterDigits(nodes.target.value, start), caretAfterDigits(nodes.target.value, end));
        }
    }
    function clearLanguageTimer() {
        if (state.languageTimer !== null) { window.clearTimeout(state.languageTimer); state.languageTimer = null; }
    }
    function failLanguage(source) {
        var requested = state.languagePending && state.languagePending.language;
        clearLanguageTimer(); state.languagePending = null;
        state.languageRetry = requested || state.languageRetry;
        state.languageFeedback = source;
        setLanguage(state.savedLanguage);
    }
    function chooseLanguage(language) {
        if (!state.connected || !validLanguage(language) ||
                (language === state.language && !state.languagePending && state.languageRetry === null)) { return; }
        clearLanguageTimer(); state.languageRequestId += 1;
        var request = {language:language, request_id:state.languageRequestId};
        state.languagePending = request; state.languageFeedback = ''; state.languageRetry = null;
        var oldContentScroll = nodes.content.scrollTop;
        setLanguage(language); renderData(); nodes.content.scrollTop = oldContentScroll;
        if (!invoke('onSetLanguage', request)) {
            failLanguage('No se pudo guardar el idioma. Puedes reintentar.'); renderData(); return;
        }
        // A mock or native bridge may acknowledge synchronously during invoke.
        if (!state.languagePending || state.languagePending.request_id !== request.request_id) { return; }
        state.languageTimer = window.setTimeout(function () {
            state.languageTimer = null;
            if (!state.disposed && state.languagePending && state.languagePending.request_id === request.request_id) {
                failLanguage('El idioma no se guard\u00f3 a tiempo. Puedes reintentar.'); renderData();
            }
        }, 6000);
    }
    function acceptLanguage(payload) {
        var incoming = validLanguage(payload.language) ? payload.language : 'es';
        var acknowledgement = payload.language_selection;
        var id = acknowledgement ? acknowledgementId(acknowledgement.request_id) : null;
        if (id !== null) { state.languageRequestId = Math.max(state.languageRequestId, id); }
        if (!state.languageLoaded) {
            state.languageLoaded = true; state.savedLanguage = incoming;
            if (!state.languagePending) { setLanguage(incoming); }
        }
        if (state.languagePending) {
            if (id !== state.languagePending.request_id || acknowledgement.requested_language !== state.languagePending.language) { return; }
            if (acknowledgement.available === true && incoming === state.languagePending.language) {
                clearLanguageTimer(); state.languageAcceptedId = id; state.savedLanguage = incoming;
                state.languagePending = null; state.languageRetry = null; state.languageFeedback = 'Idioma guardado.';
                setLanguage(incoming);
            } else if (acknowledgement.available === false) {
                state.savedLanguage = incoming;
                failLanguage('No se pudo guardar el idioma. Puedes reintentar.');
            }
        } else if (id !== null && id >= state.languageAcceptedId && id === state.languageRequestId) {
            // Honor a late success after a timeout, without accepting older requests.
            if (acknowledgement.available === true && acknowledgement.requested_language === incoming) {
                state.languageAcceptedId = id; state.savedLanguage = incoming;
                state.languageRetry = null; state.languageFeedback = 'Idioma guardado.'; setLanguage(incoming);
            }
        }
    }
    function setClass(node, name, active) {
        var current = ' ' + node.className + ' ';
        var token = ' ' + name + ' ';
        if (active && current.indexOf(token) < 0) { node.className += ' ' + name; }
        if (!active && current.indexOf(token) >= 0) {
            node.className = current.replace(token, ' ').replace(/^\s+|\s+$/g, '');
        }
    }
    function show(node, visible) { setClass(node, 'lc-hidden', !visible); }
    function disable(node, disabled) {
        node.disabled = disabled;
        node.setAttribute('aria-disabled', disabled ? 'true' : 'false');
        setClass(node, 'lc-disabled', disabled);
    }
    function number(value) {
        return typeof value === 'number' && isFinite(value) ? value : null;
    }
    function integerText(value) {
        var amount = number(value);
        var rounded;
        if (amount === null) { return '\u2014'; }
        rounded = Math.round(Math.abs(amount));
        return (amount < 0 ? '-' : '') + groupDigits(String(rounded));
    }
    function signedText(value) {
        var amount = number(value);
        var rounded;
        if (amount === null) { return '\u2014'; }
        rounded = Math.round(Math.abs(amount));
        return (amount < 0 ? '-' : '+') + groupDigits(String(rounded));
    }
    function groupDigits(digits) {
        return digits.replace(/\B(?=([0-9]{3})+(?![0-9]))/g, state.language === 'en' ? ',' : '.');
    }
    function cleanLeadingZeros(digits) { return digits.replace(/^0+(?=[0-9])/, ''); }
    function validDigits(digits) {
        return /^[0-9]+$/.test(digits) &&
            (digits.length < MAX_DIGITS.length ||
             (digits.length === MAX_DIGITS.length && digits <= MAX_DIGITS));
    }
    function digitsOfNumber(value) {
        var amount = number(value);
        if (amount === null || amount < 0 || Math.floor(amount) !== amount || amount > 9007199254740991) { return '0'; }
        return String(amount);
    }
    function colorNumber(node, value) {
        var amount = number(value);
        setClass(node, 'lc-positive', amount !== null && amount > 0);
        setClass(node, 'lc-negative', amount !== null && amount < 0);
        setClass(node, 'lc-muted', amount === null);
    }
    function expenseText(value) {
        var amount = number(value);
        if (amount === null) { return '\u2014'; }
        return amount === 0 ? '0' : '-' + integerText(Math.abs(amount));
    }
    function colorExpense(node, value) {
        var amount = number(value);
        colorNumber(node, amount === null ? null : -Math.abs(amount));
    }
    function setAmountParts(node, parts) {
        var index, part, amount;
        setText(node, '');
        setClass(node, 'lc-amount-line', true);
        for (index = 0; index < parts.length; index += 1) {
            part = parts[index];
            amount = document.createElement('span');
            if (typeof part === 'string') {
                amount.className = 'lc-text-part';
                setText(amount, part);
            } else {
                amount.className = 'lc-amount';
                setText(amount, part.signed ? signedText(part.value) : integerText(part.value));
                colorNumber(amount, part.value);
            }
            node.appendChild(amount);
        }
    }
    function percentText(value) {
        var text = (Math.round(value * 10) / 10).toFixed(1);
        return (state.language === 'en' ? text : text.replace('.', ',')) + ' %';
    }
    function currentGoal() { return state.payload && state.payload.goal ? state.payload.goal : {}; }
    function ready() { return !!(state.payload && state.payload.ready === true); }
    function goalBusy() { return state.pendingSave || state.pendingGoalReset !== null; }
    function mutationPending() { return goalBusy() || state.historyPendingReset; }
    function resetGeneration(goal) {
        var generation = number(goal.reset_generation);
        return generation !== null && generation >= 0 && Math.floor(generation) === generation ? generation : 0;
    }
    function activeGoal(goal) {
        return goal.active === true || (number(goal.baseline) !== null && goal.baseline >= 0 && number(goal.target) !== null && goal.target > 0);
    }
    function completionReferenceMatches(event) {
        var payload = state.payload || {}, goal = currentGoal();
        var target = number(goal.target), current = number(goal.current);
        return !!(event && ready() && typeof event.account_context === 'string' &&
            event.account_context === payload.account_context && target !== null && target > 0 &&
            goal.active !== false && current !== null && current >= target &&
            number(event.target) === target && number(event.reset_generation) !== null &&
            event.reset_generation === resetGeneration(goal));
    }
    function completionWindowBounds() {
        var rect = nodes.window.getBoundingClientRect();
        return {width:rect.width || nodes.window.offsetWidth || rect.right - rect.left,
            height:rect.height || nodes.window.offsetHeight || rect.bottom - rect.top};
    }
    function completionSurfaceVisible() {
        var rect, viewport, nativeWindow = state.payload && state.payload.window;
        if (document.hidden === true || document.visibilityState === 'hidden' || state.pendingViewMode !== null) { return false; }
        if (state.payload && state.payload.view_mode !== state.viewMode) { return false; }
        if (nativeView()) {
            rect = completionWindowBounds();
            if (!state.nativeVerified || !nativeWindow || nativeWindow.ready !== true ||
                    !sameSize(nativeSize(), rect.width, rect.height) || !sameSize(nativeWindow, rect.width, rect.height)) { return false; }
        }
        if (state.viewMode === 'widget') { return true; }
        if (state.viewMode !== 'details') { return false; }
        // Keep a completion pending while its goal is scrolled out of sight.
        rect = nodes.remaining.getBoundingClientRect();
        viewport = nodes.content.getBoundingClientRect();
        return (rect.height || nodes.remaining.clientHeight || rect.bottom - rect.top) > 0 &&
            rect.bottom > viewport.top + 4 && rect.top < viewport.bottom - 4;
    }
    function completionPresentationKey(event) {
        var payload = state.payload || {}, display = payload.completion_display, rect;
        if (state.disposed || !state.connected || mutationPending() || state.viewModeError || state.localError || payload.error ||
                !completionReferenceMatches(event) || typeof event.id !== 'string' || !/^[0-9a-f]{32}$/.test(event.id) ||
                !display || display.ready !== true || display.account_context !== payload.account_context ||
                number(display.generation) === null || display.generation < 0 || Math.floor(display.generation) !== display.generation ||
                !completionSurfaceVisible()) { return null; }
        rect = completionWindowBounds();
        return [event.account_context, event.id, display.generation, state.viewMode,
            Math.round(rect.width), Math.round(rect.height), state.nativeGeometry].join(':');
    }
    function clearCompletionSparks() {
        setText(nodes['celebration-sparks'], ''); show(nodes['celebration-sparks'], false);
        setText(nodes['goal-celebration-sparks'], ''); show(nodes['goal-celebration-sparks'], false);
    }
    function cancelGoalCompletion() {
        if (state.celebrationTimer !== null) { window.clearTimeout(state.celebrationTimer); state.celebrationTimer = null; }
        if (state.celebrationAckTimer !== null) { window.clearTimeout(state.celebrationAckTimer); state.celebrationAckTimer = null; }
        if (state.celebrationWatchTimer !== null) { window.clearTimeout(state.celebrationWatchTimer); state.celebrationWatchTimer = null; }
        if (state.celebrationWaitTimer !== null) { window.clearTimeout(state.celebrationWaitTimer); state.celebrationWaitTimer = null; }
        state.celebrationWaiting = null;
        state.celebration = null;
        clearCompletionSparks();
        setClass(nodes.widget, 'lc-widget-celebrating', false);
        setClass(nodes['goal-progress'], 'lc-goal-celebrating', false);
    }
    function reducedCompletionMotion() {
        try { return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
        catch (ignore) { return false; }
    }
    function createCompletionSparks(surface) {
        var layer = surface === 'widget' ? nodes['celebration-sparks'] : nodes['goal-celebration-sparks'];
        var burst, particle, group, index;
        // Sixteen original particles; no frame loop, randomness or image assets.
        for (group = 0; group < 2; group += 1) {
            burst = document.createElement('div');
            burst.className = 'lc-spark-burst' + (group === 1 ? ' lc-spark-burst-second' : '');
            for (index = 0; index < 8; index += 1) {
                particle = document.createElement('div');
                particle.className = 'lc-spark lc-spark-' + index + (index % 3 === 0 ? ' lc-spark-warm' : '');
                burst.appendChild(particle);
            }
            layer.appendChild(burst);
        }
        show(layer, true);
    }
    function acknowledgeGoalCompletion(event) {
        var model = window.model, command = model && model.onAcknowledgeGoalCompletion;
        var args = {id:event.id, account_context:event.account_context, presentation_generation:event.presentation_generation};
        // A decorative acknowledgement must not replace useful finance errors.
        try {
            if (typeof command === 'function') { command.call(model, args); }
            else if (command && typeof command.value === 'function') { command.value.call(command, args); }
        } catch (ignore) { /* The durable pending event can be retried by a later view. */ }
    }
    function scheduleCompletionAcknowledgement(event) {
        state.celebrationAckTimer = window.setTimeout(function () {
            var pending = state.payload && state.payload.goal_completion;
            state.celebrationAckTimer = null;
            if (!state.disposed && pending && pending.id === event.id &&
                    pending.account_context === event.account_context && completionReferenceMatches(event) &&
                    state.payload.completion_display && state.payload.completion_display.ready === true &&
                    state.payload.completion_display.generation === event.presentation_generation) {
                // One retry if saving the acknowledgement failed; no repeated celebration.
                acknowledgeGoalCompletion(event);
            }
        }, 1000);
    }
    function watchGoalCompletion() {
        state.celebrationWatchTimer = window.setTimeout(function () {
            state.celebrationWatchTimer = null;
            if (!state.celebration || state.disposed) { return; }
            renderGoalCompletion();
            if (state.celebration) { watchGoalCompletion(); }
        }, 200);
    }
    function startGoalCompletion(waiting) {
        var event = state.payload && state.payload.goal_completion, current;
        if (!waiting || completionPresentationKey(event) !== waiting.key) { renderGoalCompletion(); return; }
        current = {id:event.id, account_context:event.account_context, target:event.target,
            reset_generation:event.reset_generation, surface:state.viewMode, key:waiting.key,
            presentation_generation:state.payload.completion_display.generation};
        state.celebration = current;
        if (!reducedCompletionMotion()) { createCompletionSparks(current.surface); }
        state.celebrationTimer = window.setTimeout(function () {
            var latest = state.payload && state.payload.goal_completion;
            state.celebrationTimer = null;
            if (state.celebration !== current || completionPresentationKey(latest) !== current.key) {
                cancelGoalCompletion(); if (!state.disposed) { renderData(); } return;
            }
            // Acknowledge only after the full effect was visible in a stable garage.
            state.celebrationSeen[current.account_context + ':' + current.id] = {
                id:current.id, account_context:current.account_context, target:current.target,
                reset_generation:current.reset_generation, presentation_generation:current.presentation_generation,
                confirmed:false};
            cancelGoalCompletion();
            if (!state.disposed) {
                renderData(); acknowledgeGoalCompletion(current);
                if (!state.disposed && completionReferenceMatches(current)) { scheduleCompletionAcknowledgement(current); }
            }
        }, 2800);
        watchGoalCompletion();
        renderGoalCompletion();
    }
    function renderGoalCompletion() {
        var payload = state.payload || {}, event = payload.goal_completion, current = state.celebration;
        var context = typeof payload.account_context === 'string' ? payload.account_context : null;
        var key, seenKey, seen, seenName, display = payload.completion_display, restore = false, waiting;
        if (context !== state.celebrationContext) {
            restore = !!current; cancelGoalCompletion(); state.celebrationSeen = {}; state.celebrationContext = context; current = null;
        }
        key = completionPresentationKey(event);
        if (current && current.key !== key) {
            cancelGoalCompletion(); current = null; restore = true;
        }
        if (state.celebrationWaiting && state.celebrationWaiting.key !== key) { cancelGoalCompletion(); }
        seenKey = event && context + ':' + event.id;
        seen = seenKey && state.celebrationSeen[seenKey];
        if (seen && !seen.confirmed && display && display.account_context === context &&
                number(display.generation) !== null && display.generation !== seen.presentation_generation) {
            // Native visibility can change just before ACK. Its pending event is still owed to the user.
            delete state.celebrationSeen[seenKey]; seen = null;
        }
        if (event === null && display && display.ready === true && display.account_context === context) {
            for (seenName in state.celebrationSeen) {
                if (state.celebrationSeen.hasOwnProperty(seenName)) {
                    seen = state.celebrationSeen[seenName];
                    if (!seen.confirmed && completionReferenceMatches(seen)) { seen.confirmed = true; }
                }
            }
        }
        if (!current && key !== null && !state.celebrationSeen[seenKey] && !state.celebrationWaiting) {
            waiting = {key:key}; state.celebrationWaiting = waiting;
            // Garage space, native visibility and dimensions must settle before the full duration begins.
            state.celebrationWaitTimer = window.setTimeout(function () {
                state.celebrationWaitTimer = null;
                if (state.celebrationWaiting !== waiting) { return; }
                state.celebrationWaiting = null; startGoalCompletion(waiting);
            }, 1500);
        }
        if (!current) {
            if (restore) { renderWidget(); renderGoal(); }
            return;
        }
        setClass(nodes.widget, 'lc-widget-celebrating', state.viewMode === 'widget');
        setClass(nodes['goal-progress'], 'lc-goal-celebrating', state.viewMode === 'details');
        if (state.viewMode === 'widget') { setText(nodes['widget-status'], t('\u00a1Meta alcanzada! \u00a1Buen trabajo!')); }
        else if (state.viewMode === 'details') { setText(nodes.remaining, t('\u00a1Meta alcanzada! \u00a1Buen trabajo!')); }
    }
    function validViewMode(mode) { return mode === 'widget' || mode === 'details' || mode === 'minimized'; }
    function renderViewMode() {
        var widget = state.viewMode === 'widget';
        var minimized = state.viewMode === 'minimized';
        show(nodes.widget, widget);
        show(nodes.details, state.viewMode === 'details');
        show(nodes.minimized, minimized);
        setClass(nodes.window, 'lc-view-widget', widget);
        setClass(nodes.window, 'lc-view-details', state.viewMode === 'details');
        setClass(nodes.window, 'lc-view-minimized', minimized);
        if (minimized) {
            nodes.window.removeAttribute('aria-labelledby');
            nodes.window.setAttribute('aria-label', t('Contabilidad de cr\u00e9ditos minimizada'));
        } else {
            nodes.window.removeAttribute('aria-label');
            nodes.window.setAttribute('aria-labelledby', widget ? 'lc-widget-title' : 'lc-title');
        }
        nodes['widget-details'].setAttribute('aria-expanded', state.viewMode === 'details' ? 'true' : 'false');
        disable(nodes['widget-details'], !state.connected);
        disable(nodes['back-widget'], !state.connected);
        disable(nodes['minimized-restore'], !state.connected);
        disable(nodes['minimized-move'], !state.connected);
        nodes['minimized-restore'].setAttribute('title', t(state.viewModeError || 'Mostrar contabilidad de cr\u00e9ditos'));
    }
    function setViewMode(mode) {
        if (!state.connected || !validViewMode(mode) || mode === state.viewMode) { return; }
        stopWindowMove();
        clearCircleInteraction();
        state.viewMode = mode;
        state.pendingViewMode = mode;
        state.chosenViewMode = mode;
        state.viewModeError = '';
        state.nativeVerified = false;
        state.announcedGeometry = '';
        setPicker(false);
        setModePicker(false);
        setVehiclePicker(false);
        if (!state.historyPendingReset) { state.historyConfirm = false; }
        renderViewMode();
        // Keep the user's local choice while an older payload is in flight.
        // This command precedes layout reports for the newly selected mode.
        invoke('onSetViewMode', {mode:mode});
        fitWindow(true);
        settleNativeSize();
        renderData();
    }
    function renderWidget() {
        var payload = state.payload || {};
        var goal = currentGoal();
        var summary = payload.summary || {};
        var available = ready();
        var target = available ? number(goal.target) : null;
        var current = available ? number(goal.current) : null;
        var percent = available ? number(goal.progress_percent) : null;
        var remaining = available ? number(goal.remaining) : null;
        var net = available ? number(summary.net_credits) : null;
        var count = available ? number(summary.battle_count) : null;
        var balance = available ? number(payload.balance) : null;
        var active = target !== null && target > 0 && goal.active !== false;
        var complete = active && current !== null && current >= target;
        var progress = t('Esperando tu cuenta');
        var status = t('El progreso aparecer\u00e1 cuando se sincronice tu saldo.');
        var percentLabel = '\u2014';
        var period = t('Batallas del per\u00edodo ') + signedText(net);
        var explanation = t('Ganancia o p\u00e9rdida de las partidas despu\u00e9s de gastos');
        if (percent !== null) { percent = Math.max(0, Math.min(complete ? 100 : 99.9, percent)); }
        if (available && !active && target !== null) {
            percent = 0;
            percentLabel = '0 %';
            progress = t('Sin meta activa');
            status = t('Configura tu meta en Ver detalles.');
        } else if (active) {
            progress = current === null ? t('Meta: ') + integerText(target) + t(' cr\u00e9ditos') :
                integerText(current) + ' / ' + integerText(target) + t(' cr\u00e9ditos');
            if (current === null || percent === null) {
                percent = null;
                status = t('Esperando el saldo actual para calcular el avance.');
            } else {
                if (complete) { percent = 100; }
                percentLabel = percentText(percent);
                status = complete ? t('Meta alcanzada.') : current < 0 ? t('Tu saldo est\u00e1 por debajo de la base de la meta.') :
                    remaining === null ? t('Avance desde el saldo base de tu meta.') : t('Faltan ') + integerText(Math.max(0, remaining)) + t(' cr\u00e9ditos.');
            }
        } else { percent = null; }
        if (state.viewModeError) { status = state.viewModeError; }
        else if (state.localError || payload.error) { status = t('No se pudo actualizar. Revisa los detalles.'); }
        setText(nodes['widget-percent'], percentLabel);
        setText(nodes['widget-progress'], progress);
        if (active) {
            setAmountParts(nodes['widget-progress'], current === null ? [t('Meta: '), {value:target}, t(' cr\u00e9ditos')] :
                [{value:current}, ' / ', {value:target}, t(' cr\u00e9ditos')]);
        }
        setClass(nodes['widget-progress'], 'lc-widget-progress-long', progress.length > 40);
        colorNumber(nodes['widget-progress'], 0);
        setText(nodes['widget-status'], status);
        if (status === t('Faltan ') + integerText(Math.max(0, remaining)) + t(' cr\u00e9ditos.') && remaining !== null) {
            setAmountParts(nodes['widget-status'], [t('Faltan '), {value:Math.max(0, remaining)}, t(' cr\u00e9ditos.')]);
        }
        nodes['widget-fill'].style.width = (percent === null ? 0 : percent) + '%';
        if (percent === null) { nodes['widget-meter'].removeAttribute('aria-valuenow'); }
        else { nodes['widget-meter'].setAttribute('aria-valuenow', String(percent)); }
        nodes['widget-meter'].setAttribute('aria-valuetext', percent === null ? t('Progreso pendiente de sincronizar') : percentLabel);
        if (count !== null) { period += ' \u00b7 ' + integerText(count) + (count === 1 ? t(' partida') : t(' partidas')); }
        else { period += t(' \u00b7 Partidas pendientes'); }
        setAmountParts(nodes['widget-period'], [t('Batallas del per\u00edodo '), {value:net, signed:true},
            count !== null ? ' \u00b7 ' + integerText(count) + (count === 1 ? t(' partida') : t(' partidas')) : t(' \u00b7 Partidas pendientes')]);
        nodes['widget-period'].setAttribute('title', explanation);
        nodes['widget-period'].setAttribute('aria-label', period + '. ' + explanation);
        setText(nodes['widget-balance'], balance === null ? t('Saldo pendiente') : t('Saldo ') + integerText(balance));
        colorNumber(nodes['widget-balance'], balance);
        setClass(nodes.widget, 'lc-widget-complete', complete);
        setClass(nodes.widget, 'lc-widget-negative', active && current !== null && current < 0);
        renderProgressCircles(available, active, percent, complete, current);
    }
    function renderProgressCircles(available, active, percent, complete, current) {
        // Dash properties belong to SVG paths, rather than circles, in Gameface.
        // Explicit circumference avoids depending on SVG pathLength support.
        var length;
        var known = available && active && percent !== null;
        var value = known ? Math.max(0, Math.min(100, percent)) : 0;
        var label = !available || !active ? '\u2014' : known ?
            (complete ? '100%' : percentText(value).replace(/\s/g, '')) : '\u2014';
        var description = !available ? t('Progreso pendiente de sincronizar') : !active ? t('Sin meta activa') :
            known ? t('Avance de la meta de cr\u00e9ditos') + ': ' + percentText(value) : t('Progreso pendiente de sincronizar');
        var labels = root.querySelectorAll('.lc-progress-circle-label');
        var arcs = root.querySelectorAll('.lc-progress-ring-value');
        var target = available && active ? number(currentGoal().target) : null;
        var targetText = integerText(target);
        if (target !== null && targetText.length > 11) {
            var divisor = target >= 1000000000000 ? 1000000000000 : 1000000;
            var suffix = divisor === 1000000 ? ' M' : state.language === 'en' ? ' T' : ' B';
            targetText = (target / divisor).toFixed(1).replace(/\.0$/, '').replace('.', state.language === 'en' ? '.' : ',') + suffix;
        }
        setText(nodes['minimized-target'], targetText);
        setClass(nodes['minimized-target'], 'lc-minimized-target-long', targetText.length > 9);
        setText(nodes['minimized-goal-label'], t('Meta'));
        if (target !== null) { description += '. ' + t('Meta') + ': ' + integerText(target) + t(' cr\u00e9ditos'); }
        var index, button, action;
        for (index = 0; index < labels.length; index += 1) { setText(labels[index], label); }
        for (index = 0; index < arcs.length; index += 1) {
            length = Number(arcs[index].getAttribute('data-ring-length')) || 213.6283;
            arcs[index].setAttribute('stroke-dashoffset', String(length * (1 - value / 100)));
            arcs[index].style.display = known && value > 0 ? 'block' : 'none';
        }
        setClass(nodes.window, 'lc-circle-complete', known && complete);
        setClass(nodes.window, 'lc-circle-inactive', available && !active);
        setClass(nodes.window, 'lc-circle-negative', active && current !== null && current < 0);
        for (index = 0; index < 3; index += 1) {
            button = index === 0 ? nodes['minimized-restore'] : index === 1 ? nodes['widget-close'] : nodes.close;
            action = t(index === 0 ? 'Mostrar contabilidad de cr\u00e9ditos' : 'Minimizar contabilidad de cr\u00e9ditos');
            button.setAttribute('aria-label', action + '. ' + description);
            button.setAttribute('title', t(state.viewModeError || action) + '. ' + description);
        }
    }
    function updateDirty() {
        state.dirty = state.invalid !== '' || state.draftDigits !== state.savedDigits || state.draftMode !== state.savedMode;
    }
    function renderDraft() {
        var valid = state.invalid === '' && validDigits(state.draftDigits);
        var editable = ready() && !mutationPending();
        var inputValid = valid || (state.invalid === '' && (state.draftDigits === '0' || state.draftDigits === ''));
        var message;
        var active = activeGoal(currentGoal());
        var hasBase = number(currentGoal().baseline) !== null;
        var withoutGoal = state.draftDigits === '0';
        updateDirty();
        nodes.target.disabled = !editable;
        disable(nodes['target-up'], !editable);
        disable(nodes['target-down'], !editable || Number(state.draftDigits || 0) <= 0);
        nodes.target.setAttribute('aria-invalid', inputValid || !state.dirty ? 'false' : 'true');
        setClass(nodes.target, 'lc-target-invalid', !inputValid && state.dirty);
        disable(nodes['save-goal'], !editable || (!withoutGoal && number(state.payload.balance) === null) || !valid);
        setText(nodes['save-goal'], state.pendingSave ? t('Guardando...') : withoutGoal ? (active ? t('Desactivar meta') : t('Guardar sin meta')) : active ? t('Actualizar meta') : hasBase ? t('Reactivar meta') : t('Iniciar meta'));
        disable(nodes['reset-goal'], !editable || !valid || Number(state.draftDigits) <= 0 || number(state.payload.balance) === null);
        setText(nodes['reset-goal'], state.pendingGoalReset ? t('Reiniciando...') : t('Reiniciar meta'));
        message = state.invalid;
        if (!message && state.dirty && !inputValid) {
            message = state.draftDigits.length > MAX_DIGITS.length ||
                (state.draftDigits.length === MAX_DIGITS.length && state.draftDigits > MAX_DIGITS) ?
                t('La meta m\u00e1xima es 9.007.199.254.740.991 cr\u00e9ditos.') :
                t('Escribe una cantidad entera; usa 0 si no quieres una meta.');
        }
        setText(nodes['input-error'], message);
        show(nodes['input-error'], message !== '');
        if (state.pendingGoalReset) { message = t('Reiniciando tu meta desde el saldo actual\u2026'); }
        else if (state.pendingSave) { message = t('Guardando tu meta\u2026'); }
        else if (state.feedback) { message = state.feedback; }
        else if (withoutGoal) { message = t('Guardar 0 desactiva el objetivo. Conserva la base, el avance y el historial.'); }
        else if (active || hasBase) { message = (state.dirty ? t('Cambios sin guardar. ') : '') + t('Conserva lo que ya has acumulado y recalcula el porcentaje.'); }
        else if (state.dirty) { message = t('Cambios sin guardar. El progreso muestra la meta guardada.'); }
        else { message = valid ? t('Inicia tu meta desde el saldo actual, en 0 %.') : t('Escribe una cantidad o 0 para continuar sin meta.'); }
        setText(nodes['draft-status'], message);
    }
    function localizedLabel(value) {
        var source = typeof value === 'string' ? value : '';
        var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        var match, month;
        if (state.language === 'en') {
            match = /^(\d{2})\/(\d{2})(?:\/(\d{4}))?(.*)$/.exec(source);
            if (match && Number(match[2]) >= 1 && Number(match[2]) <= 12) {
                source = String(Number(match[1])) + ' ' + months[Number(match[2]) - 1] + (match[3] ? ' ' + match[3] : '') + match[4];
            }
            return source.replace('hora local', 'local time');
        }
        match = /^(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?: (\d{4}))?(.*)$/.exec(source);
        if (match) {
            month = months.indexOf(match[2]) + 1;
            source = ('0' + match[1]).slice(-2) + '/' + ('0' + month).slice(-2) + (match[3] ? '/' + match[3] : '') + match[4];
        }
        return source.replace('local time', 'hora local');
    }
    function timeLabel(row) {
        return typeof row.time_label === 'string' && row.time_label ? localizedLabel(row.time_label) :
            (typeof row.occurred_at === 'string' ? row.occurred_at.replace('T', ' ').replace('Z', ' UTC') : t('Partida'));
    }
    function gameModeLabel(mode) {
        var code = mode && typeof mode.bonus_type === 'number' ? mode.bonus_type :
            mode && /^mode:[0-9]+$/.test(mode.key || '') ? Number(mode.key.slice(5)) : null;
        var label = mode && typeof mode.label === 'string' ? mode.label.replace(/^\s+|\s+$/g, '').slice(0, 160) : '';
        if (code !== null && modeNames.hasOwnProperty(code)) {
            if (state.language === 'en' || !label) { return t(modeNames[code]); }
            var english = translations[modeNames[code]];
            if (label === english || label === english.replace('Babylon: ', '')) { return modeNames[code]; }
        }
        return label ? t(label).replace(/^Modo de juego ([0-9]+)$/, state.language === 'en' ? 'Game mode $1' : 'Modo de juego $1') : t('Modo no identificado');
    }
    function modeGroups(payload) {
        var groups = payload && Array.isArray(payload.mode_groups) ? payload.mode_groups : [];
        var clean = [], seen = {}, index, group;
        for (index = 0; index < groups.length; index += 1) {
            group = groups[index];
            if (!group || typeof group.key !== 'string' || !/^(mode:[0-9]+|unknown)$/.test(group.key) || seen[group.key] ||
                    typeof group.label !== 'string' || !group.label.replace(/^\s+|\s+$/g, '') || !group.summary) { continue; }
            seen[group.key] = true; clean.push(group);
        }
        return clean;
    }
    function selectedModeGroup() {
        var groups = modeGroups(state.payload), index;
        for (index = 0; index < groups.length; index += 1) {
            if (groups[index].key === state.modeFilter) { return groups[index]; }
        }
        return null;
    }
    function modeFilterLabel() {
        var group = selectedModeGroup();
        return group ? gameModeLabel(group) : t('Todos los modos');
    }
    function battleSummary() {
        if (state.vehicleFilter !== 'all') { var selected = selectedVehicleGroup(); return state.vehicleSelection ? state.vehicleSelection.summary : selected ? selected.summary : {}; }
        var group = selectedModeGroup();
        return group ? group.summary : state.payload && state.payload.summary ? state.payload.summary : {};
    }
    function history() {
        if (state.vehicleFilter !== 'all') {
            return state.vehicleSelection && Array.isArray(state.vehicleSelection.history) ? state.vehicleSelection.history : [];
        }
        var group = selectedModeGroup();
        var rows = group ? group.history : state.payload && state.payload.history;
        return Array.isArray(rows) ? rows : [];
    }
    function acceptModeFilter(payload) {
        var context = typeof payload.account_context === 'string' ? payload.account_context : null;
        var groups = modeGroups(payload), valid = state.modeFilter === 'all', index;
        if (!payload.ready || (state.modeAccountContext !== null && context !== state.modeAccountContext)) {
            state.modeFilter = 'all'; state.selected = null; setPicker(false); setModePicker(false);
            clearVehicleFilter();
            nodes['history-options'].scrollTop = 0;
        }
        state.modeAccountContext = context;
        valid = state.modeFilter === 'all';
        for (index = 0; index < groups.length; index += 1) {
            if (groups[index].key === state.modeFilter) { valid = true; }
        }
        if (!valid) {
            state.modeFilter = 'all'; state.selected = null; setPicker(false); setModePicker(false);
            nodes['history-options'].scrollTop = 0;
        }
    }
    function setModePicker(open) {
        state.modePickerOpen = open;
        show(nodes['mode-menu'], open);
        nodes['mode-toggle'].setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) {
            setVehiclePicker(false);
            setPicker(false);
            nodes['mode-menu'].style.height = (18 + Math.min(6, modeGroups(state.payload).length + 1) * 56) + 'px';
            var rect = nodes['mode-menu'].getBoundingClientRect();
            var contentRect = nodes.content.getBoundingClientRect();
            if (rect.bottom > contentRect.bottom - 8) { nodes.content.scrollTop += rect.bottom - contentRect.bottom + 8; }
            queueLayout();
        }
    }
    function chooseModeFilter(key) {
        state.modeFilter = key; state.selected = null;
        setModePicker(false); setPicker(false);
        setVehiclePicker(false);
        nodes['history-options'].scrollTop = 0;
        if (state.vehicleFilter !== 'all') {
            if (selectedVehicleGroup()) { requestVehicleFilter(); }
            else { clearVehicleFilter(); }
        }
        renderData();
        nodes['mode-toggle'].focus();
    }
    function renderModeFilter() {
        var groups = modeGroups(state.payload), index;
        var oldScroll = nodes['mode-options'].scrollTop;
        function option(key, label, group) {
            var button = document.createElement('button'), name = document.createElement('div');
            button.type = 'button'; button.className = 'lc-mode-option';
            button.setAttribute('data-mode-key', key);
            button.setAttribute('aria-pressed', key === state.modeFilter ? 'true' : 'false');
            setClass(button, 'lc-history-option-selected', key === state.modeFilter);
            name.className = 'lc-filter-option-label'; setText(name, label.slice(0, 160));
            button.appendChild(modeImage(group)); button.appendChild(name);
            button.addEventListener('click', function () { chooseModeFilter(key); });
            nodes['mode-list'].appendChild(button);
        }
        setText(nodes['mode-label'], modeFilterLabel());
        replaceArt(nodes['mode-icon'], modeImage(selectedModeGroup()));
        disable(nodes['mode-toggle'], !ready() || groups.length === 0);
        while (nodes['mode-list'].firstChild) { nodes['mode-list'].removeChild(nodes['mode-list'].firstChild); }
        option('all', t('Todos los modos'));
        for (index = 0; index < groups.length; index += 1) { option(groups[index].key, gameModeLabel(groups[index]), groups[index]); }
        nodes['mode-options'].scrollTop = oldScroll;
        if (state.modePickerOpen) { nodes['mode-menu'].style.height = (18 + Math.min(6, groups.length + 1) * 56) + 'px'; }
    }
    function vehicleGroups() {
        var mode = selectedModeGroup();
        var source = mode ? mode.vehicle_groups : state.payload && state.payload.vehicle_groups;
        var groups = Array.isArray(source) ? source : [], clean = [], seen = {}, index, group;
        for (index = 0; index < groups.length; index += 1) {
            group = groups[index];
            if (!group || typeof group.key !== 'string' || !/^(vehicle:[0-9]+|unknown|multiple)$/.test(group.key) ||
                    seen[group.key] || typeof group.label !== 'string' || !group.summary) { continue; }
            seen[group.key] = true; clean.push(group);
        }
        return clean;
    }
    function selectedVehicleGroup() {
        var groups = vehicleGroups(), index;
        for (index = 0; index < groups.length; index += 1) { if (groups[index].key === state.vehicleFilter) { return groups[index]; } }
        return null;
    }
    function vehicleGroupLabel(group) {
        var label = group ? group.key === 'unknown' ? t('Veh\u00edculo sin identificar') : group.key === 'multiple' ? t('Varios veh\u00edculos') : group.label.slice(0, 120) : '';
        if (group && group.vehicle && (/^(?:Veh\u00edculo|Vehicle) [0-9]+$/.test(label))) { label = vehicleName(group.vehicle); }
        return group ? label + (group.vehicle ? ' (' + tierText(group.vehicle.tier) + ')' : '') : t('Todos los veh\u00edculos');
    }
    function acknowledgementId(value) {
        if (typeof value === 'string' && !/^[1-9][0-9]*$/.test(value)) { return null; }
        var numeric = typeof value === 'string' ? Number(value) : number(value);
        return numeric !== null && numeric > 0 && numeric <= 9007199254740991 && Math.floor(numeric) === numeric ? numeric : null;
    }
    function clearVehicleTimer() {
        if (state.vehicleTimer !== null) { window.clearTimeout(state.vehicleTimer); state.vehicleTimer = null; }
    }
    function vehicleAwaiting() { return state.vehicleFilter !== 'all' && !state.vehicleSelection; }
    function clearVehicleFilter() {
        clearVehicleTimer(); state.vehicleAttempts = 0;
        state.vehicleFilter = 'all'; state.vehicleRequest = null; state.vehicleExpected = null;
        state.vehicleSelection = null; state.vehicleFeedback = ''; state.selected = null;
        setVehiclePicker(false);
    }
    function requestVehicleFilter(retry) {
        if (!ready() || state.vehicleFilter === 'all' || !selectedVehicleGroup()) { return; }
        clearVehicleTimer();
        if (retry !== true) { state.vehicleAttempts = 0; }
        state.vehicleAttempts += 1; state.vehicleRequestId += 1;
        var request = {mode_key:state.modeFilter, vehicle_key:state.vehicleFilter, request_id:state.vehicleRequestId,
            account_context:state.payload.account_context};
        state.vehicleExpected = request; state.vehicleRequest = request; state.vehicleSelection = null;
        state.selected = null; state.vehicleFeedback = '';
        if (!invoke('onSetVehicleFilter', request)) {
            state.vehicleRequest = null; state.vehicleFeedback = t('No se pudo cargar la lista de partidas. Puedes reintentar; los importes del vehículo ya están disponibles.');
        } else {
            state.vehicleTimer = window.setTimeout(function () {
                state.vehicleTimer = null;
                if (!state.vehicleRequest || state.vehicleRequest.request_id !== request.request_id || state.disposed) { return; }
                if (state.vehicleAttempts < 2) { requestVehicleFilter(true); }
                else { state.vehicleRequest = null; state.vehicleFeedback = t('La lista de partidas está tardando. Los importes están disponibles; puedes reintentar.'); }
                renderData();
            }, 6000);
        }
    }
    function acceptVehicleFilter(payload) {
        var response = payload.vehicle_selection, expected = state.vehicleExpected;
        var responseId = response ? acknowledgementId(response.request_id) : null;
        if (responseId !== null) { state.vehicleRequestId = Math.max(state.vehicleRequestId, responseId); }
        if (state.vehicleFilter === 'all') { return; }
        if (!selectedVehicleGroup()) { clearVehicleFilter(); return; }
        if (!expected || expected.mode_key !== state.modeFilter || expected.vehicle_key !== state.vehicleFilter) {
            requestVehicleFilter(); return;
        }
        if (response && responseId === expected.request_id && response.mode_key === expected.mode_key &&
                response.vehicle_key === expected.vehicle_key) {
            if (response.available === false) {
                clearVehicleFilter(); state.vehicleFeedback = t('El veh\u00edculo ya no tiene partidas en este modo.');
            } else if (response.summary && Array.isArray(response.history)) {
                clearVehicleTimer(); state.vehicleSelection = response; state.vehicleRequest = null; state.vehicleFeedback = '';
            }
        } else if (state.vehicleRequest && payload.error) {
            state.vehicleRequest = null; state.vehicleFeedback = t('No se pudo filtrar el veh\u00edculo. Puedes reintentar.');
        }
    }
    function setVehiclePicker(open) {
        state.vehiclePickerOpen = open; show(nodes['vehicle-menu'], open);
        nodes['vehicle-toggle'].setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) {
            setPicker(false); setModePicker(false);
            nodes['vehicle-menu'].style.height = (18 + Math.min(6, vehicleGroups().length + 1) * 56) + 'px';
            var rect = nodes['vehicle-menu'].getBoundingClientRect(), contentRect = nodes.content.getBoundingClientRect();
            if (rect.bottom > contentRect.bottom - 8) { nodes.content.scrollTop += rect.bottom - contentRect.bottom + 8; }
            queueLayout();
        }
    }
    function chooseVehicleFilter(key) {
        state.vehicleFilter = key; state.selected = null; setVehiclePicker(false); setPicker(false);
        nodes['history-options'].scrollTop = 0;
        if (key === 'all') { clearVehicleFilter(); } else { requestVehicleFilter(); }
        renderData(); nodes['vehicle-toggle'].focus();
    }
    function renderVehicleFilter() {
        var groups = vehicleGroups(), index, oldScroll = nodes['vehicle-options'].scrollTop;
        function option(key, label, group) {
            var button = document.createElement('button'), name = document.createElement('div'); button.type = 'button'; button.className = 'lc-mode-option lc-vehicle-option';
            button.setAttribute('data-vehicle-key', key); button.setAttribute('aria-pressed', key === state.vehicleFilter ? 'true' : 'false');
            setClass(button, 'lc-history-option-selected', key === state.vehicleFilter);
            name.className = 'lc-filter-option-label'; setText(name, label);
            if (group && group.vehicle) { button.appendChild(vehicleImage(group.vehicle)); }
            else { var space = document.createElement('div'); space.className = 'lc-filter-tank-space'; button.appendChild(space); }
            button.appendChild(name);
            button.addEventListener('click', function () { chooseVehicleFilter(key); }); nodes['vehicle-list'].appendChild(button);
        }
        setText(nodes['vehicle-label'], vehicleGroupLabel(selectedVehicleGroup()));
        var selected = selectedVehicleGroup();
        replaceArt(nodes['vehicle-icon'], selected && selected.vehicle ? vehicleImage(selected.vehicle) : null);
        disable(nodes['vehicle-toggle'], !ready() || groups.length === 0);
        while (nodes['vehicle-list'].firstChild) { nodes['vehicle-list'].removeChild(nodes['vehicle-list'].firstChild); }
        option('all', t('Todos los veh\u00edculos'));
        for (index = 0; index < groups.length; index += 1) { option(groups[index].key, vehicleGroupLabel(groups[index]), groups[index]); }
        nodes['vehicle-options'].scrollTop = oldScroll;
        if (state.vehiclePickerOpen) { nodes['vehicle-menu'].style.height = (18 + Math.min(6, groups.length + 1) * 56) + 'px'; }
        setText(nodes['vehicle-status'], state.vehicleRequest ? t('Cargando la lista de partidas. Los importes del vehículo ya están disponibles.') : state.vehicleFeedback);
        show(nodes['vehicle-retry'], vehicleAwaiting() && !state.vehicleRequest);
        disable(nodes['vehicle-retry'], !ready() || !!state.vehicleRequest);
    }
    function clockLabel(value) { return typeof value === 'string' ? localizedLabel(value.replace(/^\s+|\s+$/g, '')) : ''; }
    function historySettings(payload) {
        var value = payload && payload.history_control;
        return value && number(value.generation) !== null && value.generation >= 0 ? {generation:value.generation} : null;
    }
    function historyControlReady() { return ready() && historySettings(state.payload) !== null; }
    function renderHistoryControl() {
        var control = state.payload && state.payload.history_control;
        var available = historyControlReady(), pending = mutationPending();
        setText(nodes['history-settings-status'], state.historyPendingReset ? t('Reiniciando historial...') : state.historyFeedback);
        disable(nodes['history-reset'], !available || !control || control.can_reset !== true || pending);
        setText(nodes['history-reset'], state.historyPendingReset ? t('Reiniciando...') : t('Reiniciar historial'));
        show(nodes['history-confirmation'], state.historyConfirm);
        setText(nodes['history-confirm-note'], t('El historial actual queda en 0 y la meta se desactiva. Puedes escribir una nueva desde tu saldo actual. Tu saldo y los días anteriores se conservan.'));
        disable(nodes['history-confirm'], !available || !control || control.can_reset !== true || pending);
        disable(nodes['history-cancel'], state.historyPendingReset);
        queueLayout();
    }
    function acceptHistoryControl(payload) {
        var incoming = historySettings(payload), changed;
        if (!incoming) { return; }
        changed = state.historyGeneration !== null && state.historyGeneration !== incoming.generation;
        state.historySaved = incoming; state.historyGeneration = incoming.generation;
        if (changed) {
            clearArchive();
            state.historyPendingReset = false; state.historyConfirm = false;
            state.historyFeedback = t('Historial reiniciado.'); state.selected = null;
            state.modeFilter = 'all'; setModePicker(false); clearVehicleFilter(); setPicker(false);
            nodes['history-options'].scrollTop = 0;
            if (payload.goal && number(payload.goal.target) === 0) {
                state.draftDigits = '0'; state.savedDigits = '0'; state.draftMode = 'balance_growth'; state.savedMode = 'balance_growth';
                state.dirty = false; state.pendingSave = false; state.pendingGoalReset = null;
                state.invalid = ''; state.rejectedRaw = null; state.feedback = t('Nuevo historial. Puedes iniciar una meta desde tu saldo actual.');
                nodes.target.value = '0';
            }
        } else if (state.historyPendingReset && payload.error) {
            state.historyPendingReset = false; state.historyFeedback = t('No se reinició el historial. Puedes volver a intentarlo.');
        }
    }
    function resetHistory() {
        var control = state.payload && state.payload.history_control;
        if (goalBusy() || !historyControlReady() || !control || control.can_reset !== true || state.historyPendingReset) { return; }
        state.historyConfirm = true;
        renderHistoryControl();
        nodes['history-confirm'].focus();
    }
    function cancelHistoryReset() {
        if (state.historyPendingReset) { return; }
        state.historyConfirm = false;
        renderHistoryControl();
        nodes['history-reset'].focus();
    }
    function confirmHistoryReset() {
        var control = state.payload && state.payload.history_control;
        if (goalBusy() || !state.historyConfirm || !historyControlReady() || !control || control.can_reset !== true || state.historyPendingReset) { return; }
        state.historyPendingReset = true;
        state.historyFeedback = '';
        if (!invoke('onResetHistory', {confirm:true})) { state.historyPendingReset = false; }
        renderData();
    }
    function selectedRecord() {
        var rows = history();
        var index;
        if (state.selected !== null) {
            for (index = 0; index < rows.length; index += 1) {
                if (String(rows[index].battle_id) === state.selected) { return rows[index]; }
            }
            state.selected = null;
        }
        return battleSummary();
    }
    function fitHistoryPicker(reveal) {
        var count = history().length;
        var available = nodes.content.clientHeight - nodes['history-toggle'].offsetHeight - 24;
        var visible = Math.max(1, Math.min(5, Math.floor((available - 50) / 72)));
        var rect, contentRect;
        // 40px summary row, up to five complete 72px battles, padding and border.
        nodes['history-menu'].style.height = (50 + Math.min(count, visible) * 72) + 'px';
        if (reveal) {
            rect = nodes['history-menu'].getBoundingClientRect();
            contentRect = nodes.content.getBoundingClientRect();
            if (rect.bottom > contentRect.bottom - 8) {
                nodes.content.scrollTop += rect.bottom - contentRect.bottom + 8;
            }
        }
    }
    function setPicker(open) {
        state.pickerOpen = open;
        show(nodes['history-menu'], open);
        if (open) {
            setModePicker(false);
            setVehiclePicker(false);
            fitHistoryPicker(true);
            queueLayout();
        }
        nodes['history-toggle'].setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    function renderReserves(record, hasData) {
        var reserves = hasData && record.reserves;
        var personal = reserves ? number(reserves.personal) : null;
        var clan = reserves ? number(reserves.clan) : null;
        var summary = state.selected === null;
        var known = reserves ? number(reserves.known_battles) : null;
        var total = reserves ? number(reserves.total_battles) : null;
        var note;
        // Missing historical detail is unknown, never a fabricated zero bonus.
        if (personal === null || clan === null || personal < 0 || clan < 0 ||
                (summary && (known === null || total === null || (known === 0 && total > 0)))) {
            personal = null; clan = null;
            note = hasData ? t('El juego no proporcionó el detalle de reservas de estas partidas. Sus créditos ya están incluidos en los ingresos brutos.') : t('El detalle de reservas aparecerá si el juego lo proporciona. Los ingresos y gastos se actualizan por separado.');
        } else {
            note = t('Ya incluidas en los ingresos brutos.');
            if (summary && known < total) {
                note += t(' Desglose disponible en ') + integerText(known) + t(' de ') + integerText(total) + t(' partidas.');
            }
        }
        setText(nodes['reserve-personal'], personal === 0 ? '0' : signedText(personal));
        setText(nodes['reserve-clan'], clan === 0 ? '0' : signedText(clan));
        colorNumber(nodes['reserve-personal'], personal);
        colorNumber(nodes['reserve-clan'], clan);
        setText(nodes['reserve-note'], note);
    }
    function renderDetail() {
        var record = selectedRecord();
        var expenses = record.expenses || {};
        var hasData = ready() && number(record.gross_credits) !== null;
        var gross = hasData ? number(record.gross_credits) : null;
        var net = hasData ? number(record.net_credits) : null;
        var other = hasData ? number(expenses.other) : null;
        setText(nodes['history-label'], state.selected === null ? battleScopeLabel() : vehicleLabel(record) + ' \u00b7 ' + timeLabel(record));
        renderVehicles(record);
        show(nodes['detail-mode'], state.selected !== null);
        renderBattleMode(record);
        setText(nodes.gross, signedText(gross));
        colorNumber(nodes.gross, gross);
        renderReserves(record, hasData);
        setText(nodes.repair, expenseText(hasData ? expenses.repair : null));
        setText(nodes.ammo, expenseText(hasData ? expenses.ammo : null));
        setText(nodes.consumables, expenseText(hasData ? expenses.consumables : null));
        setText(nodes.other, expenseText(other));
        colorExpense(nodes.repair, hasData ? expenses.repair : null);
        colorExpense(nodes.ammo, hasData ? expenses.ammo : null);
        colorExpense(nodes.consumables, hasData ? expenses.consumables : null);
        colorExpense(nodes.other, other);
        show(nodes['other-row'], other !== null && other !== 0);
        setText(nodes['detail-net'], signedText(net));
        colorNumber(nodes['detail-net'], net);
        show(nodes['history-empty'], ready() && !vehicleAwaiting() && history().length === 0);
        setText(nodes['history-empty'], state.vehicleFilter !== 'all' ? t('No hay partidas registradas para este veh\u00edculo y modo.') : state.modeFilter === 'all' ? t('Las partidas finalizadas aparecer\u00e1n aqu\u00ed.') : t('No hay partidas registradas en este modo.'));
        while (nodes['detail-rewards'].firstChild) { nodes['detail-rewards'].removeChild(nodes['detail-rewards'].firstChild); }
        if (state.selected !== null && record.rewards) {
            for (var r = 0; r < record.rewards.length; r += 1) {
                var line = document.createElement('div');
                line.className = 'lc-foot';
                setAmountParts(line, [rewardTitle(record.rewards[r]) + ': ', {value:record.rewards[r].credits, signed:true}, t(' cr. (incluido en el ingreso bruto)')]);
                nodes['detail-rewards'].appendChild(line);
            }
        }
        queueLayout();
    }
    function tierText(tier) {
        var romans = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX'];
        return typeof tier === 'number' && tier % 1 === 0 && tier >= 1 && tier <= 20 ? t('Nivel ') + romans[tier - 1] : t('Nivel sin identificar');
    }
    function vehicles(record) {
        return record && Array.isArray(record.vehicles) && record.vehicles.length ? record.vehicles : [{name:t('Veh\u00edculo sin identificar'), tier:null, icon:null}];
    }
    function vehicleName(vehicle) {
        var name = vehicle && typeof vehicle.name === 'string' ? vehicle.name : '';
        var identity = vehicle && vehicle.vehicle_type_id;
        if (identity !== undefined && (name === 'Veh\u00edculo ' + identity || name === 'Vehicle ' + identity)) {
            return (state.language === 'en' ? 'Vehicle ' : 'Veh\u00edculo ') + identity;
        }
        return !name || name === 'Veh\u00edculo sin identificar' || name === 'Unknown vehicle' ? t('Veh\u00edculo sin identificar') : name;
    }
    function vehicleLabel(record) {
        var rows = vehicles(record), labels = [], n;
        for (n = 0; n < rows.length; n += 1) { labels.push(vehicleName(rows[n]) + ' (' + tierText(rows[n].tier) + ')'); }
        return labels.join(' / ');
    }
    function battleModeLabel(record) {
        return gameModeLabel(record && record.battle_mode);
    }
    function replaceArt(container, art) {
        while (container.firstChild) { container.removeChild(container.firstChild); }
        if (art) { container.appendChild(art); }
    }
    function safeLocalImage(value, kind) {
        if (typeof value !== 'string' || value.indexOf('..') !== -1) { return false; }
        // Wargaming mounts event assets below their native resource prefix.
        // Only local PNG resource directories are accepted, never arbitrary URLs.
        if (kind === 'mode') { return /^coui:\/\/(?:(?:halloween|comp7_light)\/)?gui\/maps\/icons\/battleTypes\/(?:64x64|136x136)\/[A-Za-z0-9_.-]+\.png$/.test(value); }
        return /^coui:\/\/(?:halloween\/)?gui\/maps\/(?:icons\/vehicle|shop\/vehicles)\/[A-Za-z0-9_./-]+\.png$/.test(value);
    }
    function loadLocalImage(frame, image, fallback, sources, kind) {
        var clean = [], seen = {}, index, cursor = 0;
        for (index = 0; index < sources.length && clean.length < 6; index += 1) {
            if (safeLocalImage(sources[index], kind) && !seen[sources[index]]) { clean.push(sources[index]); seen[sources[index]] = true; }
        }
        if (!clean.length) { return; }
        image.addEventListener('load', function () { if (fallback) { show(fallback, false); } show(image, true); });
        image.addEventListener('error', function () {
            show(image, false);
            if (fallback) { show(fallback, true); }
            cursor += 1;
            if (cursor < clean.length) { image.src = clean[cursor]; }
        });
        show(image, false); frame.appendChild(image); image.src = clean[0];
    }
    function modeImage(mode) {
        var frame = document.createElement('div'), image = document.createElement('img');
        frame.className = 'lc-mode-art'; frame.setAttribute('aria-hidden', 'true'); image.alt = '';
        if (mode && mode.icon) { loadLocalImage(frame, image, null, [mode.icon], 'mode'); }
        return frame;
    }
    function renderBattleMode(record) {
        var text = document.createElement('div'); text.className = 'lc-mode-detail-label';
        setText(text, t('Modo de juego: ') + battleModeLabel(record));
        replaceArt(nodes['detail-mode'], modeImage(record && record.battle_mode));
        nodes['detail-mode'].appendChild(text);
    }
    function vehicleImage(vehicle) {
        var frame = document.createElement('div'), img = document.createElement('img'), fallback = document.createElement('div');
        var sources = [vehicle.icon];
        frame.className = 'lc-tank-art';
        fallback.className = 'lc-tank-placeholder';
        setText(fallback, t('Sin imagen'));
        frame.appendChild(fallback);
        img.alt = vehicleName(vehicle);
        loadLocalImage(frame, img, fallback, sources, 'vehicle');
        return frame;
    }
    function renderVehicles(record) {
        var container = nodes['detail-vehicles'], rows, index, row, card, info, name, level;
        while (container.firstChild) { container.removeChild(container.firstChild); }
        show(container, state.selected !== null);
        if (state.selected === null) { return; }
        rows = vehicles(record);
        for (index = 0; index < rows.length; index += 1) {
            row = rows[index]; card = document.createElement('div'); info = document.createElement('div');
            name = document.createElement('div'); level = document.createElement('div');
            card.className = 'lc-tank-card'; info.className = 'lc-tank-info';
            name.className = 'lc-tank-name'; level.className = 'lc-tank-tier';
            setText(name, vehicleName(row), true); setText(level, tierText(row.tier));
            info.appendChild(name); info.appendChild(level); card.appendChild(vehicleImage(row)); card.appendChild(info);
            container.appendChild(card);
        }
    }
    function makeHistoryButton(label, amount, identity, record, onSelect, selectedIdentity) {
        var button = document.createElement('button');
        var title = document.createElement('div');
        var net = document.createElement('div');
        button.type = 'button';
        button.className = 'lc-history-option';
        setClass(button, 'lc-history-option-selected', identity === (typeof onSelect === 'function' ? selectedIdentity : state.selected));
        title.className = 'lc-history-time';
        net.className = 'lc-history-net';
        setText(title, label);
        if (record) {
            var name = document.createElement('div'), stamp = document.createElement('div'), stampLabel = document.createElement('div');
            name.className = 'lc-history-tank'; stamp.className = 'lc-history-stamp';
            stampLabel.className = 'lc-history-stamp-label';
            setText(name, vehicleLabel(record)); setText(stampLabel, label + ' \u00b7 ' + battleModeLabel(record));
            stamp.appendChild(modeImage(record.battle_mode)); stamp.appendChild(stampLabel);
            button.setAttribute('title', vehicleLabel(record) + ' \u00b7 ' + label + ' \u00b7 ' + battleModeLabel(record));
            button.setAttribute('aria-label', vehicleLabel(record) + ' \u00b7 ' + label + ' \u00b7 ' + battleModeLabel(record) + ' \u00b7 ' + signedText(amount));
            setText(title, ''); title.appendChild(name); title.appendChild(stamp);
            button.appendChild(vehicleImage(vehicles(record)[0]));
            setClass(button, 'lc-history-battle', true);
        }
        setText(net, amount === null ? '' : signedText(amount));
        colorNumber(net, amount);
        button.appendChild(title);
        button.appendChild(net);
        button.addEventListener('click', function () {
            if (typeof onSelect === 'function') { onSelect(identity); return; }
            state.selected = identity;
            setPicker(false);
            renderDetail();
            renderHistory();
            nodes['history-toggle'].focus();
        });
        return button;
    }
    function renderHistory() {
        var rows = history();
        var summary = battleSummary();
        var row;
        var index;
        var oldScroll = nodes['history-options'].scrollTop;
        while (nodes['history-list'].firstChild) {
            nodes['history-list'].removeChild(nodes['history-list'].firstChild);
        }
        nodes['history-list'].appendChild(makeHistoryButton(battleScopeLabel(), number(summary.net_credits), null));
        for (index = 0; index < rows.length; index += 1) {
            row = rows[index];
            if (!row || row.battle_id === undefined || row.battle_id === null) { continue; }
            nodes['history-list'].appendChild(makeHistoryButton(timeLabel(row), number(row.net_credits), String(row.battle_id), row));
        }
        nodes['history-options'].scrollTop = oldScroll;
        if (state.pickerOpen) { fitHistoryPicker(false); }
        queueLayout();
    }
    function battleScopeLabel() {
        if (state.vehicleFilter !== 'all') {
            return t('Partidas de ') + vehicleGroupLabel(selectedVehicleGroup()) + (state.modeFilter === 'all' ? '' : ' \u00b7 ' + modeFilterLabel());
        }
        return state.modeFilter === 'all' ? t('Todas las partidas') : t('Todas las partidas de ') + modeFilterLabel();
    }
    function archiveEnvelope() { return state.payload && state.payload.history_archive ? state.payload.history_archive : {}; }
    function archiveDays() {
        var source = archiveEnvelope().days, clean = [], index, row;
        if (!Array.isArray(source)) { return clean; }
        for (index = 0; index < source.length; index += 1) {
            row = source[index];
            if (row && typeof row.key === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(row.key) && typeof row.label === 'string') { clean.push(row); }
        }
        return clean;
    }
    function archiveFind(rows, key) {
        var index;
        for (index = 0; index < rows.length; index += 1) { if (rows[index].key === key) { return rows[index]; } }
        return null;
    }
    function archiveDayRecord() { return archiveFind(archiveDays(), state.archiveDay); }
    function archiveSummary() {
        if (state.archiveSelection) { return state.archiveSelection.summary || {}; }
        var group = state.archiveVehicle !== 'all' ? archiveFind(state.archiveVehicleGroups, state.archiveVehicle) :
            state.archiveMode !== 'all' ? archiveFind(state.archiveModeGroups, state.archiveMode) : archiveDayRecord();
        return group && group.summary ? group.summary : {};
    }
    function archiveRows() { return state.archiveSelection && Array.isArray(state.archiveSelection.history) ? state.archiveSelection.history : []; }
    function clearArchiveTimer() {
        if (state.archiveTimer !== null) { window.clearTimeout(state.archiveTimer); state.archiveTimer = null; }
    }
    function clearArchive() {
        clearArchiveTimer(); state.archiveOpen = false; state.archivePicker = null;
        state.archiveDay = null; state.archiveMode = 'all'; state.archiveVehicle = 'all';
        state.archiveRequest = null; state.archiveExpected = null; state.archiveSelection = null; state.archiveSelected = null;
        state.archiveModeGroups = []; state.archiveVehicleGroups = []; state.archiveFeedback = ''; state.archiveAttempts = 0;
        var lists = ['archive-battle-list', 'archive-day-list', 'archive-mode-list', 'archive-vehicle-list'];
        for (var index = 0; index < lists.length; index += 1) {
            var list = nodes[lists[index]]; while (list && list.firstChild) { list.removeChild(list.firstChild); }
        }
    }
    function setArchivePicker(kind) {
        state.archivePicker = kind;
        for (var index = 0; index < archiveKinds.length; index += 1) {
            var key = archiveKinds[index]; show(nodes['archive-' + key + '-menu'], kind === key);
            nodes['archive-' + key + '-toggle'].setAttribute('aria-expanded', kind === key ? 'true' : 'false');
        }
        queueLayout();
    }
    function requestArchive(retry) {
        if (!ready() || !state.archiveOpen || !archiveDayRecord()) { return; }
        clearArchiveTimer();
        if (retry !== true) { state.archiveAttempts = 0; }
        state.archiveAttempts += 1; state.archiveRequestId += 1;
        var request = {day_key:state.archiveDay, mode_key:state.archiveMode, vehicle_key:state.archiveVehicle,
            request_id:state.archiveRequestId, account_context:state.payload.account_context};
        state.archiveRequest = request; state.archiveExpected = request; state.archiveSelection = null; state.archiveSelected = null; state.archiveFeedback = '';
        if (!invoke('onSelectHistoryDay', request)) {
            state.archiveRequest = null; state.archiveFeedback = t('No se pudo cargar la jornada. Puedes reintentar.');
        } else {
            state.archiveTimer = window.setTimeout(function () {
                state.archiveTimer = null;
                if (state.disposed || !state.archiveRequest || state.archiveRequest.request_id !== request.request_id) { return; }
                if (state.archiveAttempts < 2) { requestArchive(true); }
                else { state.archiveRequest = null; state.archiveFeedback = t('Esta jornada está tardando en cargar. Puedes reintentar.'); }
                renderArchive();
            }, 6000);
        }
    }
    function acceptArchive(payload) {
        var context = typeof payload.account_context === 'string' ? payload.account_context : null;
        if (!payload.ready || (state.archiveContext !== null && state.archiveContext !== context)) { clearArchive(); }
        state.archiveContext = context;
        var response = archiveEnvelope().selection, expected = state.archiveExpected;
        if (!state.archiveOpen) { return; }
        if (!archiveDayRecord()) {
            var days = archiveDays();
            state.archiveDay = days.length ? days[0].key : null; state.archiveMode = 'all'; state.archiveVehicle = 'all';
            state.archiveSelection = null; state.archiveExpected = null; state.archiveRequest = null;
            state.archiveModeGroups = []; state.archiveVehicleGroups = [];
            if (state.archiveDay) { requestArchive(); }
            return;
        }
        if (!expected || !response || acknowledgementId(response.request_id) !== expected.request_id ||
                response.day_key !== expected.day_key || response.mode_key !== expected.mode_key || response.vehicle_key !== expected.vehicle_key ||
                (response.account_context !== undefined && response.account_context !== context)) { return; }
        clearArchiveTimer(); state.archiveRequest = null;
        if (response.available === false) { state.archiveSelection = null; state.archiveFeedback = t('No hay datos para esta selección. Elige otro día, modo o vehículo.'); return; }
        if (!response.summary || !Array.isArray(response.history)) { state.archiveFeedback = t('No se pudo leer esta jornada. Puedes reintentar.'); return; }
        state.archiveSelection = response; state.archiveFeedback = '';
        state.archiveModeGroups = modeGroups({mode_groups:response.mode_groups});
        state.archiveVehicleGroups = Array.isArray(response.vehicle_groups) ? response.vehicle_groups.filter(function (group) {
            return group && typeof group.key === 'string' && /^(vehicle:[0-9]+|unknown|multiple)$/.test(group.key) && typeof group.label === 'string' && group.summary;
        }) : [];
        if (state.archiveSelected !== null && !response.history.some(function (row) { return String(row.battle_id) === state.archiveSelected; })) { state.archiveSelected = null; }
    }
    function chooseArchive(kind, key) {
        if (kind === 'day') {
            if (!archiveFind(archiveDays(), key)) { return; }
            state.archiveDay = key; state.archiveMode = 'all'; state.archiveVehicle = 'all';
            state.archiveModeGroups = []; state.archiveVehicleGroups = [];
        } else if (kind === 'mode') {
            if (key !== 'all' && !archiveFind(state.archiveModeGroups, key)) { return; }
            state.archiveMode = key; state.archiveVehicle = 'all'; state.archiveVehicleGroups = [];
        } else {
            if (key !== 'all' && !archiveFind(state.archiveVehicleGroups, key)) { return; }
            state.archiveVehicle = key;
        }
        setArchivePicker(null); nodes['archive-battle-options'].scrollTop = 0; requestArchive(); renderArchive();
        nodes['archive-' + kind + '-toggle'].focus();
    }
    function archiveOption(kind, group, label) {
        var button = document.createElement('button'), name = document.createElement('div');
        button.type = 'button'; button.className = 'lc-mode-option' + (kind === 'vehicle' ? ' lc-vehicle-option' : '');
        button.setAttribute('data-archive-' + kind, group.key);
        var selected = kind === 'day' ? state.archiveDay : kind === 'mode' ? state.archiveMode : state.archiveVehicle;
        setClass(button, 'lc-history-option-selected', selected === group.key); button.setAttribute('aria-pressed', selected === group.key ? 'true' : 'false');
        name.className = 'lc-filter-option-label'; setText(name, label);
        if (kind === 'mode') { button.appendChild(modeImage(group)); }
        if (kind === 'vehicle') {
            if (group.vehicle) { button.appendChild(vehicleImage(group.vehicle)); }
            else { var space = document.createElement('div'); space.className = 'lc-filter-tank-space'; button.appendChild(space); }
        }
        button.appendChild(name); button.addEventListener('click', function () { chooseArchive(kind, group.key); });
        return button;
    }
    function renderArchive() {
        var days = archiveDays(), day = archiveDayRecord(), mode = archiveFind(state.archiveModeGroups, state.archiveMode);
        var vehicle = archiveFind(state.archiveVehicleGroups, state.archiveVehicle), summary = archiveSummary();
        var rows = archiveRows(), record = summary, index, kind, list, groups, selectedRow = null;
        var status = state.archiveRequest ? t('Cargando la jornada seleccionada…') : state.archiveFeedback;
        show(nodes['archive-panel'], state.archiveOpen); nodes['archive-toggle'].setAttribute('aria-expanded', state.archiveOpen ? 'true' : 'false');
        setText(nodes['archive-chevron'], state.archiveOpen ? '−' : '+');
        setClass(nodes['archive-toggle'], 'lc-archive-open', state.archiveOpen);
        var toggleLabel = t(state.archiveOpen ? 'Ocultar historial por d\u00eda' : 'Mostrar historial por d\u00eda');
        nodes['archive-toggle'].setAttribute('aria-label', toggleLabel);
        nodes['archive-toggle'].setAttribute('title', toggleLabel);
        if (!state.archiveOpen) { return; }
        if (!days.length) { status = archiveEnvelope().ready === false ? t('Las jornadas anteriores estarán disponibles al sincronizar la cuenta.') : t('Aún no hay jornadas anteriores guardadas.'); }
        setText(nodes['archive-status'], status); show(nodes['archive-filters'], days.length > 0);
        setText(nodes['archive-day-label'], day ? localizedLabel(day.label) : t('Seleccionar día'));
        setText(nodes['archive-mode-label'], mode ? gameModeLabel(mode) : t('Todos los modos'));
        setText(nodes['archive-vehicle-label'], vehicleGroupLabel(vehicle));
        replaceArt(nodes['archive-mode-icon'], modeImage(mode)); replaceArt(nodes['archive-vehicle-icon'], vehicle && vehicle.vehicle ? vehicleImage(vehicle.vehicle) : null);
        for (index = 0; index < archiveKinds.length; index += 1) {
            kind = archiveKinds[index]; list = nodes['archive-' + kind + '-list'];
            var oldPickerScroll = nodes['archive-' + kind + '-options'].scrollTop;
            while (list.firstChild) { list.removeChild(list.firstChild); }
            groups = kind === 'day' ? days : kind === 'mode' ? state.archiveModeGroups : state.archiveVehicleGroups;
            if (kind !== 'day') { list.appendChild(archiveOption(kind, {key:'all'}, kind === 'mode' ? t('Todos los modos') : t('Todos los vehículos'))); }
            for (var n = 0; n < groups.length; n += 1) { list.appendChild(archiveOption(kind, groups[n], kind === 'vehicle' ? vehicleGroupLabel(groups[n]) : kind === 'mode' ? gameModeLabel(groups[n]) : localizedLabel(groups[n].label))); }
            nodes['archive-' + kind + '-options'].scrollTop = oldPickerScroll;
            nodes['archive-' + kind + '-menu'].style.height = (18 + Math.min(6, groups.length + (kind === 'day' ? 0 : 1)) * (kind === 'vehicle' ? 56 : kind === 'mode' ? 56 : 48)) + 'px';
            disable(nodes['archive-' + kind + '-toggle'], !ready() || !days.length || (kind !== 'day' && groups.length === 0));
        }
        show(nodes['archive-retry'], !!state.archiveFeedback && !!day && !state.archiveRequest);
        disable(nodes['archive-retry'], !ready() || !!state.archiveRequest);
        var count = number(summary.battle_count), total = state.archiveSelection ? number(state.archiveSelection.history_total) : count;
        setText(nodes['archive-count'], count === null ? t('Partidas pendientes de cargar') : integerText(count) + (count === 1 ? t(' partida') : t(' partidas')) + (total > rows.length && rows.length ? t(' · Se muestran las últimas ') + integerText(rows.length) : ''));
        var top = nodes['archive-battle-options'].scrollTop;
        while (nodes['archive-battle-list'].firstChild) { nodes['archive-battle-list'].removeChild(nodes['archive-battle-list'].firstChild); }
        function selectRecord(identity) { state.archiveSelected = identity; renderArchive(); }
        nodes['archive-battle-list'].appendChild(makeHistoryButton(t('Todas las partidas de esta selección'), number(summary.net_credits), null, null, selectRecord, state.archiveSelected));
        for (index = 0; index < rows.length; index += 1) {
            if (!rows[index] || rows[index].battle_id === undefined) { continue; }
            nodes['archive-battle-list'].appendChild(makeHistoryButton(timeLabel(rows[index]), number(rows[index].net_credits), String(rows[index].battle_id), rows[index], selectRecord, state.archiveSelected));
            if (String(rows[index].battle_id) === state.archiveSelected) { selectedRow = rows[index]; }
        }
        nodes['archive-battle-options'].scrollTop = top;
        nodes['archive-battles'].style.height = (50 + Math.min(5, rows.length) * 72) + 'px';
        show(nodes['archive-battles'], !!day && rows.length > 0); if (selectedRow) { record = selectedRow; }
        setText(nodes['archive-detail-title'], selectedRow ? vehicleLabel(selectedRow) + ' · ' + timeLabel(selectedRow) + ' · ' + battleModeLabel(selectedRow) : day ? t('Resultado de ') + localizedLabel(day.label) + (mode ? ' · ' + gameModeLabel(mode) : '') + (vehicle ? ' · ' + vehicleGroupLabel(vehicle) : '') : t('Selecciona una jornada'));
        var expense = record.expenses || {}, reserve = record.reserves || {};
        var known = selectedRow ? number(reserve.personal) !== null && number(reserve.clan) !== null : number(reserve.known_battles) > 0 || number(reserve.total_battles) === 0;
        var values = {gross:record.gross_credits, personal:known ? reserve.personal : null, clan:known ? reserve.clan : null, repair:expense.repair, ammo:expense.ammo, consumables:expense.consumables, other:expense.other, net:record.net_credits};
        for (var key in values) { if (values.hasOwnProperty(key)) {
            var value = number(values[key]), target = nodes['archive-' + key], isExpense = key === 'repair' || key === 'ammo' || key === 'consumables' || key === 'other';
            setText(target, isExpense ? expenseText(value) : signedText(value));
            if (isExpense) { colorExpense(target, value); } else { colorNumber(target, value); }
        } }
        var reserveNote = known ? t('Las reservas ya están incluidas en los ingresos brutos.') : t('El detalle de reservas no está disponible para todas las partidas. Sus créditos ya forman parte de los ingresos brutos.');
        if (!selectedRow && known && number(reserve.known_battles) !== null && number(reserve.total_battles) !== null && reserve.known_battles < reserve.total_battles) {
            reserveNote += t(' Desglose disponible en ') + integerText(reserve.known_battles) + t(' de ') + integerText(reserve.total_battles) + t(' partidas.');
        }
        setText(nodes['archive-reserve-note'], reserveNote);
        var extra = day ? number(day.external_credits) : null;
        setAmountParts(nodes['archive-extra'], extra !== null && extra !== 0 ? [t('Abonos adicionales de toda la jornada: '), {value:extra, signed:true}, t(' créditos. Se muestran por separado del resultado de las batallas.')] : []);
        setArchivePicker(state.archivePicker); queueLayout();
    }
    function toggleArchive() {
        state.archiveOpen = !state.archiveOpen; setArchivePicker(null);
        if (state.archiveOpen) {
            var days = archiveDays();
            if (!archiveDayRecord()) { state.archiveDay = days.length ? days[0].key : null; state.archiveMode = 'all'; state.archiveVehicle = 'all'; }
            if (state.archiveDay && !state.archiveSelection) { requestArchive(); }
        } else { clearArchiveTimer(); state.archiveRequest = null; }
        renderArchive();
    }
    function renderGoal() {
        var goal = currentGoal();
        var current = ready() ? number(goal.current) : null;
        var target = ready() ? number(goal.target) : null;
        var percent = number(goal.progress_percent);
        var remaining = number(goal.remaining);
        var estimate = number(goal.estimated_battles);
        var complete = target !== null && target > 0 && goal.complete === true;
        var since;
        setText(nodes['goal-title'], activeGoal(goal) ? t('Tu meta de cr\u00e9ditos') : t('Meta opcional de cr\u00e9ditos'));
        if (percent !== null) { percent = Math.max(0, Math.min(100, percent)); }
        if (target === 0) {
            setText(nodes['progress-text'], t('Sin meta activa'));
            setText(nodes.percent, percentText(0));
            nodes.fill.style.width = '0%';
            nodes.meter.setAttribute('aria-valuenow', '0');
            setText(nodes.remaining, number(goal.baseline) !== null ?
                t('La contabilidad sigue activa sin objetivo. Puedes reactivar la meta conservando tu avance.') :
                t('La contabilidad sigue activa sin objetivo. Puedes iniciar una meta cuando quieras.'));
            setText(nodes.estimate, '');
        } else if (current === null || target === null) {
            setText(nodes['progress-text'], target === null ? t('Sin meta disponible') : t('Meta guardada: ') + integerText(target) + t(' cr\u00e9ditos'));
            setText(nodes.percent, '\u2014');
            nodes.fill.style.width = '0%';
            nodes.meter.setAttribute('aria-valuenow', '0');
            setText(nodes.remaining, ready() ? t('Saldo pendiente de sincronizar.') : t('El progreso aparecer\u00e1 cuando la cuenta est\u00e9 lista.'));
            setText(nodes.estimate, '');
        } else {
            setAmountParts(nodes['progress-text'], [{value:current}, ' / ', {value:target}]);
            setText(nodes.percent, percent === null ? '\u2014' : percentText(percent));
            nodes.fill.style.width = (percent === null ? 0 : percent) + '%';
            nodes.meter.setAttribute('aria-valuenow', String(percent === null ? 0 : percent));
            if (!complete && remaining !== null) { setAmountParts(nodes.remaining, [t('Faltan '), {value:Math.max(0, remaining)}, t(' cr\u00e9ditos')]); }
            else { setText(nodes.remaining, complete ? t('Meta alcanzada.') : t('Progreso pendiente de actualizar.')); }
            setText(nodes.estimate, !complete && estimate !== null ? '\u2248 ' + integerText(Math.max(0, estimate)) + (estimate === 1 ? t(' partida') : t(' partidas')) + t(' al promedio registrado') : '');
        }
        since = clockLabel(goal.since_label);
        setText(nodes['goal-since'], since ? (target === 0 ? t('\u00daltima meta iniciada: ') : t('Meta iniciada: ')) + since :
            (number(goal.target) !== null && goal.target > 0 ? t('Inicio de la meta: pendiente de sincronizar.') : ''));
        if (number(goal.baseline) !== null) {
            setAmountParts(nodes['base-note'], target === 0 ? [t('\u00daltimo saldo base: '), {value:goal.baseline}] :
                [t('Saldo base: '), {value:goal.baseline}, t(' | Saldo al completar: '), {value:goal.final_balance}]);
        } else { setText(nodes['base-note'], t('Al iniciar una meta, tu saldo actual se guardar\u00e1 como base del 0 %.')); }
        show(nodes['goal-accumulated'], target === 0 && number(goal.baseline) !== null);
        if (target === 0 && number(goal.baseline) !== null) {
            if (current === null) { setText(nodes['goal-accumulated'], t('Avance conservado: pendiente de sincronizar el saldo.')); }
            else { setAmountParts(nodes['goal-accumulated'], [t('Avance conservado: '), {value:current, signed:true}, t(' cr\u00e9ditos desde el saldo base.')]); }
        }
        setClass(nodes.fill, 'lc-fill-complete', complete);
    }
    function renderWallet() {
        var wallet = state.payload && state.payload.wallet ? state.payload.wallet : {};
        var fields = [['wallet-base', 'baseline', false], ['wallet-battles', 'battle_net', true],
            ['wallet-external', 'external_credits', true], ['wallet-other', 'unclassified', true], ['wallet-total', 'balance', false]];
        var index;
        var value;
        for (index = 0; index < fields.length; index += 1) {
            value = wallet.ready ? number(wallet[fields[index][1]]) : null;
            setText(nodes[fields[index][0]], fields[index][2] ? signedText(value) : integerText(value));
            colorNumber(nodes[fields[index][0]], value);
        }
        var started = clockLabel(wallet.started_at_label);
        setText(nodes['wallet-period'], wallet.ready ? (started ? t('Seguimiento desde ') + started : t('Inicio del seguimiento: pendiente de sincronizar.')) : t('Esperando un saldo sincronizado...'));
    }
    function rewardRow(title, amount, context) {
        var row = document.createElement('div');
        var line = document.createElement('div');
        var name = document.createElement('div');
        var credits = document.createElement('div');
        var note = document.createElement('div');
        row.className = 'lc-reward'; line.className = 'lc-reward-line';
        name.className = 'lc-reward-title'; credits.className = 'lc-reward-amount'; note.className = 'lc-reward-context';
        setText(name, title, true); setText(credits, signedText(amount)); colorNumber(credits, amount); setText(note, context);
        line.appendChild(name); line.appendChild(credits); row.appendChild(line); row.appendChild(note);
        nodes['rewards-list'].appendChild(row);
    }
    function rewardTitle(item) {
        var title = item && typeof item.title === 'string' ? item.title : '';
        var names = {tokenQuests:['Misi\u00f3n / recompensa','Mission / reward'],
            potapovQuestBonus:['Misi\u00f3n de campa\u00f1a','Campaign mission'], personalMission3Quest:['Misi\u00f3n de campa\u00f1a','Campaign mission'],
            personalMission4Quest:['Misi\u00f3n de campa\u00f1a','Campaign mission'], hangarQuests:['Misi\u00f3n adicional','Additional mission'],
            rankedQuests:['Misi\u00f3n de clasificaci\u00f3n','Ranked mission'], royaleQuests:['Misi\u00f3n de evento','Event mission'],
            battlePassReward:['Recompensa del pase de batalla','Battle Pass reward'], piggyBankSmashed:['Reserva de cr\u00e9ditos','Credit Reserve'],
            invoiceReceived:['Abono / retirada de cr\u00e9ditos','Credit deposit / withdrawal'], battleResults:['Misiones de la partida','Battle missions']};
        var match;
        if (item.quest_id !== undefined && item.name_resolved === false) {
            return (state.language === 'en' ? 'Mission ' : 'Misi\u00f3n ') + item.quest_id;
        }
        if (names.hasOwnProperty(item.kind)) { return names[item.kind][state.language === 'en' ? 1 : 0]; }
        // Only translate wrappers generated by the mod; retain the native name inside.
        match = /^(?:Crisol|Crucible): (.*) \| (?:Misi\u00f3n|Mission) (.*)$/.exec(title);
        if (match) { return (state.language === 'en' ? 'Crucible: ' : 'Crisol: ') + match[1] + (state.language === 'en' ? ' | Mission ' : ' | Misi\u00f3n ') + match[2]; }
        if (item.kind === 'battlePassVoucher') {
            return title.replace(/^(?:Raspado de cup\u00f3n del Pase de batalla|Battle Pass voucher scratch reward)/,
                state.language === 'en' ? 'Battle Pass voucher scratch reward' : 'Raspado de cup\u00f3n del Pase de batalla');
        }
        return title;
    }
    function renderRewards() {
        var rows = state.payload && state.payload.rewards ? state.payload.rewards : [];
        var viewport = document.getElementById('lc-rewards-viewport');
        var top = viewport.scrollTop;
        var index;
        var part;
        var receipt;
        var context;
        while (nodes['rewards-list'].firstChild) { nodes['rewards-list'].removeChild(nodes['rewards-list'].firstChild); }
        for (index = 0; index < rows.length; index += 1) {
            receipt = rows[index];
            context = localizedLabel(receipt.time_label) + ' | ' + (receipt.included_in_battle ? t('Incluido en partida') : t('Movimiento adicional'));
            if (receipt.parts && receipt.parts.length) {
                for (part = 0; part < receipt.parts.length; part += 1) { rewardRow(rewardTitle(receipt.parts[part]), receipt.parts[part].credits, context); }
            } else { rewardRow(rewardTitle(receipt), receipt.credits, context); }
        }
        if (!rows.length) { rewardRow(t('Los nuevos recibos de misiones y recompensas aparecer\u00e1n aqu\u00ed.'), null, t('Se registra el nombre cuando el juego permite identificarlo.')); }
        viewport.scrollTop = top;
        queueLayout();
    }
    function renderData() {
        renderLanguage();
        var payload = state.payload || {};
        var summary = battleSummary();
        var count = number(summary.battle_count);
        var pending = number((payload.summary || {}).pending_battles);
        var net = ready() ? number(summary.net_credits) : null;
        var goalBase = ready() ? number(currentGoal().baseline) : null;
        var savedGoal = currentGoal();
        var hasGoal = number(savedGoal.target) !== null && savedGoal.target > 0;
        var goalRemaining = ready() && hasGoal && number(payload.balance) !== null ? number(savedGoal.remaining) : null;
        var summaryNodes, statIndex;
        if (goalRemaining !== null) { goalRemaining = Math.max(0, goalRemaining); }
        var balance = ready() ? number(payload.balance) : null;
        var message = typeof payload.message === 'string' ? t(payload.message) : '';
        var error = t(state.viewModeError || state.localError || (typeof payload.error === 'string' ? payload.error : ''));
        if (!message) { message = ready() ? t('Datos de tu cuenta actual') : t('Esperando los datos de tu cuenta\u2026'); }
        if (ready()) { message = t('Datos en vivo | ') + message; }
        if (pending !== null && pending > 0) { message += ' \u00b7 ' + integerText(pending) + (pending === 1 ? t(' resultado pendiente') : t(' resultados pendientes')); }
        setText(nodes.message, message);
        setText(nodes['backend-error'], error);
        show(nodes['backend-error'], error !== '');
        setText(nodes['net-label'], state.vehicleFilter !== 'all' ? t('Ganancia o p\u00e9rdida del veh\u00edculo') : state.modeFilter === 'all' ? t('Ganancia o p\u00e9rdida total') : t('Ganancia o p\u00e9rdida del modo'));
        setText(nodes['battle-count'], ready() && count !== null ? integerText(count) +
            (count === 1 ? t(' partida registrada') : t(' partidas registradas')) + (state.modeFilter === 'all' ? '' : ' \u00b7 ' + modeFilterLabel()) +
            (state.vehicleFilter === 'all' ? '' : ' \u00b7 ' + vehicleGroupLabel(selectedVehicleGroup())) : vehicleAwaiting() ? t('Partidas pendientes de filtrar') : t('Partidas registradas'));
        setText(nodes['net-total'], signedText(net));
        colorNumber(nodes['net-total'], net);
        setText(nodes['goal-base'], goalBase === null ? '\u2014' : integerText(goalBase));
        colorNumber(nodes['goal-base'], goalBase);
        setText(nodes['goal-base-status'], !ready() ? t('Esperando tu cuenta') : goalBase === null ? t('Sin meta iniciada') : activeGoal(currentGoal()) ? t('Base de tu meta actual') : t('\u00daltima meta \u00b7 sin meta activa'));
        setText(nodes.balance, balance === null ? (ready() ? t('Pendiente') : '\u2014') : integerText(balance));
        colorNumber(nodes.balance, balance);
        setText(nodes['goal-remaining'], integerText(goalRemaining));
        colorNumber(nodes['goal-remaining'], goalRemaining);
        setText(nodes['goal-remaining-status'], !ready() ? t('Esperando tu cuenta') : !hasGoal ? t('Sin meta activa') :
            goalRemaining === null ? t('Saldo pendiente') : goalRemaining === 0 ? t('Meta alcanzada') : t('Para completar la meta'));
        summaryNodes = [nodes['net-total'], nodes['goal-base'], nodes.balance, nodes['goal-remaining']];
        for (statIndex = 0; statIndex < summaryNodes.length; statIndex += 1) {
            setClass(summaryNodes[statIndex], 'lc-value-long', summaryNodes[statIndex].textContent.length > 12);
        }
        setClass(nodes.balance, 'lc-muted', balance === null);
        disable(nodes.refresh, !state.connected || state.pendingRefresh);
        show(nodes.refresh, error !== '');
        setText(nodes.refresh, state.pendingRefresh ? t('Actualizando\u2026') : t('Actualizar'));
        disable(nodes['history-toggle'], !ready() || vehicleAwaiting());
        renderViewMode();
        renderWidget();
        renderGoal();
        renderModeFilter();
        renderVehicleFilter();
        renderDetail();
        renderHistory();
        renderDraft();
        renderHistoryControl();
        renderWallet();
        renderRewards();
        renderArchive();
        renderGoalCompletion();
    }
    function applyPayload(payload) {
        var goal;
        var incomingDigits;
        var incomingMode;
        var acknowledge;
        var resetAcknowledge;
        var resetRequest;
        var previousMode = state.viewMode;
        var incomingViewMode;
        var modeRollback = false;
        var wasWindowReady = !!(state.payload && state.payload.window && state.payload.window.ready);
        if (!payload || payload.schema !== 1 || typeof payload.ready !== 'boolean') {
            state.localError = t('No se pudieron leer los datos del panel. Pulsa Actualizar.');
            state.pendingRefresh = false;
            state.pendingSave = false;
            state.pendingGoalReset = null;
            if (state.vehicleRequest) { state.vehicleRequest = null; state.vehicleFeedback = t('No se pudo filtrar el veh\u00edculo. Puedes reintentar.'); }
            renderData();
            return;
        }
        acceptLanguage(payload);
        incomingViewMode = payload.view_mode;
        if (validViewMode(incomingViewMode)) {
            if (state.pendingViewMode !== null && state.pendingViewMode !== incomingViewMode &&
                    typeof payload.error === 'string' && payload.error.replace(/^\s+|\s+$/g, '') !== '') {
                state.pendingViewMode = null;
                state.chosenViewMode = null;
                state.viewMode = incomingViewMode;
                modeRollback = true;
            } else if ((state.chosenViewMode === null || state.chosenViewMode === incomingViewMode) &&
                    (state.pendingViewMode === null || state.pendingViewMode === incomingViewMode)) {
                state.viewMode = incomingViewMode;
                if (state.pendingViewMode === incomingViewMode) { state.pendingViewMode = null; }
            }
        }
        goal = payload.goal || {};
        incomingDigits = digitsOfNumber(goal.target);
        incomingMode = 'balance_growth';
        resetRequest = state.pendingGoalReset;
        resetAcknowledge = resetRequest && resetGeneration(goal) > resetRequest.generation &&
            incomingDigits === resetRequest.value && incomingMode === resetRequest.mode;
        acknowledge = state.pendingSave && incomingDigits === state.draftDigits && incomingMode === state.draftMode;
        if ((!state.dirty || acknowledge || state.payload === null) && !resetRequest) {
            state.draftDigits = incomingDigits;
            state.draftMode = incomingMode;
            state.invalid = '';
            state.rejectedRaw = null;
            var formattedIncoming = groupDigits(incomingDigits);
            if (nodes.target.value !== formattedIncoming) { nodes.target.value = formattedIncoming; }
        }
        state.savedDigits = incomingDigits;
        state.savedMode = incomingMode;
        if (resetRequest && payload.error) {
            state.pendingGoalReset = null;
            state.feedback = t('No se reinici\u00f3 la meta. Conservas tu avance; puedes volver a intentarlo.');
        } else if (resetAcknowledge) {
            state.pendingGoalReset = null;
            state.feedback = t('Meta reiniciada desde tu saldo actual, en 0 %. El historial se conserva.');
        } else if (resetRequest && resetGeneration(goal) > resetRequest.generation) {
            state.pendingGoalReset = null;
            state.feedback = t('La meta cambi\u00f3 durante el reinicio. Revisa la cantidad y vuelve a intentarlo.');
        } else if (acknowledge) {
            state.pendingSave = false;
            state.pendingGoalReset = null;
            state.feedback = incomingDigits === '0' ? t('Sin meta activa. Tu contabilidad contin\u00faa.') : t('Meta guardada.');
        } else if (state.pendingSave && payload.error) {
            state.pendingSave = false;
            state.feedback = t('No se guard\u00f3 la meta. Puedes volver a intentarlo.');
        }
        state.payload = payload;
        acceptModeFilter(payload);
        acceptHistoryControl(payload);
        acceptVehicleFilter(payload);
        acceptArchive(payload);
        if (modeRollback) { state.viewModeError = t('No se pudo cambiar la vista. Puedes volver a intentarlo.'); }
        else if (!payload.error) { state.viewModeError = ''; }
        state.localError = modeRollback ? t('No se pudo cambiar la vista. Puedes volver a intentarlo.') : '';
        state.pendingRefresh = false;
        renderData();
        if (nativeView()) {
            var becameReady = !wasWindowReady && payload.window && payload.window.ready;
            fitWindow(becameReady === true || previousMode !== state.viewMode);
            if (becameReady || previousMode !== state.viewMode) { settleNativeSize(); }
            else { queueNativeSizeCheck(); }
        } else if (previousMode !== state.viewMode) { fitWindow(); }
    }
    function readModel() {
        var model = window.model;
        var raw;
        try {
            raw = model && model.payload;
            if (raw && typeof raw !== 'string' && typeof raw.value === 'string') { raw = raw.value; }
            if (typeof raw !== 'string') { throw new Error('missing payload'); }
            applyPayload(JSON.parse(raw));
        } catch (error) {
            state.localError = t('No se pudieron leer los datos del panel. Pulsa Actualizar.');
            state.pendingRefresh = false;
            state.pendingSave = false;
            state.pendingGoalReset = null;
            if (state.vehicleRequest) { state.vehicleRequest = null; state.vehicleFeedback = t('No se pudo filtrar el veh\u00edculo. Puedes reintentar.'); }
            renderData();
        }
    }
    function invoke(name, args) {
        var model = window.model;
        var command = model && model[name];
        try {
            if (typeof command === 'function') { command.call(model, args); return true; }
            if (command && typeof command.value === 'function') { command.value.call(command, args); return true; }
        } catch (error) {
            state.localError = t('El juego no pudo completar la acci\u00f3n. Pulsa Actualizar para intentarlo de nuevo.');
            return false;
        }
        state.localError = t('El panel a\u00fan no est\u00e1 conectado al juego.');
        return false;
    }
    function caretInfo(input) {
        var start = typeof input.selectionStart === 'number' ? input.selectionStart : input.value.length;
        var end = typeof input.selectionEnd === 'number' ? input.selectionEnd : start;
        return {start: start, end: end};
    }
    function setCaret(input, start, end) {
        if (typeof input.setSelectionRange === 'function') {
            try { input.setSelectionRange(start, end); } catch (ignore) { /* Some native focus states reject selection changes. */ }
        }
    }
    function digitsBefore(value, caret) {
        return (value.slice(0, caret).match(/[0-9]/g) || []).length;
    }
    function caretAfterDigits(value, count) {
        var index;
        var found = 0;
        if (count <= 0) { return 0; }
        for (index = 0; index < value.length; index += 1) {
            if (/[0-9]/.test(value.charAt(index))) { found += 1; }
            if (found === count) { return index + 1; }
        }
        return value.length;
    }
    function editTarget(strictPaste) {
        var input = nodes.target;
        var raw = input.value;
        var selection = caretInfo(input);
        var leftCount = digitsBefore(raw, selection.start);
        var rightCount = digitsBefore(raw, selection.end);
        var digits;
        var removedZeros;
        var formatted;
        if (state.invalid && state.rejectedRaw === raw) { renderDraft(); return; }
        state.rejectedRaw = null;
        if (raw.length > 64) {
            state.invalid = t('La meta m\u00e1xima es 9.007.199.254.740.991 cr\u00e9ditos.');
            state.rejectedRaw = raw;
            state.draftDigits = '';
            state.feedback = '';
            renderDraft();
            return;
        }
        var acceptable = strictPaste ?
            /^(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,3}(?:\s[0-9]{3})+)$/.test(raw.replace(/^\s+|\s+$/g, '')) :
            (state.language === 'en' ? /^[0-9,]*$/ : /^[0-9.]*$/).test(raw);
        state.feedback = '';
        if (!acceptable) {
            state.invalid = t('Usa cr\u00e9ditos enteros: por ejemplo 1.000.000. No se admiten decimales.');
            state.rejectedRaw = raw;
            state.draftDigits = '';
            renderDraft();
            return;
        }
        digits = raw.replace(/[^0-9]/g, '');
        formatted = cleanLeadingZeros(digits);
        removedZeros = digits.length - formatted.length;
        state.draftDigits = formatted;
        state.invalid = '';
        formatted = groupDigits(formatted);
        input.value = formatted;
        setCaret(input, caretAfterDigits(formatted, Math.max(0, leftCount - removedZeros)),
            caretAfterDigits(formatted, Math.max(0, rightCount - removedZeros)));
        renderDraft();
    }
    function keyName(event) {
        var code = event.keyCode || event.which;
        if (event.key) { return event.key; }
        if (code === 8) { return 'Backspace'; }
        if (code === 46) { return 'Delete'; }
        if (code === 27) { return 'Escape'; }
        if (code === 13) { return 'Enter'; }
        if (code === 40) { return 'ArrowDown'; }
        if (code === 38) { return 'ArrowUp'; }
        if (code === 33) { return 'PageUp'; }
        if (code === 34) { return 'PageDown'; }
        if (code === 36) { return 'Home'; }
        if (code === 35) { return 'End'; }
        if (code === 86) { return 'v'; }
        return '';
    }
    function onTargetKeyDown(event) {
        var key = keyName(event);
        var selection = caretInfo(nodes.target);
        var raw = nodes.target.value;
        var remove = -1;
        if (key === 'ArrowUp' || key === 'ArrowDown') {
            event.preventDefault(); event.stopPropagation();
            stepTarget(key === 'ArrowUp' ? 1 : -1); return;
        }
        if ((event.ctrlKey || event.metaKey) && key.toLowerCase() === 'v') {
            state.pasteExpected = true;
            state.pasteSelection = {before: raw.slice(0, selection.start), after: raw.slice(selection.end)};
            return;
        }
        var separator = state.language === 'en' ? ',' : '.';
        if (selection.start !== selection.end || !(state.language === 'en' ? /^[0-9,]*$/ : /^[0-9.]*$/).test(raw)) { return; }
        if (key === 'Backspace' && raw.charAt(selection.start - 1) === separator) { remove = selection.start - 2; }
        if (key === 'Delete' && raw.charAt(selection.start) === separator) { remove = selection.start + 1; }
        if (remove >= 0 && remove < raw.length) {
            event.preventDefault();
            nodes.target.value = raw.slice(0, remove) + raw.slice(remove + 1);
            setCaret(nodes.target, Math.min(selection.start, remove), Math.min(selection.start, remove));
            editTarget(false);
        }
    }
    function pasteTarget(event) {
        var data = event.clipboardData;
        var pasted;
        var selection;
        var valid;
        if (!data || typeof data.getData !== 'function') { return; }
        pasted = data.getData('text').replace(/^\s+|\s+$/g, '');
        selection = caretInfo(nodes.target);
        valid = pasted.length <= 64 && /^(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,3}(?:\s[0-9]{3})+)$/.test(pasted);
        event.preventDefault();
        state.pasteExpected = false;
        state.pasteSelection = null;
        if (!valid) {
            state.invalid = t('No se peg\u00f3 la cantidad. Usa un entero como 1.000.000, sin decimales.');
            state.rejectedRaw = nodes.target.value;
            state.feedback = '';
            renderDraft();
            return;
        }
        state.rejectedRaw = null;
        pasted = pasted.replace(/[^0-9]/g, '');
        nodes.target.value = nodes.target.value.slice(0, selection.start) + pasted + nodes.target.value.slice(selection.end);
        setCaret(nodes.target, selection.start + pasted.length, selection.start + pasted.length);
        editTarget(false);
    }
    function onTargetKeyUp() {
        var expected = state.pasteSelection;
        var raw = nodes.target.value;
        var inserted;
        var valid;
        if (state.pasteExpected && expected) {
            state.pasteExpected = false;
            state.pasteSelection = null;
            inserted = raw.slice(expected.before.length, raw.length - expected.after.length).replace(/^\s+|\s+$/g, '');
            valid = inserted.length <= 64 && /^(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+|[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,3}(?:\s[0-9]{3})+)$/.test(inserted);
            if (!valid) {
                state.invalid = t('Usa un entero como 1.000.000, sin decimales.');
                state.draftDigits = '';
                state.rejectedRaw = raw;
                state.feedback = '';
                renderDraft();
                return;
            }
            state.rejectedRaw = null;
            nodes.target.value = expected.before + inserted.replace(/[^0-9]/g, '') + expected.after;
            setCaret(nodes.target, expected.before.length + inserted.replace(/[^0-9]/g, '').length,
                expected.before.length + inserted.replace(/[^0-9]/g, '').length);
        }
        editTarget(false);
    }
    function saveGoal() {
        if (!ready() || mutationPending() || state.invalid || !validDigits(state.draftDigits) ||
                (state.draftDigits !== '0' && number(state.payload.balance) === null)) { return; }
        state.pendingSave = true;
        state.feedback = '';
        state.localError = '';
        if (!invoke('onSaveGoal', {value: state.draftDigits, mode: state.draftMode})) { state.pendingSave = false; }
        renderData();
    }
    function resetGoal() {
        if (!ready() || mutationPending() || state.invalid || !validDigits(state.draftDigits) ||
                Number(state.draftDigits) <= 0 || number(state.payload.balance) === null) { return; }
        state.pendingGoalReset = {value:state.draftDigits, mode:state.draftMode, generation:resetGeneration(currentGoal())};
        state.feedback = '';
        state.localError = '';
        if (!invoke('onResetGoal', {value:state.draftDigits, mode:state.draftMode})) { state.pendingGoalReset = null; }
        renderData();
    }
    function stepTarget(direction) {
        if (!ready() || mutationPending()) { return; }
        var amount = Number(state.draftDigits || 0);
        if (!isFinite(amount) || amount < 0 || amount > 9007199254740991) { amount = 0; }
        amount = Math.max(0, Math.min(9007199254740991, amount + direction * 100000));
        nodes.target.value = String(amount);
        state.invalid = ''; state.rejectedRaw = null;
        editTarget(false);
    }
    function minimizePanel() { setViewMode('minimized'); }
    function refreshPanel() {
        if (!state.connected || state.pendingRefresh) { return; }
        state.pendingRefresh = true;
        state.localError = '';
        if (!invoke('onRefresh', {})) { state.pendingRefresh = false; }
        renderData();
    }
    function inside(node, ancestor) {
        while (node) { if (node === ancestor) { return true; } node = node.parentNode; }
        return false;
    }
    function onDocumentKey(event) {
        var key = keyName(event);
        if (key === 'Escape' || key === 'Esc') {
            if (state.viewMode === 'minimized') { return; }
            event.preventDefault();
            event.stopPropagation();
            if (state.viewMode === 'details' && state.historyConfirm) { cancelHistoryReset(); }
            else if (state.viewMode === 'details' && state.archivePicker !== null) { setArchivePicker(null); }
            else if (state.viewMode === 'details' && state.modePickerOpen) { setModePicker(false); nodes['mode-toggle'].focus(); }
            else if (state.viewMode === 'details' && state.vehiclePickerOpen) { setVehiclePicker(false); nodes['vehicle-toggle'].focus(); }
            else if (state.viewMode === 'details' && state.pickerOpen) { setPicker(false); nodes['history-toggle'].focus(); }
            else if (state.viewMode === 'details') { setViewMode('widget'); }
            else { minimizePanel(); }
        }
    }
    nodes.close.addEventListener('click', minimizePanel);
    nodes['widget-close'].addEventListener('click', minimizePanel);
    nodes['minimized-restore'].addEventListener('click', function () { setViewMode('widget'); });
    nodes['minimized-move'].addEventListener('mousedown', startWindowMove, false);
    function bindCircleHover(node) {
        node.addEventListener('mouseenter', enterCircle, false);
        node.addEventListener('mouseleave', leaveCircle, false);
    }
    bindCircleHover(nodes['minimized-restore']);
    bindCircleHover(nodes['minimized-move']);
    nodes.minimized.addEventListener('mouseleave', function () {
        clearCircleHideTimer(); state.circleHovered = false; renderCircleHandle();
    }, false);
    nodes.minimized.addEventListener('focusin', function () { renderCircleHandle(); }, false);
    nodes.minimized.addEventListener('focusout', function (event) {
        if (!inside(event.relatedTarget, nodes.minimized)) { state.circleKeyboard = false; renderCircleHandle(); }
    }, false);
    document.addEventListener('mousedown', function () { state.circleKeyboard = false; renderCircleHandle(); }, true);
    document.addEventListener('keydown', function (event) {
        if (keyName(event) === 'Tab' && state.viewMode === 'minimized') { state.circleKeyboard = true; renderCircleHandle(); }
    }, true);
    window.addEventListener('blur', clearCircleInteraction, false);
    nodes['widget-details'].addEventListener('click', function () { setViewMode('details'); });
    nodes['back-widget'].addEventListener('click', function () { setViewMode('widget'); });
    nodes['language-es'].addEventListener('click', function () { chooseLanguage('es'); });
    nodes['language-en'].addEventListener('click', function () { chooseLanguage('en'); });
    nodes['language-retry'].addEventListener('click', function () { if (state.languageRetry) { chooseLanguage(state.languageRetry); } });
    function keepDraftFocus(event) {
        if (document.activeElement === nodes.target) { event.preventDefault(); }
    }
    nodes['language-es'].addEventListener('mousedown', keepDraftFocus);
    nodes['language-en'].addEventListener('mousedown', keepDraftFocus);
    nodes['widget-drag-bar'].addEventListener('mousedown', startWindowMove, false);
    nodes['widget-chart'].addEventListener('mousedown', startWindowMove, false);
    nodes['drag-bar'].addEventListener('mousedown', startWindowMove, false);
    document.addEventListener('mousemove', updateWindowMove, false);
    document.addEventListener('mouseup', stopWindowMove, false);
    nodes.refresh.addEventListener('click', refreshPanel);
    nodes['archive-toggle'].addEventListener('click', toggleArchive);
    nodes['archive-retry'].addEventListener('click', function () { if (!state.archiveRequest) { requestArchive(); renderArchive(); } });
    function bindArchivePicker(kind) {
        nodes['archive-' + kind + '-toggle'].addEventListener('click', function () {
            if (!nodes['archive-' + kind + '-toggle'].disabled) { setArchivePicker(state.archivePicker === kind ? null : kind); }
        });
    }
    for (i = 0; i < archiveKinds.length; i += 1) { bindArchivePicker(archiveKinds[i]); }
    nodes['history-reset'].addEventListener('click', resetHistory);
    nodes['history-confirm'].addEventListener('click', confirmHistoryReset);
    nodes['history-cancel'].addEventListener('click', cancelHistoryReset);
    nodes['save-goal'].addEventListener('click', saveGoal);
    nodes['reset-goal'].addEventListener('click', resetGoal);
    nodes['target-up'].addEventListener('click', function () { if (!nodes['target-up'].disabled) { stepTarget(1); } });
    nodes['target-down'].addEventListener('click', function () { if (!nodes['target-down'].disabled) { stepTarget(-1); } });
    nodes.target.addEventListener('keydown', onTargetKeyDown);
    nodes.target.addEventListener('keyup', onTargetKeyUp);
    nodes.target.addEventListener('input', function () { if (!state.pasteExpected) { editTarget(false); } });
    nodes.target.addEventListener('paste', pasteTarget);
    nodes.target.addEventListener('blur', function () { if (!state.invalid) { editTarget(false); } });
    nodes['history-toggle'].addEventListener('click', function () { if (ready()) { setPicker(!state.pickerOpen); } });
    nodes['mode-toggle'].addEventListener('click', function () { if (ready() && modeGroups(state.payload).length) { setModePicker(!state.modePickerOpen); } });
    nodes['mode-toggle'].addEventListener('keydown', function (event) {
        if (keyName(event) === 'ArrowDown' && ready() && modeGroups(state.payload).length) {
            event.preventDefault(); setModePicker(true);
            if (nodes['mode-list'].firstChild) { nodes['mode-list'].firstChild.focus(); }
        }
    });
    nodes['vehicle-toggle'].addEventListener('click', function () { if (ready() && vehicleGroups().length) { setVehiclePicker(!state.vehiclePickerOpen); } });
    nodes['vehicle-toggle'].addEventListener('keydown', function (event) {
        if (keyName(event) === 'ArrowDown' && ready() && vehicleGroups().length) {
            event.preventDefault(); setVehiclePicker(true);
            if (nodes['vehicle-list'].firstChild) { nodes['vehicle-list'].firstChild.focus(); }
        }
    });
    nodes['vehicle-retry'].addEventListener('click', function () { if (!state.vehicleRequest) { requestVehicleFilter(); renderData(); } });
    nodes['history-toggle'].addEventListener('keydown', function (event) {
        if (keyName(event) === 'ArrowDown' && ready()) {
            event.preventDefault();
            setPicker(true);
            if (nodes['history-list'].firstChild) { nodes['history-list'].firstChild.focus(); }
        }
    });
    document.addEventListener('keydown', onDocumentKey);
    document.addEventListener('click', function (event) {
        if (inside(event.target, nodes['language-controls']) || inside(event.target, nodes['language-retry'])) { return; }
        if (state.archivePicker !== null && !inside(event.target, nodes['archive-' + state.archivePicker + '-toggle']) && !inside(event.target, nodes['archive-' + state.archivePicker + '-menu'])) { setArchivePicker(null); }
        if (!inside(event.target, nodes['history-toggle']) && !inside(event.target, nodes['history-menu'])) { setPicker(false); }
        if (!inside(event.target, nodes['mode-toggle']) && !inside(event.target, nodes['mode-menu'])) { setModePicker(false); }
        if (!inside(event.target, nodes['vehicle-toggle']) && !inside(event.target, nodes['vehicle-menu'])) { setVehiclePicker(false); }
    });

    function onDataChanged() { if (!state.disposed) { readModel(); } }
    function connect() {
        if (state.disposed || state.connected) { return; }
        bridgeEngine = window.engine || bridgeEngine;
        bridgeViewEnv = window.viewEnv || bridgeViewEnv;
        state.engineReady = true;
        state.connected = true;
        if (bridgeEngine && typeof bridgeEngine.on === 'function') { bridgeEngine.on('viewEnv.onDataChanged', onDataChanged); }
        if (bridgeViewEnv && typeof bridgeViewEnv.addDataChangedCallback === 'function') {
            state.callbackId = bridgeViewEnv.addDataChangedCallback('model', 0, true);
        }
        if (bridgeEngine && typeof bridgeEngine.on === 'function') {
            bridgeEngine.on('clientResized', onClientSizeChanged);
            bridgeEngine.on('self.onScaleUpdated', onClientSizeChanged);
            bridgeEngine.on('self.onLoaded', onNativeLoaded);
            bridgeEngine.on('self.onTextureReady', onNativeTextureReady);
            bridgeEngine.on('mouseup', stopWindowMove);
        }
        fitWindow();
        readModel();
        settleNativeSize();
    }
    function scheduleConnect() {
        if (state.disposed || state.startScheduled) { return; }
        state.startScheduled = true;
        // Size a normal native window before waiting for rendered frames: a
        // zero-sized view may not deliver animation frames at all.
        connect();
    }
    function listenForDom() {
        if (state.disposed || state.domWait || state.domReady) { return; }
        if (window.isDomBuilt) { state.domReady = true; return; }
        if (!bridgeEngine || typeof bridgeEngine.on !== 'function') { state.domReady = true; return; }
        state.domWait = function () {
            if (bridgeEngine && typeof bridgeEngine.off === 'function') { bridgeEngine.off('self.onDomBuilt', state.domWait); }
            state.domWait = null;
            state.domReady = true;
            if (state.engineReady) { scheduleConnect(); }
        };
        bridgeEngine.on('self.onDomBuilt', state.domWait);
    }
    function engineReady() {
        if (state.disposed) { return; }
        state.engineReady = true;
        // Request native bounds before waiting for DOM measurement. Waiting for
        // onDomBuilt first leaves normal Wulf windows stuck at the default size.
        bridgeViewEnv = window.viewEnv || bridgeViewEnv;
        fitWindow();
        if (window.isDomBuilt) { state.domReady = true; }
        if (state.domReady) { scheduleConnect(); }
        else { listenForDom(); }
    }
    function dispose() {
        var index;
        state.disposed = true; clearVehicleTimer(); clearArchiveTimer(); clearLanguageTimer(); cancelGoalCompletion();
        state.sizingGeneration += 1;
        if (state.sizingTimer !== null) { window.clearTimeout(state.sizingTimer); state.sizingTimer = null; }
        stopWindowMove();
        clearCircleInteraction();
        window.removeEventListener('blur', clearCircleInteraction, false);
        document.removeEventListener('mousemove', updateWindowMove, false);
        document.removeEventListener('mouseup', stopWindowMove, false);
        for (index = 0; index < scrollers.length; index += 1) { scrollers[index].dispose(); }
        window.removeEventListener('resize', fitWindow);
        if (bridgeEngine && typeof bridgeEngine.off === 'function') { bridgeEngine.off('viewEnv.onDataChanged', onDataChanged); }
        if (bridgeEngine && typeof bridgeEngine.off === 'function') {
            bridgeEngine.off('clientResized', onClientSizeChanged);
            bridgeEngine.off('self.onScaleUpdated', onClientSizeChanged);
            bridgeEngine.off('self.onLoaded', onNativeLoaded);
            bridgeEngine.off('self.onTextureReady', onNativeTextureReady);
            bridgeEngine.off('mouseup', stopWindowMove);
        }
        if (state.domWait && bridgeEngine && typeof bridgeEngine.off === 'function') { bridgeEngine.off('self.onDomBuilt', state.domWait); }
        if (state.callbackId !== null && bridgeViewEnv && typeof bridgeViewEnv.removeDataChangedCallback === 'function') {
            try { bridgeViewEnv.removeDataChangedCallback(state.callbackId, 0); } catch (ignore) { /* Native view may already be gone. */ }
        }
        document.removeEventListener('keydown', onDocumentKey);
        nodes.content.removeEventListener('scroll', renderGoalCompletion, false);
        document.removeEventListener('visibilitychange', renderGoalCompletion, false);
    }
    window.addEventListener('unload', dispose);
    nodes.content.addEventListener('scroll', renderGoalCompletion, false);
    document.addEventListener('visibilitychange', renderGoalCompletion, false);
    scrollControl(nodes.content, document.getElementById('lc-content-track'), document.getElementById('lc-content-thumb'));
    scrollControl(nodes['history-options'], document.getElementById('lc-history-track'), document.getElementById('lc-history-thumb'));
    scrollControl(nodes['mode-options'], document.getElementById('lc-mode-track'), document.getElementById('lc-mode-thumb'));
    scrollControl(nodes['vehicle-options'], document.getElementById('lc-vehicle-track'), document.getElementById('lc-vehicle-thumb'));
    for (i = 0; i < archiveKinds.length; i += 1) {
        scrollControl(nodes['archive-' + archiveKinds[i] + '-options'], document.getElementById('lc-archive-' + archiveKinds[i] + '-track'), document.getElementById('lc-archive-' + archiveKinds[i] + '-thumb'));
    }
    scrollControl(nodes['archive-battle-options'], document.getElementById('lc-archive-battle-track'), document.getElementById('lc-archive-battle-thumb'));

    scrollControl(document.getElementById('lc-rewards-viewport'), document.getElementById('lc-rewards-track'), document.getElementById('lc-rewards-thumb'));
    window.addEventListener('resize', fitWindow);
    fitWindow();
    renderData();
    if (bridgeEngine && bridgeEngine.whenReady && typeof bridgeEngine.whenReady.then === 'function') {
        // Listen immediately: native DOM readiness may arrive before the engine promise.
        listenForDom();
        bridgeEngine.whenReady.then(engineReady, function () {
            state.localError = t('No se pudo conectar la interfaz con el juego.');
            renderData();
        });
    } else if (window.model) { connect(); }
    else {
        state.localError = t('Esperando la conexi\u00f3n del juego.');
        renderData();
    }
}());
