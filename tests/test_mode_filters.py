# -*- coding: utf-8 -*-
"""Mode totals use the whole visible period, independently of picker limits."""
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


def result(number, mode=1, gross=100000, expenses=None, reserves=None,
           account="101", region="NA", status="final", minute=None):
    when = datetime.datetime(2026, 10, 18, 12) + datetime.timedelta(
        minutes=number if minute is None else minute)
    row = {"region": region, "account_id": account, "battle_id": str(number),
           "occurred_at": when.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": status,
           "credits": {"gross": gross, "expenses": expenses or {
               "repair": 10000, "ammo": 20000, "consumables": 5000, "other": 0}}}
    if mode is not None:
        row["battle_mode"] = {"bonus_type": mode}
    if reserves is not None:
        row["credits"]["reserves"] = reserves
    return row


class ModeFilterTests(unittest.TestCase):
    def setUp(self):
        clock = mock_local_timezone("America/Bogota")
        clock.__enter__()
        self.addCleanup(clock.__exit__, None, None, None)
        self.ledger = EconomyLedger()

    def payload(self, config=None, balance=22000000, **kwargs):
        return build_payload(self.ledger, "NA", "101", config or {}, balance,
                             now_utc="2026-10-19T12:00:00Z", **kwargs)

    def groups(self, payload=None):
        return dict((group["key"], group) for group in
                    (self.payload() if payload is None else payload)["mode_groups"])

    def test_three_requested_modes_are_available_with_zero_results(self):
        payload = self.payload()
        self.assertEqual([group["key"] for group in payload["mode_groups"]],
                         ["mode:1", "mode:20", "mode:43"])
        self.assertEqual([group["label"] for group in payload["mode_groups"]],
                         [u"Batalla aleatoria", u"Escaramuza", u"Asedio"])
        for group in payload["mode_groups"]:
            self.assertEqual(group["history"], [])
            self.assertEqual(group["history_total"], 0)
            self.assertEqual(group["summary"], self.ledger.summary("NA", "101"))

    def test_account_context_changes_without_exposing_a_waiting_accounts_history(self):
        self.ledger.upsert_result(result(1, 20))
        waiting = build_payload(self.ledger, "NA", None, {}, None)
        self.assertIsNone(waiting["account_context"])
        self.assertEqual(waiting["mode_groups"], [])
        self.assertEqual(self.payload()["account_context"], "NA:101")
        other = build_payload(self.ledger, "NA", "202", {}, 0)
        self.assertEqual(other["account_context"], "NA:202")
        self.assertTrue(all(group["history_total"] == 0 for group in other["mode_groups"]))

    def test_each_native_mode_has_its_own_complete_financial_summary(self):
        for row in (result(1, 1, gross=80000), result(2, 20, gross=20000),
                    result(3, 43, gross=110000), result(4, 21, gross=40000)):
            self.ledger.upsert_result(row)
        payload = self.payload()
        groups = self.groups(payload)
        self.assertEqual(groups["mode:1"]["summary"]["net_credits"], 45000)
        self.assertEqual(groups["mode:20"]["summary"]["net_credits"], -15000)
        self.assertEqual(groups["mode:43"]["summary"]["net_credits"], 75000)
        self.assertEqual(groups["mode:21"]["summary"]["net_credits"], 5000)
        for field in ("gross_credits", "total_expenses", "net_credits", "battle_count"):
            self.assertEqual(sum(group["summary"][field] for group in groups.values()),
                             payload["summary"][field])

    def test_older_selected_mode_is_available_beyond_100_newer_other_modes(self):
        self.ledger.upsert_result(result(1, 20, gross=80000))
        for number in range(2, 108):
            self.ledger.upsert_result(result(number, 1))
        payload = self.payload()
        self.assertEqual(len(payload["history"]), 100)
        self.assertNotIn("1", [row["battle_id"] for row in payload["history"]])
        group = self.groups(payload)["mode:20"]
        self.assertEqual(group["history_total"], 1)
        self.assertEqual(group["history"][0]["battle_id"], "1")
        self.assertEqual(group["summary"]["net_credits"], 45000)

    def test_totals_resources_and_reserves_include_more_than_100_battles_in_one_mode(self):
        for number in range(130):
            row = result(number, 43, reserves={"personal": 1000, "clan": 2000})
            row["resources"] = {"bonds": {"earned": 4, "spent": 1}}
            self.ledger.upsert_result(row)
        group = self.groups()["mode:43"]
        self.assertEqual(len(group["history"]), 100)
        self.assertEqual(group["history"][0]["battle_id"], "129")
        self.assertEqual(group["history"][-1]["battle_id"], "30")
        self.assertEqual(group["history_total"], 130)
        self.assertEqual(group["summary"]["net_credits"], 130 * 65000)
        self.assertEqual(group["summary"]["gross_credits"], 130 * 100000)
        self.assertEqual(group["summary"]["expenses"],
                         {"repair": 1300000, "ammo": 2600000, "consumables": 650000, "other": 0})
        self.assertEqual(group["summary"]["reserves"],
                         {"personal": 130000, "clan": 260000, "known_battles": 130, "total_battles": 130})
        self.assertEqual(group["summary"]["resources"]["bonds"]["net"], 390)

    def test_partial_reserve_coverage_preserves_unknown_versus_verified_zero(self):
        self.ledger.upsert_result(result(1, 20))
        self.ledger.upsert_result(result(2, 20, reserves={"personal": 0, "clan": 0}))
        self.ledger.upsert_result(result(3, 20, reserves={"personal": 3000, "clan": 4000}))
        self.ledger.upsert_result(result(4, 1, reserves={"personal": 5000, "clan": 6000}))
        group = self.groups()["mode:20"]
        self.assertEqual(group["summary"]["reserves"],
                         {"personal": 3000, "clan": 4000, "known_battles": 2, "total_battles": 3})
        self.assertIsNone(group["history"][-1]["reserves"])
        self.assertEqual(group["history"][1]["reserves"], {"personal": 0, "clan": 0})
        self.assertEqual(group["summary"]["net_credits"], 3 * 65000)

    def test_missing_unknown_numeric_and_same_label_modes_keep_distinct_identities(self):
        for number, mode in enumerate((None, 0, 2147483647, 4, 5), start=1):
            self.ledger.upsert_result(result(number, mode))
        groups = self.groups()
        self.assertEqual(groups["unknown"]["label"], u"Modo no identificado")
        self.assertEqual(groups["mode:0"]["label"], u"Modo no identificado (código 0)")
        self.assertEqual(groups["mode:2147483647"]["label"],
                         u"Modo no identificado (código 2147483647)")
        self.assertEqual(groups["mode:4"]["label"], groups["mode:5"]["label"])
        for key in ("unknown", "mode:0", "mode:2147483647", "mode:4", "mode:5"):
            self.assertEqual(groups[key]["history_total"], 1)
        self.assertIsNone(groups["unknown"]["history"][0]["battle_mode"])

    def test_gui_type_never_changes_the_bonus_type_group(self):
        row = result(1, 20)
        row["battle_mode"]["gui_type"] = 43
        self.ledger.upsert_result(row)
        groups = self.groups()
        self.assertEqual(groups["mode:20"]["history_total"], 1)
        self.assertEqual(groups["mode:43"]["history_total"], 0)
        self.assertEqual(groups["mode:20"]["history"][0]["battle_mode"]["gui_type"], 43)

    def test_pending_counts_use_known_mode_and_never_enter_final_history_or_income(self):
        self.ledger.upsert_result(result(1, 20, status="pending"))
        self.ledger.upsert_result(result(2, None, status="pending"))
        self.ledger.upsert_result(result(3, 43))
        payload = self.payload(pending_count=4)
        groups = self.groups(payload)
        self.assertEqual(payload["summary"]["pending_battles"], 6)
        self.assertEqual(groups["mode:20"]["summary"]["pending_battles"], 1)
        self.assertEqual(groups["unknown"]["summary"]["pending_battles"], 1)
        self.assertEqual(groups["mode:20"]["summary"]["net_credits"], 0)
        self.assertEqual(groups["mode:20"]["history"], [])
        self.assertEqual(groups["unknown"]["history"], [])

    def test_history_reset_accounts_and_regions_apply_before_grouping(self):
        for row in (result(1, 20), result(2, 43), result(3, 20),
                    result(4, 43, account="202"), result(5, 20, region="EU")):
            self.ledger.upsert_result(row)
        config = reset_history_config({}, "NA", "101", 22000000,
            "2026-10-18T12:01:30Z", ["1", "3"], [])
        original = self.ledger.to_dict()
        payload = self.payload(config)
        groups = self.groups(payload)
        self.assertEqual(groups["mode:20"]["history_total"], 0)
        self.assertEqual(groups["mode:43"]["history_total"], 1)
        self.assertEqual(groups["mode:43"]["history"][0]["battle_id"], "2")
        self.assertEqual(payload["summary"]["battle_count"], 1)
        self.assertEqual(self.ledger.to_dict(), original)

    def test_repeated_result_and_corrected_mode_replace_one_group_instead_of_adding(self):
        first = result(1, 20)
        self.ledger.upsert_result(first)
        self.ledger.upsert_result(first)
        self.assertEqual(self.groups()["mode:20"]["history_total"], 1)
        self.ledger.upsert_result(result(1, 43, gross=90000))
        groups = self.groups()
        self.assertEqual(groups["mode:20"]["history_total"], 0)
        self.assertEqual(groups["mode:43"]["history_total"], 1)
        self.assertEqual(groups["mode:43"]["summary"]["net_credits"], 55000)

    def test_group_rows_keep_vehicle_time_rewards_and_defensive_copies(self):
        row = result(1, 20, reserves={"personal": 1000, "clan": 2000})
        row["vehicles"] = [{"vehicle_type_id": "321", "name": "XM57", "tier": 8, "icon": ICON}]
        self.ledger.upsert_result(row)
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, START)
        receipt = {"id": "battleResults:1", "kind": "battleResults",
            "occurred_at": row["occurred_at"], "battle_id": "1", "credits": 1000,
            "included_in_battle": True, "title": u"Misiones de la partida",
            "parts": [{"quest_id": "quest", "title": "Crisol", "credits": 1000, "name_resolved": True}]}
        wallet.upsert_receipt("NA", "101", receipt)
        originals = copy.deepcopy((self.ledger.to_dict(), wallet.data))
        payload = self.payload(wallet=wallet)
        group_row = self.groups(payload)["mode:20"]["history"][0]
        self.assertEqual(group_row, payload["history"][0])
        self.assertEqual(group_row["vehicles"], row["vehicles"])
        self.assertEqual(group_row["time_label"], "18/10 07:01")
        self.assertEqual(group_row["rewards"], receipt["parts"])
        group_row["vehicles"][0]["name"] = "changed"
        group_row["rewards"][0]["title"] = "changed"
        group_row["reserves"]["clan"] = 99
        group_row["expenses"]["repair"] = 99
        self.assertEqual(payload["history"][0]["vehicles"][0]["name"], "XM57")
        self.assertEqual(payload["history"][0]["rewards"][0]["title"], "Crisol")
        self.assertEqual((self.ledger.to_dict(), wallet.data), originals)

    def test_mode_totals_do_not_change_global_goal_wallet_or_external_rewards(self):
        for row in (result(1, 1), result(2, 20, gross=20000), result(3, 43)):
            self.ledger.upsert_result(row)
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, START)
        receipt = {"id": "tokenQuests:1", "kind": "tokenQuests",
            "occurred_at": "2026-10-18T12:10:00Z", "battle_id": None,
            "credits": 100000, "included_in_battle": False, "title": "Crisol", "parts": []}
        wallet.upsert_receipt("NA", "101", receipt)
        config = {"account_goals": {"NA:101": {"mode": "balance_growth", "target": 1000000,
                  "baseline": 22000000, "since_utc": START}}}
        previous = copy.deepcopy((self.ledger.to_dict(), wallet.data, config))
        payload = self.payload(config, balance=22215000, wallet=wallet)
        self.assertEqual(payload["summary"], self.ledger.summary("NA", "101"))
        self.assertEqual(payload["wallet"]["battle_net"], 115000)
        self.assertEqual(payload["wallet"]["external_credits"], 100000)
        self.assertEqual(payload["wallet"]["unclassified"], 0)
        self.assertEqual(payload["goal"]["current"], 215000)
        self.assertEqual(payload["balance"], 22215000)
        self.assertEqual(len(payload["rewards"]), 1)
        self.assertEqual(sum(group["summary"]["net_credits"] for group in payload["mode_groups"]), 115000)
        self.assertEqual((self.ledger.to_dict(), wallet.data, config), previous)


if __name__ == "__main__":
    unittest.main()
