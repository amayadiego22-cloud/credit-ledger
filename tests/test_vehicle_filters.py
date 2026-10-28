# -*- coding: utf-8 -*-
"""Tank filters use native identity and the whole visible accounting period."""
import copy
import datetime
import unittest

from capture.history import reset_history_config
from capture.presentation import build_payload
from capture.wallet import WalletBook
from core import EconomyLedger
from timezone_fixtures import mock_local_timezone


START = "2026-10-18T12:00:00Z"
ICON = "coui://gui/maps/icons/vehicle/usa-A01_T1_Cunningham.png"
ZERO_EXPENSES = {"repair": 0, "ammo": 0, "consumables": 0, "other": 0}


def vehicle(identity="321", name="XM57", tier=8, icon=ICON):
    return {"vehicle_type_id": str(identity), "name": name, "tier": tier, "icon": icon}


def result(number, tank="321", mode=1, gross=100000, expenses=None, reserves=None,
           account="101", region="NA", status="final", tanks=None):
    when = datetime.datetime(2026, 10, 18, 12) + datetime.timedelta(minutes=number)
    row = {"region": region, "account_id": account, "battle_id": str(number),
           "occurred_at": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": status,
           "credits": {"gross": gross, "expenses": expenses if expenses is not None else {
               "repair": 10000, "ammo": 20000, "consumables": 5000, "other": 0}}}
    row["vehicles"] = tanks if tanks is not None else ([vehicle(tank)] if tank is not None else [])
    if mode is not None:
        row["battle_mode"] = {"bonus_type": mode}
    if reserves is not None:
        row["credits"]["reserves"] = reserves
    return row


class VehicleFilterTests(unittest.TestCase):
    def setUp(self):
        clock = mock_local_timezone("America/Bogota")
        clock.__enter__()
        self.addCleanup(clock.__exit__, None, None, None)
        self.ledger = EconomyLedger()

    def payload(self, config=None, balance=22000000, **kwargs):
        return build_payload(self.ledger, "NA", "101", config or {}, balance,
                             now_utc="2026-10-19T12:00:00Z", **kwargs)

    def groups(self, payload=None, mode="all"):
        current = self.payload() if payload is None else payload
        context = current if mode == "all" else next(
            group for group in current["mode_groups"] if group["key"] == mode)
        return dict((group["key"], group) for group in context["vehicle_groups"])

    def selection(self, key="vehicle:321", mode="all", request_id=7, **kwargs):
        return self.payload(vehicle_filter={"mode_key": mode, "vehicle_key": key,
                            "request_id": request_id}, **kwargs)["vehicle_selection"]

    def test_empty_and_waiting_accounts_have_no_invented_tanks_or_selection(self):
        current = self.payload()
        self.assertEqual(current["vehicle_groups"], [])
        self.assertIsNone(current["vehicle_selection"])
        self.assertTrue(all(group["vehicle_groups"] == [] for group in current["mode_groups"]))
        self.ledger.upsert_result(result(1))
        waiting = build_payload(self.ledger, "NA", None, {}, None,
            vehicle_filter={"vehicle_key": "vehicle:321", "request_id": 9})
        self.assertEqual(waiting["vehicle_groups"], [])
        self.assertIsNone(waiting["vehicle_selection"])

    def test_native_id_keeps_same_names_separate_and_ignores_name_or_tier_changes(self):
        self.ledger.upsert_result(result(1, tanks=[vehicle("0321", "Same name", 8)]))
        self.ledger.upsert_result(result(2, tanks=[vehicle("654", "Same name", 8)]))
        self.ledger.upsert_result(result(3, tanks=[vehicle("321", "New name", 9)]))
        groups = self.groups()
        self.assertEqual(set(groups), {"vehicle:321", "vehicle:654"})
        self.assertEqual(groups["vehicle:321"]["history_total"], 2)
        self.assertEqual(groups["vehicle:321"]["label"], "New name")
        self.assertEqual(groups["vehicle:321"]["vehicle"], vehicle("321", "New name", 9))
        self.assertEqual(groups["vehicle:654"]["history_total"], 1)

    def test_ranking_uses_net_total_descending_with_count_name_and_id_ties(self):
        for row in (result(1, "100", gross=70000), result(2, "100", gross=70000),
                    result(3, "200", gross=100000), result(4, "300", gross=35000),
                    result(5, "400", gross=20000), result(6, "500", gross=10000)):
            self.ledger.upsert_result(row)
        current = self.payload()
        self.assertEqual([group["key"] for group in current["vehicle_groups"]],
                         ["vehicle:100", "vehicle:200", "vehicle:300", "vehicle:400", "vehicle:500"])
        groups = self.groups(current)
        self.assertEqual(groups["vehicle:100"]["summary"]["average_net_credits"], 35000)
        self.assertEqual(groups["vehicle:200"]["summary"]["net_credits"], 65000)
        self.assertEqual(groups["vehicle:400"]["summary"]["average_net_credits"], -15000)
        self.assertTrue(all(group["rankable"] for group in current["vehicle_groups"]))
        for identity, name in (("700", "Alpha"), ("600", "Alpha"), ("800", "Zulu")):
            self.ledger.upsert_result(result(int(identity), gross=70000,
                                             tanks=[vehicle(identity, name)]))
        tied = [group["key"] for group in self.payload()["vehicle_groups"]
                if group["summary"]["net_credits"] == 35000]
        self.assertEqual(tied, ["vehicle:600", "vehicle:700", "vehicle:800"])

    def test_same_tank_can_be_filtered_across_all_modes_or_with_one_exact_mode(self):
        for row in (result(1, mode=1, gross=80000), result(2, mode=20, gross=20000),
                    result(3, mode=43, gross=110000), result(4, tank="654", mode=20)):
            self.ledger.upsert_result(row)
        self.assertEqual(self.groups()["vehicle:321"]["summary"]["net_credits"], 105000)
        selection = self.selection(mode="mode:20", request_id=42)
        self.assertTrue(selection["available"])
        self.assertEqual((selection["mode_key"], selection["vehicle_key"], selection["request_id"]),
                         ("mode:20", "vehicle:321", 42))
        self.assertEqual(selection["history_total"], 1)
        self.assertEqual(selection["summary"]["net_credits"], -15000)
        self.assertEqual([row["battle_id"] for row in selection["history"]], ["2"])
        self.assertEqual(self.groups(mode="mode:20")["vehicle:321"]["summary"], selection["summary"])
        self.assertEqual(self.selection()["history_total"], 3)

    def test_tank_selection_recovers_older_rows_outside_global_and_mode_picker_caps(self):
        self.ledger.upsert_result(result(1, mode=20, gross=80000))
        for number in range(2, 110):
            self.ledger.upsert_result(result(number, "654", mode=20))
        current = self.payload()
        self.assertNotIn("1", [row["battle_id"] for row in current["history"]])
        mode = next(group for group in current["mode_groups"] if group["key"] == "mode:20")
        self.assertNotIn("1", [row["battle_id"] for row in mode["history"]])
        selected = self.selection(mode="mode:20")
        self.assertEqual(selected["history"][0]["battle_id"], "1")
        self.assertEqual(selected["summary"]["net_credits"], 45000)
        self.assertEqual(self.selection()["history"], selected["history"])

    def test_more_than_100_tank_battles_use_full_totals_reserves_and_resources(self):
        for number in range(130):
            row = result(number, mode=43, reserves={"personal": 1000, "clan": 2000})
            row["resources"] = {"bonds": {"earned": 4, "spent": 1}}
            self.ledger.upsert_result(row)
        selected = self.selection(mode="mode:43")
        self.assertEqual((len(selected["history"]), selected["history_total"]), (100, 130))
        self.assertEqual([selected["history"][0]["battle_id"], selected["history"][-1]["battle_id"]],
                         ["129", "30"])
        self.assertEqual(selected["summary"]["net_credits"], 130 * 65000)
        self.assertEqual(selected["summary"]["gross_credits"], 130 * 100000)
        self.assertEqual(selected["summary"]["reserves"],
                         {"personal": 130000, "clan": 260000, "known_battles": 130, "total_battles": 130})
        self.assertEqual(selected["summary"]["resources"]["bonds"]["net"], 390)

    def test_partial_reserve_metadata_is_never_inferred_or_added_again(self):
        self.ledger.upsert_result(result(1))
        self.ledger.upsert_result(result(2, reserves={"personal": 0, "clan": 0}))
        self.ledger.upsert_result(result(3, reserves={"personal": 3000, "clan": 4000}))
        selected = self.selection()
        self.assertEqual(selected["summary"]["reserves"],
                         {"personal": 3000, "clan": 4000, "known_battles": 2, "total_battles": 3})
        self.assertEqual(selected["summary"]["net_credits"], 195000)
        self.assertIsNone(selected["history"][-1]["reserves"])
        self.assertEqual(selected["history"][1]["reserves"], {"personal": 0, "clan": 0})

    def test_unknown_and_multi_tank_native_aggregates_have_one_unranked_bucket_each(self):
        for row in (result(1), result(2, tank=None, gross=20000),
                    result(3, gross=900000, tanks=[vehicle(), vehicle("654")])):
            self.ledger.upsert_result(row)
        current = self.payload()
        groups = self.groups(current)
        self.assertEqual(set(groups), {"vehicle:321", "unknown", "multiple"})
        self.assertNotIn("vehicle:654", groups)
        self.assertEqual(groups["vehicle:321"]["summary"]["net_credits"], 65000)
        self.assertEqual(groups["multiple"]["summary"]["net_credits"], 865000)
        self.assertEqual(groups["multiple"]["label"], u"Varios veh\u00edculos")
        for key in ("unknown", "multiple"):
            self.assertIsNone(groups[key]["vehicle"])
            self.assertFalse(groups[key]["rankable"])
        self.assertEqual(current["vehicle_groups"][0]["key"], "vehicle:321")
        for field in ("gross_credits", "total_expenses", "net_credits", "battle_count"):
            self.assertEqual(sum(group["summary"][field] for group in groups.values()), current["summary"][field])
        self.assertEqual(self.selection("unknown")["history"][0]["battle_id"], "2")
        self.assertEqual(self.selection("multiple")["history"][0]["battle_id"], "3")

    def test_pending_tanks_never_affect_income_history_or_profitable_ranking(self):
        self.ledger.upsert_result(result(1, status="pending"))
        self.ledger.upsert_result(result(2, tank=None, status="pending"))
        self.ledger.upsert_result(result(3, tank="654", gross=10000))
        current = self.payload(pending_count=4)
        groups = self.groups(current)
        self.assertEqual(current["summary"]["pending_battles"], 6)
        self.assertEqual(groups["vehicle:321"]["summary"]["pending_battles"], 1)
        self.assertFalse(groups["vehicle:321"]["rankable"])
        self.assertEqual(current["vehicle_groups"][0]["key"], "vehicle:654")
        selected = self.selection()
        self.assertTrue(selected["available"])
        self.assertEqual(selected["history"], [])
        self.assertEqual(selected["history_total"], 0)
        self.assertEqual(selected["summary"]["net_credits"], 0)
        self.assertEqual(sum(group["summary"]["pending_battles"] for group in groups.values()), 2)

    def test_vehicle_groups_are_scoped_to_account_and_region(self):
        self.ledger.upsert_result(result(1, tank="321"))
        self.ledger.upsert_result(result(2, tank="654", account="202"))
        self.ledger.upsert_result(result(3, tank="987", region="EU"))
        self.assertEqual(set(self.groups()), {"vehicle:321"})
        other = build_payload(self.ledger, "NA", "202", {}, 0,
            vehicle_filter={"mode_key": "all", "vehicle_key": "vehicle:321", "request_id": 9})
        self.assertEqual([group["key"] for group in other["vehicle_groups"]], ["vehicle:654"])
        self.assertFalse(other["vehicle_selection"]["available"])
        self.assertEqual(other["vehicle_selection"]["history"], [])

    def test_history_reset_projection_applies_before_vehicle_totals_and_ranking(self):
        for row in (result(1, "321"), result(2, "654"), result(3, "321")):
            self.ledger.upsert_result(row)
        config = reset_history_config({}, "NA", "101", 22000000,
            "2026-10-18T12:01:30Z", ["1", "3"], [])
        original = self.ledger.to_dict()
        current = self.payload(config)
        self.assertEqual(set(self.groups(current)), {"vehicle:654"})
        self.assertEqual(self.selection("vehicle:654", config=config)["history_total"], 1)
        self.assertFalse(self.selection(config=config)["available"])
        self.assertEqual(self.ledger.to_dict(), original)

    def test_retries_and_corrected_vehicle_or_mode_replace_without_double_counting(self):
        first = result(1, "321", mode=20)
        self.ledger.upsert_result(first)
        self.ledger.upsert_result(first)
        self.assertEqual(self.selection()["history_total"], 1)
        self.ledger.upsert_result(result(1, "654", mode=43, gross=90000))
        self.assertEqual(set(self.groups()), {"vehicle:654"})
        self.assertFalse(self.selection(mode="mode:20")["available"])
        self.assertEqual(self.selection("vehicle:654", "mode:43")["summary"]["net_credits"], 55000)

    def test_latest_name_and_older_optional_metadata_combine_without_financial_changes(self):
        self.ledger.upsert_result(result(1, tanks=[vehicle("321", "Resolved name", 8)]))
        self.ledger.upsert_result(result(2, tanks=[vehicle("321", u"Veh\u00edculo 321", None, None)]))
        group = self.groups()["vehicle:321"]
        self.assertEqual(group["vehicle"], vehicle("321", "Resolved name", 8))
        self.assertEqual(group["label"], "Resolved name")
        self.assertEqual(group["summary"]["net_credits"], 130000)
        self.ledger.upsert_result(result(3, tanks=[vehicle("321", "New native name", 9, None)]))
        self.assertEqual(self.groups()["vehicle:321"]["vehicle"], vehicle("321", "New native name", 9))

    def test_missing_modes_and_same_label_modes_stay_distinct_in_vehicle_selection(self):
        for number, mode in enumerate((None, 4, 5), start=1):
            self.ledger.upsert_result(result(number, mode=mode))
        self.assertEqual(self.selection(mode="unknown")["history"][0]["battle_id"], "1")
        self.assertEqual(self.selection(mode="mode:4")["history"][0]["battle_id"], "2")
        self.assertEqual(self.selection(mode="mode:5")["history"][0]["battle_id"], "3")
        self.assertEqual(self.selection()["history_total"], 3)

    def test_invalid_or_disappeared_selection_echoes_request_without_returning_global_history(self):
        self.ledger.upsert_result(result(1))
        for key, mode in (("vehicle:999", "all"), ("vehicle:321", "mode:999"), ("unknown", "mode:20")):
            selected = self.selection(key, mode, request_id=42)
            self.assertFalse(selected["available"])
            self.assertEqual((selected["mode_key"], selected["vehicle_key"], selected["request_id"]), (mode, key, 42))
            self.assertEqual(selected["history"], [])
            self.assertEqual(selected["history_total"], 0)
            self.assertEqual(selected["summary"]["net_credits"], 0)
        self.assertIsNone(self.payload(vehicle_filter="invalid")["vehicle_selection"])
        self.assertIsNone(self.payload(vehicle_filter={"vehicle_key": "all"})["vehicle_selection"])

    def test_rows_and_summaries_have_defensive_copies_and_keep_reward_annotations(self):
        row = result(1, mode=20, reserves={"personal": 1000, "clan": 2000})
        self.ledger.upsert_result(row)
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, START)
        receipt = {"id": "battleResults:1", "kind": "battleResults", "occurred_at": row["occurred_at"],
            "battle_id": "1", "credits": 1000, "included_in_battle": True, "title": u"Misiones de la partida",
            "parts": [{"quest_id": "quest", "title": "Crisol", "credits": 1000, "name_resolved": True}]}
        wallet.upsert_receipt("NA", "101", receipt)
        original = copy.deepcopy((self.ledger.to_dict(), wallet.data))
        current = self.payload(wallet=wallet, vehicle_filter={"mode_key": "mode:20",
                               "vehicle_key": "vehicle:321", "request_id": 1})
        selected = current["vehicle_selection"]
        self.assertEqual(selected["history"][0], current["history"][0])
        self.assertEqual(selected["history"][0]["time_label"], "18/10 07:01")
        self.assertEqual(selected["history"][0]["rewards"], receipt["parts"])
        selected["summary"]["expenses"]["repair"] = 99
        selected["history"][0]["vehicles"][0]["name"] = "changed"
        selected["history"][0]["expenses"]["repair"] = 99
        selected["history"][0]["reserves"]["clan"] = 99
        selected["history"][0]["rewards"][0]["title"] = "changed"
        self.assertEqual(self.groups(current, "mode:20")["vehicle:321"]["summary"]["expenses"]["repair"], 10000)
        self.assertEqual(current["history"][0]["vehicles"][0]["name"], "XM57")
        self.assertEqual(current["history"][0]["rewards"][0]["title"], "Crisol")
        self.assertEqual((self.ledger.to_dict(), wallet.data), original)

    def test_filtering_does_not_change_global_goal_balance_wallet_or_external_rewards(self):
        for row in (result(1, "321", 1), result(2, "321", 20, gross=20000), result(3, "654", 43)):
            self.ledger.upsert_result(row)
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, START)
        receipt = {"id": "tokenQuests:1", "kind": "tokenQuests", "occurred_at": "2026-10-18T12:10:00Z",
            "battle_id": None, "credits": 100000, "included_in_battle": False, "title": "Crisol", "parts": []}
        wallet.upsert_receipt("NA", "101", receipt)
        config = {"account_goals": {"NA:101": {"mode": "balance_growth", "target": 1000000,
                  "baseline": 22000000, "since_utc": START}}}
        original = copy.deepcopy((self.ledger.to_dict(), wallet.data, config))
        all_data = self.payload(config, balance=22215000, wallet=wallet)
        selected = self.payload(config, balance=22215000, wallet=wallet,
            vehicle_filter={"mode_key": "mode:20", "vehicle_key": "vehicle:321", "request_id": 7})
        for field in ("summary", "goal", "balance", "wallet", "rewards", "history", "mode_groups", "vehicle_groups"):
            self.assertEqual(selected[field], all_data[field])
        self.assertEqual(selected["vehicle_selection"]["summary"]["net_credits"], -15000)
        self.assertEqual(selected["goal"]["current"], 215000)
        self.assertEqual(selected["wallet"]["external_credits"], 100000)
        self.assertEqual(selected["wallet"]["unclassified"], 0)
        self.assertEqual((self.ledger.to_dict(), wallet.data, config), original)

    def test_many_tanks_have_compact_groups_and_only_one_requested_history(self):
        for number in range(120):
            self.ledger.upsert_result(result(number, tank=str(1000 + number), mode=(1 if number % 2 else 20)))
        current = self.payload(vehicle_filter={"mode_key": "all", "vehicle_key": "vehicle:1001", "request_id": 7})
        self.assertEqual(len(current["vehicle_groups"]), 120)
        for context in [current] + current["mode_groups"]:
            for group in context["vehicle_groups"]:
                self.assertNotIn("history", group)
        self.assertEqual(len(current["vehicle_selection"]["history"]), 1)
        self.assertEqual(current["vehicle_selection"]["history"][0]["battle_id"], "1")


if __name__ == "__main__":
    unittest.main()
