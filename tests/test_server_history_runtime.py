"""Daily server cycles through the collector, live balance and persisted periods."""
import copy
import types
import unittest
from unittest.mock import patch

import test_history_runtime as harness
from capture import runtime
from capture.history import get_history_state
from capture.server_clock import server_day_clock
from capture.storage import read_json
from test_server_clock import epoch


BASE = 22000000


class ServerHistoryRuntimeTests(unittest.TestCase):
    setUp = harness.HistoryRuntimeTests.setUp
    tearDown = harness.HistoryRuntimeTests.tearDown
    raw_result = harness.HistoryRuntimeTests.raw_result
    capture = harness.HistoryRuntimeTests.capture
    receipt = harness.HistoryRuntimeTests.receipt
    clock = harness.HistoryRuntimeTests.clock

    def native(self, stamp):
        return patch.object(self.collector, "_read_server_clock", return_value=(
            server_day_clock(epoch(stamp), 36000) if stamp else None))

    def start(self):
        self.balance = BASE
        self.collector._sync_finance()
        self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})
        self.capture(9001, "2026-10-18T12:00:00Z")
        self.receipt("token:old", "2026-10-18T12:00:00Z")
        self.balance += 76500
        return self.collector.panel_payload()

    def test_server_rollover_zeros_all_groups_goal_and_wallet_period_only_once(self):
        with self.native("2026-10-18T12:00:00Z"):
            before = self.start()
            self.assertEqual(before["history_control"]["mode"], "server")
            self.assertTrue(before["history_control"]["server_clock_ready"])
            self.assertEqual(before["summary"]["net_credits"], 51500)
        ledger = copy.deepcopy(self.collector.ledger.to_dict())
        with self.native("2026-10-19T10:00:00Z"):
            fresh = self.collector.panel_payload()
            self.assertEqual(fresh["history_control"]["generation"], 1)
            self.assertEqual(fresh["summary"]["battle_count"], 0)
            self.assertEqual(fresh["summary"]["net_credits"], 0)
            self.assertEqual(fresh["history"], [])
            self.assertEqual(fresh["vehicle_groups"], [])
            self.assertEqual(fresh["rewards"], [])
            self.assertEqual(fresh["wallet"]["baseline"], self.balance)
            self.assertEqual(fresh["wallet"]["change"], 0)
            self.assertEqual(fresh["goal"]["target"], 0)
            self.assertFalse(fresh["goal"]["active"])
            self.assertIsNone(fresh["goal"]["baseline"])
            self.assertEqual(fresh["goal"]["reset_generation"], 1)
            self.assertEqual(self.collector.ledger.to_dict(), ledger)
            self.assertEqual(len(self.collector.wallet.receipts("NA", "101")), 1)
            self.collector.save_goal({"value": "500000", "mode": "balance_growth"})
            self.assertEqual(self.collector.panel_payload()["goal"]["baseline"], self.balance)
            self.capture(9002, "2026-10-19T10:00:00Z")
            self.balance += 51500
            for _ in range(3):
                fresh = self.collector.panel_payload()
                self.assertEqual(fresh["summary"]["net_credits"], 51500)
                self.assertEqual(fresh["goal"]["current"], 51500)
                self.assertEqual(fresh["history_control"]["generation"], 1)
            self.capture(9003, "2026-10-18T15:00:00Z")
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 1)

    def test_unavailable_calendar_and_balance_wait_then_reset_after_offline_days(self):
        with self.native("2026-10-18T12:00:00Z"):
            self.start()
        with self.native(None), self.clock("2030-01-01T00:00:00Z"):
            payload = self.collector.panel_payload()
            self.assertFalse(payload["history_control"]["server_clock_ready"])
            self.assertEqual(payload["history_control"]["generation"], 0)
            self.assertEqual(payload["goal"]["target"], 3000000)
        self.balance = None
        with self.native("2026-10-23T12:00:00Z"):
            self.collector._sync_finance()
            self.assertEqual(get_history_state(self.collector.config, "NA", "101")["generation"], 0)
            self.balance = BASE + 200000
            fresh = self.collector.panel_payload()
            self.assertEqual(fresh["history_control"]["generation"], 1)
            self.assertEqual(fresh["wallet"]["baseline"], BASE + 200000)
            self.assertEqual(fresh["goal"]["target"], 0)

    def test_removed_manual_schedule_cannot_disable_server_reset(self):
        with self.native("2026-10-18T12:00:00Z"):
            self.start()
            self.collector.save_history_settings({"mode": "manual", "hour": 6, "preserve_goal": False})
        with self.native("2026-10-23T12:00:00Z"):
            self.assertEqual(self.collector.panel_payload()["summary"]["battle_count"], 0)
            self.assertEqual(self.collector.panel_payload()["history_control"]["mode"], "server")
            self.collector.reset_history({"confirm": True})
            fresh = self.collector.panel_payload()
            self.assertEqual(fresh["goal"]["target"], 0)
            self.assertEqual(fresh["summary"]["battle_count"], 0)

    def test_failed_period_commit_preserves_goal_and_retries_same_server_cycle(self):
        with self.native("2026-10-18T12:00:00Z"):
            self.start()
        saved = copy.deepcopy(self.collector.config)
        original = runtime.atomic_json
        def save(path, data):
            if path == self.collector.config_path:
                raise OSError("synthetic period commit failure")
            return original(path, data)
        with self.native("2026-10-19T12:00:00Z"):
            with patch.object(runtime, "atomic_json", side_effect=save):
                with self.assertRaises(OSError):
                    self.collector._sync_finance()
            self.assertEqual(self.collector.config, saved)
            self.assertEqual(read_json(self.collector.config_path), saved)
            self.assertEqual(self.collector.panel_payload()["history_control"]["generation"], 1)

    def test_native_calendar_is_blocked_until_this_accounts_show_gui_correction(self):
        clock = server_day_clock(epoch("2026-10-19T12:00:00Z"), 36000)
        with patch.object(runtime, "native_server_clock", return_value=clock) as native:
            self.assertIsNone(self.collector._read_server_clock())
            native.assert_not_called()
            self.collector._on_account_gui({"databaseID": 101})
            self.assertEqual(self.collector._read_server_clock(), clock)
            self.collector._leave_account()
            self.assertIsNone(self.collector._read_server_clock())
            self.collector._on_account_gui({"databaseID": 999})
            self.assertIsNone(self.collector._read_server_clock())


if __name__ == "__main__":
    unittest.main()
