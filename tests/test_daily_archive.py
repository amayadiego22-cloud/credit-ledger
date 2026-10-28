# -*- coding: utf-8 -*-
"""Past server days are read-only, exact, and independent of visible resets."""
import copy
import datetime
import unittest

from capture.archive import partition_server_days, server_day_bounds
from capture.presentation import build_payload
from capture.wallet import WalletBook
from core import EconomyLedger
from timezone_fixtures import mock_local_timezone


NOW = "2026-10-20T15:00:00Z"
CLOCK = {"cycle_start_utc": "2026-10-20T10:00:00Z",
         "next_reset_utc": "2026-10-21T10:00:00Z", "server_now_utc": NOW}
ICON = "coui://gui/maps/icons/vehicle/usa-A01_T1_Cunningham.png"


def result(identity, occurred="2026-10-19T14:00:00Z", mode=20, tank="321", gross=100000,
           account="101", region="NA", status="final"):
    row = {"region": region, "account_id": account, "battle_id": str(identity),
           "occurred_at": occurred, "status": status,
           "vehicles": [{"vehicle_type_id": tank, "name": "XM57", "tier": 8, "icon": ICON}],
           "credits": {"gross": gross, "expenses": {"repair": 10000, "ammo": 20000,
                          "consumables": 5000, "other": 0},
                       "reserves": {"personal": 1000, "clan": 2000}}}
    if mode is not None:
        row["battle_mode"] = {"bonus_type": mode}
    return row


def receipt(identity, amount=15000, included=False, battle=None, occurred="2026-10-19T14:00:00Z"):
    return {"id": str(identity), "occurred_at": occurred, "credits": amount,
            "included_in_battle": included, "battle_id": str(battle) if battle is not None else None,
            "parts": [{"quest_id": "daily_1", "name": "Crisol", "credits": amount,
                       "name_resolved": True}]}


class DailyArchiveTests(unittest.TestCase):
    def setUp(self):
        zone = mock_local_timezone("America/Bogota")
        zone.__enter__()
        self.addCleanup(zone.__exit__, None, None, None)
        self.ledger, self.wallet = EconomyLedger(), WalletBook()
        self.config = {"account_history": {"NA:101": {"mode": "server", "clock": "server_v1",
            "server_cycle": CLOCK["cycle_start_utc"], "since_utc": CLOCK["cycle_start_utc"],
            "baseline": 22000000, "generation": 4, "excluded_battles": ["1"]}},
            "account_goals": {"NA:101": {"target": 0, "baseline": 22000000,
                "since_utc": CLOCK["cycle_start_utc"], "mode": "balance_growth"}}}

    def archive(self, requested=None, **kwargs):
        return build_payload(self.ledger, "NA", "101", self.config, 22000000,
            now_utc=NOW, server_clock=kwargs.get("server_clock", CLOCK),
            wallet=self.wallet, archive_filter=requested)["history_archive"]

    def query(self, day="2026-10-19T10:00:00Z", mode="all", tank="all", request=7):
        return self.archive({"day_key": day, "mode_key": mode, "vehicle_key": tank,
                             "request_id": request})["selection"]

    def test_native_boundaries_include_end_of_previous_day_but_not_current_or_future(self):
        for row in (result(1, "2026-10-19T09:59:59Z"), result(2, "2026-10-19T10:00:00Z"),
                    result(3, "2026-10-20T09:59:59Z"), result(4, "2026-10-20T10:00:00Z"),
                    result(5, "2026-10-22T01:00:00Z")):
            self.ledger.upsert_result(row)
        days = self.archive()["days"]
        self.assertEqual([day["key"] for day in days],
                         ["2026-10-19T10:00:00Z", "2026-10-18T10:00:00Z"])
        self.assertEqual([day["label"] for day in days], ["19/10/2026", "18/10/2026"])
        self.assertEqual([day["battle_count"] for day in days], [2, 1])
        self.assertEqual([row["battle_id"] for row in self.query()["history"]], ["3", "2"])

    def test_archive_ignores_manual_reset_exclusions_but_never_changes_live_data(self):
        self.ledger.upsert_result(result(1))
        self.wallet.upsert_receipt("NA", "101", receipt(1))
        self.wallet.observe("NA", "101", 22000000, CLOCK["cycle_start_utc"])
        before = (copy.deepcopy(self.config), self.ledger.to_dict(), copy.deepcopy(self.wallet.data))
        payload = build_payload(self.ledger, "NA", "101", self.config, 22000000,
            now_utc=NOW, server_clock=CLOCK, wallet=self.wallet,
            archive_filter={"day_key": "2026-10-19T10:00:00Z", "request_id": 8})
        self.assertEqual(payload["summary"]["battle_count"], 0)
        self.assertEqual(payload["history_archive"]["selection"]["history_total"], 1)
        self.assertEqual(payload["goal"]["target"], 0)
        self.assertEqual(before, (self.config, self.ledger.to_dict(), self.wallet.data))

    def test_mode_and_tank_filters_use_exact_full_day_scopes_and_preserve_metadata(self):
        for row in (result(1, mode=1), result(2, mode=20), result(3, mode=20, tank="654"),
                    result(4, mode=43), result(5, mode=102), result(6, mode=None)):
            self.ledger.upsert_result(row)
        self.assertEqual(self.query()["history_total"], 6)
        scoped = self.query(mode="mode:20", tank="vehicle:321", request=42)
        self.assertTrue(scoped["available"])
        self.assertEqual((scoped["mode_key"], scoped["vehicle_key"], scoped["request_id"]),
                         ("mode:20", "vehicle:321", 42))
        self.assertEqual(scoped["summary"]["net_credits"], 65000)
        self.assertEqual(scoped["history_total"], 1)
        self.assertEqual(scoped["history"][0]["vehicles"][0]["icon"], ICON)
        self.assertEqual(scoped["history"][0]["vehicles"][0]["tier"], 8)
        self.assertEqual(scoped["history"][0]["battle_mode"]["bonus_type"], 20)
        self.assertEqual(set(group["key"] for group in scoped["mode_groups"]),
                         {"mode:1", "mode:20", "mode:43", "mode:102", "unknown"})
        self.assertTrue(all("history" not in group for group in scoped["mode_groups"]))
        self.assertTrue(all("vehicle_groups" not in group for group in scoped["mode_groups"]))
        self.assertEqual(self.query(mode="unknown")["history_total"], 1)

    def test_selected_history_caps_100_but_summaries_use_all_130_results(self):
        for number in range(130):
            when = datetime.datetime(2026, 10, 19, 12) + datetime.timedelta(minutes=number)
            self.ledger.upsert_result(result(number, when.strftime("%Y-%m-%dT%H:%M:%SZ")))
        selected = self.query(mode="mode:20", tank="vehicle:321")
        self.assertEqual((len(selected["history"]), selected["history_total"]), (100, 130))
        self.assertEqual(selected["history"][0]["battle_id"], "129")
        self.assertEqual(selected["history"][-1]["battle_id"], "30")
        self.assertEqual(selected["summary"]["net_credits"], 130 * 65000)
        self.assertEqual(selected["summary"]["reserves"]["clan"], 260000)
        self.assertEqual(self.archive()["days"][0]["battle_count"], 130)

    def test_all_recorded_days_remain_available_without_a_30_day_cutoff(self):
        for number in range(45):
            when = datetime.datetime(2026, 10, 19, 12) - datetime.timedelta(days=number)
            self.ledger.upsert_result(result(number, when.strftime("%Y-%m-%dT%H:%M:%SZ")))
        self.assertEqual(len(self.archive()["days"]), 45)

    def test_foreign_accounts_regions_and_pending_finance_do_not_leak(self):
        for row in (result(1), result(2, account="102"), result(3, region="EU"),
                    result(4, status="pending")):
            self.ledger.upsert_result(row)
        self.assertEqual(self.archive()["days"][0]["battle_count"], 1)
        self.assertEqual(self.query()["history_total"], 1)
        self.assertEqual(self.query()["account_context"], "NA:101")
        self.wallet.upsert_receipt("EU", "101", receipt(1, amount=999999))
        self.assertEqual(self.query()["external_credits"], 0)

    def test_missing_or_invalid_clock_has_no_local_midnight_fallback(self):
        self.ledger.upsert_result(result(1))
        for clock in (None, {}, {"cycle_start_utc": "2026-10-20T10:00:00Z",
                                 "next_reset_utc": "2026-10-21T11:00:00Z"}):
            current = partition_server_days(self.ledger, "NA", "101", {}, NOW, clock)
            self.assertEqual(current, {"ready": False, "days": []})
        missing_account = build_payload(self.ledger, "NA", None, {}, None,
            now_utc=NOW, server_clock=CLOCK)["history_archive"]
        self.assertEqual(missing_account, {"ready": False, "days": [], "selection": None})

    def test_saved_native_cycle_is_last_known_cutoff_and_never_advanced_by_pc_time(self):
        self.ledger.upsert_result(result(1))
        self.ledger.upsert_result(result(2, "2026-10-21T12:00:00Z"))
        current = partition_server_days(self.ledger, "NA", "101", self.config,
                                        "2026-10-25T12:00:00Z", None)
        self.assertTrue(current["ready"])
        self.assertEqual([day["key"] for day in current["days"]], ["2026-10-19T10:00:00Z"])
        self.config["account_history"]["NA:101"]["server_cycle"] = "2026-10-26T10:00:00Z"
        self.assertFalse(partition_server_days(self.ledger, "NA", "101", self.config,
                                              "2026-10-25T12:00:00Z", None)["ready"])

    def test_extra_rewards_are_separate_and_same_battle_quest_is_not_double_counted(self):
        self.ledger.upsert_result(result(1))
        self.wallet.upsert_receipt("NA", "101", receipt(1, included=True, battle=1))
        self.wallet.upsert_receipt("NA", "101", receipt(2, battle=1))
        self.wallet.upsert_receipt("NA", "101", receipt(3, amount=50000))
        selected = self.query(mode="mode:20", tank="vehicle:321")
        self.assertEqual(selected["summary"]["net_credits"], 65000)
        self.assertEqual(selected["external_credits"], 50000)
        self.assertEqual([row["id"] for row in selected["external_rewards"]], ["3"])
        self.assertEqual(selected["history"][0]["rewards"][0]["name"], "Crisol")
        self.assertEqual(self.archive()["days"][0]["external_credits"], 50000)

    def test_receipt_only_day_is_available_and_unknown_queries_never_show_live_stats(self):
        self.wallet.upsert_receipt("NA", "101", receipt(1))
        day = self.archive()["days"][0]
        self.assertEqual((day["battle_count"], day["external_credits"]), (0, 15000))
        self.assertEqual(self.query()["summary"]["net_credits"], 0)
        for selection in (self.query(day="2026-10-18T10:00:00Z"),
                          self.query(mode="mode:9999"), self.query(tank="vehicle:9999")):
            self.assertFalse(selection["available"])
            self.assertEqual(selection["history"], [])
            self.assertEqual(selection["summary"]["net_credits"], 0)

    def test_metadata_day_bounds_require_exact_prior_native_offset(self):
        bounds = server_day_bounds(self.config, "NA", "101", NOW, CLOCK,
                                    "2026-10-19T10:00:00Z")
        self.assertEqual(bounds, {"start_utc": "2026-10-19T10:00:00Z",
                                  "end_utc": "2026-10-20T10:00:00Z"})
        for value in (None, "2026-10-19", "2026-10-19T00:00:00Z", "2026-10-19T10:00:01Z",
                      "2026-10-20T10:00:00Z", "2026-10-21T10:00:00Z"):
            self.assertIsNone(server_day_bounds(self.config, "NA", "101", NOW, CLOCK, value))
        self.assertIsNone(server_day_bounds({}, "NA", "101", NOW, None,
                                             "2026-10-19T10:00:00Z"))

    def test_later_battle_receipt_deduplicates_prior_day_extra_receipt(self):
        self.ledger.upsert_result(result(1))
        self.wallet.upsert_receipt("NA", "101", receipt(1, battle=1))
        self.wallet.upsert_receipt("NA", "101", receipt(2, included=True, battle=1,
                                                  occurred="2026-10-20T12:00:00Z"))
        selected = self.query()
        self.assertEqual(selected["external_credits"], 0)
        self.assertEqual(selected["external_rewards"], [])
        self.assertEqual(selected["history"][0]["rewards"][0]["name"], "Crisol")


if __name__ == "__main__":
    unittest.main()
