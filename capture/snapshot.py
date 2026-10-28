# -*- coding: utf-8 -*-
"""Extract only the local player's economy from a full battle result.

This module is independent of BigWorld so its input contract can be checked
outside the game. Financial values are observations, not reconciled totals.
"""
from __future__ import division

import datetime
import math
import base64
from .compatibility import SUPPORTED_CLIENTS

try:
    string_types = (basestring,)
    integer_types = (int, long)
    text_type = unicode
    binary_types = (str, bytearray, buffer)
except NameError:
    string_types = (str,)
    integer_types = (int,)
    text_type = str
    binary_types = (bytes, bytearray, memoryview)

SCHEMA_VERSION = 1
CLIENT_VERSION = "2.4.1.1"
_FINANCIAL_PARTS = ("credit", "gold", "crystal", "cost", "expense", "piggy",
                    "freexp", "freeexperience", "multiplier", "factor")
_CONTEXT_FIELDS = ("typeCompDescr", "isPremium", "premiumAccountType",
                   "duration", "arenaCreateTime", "arenaBonusType", "bonusType", "guiType")


class SnapshotError(ValueError):
    pass


def _identifier(value, name):
    if isinstance(value, bool):
        raise SnapshotError("%s is not an identifier" % name)
    if isinstance(value, integer_types):
        if value <= 0:
            raise SnapshotError("%s must be positive" % name)
        return text_type(value)
    if isinstance(value, string_types) and value.isdigit() and int(value) > 0:
        return text_type(int(value))
    raise SnapshotError("%s is missing or invalid" % name)


def json_value(value, depth=0):
    """Bound serialization without repr(), arbitrary methods or pickle."""
    if value is None or isinstance(value, (bool,) + integer_types):
        return value
    if isinstance(value, float):
        return value if not (math.isnan(value) or math.isinf(value)) else None
    if isinstance(value, binary_types):
        raw = bytes(value)
        return {"encoding": "base64", "bytes": len(raw),
                "data": base64.b64encode(raw[:262144]).decode("ascii"),
                "truncated": len(raw) > 262144}
    if isinstance(value, string_types):
        return value[:4096]
    if depth >= 8:
        return {"capture_truncated": "depth"}
    if isinstance(value, (list, tuple)):
        result = [json_value(item, depth + 1) for item in value[:256]]
        if len(value) > 256:
            result.append({"capture_truncated": "items"})
        return result
    if isinstance(value, dict):
        result = {}
        for key in sorted(value, key=lambda item: text_type(type(item)) + text_type(item) if isinstance(item, (string_types + integer_types)) else text_type(type(item))):
            if len(result) >= 256:
                result["capture_truncated"] = "items"
                break
            if isinstance(key, (string_types + integer_types)):
                result[text_type(key)] = json_value(value[key], depth + 1)
        return result
    return {"capture_unsupported_type": type(value).__name__}


def financial_fields(row):
    if not isinstance(row, dict):
        raise SnapshotError("personal row must be a dictionary")
    fields = {}
    keys = []
    for key, value in row.items():
        if not isinstance(key, string_types):
            continue
        keys.append(text_type(key))
        lower = key.lower()
        if any(part in lower for part in _FINANCIAL_PARTS) or key in _CONTEXT_FIELDS:
            fields[text_type(key)] = json_value(value)
    return {"fields": fields, "available_keys": sorted(keys)}


def make_snapshot(results, region, source="event", captured_at=None, client=CLIENT_VERSION):
    if client not in SUPPORTED_CLIENTS:
        raise SnapshotError("unsupported client version")
    if not isinstance(results, dict):
        raise SnapshotError("battle result must be a dictionary")
    battle_id = _identifier(results.get("arenaUniqueID"), "battle_id")
    personal = results.get("personal")
    if not isinstance(personal, dict):
        raise SnapshotError("personal results are missing")
    avatar = personal.get("avatar")
    if not isinstance(avatar, dict):
        raise SnapshotError("personal avatar is missing")
    account_id = _identifier(avatar.get("accountDBID"), "account_id")
    if not isinstance(region, string_types) or not region.strip():
        raise SnapshotError("region is missing")
    vehicles = []
    for key, row in personal.items():
        if key == "avatar":
            continue
        vehicle_id = _identifier(key, "personal vehicle type")
        captured = financial_fields(row)
        captured["vehicle_type_id"] = vehicle_id
        vehicles.append(captured)
    if not vehicles:
        raise SnapshotError("personal vehicle results are missing")
    vehicles.sort(key=lambda row: int(row["vehicle_type_id"]))
    common = results.get("common", {})
    common = common if isinstance(common, dict) else {}
    stamp = captured_at or datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "capture_schema": SCHEMA_VERSION,
        "client_version": client,
        "captured_at": stamp,
        "region": region.strip().upper(),
        "account_id": account_id,
        "battle_id": battle_id,
        "source": source,
        "common": dict((key, json_value(common[key])) for key in _CONTEXT_FIELDS
                       if key in common),
        "personal": {"avatar": financial_fields(avatar), "vehicles": vehicles},
        "reconciliation": {"status": "unverified"},
    }
