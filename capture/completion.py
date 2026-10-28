# -*- coding: utf-8 -*-
"""Durable, account-scoped presentation events for completed credit goals.

This namespace records no income or account balance. A completion is armed by
observing a live goal and consumed only by the view's explicit acknowledgement.
"""
import copy
import datetime
import re
import uuid

from .wallet import exact_amount

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)

NAMESPACE = "account_goal_completions"


def _key(region, account_id):
    return region + ":" + str(account_id)


def _reference(config, region, account_id):
    goals = config.get("account_goals", {})
    goal = goals.get(_key(region, account_id)) if isinstance(goals, dict) else None
    if not isinstance(goal, dict) or goal.get("mode") != "balance_growth":
        return None, None
    base = exact_amount(goal.get("baseline"))
    generation = exact_amount(goal.get("reset_generation", 0))
    target = exact_amount(goal.get("target"))
    since = goal.get("since_utc")
    if (base is None or base < 0 or generation is None or generation < 0 or
            target is None or target < 0 or not isinstance(since, string_types)):
        return None, None
    try:
        if datetime.datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").strftime(
                "%Y-%m-%dT%H:%M:%SZ") != since:
            return None, None
    except (ValueError, TypeError, OverflowError):
        return None, None
    return {"baseline": base, "since_utc": since, "reset_generation": generation}, target


def _tracker(config, key):
    accounts = config.get(NAMESPACE, {})
    return accounts.get(key) if isinstance(accounts, dict) else None


def _pending_valid(pending):
    return (isinstance(pending, dict) and isinstance(pending.get("id"), string_types) and
            re.match(r"[0-9a-f]{32}\Z", pending["id"]) is not None and
            exact_amount(pending.get("target")) is not None and pending["target"] > 0)


def _store(previous, key, value):
    updated = copy.deepcopy(previous)
    accounts = updated.get(NAMESPACE)
    if not isinstance(accounts, dict):
        accounts = {}
        updated[NAMESPACE] = accounts
    if value is None:
        accounts.pop(key, None)
    else:
        accounts[key] = value
    return updated


def sync_goal_completion(previous, region, account_id, balance, token_factory=None):
    """Return a changed config, or None; callers commit it before publishing.

    The first observation of an already-complete goal is a silent migration.
    The high-water target survives deactivation and recrossing the same goal.
    Only an explicit new reference (baseline/start/reset generation) rearms it.
    """
    amount = exact_amount(balance)
    if not account_id or amount is None or amount < 0:
        return None
    key = _key(region, account_id)
    reference, target = _reference(previous, region, account_id)
    saved = _tracker(previous, key)
    if reference is None:
        return _store(previous, key, None) if saved is not None else None
    complete = target > 0 and amount - reference["baseline"] >= target
    maximum = exact_amount(saved.get("highest_completed_target")) if isinstance(saved, dict) else None
    if (not isinstance(saved, dict) or saved.get("schema") != 1 or
            saved.get("reference") != reference or maximum is None or maximum < 0):
        # An existing success must not produce fireworks on installation/login.
        state = {"schema": 1, "reference": reference,
                 "highest_completed_target": target if complete else 0,
                 "pending": None}
        return _store(previous, key, state)
    state = copy.deepcopy(saved)
    pending = state.get("pending")
    if (not _pending_valid(pending) or pending["target"] != target or not complete):
        state["pending"] = None
    if complete and target > maximum:
        token = token_factory() if token_factory is not None else uuid.uuid4().hex
        if not isinstance(token, string_types) or not re.match(r"[0-9a-f]{32}\Z", token):
            raise ValueError("invalid goal completion token")
        state["highest_completed_target"] = target
        state["pending"] = {"id": token, "target": target}
    return _store(previous, key, state) if state != saved else None


def goal_completion_payload(config, region, account_id, balance):
    """Only expose a pending event for the exact synchronized active goal."""
    amount = exact_amount(balance)
    if not account_id or amount is None or amount < 0:
        return None
    key = _key(region, account_id)
    reference, target = _reference(config, region, account_id)
    saved = _tracker(config, key)
    if (reference is None or target <= 0 or amount - reference["baseline"] < target or
            not isinstance(saved, dict) or saved.get("schema") != 1 or
            saved.get("reference") != reference):
        return None
    pending = saved.get("pending")
    if not _pending_valid(pending) or pending["target"] != target:
        return None
    return {"id": pending["id"], "account_context": key, "target": target,
            "reset_generation": reference["reset_generation"]}


def acknowledge_goal_completion(previous, region, account_id, balance, args):
    """Stale/foreign acknowledgements cannot consume another goal's event."""
    if not isinstance(args, dict):
        return None
    pending = goal_completion_payload(previous, region, account_id, balance)
    if (pending is None or args.get("id") != pending["id"] or
            args.get("account_context") != pending["account_context"]):
        return None
    key = pending["account_context"]
    saved = copy.deepcopy(_tracker(previous, key))
    saved["pending"] = None
    return _store(previous, key, saved)
