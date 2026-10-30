# -*- coding: utf-8 -*-
"""BigWorld entry points for the original offline credit-ledger release."""
from __future__ import division

import datetime
import copy
import os
import re
import sys
import time
import traceback

from .native import derive_credits
from .normalizer import normalize_snapshot, result_time
from .snapshot import CLIENT_VERSION, make_snapshot
from .vehicles import resolve_vehicles, merge_vehicles
from .battle_modes import battle_mode_from_common
from .storage import CaptureStore, atomic_json, read_json, json_exists
from .presentation import (build_payload, parse_goal_command, parse_reset_goal_command,
                           ensure_balance_goal, balance_goal, history_ledger)
from .wallet import WalletBook, reward_receipt, REWARD_KINDS, safe_text
from .history import (get_history_state, record_visible, parse_history_settings,
                      reset_history_config, ensure_mandatory_server_history, server_reset_due)
from .server_clock import native_server_clock
from .archive import server_day_bounds
from .localization import language, translate
from .completion import (sync_goal_completion, goal_completion_payload,
                         acknowledge_goal_completion)
from .compatibility import resolve_realm, client_version

VERSION = "0.22.14"
PREFIX = "[CreditLedger]"

_MATCHMAKING_TYPES = frozenset((
    ("gui.Scaleform.daapi.view.lobby.battle_queue.states", "CommonBattleQueueState"),
    ("gui.Scaleform.daapi.view.lobby.battle_queue.states", "StrongholdsBattleQueueState"),
    ("halloween.gui.impl.lobby.states", "HalloweenPreBattleQueueState"),
    ("last_stand.gui.impl.lobby.states", "LastStandPreBattleQueueState"),
    ("gui.impl.lobby.maps_training.states", "MapsTrainingQueueState"),
    ("battle_royale.gui.impl.lobby.views.states", "BattleRoyaleTournamentQueueState"),
))


def _is_matchmaking_state(state):
    """Recognize loaded native queue classes without initializing event modes."""
    for cls in type(state).__mro__:
        module_name, name = cls.__module__, cls.__name__
        if (module_name, name) in _MATCHMAKING_TYPES:
            module = sys.modules.get(module_name)
            if module is not None and getattr(module, name, None) is cls:
                return True
    return False


def _now_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def credits_text(amount, selected="es"):
    text = format(int(amount), ",d")
    return text if selected == "en" else text.replace(",", ".")


def _view_request_id(value):
    """Canonicalize native Wulf numeric arguments without changing money parsing.

    Command arguments can arrive as strings or real numbers. The stock client
    explicitly converts numeric command fields too. Only exact, positive JS-safe
    integers are valid sequence IDs; booleans and permissive int coercions are not.
    """
    try:
        strings, integers = (basestring,), (int, long)
    except NameError:
        strings, integers = (str,), (int,)
    if isinstance(value, bool):
        raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
    if isinstance(value, strings):
        if len(value) > 16 or not re.match(r"[1-9][0-9]*\Z", value):
            raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
        parsed = int(value)
    elif isinstance(value, integers):
        parsed = value
    elif isinstance(value, float):
        try:
            parsed = int(value)
        except (ValueError, OverflowError):
            raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
        if parsed != value:
            raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
    else:
        raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
    if not 0 < parsed <= 9007199254740991:
        raise ValueError(u"La solicitud del filtro no es v\u00e1lida.")
    return parsed


def _view_filter_keys(args):
    try:
        string_type = basestring
    except NameError:
        string_type = str
    mode_key, vehicle_key = args.get("mode_key"), args.get("vehicle_key")
    if (not isinstance(mode_key, string_type) or len(mode_key) > 32 or
            not re.match(r"(?:all|unknown|mode:(?:0|[1-9][0-9]{0,9}))\Z", mode_key) or
            (mode_key.startswith("mode:") and int(mode_key[5:]) > 2147483647)):
        raise ValueError(u"El modo seleccionado no es v\u00e1lido.")
    if (not isinstance(vehicle_key, string_type) or len(vehicle_key) > 32 or
            not re.match(r"(?:all|unknown|multiple|vehicle:[1-9][0-9]{0,9})\Z", vehicle_key) or
            (vehicle_key.startswith("vehicle:") and int(vehicle_key[8:]) > 2147483647)):
        raise ValueError(u"El veh\u00edculo seleccionado no es v\u00e1lido.")
    return mode_key, vehicle_key


def _game_client_version(directory):
    with open(os.path.join(directory, "version.xml"), "rb") as handle:
        return client_version(handle.read(16384).decode("utf-8", "replace"))


def _game_directory():
    candidates = [os.path.dirname(sys.executable),
                  os.path.dirname(os.path.dirname(sys.executable)),
                  os.getcwd(), os.path.dirname(os.getcwd())]
    for candidate in candidates:
        version_path = os.path.join(candidate, "version.xml")
        if os.path.isdir(os.path.join(candidate, "mods")) and os.path.isfile(version_path):
            try:
                _game_client_version(candidate)
                return os.path.abspath(candidate)
            except RuntimeError:
                continue
    raise RuntimeError("client version/root is not a supported 2.4.1.0 or 2.4.1.1 installation")


class Collector(object):
    def __init__(self):
        import BigWorld
        import BattleReplay
        import constants
        from PlayerEvents import g_playerEvents
        from .ledger import EconomyLedger

        self.world = BigWorld
        self.replay = BattleReplay
        self.events = g_playerEvents
        self.realm = resolve_realm(constants)
        game_directory = _game_directory()
        self.client_version = _game_client_version(game_directory)
        self.directory = os.path.join(game_directory, "mods", "configs", "credit_ledger")
        self.store = CaptureStore(self.directory)
        self._alive = True
        self._tick_id = None
        self._notice_ids = set()
        self._pending = {}
        self._restored_accounts = set()
        self._vehicle_items = {}
        self._vehicle_filter = None
        self._vehicle_filter_context = None
        self._vehicle_filter_generation = None
        self._vehicle_filter_model = None
        self._last_vehicle_filter_request_id = 0
        self._archive_filter = None
        self._archive_filter_context = None
        self._archive_filter_generation = None
        self._archive_filter_model = None
        self._last_archive_filter_request_id = 0
        self._language_selection = None
        self._language_selection_model = None
        self._last_language_request_id = 0
        self._in_flight = False
        self._hooks = []
        self.panel = None
        self.panel_error = None
        self._gui_account_id = None
        self._server_clock_account_id = None
        self._garage_visible = False
        self._completion_display_generation = 0
        self._completion_display_context = None
        self._completion_display_ready = False
        self._completion_presence_callback = None
        self._completion_presence_key = None
        self._completion_presence_attempts = 0
        self._garage_recovery_allowed = False
        self._app_loader = None
        self._lobby_space_id = None
        self._garage_route_machine = None
        self._garage_route_event = None
        self._battle_account_id = None
        self._receipt_queue = []
        self._wallet_callback = None
        self._message_types = {}
        self._quest_names = {}
        self._rewards_registered = False
        self._coupon_observer = None
        self.started_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.last_capture = None
        self.last_error = None
        self.captures_this_run = 0
        self.config_path = os.path.join(self.directory, "config.json")
        if json_exists(self.config_path):
            self.config = read_json(self.config_path)
        else:
            self.config = {"enabled": True, "notifications": True,
                           "credit_target": 100000, "goal_mode": "balance_growth",
                           "goal_since_utc": self.started_at}
            atomic_json(self.config_path, self.config)
        if not isinstance(self.config, dict):
            raise ValueError("credit ledger config must be an object")
        self.ledger_path = os.path.join(self.directory, "ledger.json")
        self.ledger = (EconomyLedger.load(self.ledger_path)
                       if json_exists(self.ledger_path) else EconomyLedger())
        self.wallet_path = os.path.join(self.directory, "wallet.json")
        self.wallet = WalletBook(read_json(self.wallet_path) if json_exists(self.wallet_path) else None)
        if not self.config.get("enabled", True):
            self._alive = False
            self._status("disabled")
            return
        try:
            self._subscribe("onBattleResultsReceived", self._on_result)
            self._subscribe("onAvatarBecomePlayer", self._on_avatar)
            self._subscribe("onAccountBecomePlayer", self._on_account)
            self._subscribe("onAccountBecomeNonPlayer", self._leave_account)
            self._subscribe("onAccountShowGUI", self._on_account_gui)
            self._subscribe("onClientUpdated", self._on_client_updated)
            self._status("listening")
            self._schedule_tick()
        except Exception:
            self.close()
            raise
        try:
            from .panel import LedgerPanel
            self.panel = LedgerPanel(self)
        except Exception:
            print(PREFIX + " garage widget unavailable; economy capture remains active")
            traceback.print_exc()
        self._bind_lobby()
        try:
            from chat_shared import SYS_MESSAGE_TYPE
            from messenger.proto.events import g_messengerEvents
            for kind in list(REWARD_KINDS) + ["battleResults"]:
                entry = getattr(SYS_MESSAGE_TYPE, kind, None)
                if entry is not None:
                    self._message_types[entry.index()] = kind
            event = g_messengerEvents.serviceChannel.onChatMessageReceived
            event += self._on_sys_message
            self._hooks.append((event, self._on_sys_message))
            self._rewards_registered = True
        except Exception:
            print(PREFIX + " native reward receipts unavailable")
            traceback.print_exc()
        try:
            from .coupons import CouponObserver
            self._coupon_observer = CouponObserver(self)
        except Exception:
            print(PREFIX + " voucher observer unavailable; balance tracking remains active")
            traceback.print_exc()
        self._status("listening")
        print(PREFIX + " " + VERSION + " listening for own battle economy")

    def _subscribe(self, name, callback):
        event = getattr(self.events, name)
        event += callback
        self._hooks.append((event, callback))

    def _status(self, state):
        self.store.write_status({"version": VERSION, "client_version": self.client_version,
                                 "state": state, "started_at": self.started_at,
                                 "captures_this_run": self.captures_this_run,
                                 "last_capture": self.last_capture,
                                 "last_error": self.last_error,
                                 "reference_battle_comparison": "confirmed_by_user",
                                 "reference_battle_net_credits": -113508,
                                 "reward_listener_registered": self._rewards_registered,
                                 "voucher_observer_registered": self._coupon_observer is not None,
                                 "panel_available": self.panel is not None,
                                 "mod_menu_entry_registered": False,
                                 "native_lobby_lifecycle_bound": self._app_loader is not None})

    def _error(self, operation):
        self.last_error = operation
        print(PREFIX + " " + operation + "; see traceback")
        traceback.print_exc()
        try:
            self._status("listening_with_error")
        except Exception:
            traceback.print_exc()

    def _notify(self, message):
        if not self._alive or not self.config.get("notifications", True) or self.replay.isPlaying():
            return
        try:
            from gui import SystemMessages
            SystemMessages.pushMessage(translate(message, language(self.config)),
                                       type=SystemMessages.SM_TYPE.Information)
        except Exception:
            print(PREFIX + " notification unavailable")

    def _defer_notice(self, callback):
        token = [None]
        def run():
            self._notice_ids.discard(token[0])
            if self._alive:
                try:
                    callback()
                except Exception:
                    self._error("notification_failed")
        token[0] = self.world.callback(2.0, run)
        self._notice_ids.add(token[0])

    def _on_account(self, *args):
        self._leave_account()
        if self._alive:
            self._garage_recovery_allowed = True
            self._ensure_garage_widget(restore=True)
            self._defer_notice(lambda: self._notify(
                u"Contabilidad de cr\u00e9ditos: captura activa. "
                u"El widget aparece en el garaje; pulsa el c\u00edrculo para abrir el resumen."))

    def _leave_account(self, *args):
        self._invalidate_completion_display()
        self._unbind_garage_route()
        self._garage_visible = False
        self._garage_recovery_allowed = False
        self._gui_account_id = None
        self._server_clock_account_id = None
        self._battle_account_id = None
        self._receipt_queue = []
        self._quest_names = {}
        self.panel_error = None
        if self.panel is not None:
            self.panel.close_window()

    def _on_account_gui(self, context):
        if not self._alive or self.replay.isPlaying():
            return
        player = self.world.player()
        if player is None or not hasattr(player, "battleResultsCache"):
            return
        native_id = getattr(player, "databaseID", None)
        value = context.get("databaseID") if isinstance(context, dict) else None
        if value and native_id and str(value) != str(native_id):
            return
        self._garage_recovery_allowed = True
        self._gui_account_id = str(value) if value else None
        # Account.showGUI initializes native server UTC correction before this
        # event. Do not use an earlier helper fallback based on the PC clock.
        self._server_clock_account_id = str(native_id or value) if native_id or value else None
        self._on_client_updated()
        self._ensure_garage_widget(restore=True)
        if self.panel is not None:
            self.panel.refresh()

    def _bind_lobby(self):
        """Observe the native lobby space, including late GUI initialization."""
        if self._app_loader is not None:
            return True
        attached = []
        try:
            from helpers import dependency
            from skeletons.gui.app_loader import IAppLoader, GuiGlobalSpaceID
            loader = dependency.instance(IAppLoader)
            lobby_space_id = GuiGlobalSpaceID.LOBBY
            connections = ((loader.onGUISpaceEntered, self._on_gui_space_entered),
                           (loader.onGUISpaceLeft, self._on_gui_space_left),
                           (loader.onGUIInitialized, self._on_gui_initialized))
            if not callable(loader.getSpaceID):
                return False
            for event, callback in connections:
                event += callback
                attached.append((event, callback))
            self._app_loader = loader
            self._lobby_space_id = lobby_space_id
            self._hooks.extend(attached)
        except Exception:
            for event, callback in reversed(attached):
                try:
                    event -= callback
                except Exception:
                    pass
            return False
        if self._native_lobby_state() is True and self._has_account_entity():
            self._garage_recovery_allowed = True
        self._ensure_garage_widget(restore=True)
        return True

    def _native_lobby_state(self):
        if self._app_loader is None:
            return None
        try:
            return self._app_loader.getSpaceID() == self._lobby_space_id
        except Exception:
            # A known service failing is not evidence that the garage is open.
            return False

    def _has_account_entity(self):
        player = self.world.player()
        return player is not None and hasattr(player, "battleResultsCache")

    def _unbind_garage_route(self):
        event = self._garage_route_event
        self._garage_route_event = None
        self._garage_route_machine = None
        if event is not None:
            try:
                event -= self._on_garage_route_changed
            except Exception:
                pass

    def _garage_view_visible(self):
        """The lobby also contains research, profile, store and other pages.

        Use the native HANGAR flag for garages and native battle queue classes
        for matchmaking. Other pages and unknown/loading routes stay hidden.
        """
        try:
            from gui.Scaleform.lobby_entry import getLobbyStateMachine
            from gui.lobby_state_machine.states import isHangarState
            machine = getLobbyStateMachine()
            if machine is not self._garage_route_machine:
                self._unbind_garage_route()
                if machine is not None:
                    event = machine.onVisibleRouteChanged
                    event += self._on_garage_route_changed
                    self._garage_route_machine = machine
                    self._garage_route_event = event
            if machine is None:
                return False
            state = machine.visibleState
            if state is None:
                return False
            if isHangarState(state):
                return True
            return _is_matchmaking_state(state)
        except Exception:
            return False

    def _on_garage_route_changed(self, *args):
        if self._alive:
            self._ensure_garage_widget(restore=True)

    def _on_gui_space_entered(self, space_id):
        if not self._alive:
            return
        if space_id == self._lobby_space_id and self._native_lobby_state() is True:
            if self._has_account_entity():
                self._garage_recovery_allowed = True
            self._ensure_garage_widget(restore=True)
        else:
            self._invalidate_completion_display()
            self._unbind_garage_route()
            self._garage_visible = False
            self._garage_recovery_allowed = False
            if self.panel is not None:
                self.panel.close_window()

    def _on_gui_space_left(self, space_id):
        if space_id == self._lobby_space_id:
            self._invalidate_completion_display()
            self._unbind_garage_route()
            self._garage_visible = False
            self._garage_recovery_allowed = False
            if self.panel is not None:
                self.panel.close_window()

    def _on_gui_initialized(self):
        self._ensure_garage_widget(restore=True)

    def _ensure_garage_widget(self, restore=False):
        if not self._alive or self.replay.isPlaying() or self.panel is None:
            return
        lobby = self._native_lobby_state()
        if lobby is False or not self._garage_view_visible():
            was_visible = self._garage_visible
            if was_visible:
                self._invalidate_completion_display()
            self._garage_visible = False
            if was_visible:
                self.panel.close_window()
            return
        if not self._garage_recovery_allowed or not self._account_id():
            return
        self._garage_visible = True
        try:
            self.panel.ensure_visible(restore=restore)
        except Exception:
            self._error("garage_widget_unavailable")

    def _on_avatar(self, *args):
        self._invalidate_completion_display()
        self._unbind_garage_route()
        self._garage_visible = False
        self._garage_recovery_allowed = False
        self._gui_account_id = None
        self._server_clock_account_id = None
        self._battle_account_id = None
        if self.panel is not None:
            self.panel.close_window()
        if not self._alive or self.replay.isPlaying():
            return
        try:
            player = self.world.player()
            arena_id = getattr(player, "arenaUniqueID", None)
            arena = getattr(player, "arena", None)
            own_vehicle = getattr(player, "playerVehicleID", None)
            own_row = arena.vehicles.get(own_vehicle, {}) if arena is not None else {}
            account_id = own_row.get("accountDBID")
            if account_id:
                self._battle_account_id = str(account_id)
            if arena_id and account_id:
                self._pending[(str(account_id), int(arena_id))] = time.time()
        except Exception:
            self._error("pending_identity_unavailable")

    def _on_result(self, is_player_vehicle, results):
        if not self._alive or not is_player_vehicle or self.replay.isPlaying():
            return
        self._capture(results, "event")

    def _capture(self, results, source, expected_account=None):
        if not self._alive or self.replay.isPlaying():
            return
        try:
            snapshot = make_snapshot(results, self.realm, source, client=self.client_version)
            if expected_account is not None and snapshot["account_id"] != expected_account:
                raise ValueError("cached result belongs to a different account")
            rows = snapshot["personal"]["vehicles"]
            resolved = dict((row["vehicle_type_id"], row) for row in resolve_vehicles(rows, self._vehicle_item))
            for row in rows:
                row.update(resolved.get(row["vehicle_type_id"], {}))
            record = None
            try:
                snapshot["native_credits"] = derive_credits(results)
                snapshot["reconciliation"] = {"status": "native_calculated",
                                                "compared_with_real_report": False}
                record = normalize_snapshot(snapshot)
            except Exception as error:
                snapshot["reconciliation"] = {"status": "unverified",
                                                "reason_type": type(error).__name__,
                                                "reason": str(error)[:256]}
                print(PREFIX + " native financial mapping unavailable; raw capture retained")
                traceback.print_exc()
            action, path = self.store.save(snapshot)
            ledger_action = "unchanged"
            if record is not None:
                next_ledger = type(self.ledger).from_dict(self.ledger.to_dict())
                ledger_action = next_ledger.upsert_result(record)
                if ledger_action != "unchanged":
                    next_ledger.save(self.ledger_path)
                    self.ledger = next_ledger
            self._pending.pop((snapshot["account_id"], int(snapshot["battle_id"])), None)
            if action != "unchanged" or ledger_action != "unchanged":
                self.captures_this_run += 1
                self.last_capture = os.path.relpath(path, self.directory)
                self.last_error = None
                self._status("listening")
                if record is not None:
                    self._defer_notice(lambda: self._result_notice(record))
                else:
                    self._defer_notice(lambda: self._notify(
                        u"Contabilidad: resultado guardado; desglose pendiente de conciliaci\u00f3n."))
                print(PREFIX + " own economy capture " + action)
            if self.panel is not None:
                self.panel.refresh()
        except Exception:
            self._error("capture_failed")

    def _account_id(self):
        player = self.world.player()
        # The GUI event is an account-only fallback while the hangar is loading.
        if player is None or not hasattr(player, "battleResultsCache"):
            return None
        value = getattr(player, "databaseID", None)
        return str(value) if value else self._gui_account_id

    def panel_payload(self):
        self._sync_finance()
        account_id = self._account_id()
        server_clock = self._read_server_clock() if account_id else None
        now = server_clock["server_now_utc"] if server_clock else _now_utc()
        state = get_history_state(self.config, self.realm, account_id, now, server_clock)
        state["excluded_battles"] = frozenset(state["excluded_battles"])
        archive_filter = self._active_archive_selection(account_id, state)
        archive_bounds = (server_day_bounds(self.config, self.realm, account_id, now,
                          server_clock, archive_filter.get("day_key")) if archive_filter else None)
        pending = 0
        if account_id:
            candidates = self.store.recovery_candidates(self.realm, account_id)
            self._enrich_vehicle_history(account_id, candidates, archive_bounds)
            self._enrich_missing_mode_history(account_id, state, archive_bounds)
            known = set(row["battle_id"] for row in self.ledger.list_results(
                self.realm, account_id, include_pending=False))
            pending_ids = set()
            for item in candidates:
                try:
                    identity = item["battle_id"]
                    if identity not in known and identity and record_visible({
                            "battle_id":identity, "occurred_at":result_time(item)}, state):
                        pending_ids.add(identity)
                except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
                    # Keep malformed evidence on disk without breaking the view.
                    continue
            pending = len(pending_ids)
        payload = build_payload(self.ledger, self.realm, account_id, self.config,
                             self._read_balance() if account_id else None,
                             pending_count=pending, error=self.panel_error, wallet=self.wallet, now_utc=now,
                             vehicle_filter=self._active_vehicle_filter(account_id, state),
                             archive_filter=archive_filter,
                             server_clock=server_clock)
        payload["goal_completion"] = (goal_completion_payload(
            self.config, self.realm, account_id,
            self._read_balance() if account_id else None)
            if self._alive and not self.replay.isPlaying() else None)
        payload["completion_display"] = self._completion_display(account_id)
        self._schedule_completion_presence(payload["goal_completion"], payload["completion_display"])
        if self._language_selection_model is getattr(self.panel, "model", None):
            selection = copy.deepcopy(self._language_selection)
            if selection is not None:
                selection["language"] = language(self.config)
                selection["error"] = translate(selection.get("error"), language(self.config))
            payload["language_selection"] = selection
        else:
            payload["language_selection"] = None
        return payload

    def _invalidate_completion_display(self):
        """An old visible-view acknowledgement must not survive a transition."""
        self._completion_display_generation += 1
        self._completion_display_ready = False
        self._completion_presence_key = None
        callback = self._completion_presence_callback
        self._completion_presence_callback = None
        if callback is not None:
            try:
                self.world.cancelCallback(callback)
            except Exception:
                pass

    def _read_completion_stage(self):
        """Native hangar load/Waiting checks, not a timer or balance heuristic.

        Installed 2.4.1.0 HangarSpace itself delays actions until spaceInited;
        isModelLoaded and Waiting additionally exclude the black loading stage.
        An unavailable service is not evidence that the celebration is visible.
        """
        try:
            from helpers import dependency
            from skeletons.gui.shared.utils import IHangarSpace
            from gui.Scaleform.Waiting import Waiting
            space = dependency.instance(IHangarSpace)
            initialized = space.spaceInited
            loaded = space.isModelLoaded
            loaded = loaded() if callable(loaded) else loaded
            return initialized is True and loaded is True and Waiting.isVisible() is False
        except Exception:
            return False

    def _completion_display(self, account_id=None):
        account_id = account_id or self._account_id()
        context = self.realm + ":" + account_id if account_id else None
        panel_ready = getattr(self.panel, "completion_surface_ready", None)
        ready = bool(self._alive and not self.replay.isPlaying() and account_id and
                     self._garage_visible and self._server_clock_account_id == account_id and
                     self._native_lobby_state() is True and self._garage_view_visible() and
                     self._read_completion_stage() and
                     callable(panel_ready) and panel_ready())
        if (context != self._completion_display_context or ready != self._completion_display_ready):
            self._completion_display_generation += 1
            self._completion_display_context = context
            self._completion_display_ready = ready
        return {"ready": ready, "generation": self._completion_display_generation,
                "account_context": context}

    def _schedule_completion_presence(self, event, display):
        """Briefly publish real loading transitions while a completion is pending.

        Twenty seconds per presentation state, only for this native visible
        panel; ordinary ten-second collection remains the fallback afterwards.
        """
        if (not event or not self._alive or self.panel is None or
                getattr(self.panel, "model", None) is None or
                getattr(self.panel, "_mode", None) not in ("widget", "details") or
                self._native_lobby_state() is not True):
            self._completion_presence_key = None
            callback = self._completion_presence_callback
            self._completion_presence_callback = None
            if callback is not None:
                try:
                    self.world.cancelCallback(callback)
                except Exception:
                    pass
            return
        key = (event["id"], event["account_context"], display["generation"])
        if key != self._completion_presence_key:
            self._completion_presence_key = key
            self._completion_presence_attempts = 40
        if self._completion_presence_callback is None and self._completion_presence_attempts > 0:
            self._completion_presence_attempts -= 1
            self._completion_presence_callback = self.world.callback(0.5, self._poll_completion_presence)

    def _poll_completion_presence(self):
        self._completion_presence_callback = None
        if self._alive and self.panel is not None:
            self.panel.refresh()

    def acknowledge_goal_completion(self, args):
        """Consume only this event; never clear unrelated panel feedback."""
        try:
            account_id = self._account_id()
            if (not self._alive or self.replay.isPlaying() or not account_id):
                return
            pending = goal_completion_payload(self.config, self.realm, account_id,
                                              self._read_balance())
            if (not isinstance(args, dict) or pending is None or
                    args.get("id") != pending["id"] or
                    args.get("account_context") != pending["account_context"]):
                return
            try:
                generation = _view_request_id(args.get("presentation_generation"))
            except ValueError:
                return
            display = self._completion_display(account_id)
            if not display["ready"] or generation != display["generation"]:
                # Publish a loading/hidden transition found at the exact ACK
                # boundary so that this same pending event can be shown later.
                if self.panel is not None:
                    self.panel.refresh(force=True)
                return
            updated = acknowledge_goal_completion(self.config, self.realm,
                        account_id, self._read_balance(), args)
            if updated is None:
                return
            atomic_json(self.config_path, updated)
            self.config = updated
            print(PREFIX + " goal completion shown and acknowledged")
        except Exception:
            # Keep the durable pending event available for a later retry.
            self._error("goal_completion_ack_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def set_language(self, args):
        """Persist only the language and refresh this same live native view."""
        model = getattr(self.panel, "model", None)
        if model is not self._language_selection_model:
            self._language_selection_model = model
            self._language_selection = None
            self._last_language_request_id = 0
        request_id, requested = None, None
        try:
            if not isinstance(args, dict):
                raise ValueError(u"Selecciona español o inglés.")
            request_id = _view_request_id(args.get("request_id"))
            if request_id <= self._last_language_request_id:
                return
            self._last_language_request_id = request_id
            requested = args.get("language")
            try:
                strings = (basestring,)
            except NameError:
                strings = (str,)
            if not isinstance(requested, strings) or requested not in ("es", "en"):
                requested = None
                raise ValueError(u"Selecciona español o inglés.")
            if self.config.get("ui_language") != requested:
                updated = copy.deepcopy(self.config)
                updated["ui_language"] = requested
                # Publish the preference only after the whole config was saved.
                # Failed writes leave financial/history settings and language intact.
                atomic_json(self.config_path, updated)
                self.config = updated
            self._language_selection = {"request_id": request_id,
                "requested_language": requested, "language": language(self.config),
                "available": True, "error": None}
        except ValueError as error:
            message = str(error) if sys.version_info[0] >= 3 else unicode(error)
            self._language_selection = {"request_id": request_id,
                "requested_language": requested, "language": language(self.config),
                "available": False, "error": message}
        except Exception:
            message = u"No se pudo guardar el idioma. La selección anterior se conserva."
            self._language_selection = {"request_id": request_id,
                "requested_language": requested, "language": language(self.config),
                "available": False, "error": message}
            self._error("language_save_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def _active_vehicle_filter(self, account_id, state):
        context = self.realm + ":" + str(account_id) if account_id else None
        if (context != self._vehicle_filter_context or
                state["generation"] != self._vehicle_filter_generation or
                (self._vehicle_filter is not None and
                 getattr(self.panel, "model", None) is not self._vehicle_filter_model)):
            self._vehicle_filter = None
            self._vehicle_filter_context = None
            self._vehicle_filter_generation = None
            self._vehicle_filter_model = None
            self._last_vehicle_filter_request_id = 0
        return self._vehicle_filter

    def set_vehicle_filter(self, args):
        """Request one vehicle's history without writing any filter to disk."""
        try:
            account_id = self._account_id()
            context = self.realm + ":" + str(account_id) if account_id else None
            if (not isinstance(args, dict) or context is None or
                    args.get("account_context") != context):
                raise ValueError(u"La cuenta cambi\u00f3. Vuelve a elegir el veh\u00edculo.")
            mode_key, vehicle_key = _view_filter_keys(args)
            request_id = _view_request_id(args.get("request_id"))
            state = get_history_state(self.config, self.realm, account_id, _now_utc())
            model = getattr(self.panel, "model", None)
            if (context != self._vehicle_filter_context or
                    state["generation"] != self._vehicle_filter_generation or
                    model is not self._vehicle_filter_model):
                self._last_vehicle_filter_request_id = 0
            if request_id > self._last_vehicle_filter_request_id:
                self._vehicle_filter = {"mode_key": mode_key, "vehicle_key": vehicle_key,
                                        "request_id": request_id}
                self._vehicle_filter_context = context
                self._vehicle_filter_generation = state["generation"]
                self._vehicle_filter_model = model
                self._last_vehicle_filter_request_id = request_id
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudo cargar el veh\u00edculo. Vuelve a intentarlo."
            self._error("vehicle_filter_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def _active_archive_selection(self, account_id, state):
        context = self.realm + ":" + str(account_id) if account_id else None
        if (context != self._archive_filter_context or
                state["generation"] != self._archive_filter_generation or
                (self._archive_filter is not None and
                 getattr(self.panel, "model", None) is not self._archive_filter_model)):
            self._archive_filter = None
            self._archive_filter_context = None
            self._archive_filter_generation = None
            self._archive_filter_model = None
            self._last_archive_filter_request_id = 0
        return self._archive_filter

    def set_archive_selection(self, args):
        """Read an older server day's evidence; never mutate account statistics."""
        try:
            account_id = self._account_id()
            context = self.realm + ":" + str(account_id) if account_id else None
            if (not isinstance(args, dict) or context is None or
                    args.get("account_context") != context):
                raise ValueError(u"La cuenta cambi\u00f3. Vuelve a elegir el d\u00eda.")
            mode_key, vehicle_key = _view_filter_keys(args)
            request_id = _view_request_id(args.get("request_id"))
            day_key = args.get("day_key")
            try:
                string_type = basestring
            except NameError:
                string_type = str
            if (not isinstance(day_key, string_type) or len(day_key) != 20 or
                    not re.match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z", day_key)):
                raise ValueError(u"El d\u00eda seleccionado no es v\u00e1lido.")
            parsed = datetime.datetime.strptime(day_key, "%Y-%m-%dT%H:%M:%SZ")
            if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != day_key:
                raise ValueError(u"El d\u00eda seleccionado no es v\u00e1lido.")
            state = get_history_state(self.config, self.realm, account_id, _now_utc())
            model = getattr(self.panel, "model", None)
            if (context != self._archive_filter_context or
                    state["generation"] != self._archive_filter_generation or
                    model is not self._archive_filter_model):
                self._last_archive_filter_request_id = 0
            if request_id > self._last_archive_filter_request_id:
                self._archive_filter = {"day_key": day_key, "mode_key": mode_key,
                                        "vehicle_key": vehicle_key, "request_id": request_id}
                self._archive_filter_context = context
                self._archive_filter_generation = state["generation"]
                self._archive_filter_model = model
                self._last_archive_filter_request_id = request_id
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudo cargar el d\u00eda. Vuelve a intentarlo."
            self._error("archive_selection_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def _vehicle_item(self, compact_id):
        if compact_id not in self._vehicle_items:
            from helpers import dependency
            from skeletons.gui.shared import IItemsCache
            item = dependency.instance(IItemsCache).items.getItemByCD(compact_id)
            if item is not None:
                self._vehicle_items[compact_id] = item
            return item
        return self._vehicle_items[compact_id]

    def _enrich_vehicle_history(self, account_id, snapshots, archive_bounds=None):
        """Recover vehicle/mode metadata; keep original financial evidence intact."""
        try:
            by_battle = dict((item.get("battle_id"), item) for item in snapshots
                             if item.get("region") == self.realm and item.get("account_id") == str(account_id))
            state = get_history_state(self.config, self.realm, account_id)
            state["excluded_battles"] = frozenset(state["excluded_battles"])
            records = [record for record in self.ledger.list_results(
                self.realm, account_id, include_pending=False)
                if self._metadata_record_visible(record, state, archive_bounds)]
            # One native metadata lookup per type also refreshes older mode or
            # tank histories outside the global 100-row display window.
            resolved_by_type = {}
            next_ledger = None
            for record in records:
                snapshot = by_battle.get(record["battle_id"], {})
                personal = snapshot.get("personal", {})
                personal = personal if isinstance(personal, dict) else {}
                rows = merge_vehicles(record.get("vehicles", []), personal.get("vehicles", []))
                vehicles = []
                for row in rows:
                    identity = row["vehicle_type_id"]
                    if identity not in resolved_by_type:
                        resolved_by_type[identity] = resolve_vehicles(
                            [{"vehicle_type_id": identity}], self._vehicle_item)[0]
                    vehicles.append(merge_vehicles([row], [resolved_by_type[identity]])[0])
                mode = record.get("battle_mode")
                if mode is None:
                    mode = battle_mode_from_common(snapshot.get("common", {}))
                if vehicles != record.get("vehicles", []) or mode != record.get("battle_mode"):
                    if next_ledger is None:
                        next_ledger = type(self.ledger).from_dict(self.ledger.to_dict())
                    record["vehicles"] = vehicles
                    record["battle_mode"] = mode
                    next_ledger.upsert_result(record)
            if next_ledger is not None:
                next_ledger.save(self.ledger_path)
                self.ledger = next_ledger
        except Exception:
            # Retry on the next payload, without blocking financial capture/UI.
            print(PREFIX + " history metadata update deferred")

    def _metadata_record_visible(self, record, state, archive_bounds):
        return (record_visible(record, state) or bool(archive_bounds and
                archive_bounds["start_utc"] <= record["occurred_at"] < archive_bounds["end_utc"]))

    def _enrich_missing_mode_history(self, account_id, state, archive_bounds=None):
        """Recover old visible mode metadata without the global 100-row limit."""
        try:
            records = [record for record in self.ledger.list_results(
                self.realm, account_id, include_pending=False)
                if record.get("battle_mode") is None and
                self._metadata_record_visible(record, state, archive_bounds)]
            by_battle = dict((record["battle_id"], record) for record in records)
            candidates = self.store.mode_metadata(self.realm, account_id, sorted(by_battle, reverse=True))
            next_ledger = None
            for snapshot in candidates:
                mode = battle_mode_from_common(snapshot.get("common"))
                record = by_battle.get(snapshot.get("battle_id"))
                if mode is not None and record is not None:
                    if next_ledger is None:
                        next_ledger = type(self.ledger).from_dict(self.ledger.to_dict())
                    record["battle_mode"] = mode
                    next_ledger.upsert_result(record)
            if next_ledger is not None:
                next_ledger.save(self.ledger_path)
                self.ledger = next_ledger
        except Exception:
            print(PREFIX + " old battle mode metadata update deferred")

    def save_history_settings(self, args):
        try:
            account_id = self._account_id()
            if not account_id:
                raise ValueError(u"Espera que se sincronice tu cuenta antes de cambiar el historial.")
            if (not isinstance(args, dict) or args.get("mode") != "server" or
                    args.get("preserve_goal", False) is not False):
                raise ValueError(u"El reinicio diario del servidor es autom\u00e1tico y permanece activo.")
            server_clock = self._read_server_clock()
            now = server_clock["server_now_utc"] if server_clock else _now_utc()
            updated = parse_history_settings(args, self.config, self.realm, account_id,
                                             now, server_clock)
            atomic_json(self.config_path, updated)
            self.config = updated
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudieron guardar los ajustes del historial."
            self._error("history_settings_save_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def _reset_history(self, account_id, balance, now, automatic=False,
                       server_clock=None, clear_goal=False):
        battle_ids = [row["battle_id"] for row in self.ledger.list_results(self.realm, account_id)]
        battle_ids.extend(row["battle_id"] for row in self.store.recovery_candidates(self.realm, account_id))
        receipt_ids = [row["id"] for row in self.wallet.receipts(self.realm, account_id)]
        updated = reset_history_config(self.config, self.realm, account_id, balance, now,
                                       battle_ids, receipt_ids, automatic=automatic,
                                       server_clock=server_clock, clear_goal=clear_goal)
        updated = sync_goal_completion(updated, self.realm, account_id, balance) or updated
        # One atomic configuration commit changes the period, its balance base
        # and the goal together. Failed saves leave the previous period intact.
        atomic_json(self.config_path, updated)
        self.config = updated

    def reset_history(self, args):
        try:
            if not isinstance(args, dict) or args.get("confirm") is not True:
                raise ValueError(u"Confirma el reinicio del historial en el panel.")
            self._sync_finance(skip_daily_reset=True)
            account_id = self._account_id()
            if not account_id:
                raise ValueError(u"Espera que se sincronice tu cuenta antes de reiniciar el historial.")
            server_clock = self._read_server_clock()
            now = server_clock["server_now_utc"] if server_clock else _now_utc()
            self._reset_history(account_id, self._read_balance(), now,
                                server_clock=server_clock, clear_goal=True)
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudo reiniciar el historial. Los datos anteriores se conservan."
            self._error("history_reset_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def save_goal(self, args):
        try:
            if not isinstance(args, dict) or not self._account_id():
                raise ValueError(u"Espera que se sincronice tu cuenta antes de guardar la meta.")
            if get_history_state(self.config, self.realm, self._account_id())["mode"] == "server":
                self._sync_finance()
            server_clock = self._read_server_clock()
            now = server_clock["server_now_utc"] if server_clock else _now_utc()
            updated = parse_goal_command(args.get("value"), args.get("mode"), self.config, now,
                                         self._read_balance(), self.realm, self._account_id())
            updated = sync_goal_completion(updated, self.realm, self._account_id(),
                                           self._read_balance()) or updated
            atomic_json(self.config_path, updated)
            self.config = updated
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudo guardar la meta. Revisa el archivo game.log."
            self._error("goal_save_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def reset_goal(self, args):
        """Start only this account's goal anew; never reset its battle period."""
        try:
            account_id = self._account_id()
            if not isinstance(args, dict) or not account_id:
                raise ValueError(u"Espera que se sincronice tu cuenta antes de reiniciar la meta.")
            if get_history_state(self.config, self.realm, account_id)["mode"] == "server":
                self._sync_finance()
            server_clock = self._read_server_clock()
            now = server_clock["server_now_utc"] if server_clock else _now_utc()
            updated = parse_reset_goal_command(args.get("value"), args.get("mode"),
                         self.config, now, self._read_balance(), self.realm, account_id)
            updated = sync_goal_completion(updated, self.realm, account_id,
                                           self._read_balance()) or updated
            atomic_json(self.config_path, updated)
            self.config = updated
            self.panel_error = None
        except ValueError as error:
            self.panel_error = str(error) if sys.version_info[0] >= 3 else unicode(error)
        except Exception:
            self.panel_error = u"No se pudo reiniciar la meta. Tu meta anterior se conserva."
            self._error("goal_reset_failed")
        if self.panel is not None:
            self.panel.refresh(force=True)

    def _result_notice(self, record):
        try:
            self._sync_finance()
        except Exception:
            self._error("history_notice_sync_failed")
        state = get_history_state(self.config, record["region"], record["account_id"])
        if not record_visible(record, state):
            return
        total = history_ledger(self.ledger, record["region"], record["account_id"], self.config).summary(
            record["region"], record["account_id"])
        expense = record["credits"]["expenses"]
        net = record["credits"]["gross"] - sum(expense.values())
        sign = u"+" if net >= 0 else u""
        selected = language(self.config)
        text = translate(u"Contabilidad | Neto: %s%s cr. | Reparaciones: %s | "
                u"Munici\u00f3n: %s | Consumibles/directivas: %s | Historial: %s cr.", selected) % (
                sign, credits_text(net, selected), credits_text(expense["repair"], selected),
                credits_text(expense["ammo"], selected), credits_text(expense["consumables"], selected),
                credits_text(total["net_credits"], selected))
        try:
            balance = self._read_balance()
            status = balance_goal(self.config, self.realm, record["account_id"], balance)
            if not status["active"]:
                text += translate(u" | Sin meta activa.", selected)
            elif status["current"] is not None:
                path = os.path.join(self.directory, "goals", record["region"],
                                    record["account_id"] + ".json")
                atomic_json(path, status)
                if status["complete"]:
                    text += translate(u" | Meta alcanzada.", selected)
                else:
                    text += translate(u" | Meta %s: faltan %s cr.", selected) % (
                        credits_text(status["target"], selected), credits_text(status["remaining"], selected))
            else:
                text += translate(u" | Meta: saldo pendiente de sincronizar.", selected)
        except Exception:
            print(PREFIX + " goal could not be evaluated")
            traceback.print_exc()
        self._notify(text)

    def _resolve_quest_name(self, quest_id):
        if quest_id in self._quest_names:
            return self._quest_names[quest_id]
        # Crucible awards are carried by the battleResults detailedRewards map.
        # Its Gameface popups are another presentation of that same award.
        try:
            from challenges_common import isChallengeQuest
            if isChallengeQuest(quest_id):
                from helpers import dependency
                from gui.impl.lobby.challenges.views_helpers import parseChallengeQuestId
                from skeletons.gui.challenges import IChallengesController
                challenge_id, mission = parseChallengeQuestId(quest_id)
                challenge = dependency.instance(IChallengesController).getChallenge(challenge_id)
                if challenge is not None:
                    name = u"Crisol: %s | Misi\u00f3n %s" % (safe_text(challenge.name), mission)
                    self._quest_names[quest_id] = name
                    return name
        except Exception:
            pass
        try:
            from helpers import dependency
            from skeletons.gui.server_events import IEventsCache
            cache = dependency.instance(IEventsCache)
            quest = cache.getQuestByID(quest_id)
            if quest is None:
                quest = cache.getAllQuests(includePersonalMissions=True).get(quest_id)
            if quest is None:
                quest = cache.getHiddenQuests().get(quest_id)
            if quest is not None:
                name = safe_text(quest.getUserName())
                if name:
                    self._quest_names[quest_id] = name
                return name
        except Exception:
            pass
        return ""

    def _on_sys_message(self, client_id, message):
        if not self._alive or self.replay.isPlaying():
            return
        try:
            kind = self._message_types.get(getattr(message, "type", None))
            invoice = None
            if kind == "invoiceReceived":
                from constants import INVOICE_ASSET
                data = message.data if isinstance(message.data, dict) else {}
                asset = data.get("assetType")
                if asset == INVOICE_ASSET.CREDITS:
                    invoice = data.get("amount")
                elif asset == INVOICE_ASSET.DATA and isinstance(data.get("data"), dict):
                    invoice = data["data"].get("credits")
            now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            receipt = reward_receipt(message, kind, now, self._resolve_quest_name, invoice)
            if receipt is not None:
                self.accept_receipt(receipt)
        except Exception:
            self._error("reward_receipt_failed")

    def accept_receipt(self, receipt):
        account_id = self._account_id() or self._battle_account_id
        if account_id:
            next_wallet = WalletBook(self.wallet.data)
            if next_wallet.upsert_receipt(self.realm, account_id, receipt):
                atomic_json(self.wallet_path, next_wallet.data)
                self.wallet = next_wallet
        else:
            self._receipt_queue.append(receipt)
            self._receipt_queue = self._receipt_queue[-100:]
        self._on_client_updated()

    def save_panel_view_mode(self, mode):
        import copy
        if mode not in ("widget", "details", "minimized"):
            raise ValueError("unknown credit ledger view mode")
        if self.config.get("panel_view_mode") != mode:
            updated = copy.deepcopy(self.config)
            updated["panel_view_mode"] = mode
            atomic_json(self.config_path, updated)
            self.config = updated

    def save_panel_position(self, x, y, view_mode=None):
        import copy
        if view_mode is not None and view_mode not in ("widget", "details", "minimized"):
            raise ValueError("unknown credit ledger view mode")
        position = {"x": int(x), "y": int(y)}
        updated = copy.deepcopy(self.config)
        if view_mode is None:
            updated["panel_position"] = position
        else:
            if not isinstance(updated.get("panel_positions"), dict):
                updated["panel_positions"] = {}
            updated["panel_positions"][view_mode] = position
            if view_mode == "details":
                updated["panel_position"] = position
        if self.config != updated:
            atomic_json(self.config_path, updated)
            self.config = updated

    def _on_client_updated(self, *args):
        if not self._alive or self._wallet_callback is not None:
            return
        self._wallet_callback = self.world.callback(1.0, self._wallet_changed)

    def _wallet_changed(self):
        self._wallet_callback = None
        try:
            self._ensure_garage_widget()
            self._sync_finance()
            if self.panel is not None:
                self.panel.refresh()
        except Exception:
            self._error("wallet_sync_failed")

    def _sync_finance(self, skip_daily_reset=False):
        if not self._alive or self.replay.isPlaying():
            return
        account_id = self._account_id()
        balance = self._read_balance() if account_id else None
        if not account_id or balance is None:
            return
        server_clock = self._read_server_clock()
        now = server_clock["server_now_utc"] if server_clock else _now_utc()
        next_wallet = WalletBook(self.wallet.data)
        changed = next_wallet.observe(self.realm, account_id, balance, now)
        for receipt in self._receipt_queue:
            changed = next_wallet.upsert_receipt(self.realm, account_id, receipt) or changed
        # Resolve delayed quest-cache synchronization without changing amounts.
        recent_receipts = sorted(next_wallet.receipts(self.realm, account_id),
                                 key=lambda row: row["occurred_at"], reverse=True)[:100]
        for receipt in recent_receipts:
            resolved = False
            for part in receipt.get("parts", []):
                if not part.get("name_resolved"):
                    name = self._resolve_quest_name(part["quest_id"])
                    if name:
                        part["title"], part["name_resolved"] = name, True
                        resolved = True
            if resolved:
                changed = next_wallet.upsert_receipt(self.realm, account_id, receipt) or changed
        if changed:
            atomic_json(self.wallet_path, next_wallet.data)
            self.wallet = next_wallet
        self._receipt_queue = []
        updated = ensure_balance_goal(self.config, self.realm, account_id, balance, now)
        if updated is not None:
            atomic_json(self.config_path, updated)
            self.config = updated
        updated = ensure_mandatory_server_history(self.config, self.realm, account_id, now, server_clock)
        if updated is not None:
            atomic_json(self.config_path, updated)
            self.config = updated
        if not skip_daily_reset and server_reset_due(self.config, self.realm, account_id, now, server_clock):
            self._reset_history(account_id, balance, now, automatic=True, server_clock=server_clock)
            print(PREFIX + " server game-day history restarted; default credit goal started")
        try:
            updated = sync_goal_completion(self.config, self.realm, account_id, balance)
            if updated is not None:
                prior_event = goal_completion_payload(self.config, self.realm, account_id, balance)
                atomic_json(self.config_path, updated)
                self.config = updated
                if goal_completion_payload(updated, self.realm, account_id, balance) != prior_event:
                    if goal_completion_payload(updated, self.realm, account_id, balance) is not None:
                        print(PREFIX + " goal completion queued until visible in garage")
        except Exception:
            # Presentation bookkeeping must not interrupt financial capture.
            self._error("goal_completion_save_failed")

    def _read_server_clock(self):
        try:
            account_id = self._account_id()
            if not account_id or account_id != getattr(self, "_server_clock_account_id", None):
                return None
            return native_server_clock(self.world.player())
        except Exception:
            # An optional calendar read must never stop battle/balance capture.
            return None

    def _read_balance(self):
        try:
            from helpers import dependency
            from skeletons.gui.shared import IItemsCache
            stats = dependency.instance(IItemsCache).items.stats
            if not stats.isSynced():
                return None
            value = stats.credits
            try:
                integers = (int, long)
            except NameError:
                integers = (int,)
            if isinstance(value, integers) and not isinstance(value, bool) and value >= 0:
                return value
        except Exception:
            pass
        return None

    def _schedule_tick(self):
        if self._alive:
            self._tick_id = self.world.callback(10.0, self._tick)

    def _restore_captures(self, account_id):
        known = set(row["battle_id"] for row in self.ledger.list_results(self.realm, account_id,
                                                                       include_pending=False))
        for snapshot in self.store.recovery_candidates(self.realm, account_id):
            battle_id = snapshot.get("battle_id")
            if battle_id in known:
                continue
            if snapshot.get("reconciliation", {}).get("status") == "native_calculated":
                try:
                    record = normalize_snapshot(snapshot)
                    next_ledger = type(self.ledger).from_dict(self.ledger.to_dict())
                    next_ledger.upsert_result(record)
                    next_ledger.save(self.ledger_path)
                    self.ledger = next_ledger
                    known.add(battle_id)
                    continue
                except Exception:
                    print(PREFIX + " saved capture requires a fresh native calculation")
            try:
                self._pending[(str(account_id), int(battle_id))] = time.time()
            except (ValueError, TypeError):
                continue
        self._restored_accounts.add(str(account_id))

    def _tick(self):
        self._tick_id = None
        if not self._alive:
            return
        try:
            self._ensure_garage_widget()
            self._sync_finance()
            if self.panel is not None:
                self.panel.refresh()
            if self.replay.isPlaying() or self._in_flight:
                return
            player = self.world.player()
            account_id = getattr(player, "databaseID", None)
            cache = getattr(player, "battleResultsCache", None)
            if not account_id or cache is None:
                return
            if str(account_id) not in self._restored_accounts:
                self._restore_captures(str(account_id))
            candidates = []
            for identity, created in list(self._pending.items()):
                if time.time() - created > 3600:
                    self._pending.pop(identity, None)
                elif identity[0] == str(account_id):
                    candidates.append(identity)
            if not candidates:
                return
            identity = sorted(candidates, key=lambda item: self._pending[item])[0]
            self._in_flight = True
            def received(code, result):
                self._in_flight = False
                if self._alive and code in (1, 2) and isinstance(result, dict):
                    self._capture(result, "cache", identity[0])
            try:
                cache.get(identity[1], received)
            except Exception:
                self._in_flight = False
                raise
        except Exception:
            self._error("cache_retry_failed")
        finally:
            self._schedule_tick()

    def close(self):
        self._invalidate_completion_display()
        self._unbind_garage_route()
        self._alive = False
        self._garage_visible = False
        self._garage_recovery_allowed = False
        self._gui_account_id = None
        if self._coupon_observer is not None:
            self._coupon_observer.close()
            self._coupon_observer = None
        if self.panel is not None:
            try:
                self.panel.close()
            except Exception:
                traceback.print_exc()
            self.panel = None
        for event, callback in self._hooks:
            try:
                event -= callback
            except Exception:
                pass
        self._hooks = []
        for callback_id in list(self._notice_ids) + [self._tick_id, self._wallet_callback]:
            if callback_id is not None:
                try:
                    self.world.cancelCallback(callback_id)
                except Exception:
                    pass
        self._notice_ids.clear()
        self._tick_id = None
        try:
            self._status("stopped")
        except Exception:
            traceback.print_exc()


_collector = None


def init():
    global _collector
    if _collector is None:
        try:
            _collector = Collector()
        except Exception:
            print(PREFIX + " initialization failed; other mods are unaffected")
            traceback.print_exc()


def fini():
    global _collector
    if _collector is not None:
        _collector.close()
        _collector = None
