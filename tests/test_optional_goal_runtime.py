"""An optional credit goal must not alter the account's financial tracking."""
import calendar
import copy
import unittest
from unittest.mock import patch

import test_capture_runtime as harness
from capture import runtime
from capture.storage import atomic_json, read_json


START = "2026-10-18T12:00:00Z"
STOP = "2026-10-18T13:00:00Z"
RESTART = "2026-10-18T14:00:00Z"
BASE = 22000000
KEY = "NA:101"


class OptionalGoalRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def save(self, value, stamp=START):
        with patch.object(runtime, "_now_utc", return_value=stamp):
            self.collector.save_goal({"value": value, "mode": "balance_growth"})

    def start_goal(self):
        self.balance = BASE
        self.save("1000000")
        self.assertIsNone(self.collector.panel_error)
        return copy.deepcopy(self.collector.config["account_goals"][KEY])

    def test_initial_zero_is_saved_without_balance_and_has_no_fabricated_base(self):
        self.assertIsNone(self.balance)
        self.save("0")
        self.assertIsNone(self.collector.panel_error)
        saved = read_json(self.collector.config_path)["account_goals"][KEY]
        self.assertEqual(saved["schema"], 2)
        self.assertEqual(saved["mode"], "balance_growth")
        self.assertEqual(saved["target"], 0)
        self.assertIsNone(saved["baseline"])
        self.assertIsNone(saved["since_utc"])
        payload = self.collector.panel_payload()
        self.assertFalse(payload["goal"]["active"])
        self.assertEqual(payload["goal"]["target"], 0)
        self.assertIsNone(payload["balance"])

    def test_disabling_preserves_base_date_finances_period_and_other_account(self):
        original_goal = self.start_goal()
        self.events.onBattleResultsReceived.emit(True, harness.fixture())
        self.balance = BASE + 51500
        self.collector._sync_finance()
        self.collector.config["account_history"] = {
            KEY: {"mode": "manual", "hour": 6, "preserve_goal": False,
                  "since_utc": START, "baseline": BASE, "generation": 4,
                  "excluded_battles": [], "excluded_receipts": [],
                  "daily_cycle": None, "clock": "local_v1"}}
        self.collector.config["account_goals"]["NA:202"] = {
            "schema": 2, "mode": "balance_growth", "target": 5000000,
            "baseline": 41000000, "since_utc": START}
        atomic_json(self.collector.config_path, self.collector.config)
        before_ledger = copy.deepcopy(self.collector.ledger.to_dict())
        before_wallet = copy.deepcopy(self.collector.wallet.data)
        before_history = copy.deepcopy(self.collector.config["account_history"])
        before_other = copy.deepcopy(self.collector.config["account_goals"]["NA:202"])
        disk_ledger = read_json(self.collector.ledger_path)
        disk_wallet = read_json(self.collector.wallet_path)
        self.save("0", STOP)
        self.assertIsNone(self.collector.panel_error)
        saved = read_json(self.collector.config_path)
        self.assertEqual(saved["account_goals"][KEY]["target"], 0)
        self.assertEqual(saved["account_goals"][KEY]["baseline"], original_goal["baseline"])
        self.assertEqual(saved["account_goals"][KEY]["since_utc"], original_goal["since_utc"])
        self.assertEqual(saved["account_history"], before_history)
        self.assertEqual(saved["account_goals"]["NA:202"], before_other)
        self.assertEqual(self.collector.ledger.to_dict(), before_ledger)
        self.assertEqual(self.collector.wallet.data, before_wallet)
        self.assertEqual(read_json(self.collector.ledger_path), disk_ledger)
        self.assertEqual(read_json(self.collector.wallet_path), disk_wallet)
        self.assertFalse(self.collector.panel_payload()["goal"]["active"])

    def test_disabled_goal_survives_a_new_collector_and_later_balance_sync(self):
        self.start_goal()
        self.save("0", STOP)
        saved = copy.deepcopy(read_json(self.collector.config_path)["account_goals"][KEY])
        self.collector.close()
        reopened = runtime.Collector()
        try:
            with patch.object(reopened, "_read_balance", return_value=BASE + 100000):
                reopened._sync_finance()
                payload = reopened.panel_payload()
            self.assertEqual(reopened.config["account_goals"][KEY], saved)
            self.assertEqual(read_json(reopened.config_path)["account_goals"][KEY], saved)
            self.assertFalse(payload["goal"]["active"])
            self.assertEqual(payload["goal"]["target"], 0)
            self.assertEqual(payload["balance"], BASE + 100000)
        finally:
            reopened.close()

    def test_failed_disable_commit_keeps_previous_goal_in_memory_and_on_disk(self):
        self.start_goal()
        before = copy.deepcopy(self.collector.config)
        with patch.object(runtime, "atomic_json", side_effect=OSError("synthetic config write failure")), \
                patch.object(self.collector, "_error") as error:
            self.save("0", STOP)
        error.assert_called_once_with("goal_save_failed")
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, before)
        self.assertEqual(read_json(self.collector.config_path), before)
        self.assertTrue(self.collector.panel_payload()["goal"]["active"])

    def test_capture_and_rewards_continue_while_goal_is_disabled(self):
        self.balance = BASE
        with patch.object(runtime, "_now_utc", return_value=START):
            self.save("0")
            self.collector._sync_finance()
        result = harness.fixture()
        stamp = runtime.datetime.datetime.strptime(STOP, "%Y-%m-%dT%H:%M:%SZ")
        result["common"]["arenaCreateTime"] = calendar.timegm(stamp.timetuple()) - 300
        self.events.onBattleResultsReceived.emit(True, result)
        with patch.object(runtime, "_now_utc", return_value=STOP):
            self.collector.accept_receipt({"id": "optional-goal:mission", "kind": "tokenQuests",
                "occurred_at": STOP, "battle_id": None, "credits": 25000,
                "included_in_battle": False, "title": "Misión adicional", "parts": []})
            self.balance = BASE + 51500 + 25000
            payload = self.collector.panel_payload()
        self.assertFalse(payload["goal"]["active"])
        self.assertEqual(payload["goal"]["target"], 0)
        self.assertEqual(payload["summary"]["battle_count"], 1)
        self.assertEqual(payload["summary"]["net_credits"], 51500)
        self.assertEqual(payload["wallet"]["battle_net"], 51500)
        self.assertEqual(payload["wallet"]["external_credits"], 25000)
        self.assertEqual(payload["wallet"]["unclassified"], 0)
        self.assertEqual(payload["balance"], BASE + 76500)
        self.assertEqual(len(self.collector.wallet.receipts("NA", "101")), 1)
        self.assertEqual(read_json(self.collector.config_path)["account_goals"][KEY]["target"], 0)

    def test_active_goal_can_be_disabled_when_balance_is_temporarily_unknown(self):
        original = self.start_goal()
        self.balance = None
        self.save("0", STOP)
        self.assertIsNone(self.collector.panel_error)
        saved = self.collector.config["account_goals"][KEY]
        self.assertEqual(saved["target"], 0)
        self.assertEqual(saved["baseline"], original["baseline"])
        self.assertEqual(saved["since_utc"], original["since_utc"])
        self.assertEqual(read_json(self.collector.config_path)["account_goals"][KEY], saved)

    def test_positive_goal_after_zero_resumes_original_balance_and_time(self):
        original = self.start_goal()
        self.save("0", STOP)
        disabled = copy.deepcopy(self.collector.config)
        self.balance = None
        self.save("2000000", RESTART)
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, disabled)
        self.balance = BASE + 76500
        self.save("2000000", RESTART)
        self.assertIsNone(self.collector.panel_error)
        saved = self.collector.config["account_goals"][KEY]
        self.assertEqual(saved["target"], 2000000)
        self.assertEqual(saved["baseline"], original["baseline"])
        self.assertEqual(saved["since_utc"], original["since_utc"])
        payload = self.collector.panel_payload()
        self.assertTrue(payload["goal"]["active"])
        self.assertEqual(payload["goal"]["current"], 76500)
        self.assertAlmostEqual(payload["goal"]["progress_percent"], 3.825)

    def test_disabled_progress_survives_reopen_and_resumes_after_a_loss(self):
        original = self.start_goal()
        self.balance = BASE + 100000
        self.save("0", STOP)
        self.collector.close()
        reopened = runtime.Collector()
        try:
            with patch.object(reopened, "_read_balance", return_value=BASE - 50000), \
                    patch.object(runtime, "_now_utc", return_value=RESTART):
                inactive = reopened.panel_payload()["goal"]
                self.assertFalse(inactive["active"])
                self.assertEqual(inactive["current"], -50000)
                reopened.save_goal({"value": "2000000", "mode": "balance_growth"})
                resumed = reopened.panel_payload()["goal"]
            self.assertIsNone(reopened.panel_error)
            self.assertTrue(resumed["active"])
            self.assertEqual(resumed["baseline"], original["baseline"])
            self.assertEqual(resumed["since_utc"], original["since_utc"])
            self.assertEqual(resumed["current"], -50000)
            self.assertEqual(resumed["remaining"], 2050000)
            self.assertEqual(resumed["progress_percent"], 0)
        finally:
            reopened.close()

    def test_zero_still_requires_a_valid_account_identity(self):
        before = copy.deepcopy(self.collector.config)
        self.account = None
        self.save("0", STOP)
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, before)
        self.assertEqual(read_json(self.collector.config_path), before)


if __name__ == "__main__":
    unittest.main()
