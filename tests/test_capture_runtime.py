import copy
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import core.ledger
from capture import runtime
from capture.native import derive_credits
from capture.storage import read_json
from capture.snapshot import make_snapshot
from test_native_finance import Reusable
from test_snapshot import fixture


class Event(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, callback):
        self.handlers.append(callback)
        return self

    def __isub__(self, callback):
        self.handlers.remove(callback)
        return self

    def emit(self, *args):
        for callback in list(self.handlers):
            callback(*args)


class CommonBattleQueueState(object):
    hangar = False


class StrongholdsBattleQueueState(object):
    hangar = False


class HalloweenPreBattleQueueState(object):
    hangar = False


class LastStandPreBattleQueueState(object):
    hangar = False


class MapsTrainingQueueState(object):
    hangar = False


class BattleRoyaleTournamentQueueState(object):
    hangar = False


CommonQueueState = CommonBattleQueueState
StrongholdsQueueState = StrongholdsBattleQueueState
QUEUE_STATE_TYPES = (
    ("gui.Scaleform.daapi.view.lobby.battle_queue.states", CommonQueueState),
    ("gui.Scaleform.daapi.view.lobby.battle_queue.states", StrongholdsQueueState),
    ("halloween.gui.impl.lobby.states", HalloweenPreBattleQueueState),
    ("last_stand.gui.impl.lobby.states", LastStandPreBattleQueueState),
    ("gui.impl.lobby.maps_training.states", MapsTrainingQueueState),
    ("battle_royale.gui.impl.lobby.views.states", BattleRoyaleTournamentQueueState),
)
for queue_module_name, queue_class in QUEUE_STATE_TYPES:
    queue_class.__module__ = queue_module_name


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="credit-ledger-runtime-")
        with open(os.path.join(self.directory, "version.xml"), "w") as version_file:
            version_file.write("<version.xml><version>v.2.4.1.1 #984</version></version.xml>")
        self.callbacks = {}
        self.world = types.ModuleType("BigWorld")
        def callback(delay, function):
            token = len(self.callbacks) + 1
            self.callbacks[token] = function
            return token
        self.world.callback = callback
        self.world.cancelCallback = lambda token: self.callbacks.pop(token, None)
        self.account = types.SimpleNamespace(databaseID=101, battleResultsCache=None)
        self.world.player = lambda: self.account
        self.replay = types.ModuleType("BattleReplay")
        self.replay.isPlaying = lambda: False
        constants = types.ModuleType("constants")
        constants.CURRENT_REALM = "NA"
        constants.INVOICE_ASSET = types.SimpleNamespace(CREDITS=1, DATA=2)
        chat_shared = types.ModuleType("chat_shared")
        chat_shared.SYS_MESSAGE_TYPE = types.SimpleNamespace(tokenQuests=types.SimpleNamespace(index=lambda: 1),
              battleResults=types.SimpleNamespace(index=lambda: 2), invoiceReceived=types.SimpleNamespace(index=lambda: 3))
        self.service_events = Event()
        messenger = types.ModuleType("messenger.proto.events")
        messenger.g_messengerEvents = types.SimpleNamespace(serviceChannel=types.SimpleNamespace(onChatMessageReceived=self.service_events))
        player_events = types.ModuleType("PlayerEvents")
        self.events = types.SimpleNamespace(onBattleResultsReceived=Event(),
                                           onAvatarBecomePlayer=Event(),
                                           onAccountShowGUI=Event(),
                                           onAccountBecomeNonPlayer=Event(),
                                           onClientUpdated=Event(),
                                           onAccountBecomePlayer=Event())
        player_events.g_playerEvents = self.events
        self.garage_state = types.SimpleNamespace(hangar=True)
        self.lobby_machine = types.SimpleNamespace(visibleState=self.garage_state,
                                                   onVisibleRouteChanged=Event())
        lobby_entry = types.ModuleType("gui.Scaleform.lobby_entry")
        lobby_entry.getLobbyStateMachine = lambda: self.lobby_machine
        lobby_states = types.ModuleType("gui.lobby_state_machine.states")
        lobby_states.isHangarState = lambda state: getattr(state, "hangar", False) is True
        queue_modules = {}
        for module_name, queue_class in QUEUE_STATE_TYPES:
            module = queue_modules.setdefault(module_name, types.ModuleType(module_name))
            setattr(module, queue_class.__name__, queue_class)
        mocked_modules = {"BigWorld": self.world,
                          "BattleReplay": self.replay, "constants": constants,
                          "chat_shared": chat_shared, "messenger.proto.events": messenger,
                          "PlayerEvents": player_events, "capture.ledger": core.ledger,
                          "gui.Scaleform.lobby_entry": lobby_entry,
                          "gui.lobby_state_machine.states": lobby_states}
        mocked_modules.update(queue_modules)
        self.modules = patch.dict(sys.modules, mocked_modules)
        self.modules.start()
        self.root_patch = patch.object(runtime, "_game_directory", return_value=self.directory)
        self.root_patch.start()
        self.derive_patch = patch.object(runtime, "derive_credits",
                            side_effect=lambda result: derive_credits(result, lambda _: Reusable()))
        self.derive_patch.start()
        self.panel_patch = patch("capture.panel.LedgerPanel", return_value=types.SimpleNamespace(
            close=lambda: None, close_window=lambda: None, refresh=lambda **kwargs: None,
            ensure_visible=lambda **kwargs: None))
        self.panel_patch.start()
        self.coupon_patch = patch("capture.coupons.CouponObserver", return_value=types.SimpleNamespace(close=lambda:None))
        self.coupon_patch.start()
        self.collector = runtime.Collector()
        self.balance = None
        self.balance_patch = patch.object(self.collector, "_read_balance", side_effect=lambda: self.balance)
        self.balance_patch.start()

    def tearDown(self):
        self.collector.close()
        self.balance_patch.stop()
        self.coupon_patch.stop()
        self.panel_patch.stop()
        self.derive_patch.stop()
        self.root_patch.stop()
        self.modules.stop()
        shutil.rmtree(self.directory)

    def test_actual_event_wiring_records_once_and_fini_unsubscribes(self):
        self.events.onBattleResultsReceived.emit(True, fixture())
        self.events.onBattleResultsReceived.emit(True, fixture())
        summary = self.collector.ledger.summary("NA", "101")
        self.assertEqual(summary["battle_count"], 1)
        self.assertEqual(summary["net_credits"], 51500)
        self.assertEqual(self.collector.captures_this_run, 1)
        self.assertTrue(os.path.isfile(self.collector.ledger_path))
        self.collector.close()
        self.assertEqual(self.events.onBattleResultsReceived.handlers, [])

    def test_replays_and_other_player_events_do_not_record(self):
        self.events.onBattleResultsReceived.emit(False, fixture())
        self.replay.isPlaying = lambda: True
        self.events.onBattleResultsReceived.emit(True, fixture())
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 0)

    def test_missing_native_replay_is_retained_without_invented_zero(self):
        raw = fixture()
        del raw["personal"][321]["creditsReplay"]
        self.events.onBattleResultsReceived.emit(True, raw)
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 0)
        capture = read_json(os.path.join(self.collector.directory, self.collector.last_capture))
        self.assertEqual(capture["reconciliation"]["status"], "unverified")

    def test_cache_synchronous_callback_is_account_scoped_and_idempotent(self):
        class Cache(object):
            def get(self, arena_id, callback):
                callback(2, fixture())
        self.account.battleResultsCache = Cache()
        self.collector._pending[("101", fixture()["arenaUniqueID"])] = runtime.time.time()
        self.collector._pending[("999", 55)] = runtime.time.time()
        self.collector._tick()
        self.assertFalse(self.collector._in_flight)
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 1)
        self.assertIn(("999", 55), self.collector._pending)

    def test_failed_ledger_commit_can_retry_identical_saved_capture(self):
        original = core.ledger.EconomyLedger.save
        with patch.object(core.ledger.EconomyLedger, "save", side_effect=OSError("synthetic write failure")):
            self.events.onBattleResultsReceived.emit(True, fixture())
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 0)
        self.events.onBattleResultsReceived.emit(True, fixture())
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 1)
        self.assertIsNone(read_json(os.path.join(self.collector.directory, "status.json"))["last_error"])

    def test_unverified_saved_battle_is_retried_on_next_session_same_account(self):
        self.collector.store.save(make_snapshot(fixture(), "NA"))
        class Cache(object):
            def get(self, arena_id, callback):
                callback(2, fixture())
        self.account.battleResultsCache = Cache()
        self.collector._tick()
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 1)
        self.assertEqual(self.collector.ledger.summary("NA", "101")["net_credits"], 51500)

    def test_saved_native_capture_recovers_without_network_request(self):
        snapshot = make_snapshot(fixture(), "NA")
        snapshot["native_credits"] = derive_credits(fixture(), lambda _: Reusable())
        snapshot["reconciliation"] = {"status": "native_calculated"}
        self.collector.store.save(snapshot)
        self.collector._restore_captures("101")
        self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 1)
        self.assertEqual(self.collector._pending, {})

    def test_goal_save_commits_before_replacing_configuration(self):
        self.balance = 22000000
        self.collector.save_goal({"value": "4000000", "mode": "balance_growth"})
        self.assertEqual(read_json(self.collector.config_path)["credit_target"], 4000000)
        with patch.object(runtime, "atomic_json", side_effect=OSError("synthetic failure")):
            self.collector.save_goal({"value": "9000000", "mode": "balance_growth"})
        self.assertEqual(self.collector.config["credit_target"], 4000000)
        self.assertIsNotNone(self.collector.panel_error)

    def test_native_receipts_and_balance_updates_reconcile_without_duplicate_credit(self):
        self.balance = 22000000
        self.collector._sync_finance()
        self.collector.save_goal({"value":"3000000", "mode":"balance_growth"})
        message = types.SimpleNamespace(type=1, messageId=77, sentTime=runtime.time.time(), data={
            "detailedRewards": {"crucible_1": {"credits": 150000}}})
        with patch.object(self.collector, "_resolve_quest_name", return_value="Crisol: etapa 1"):
            self.service_events.emit(1, message)
            self.service_events.emit(2, message)
        self.balance = 22150000
        self.events.onClientUpdated.emit({"stats": {"credits": self.balance}}, False)
        self.collector._wallet_changed()
        payload = self.collector.panel_payload()
        self.assertEqual(payload["goal"]["current"], 150000)
        self.assertEqual(payload["wallet"]["external_credits"], 150000)
        self.assertEqual(payload["wallet"]["unclassified"], 0)
        self.assertEqual(payload["rewards"][0]["parts"][0]["title"], "Crisol: etapa 1")
        self.assertEqual(len(read_json(self.collector.wallet_path)["accounts"]["NA:101"]["receipts"]), 1)
        self.collector.close()
        self.assertEqual(self.service_events.handlers, [])

    def test_balance_is_saved_without_inventing_a_mission_source(self):
        self.balance = 22000000
        self.collector._sync_finance()
        self.balance += 50000
        payload = self.collector.panel_payload()
        self.assertEqual(payload["wallet"]["unclassified"], 50000)
        self.assertEqual(payload["rewards"], [])

    def test_zero_target_does_not_announce_a_completed_or_zero_remaining_goal(self):
        self.balance = 22000000
        self.collector._sync_finance()
        self.collector.save_goal({"value":"0", "mode":"balance_growth"})
        record = {"region":"NA", "account_id":"101", "credits":{"gross":50000,
            "expenses":{"repair":1000,"ammo":2000,"consumables":0,"other":0}}}
        with patch.object(self.collector, "_notify") as notify:
            self.collector._result_notice(record)
        self.assertIn("Sin meta activa.", notify.call_args[0][0])
        self.assertNotIn("faltan 0", notify.call_args[0][0])

    def test_first_wallet_sync_starts_default_goal_without_replacing_saved_goal(self):
        self.balance = 22000000
        self.collector._sync_finance()
        goal = self.collector.panel_payload()["goal"]
        self.assertEqual(goal["target"], 100000)
        self.assertEqual(goal["baseline"], self.balance)
        self.assertEqual(goal["current"], 0)
        self.collector.save_goal({"value":"0", "mode":"balance_growth"})
        self.balance += 50000
        self.collector._sync_finance()
        goal = self.collector.panel_payload()["goal"]
        self.assertEqual(goal["target"], 0)
        self.assertFalse(goal["active"])
        self.assertEqual(goal["baseline"], 22000000)

    def test_crucible_name_uses_native_challenge_chain_and_mission_index(self):
        def module(name, **attrs):
            value = types.ModuleType(name)
            value.__dict__.update(attrs)
            return value
        interface = object()
        native = {
            "challenges_common": module("challenges_common", isChallengeQuest=lambda q:q.startswith("challenge_")),
            "helpers": module("helpers", dependency=types.SimpleNamespace(instance=lambda _:types.SimpleNamespace(
                getChallenge=lambda identity:types.SimpleNamespace(name="Supernova")))),
            "skeletons.gui.challenges": module("skeletons.gui.challenges", IChallengesController=interface),
            "gui.impl.lobby.challenges.views_helpers": module("gui.impl.lobby.challenges.views_helpers", parseChallengeQuestId=lambda q:(42,3))}
        with patch.dict(sys.modules, native):
            self.assertEqual(self.collector._resolve_quest_name("challenge_42_3"), "Crisol: Supernova | Misión 3")

    def test_panel_account_fallback_is_cleared_entering_battle(self):
        self.events.onAccountShowGUI.emit({"databaseID": 101})
        del self.account.databaseID
        self.assertEqual(self.collector._account_id(), "101")
        self.events.onAvatarBecomePlayer.emit()
        self.assertIsNone(self.collector._account_id())

    def test_view_mode_and_each_position_persist_without_changing_the_goal(self):
        self.balance = 22000000
        self.collector._sync_finance()
        self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})
        before_goal = copy.deepcopy(self.collector.config["account_goals"])
        self.collector.save_panel_position(24, 96, "widget")
        self.collector.save_panel_view_mode("details")
        self.collector.save_panel_position(670, 230, "details")
        self.collector.save_panel_view_mode("widget")
        saved = read_json(self.collector.config_path)
        self.assertEqual(saved["panel_view_mode"], "widget")
        self.assertEqual(saved["panel_positions"], {
            "widget": {"x": 24, "y": 96}, "details": {"x": 670, "y": 230}})
        self.assertEqual(saved["account_goals"], before_goal)

    def test_invalid_or_failed_view_mode_save_keeps_previous_configuration(self):
        self.collector.save_panel_view_mode("widget")
        before = copy.deepcopy(self.collector.config)
        for mode in (None, False, "fullscreen", {}, 1):
            with self.assertRaises(ValueError):
                self.collector.save_panel_view_mode(mode)
            self.assertEqual(self.collector.config, before)
        with patch.object(runtime, "atomic_json", side_effect=OSError("synthetic write failure")):
            with self.assertRaises(OSError):
                self.collector.save_panel_view_mode("details")
        self.assertEqual(self.collector.config, before)
        self.assertEqual(read_json(self.collector.config_path), before)

    def test_widget_automatically_returns_to_garage_and_never_opens_during_battle(self):
        panel = self.collector.panel
        with patch.object(panel, "ensure_visible") as ensure, patch.object(panel, "close_window") as close:
            self.collector._tick()
            ensure.assert_not_called()
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.assertEqual(ensure.call_count, 1)
            self.collector._tick()
            self.assertEqual(ensure.call_count, 2)
            self.events.onAvatarBecomePlayer.emit()
            close.assert_called_once()
            self.collector._tick()
            self.assertEqual(ensure.call_count, 2)
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            self.assertEqual(ensure.call_count, 3)
            self.events.onAccountBecomeNonPlayer.emit()
            self.collector._tick()
            self.assertEqual(ensure.call_count, 3)

    def test_automatic_widget_respects_replays_and_failures_do_not_stop_accounting(self):
        panel = self.collector.panel
        with patch.object(panel, "ensure_visible") as ensure:
            self.replay.isPlaying = lambda: True
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            ensure.assert_not_called()
            self.replay.isPlaying = lambda: False
            self.events.onAccountShowGUI.emit({"databaseID": 101})
            ensure.side_effect = RuntimeError("synthetic parent window unavailable")
            with patch.object(self.collector, "_error") as error:
                self.collector._ensure_garage_widget()
            error.assert_called_once_with("garage_widget_unavailable")
            self.balance = 22000000
            self.collector._sync_finance()
            self.assertEqual(self.collector.panel_payload()["balance"], self.balance)

    def test_minimized_mode_and_position_persist_for_the_visible_launcher(self):
        self.collector.save_panel_position(1800, 96, "minimized")
        self.collector.save_panel_view_mode("minimized")
        saved = read_json(self.collector.config_path)
        self.assertEqual(saved["panel_view_mode"], "minimized")
        self.assertEqual(saved["panel_positions"]["minimized"], {"x": 1800, "y": 96})


if __name__ == "__main__":
    unittest.main()
