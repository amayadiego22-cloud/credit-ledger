# -*- coding: utf-8 -*-
"""Convert explicitly reconciled native credits into the ledger contract."""
import time

from .native import POLICY
from .vehicles import normalize_vehicles
from .battle_modes import battle_mode_from_common

try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


class ReconciliationError(ValueError):
    pass


def result_time(snapshot):
    """Use the battle's end time, including results received from an old cache."""
    occurred_at = snapshot["captured_at"]
    common = snapshot.get("common", {})
    start = common.get("arenaCreateTime")
    duration = common.get("duration")
    if (isinstance(start, integer_types) and not isinstance(start, bool) and start > 0
            and isinstance(duration, integer_types) and not isinstance(duration, bool)
            and 0 <= duration <= 86400):
        occurred_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start + duration))
    return occurred_at


def normalize_snapshot(snapshot):
    native = snapshot.get("native_credits")
    if (not isinstance(native, dict) or native.get("policy") != POLICY
            or native.get("row_kind") != "aggregate"):
        raise ReconciliationError("native credit records are missing or unverified")
    totals = native.get("totals", {})
    for field in ("gross", "repair", "ammo", "consumables", "other", "net"):
        amount = totals.get(field)
        if isinstance(amount, bool) or not isinstance(amount, integer_types):
            raise ReconciliationError("native %s is not an integer" % field)
        if field != "net" and amount < 0:
            raise ReconciliationError("native %s cannot be negative" % field)
    expenses = dict((key, totals[key]) for key in ("repair", "ammo", "consumables", "other"))
    if totals["net"] != totals["gross"] - sum(expenses.values()):
        raise ReconciliationError("native credit totals do not reconcile")
    rows = native.get("rows")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ReconciliationError("native rows are missing")
    for field in totals:
        if field in ("gross", "repair", "ammo", "consumables", "other", "net"):
            try:
                observed = sum(row[field] for row in rows)
            except (TypeError, KeyError):
                raise ReconciliationError("native row is incomplete")
            if observed != totals[field]:
                raise ReconciliationError("native rows disagree with totals")
    credits = {"gross": totals["gross"], "expenses": expenses}
    if "reserves" in native:
        reserves = native["reserves"]
        if not isinstance(reserves, dict) or set(reserves) != set(("personal", "clan")):
            raise ReconciliationError("native reserve credits are incomplete")
        for kind in ("personal", "clan"):
            amount = reserves[kind]
            if isinstance(amount, bool) or not isinstance(amount, integer_types) or amount < 0:
                raise ReconciliationError("native %s reserve credits are invalid" % kind)
        if sum(reserves.values()) > totals["gross"]:
            raise ReconciliationError("native reserve credits exceed gross credits")
        # These are included parts of the verified aggregate, never extra income.
        credits["reserves"] = dict((kind, reserves[kind]) for kind in ("personal", "clan"))
    occurred_at = result_time(snapshot)
    return {"region": snapshot["region"], "account_id": snapshot["account_id"],
            "battle_id": snapshot["battle_id"], "occurred_at": occurred_at,
            "vehicles": normalize_vehicles(snapshot.get("personal", {}).get("vehicles", [])),
            "battle_mode": battle_mode_from_common(snapshot.get("common")),
            "status": "final", "credits": credits}
