# -*- coding: utf-8 -*-
"""Read-only daily projections of captured results, using native server days.

The current visible history can be reset freely: audited results and receipts
remain the source for these projections. A missing native clock never becomes
a guessed local-midnight schedule.
"""
import copy
import datetime

from .local_clock import time_label

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


_STAMP = "%Y-%m-%dT%H:%M:%SZ"
_DAY = datetime.timedelta(days=1)


def _utc(value):
    if not isinstance(value, string_types):
        return None
    try:
        parsed = datetime.datetime.strptime(value, _STAMP)
        if parsed.strftime(_STAMP) == value and 2000 <= parsed.year < 2100:
            return parsed
    except (TypeError, ValueError, OverflowError):
        pass
    return None


def _current_cycle(config, region, account_id, now_utc, server_clock):
    """Prefer a validated native cycle, else retain the last known cutoff.

    A saved cycle supplies its UTC reset offset, but is not advanced by the PC
    clock. Until the native clock returns, newer days remain current/unknown.
    """
    now = _utc(now_utc)
    if not region or not account_id:
        return None
    if now is None:
        return None
    if isinstance(server_clock, dict):
        start = _utc(server_clock.get("cycle_start_utc"))
        end = _utc(server_clock.get("next_reset_utc"))
        observed = _utc(server_clock.get("server_now_utc", now_utc))
        if (start is not None and end is not None and observed is not None and
                end - start == _DAY and start <= observed < end):
            return start
    accounts = config.get("account_history", {}) if isinstance(config, dict) else {}
    saved = accounts.get(region + ":" + str(account_id), {}) if isinstance(accounts, dict) else {}
    start = _utc(saved.get("server_cycle")) if isinstance(saved, dict) else None
    return start if start is not None and start <= now else None


def _cycle_for(occurred_at, current):
    occurred = _utc(occurred_at)
    if occurred is None:
        return None
    # Integer day arithmetic preserves the native UTC offset across every date,
    # including records immediately before a server-day boundary.
    return current + _DAY * ((occurred - current).days)


def server_day_bounds(config, region, account_id, now_utc, server_clock, day_key):
    """Validate an exact completed native day for bounded metadata recovery."""
    current = _current_cycle(config, region, account_id, now_utc, server_clock)
    day = _utc(day_key)
    if current is None or day is None or day >= current or _cycle_for(day_key, current) != day:
        return None
    return {"start_utc": day_key, "end_utc": (day + _DAY).strftime(_STAMP)}


def partition_server_days(ledger, region, account_id, config, now_utc,
                          server_clock=None, receipts=None):
    """Return internal period ledgers for all captured, completed server days.

    No configuration, original ledger, wallet, or receipts are changed. Pending
    records have no final financial report and are excluded from past-day sums.
    The caller serializes summaries and at most one selected history list.
    """
    current = _current_cycle(config, region, account_id, now_utc, server_clock)
    if current is None or not account_id:
        return {"ready": False, "days": []}
    grouped = {}

    def period(occurred_at):
        day = _cycle_for(occurred_at, current)
        if day is None or day >= current:
            return None
        key = day.strftime(_STAMP)
        if key not in grouped:
            label = time_label(key).split(" ", 1)[0] or day.strftime("%d/%m/%Y")
            grouped[key] = {"key": key, "label": label,
                            "ledger": type(ledger)(), "receipts": []}
        return grouped[key]

    for record in ledger.list_results(region, account_id, include_pending=False):
        bucket = period(record["occurred_at"])
        if bucket is not None:
            bucket["ledger"].upsert_result(record)
    for receipt in receipts or []:
        bucket = period(receipt.get("occurred_at"))
        if bucket is not None:
            bucket["receipts"].append(receipt)
    return {"ready": True, "days": [grouped[key] for key in sorted(grouped, reverse=True)]}


def external_reward_rows(receipts, all_receipts):
    """Return independent receipt copies after the live-wallet deduplication."""
    included = set((row.get("battle_id"), part["quest_id"])
                   for row in all_receipts if row.get("included_in_battle") and row.get("battle_id")
                   for part in row.get("parts", []))
    result = []
    for row in receipts:
        if row.get("included_in_battle"):
            continue
        item = copy.deepcopy(row)
        if row.get("parts"):
            item["parts"] = [part for part in item["parts"]
                             if not row.get("battle_id") or
                             (row["battle_id"], part["quest_id"]) not in included]
            if not item["parts"]:
                continue
            item["credits"] = sum(part["credits"] for part in item["parts"])
        result.append(item)
    return result


def external_reward_total(receipts, all_receipts):
    """Included battle awards remain annotations, never extra income."""
    return sum(row["credits"] for row in external_reward_rows(receipts, all_receipts))
