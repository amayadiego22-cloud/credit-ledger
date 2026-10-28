"""History periods through the collector, persistence and financial payload."""
import calendar
import copy
import unittest
from unittest.mock import patch

import test_capture_runtime as harness
from capture import runtime
from capture.history import get_history_state
from capture.storage import read_json
from timezone_fixtures import mock_local_timezone


NOW = "2026-10-18T15:30:00Z"
OLD = "2026-10-18T15:29:59Z"
BASE = 22000000


class HistoryRuntimeTests(unittest.TestCase):
    tearDown = harness.RuntimeTests.tearDown

    def setUp(self):
        timezone = mock_local_timezone("America/Bogota")
        timezone.__enter__()
        self.addCleanup(timezone.__exit__, None, None, None)
        harness.RuntimeTests.setUp(self)

    def clock(self, stamp=NOW):
        return patch.object(runtime, "_now_utc", return_value=stamp)

    def native_clock(self, stamp):
        from capture.server_clock import server_day_clock
        parsed = runtime.datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        clock = server_day_clock(calendar.timegm(parsed.timetuple()), 36000)
        return patch.object(self.collector, "_read_server_clock", return_value=clock)

    def raw_result(self, identity=9001, when=NOW, account_id=101):
        result = harness.fixture()
        result["arenaUniqueID"] = identity
        result["personal"]["avatar"]["accountDBID"] = account_id
        stamp = runtime.datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M:%SZ")
        result["common"] = {"arenaCreateTime": calendar.timegm(stamp.timetuple()) - 300,
                            "duration": 300}
        return result

    def capture(self, identity=9001, when=NOW):
        self.events.onBattleResultsReceived.emit(True, self.raw_result(identity, when))

    def receipt(self, identity="token:1", when=NOW, credits=25000):
        self.collector.accept_receipt({"id": identity, "kind": "tokenQuests",
            "occurred_at": when, "battle_id": None, "credits": credits,
            "included_in_battle": False, "title": "Misión de prueba", "parts": []})

    def synced_goal(self):
        self.balance = BASE
        self.collector._sync_finance()
        self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})

    def test_manual_reset_starts_zero_then_counts_new_battles_and_rewards_exactly(self):
        with self.clock():
            self.synced_goal()
            self.capture(9001, OLD)
            self.receipt("token:old", OLD)
            self.balance = BASE + 51500 + 25000
            before = self.collector.panel_payload()
            self.assertEqual(before["summary"]["net_credits"], 51500)
            self.collector.reset_history({"confirm": True})
            cleared = self.collector.panel_payload()
            self.assertEqual(cleared["summary"]["battle_count"], 0)
            self.assertEqual(cleared["summary"]["net_credits"], 0)
            self.assertEqual(cleared["history"], [])
            self.assertEqual(cleared["rewards"], [])
            self.assertEqual(cleared["wallet"]["change"], 0)
            self.assertEqual(cleared["wallet"]["battle_net"], 0)
            self.assertEqual(cleared["wallet"]["external_credits"], 0)
            self.assertEqual(cleared["wallet"]["unclassified"], 0)
            self.assertFalse(cleared["history_control"]["preserve_goal"])
            self.assertEqual(cleared["goal"]["current"], 0)
            self.assertEqual(cleared["goal"]["target"], 0)
            self.assertIsNone(cleared["goal"]["baseline"])
            self.assertFalse(cleared["goal"]["active"])
            # A fresh goal is a deliberate action after clearing the history.
            self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})
            self.assertEqual(self.collector.panel_payload()["goal"]["baseline"], self.balance)
            self.capture(9002, NOW)
            self.receipt("token:new", NOW)
            self.balance += 51500 + 25000
            payload = self.collector.panel_payload()
            self.assertEqual(payload["summary"]["battle_count"], 1)
            self.assertEqual(payload["summary"]["gross_credits"], 80500)
            self.assertEqual(payload["summary"]["net_credits"], 51500)
            self.assertEqual(payload["wallet"]["change"], 76500)
            self.assertEqual(payload["wallet"]["external_credits"], 25000)
            self.assertEqual(payload["wallet"]["battle_net"], 51500)
            self.assertEqual(payload["wallet"]["unclassified"], 0)
            self.assertEqual(payload["goal"]["current"], 76500)
            self.assertEqual([row["battle_id"] for row in payload["history"]], ["9002"])
            self.assertEqual([row["id"] for row in payload["rewards"]], ["token:new"])
            # The underlying financial evidence remains available for recovery.
            self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 2)
            self.assertEqual(len(self.collector.wallet.receipts("NA", "101")), 2)

    def test_same_second_old_ids_and_replayed_cache_do_not_reappear(self):
        with self.clock():
            self.synced_goal()
            self.capture(9001, NOW)
            self.receipt("token:old", NOW)
            self.balance += 76500
            self.collector.reset_history({"confirm": True})
            self.capture(9001, NOW)
            self.receipt("token:old", NOW)
            test = self

            class Cache(object):
                def get(self, identity, callback):
                    callback(2, test.raw_result(9001, NOW))

            self.account.battleResultsCache = Cache()
            self.collector._pending[("101", 9001)] = runtime.time.time()
            self.collector._tick()
            payload = self.collector.panel_payload()
            self.assertEqual(payload["history"], [])
            self.assertEqual(payload["rewards"], [])
            self.assertEqual(payload["summary"]["net_credits"], 0)
            self.assertEqual(payload["wallet"]["change"], 0)
            self.assertEqual(payload["wallet"]["unclassified"], 0)
            self.capture(9002, NOW)
            self.balance += 51500
            self.assertEqual(self.collector.panel_payload()["summary"]["net_credits"], 51500)

    def test_old_unverified_raw_capture_is_hidden_after_reset_and_can_still_recover(self):
        with self.clock():
            self.synced_goal()
            raw = self.raw_result(9001, NOW)
            del raw["personal"][321]["creditsReplay"]
            with patch.object(runtime.traceback, "print_exc"), patch("builtins.print"):
                self.events.onBattleResultsReceived.emit(True, raw)
            self.assertEqual(self.collector.panel_payload()["summary"]["pending_battles"], 1)
            candidates = self.collector.store.recovery_candidates("NA", "101")
            self.assertEqual(candidates[0]["reconciliation"]["status"], "unverified")
            self.collector.reset_history({"confirm": True})
            self.assertEqual(self.collector.panel_payload()["summary"]["pending_battles"], 0)
            self.assertEqual(len(self.collector.store.recovery_candidates("NA", "101")), 1)
            # A cache retry may complete its finances but cannot revive an old ID.
            self.capture(9001, NOW)
            payload = self.collector.panel_payload()
            self.assertEqual(payload["summary"]["pending_battles"], 0)
            self.assertEqual(payload["summary"]["battle_count"], 0)
            self.assertEqual(payload["history"], [])
            self.assertEqual(self.collector.ledger.summary("NA", "101")["battle_count"], 1)
            fresh = self.raw_result(9002, NOW)
            del fresh["personal"][321]["creditsReplay"]
            with patch.object(runtime.traceback, "print_exc"), patch("builtins.print"):
                self.events.onBattleResultsReceived.emit(True, fresh)
            self.assertEqual(self.collector.panel_payload()["summary"]["pending_battles"], 1)

    def test_delayed_notice_from_previous_period_is_not_pushed_after_manual_reset(self):
        with self.clock():
            self.synced_goal()
            self.capture(9001, NOW)
            record = self.collector.ledger.list_results("NA", "101", include_pending=False)[0]
            self.balance += 51500
            self.collector.reset_history({"confirm": True})
            with patch.object(self.collector, "_notify") as notify:
                self.collector._result_notice(record)
            notify.assert_not_called()

    def test_delayed_notice_at_daily_boundary_observes_reset_before_reading_period(self):
        with self.native_clock("2026-10-18T09:59:59Z"):
            self.synced_goal()
            self.capture(9001, "2026-10-18T09:59:59Z")
            record = self.collector.ledger.list_results("NA", "101", include_pending=False)[0]
            self.balance += 51500
        with self.native_clock("2026-10-18T10:00:00Z"):
            with patch.object(self.collector, "_notify") as notify:
                self.collector._result_notice(record)
            notify.assert_not_called()
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 1)
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 0)

    def test_reset_keeps_other_account_state_goals_and_results(self):
        with self.clock():
            self.synced_goal()
            other_history = {"mode": "daily", "hour": 4, "preserve_goal": True,
                "since_utc": "2026-10-17T15:00:00Z", "baseline": 100000,
                "excluded_battles": ["1"], "excluded_receipts": [],
                "generation": 3, "daily_cycle": "2026-10-18T09:00:00Z"}
            other_goal = {"schema": 2, "mode": "balance_growth", "target": 900000,
                          "baseline": 100000, "since_utc": OLD}
            self.collector.config["account_history"] = {"NA:202": copy.deepcopy(other_history)}
            self.collector.config["account_goals"]["NA:202"] = copy.deepcopy(other_goal)
            self.collector.ledger.upsert_result({"region": "NA", "account_id": "202",
                "battle_id": "77", "occurred_at": OLD, "status": "final",
                "credits": {"gross": 50000, "expenses": {
                    "repair": 1000, "ammo": 2000, "consumables": 0, "other": 0}}})
            self.collector.reset_history({"confirm": True})
            saved = read_json(self.collector.config_path)
            self.assertEqual(saved["account_history"]["NA:202"], other_history)
            self.assertEqual(saved["account_goals"]["NA:202"], other_goal)
            self.assertEqual(self.collector.ledger.summary("NA", "202")["net_credits"], 47000)

    def test_failed_history_commit_retains_config_goal_and_visible_history(self):
        with self.clock():
            self.synced_goal()
            self.capture(9001, OLD)
            self.balance += 51500
            self.collector._sync_finance()
            before = copy.deepcopy(self.collector.config)
            saved = read_json(self.collector.config_path)
            original = runtime.atomic_json

            def failing_config(path, data):
                if path == self.collector.config_path:
                    raise OSError("synthetic config commit failure")
                return original(path, data)

            with patch.object(runtime, "atomic_json", side_effect=failing_config), \
                    patch.object(runtime.traceback, "print_exc"), patch("builtins.print"):
                self.collector.reset_history({"confirm": True})
            self.assertEqual(self.collector.config, before)
            self.assertEqual(read_json(self.collector.config_path), saved)
            self.assertIsNotNone(self.collector.panel_error)
            payload = self.collector.panel_payload()
            self.assertEqual(payload["summary"]["net_credits"], 51500)
            self.assertEqual(payload["goal"]["current"], 51500)

    def test_manual_reset_requires_confirmation_and_synchronized_balance(self):
        with self.clock():
            self.assertFalse(self.collector.panel_payload()["history_control"]["can_reset"])
            before = copy.deepcopy(self.collector.config)
            self.collector.reset_history({"confirm": True})
            self.assertEqual(self.collector.config, before)
            self.assertIsNotNone(self.collector.panel_error)
            self.synced_goal()
            self.assertTrue(self.collector.panel_payload()["history_control"]["can_reset"])
            for args in ({}, {"confirm": False}, {"confirm": 1}, None):
                before = copy.deepcopy(self.collector.config)
                self.collector.reset_history(args)
                self.assertEqual(self.collector.config, before)
            self.balance = 0
            self.assertTrue(self.collector.panel_payload()["history_control"]["can_reset"])
            self.collector.reset_history({"confirm": True})
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["baseline"], 0)

    def test_default_reset_clears_saved_goal_for_explicit_reactivation(self):
        with self.clock():
            self.synced_goal()
            self.balance = BASE + 600000
            self.collector.reset_history({"confirm": True})
            goal = self.collector.panel_payload()["goal"]
            self.assertEqual(goal["target"], 0)
            self.assertIsNone(goal["baseline"])
            self.assertEqual(goal["current"], 0)
            self.assertEqual(goal["progress_percent"], 0)
            self.assertIsNone(goal["final_balance"])
            self.assertFalse(goal["active"])
            saved_goal = read_json(self.collector.config_path)["account_goals"]["NA:101"]
            self.assertIsNone(saved_goal["since_utc"])
            self.assertEqual(saved_goal["target"], 0)
            self.assertEqual(saved_goal["reset_generation"], 1)

    def test_manual_full_reset_ignores_legacy_preserve_goal_choice(self):
        with self.clock():
            self.synced_goal()
            self.collector.save_history_settings({"mode": "manual", "hour": 6,
                                                  "preserve_goal": True})
            self.balance = BASE + 600000
            self.collector.reset_history({"confirm": True})
            self.assertEqual(self.collector.panel_payload()["goal"]["current"], 0)
            self.assertIsNone(self.collector.config["account_goals"]["NA:101"]["baseline"])
            self.assertEqual(self.collector.config["account_goals"]["NA:101"]["target"], 0)

    def test_hidden_server_policy_rejects_removed_schedule_settings(self):
        with self.native_clock(NOW):
            self.synced_goal()
            saved = copy.deepcopy(self.collector.config)
            for args in ({"mode": "manual"}, {"mode": "daily", "hour": 6},
                         {"mode": "daily", "hour": -1}, None):
                self.collector.save_history_settings(args)
                self.assertEqual(self.collector.config, saved)
                self.assertIsNotNone(self.collector.panel_error)
            self.assertEqual(get_history_state(saved, "NA", "101")["mode"], "server")

    def test_server_boundary_resets_once_without_local_six_am(self):
        with self.native_clock("2026-10-18T09:59:59Z"):
            self.synced_goal()
            self.capture(9001, "2026-10-18T09:59:59Z")
            self.balance += 51500
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 1)
        with self.native_clock("2026-10-18T10:00:00Z"):
            self.events.onClientUpdated.emit({"stats": {"credits": self.balance}}, False)
            self.collector._wallet_changed()
            payload = self.collector.panel_payload()
            self.assertEqual(payload["summary"]["battle_count"], 0)
            self.assertEqual(payload["goal"]["target"], 0)
            self.assertFalse(payload["goal"]["active"])
            self.capture(9002, "2026-10-18T10:00:00Z")
            self.balance += 51500
        with self.native_clock("2026-10-19T09:59:59Z"):
            self.assertEqual(self.collector.panel_payload()["summary"]["net_credits"], 51500)
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 1)
        with self.native_clock("2026-10-19T10:00:00Z"):
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 0)
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 2)

    def test_local_pc_calendar_cannot_schedule_the_builtin_reset(self):
        with mock_local_timezone("UTC"), self.clock("2030-01-01T06:00:00Z"), self.native_clock("2026-10-18T09:59:59Z"):
            self.synced_goal()
            self.capture(9001, "2026-10-18T09:59:59Z")
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 1)
        with mock_local_timezone("America/Bogota"), self.clock("2025-01-01T00:00:00Z"), self.native_clock("2026-10-18T10:00:00Z"):
            payload = self.collector.panel_payload()
            self.assertEqual(payload["summary"]["battle_count"], 0)
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["server_cycle"], "2026-10-18T10:00:00Z")

    def test_legacy_local_schedule_migrates_without_erasing_current_results_or_goal(self):
        with self.native_clock(NOW):
            self.synced_goal()
            self.capture(9001, OLD)
            self.balance += 51500
            goal = copy.deepcopy(self.collector.config["account_goals"]["NA:101"])
            self.collector.config["account_history"] = {"NA:101": {
                "mode": "daily", "hour": 6, "preserve_goal": True,
                "since_utc": None, "baseline": None, "generation": 0,
                "excluded_battles": [], "excluded_receipts": [],
                "daily_cycle": "2026-10-17T11:00:00Z"}}
            self.collector._sync_finance()
            state = get_history_state(self.collector.config, "NA", "101")
            self.assertEqual(state["mode"], "server")
            self.assertEqual(state["clock"], "server_v1")
            self.assertEqual(state["server_cycle"], "2026-10-18T10:00:00Z")
            self.assertEqual(state["generation"], 0)
            self.assertIsNone(state["since_utc"])
            self.assertEqual(self.collector.config["account_goals"]["NA:101"], goal)
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 1)

    def test_overdue_server_reset_waits_for_first_synced_balance_after_offline_days(self):
        with self.native_clock("2026-10-17T12:00:00Z"):
            self.synced_goal()
            self.capture(9001, "2026-10-17T12:00:00Z")
        with self.native_clock("2026-10-22T15:00:00Z"):
            self.balance = None
            self.collector._sync_finance()
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 0)
            self.balance = BASE + 51500
            self.collector._sync_finance()
            state = get_history_state(self.collector.config, "NA", "101")
            self.assertEqual(state["generation"], 1)
            self.assertEqual(state["since_utc"], "2026-10-22T15:00:00Z")
            self.assertEqual(state["baseline"], self.balance)
            self.assertEqual(state["server_cycle"], "2026-10-22T10:00:00Z")
            self.collector._sync_finance()
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 1)
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 0)


if __name__ == "__main__":
    unittest.main()
