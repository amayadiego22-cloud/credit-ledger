# -*- coding: utf-8 -*-
"""Client-independent economy bookkeeping, compatible with Python 2.7 and 3.

Input adapters must supply gross credits before expenses and actual expense
amounts. No game API, game hooks, or balance inference is implemented here.
"""
from __future__ import division

import copy
import datetime
import io
import json
import math
import os
import re
import sys
import tempfile


try:
    string_types = (basestring,)
    integer_types = (int, long)
    text_type = unicode
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str


EXPENSE_CATEGORIES = ("repair", "ammo", "consumables", "other")
UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SCHEMA_VERSION = 1


class LedgerValidationError(ValueError):
    """An input or persisted document does not conform to the ledger schema."""


def _mapping(value, name):
    if not isinstance(value, dict):
        raise LedgerValidationError("%s must be an object" % name)
    return value


def _keys(value, required, optional, name):
    _mapping(value, name)
    actual = set(value)
    missing = set(required) - actual
    unexpected = actual - set(required) - set(optional)
    if missing:
        raise LedgerValidationError("%s is missing: %s" %
                                    (name, ", ".join(sorted(missing))))
    if unexpected:
        raise LedgerValidationError("%s contains unsupported fields" % name)


def _text(value, name):
    if not isinstance(value, string_types) or not value.strip():
        raise LedgerValidationError("%s must be a nonempty string" % name)
    return value.strip()


def _identifier(value, name):
    if isinstance(value, bool):
        raise LedgerValidationError("%s cannot be a boolean" % name)
    if isinstance(value, integer_types):
        if value < 0:
            raise LedgerValidationError("%s cannot be negative" % name)
        return text_type(value)
    return _text(value, name)


def _amount(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, integer_types):
        raise LedgerValidationError("%s must be an integer, not a boolean" % name)
    if value < 0 or (positive and value == 0):
        raise LedgerValidationError("%s must be %s" %
                                    (name, "positive" if positive else "nonnegative"))
    return value


def _utc(value, name):
    if not isinstance(value, string_types):
        raise LedgerValidationError("%s must use YYYY-MM-DDTHH:MM:SSZ UTC" % name)
    try:
        parsed = datetime.datetime.strptime(value, UTC_FORMAT)
    except (TypeError, ValueError):
        raise LedgerValidationError("%s must use YYYY-MM-DDTHH:MM:SSZ UTC" % name)
    if parsed.strftime(UTC_FORMAT) != value:
        raise LedgerValidationError("%s must use YYYY-MM-DDTHH:MM:SSZ UTC" % name)
    return value


def _normalize_credits(value):
    _keys(value, ("gross", "expenses"), ("reserves",), "credits")
    expenses = value["expenses"]
    _keys(expenses, EXPENSE_CATEGORIES, (), "credits.expenses")
    normalized = {
        "gross": _amount(value["gross"], "credits.gross"),
        "expenses": dict((category, _amount(expenses[category],
                            "credits.expenses.%s" % category))
                         for category in EXPENSE_CATEGORIES),
    }
    if "reserves" in value:
        reserves = value["reserves"]
        _keys(reserves, ("personal", "clan"), (), "credits.reserves")
        normalized["reserves"] = dict((kind, _amount(reserves[kind],
            "credits.reserves.%s" % kind)) for kind in ("personal", "clan"))
        if sum(normalized["reserves"].values()) > normalized["gross"]:
            raise LedgerValidationError("reserve credits exceed gross credits")
    return normalized


def _normalize_resources(value):
    _mapping(value, "resources")
    normalized = {}
    for name, amounts in value.items():
        resource = _text(name, "resource name").lower()
        if resource == "credits":
            raise LedgerValidationError("credits belong in the credits object")
        if resource in normalized:
            raise LedgerValidationError("resource names must be unique ignoring case")
        _keys(amounts, ("earned", "spent"), (), "resource %s" % resource)
        normalized[resource] = {
            "earned": _amount(amounts["earned"], "resources.%s.earned" % resource),
            "spent": _amount(amounts["spent"], "resources.%s.spent" % resource),
        }
    return normalized


def _normalize_record(value):
    _keys(value, ("region", "account_id", "battle_id", "occurred_at", "status"),
          ("credits", "resources", "vehicles", "battle_mode"), "result")
    status = value["status"]
    if status not in ("pending", "final"):
        raise LedgerValidationError("status must be pending or final")
    credits = value.get("credits")
    if credits is None and status == "final":
        raise LedgerValidationError("final results require complete credits")
    return {
        "region": _text(value["region"], "region").upper(),
        "account_id": _identifier(value["account_id"], "account_id"),
        "battle_id": _identifier(value["battle_id"], "battle_id"),
        "occurred_at": _utc(value["occurred_at"], "occurred_at"),
        "status": status,
        "credits": None if credits is None else _normalize_credits(credits),
        "resources": _normalize_resources(value.get("resources", {})),
        "vehicles": _normalize_vehicles(value.get("vehicles", [])),
        "battle_mode": _normalize_battle_mode(value.get("battle_mode")),
    }


def _normalize_battle_mode(value):
    if value is None:
        return None
    _keys(value, ("bonus_type",), ("gui_type",), "battle_mode")
    normalized = {}
    for field in ("bonus_type", "gui_type"):
        if field not in value:
            continue
        code = value[field]
        if (isinstance(code, bool) or not isinstance(code, integer_types)
                or not 0 <= code <= 2147483647):
            raise LedgerValidationError("battle_mode.%s must be a bounded integer" % field)
        normalized[field] = code
    return normalized


def _normalize_vehicles(rows):
    if not isinstance(rows, list) or len(rows) > 64:
        raise LedgerValidationError("vehicles must be a bounded list")
    result, seen = [], set()
    for row in rows:
        _keys(row, ("vehicle_type_id", "name", "tier", "icon"), (), "vehicle")
        identity = _identifier(row["vehicle_type_id"], "vehicle_type_id")
        if not identity.isdigit() or not 0 < int(identity) < 2147483648 or identity in seen:
            raise LedgerValidationError("vehicle type IDs must be positive and unique")
        identity = text_type(int(identity))
        if identity in seen:
            raise LedgerValidationError("vehicle type IDs must be unique")
        seen.add(identity)
        name = _text(row["name"], "vehicle.name")
        if len(name) > 160:
            raise LedgerValidationError("vehicle name too long")
        tier = row["tier"]
        if tier is not None and (isinstance(tier, bool) or not isinstance(tier, integer_types) or not 1 <= tier <= 20):
            raise LedgerValidationError("vehicle tier must be 1 through 20 or unknown")
        icon = row["icon"]
        if icon is not None and (not isinstance(icon, string_types) or not re.match(
                r'^coui://(?:halloween/)?gui/maps/(?:icons/vehicle|shop/vehicles)/[A-Za-z0-9_./-]+\.png\Z', icon)
                or any(p in ('', '.', '..') for p in icon[7:].split('/'))):
            raise LedgerValidationError("vehicle art must be a local tank resource")
        result.append({"vehicle_type_id":identity, "name":name, "tier":tier, "icon":icon})
    return result


def _record_key(record):
    return (record["region"], record["account_id"], record["battle_id"])


def _windows_replace(source, destination):
    """Recoverable replacement for the client's Python 2 without _ctypes.

    Windows os.rename cannot replace a destination. Preserve it as .previous;
    a restart between the two renames restores that file before loading.
    """
    previous = destination + ".previous"
    if not os.path.exists(destination):
        os.rename(source, destination)
        return
    if os.path.exists(previous):
        os.unlink(previous)
    os.rename(destination, previous)
    try:
        os.rename(source, destination)
    except Exception:
        if not os.path.exists(destination):
            os.rename(previous, destination)
        raise


def _recover_previous(path):
    if not os.path.exists(path) and os.path.isfile(path + ".previous"):
        os.rename(path + ".previous", path)
    return path


def _atomic_replace(source, destination):
    if hasattr(os, "replace"):
        os.replace(source, destination)
    elif os.name == "nt":
        _windows_replace(source, destination)
    else:
        os.rename(source, destination)


class EconomyLedger(object):
    """An account-scoped, idempotent store of explicitly supplied results.

    A repeated identity replaces its prior record; it never adds another battle.
    Only final records contribute to summaries and goals. Calls are not a
    synchronization mechanism: use one writer per JSON file.
    """

    def __init__(self):
        self._records = {}

    def upsert_result(self, result):
        record = _normalize_record(result)
        key = _record_key(record)
        previous = self._records.get(key)
        if previous is not None and previous.get("battle_mode") is not None:
            if record["battle_mode"] is None:
                record["battle_mode"] = copy.deepcopy(previous["battle_mode"])
            elif (record["battle_mode"]["bonus_type"] == previous["battle_mode"]["bonus_type"]
                    and "gui_type" not in record["battle_mode"]
                    and "gui_type" in previous["battle_mode"]):
                record["battle_mode"]["gui_type"] = previous["battle_mode"]["gui_type"]
        if previous is not None and previous.get("vehicles"):
            # Old callbacks may lack metadata that has already been recovered.
            by_id = dict((v["vehicle_type_id"], v) for v in previous["vehicles"])
            if not record["vehicles"]:
                record["vehicles"] = copy.deepcopy(previous["vehicles"])
            else:
                for vehicle in record["vehicles"]:
                    old = by_id.get(vehicle["vehicle_type_id"], {})
                    for field in ("name", "tier", "icon"):
                        if (vehicle[field] is None or (field == "name" and vehicle[field] == u"Veh\u00edculo " + vehicle["vehicle_type_id"])) and old.get(field) is not None:
                            vehicle[field] = old[field]
        # An asynchronous pending notification can arrive after its final result.
        # Preserve the complete result; final-to-final corrections still replace.
        if previous is not None and previous["status"] == "final" and record["status"] == "pending":
            return "ignored_pending"
        if previous == record:
            return "unchanged"
        self._records[key] = record
        return "inserted" if previous is None else "updated"

    def list_results(self, region=None, account_id=None, include_pending=True):
        if region is not None:
            region = _text(region, "region").upper()
        if account_id is not None:
            account_id = _identifier(account_id, "account_id")
        records = []
        for key in sorted(self._records):
            record = self._records[key]
            if region is not None and record["region"] != region:
                continue
            if account_id is not None and record["account_id"] != account_id:
                continue
            if not include_pending and record["status"] != "final":
                continue
            records.append(copy.deepcopy(record))
        return records

    def summary(self, region, account_id, since_utc=None):
        region = _text(region, "region").upper()
        account_id = _identifier(account_id, "account_id")
        if since_utc is not None:
            since_utc = _utc(since_utc, "since_utc")
        count = 0
        pending = 0
        gross = 0
        expenses = dict((category, 0) for category in EXPENSE_CATEGORIES)
        resources = {}
        reserves = {"personal": 0, "clan": 0, "known_battles": 0, "total_battles": 0}
        for record in self.list_results(region, account_id):
            if since_utc is not None and record["occurred_at"] < since_utc:
                continue
            if record["status"] == "pending":
                pending += 1
                continue
            count += 1
            gross += record["credits"]["gross"]
            known_reserves = record["credits"].get("reserves")
            if known_reserves is not None:
                reserves["known_battles"] += 1
                reserves["personal"] += known_reserves["personal"]
                reserves["clan"] += known_reserves["clan"]
            for category in EXPENSE_CATEGORIES:
                expenses[category] += record["credits"]["expenses"][category]
            for name, amounts in record["resources"].items():
                totals = resources.setdefault(name, {"earned": 0, "spent": 0})
                totals["earned"] += amounts["earned"]
                totals["spent"] += amounts["spent"]
        total_expenses = sum(expenses.values())
        net = gross - total_expenses
        reserves["total_battles"] = count
        for totals in resources.values():
            totals["net"] = totals["earned"] - totals["spent"]
            totals["average_net"] = totals["net"] / count if count else None
        return {
            "region": region,
            "account_id": account_id,
            "since_utc": since_utc,
            "battle_count": count,
            "pending_battles": pending,
            "gross_credits": gross,
            "expenses": expenses,
            "total_expenses": total_expenses,
            "net_credits": net,
            "average_net_credits": net / count if count else None,
            "reserves": reserves,
            "resources": resources,
        }

    def goal_status(self, goal, external_balance=None):
        """Evaluate net earnings since a UTC cutoff or an external real balance.

        resource defaults to credits. For other resources, averages include every
        final battle in the chosen period, including those with no resource gain.
        """
        _keys(goal, ("region", "account_id", "mode", "target"),
              ("resource", "since_utc"), "goal")
        mode = goal["mode"]
        if mode not in ("net_earnings", "balance"):
            raise LedgerValidationError("goal.mode must be net_earnings or balance")
        target = _amount(goal["target"], "goal.target", positive=True)
        resource = _text(goal.get("resource", "credits"), "goal.resource").lower()
        since_utc = goal.get("since_utc")
        if mode == "net_earnings" and since_utc is None:
            raise LedgerValidationError("net_earnings goals require since_utc")
        totals = self.summary(goal["region"], goal["account_id"], since_utc)
        if resource == "credits":
            net = totals["net_credits"]
            average = totals["average_net_credits"]
        else:
            amounts = totals["resources"].get(resource, {})
            net = amounts.get("net", 0)
            average = net / totals["battle_count"] if totals["battle_count"] else None
        if mode == "balance":
            current = _amount(external_balance, "external_balance")
        else:
            current = net
        remaining = max(0, target - current)
        complete = current >= target
        progress = min(1.0, max(0.0, current / target))
        estimate = None
        if complete:
            estimate = 0
        elif average is not None and average > 0:
            estimate = int(math.ceil(remaining / average))
        return {
            "region": totals["region"],
            "account_id": totals["account_id"],
            "mode": mode,
            "resource": resource,
            "target": target,
            "since_utc": since_utc,
            "current": current,
            "remaining": remaining,
            "progress": progress,
            "progress_percent": progress * 100,
            "complete": complete,
            "battle_count": totals["battle_count"],
            "average_per_battle": average,
            "estimated_battles": estimate,
        }

    def to_dict(self):
        return {"schema_version": SCHEMA_VERSION, "records": self.list_results()}

    @classmethod
    def from_dict(cls, data):
        _keys(data, ("schema_version", "records"), (), "ledger")
        if (isinstance(data["schema_version"], bool) or
                not isinstance(data["schema_version"], integer_types) or
                data["schema_version"] != SCHEMA_VERSION):
            raise LedgerValidationError("unsupported schema_version")
        if not isinstance(data["records"], list):
            raise LedgerValidationError("records must be an array")
        ledger = cls()
        for raw in data["records"]:
            record = _normalize_record(raw)
            key = _record_key(record)
            if key in ledger._records:
                raise LedgerValidationError("duplicate identity in persisted records")
            ledger._records[key] = record
        return ledger

    def save(self, path):
        """Write UTF-8 JSON with atomic or recoverable replacement.

        Python 3 uses atomic os.replace. The game's Windows Python 2 uses a
        .previous journal and restores the old file on failure or restart.
        """
        destination = _recover_previous(os.path.abspath(path))
        directory = os.path.dirname(destination)
        content = json.dumps(self.to_dict(), ensure_ascii=False,
                             indent=2, sort_keys=True).encode("utf-8")
        descriptor, temporary = tempfile.mkstemp(
            prefix=".%s." % os.path.basename(destination), suffix=".tmp", dir=directory)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.write(b"\n")
                handle.flush()
                os.fsync(handle.fileno())
            _atomic_replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path):
        with io.open(_recover_previous(path), "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls.from_dict(data)
