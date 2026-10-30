"""Completion persistence through native balance sync, saves and view ACKs."""
import copy
import sys
import types
import unittest
from unittest.mock import patch

import test_capture_runtime as harness
from capture import runtime
from capture.completion import NAMESPACE
from capture.storage import read_json

BASE = 22000000
NOW = "2026-10-19T18:00:00Z"


class GoalCompletionRuntimeTests(unittest.TestCase):
    tearDown = harness.RuntimeTests.tearDown

    def setUp(self):
        harness.RuntimeTests.setUp(self)
        self.clock = patch.object(runtime, "_now_utc", return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.balance = BASE
        self.collector._garage_visible = True
        self.collector._server_clock_account_id = "101"
        self.display_stage = True
        self.display_lobby = True
        self.display_panel = True
        self.collector.panel.model = object()
        self.collector.panel._mode = "widget"
        self.collector.panel.completion_surface_ready = lambda: self.display_panel
        self.stage_patch = patch.object(self.collector, "_read_completion_stage",
                                        side_effect=lambda: self.display_stage)
        self.lobby_patch = patch.object(self.collector, "_native_lobby_state",
                                        side_effect=lambda: self.display_lobby)
        self.stage_patch.start()
        self.lobby_patch.start()
        self.addCleanup(self.stage_patch.stop)
        self.addCleanup(self.lobby_patch.stop)

    def ack(self, event):
        args = dict(event, presentation_generation=self.collector._completion_display()["generation"])
        self.collector.acknowledge_goal_completion(args)

    def test_other_lobby_page_keeps_completion_pending_even_before_route_event(self):
        pending = self.complete()
        generation = self.collector._completion_display()["generation"]
        self.lobby_machine.visibleState = types.SimpleNamespace(hangar=False)
        self.assertFalse(self.collector._completion_display()["ready"])
        self.collector.acknowledge_goal_completion(dict(pending, presentation_generation=generation))
        self.assertIsNotNone(self.collector.panel_payload()["goal_completion"])
        self.lobby_machine.visibleState = self.garage_state
        self.assertTrue(self.collector._completion_display()["ready"])
        self.ack(pending)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def start(self, target=1000000):
        self.collector._sync_finance()
        self.collector.save_goal({"value": str(target), "mode": "balance_growth"})
        self.assertIsNone(self.collector.panel_error)

    def complete(self):
        self.start()
        self.balance += 1000000
        pending = self.collector.panel_payload()["goal_completion"]
        self.assertIsNotNone(pending)
        return pending

    def test_goal_save_arms_then_balance_update_emits_and_persists_one_event(self):
        pending = self.complete()
        snapshot = copy.deepcopy(self.collector.config)
        self.assertEqual(read_json(self.collector.config_path), snapshot)
        self.collector.set_language({"language": "en", "request_id": "1"})
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.collector._sync_finance()
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.assertEqual(self.collector.config[NAMESPACE], snapshot[NAMESPACE])

    def test_ack_durably_clears_only_bookkeeping_and_preserves_other_feedback(self):
        pending = self.complete()
        config = copy.deepcopy(self.collector.config)
        ledger = self.collector.ledger.to_dict()
        wallet = copy.deepcopy(self.collector.wallet.data)
        self.collector.panel_error = "Keep unrelated goal error"
        self.ack(pending)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.assertEqual(self.collector.panel_error, "Keep unrelated goal error")
        after = self.collector.config
        self.assertEqual({k: v for k, v in after.items() if k != NAMESPACE},
                         {k: v for k, v in config.items() if k != NAMESPACE})
        self.assertEqual(self.collector.ledger.to_dict(), ledger)
        self.assertEqual(self.collector.wallet.data, wallet)
        self.assertEqual(read_json(self.collector.config_path), after)
        # A new collector session reads the durable suppression marker.
        self.collector.config = read_json(self.collector.config_path)
        self.ack(pending)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def test_existing_success_migrates_without_retroactive_event(self):
        self.start()
        self.collector.config.pop(NAMESPACE)
        self.balance += 1000000
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.assertIn(NAMESPACE, read_json(self.collector.config_path))

    def test_failed_ack_rolls_back_and_can_retry_without_global_error_changes(self):
        pending = self.complete()
        snapshot = copy.deepcopy(self.collector.config)
        self.collector.panel_error = "Unrelated validation error"
        with patch.object(runtime, "atomic_json", side_effect=OSError("synthetic ACK failure")):
            self.ack(pending)
        self.assertEqual(self.collector.config, snapshot)
        self.assertEqual(read_json(self.collector.config_path), snapshot)
        self.assertEqual(self.collector.panel_error, "Unrelated validation error")
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.ack(pending)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def test_failed_event_commit_does_not_publish_uncommitted_event_and_recovers(self):
        self.start()
        snapshot = copy.deepcopy(self.collector.config)
        self.balance += 1000000
        original_atomic = runtime.atomic_json
        def fail_config(path, value):
            if path == self.collector.config_path:
                raise OSError("synthetic completion failure")
            return original_atomic(path, value)
        with patch.object(runtime, "atomic_json", side_effect=fail_config):
            self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.assertEqual(self.collector.config, snapshot)
        self.assertEqual(read_json(self.collector.config_path), snapshot)
        self.assertIsNotNone(self.collector.panel_payload()["goal_completion"])

    def test_disable_history_reset_and_explicit_goal_reset_invalidate_old_acks(self):
        old = self.complete()
        self.collector.save_goal({"value": "0", "mode": "balance_growth"})
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.ack(old)
        self.collector.save_goal({"value": "1000000", "mode": "balance_growth"})
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.collector.reset_goal({"value": "1000000", "mode": "balance_growth"})
        self.balance += 1000000
        new = self.collector.panel_payload()["goal_completion"]
        self.assertNotEqual(new["id"], old["id"])
        self.ack(old)
        self.assertEqual(self.collector.panel_payload()["goal_completion"], new)
        self.collector.reset_history({"confirm": True})
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        fresh_goal = self.collector.panel_payload()["goal"]
        self.assertEqual(fresh_goal["target"], 100000)
        self.assertEqual(fresh_goal["baseline"], self.balance)
        self.assertEqual(fresh_goal["current"], 0)
        self.assertFalse(fresh_goal["complete"])

    def test_unsynced_balance_replay_and_foreign_account_never_expose_or_ack_event(self):
        pending = self.complete()
        completed_balance = self.balance
        self.balance = None
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.ack(pending)
        self.balance = completed_balance
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.replay.isPlaying = lambda: True
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.ack(pending)
        self.replay.isPlaying = lambda: False
        self.account.databaseID = 102
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])
        self.ack(pending)
        self.account.databaseID = 101
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)

    def test_new_goal_and_tracker_arm_in_one_atomic_commit(self):
        self.collector._sync_finance()
        previous = copy.deepcopy(self.collector.config)
        with patch.object(runtime, "atomic_json", side_effect=OSError("synthetic goal save failure")):
            self.collector.save_goal({"value": "1000000", "mode": "balance_growth"})
        self.assertEqual(self.collector.config, previous)
        self.assertEqual(read_json(self.collector.config_path), previous)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def test_completion_during_loading_waits_for_owned_native_garage_and_rejects_early_ack(self):
        self.display_stage = False
        pending = self.complete()
        blocked = self.collector.panel_payload()["completion_display"]
        self.assertFalse(blocked["ready"])
        self.collector.acknowledge_goal_completion(dict(pending,
            presentation_generation=blocked["generation"]))
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.display_stage = True
        ready = self.collector.panel_payload()["completion_display"]
        self.assertTrue(ready["ready"])
        self.assertGreater(ready["generation"], blocked["generation"])
        self.collector.acknowledge_goal_completion(dict(pending,
            presentation_generation=blocked["generation"]))
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.ack(pending)
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def test_balance_and_account_entity_do_not_replace_own_show_gui_or_native_readiness(self):
        self.complete()
        self.collector._server_clock_account_id = None
        self.assertFalse(self.collector.panel_payload()["completion_display"]["ready"])
        self.collector._server_clock_account_id = "102"
        self.assertFalse(self.collector.panel_payload()["completion_display"]["ready"])
        self.collector._server_clock_account_id = "101"
        self.collector._garage_visible = False
        self.assertFalse(self.collector.panel_payload()["completion_display"]["ready"])
        self.collector._garage_visible = True
        for lobby in (False, None):
            self.display_lobby = lobby
            self.assertFalse(self.collector.panel_payload()["completion_display"]["ready"])
        self.display_lobby = True
        self.assertTrue(self.collector.panel_payload()["completion_display"]["ready"])

    def test_hidden_surface_or_reentry_invalidates_old_visible_generation_without_losing_event(self):
        pending = self.complete()
        original = self.collector.panel_payload()["completion_display"]
        self.display_panel = False
        with patch.object(self.collector.panel, "refresh") as refreshed:
            self.collector.acknowledge_goal_completion(dict(pending,
                presentation_generation=original["generation"]))
            refreshed.assert_called_once_with(force=True)
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.display_panel = True
        returned = self.collector.panel_payload()["completion_display"]
        self.assertGreater(returned["generation"], original["generation"])
        self.collector.acknowledge_goal_completion(dict(pending,
            presentation_generation=original["generation"]))
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.collector._invalidate_completion_display()
        self.collector.acknowledge_goal_completion(dict(pending,
            presentation_generation=returned["generation"]))
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)

    def test_native_generation_argument_accepts_canonical_wulf_strings_and_rejects_unsafe_values(self):
        pending = self.complete()
        generation = self.collector.panel_payload()["completion_display"]["generation"]
        for invalid in (None, True, "01", " " + str(generation), generation + 0.5):
            self.collector.acknowledge_goal_completion(dict(pending,
                presentation_generation=invalid))
            self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.collector.acknowledge_goal_completion(dict(pending,
            presentation_generation=str(generation)))
        self.assertIsNone(self.collector.panel_payload()["goal_completion"])

    def test_native_hangar_and_waiting_contract_fails_closed_until_all_loaded(self):
        interface = object()
        space = types.SimpleNamespace(spaceInited=True, isModelLoaded=True)
        waiting = {"shown": False}
        helpers = types.ModuleType("helpers")
        helpers.dependency = types.SimpleNamespace(instance=lambda contract: space if contract is interface else None)
        shared = types.ModuleType("skeletons.gui.shared.utils")
        shared.IHangarSpace = interface
        scaleform = types.ModuleType("gui.Scaleform.Waiting")
        scaleform.Waiting = types.SimpleNamespace(isVisible=lambda: waiting["shown"])
        with patch.dict(sys.modules, {"helpers": helpers,
              "skeletons.gui.shared.utils": shared, "gui.Scaleform.Waiting": scaleform}):
            self.assertTrue(runtime.Collector._read_completion_stage(self.collector))
            waiting["shown"] = True
            self.assertFalse(runtime.Collector._read_completion_stage(self.collector))
            waiting["shown"] = None
            self.assertFalse(runtime.Collector._read_completion_stage(self.collector))
            waiting["shown"] = False
            space.spaceInited = False
            self.assertFalse(runtime.Collector._read_completion_stage(self.collector))
            space.spaceInited = True
            space.isModelLoaded = lambda: False
            self.assertFalse(runtime.Collector._read_completion_stage(self.collector))
            space.isModelLoaded = lambda: True
            self.assertTrue(runtime.Collector._read_completion_stage(self.collector))
            del space.spaceInited
            self.assertFalse(runtime.Collector._read_completion_stage(self.collector))

    def test_pending_presence_poll_is_bounded_and_cancels_for_minimized_or_closed_view(self):
        pending = self.complete()
        self.collector.panel.refresh = lambda **kwargs: self.collector.panel_payload()
        count = 0
        while self.collector._completion_presence_callback is not None and count < 45:
            token = self.collector._completion_presence_callback
            self.callbacks.pop(token)()
            count += 1
        self.assertEqual(count, 40)
        self.assertIsNone(self.collector._completion_presence_callback)
        self.assertEqual(self.collector.panel_payload()["goal_completion"], pending)
        self.assertIsNone(self.collector._completion_presence_callback)
        self.collector.panel._mode = "minimized"
        self.display_panel = False
        self.collector.panel_payload()
        self.assertIsNone(self.collector._completion_presence_callback)
        self.collector.panel._mode = "widget"
        self.display_panel = True
        self.collector.panel_payload()
        token = self.collector._completion_presence_callback
        self.assertIsNotNone(token)
        self.collector.close()
        self.assertNotIn(token, self.callbacks)

