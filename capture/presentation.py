# -*- coding: utf-8 -*-
"""Account-scoped data and incremental balance goals for the garage view."""
from __future__ import division
import copy
import datetime
import re
from .wallet import exact_amount
from .history import get_history_state, record_visible, receipt_visible
from .local_clock import time_label, timezone_label
from .battle_modes import battle_mode_payload, battle_mode_icon
from .archive import partition_server_days, external_reward_total, external_reward_rows
from .localization import localize_payload

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


def account_key(region, account_id):
    return region + ":" + str(account_id)


DEFAULT_CREDIT_TARGET = 100000


def ensure_balance_goal(previous, region, account_id, balance, now):
    """Start a new account once; saved and deliberately disabled goals survive."""
    key = account_key(region, account_id)
    saved = previous.get("account_goals", {}).get(key, {})
    if saved.get("schema") == 2 or exact_amount(balance) is None or balance < 0:
        return None
    first_use = key not in previous.get("account_goals", {})
    target = DEFAULT_CREDIT_TARGET if first_use else 0
    if first_use and (not _valid_goal_time(now) or balance + target > 9007199254740991):
        return None
    updated = copy.deepcopy(previous)
    updated.setdefault("account_goals", {})[key] = {
        "schema": 2, "mode": "balance_growth", "target": target,
        "baseline": balance if first_use else None, "since_utc": now if first_use else None}
    updated["credit_target"] = target
    return updated


def _valid_goal_time(value):
    if not isinstance(value, string_types):
        return False
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%Y-%m-%dT%H:%M:%SZ") == value
    except (TypeError, ValueError, OverflowError):
        return False


def _goal_command_context(value, mode, previous, balance, region, account_id):
    if not isinstance(value, string_types) or not re.match(r"[0-9]{1,16}\Z", value):
        raise ValueError(u"Introduce una cantidad entera igual o mayor que cero.")
    amount = int(value)
    if amount < 0 or amount > 9007199254740991:
        raise ValueError(u"La meta debe estar entre 0 y 9.007.199.254.740.991 cr\u00e9ditos.")
    if mode != "balance_growth":
        raise ValueError(u"Actualiza el panel para iniciar una meta desde tu saldo.")
    if not region or not account_id:
        raise ValueError(u"Espera que se sincronice tu cuenta antes de guardar la meta.")
    if amount > 0 and (exact_amount(balance) is None or balance < 0):
        raise ValueError(u"Espera que se sincronice tu saldo antes de iniciar la meta.")
    if not isinstance(previous, dict) or not isinstance(previous.get("account_goals", {}), dict):
        raise ValueError(u"La configuraci\u00f3n de la meta guardada no es v\u00e1lida.")
    key = account_key(region, account_id)
    saved = previous.get("account_goals", {}).get(key, {})
    if not isinstance(saved, dict):
        raise ValueError(u"La configuraci\u00f3n de la meta guardada no es v\u00e1lida.")
    saved_target = exact_amount(saved.get("target", 0))
    if saved_target is None or saved_target < 0:
        raise ValueError(u"La cantidad de la meta guardada no es v\u00e1lida.")
    generation = exact_amount(saved.get("reset_generation", 0))
    if generation is None or generation < 0:
        raise ValueError(u"El contador de reinicios de la meta no es v\u00e1lido.")
    return amount, key, saved, saved_target, generation


def parse_goal_command(value, mode, previous, now_utc, balance=None, region=None, account_id=None):
    """Change the amount or deactivate; a saved start survives either action."""
    amount, key, saved, saved_target, generation = _goal_command_context(
        value, mode, previous, balance, region, account_id)
    base, since = saved.get("baseline"), saved.get("since_utc")
    if ((base is not None and (exact_amount(base) is None or base < 0)) or
            (since is not None and not _valid_goal_time(since)) or
            (base is None) != (since is None) or
            ((base is not None or saved_target > 0) and saved.get("mode") != "balance_growth") or
            (saved_target > 0 and base is None)):
        raise ValueError(u"La base o la fecha de la meta guardada no es v\u00e1lida.")
    first_start = amount > 0 and base is None
    if first_start:
        base, since = balance, now_utc
        if not _valid_goal_time(since):
            raise ValueError(u"La fecha de inicio de la meta no es v\u00e1lida.")
    if base is not None and base + amount > 9007199254740991:
        raise ValueError(u"La suma del saldo y la meta supera el l\u00edmite permitido.")
    updated = copy.deepcopy(previous)
    goal = updated.setdefault("account_goals", {}).setdefault(key, {})
    goal["target"] = amount
    if first_start:
        goal.update(schema=2, mode="balance_growth", baseline=base,
                    since_utc=since, reset_generation=generation)
    elif amount == 0:
        goal.setdefault("schema", 2)
        goal.setdefault("mode", "balance_growth")
        goal.setdefault("baseline", base)
        goal.setdefault("since_utc", since)
    updated["credit_target"] = amount
    return updated


def parse_reset_goal_command(value, mode, previous, now_utc, balance=None,
                             region=None, account_id=None):
    """Only this explicit action discards progress and begins at today's balance."""
    amount, key, saved, saved_target, generation = _goal_command_context(
        value, mode, previous, balance, region, account_id)
    if amount == 0:
        raise ValueError(u"Introduce una cantidad mayor que cero para reiniciar la meta.")
    if not _valid_goal_time(now_utc):
        raise ValueError(u"La fecha de inicio de la meta no es v\u00e1lida.")
    if balance + amount > 9007199254740991:
        raise ValueError(u"La suma del saldo y la meta supera el l\u00edmite permitido.")
    if generation >= 9007199254740991:
        raise ValueError(u"El contador de reinicios de la meta supera el l\u00edmite admitido.")
    updated = copy.deepcopy(previous)
    goal = updated.setdefault("account_goals", {}).setdefault(key, {})
    goal.update(schema=2, mode="balance_growth", target=amount, baseline=balance,
                since_utc=now_utc, reset_generation=generation + 1)
    updated["credit_target"] = amount
    return updated


def balance_goal(config, region, account_id, balance):
    saved = config.get("account_goals", {}).get(account_key(region, account_id), {})
    target = saved.get("target", 0)
    base = saved.get("baseline")
    goal = {"mode": "balance_growth", "target": target, "baseline": base,
            "since_utc": saved.get("since_utc"), "current": None, "remaining": None,
            "progress_percent": None, "complete": False, "estimated_battles": None,
            "active": bool(base is not None and target > 0),
            "reset_generation": saved.get("reset_generation", 0),
            "final_balance": base + target if base is not None and target > 0 else None}
    if target == 0:
        current = balance - base if base is not None and balance is not None else (
            None if base is not None else 0)
        goal.update(current=current, remaining=0, progress_percent=0)
    if base is not None and balance is not None and exact_amount(target) is not None and target > 0:
        change = balance - base
        goal.update(current=change, remaining=max(0, target - change), complete=change >= target,
                    progress_percent=100.0 * max(0.0, min(1.0, change / target)))
    return goal


def _time_label(utc):
    return time_label(utc, compact=True) or utc


def history_ledger(ledger, region, account_id, config):
    """A read-only projection keeps retired results from reappearing on retry."""
    state = get_history_state(config, region, account_id)
    if state["since_utc"] is None and not state["excluded_battles"]:
        return ledger
    current = type(ledger)()
    state["excluded_battles"] = frozenset(state["excluded_battles"])
    for record in ledger.list_results(region, account_id):
        if record_visible(record, state):
            current.upsert_result(record)
    return current


def _history_row(record, by_battle):
    """Use the same metadata and receipt annotations in every history view."""
    credit = record["credits"]
    seen, rewards = set(), []
    for part in by_battle.get(record["battle_id"], []):
        if part["quest_id"] not in seen:
            seen.add(part["quest_id"])
            rewards.append(copy.deepcopy(part))
    return {"battle_id": record["battle_id"],
            "vehicles": copy.deepcopy(record.get("vehicles", [])),
            "battle_mode": battle_mode_payload(record.get("battle_mode")),
            "occurred_at": record["occurred_at"], "time_label": _time_label(record["occurred_at"]),
            "gross_credits": credit["gross"], "expenses": copy.deepcopy(credit["expenses"]),
            "reserves": copy.deepcopy(credit.get("reserves")),
            "net_credits": credit["gross"] - sum(credit["expenses"].values()), "rewards": rewards}


def _mode_identity(mode):
    safe = battle_mode_payload(mode)
    if safe is None:
        return "unknown", u"Modo no identificado"
    return "mode:%s" % safe["bonus_type"], safe["label"]


def _vehicle_identity(record):
    """A native aggregate belongs to one tank, or one unattributed bucket."""
    vehicles = record.get("vehicles", [])
    if not vehicles:
        return "unknown", u"Veh\u00edculo no identificado", None
    if len(vehicles) != 1:
        return "multiple", u"Varios veh\u00edculos", None
    vehicle = vehicles[0]
    return "vehicle:" + vehicle["vehicle_type_id"], vehicle["name"], vehicle


def _vehicle_groups(visible_ledger, region, account_id):
    """Small, whole-period summaries; histories are requested one at a time.

    Results with several own vehicles report one native credit aggregate. Keep
    that aggregate in a separate bucket instead of inventing per-tank income.
    Names and tiers are presentation only; the native type ID identifies a tank.
    """
    grouped = {}
    records = sorted(visible_ledger.list_results(region, account_id),
                     key=lambda row: (row["occurred_at"], row["battle_id"]), reverse=True)
    for record in records:
        key, label, vehicle = _vehicle_identity(record)
        if key not in grouped:
            grouped[key] = {"label": label, "vehicle": copy.deepcopy(vehicle),
                            "ledger": type(visible_ledger)()}
        group = grouped[key]
        if vehicle is not None:
            # Prefer the latest resolved name while retaining older native art
            # or tier if a later result could not resolve that optional detail.
            saved = group["vehicle"]
            for field in ("name", "tier", "icon"):
                if (saved[field] is None or (field == "name" and
                        saved[field] == u"Veh\u00edculo " + saved["vehicle_type_id"])):
                    saved[field] = vehicle[field]
            group["label"] = saved["name"]
        group["ledger"].upsert_result(record)
    result = []
    for key, group in grouped.items():
        summary = group["ledger"].summary(region, account_id)
        result.append({"key": key, "label": group["label"], "vehicle": group["vehicle"],
                       "rankable": group["vehicle"] is not None and summary["battle_count"] > 0,
                       "summary": summary, "history_total": summary["battle_count"]})
    def order(group):
        if group["vehicle"] is None:
            return (2, 0, 0, group["key"], 0)
        return (0 if group["rankable"] else 1, -group["summary"]["net_credits"],
                -group["history_total"], group["label"].lower(),
                int(group["vehicle"]["vehicle_type_id"]))
    return sorted(result, key=order)


def _vehicle_selection(visible_ledger, region, account_id, by_battle,
                       requested, vehicle_groups, mode_groups):
    """Return at most 100 rows for one exact mode/tank selection."""
    if not isinstance(requested, dict) or requested.get("vehicle_key") in (None, "all"):
        return None
    mode_key = requested.get("mode_key", "all")
    vehicle_key = requested.get("vehicle_key")
    groups = vehicle_groups if mode_key == "all" else []
    if mode_key != "all":
        for mode in mode_groups:
            if mode["key"] == mode_key:
                groups = mode["vehicle_groups"]
                break
    selected = next((group for group in groups if group["key"] == vehicle_key), None)
    summary = (copy.deepcopy(selected["summary"]) if selected is not None
               else type(visible_ledger)().summary(region, account_id))
    selection = {"mode_key": mode_key, "vehicle_key": vehicle_key,
                 "request_id": requested.get("request_id"), "available": selected is not None,
                 "summary": summary, "history": [], "history_total": summary["battle_count"]}
    if selected is None:
        return selection
    records = sorted(visible_ledger.list_results(region, account_id, include_pending=False),
                     key=lambda row: (row["occurred_at"], row["battle_id"]), reverse=True)
    for record in records:
        if (_vehicle_identity(record)[0] == vehicle_key and
                (mode_key == "all" or _mode_identity(record.get("battle_mode"))[0] == mode_key)):
            selection["history"].append(_history_row(record, by_battle))
            if len(selection["history"]) == 100:
                break
    return selection


def _mode_groups(visible_ledger, region, account_id, by_battle, include_history=True,
                 include_vehicle_groups=True):
    """Summarize whole-period native modes before limiting each visible list.

    Each record belongs to exactly one raw bonus-type group. GUI types, labels,
    and the currently selected garage mode never identify a group. Pending
    records contribute only to their own group's pending count (unknown when
    metadata is missing); callback-only
    pending results cannot be assigned to a mode until metadata arrives.
    """
    grouped, order = {}, []
    for code in (1, 20, 43):
        key, label = _mode_identity({"bonus_type": code})
        grouped[key] = {"label": label, "ledger": type(visible_ledger)(), "history": []}
        order.append(key)
    records = sorted(visible_ledger.list_results(region, account_id),
                     key=lambda row: (row["occurred_at"], row["battle_id"]), reverse=True)
    extra = {}
    for record in records:
        key, label = _mode_identity(record.get("battle_mode"))
        if key not in grouped:
            grouped[key] = {"label": label, "ledger": type(visible_ledger)(), "history": []}
            extra[key] = record["battle_mode"]["bonus_type"] if key != "unknown" else 2147483648
        group = grouped[key]
        group["ledger"].upsert_result(record)
        if include_history and record["status"] == "final" and len(group["history"]) < 100:
            group["history"].append(_history_row(record, by_battle))
    order.extend(sorted(extra, key=lambda key: extra[key]))
    result = []
    for key in order:
        group = grouped[key]
        summary = group["ledger"].summary(region, account_id)
        item = {"key": key, "label": group["label"], "summary": summary,
                "icon": battle_mode_icon(int(key[5:])) if key != "unknown" else None,
                "history_total": summary["battle_count"]}
        if include_history:
            item["history"] = group["history"]
        if include_vehicle_groups:
            item["vehicle_groups"] = _vehicle_groups(group["ledger"], region, account_id)
        result.append(item)
    return result


def _history_archive(ledger, region, account_id, config, now_utc, server_clock,
                     all_receipts, requested):
    """Expose all prior-day summaries and one bounded exact selection.

    Archive browsing does not change the live period, selected live vehicle,
    balance, or goal. Its summaries use every captured final result for the
    chosen native server day, irrespective of manual visible-history resets.
    """
    periods = partition_server_days(ledger, region, account_id, config, now_utc,
                                   server_clock, all_receipts)
    archive = {"ready": periods["ready"], "days": [], "selection": None,
               "scope_note": u"Solo se muestran partidas y recompensas registradas por el mod; los importes de batallas ya descuentan sus gastos."}
    selected = None
    for period in periods["days"]:
        summary = period["ledger"].summary(region, account_id)
        archive["days"].append({"key": period["key"], "label": period["label"],
            "summary": summary, "battle_count": summary["battle_count"],
            "net_credits": summary["net_credits"], "history_total": summary["battle_count"],
            "external_credits": external_reward_total(period["receipts"], all_receipts)})
        if isinstance(requested, dict) and requested.get("day_key") == period["key"]:
            selected = period
    if not isinstance(requested, dict):
        return archive
    empty = type(ledger)().summary(region, account_id)
    mode_key, vehicle_key = requested.get("mode_key", "all"), requested.get("vehicle_key", "all")
    selection = {"day_key": requested.get("day_key"), "label": selected["label"] if selected else "",
                 "mode_key": mode_key, "vehicle_key": vehicle_key,
                 "request_id": requested.get("request_id"), "available": False,
                 "account_context": account_key(region, account_id),
                 "summary": empty, "history": [], "history_total": 0,
                 "mode_groups": [], "vehicle_groups": [], "external_credits": 0,
                 "external_rewards": []}
    archive["selection"] = selection
    if selected is None:
        return archive
    by_battle = {}
    # Receipt timestamps may follow battle timestamps across a reset boundary.
    # Keep explicit battle annotations wherever that battle belongs.
    for receipt in all_receipts:
        if receipt.get("included_in_battle") and receipt.get("battle_id"):
            by_battle.setdefault(receipt["battle_id"], []).extend(receipt.get("parts", []))
    selection["mode_groups"] = _mode_groups(selected["ledger"], region, account_id,
                                            by_battle, False, False)
    if mode_key != "all" and not any(group["key"] == mode_key for group in selection["mode_groups"]):
        return archive
    mode_ledger = type(ledger)()
    for record in selected["ledger"].list_results(region, account_id, include_pending=False):
        if mode_key == "all" or _mode_identity(record.get("battle_mode"))[0] == mode_key:
            mode_ledger.upsert_result(record)
    selection["vehicle_groups"] = _vehicle_groups(mode_ledger, region, account_id)
    if vehicle_key != "all" and not any(group["key"] == vehicle_key for group in selection["vehicle_groups"]):
        return archive
    scoped = type(ledger)()
    for record in mode_ledger.list_results(region, account_id, include_pending=False):
        if vehicle_key == "all" or _vehicle_identity(record)[0] == vehicle_key:
            scoped.upsert_result(record)
    summary = scoped.summary(region, account_id)
    selection.update(available=True, summary=summary, history_total=summary["battle_count"])
    records = sorted(scoped.list_results(region, account_id, include_pending=False),
                     key=lambda row: (row["occurred_at"], row["battle_id"]), reverse=True)
    selection["history"] = [_history_row(record, by_battle) for record in records[:100]]
    # Extra receipts cannot safely be attributed to one mode or tank. Keep their
    # day-wide total separate so it never masquerades as tank battle earnings.
    selection["external_credits"] = external_reward_total(selected["receipts"], all_receipts)
    for item in sorted(external_reward_rows(selected["receipts"], all_receipts),
                       key=lambda row: (row["occurred_at"], row["id"]), reverse=True)[:100]:
        item["time_label"] = _time_label(item["occurred_at"])
        selection["external_rewards"].append(item)
    return archive


def build_payload(ledger, region, account_id, config, balance, pending_count=0,
                  error=None, now_utc=None, wallet=None, vehicle_filter=None, server_clock=None,
                  archive_filter=None):
    now_utc = now_utc or datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state = get_history_state(config, region, account_id, now_utc, server_clock)
    control = dict((key, state[key]) for key in
                   ("mode", "hour", "preserve_goal", "since_utc", "generation", "next_reset_utc"))
    control["can_reset"] = bool(account_id and exact_amount(balance) is not None and balance >= 0)
    # Format on the Python side so the native panel always agrees with the
    # operating-system clock used to schedule resets, even in embedded browsers.
    control["since_label"] = time_label(state["since_utc"])
    control["next_reset_label"] = time_label(state["next_reset_utc"])
    control["timezone_label"] = timezone_label(now_utc)
    control["server_clock_ready"] = bool(state["mode"] == "server" and state["next_reset_utc"])
    if state["mode"] == "server":
        control["timezone_label"] = (u"Jornada diaria del servidor; horario mostrado en la zona local del equipo.")
    state["excluded_receipts"] = frozenset(state["excluded_receipts"])
    empty = {"battle_count": 0, "gross_credits": 0,
             "expenses": {"repair": 0, "ammo": 0, "consumables": 0, "other": 0},
             "net_credits": 0, "average_net_credits": None, "pending_battles": 0,
             "reserves": {"personal": 0, "clan": 0, "known_battles": 0, "total_battles": 0}}
    payload = {"schema": 1, "ready": bool(account_id), "message": "", "balance": balance,
               "account_context": account_key(region, account_id) if account_id else None,
               "summary": empty, "goal": balance_goal(config, region, account_id, balance),
               "history": [], "mode_groups": [], "vehicle_groups": [], "vehicle_selection": None,
               "history_archive": {"ready": False, "days": [], "selection": None},
               "rewards": [], "wallet": {"ready": False}, "error": error,
               "history_control": control}
    payload["goal"]["since_label"] = time_label(payload["goal"].get("since_utc"))
    if not account_id:
        payload["message"] = u"Esperando que se sincronice tu cuenta del juego."
        return localize_payload(payload, config)
    visible_ledger = history_ledger(ledger, region, account_id, config)
    summary = visible_ledger.summary(region, account_id)
    summary["pending_battles"] += max(0, int(pending_count))
    payload["summary"] = summary
    all_receipts = wallet.receipts(region, account_id) if wallet is not None else []
    payload["history_archive"] = _history_archive(ledger, region, account_id, config,
        now_utc, server_clock, all_receipts, archive_filter)
    receipts = [receipt for receipt in all_receipts if receipt_visible(receipt, state)]
    by_battle = {}
    for receipt in receipts:
        if receipt.get("included_in_battle") and receipt.get("battle_id"):
            by_battle.setdefault(receipt["battle_id"], []).extend(receipt.get("parts", []))
    for record in sorted(visible_ledger.list_results(region, account_id, include_pending=False),
                         key=lambda row: (row["occurred_at"], row["battle_id"]), reverse=True)[:100]:
        payload["history"].append(_history_row(record, by_battle))
    payload["mode_groups"] = _mode_groups(visible_ledger, region, account_id, by_battle)
    payload["vehicle_groups"] = _vehicle_groups(visible_ledger, region, account_id)
    payload["vehicle_selection"] = _vehicle_selection(
        visible_ledger, region, account_id, by_battle, vehicle_filter,
        payload["vehicle_groups"], payload["mode_groups"])
    if wallet is not None:
        payload["wallet"] = wallet.reconciliation(region, account_id, visible_ledger, balance, period=state)
        payload["wallet"]["started_at_label"] = time_label(payload["wallet"].get("started_at"))
        for receipt in sorted(receipts, key=lambda r: (r["occurred_at"], r["id"]), reverse=True)[:100]:
            item = copy.deepcopy(receipt)
            item["time_label"] = _time_label(item["occurred_at"])
            payload["rewards"].append(item)
    if balance is None:
        payload["message"] = u"Saldo pendiente de sincronizar; el historial ya est\u00e1 disponible."
    elif not summary["battle_count"]:
        payload["message"] = u"Tu pr\u00f3xima batalla finalizada aparecer\u00e1 aqu\u00ed."
    return localize_payload(payload, config)
