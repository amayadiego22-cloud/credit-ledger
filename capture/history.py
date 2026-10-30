# -*- coding: utf-8 -*-
"""Account-scoped history periods with explicit local or native server clocks."""
import copy
import datetime

from .wallet import exact_amount, integer_types, string_types, text_type
from .goal_defaults import DEFAULT_CREDIT_TARGET
from .local_clock import daily_boundary_utc, next_daily_reset_utc


_STAMP = "%Y-%m-%dT%H:%M:%SZ"
LOCAL_CLOCK = "local_v1"
SERVER_CLOCK = "server_v1"


def _utc(value):
    if not isinstance(value, string_types):
        return None
    try:
        parsed = datetime.datetime.strptime(value, _STAMP)
        return parsed if parsed.strftime(_STAMP) == value else None
    except (TypeError, ValueError, OverflowError):
        return None


def _require_now(value):
    parsed = _utc(value)
    if parsed is None:
        raise ValueError(u"La fecha del reinicio no es una fecha UTC v\u00e1lida.")
    return parsed


def _valid_hour(value):
    return not isinstance(value, bool) and isinstance(value, integer_types) and 0 <= value <= 23


def _identity(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, integer_types):
        return text_type(value) if value >= 0 else None
    if isinstance(value, string_types) and value and len(value) <= 512:
        return value
    return None


def _key(region, account_id):
    identity = _identity(account_id)
    if not isinstance(region, string_types) or not region or identity is None:
        return None
    return region + ":" + identity


def _identities(values):
    if not isinstance(values, (list, tuple)):
        return []
    seen, result = set(), []
    for value in values:
        identity = _identity(value)
        if identity is not None and identity not in seen:
            seen.add(identity)
            result.append(identity)
    return result


def daily_boundary(now_utc, hour):
    """Latest configured local-PC boundary, including an exact match."""
    return daily_boundary_utc(now_utc, hour)


def next_daily_reset(now_utc, hour):
    """Next local-PC boundary, using the next calendar date across DST."""
    return next_daily_reset_utc(now_utc, hour)


def _server_cycle(server_clock, now_utc):
    """Validate a native day interval; never infer one from a local hour."""
    if not isinstance(server_clock, dict):
        return None
    start, end = (server_clock.get("cycle_start_utc"),
                  server_clock.get("next_reset_utc"))
    first, following, now = _utc(start), _utc(end), _utc(now_utc)
    if first is None or following is None or now is None:
        return None
    if not first <= now < following:
        return None
    return {"cycle_start_utc": start, "next_reset_utc": end}


def get_history_state(config, region, account_id, now_utc=None, server_clock=None):
    """Return a fresh, sanitized state; an invalid mode never enables resets."""
    state = {"mode": "manual", "hour": 6, "preserve_goal": False,
             "since_utc": None, "baseline": None, "excluded_battles": [],
             "excluded_receipts": [], "generation": 0, "daily_cycle": None}
    accounts = config.get("account_history", {}) if isinstance(config, dict) else {}
    saved = accounts.get(_key(region, account_id), {}) if isinstance(accounts, dict) else {}
    if not isinstance(saved, dict):
        saved = {}
    if saved.get("mode") in ("manual", "daily", "server"):
        state["mode"] = saved["mode"]
    if _valid_hour(saved.get("hour")):
        state["hour"] = saved["hour"]
    elif state["mode"] == "daily":
        # Corrupt scheduling data must not schedule a reset at a guessed hour.
        state["mode"] = "manual"
    if isinstance(saved.get("preserve_goal"), bool):
        state["preserve_goal"] = saved["preserve_goal"]
    if (not isinstance(saved.get("settings_schema"), bool) and
            isinstance(saved.get("settings_schema"), integer_types) and saved.get("settings_schema") == 1):
        state["settings_schema"] = 1
    if (not isinstance(saved.get("reset_policy"), bool) and
            isinstance(saved.get("reset_policy"), integer_types) and saved.get("reset_policy") == 2):
        state["reset_policy"] = 2
    if _utc(saved.get("since_utc")) is not None:
        state["since_utc"] = saved["since_utc"]
    amount = exact_amount(saved.get("baseline"))
    if amount is not None and amount >= 0:
        state["baseline"] = amount
    state["excluded_battles"] = _identities(saved.get("excluded_battles"))
    state["excluded_receipts"] = _identities(saved.get("excluded_receipts"))
    generation = exact_amount(saved.get("generation"))
    if generation is not None and generation >= 0:
        state["generation"] = generation
    if _utc(saved.get("daily_cycle")) is not None:
        state["daily_cycle"] = saved["daily_cycle"]
    if saved.get("clock") == LOCAL_CLOCK:
        state["clock"] = LOCAL_CLOCK
    elif saved.get("clock") == SERVER_CLOCK:
        state["clock"] = SERVER_CLOCK
    if state["mode"] == "server":
        state["preserve_goal"] = False
        state["server_cycle"] = (saved.get("server_cycle")
                                  if _utc(saved.get("server_cycle")) is not None else None)
    if now_utc is not None:
        _require_now(now_utc)
        state["next_reset_utc"] = (next_daily_reset(now_utc, state["hour"])
                                   if state["mode"] == "daily" else None)
        if state["mode"] == "server":
            native = _server_cycle(server_clock, now_utc)
            state["next_reset_utc"] = native["next_reset_utc"] if native else None
    return state


def ensure_local_history_clock(previous, region, account_id, now_utc):
    """Rearm legacy daily schedules locally without resetting data or goals."""
    state = get_history_state(previous, region, account_id)
    if state["mode"] != "daily" or state.get("clock") == LOCAL_CLOCK:
        return None
    state["daily_cycle"] = daily_boundary(now_utc, state["hour"])
    state["clock"] = LOCAL_CLOCK
    updated, key = _updated_account(previous, region, account_id)
    updated["account_history"][key] = state
    return updated


def ensure_server_history_clock(previous, region, account_id, now_utc, server_clock=None):
    """Migrate the old manual default and arm a first native cycle, without a reset."""
    _require_now(now_utc)
    state = get_history_state(previous, region, account_id)
    native = _server_cycle(server_clock, now_utc)
    if state["mode"] == "daily" or (state["mode"] == "manual" and state.get("settings_schema") == 1):
        return None
    migrating = state["mode"] != "server" or state.get("settings_schema") != 1
    arming = (state.get("clock") != SERVER_CLOCK or state.get("server_cycle") is None) and native is not None
    if not migrating and not arming:
        return None
    if migrating or state.get("clock") != SERVER_CLOCK:
        state["server_cycle"] = native["cycle_start_utc"] if native else None
    elif arming:
        state["server_cycle"] = native["cycle_start_utc"]
    state.update(mode="server", clock=SERVER_CLOCK, preserve_goal=False, settings_schema=1)
    updated, key = _updated_account(previous, region, account_id)
    updated["account_history"][key] = state
    return updated


def ensure_mandatory_server_history(previous, region, account_id, now_utc, server_clock=None):
    """The daily server reset is integral to the mod, with no scheduling switch.

    Migrate previous manual/local choices without an immediate financial reset.
    An already armed server day remains armed, including an overdue boundary.
    """
    _require_now(now_utc)
    state = get_history_state(previous, region, account_id)
    native = _server_cycle(server_clock, now_utc)
    needs_policy = (state["mode"] != "server" or state.get("reset_policy") != 2 or
                    state.get("clock") != SERVER_CLOCK)
    needs_arm = state.get("server_cycle") is None and native is not None
    if not needs_policy and not needs_arm:
        return None
    prior_cycle = state.get("server_cycle") if state["mode"] == "server" else None
    state.update(mode="server", clock=SERVER_CLOCK, settings_schema=1,
                 reset_policy=2, preserve_goal=False,
                 server_cycle=prior_cycle or (native["cycle_start_utc"] if native else None))
    updated, key = _updated_account(previous, region, account_id)
    updated["account_history"][key] = state
    return updated


def _updated_account(previous, region, account_id):
    key = _key(region, account_id)
    if not isinstance(previous, dict) or key is None:
        raise ValueError(u"Espera que se sincronice tu cuenta antes de cambiar el historial.")
    updated = copy.deepcopy(previous)
    if not isinstance(updated.get("account_history"), dict):
        updated["account_history"] = {}
    return updated, key


def parse_history_settings(args, previous, region, account_id, now_utc, server_clock=None):
    """Validate user settings and arm a daily schedule from the current cycle."""
    if not isinstance(args, dict):
        raise ValueError(u"Las opciones del historial no son v\u00e1lidas.")
    _require_now(now_utc)
    state = get_history_state(previous, region, account_id)
    mode = args.get("mode", state["mode"])
    hour = args.get("hour", state["hour"])
    preserve = args.get("preserve_goal", state["preserve_goal"])
    if mode not in ("manual", "daily", "server"):
        raise ValueError(u"Selecciona reinicio manual, diario o del servidor.")
    if not _valid_hour(hour):
        raise ValueError(u"La hora de reinicio debe estar entre 0 y 23.")
    if not isinstance(preserve, bool):
        raise ValueError(u"La opci\u00f3n de conservar la meta no es v\u00e1lida.")
    if mode == "daily" and (state["mode"] != "daily" or hour != state["hour"] or
                            state["daily_cycle"] is None or state.get("clock") != LOCAL_CLOCK):
        state["daily_cycle"] = daily_boundary(now_utc, hour)
    if mode == "daily":
        state["clock"] = LOCAL_CLOCK
    if mode == "server":
        native = _server_cycle(server_clock, now_utc)
        if (state["mode"] != "server" or state.get("clock") != SERVER_CLOCK or
                state.get("server_cycle") is None):
            state["server_cycle"] = native["cycle_start_utc"] if native else None
        state["clock"] = SERVER_CLOCK
        # A new server day starts a fresh default goal rather than old progress.
        preserve = False
    state.update(mode=mode, hour=hour, preserve_goal=preserve, settings_schema=1)
    updated, key = _updated_account(previous, region, account_id)
    updated["account_history"][key] = state
    return updated


def daily_reset_due(config, region, account_id, now_utc):
    state = get_history_state(config, region, account_id)
    return bool(state["mode"] == "daily" and state["daily_cycle"] is not None and
                daily_boundary(now_utc, state["hour"]) > state["daily_cycle"])


def server_reset_due(config, region, account_id, now_utc, server_clock=None):
    """A synchronized native cycle must advance; reconnects alone are not resets."""
    _require_now(now_utc)
    state = get_history_state(config, region, account_id)
    native = _server_cycle(server_clock, now_utc)
    return bool(state["mode"] == "server" and state.get("clock") == SERVER_CLOCK and
                state.get("server_cycle") is not None and native is not None and
                native["cycle_start_utc"] > state["server_cycle"])


def reset_history_config(previous, region, account_id, balance, now_utc,
                         battle_ids, receipt_ids, automatic=False,
                         server_clock=None, clear_goal=False):
    """Start a new visible period without deleting the underlying records."""
    amount = exact_amount(balance)
    if amount is None or amount < 0:
        raise ValueError(u"Espera que se sincronice tu saldo antes de reiniciar el historial.")
    if not isinstance(automatic, bool):
        raise ValueError(u"El tipo de reinicio no es v\u00e1lido.")
    if not isinstance(clear_goal, bool):
        raise ValueError(u"La opci\u00f3n de reiniciar la meta no es v\u00e1lida.")
    _require_now(now_utc)
    state = get_history_state(previous, region, account_id)
    if state["generation"] >= 9007199254740991:
        raise ValueError(u"El contador de reinicios supera el l\u00edmite admitido.")
    # Both caller-triggered and scheduled resets begin at the observed balance
    # and time. A daily cutoff is not backdated after the player was offline.
    state.update(since_utc=now_utc, baseline=amount,
                 excluded_battles=_identities(battle_ids),
                 excluded_receipts=_identities(receipt_ids),
                 generation=state["generation"] + 1)
    if state["mode"] == "server":
        native = _server_cycle(server_clock, now_utc)
        if automatic and native is None:
            raise ValueError(u"Espera que se sincronice el horario del servidor antes de reiniciar.")
        if native is not None:
            state.update(clock=SERVER_CLOCK, server_cycle=native["cycle_start_utc"])
        state["preserve_goal"] = False
        clear_goal = True
    else:
        state["daily_cycle"] = daily_boundary(now_utc, state["hour"])
    if clear_goal:
        state["preserve_goal"] = False
    updated, key = _updated_account(previous, region, account_id)
    updated["account_history"][key] = state
    goals = updated.get("account_goals", {})
    goal = goals.get(key) if isinstance(goals, dict) else None
    if clear_goal:
        generation = exact_amount(goal.get("reset_generation", 0)) if isinstance(goal, dict) else 0
        if generation is None or generation < 0 or generation >= 9007199254740991:
            raise ValueError(u"El contador de reinicios de la meta no es v\u00e1lido.")
        if not isinstance(goals, dict):
            goals = {}
            updated["account_goals"] = goals
        elif "account_goals" not in updated:
            updated["account_goals"] = goals
        # At the numeric limit, keep accounting usable and wait for a balance
        # that can represent the whole default goal before activating it.
        target = DEFAULT_CREDIT_TARGET if amount + DEFAULT_CREDIT_TARGET <= 9007199254740991 else 0
        goals[key] = {"schema": 2, "mode": "balance_growth", "target": target,
                      "baseline": amount if target else None, "since_utc": now_utc if target else None,
                      "reset_generation": generation + 1}
        updated["credit_target"] = target
    elif not state["preserve_goal"] and isinstance(goal, dict):
        target = exact_amount(goal.get("target"))
        if target is not None and target > 0:
            goal.update(baseline=amount, since_utc=now_utc)
    return updated


def _visible(item, state, id_key, exclusions, timestamp_keys):
    if not isinstance(item, dict):
        return False
    state = state if isinstance(state, dict) else {}
    identity = _identity(item.get(id_key))
    excluded = state.get(exclusions)
    if not isinstance(excluded, (set, frozenset)):
        excluded = _identities(excluded)
    if identity is not None and identity in excluded:
        return False
    cutoff = state.get("since_utc")
    if _utc(cutoff) is None:
        return True
    for key in timestamp_keys:
        stamp = item.get(key)
        if _utc(stamp) is not None:
            return stamp >= cutoff
    return False


def record_visible(record, state):
    return _visible(record, state, "battle_id", "excluded_battles",
                    ("completed_at", "occurred_at"))


def receipt_visible(receipt, state):
    return _visible(receipt, state, "id", "excluded_receipts", ("occurred_at",))
