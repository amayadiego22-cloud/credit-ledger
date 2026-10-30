"""Native realm startup, financial isolation, and regional server calendars."""
import calendar
import copy
import datetime
import os
import sys
import types
import unittest
from unittest.mock import patch

import test_capture_runtime as harness
from capture import runtime
from capture.compatibility import SUPPORTED_REALMS, resolve_realm, supported_realm
from capture.completion import goal_completion_payload
from capture.history import get_history_state
from capture.storage import read_json


NOW = "2026-10-18T12:00:00Z"
OFFSETS = {"NA": 36000, "EU": 14400, "ASIA": 7200}


def epoch(stamp):
    return calendar.timegm(datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").timetuple())


class RealmResolutionTests(unittest.TestCase):
    def test_three_wargaming_realms_keep_distinct_native_identifiers(self):
        self.assertEqual(SUPPORTED_REALMS, ("NA", "EU", "ASIA"))
        for realm in SUPPORTED_REALMS:
            with self.subTest(realm=realm):
                self.assertEqual(supported_realm(realm), realm)
                self.assertEqual(supported_realm(" " + realm.lower() + " "), realm)
                self.assertEqual(resolve_realm(types.SimpleNamespace(CURRENT_REALM=realm)), realm)

    def test_auth_realm_is_used_only_when_current_is_missing(self):
        for realm in SUPPORTED_REALMS:
            with self.subTest(realm=realm):
                for attributes in ({}, {"CURRENT_REALM": None}, {"CURRENT_REALM": ""}):
                    self.assertEqual(resolve_realm(types.SimpleNamespace(AUTH_REALM=realm, **attributes)), realm)
                self.assertEqual(resolve_realm(types.SimpleNamespace(
                    CURRENT_REALM=realm, AUTH_REALM="RU")), realm)

    def test_unsupported_current_never_uses_an_authentication_alias(self):
        for realm in ("RU", "RUS", "ASIA2", "CN", "CT", "ST", "SANDBOX", "../EU"):
            with self.subTest(realm=realm):
                with self.assertRaises(RuntimeError):
                    resolve_realm(types.SimpleNamespace(CURRENT_REALM=realm, AUTH_REALM="NA"))

    def test_missing_and_invalid_realms_are_rejected(self):
        for realm in (None, "", " ", False, True, 0, 1, [], {}, object()):
            with self.subTest(realm_type=type(realm).__name__):
                with self.assertRaises(RuntimeError):
                    supported_realm(realm)


class RegionalRuntimeTests(unittest.TestCase):
    """Run the real Collector with mocked native APIs, not a region-only stub."""
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def restart(self, realm=None, auth=None):
        self.collector.close()
        self.balance_patch.stop()
        constants = sys.modules["constants"]
        for name in ("CURRENT_REALM", "AUTH_REALM"):
            if hasattr(constants, name):
                delattr(constants, name)
        if realm is not None:
            constants.CURRENT_REALM = realm
        if auth is not None:
            constants.AUTH_REALM = auth
        self.collector = runtime.Collector()
        self.balance = None
        self.balance_patch = patch.object(self.collector, "_read_balance", side_effect=lambda: self.balance)
        self.balance_patch.start()

    def native_time(self, realm, stamp=NOW):
        self.account.serverSettings = {"regional_settings": {
            "starting_time_of_a_new_game_day": OFFSETS[realm]}}
        self.collector._server_clock_account_id = "101"
        helpers = types.ModuleType("helpers")
        helpers.time_utils = types.SimpleNamespace(getServerUTCTime=lambda: epoch(stamp))
        return patch.dict(sys.modules, {"helpers": helpers})

    def capture(self):
        raw = harness.fixture()
        raw["arenaUniqueID"] = 9001
        raw["common"] = {"arenaCreateTime": epoch(NOW) - 300, "duration": 300, "bonusType": 1}
        self.events.onBattleResultsReceived.emit(True, raw)

    def start_region(self, realm, base):
        self.restart(realm)
        with self.native_time(realm):
            self.balance = base
            self.collector._sync_finance()
            self.collector.save_goal({"value": "50000", "mode": "balance_growth"})
            self.capture()
            self.collector.accept_receipt({"id": "token:same-id", "kind": "tokenQuests",
                "occurred_at": NOW, "battle_id": None, "credits": 25000,
                "included_in_battle": False, "title": "Synthetic reward", "parts": []})
            self.balance += 76500
            return self.collector.panel_payload()

    def test_collector_loads_captures_and_presents_every_supported_realm(self):
        for index, realm in enumerate(SUPPORTED_REALMS):
            with self.subTest(realm=realm):
                base = 1000000 * (index + 1)
                payload = self.start_region(realm, base)
                self.assertEqual(self.collector.realm, realm)
                self.assertEqual(payload["account_context"], realm + ":101")
                self.assertEqual(payload["summary"]["battle_count"], 1)
                self.assertEqual(payload["summary"]["gross_credits"], 80500)
                self.assertEqual(payload["summary"]["net_credits"], 51500)
                self.assertEqual(payload["goal"]["baseline"], base)
                self.assertEqual(payload["goal"]["current"], 76500)
                self.assertEqual(payload["wallet"]["external_credits"], 25000)
                self.assertEqual(payload["wallet"]["unclassified"], 0)
                self.assertEqual(len(payload["history"]), 1)
                self.assertEqual(len(payload["rewards"]), 1)
                path = os.path.join(self.collector.directory, "captures", realm, "101", "9001.json")
                self.assertEqual(read_json(path)["region"], realm)
                event = goal_completion_payload(self.collector.config, realm, "101", self.balance)
                self.assertEqual(event["account_context"], realm + ":101")
        # The same battle/account/receipt IDs from different realms do not merge.
        self.assertEqual(len(self.collector.ledger.to_dict()["records"]), 3)
        for realm in SUPPORTED_REALMS:
            self.assertEqual(self.collector.ledger.summary(realm, "101")["net_credits"], 51500)
            self.assertEqual(len(self.collector.wallet.receipts(realm, "101")), 1)

    def test_collector_uses_native_auth_realm_fallback(self):
        for realm in SUPPORTED_REALMS:
            with self.subTest(realm=realm):
                self.restart(auth=realm)
                self.capture()
                self.assertEqual(self.collector.realm, realm)
                self.assertEqual(self.collector.ledger.summary(realm, "101")["battle_count"], 1)

    def test_unsupported_startup_rejects_before_reading_or_writing_user_data(self):
        self.collector.close()
        before = {}
        for root, directories, names in os.walk(self.directory):
            for name in names:
                path = os.path.join(root, name)
                with open(path, "rb") as handle:
                    before[path] = handle.read()
        for realm in ("RU", "CN", "CT", "UNKNOWN"):
            with self.subTest(realm=realm):
                sys.modules["constants"].CURRENT_REALM = realm
                sys.modules["constants"].AUTH_REALM = "NA"
                with patch.object(runtime, "_game_directory") as game_root:
                    with patch.object(runtime, "CaptureStore") as store:
                        with patch.object(runtime, "atomic_json") as write:
                            with self.assertRaises(RuntimeError):
                                runtime.Collector()
                            game_root.assert_not_called()
                            store.assert_not_called()
                            write.assert_not_called()
        for path, content in before.items():
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), content)

    def test_region_reset_uses_native_offset_and_preserves_other_regions(self):
        for index, realm in enumerate(SUPPORTED_REALMS):
            with self.subTest(initializing=realm):
                payload = self.start_region(realm, 1000000 * (index + 1))
                expected_hour = OFFSETS[realm] // 3600
                self.assertEqual(payload["history_control"]["next_reset_utc"],
                    "2026-10-19T%02d:00:00Z" % expected_hour)

        ledger = copy.deepcopy(self.collector.ledger.to_dict())
        before = copy.deepcopy(self.collector.config)
        wallet = copy.deepcopy(self.collector.wallet.data)
        for realm in SUPPORTED_REALMS:
            self.assertEqual(get_history_state(before, realm, "101")["generation"], 0)

        # At 02:00 UTC only Asia's next native day has begun. The NA and EU
        # accounts retain their own goals, receipts, and visible history state.
        with self.native_time("ASIA", "2026-10-19T02:00:00Z"):
            fresh = self.collector.panel_payload()
            self.assertEqual(fresh["summary"]["battle_count"], 0)
            self.assertEqual(fresh["summary"]["net_credits"], 0)
            self.assertEqual(fresh["history_control"]["generation"], 1)
            self.assertEqual(fresh["goal"]["target"], 100000)
            self.assertTrue(fresh["goal"]["active"])
            self.assertEqual(fresh["goal"]["baseline"], self.balance)
            self.assertEqual(fresh["goal"]["current"], 0)
            self.assertEqual(fresh["wallet"]["baseline"], self.balance)
            self.assertEqual(fresh["wallet"]["change"], 0)
            self.assertEqual(self.collector.panel_payload()["history_control"]["generation"], 1)
        self.assertEqual(self.collector.ledger.to_dict(), ledger)
        for realm in ("NA", "EU"):
            key = realm + ":101"
            for section in ("account_goals", "account_history", "account_goal_completions"):
                self.assertEqual(self.collector.config[section][key], before[section][key])
            self.assertEqual(self.collector.wallet.data["accounts"][key], wallet["accounts"][key])
        self.assertEqual(len(self.collector.wallet.receipts("ASIA", "101")), 1)


if __name__ == "__main__":
    unittest.main()
