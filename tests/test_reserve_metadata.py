# -*- coding: utf-8 -*-
"""Reserve components are attribution inside gross, never another credit gain."""
import copy
import unittest

from capture.history import reset_history_config
from capture.native import POLICY
from capture.normalizer import ReconciliationError, normalize_snapshot
from capture.presentation import build_payload
from capture.wallet import WalletBook
from core import EconomyLedger, LedgerValidationError


def result(battle="1", reserves=None, account="101", region="NA",
           occurred_at="2026-10-18T12:00:00Z", status="final"):
    record = {"region": region, "account_id": account, "battle_id": battle,
              "occurred_at": occurred_at, "status": status,
              "credits": {"gross": 100000, "expenses": {
                  "repair": 10000, "ammo": 20000, "consumables": 5000, "other": 0}}}
    if reserves is not None:
        record["credits"]["reserves"] = reserves
    return record


def snapshot(reserves=None):
    totals = {"gross": 100000, "repair": 10000, "ammo": 20000,
              "consumables": 5000, "other": 0, "net": 65000}
    value = {"region": "NA", "account_id": "101", "battle_id": "1",
             "captured_at": "2026-10-18T12:00:00Z", "personal": {"vehicles": []},
             "native_credits": {"policy": POLICY, "row_kind": "aggregate",
                                "totals": totals, "rows": [copy.deepcopy(totals)]}}
    if reserves is not None:
        value["native_credits"]["reserves"] = reserves
    return value


class ReserveLedgerTests(unittest.TestCase):
    def test_legacy_unknown_and_verified_zero_remain_distinct_after_round_trip(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result("unknown"))
        ledger.upsert_result(result("zero", {"personal": 0, "clan": 0}))
        loaded = EconomyLedger.from_dict(ledger.to_dict())
        records = dict((row["battle_id"], row) for row in loaded.list_results())
        self.assertNotIn("reserves", records["unknown"]["credits"])
        self.assertEqual(records["zero"]["credits"]["reserves"], {"personal": 0, "clan": 0})
        self.assertEqual(loaded.summary("NA", "101")["reserves"],
                         {"personal": 0, "clan": 0, "known_battles": 1, "total_battles": 2})

    def test_both_components_are_subtotals_and_do_not_change_money_or_goal(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result(reserves={"personal": 20000, "clan": 10000}))
        totals = ledger.summary("NA", "101")
        self.assertEqual(totals["reserves"],
                         {"personal": 20000, "clan": 10000, "known_battles": 1, "total_battles": 1})
        self.assertEqual((totals["gross_credits"], totals["total_expenses"], totals["net_credits"]),
                         (100000, 35000, 65000))
        self.assertEqual(ledger.goal_status({"region": "NA", "account_id": "101",
            "mode": "net_earnings", "target": 100000,
            "since_utc": "2026-10-18T00:00:00Z"})["current"], 65000)

    def test_repeated_result_and_corrected_components_replace_without_double_counting(self):
        ledger = EconomyLedger()
        initial = result(reserves={"personal": 20000, "clan": 10000})
        self.assertEqual(ledger.upsert_result(initial), "inserted")
        self.assertEqual(ledger.upsert_result(initial), "unchanged")
        self.assertEqual(ledger.upsert_result(result(reserves={"personal": 15000, "clan": 25000})), "updated")
        self.assertEqual(ledger.summary("NA", "101")["reserves"],
                         {"personal": 15000, "clan": 25000, "known_battles": 1, "total_battles": 1})
        # A corrected final with no verified breakdown must not retain stale attribution.
        ledger.upsert_result(result())
        self.assertEqual(ledger.summary("NA", "101")["reserves"]["known_battles"], 0)
        self.assertEqual(ledger.summary("NA", "101")["net_credits"], 65000)

    def test_pending_other_account_region_and_before_cutoff_are_not_summed(self):
        ledger = EconomyLedger()
        for row in (result("current", {"personal": 1000, "clan": 2000}),
                    result("pending", {"personal": 3000, "clan": 4000}, status="pending"),
                    result("other", {"personal": 5000, "clan": 6000}, account="202"),
                    result("region", {"personal": 5000, "clan": 6000}, region="EU"),
                    result("old", {"personal": 7000, "clan": 8000}, occurred_at="2026-10-17T23:59:59Z")):
            ledger.upsert_result(row)
        summary = ledger.summary("NA", "101", "2026-10-18T00:00:00Z")
        self.assertEqual(summary["reserves"],
                         {"personal": 1000, "clan": 2000, "known_battles": 1, "total_battles": 1})
        self.assertEqual(summary["pending_battles"], 1)

    def test_reserve_amounts_and_shape_are_strictly_validated(self):
        bad = [None, [], {}, {"personal": 1}, {"personal": 1, "clan": 2, "other": 3},
               {"personal": 100000, "clan": 1}]
        bad.extend({"personal": amount, "clan": 0} for amount in (True, False, -1, 1.0, "1"))
        bad.extend({"personal": 0, "clan": amount} for amount in (True, -1, 1.5, "1"))
        for reserves in bad:
            row = result()
            row["credits"]["reserves"] = reserves
            with self.subTest(reserves=reserves):
                with self.assertRaises(LedgerValidationError):
                    EconomyLedger().upsert_result(row)

    def test_incoming_and_summary_components_are_defensive_copies(self):
        ledger = EconomyLedger()
        incoming = result(reserves={"personal": 1000, "clan": 2000})
        ledger.upsert_result(incoming)
        incoming["credits"]["reserves"]["personal"] = 999
        ledger.list_results()[0]["credits"]["reserves"]["clan"] = 999
        ledger.summary("NA", "101")["reserves"]["personal"] = 999
        self.assertEqual(ledger.summary("NA", "101")["reserves"]["personal"], 1000)
        self.assertEqual(ledger.summary("NA", "101")["reserves"]["clan"], 2000)


class ReserveNormalizerTests(unittest.TestCase):
    def test_optional_native_components_are_copied_and_finance_is_unchanged(self):
        self.assertNotIn("reserves", normalize_snapshot(snapshot())["credits"])
        native = snapshot({"personal": 20000, "clan": 10000})
        original = copy.deepcopy(native)
        record = normalize_snapshot(native)
        self.assertEqual(native, original)
        self.assertEqual(record["credits"]["gross"], 100000)
        self.assertEqual(record["credits"]["reserves"], {"personal": 20000, "clan": 10000})
        record["credits"]["reserves"]["personal"] = 1
        self.assertEqual(native["native_credits"]["reserves"]["personal"], 20000)

    def test_native_verified_zero_is_not_omitted(self):
        self.assertEqual(normalize_snapshot(snapshot({"personal": 0, "clan": 0}))["credits"]["reserves"],
                         {"personal": 0, "clan": 0})

    def test_invalid_native_components_are_not_silently_changed_to_zero(self):
        for reserves in (None, {}, [], {"personal": 1}, {"personal": 1, "clan": 1, "x": 0},
                         {"personal": True, "clan": 0}, {"personal": 1.0, "clan": 0},
                         {"personal": "1", "clan": 0}, {"personal": -1, "clan": 0},
                         {"personal": 0, "clan": False}, {"personal": 0, "clan": -1},
                         {"personal": 100000, "clan": 1}):
            native = snapshot()
            native["native_credits"]["reserves"] = reserves
            with self.subTest(reserves=reserves):
                with self.assertRaises(ReconciliationError):
                    normalize_snapshot(native)

    def test_multiple_own_vehicles_still_use_one_aggregate_reserve_breakdown(self):
        native = snapshot({"personal": 20000, "clan": 10000})
        native["personal"]["vehicles"] = [
            {"vehicle_type_id": "321", "name": "XM57", "tier": 8, "icon": None},
            {"vehicle_type_id": "654", "name": "Pz. Neu", "tier": 11, "icon": None}]
        ledger = EconomyLedger()
        ledger.upsert_result(normalize_snapshot(native))
        self.assertEqual(len(ledger.list_results()[0]["vehicles"]), 2)
        self.assertEqual(ledger.summary("NA", "101")["reserves"],
                         {"personal": 20000, "clan": 10000, "known_battles": 1, "total_battles": 1})
        self.assertEqual(ledger.summary("NA", "101")["net_credits"], 65000)


class ReservePresentationTests(unittest.TestCase):
    def test_history_unknown_is_null_and_verified_zero_is_an_object(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result("1"))
        ledger.upsert_result(result("2", {"personal": 0, "clan": 0}))
        payload = build_payload(ledger, "NA", "101", {}, 22000000)
        by_id = dict((row["battle_id"], row) for row in payload["history"])
        self.assertIsNone(by_id["1"]["reserves"])
        self.assertEqual(by_id["2"]["reserves"], {"personal": 0, "clan": 0})
        by_id["2"]["reserves"]["personal"] = 99
        self.assertEqual(ledger.list_results()[1]["credits"]["reserves"]["personal"], 0)

    def test_period_sum_includes_battles_beyond_the_100_row_picker_limit(self):
        ledger = EconomyLedger()
        for number in range(105):
            ledger.upsert_result(result(str(number), {"personal": 1000, "clan": 2000}))
        ledger.upsert_result(result("other", {"personal": 80000, "clan": 0}, account="202"))
        payload = build_payload(ledger, "NA", "101", {}, 22000000)
        self.assertEqual(len(payload["history"]), 100)
        self.assertEqual(payload["summary"]["reserves"],
                         {"personal": 105000, "clan": 210000, "known_battles": 105, "total_battles": 105})

    def test_reset_hides_old_components_without_erasing_audit_records(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result("old", {"personal": 10000, "clan": 20000}))
        config = reset_history_config({}, "NA", "101", 22000000,
                                      "2026-10-18T13:00:00Z", ["old"], [])
        ledger.upsert_result(result("new", {"personal": 3000, "clan": 4000},
                                    occurred_at="2026-10-18T14:00:00Z"))
        payload = build_payload(ledger, "NA", "101", config, 22065000)
        self.assertEqual(payload["summary"]["reserves"],
                         {"personal": 3000, "clan": 4000, "known_battles": 1, "total_battles": 1})
        self.assertEqual([row["battle_id"] for row in payload["history"]], ["new"])
        self.assertEqual(len(ledger.list_results()), 2)

    def test_wallet_and_balance_goal_do_not_add_components_a_second_time(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result(reserves={"personal": 20000, "clan": 10000}))
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, "2026-10-18T11:00:00Z")
        wallet.observe("NA", "101", 22065000, "2026-10-18T13:00:00Z")
        config = {"account_goals": {"NA:101": {"mode": "balance_growth", "target": 100000,
                  "baseline": 22000000, "since_utc": "2026-10-18T11:00:00Z"}}}
        payload = build_payload(ledger, "NA", "101", config, 22065000, wallet=wallet)
        self.assertEqual(payload["goal"]["current"], 65000)
        self.assertEqual(payload["goal"]["remaining"], 35000)
        self.assertEqual(payload["wallet"]["battle_net"], 65000)
        self.assertEqual(payload["wallet"]["external_credits"], 0)
        self.assertEqual(payload["wallet"]["unclassified"], 0)

    def test_waiting_for_account_reports_empty_reserve_coverage(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result(reserves={"personal": 20000, "clan": 10000}))
        payload = build_payload(ledger, "NA", None, {}, None)
        self.assertEqual(payload["summary"]["reserves"],
                         {"personal": 0, "clan": 0, "known_battles": 0, "total_battles": 0})


if __name__ == "__main__":
    unittest.main()
