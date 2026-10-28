# -*- coding: utf-8 -*-
"""Presentation-only Spanish/English strings; never rewrite native records."""
import re

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


def language(config):
    value = config.get("ui_language") if isinstance(config, dict) else None
    return value if isinstance(value, string_types) and value in ("es", "en") else "es"


_EN = {
    u"Introduce una cantidad entera igual o mayor que cero.": u"Enter a whole number greater than or equal to zero.",
    u"La meta debe estar entre 0 y 9.007.199.254.740.991 créditos.": u"The goal must be between 0 and 9,007,199,254,740,991 credits.",
    u"Actualiza el panel para iniciar una meta desde tu saldo.": u"Refresh the panel to start a goal from your current balance.",
    u"Espera que se sincronice tu cuenta antes de guardar la meta.": u"Wait for your account to sync before saving the goal.",
    u"Espera que se sincronice tu saldo antes de iniciar la meta.": u"Wait for your balance to sync before starting a goal.",
    u"La configuración de la meta guardada no es válida.": u"The saved goal settings are invalid.",
    u"La cantidad de la meta guardada no es válida.": u"The saved goal amount is invalid.",
    u"El contador de reinicios de la meta no es válido.": u"The saved goal reset counter is invalid.",
    u"La base o la fecha de la meta guardada no es válida.": u"The saved goal's starting balance or date is invalid.",
    u"La fecha de inicio de la meta no es válida.": u"The goal's start date is invalid.",
    u"La suma del saldo y la meta supera el límite permitido.": u"Your balance plus the goal exceeds the supported limit.",
    u"Introduce una cantidad mayor que cero para reiniciar la meta.": u"Enter an amount greater than zero to reset the goal.",
    u"El contador de reinicios de la meta supera el límite admitido.": u"The goal reset counter exceeds the supported limit.",
    u"La fecha del reinicio no es una fecha UTC válida.": u"The reset date is not a valid UTC date.",
    u"Espera que se sincronice tu cuenta antes de cambiar el historial.": u"Wait for your account to sync before changing the history.",
    u"Las opciones del historial no son válidas.": u"The history settings are invalid.",
    u"Selecciona reinicio manual, diario o del servidor.": u"Choose manual, daily, or server reset.",
    u"La hora de reinicio debe estar entre 0 y 23.": u"The reset hour must be between 0 and 23.",
    u"La opción de conservar la meta no es válida.": u"The keep-goal option is invalid.",
    u"Espera que se sincronice tu saldo antes de reiniciar el historial.": u"Wait for your balance to sync before resetting the history.",
    u"El tipo de reinicio no es válido.": u"The reset type is invalid.",
    u"La opción de reiniciar la meta no es válida.": u"The reset-goal option is invalid.",
    u"El contador de reinicios supera el límite admitido.": u"The reset counter exceeds the supported limit.",
    u"Espera que se sincronice el horario del servidor antes de reiniciar.": u"Wait for the server time to sync before resetting.",
    u"La solicitud del filtro no es válida.": u"The filter request is invalid.",
    u"El modo seleccionado no es válido.": u"The selected game mode is invalid.",
    u"El vehículo seleccionado no es válido.": u"The selected vehicle is invalid.",
    u"La cuenta cambió. Vuelve a elegir el vehículo.": u"The account changed. Select the vehicle again.",
    u"No se pudo cargar el vehículo. Vuelve a intentarlo.": u"The vehicle could not be loaded. Please try again.",
    u"La cuenta cambió. Vuelve a elegir el día.": u"The account changed. Select the day again.",
    u"El día seleccionado no es válido.": u"The selected day is invalid.",
    u"No se pudo cargar el día. Vuelve a intentarlo.": u"The selected day could not be loaded. Please try again.",
    u"El reinicio diario del servidor es automático y permanece activo.": u"The daily server reset runs automatically and stays enabled.",
    u"No se pudieron guardar los ajustes del historial.": u"The history settings could not be saved.",
    u"Confirma el reinicio del historial en el panel.": u"Confirm the history reset in the panel.",
    u"Espera que se sincronice tu cuenta antes de reiniciar el historial.": u"Wait for your account to sync before resetting the history.",
    u"No se pudo reiniciar el historial. Los datos anteriores se conservan.": u"The history could not be reset. Your previous data has been kept.",
    u"No se pudo guardar la meta. Revisa el archivo game.log.": u"The goal could not be saved. Check game.log for details.",
    u"Espera que se sincronice tu cuenta antes de reiniciar la meta.": u"Wait for your account to sync before resetting the goal.",
    u"No se pudo reiniciar la meta. Tu meta anterior se conserva.": u"The goal could not be reset. Your previous goal has been kept.",
    u"Contabilidad: no se pudo abrir el panel. Revisa game.log.": u"Credit Ledger: the panel could not be opened. Check game.log for details.",
    u"Selecciona el resumen o los detalles de contabilidad.": u"Choose the accounting summary or details view.",
    u"No se pudo guardar la vista de contabilidad.": u"The accounting view could not be saved.",
    u"Esperando que se sincronice tu cuenta del juego.": u"Waiting for your game account to sync.",
    u"Saldo pendiente de sincronizar; el historial ya está disponible.": u"Your balance is still syncing; your battle history is already available.",
    u"Tu próxima batalla finalizada aparecerá aquí.": u"Your next completed battle will appear here.",
    u"Jornada diaria del servidor; horario mostrado en la zona local del equipo.": u"Server day; times are shown in your computer's local time zone.",
    u"Solo se muestran partidas y recompensas registradas por el mod; los importes de batallas ya descuentan sus gastos.": u"Only battles and rewards recorded by the mod are shown. Battle amounts already include their expenses.",
    u"Contabilidad de créditos: captura activa. El widget aparece en el garaje; pulsa el círculo para abrir el resumen.": u"Credit Ledger: recording is active. The widget is available in the Garage; click the circle to open the summary.",
    u"Contabilidad: resultado guardado; desglose pendiente de conciliación.": u"Credit Ledger: result saved; the breakdown is waiting for reconciliation.",
    u"Contabilidad | Neto: %s%s cr. | Reparaciones: %s | Munición: %s | Consumibles/directivas: %s | Historial: %s cr.": u"Credit Ledger | Net: %s%s credits | Repairs: %s | Ammunition: %s | Consumables/directives: %s | History: %s credits",
    u" | Sin meta activa.": u" | No active goal.",
    u" | Meta alcanzada.": u" | Goal reached.",
    u" | Meta %s: faltan %s cr.": u" | Goal: %s credits; %s credits remaining.",
    u" | Meta: saldo pendiente de sincronizar.": u" | Goal: waiting for your balance to sync.",
    u"Selecciona español o inglés.": u"Choose Spanish or English.",
    u"No se pudo guardar el idioma. La selección anterior se conserva.": u"The language could not be saved. Your previous selection has been kept.",
}

_MODE_EN = {
    1: u"Random Battle", 2: u"Team Training", 4: u"Special Battle", 5: u"Special Battle",
    7: u"Team Battle", 9: u"Special Game Mode", 13: u"Global Map",
    14: u"Tournament Battle", 15: u"Clan Tournament", 18: u"Domination",
    19: u"Steel Hunt", 20: u"Skirmish", 21: u"Advance", 22: u"Ranked Battle",
    24: u"Grand Battle", 27: u"Frontline", 29: u"Steel Hunter", 37: u"Recon Mission",
    38: u"Topography", 43: u"Onslaught", 44: u"Warm-Up", 49: u"Onslaught Light",
    101: u"Dark Tower · Normal", 102: u"Dark Tower · Hard", 103: u"Dark Tower · Nightmare",
}
_REWARD_EN = {
    "tokenQuests": u"Mission / reward", "potapovQuestBonus": u"Campaign mission",
    "personalMission3Quest": u"Campaign mission", "personalMission4Quest": u"Campaign mission",
    "hangarQuests": u"Additional mission", "rankedQuests": u"Ranked mission",
    "royaleQuests": u"Event mission", "battlePassReward": u"Battle Pass reward",
    "piggyBankSmashed": u"Credit Reserve", "invoiceReceived": u"Credit deposit / withdrawal",
    "battleResults": u"Battle missions",
}


def translate(text, selected="es"):
    return _EN.get(text, text) if selected == "en" and isinstance(text, string_types) else text


def mode_label(code):
    return _MODE_EN.get(code, u"Unidentified mode (code %s)" % code)


def _vehicle_name(vehicle):
    old = vehicle.get("name")
    identity = vehicle.get("vehicle_type_id")
    if old == u"Vehículo " + str(identity):
        vehicle["name"] = u"Vehicle " + str(identity)
    return old, vehicle.get("name")


def _reward_title(item):
    if "quest_id" in item:
        if not item.get("name_resolved"):
            item["title"] = u"Mission " + str(item["quest_id"])
        elif isinstance(item.get("title"), string_types):
            # Translate only the wrapper generated by this mod. The native
            # challenge/mission name inside it stays exactly as supplied.
            match = re.match(u"^Crisol: (.*) \\| Misión (.*)$", item["title"])
            if match:
                item["title"] = u"Crucible: %s | Mission %s" % match.groups()
    elif item.get("kind") in _REWARD_EN:
        item["title"] = _REWARD_EN[item["kind"]]
    elif item.get("kind") == "battlePassVoucher" and isinstance(item.get("title"), string_types):
        prefix = u"Raspado de cupón del Pase de batalla"
        if item["title"].startswith(prefix):
            item["title"] = u"Battle Pass voucher scratch reward" + item["title"][len(prefix):]


def localize_payload(payload, config):
    """Modify only this freshly built UI projection, not any saved source."""
    selected = language(config)
    payload["language"] = selected
    if selected != "en":
        return payload
    from .local_clock import time_label

    def visit(node, parent=""):
        if isinstance(node, list):
            for child in node:
                visit(child, parent)
        elif isinstance(node, dict):
            if "bonus_type" in node and "label" in node:
                node["label"] = mode_label(node["bonus_type"])
            if parent == "mode_groups" and "key" in node:
                key = node["key"]
                node["label"] = (mode_label(int(key[5:])) if key.startswith("mode:")
                                 else u"Unidentified mode")
            if parent == "vehicle_groups":
                if node.get("key") == "unknown":
                    node["label"] = u"Unidentified vehicle"
                elif node.get("key") == "multiple":
                    node["label"] = u"Multiple vehicles"
                elif isinstance(node.get("vehicle"), dict):
                    old, new = _vehicle_name(node["vehicle"])
                    if node.get("label") == old:
                        node["label"] = new
            if parent == "vehicles":
                _vehicle_name(node)
            _reward_title(node)
            for key in ("message", "error", "scope_note", "timezone_label"):
                if key in node:
                    node[key] = translate(node[key], selected)
            for key, source in (("since_label", "since_utc"), ("next_reset_label", "next_reset_utc"),
                                ("started_at_label", "started_at")):
                if key in node:
                    node[key] = time_label(node.get(source), language=selected)
            if "time_label" in node:
                node["time_label"] = time_label(node.get("occurred_at"), compact=True, language=selected)
            if parent == "days" and node.get("key"):
                node["label"] = time_label(node["key"], language=selected).split(" ", 3)[0:3]
                node["label"] = u" ".join(node["label"])
            if parent == "selection" and "day_key" in node and node.get("label"):
                node["label"] = u" ".join(time_label(node["day_key"], language=selected).split(" ", 3)[:3])
            if parent == "history_control" and node.get("mode") != "server":
                node["timezone_label"] = node.get("timezone_label", "").replace(
                    u"Hora local del equipo", u"Computer's local time")
            for key, value in list(node.items()):
                if isinstance(value, (dict, list)):
                    visit(value, key)
    visit(payload)
    return payload
