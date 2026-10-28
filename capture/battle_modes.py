# -*- coding: utf-8 -*-
"""Battle provenance from native common data, independent of money and tanks.

The bonus-type constants are verified against this installed 2.4.1.0 client.
GUI type is a separate enum and must never be used as a bonus-type fallback.
"""
try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


# Labels are presentation only. Persist the native codes so unknown future modes
# remain truthful and their labels can be added without rewriting battle totals.
_MODE_LABELS = {
    1: u"Batalla aleatoria",
    2: u"Entrenamiento en equipo",
    4: u"Batalla especial",
    5: u"Batalla especial",
    7: u"Batalla de equipo",
    9: u"Modo de juego especial",
    13: u"Mapa global",
    14: u"Batalla de torneo",
    15: u"Torneo de clanes",
    18: u"Dominación",
    19: u"Cacería de acero",
    20: u"Escaramuza",
    21: u"Avance",
    22: u"Batalla clasificatoria",
    24: u"Gran batalla",
    27: u"Línea del frente",
    29: u"Cazador de acero",
    37: u"Misión de reconocimiento",
    38: u"Topografía",
    43: u"Asedio",
    44: u"Entrada en calor",
    49: u"Asedio ligero",
    101: u"Torre oscura · Normal",
    102: u"Torre oscura · Difícil",
    103: u"Torre oscura · Pesadilla",
}


# Exact installed native selector resources for this supported client. Images
# remain in the game's packages; only these local references enter UI payloads.
_BASE_ART = 'coui://gui/maps/icons/battleTypes/'
_MODE_ICONS = dict((code, _BASE_ART + '64x64/' + name + '.png') for code, name in (
    (1, 'random'), (2, 'trainingsList'), (4, 'specBattlesList'),
    (5, 'specBattlesList'), (7, 'team7x7'), (9, 'event'),
    (14, 'specBattlesList'), (15, 'specBattlesList'),
    (18, 'fallout_classic'), (19, 'fallout_multiteam'),
    (20, 'strongholdsBattlesList'), (21, 'strongholdsBattlesList'),
    (22, 'ranked'), (24, 'ctf30x30'), (27, 'epicQueue'),
    (29, 'battle_royale'), (37, 'mapbox'), (38, 'mapsTraining'),
    (43, 'comp7'), (44, 'winback')))
_MODE_ICONS[13] = _BASE_ART + '136x136/clan.png'
_MODE_ICONS[49] = 'coui://comp7_light/gui/maps/icons/battleTypes/64x64/comp7_light.png'
for _code in (101, 102, 103):
    _MODE_ICONS[_code] = 'coui://halloween/gui/maps/icons/battleTypes/64x64/halloween.extend.png'


def _valid_code(value):
    return (not isinstance(value, bool) and isinstance(value, integer_types)
            and 0 <= value <= 2147483647)


def battle_mode_icon(bonus_type):
    """An unknown bonus code never inherits a logo from the garage selection."""
    return _MODE_ICONS.get(bonus_type) if _valid_code(bonus_type) else None


def battle_mode_from_common(common):
    """Read only the native battle-wide mode, never the selected garage mode."""
    if not isinstance(common, dict):
        return None
    field = "bonusType" if "bonusType" in common else "arenaBonusType"
    bonus_type = common.get(field)
    if not _valid_code(bonus_type):
        return None
    mode = {"bonus_type": bonus_type}
    gui_type = common.get("guiType")
    if _valid_code(gui_type):
        mode["gui_type"] = gui_type
    return mode


def battle_mode_payload(mode):
    """Copy safe mode metadata into UI data without altering the stored record."""
    if (not isinstance(mode, dict) or "bonus_type" not in mode
            or set(mode) - set(("bonus_type", "gui_type"))
            or not _valid_code(mode["bonus_type"])
            or ("gui_type" in mode and not _valid_code(mode["gui_type"]))):
        return None
    result = dict(mode)
    result["label"] = _MODE_LABELS.get(
        mode["bonus_type"], u"Modo no identificado (código %s)" % mode["bonus_type"])
    result["icon"] = battle_mode_icon(mode["bonus_type"])
    return result
