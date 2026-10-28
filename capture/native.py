# -*- coding: utf-8 -*-
"""Read native finance record objects; do not reproduce economy multipliers.

The selection/record names are checked against the installed 2.4.1.0 report.
The aggregate total has been compared with a real battle report. Reserve
components use that same effective column; they are already in gross credits.
"""
import struct
import math

try:
    integer_types = (int, long)
    binary_types = (str, bytearray, buffer)
except NameError:
    integer_types = (int,)
    binary_types = (bytes, bytearray, memoryview)

POLICY = "wot-2.4.1-total-credits-v1"


class NativeFinanceError(ValueError):
    pass


def _integer(value, name):
    # Native CurrencyValueModel is a real-valued model. Integer-valued floats
    # are exact credit amounts; fractional, non-finite and unsafe values aren't.
    if (isinstance(value, float) and not math.isnan(value) and not math.isinf(value)
            and abs(value) <= 9007199254740991 and value == int(value)):
        return int(value)
    if isinstance(value, bool) or not isinstance(value, integer_types):
        raise NativeFinanceError("native %s is not an exact integer credit amount (%s)" %
                                 (name, type(value).__name__))
    return value


def _reserve_breakdown(effective, gross):
    """Use monetary replay deltas, never multiply advertised reserve rates.

    These are the installed report's BOOSTERS_CREDITS and
    BATTLE_PAYMENTS_CREDITS record names. The two personal names are added by
    getRecord, and a missing replay entry contributes an observed zero.
    """
    personal = _integer(effective.getRecord("boosterCredits", "boosterCreditsFactor100"),
                        "personal reserve")
    clan = _integer(effective.getRecord("orderCreditsFactor100"), "clan reserve")
    if personal < 0 or clan < 0 or personal + clan > gross:
        raise NativeFinanceError("native reserve components do not fit gross credits")
    return {"personal": personal, "clan": clan}


def derive_credits(results, create_reusable=None):
    personal_raw = results.get("personal", {}) if isinstance(results, dict) else {}
    vehicles = [value for key, value in personal_raw.items() if key != "avatar"]
    if not vehicles:
        raise NativeFinanceError("personal vehicle records are missing")
    replay_steps = []
    for vehicle in vehicles:
        replay = vehicle.get("creditsReplay") if isinstance(vehicle, dict) else None
        if not isinstance(replay, binary_types):
            raise NativeFinanceError("native creditsReplay buffer is missing")
        raw = bytes(replay)
        if len(raw) < 2:
            raise NativeFinanceError("native creditsReplay header is incomplete")
        count = struct.unpack("<H", raw[:2])[0]
        if len(raw) != 2 + 4 * count:
            raise NativeFinanceError("native creditsReplay length is invalid")
        replay_steps.append(count)
    if create_reusable is None:
        from gui.battle_results.reusable import createReusableInfo
        create_reusable = createReusableInfo
    reusable = create_reusable(results)
    personal = reusable.personal
    premium = personal.hasAnyPremium
    if not isinstance(premium, bool):
        raise NativeFinanceError("hasAnyPremium is not the expected property")
    totals = {"gross": 0, "repair": 0, "ammo": 0, "consumables": 0,
              "other": 0, "net": 0}
    rows = []
    # RecordsIterator yields the aggregate FIRST and then per-vehicle rows.
    # Reading every row would count the aggregate and its components twice.
    aggregate = next(iter(personal.getMoneyRecords()), None)
    if aggregate is None:
        raise NativeFinanceError("native result has no aggregate financial row")
    for records in (aggregate,):
        if not isinstance(records, (tuple, list)) or len(records) != 6:
            raise NativeFinanceError("native money row does not match 2.4.1")
        effective = records[1] if premium else records[0]
        additional = records[3]
        gross = _integer(effective.getRecord("credits", "originalCreditsToDraw",
                                             "originalCreditsToDrawSquad"), "gross")
        if gross < 0:
            raise NativeFinanceError("negative gross requires explicit penalty handling")
        row = {"gross": gross, "other": 0}
        for category, field in (("repair", "autoRepairCost"),
                                ("ammo", "autoLoadCredits"),
                                ("consumables", "autoEquipCredits")):
            signed = _integer(additional.getRecord(field), field)
            if signed > 0:
                raise NativeFinanceError("native expense has an unexpected positive sign")
            row[category] = -signed
        native_net = _integer(effective.getRecord("credits", "originalCreditsToDraw",
                                                  "originalCreditsToDrawSquad") +
                              additional.getRecord("autoRepairCost", "autoLoadCredits",
                                                   "autoEquipCredits"), "net")
        row["net"] = gross - row["repair"] - row["ammo"] - row["consumables"]
        if row["net"] != native_net:
            raise NativeFinanceError("native financial row does not reconcile")
        rows.append(row)
        for key in totals:
            totals[key] += row[key]
    if not rows:
        raise NativeFinanceError("native result has no financial rows")
    result = {"policy": POLICY, "row_kind": "aggregate", "has_any_premium": premium,
            "is_wot_plus": bool(personal.isWotPlus), "rows": rows,
            "totals": totals, "credits_replay_steps": replay_steps,
            "compared_with_real_report": False}
    try:
        result["reserves"] = _reserve_breakdown(effective, totals["gross"])
    except Exception as error:
        # An unavailable optional breakdown must not discard verified income.
        # Omission stays unknown in legacy/history views, rather than zero.
        result["reserves_error"] = type(error).__name__
    return result
