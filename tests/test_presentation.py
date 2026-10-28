import copy
import unittest

from capture.presentation import build_payload, parse_goal_command, ensure_balance_goal, balance_goal
from capture.history import parse_history_settings
from capture.wallet import WalletBook
from core import EconomyLedger
from timezone_fixtures import mock_local_timezone


def observed_record(account="101"):
    # Amounts from the user-confirmed second battle; identifiers anonymized.
    return {"region": "NA", "account_id": account, "battle_id": "9001",
            "occurred_at": "2026-10-18T00:40:27Z", "status": "final",
            "credits": {"gross": 56028, "expenses": {"repair": 33136,
                         "ammo": 106400, "consumables": 30000, "other": 0}}}


class PresentationTests(unittest.TestCase):
    def setUp(self):
        clock = mock_local_timezone("America/Bogota")
        clock.__enter__()
        self.addCleanup(clock.__exit__, None, None, None)
        self.ledger = EconomyLedger()
        self.ledger.upsert_result(observed_record())
        self.config = {"credit_target": 3000000, "notifications": True,
                       "account_goals": {"NA:101": {"mode": "balance_growth", "target": 3000000,
                         "baseline": 22000000, "since_utc": "2026-10-18T00:00:00Z"}}}

    def test_real_confirmed_expenses_and_net_are_presented(self):
        payload = build_payload(self.ledger, "NA", "101", self.config, 22000000, 1)
        self.assertEqual(payload["summary"]["net_credits"], -113508)
        self.assertEqual(payload["summary"]["pending_battles"], 1)
        self.assertEqual(payload["history"][0]["time_label"], "17/10 19:40")
        self.assertEqual(payload["goal"]["remaining"], 3000000)
        self.assertEqual(payload["goal"]["progress_percent"], 0)
        self.assertEqual(payload["goal"]["final_balance"], 25000000)
        self.assertIsNone(payload["goal"]["estimated_battles"])

    def test_unknown_account_does_not_show_other_account_history(self):
        payload = build_payload(self.ledger, "NA", None, self.config, None)
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["history"], [])
        payload = build_payload(self.ledger, "NA", "102", self.config, 0)
        self.assertEqual(payload["summary"]["battle_count"], 0)
        self.assertEqual(payload["history"], [])

    def test_reset_goal_wallet_and_battle_times_agree_with_the_players_local_clock(self):
        with mock_local_timezone("Asia/Kolkata"):
            config = parse_history_settings({"mode": "daily", "hour": 6}, self.config,
                                            "NA", "101", "2026-10-18T01:00:00Z")
            config["account_history"]["NA:101"].update(
                since_utc="2026-10-17T22:00:00Z", baseline=22000000)
            wallet = WalletBook()
            wallet.observe("NA", "101", 22000000, "2026-10-17T22:00:00Z")
            payload = build_payload(self.ledger, "NA", "101", config, 22000000,
                                    now_utc="2026-10-18T01:00:00Z", wallet=wallet)
            control = payload["history_control"]
            self.assertEqual(control["next_reset_utc"], "2026-10-19T00:30:00Z")
            self.assertEqual(control["next_reset_label"],
                             "19/10/2026 06:00 (hora local, UTC+05:30)")
            self.assertEqual(control["since_label"],
                             "18/10/2026 03:30 (hora local, UTC+05:30)")
            self.assertEqual(control["timezone_label"], "Hora local del equipo (UTC+05:30)")
            self.assertEqual(payload["goal"]["since_label"],
                             "18/10/2026 05:30 (hora local, UTC+05:30)")
            self.assertEqual(payload["wallet"]["started_at_label"], control["since_label"])
            self.assertEqual(payload["history"][0]["time_label"], "18/10 06:10")

    def test_unknown_balance_is_not_treated_as_zero(self):
        payload = build_payload(self.ledger, "NA", "101", self.config, None)
        self.assertIsNone(payload["goal"]["current"])
        self.assertEqual(payload["summary"]["battle_count"], 1)
        payload = build_payload(self.ledger, "NA", "101", self.config, 0)
        self.assertEqual(payload["goal"]["current"], -22000000)
        self.assertEqual(payload["goal"]["progress_percent"], 0)

    def test_target_is_validated_again_in_python(self):
        for value in ("-1", "1.000", "1.5", "9007199254740992", True, ""):
            with self.assertRaises(ValueError):
                parse_goal_command(value, "balance_growth", self.config, "2026-10-18T01:00:00Z", 22000000, "NA", "101")
        updated = parse_goal_command("40000000", "balance_growth", self.config, "2026-10-18T01:00:00Z", 22000000, "NA", "101")
        self.assertEqual(updated["credit_target"], 40000000)
        self.assertTrue(updated["notifications"])
        self.assertEqual(self.config["credit_target"], 3000000)

    def test_editing_an_active_goal_keeps_its_original_balance_and_start_time(self):
        goal = balance_goal(self.config, "NA", "101", 23500000)
        self.assertEqual(goal["current"], 1500000)
        self.assertEqual(goal["progress_percent"], 50)
        self.assertEqual(goal["remaining"], 1500000)
        updated = parse_goal_command("3000000", "balance_growth", self.config, "2026-10-18T02:00:00Z", 23500000, "NA", "101")
        edited = balance_goal(updated, "NA", "101", 23500000)
        self.assertEqual(edited["current"], 1500000)
        self.assertEqual(edited["final_balance"], 25000000)
        self.assertEqual(edited["baseline"], 22000000)
        self.assertEqual(edited["since_utc"], "2026-10-18T00:00:00Z")

    def test_target_changes_recalculate_percentage_remaining_and_completion(self):
        config = parse_goal_command("1000000", "balance_growth", {},
            "2026-10-18T00:00:00Z", 22000000, "NA", "101")
        first = balance_goal(config, "NA", "101", 22500000)
        self.assertEqual(first["progress_percent"], 50)
        for target, percent, remaining, complete in (
                (2000000, 25, 1500000, False),
                (750000, 100.0 * 2 / 3, 250000, False),
                (400000, 100, 0, True),
                (2000000, 25, 1500000, False)):
            config = parse_goal_command(str(target), "balance_growth", config,
                "2026-10-18T03:00:00Z", 22500000, "NA", "101")
            goal = balance_goal(config, "NA", "101", 22500000)
            self.assertAlmostEqual(goal["progress_percent"], percent)
            self.assertEqual(goal["current"], 500000)
            self.assertEqual(goal["remaining"], remaining)
            self.assertEqual(goal["complete"], complete)
            self.assertEqual(goal["final_balance"], 22000000 + target)
            self.assertEqual(goal["baseline"], 22000000)
            self.assertEqual(goal["since_utc"], "2026-10-18T00:00:00Z")
            self.assertEqual(config["credit_target"], target)

    def test_target_edit_preserves_losses_other_accounts_and_history_configuration(self):
        self.config["account_goals"]["NA:202"] = {"schema": 2, "mode": "balance_growth",
            "target": 1000000, "baseline": 9000000, "since_utc": "2026-10-17T12:00:00Z"}
        self.config["account_history"] = {"NA:101": {"mode": "daily", "hour": 6,
            "generation": 3, "excluded_battles": ["9001"], "baseline": 22000000}}
        self.config["account_goals"]["NA:101"]["extra_saved_value"] = "keep"
        previous = copy.deepcopy(self.config)
        edited = parse_goal_command("1000000", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", 21750000, "NA", "101")
        goal = balance_goal(edited, "NA", "101", 21750000)
        self.assertEqual(goal["current"], -250000)
        self.assertEqual(goal["remaining"], 1250000)
        self.assertEqual(goal["progress_percent"], 0)
        self.assertFalse(goal["complete"])
        expected = copy.deepcopy(previous)
        expected["account_goals"]["NA:101"]["target"] = 1000000
        expected["credit_target"] = 1000000
        self.assertEqual(edited, expected)
        self.assertEqual(self.config, previous)

    def test_saved_base_controls_amount_limit_and_current_balance_is_still_required(self):
        maximum = 9007199254740991
        target = maximum - 22000000
        edited = parse_goal_command(str(target), "balance_growth", self.config,
            "2026-10-18T03:00:00Z", 22500000, "NA", "101")
        self.assertEqual(balance_goal(edited, "NA", "101", 22500000)["final_balance"], maximum)
        with self.assertRaises(ValueError):
            parse_goal_command(str(target + 1), "balance_growth", self.config,
                "2026-10-18T03:00:00Z", 21750000, "NA", "101")
        with self.assertRaises(ValueError):
            parse_goal_command("2000000", "balance_growth", self.config,
                "2026-10-18T03:00:00Z", None, "NA", "101")

    def test_corrupt_active_goal_is_rejected_without_inventing_a_new_base(self):
        cases = ({"baseline": None}, {"baseline": True}, {"baseline": -1},
                 {"baseline": "22000000"}, {"since_utc": None},
                 {"since_utc": "invalid"}, {"since_utc": "2026-02-30T00:00:00Z"},
                 {"mode": "balance"}, {"target": True}, {"target": "1000000"})
        for changes in cases:
            config = copy.deepcopy(self.config)
            config["account_goals"]["NA:101"].update(changes)
            before = copy.deepcopy(config)
            with self.assertRaises(ValueError):
                parse_goal_command("2000000", "balance_growth", config,
                    "2026-10-18T03:00:00Z", 22500000, "NA", "101")
            self.assertEqual(config, before)
        for config in (None, {"account_goals": []}, {"account_goals": {"NA:101": None}}):
            with self.assertRaises(ValueError):
                parse_goal_command("2000000", "balance_growth", config,
                    "2026-10-18T03:00:00Z", 22500000, "NA", "101")

    def test_first_use_starts_at_100000_and_existing_account_goals_survive(self):
        legacy = {"credit_target": 1000000, "notifications": True}
        self.assertIsNone(ensure_balance_goal(legacy, "NA", "101", None, "2026-10-18T01:00:00Z"))
        migrated = ensure_balance_goal(legacy, "NA", "101", 22329142, "2026-10-18T01:00:00Z")
        goal = balance_goal(migrated, "NA", "101", 22329142)
        self.assertEqual(goal["progress_percent"], 0)
        self.assertEqual(goal["target"], 100000)
        self.assertTrue(goal["active"])
        self.assertEqual(goal["baseline"], 22329142)
        self.assertIsNone(ensure_balance_goal(migrated, "NA", "101", 23000000, "2026-10-18T02:00:00Z"))
        other = ensure_balance_goal(migrated, "NA", "102", 90000, "2026-10-18T02:00:00Z")
        self.assertEqual(other["account_goals"]["NA:101"]["baseline"], 22329142)
        self.assertEqual(other["account_goals"]["NA:102"]["baseline"], 90000)
        manual = parse_goal_command("3000000", "balance_growth", migrated, "2026-10-18T02:00:00Z", 23000000, "NA", "101")
        self.assertIsNone(ensure_balance_goal(manual, "NA", "101", 24000000, "2026-10-18T03:00:00Z"))
        self.assertEqual(balance_goal(manual, "NA", "101", 24000000)["current"], 1670858)
        self.assertEqual(balance_goal({}, "NA", "102", 100)["target"], 0)

    def test_unknown_balance_cannot_start_a_goal_and_completion_is_clamped(self):
        with self.assertRaises(ValueError):
            parse_goal_command("1000000", "balance_growth", self.config, "2026-10-18T02:00:00Z", None, "NA", "101")
        completed = balance_goal(self.config, "NA", "101", 27000000)
        self.assertEqual(completed["progress_percent"], 100)
        self.assertEqual(completed["remaining"], 0)

    def test_initial_zero_saves_no_active_goal_without_inventing_a_start(self):
        previous = {"notifications": True}
        updated = parse_goal_command("0", "balance_growth", previous,
            "2026-10-18T02:00:00Z", None, "NA", "101")
        saved = updated["account_goals"]["NA:101"]
        self.assertEqual(saved["target"], 0)
        self.assertIsNone(saved["baseline"])
        self.assertIsNone(saved["since_utc"])
        self.assertEqual(saved["schema"], 2)
        self.assertEqual(updated["credit_target"], 0)
        self.assertEqual(previous, {"notifications": True})
        for balance in (None, 0, 22000000):
            goal = balance_goal(updated, "NA", "101", balance)
            self.assertFalse(goal["active"])
            self.assertFalse(goal["complete"])
            self.assertEqual(goal["current"], 0)
            self.assertEqual(goal["remaining"], 0)
            self.assertEqual(goal["progress_percent"], 0)
            self.assertIsNone(goal["final_balance"])

    def test_zero_deactivates_and_repeated_zero_keeps_the_last_goal_start(self):
        before = copy.deepcopy(self.config)
        disabled = parse_goal_command("0", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", None, "NA", "101")
        self.assertEqual(self.config, before)
        for stamp, balance in (("2026-10-18T03:00:00Z", None),
                               ("2026-10-19T15:00:00Z", 25000000)):
            disabled = parse_goal_command("0", "balance_growth", disabled,
                stamp, balance, "NA", "101")
            goal = balance_goal(disabled, "NA", "101", balance)
            self.assertEqual(goal["target"], 0)
            self.assertEqual(goal["baseline"], 22000000)
            self.assertEqual(goal["since_utc"], "2026-10-18T00:00:00Z")
            self.assertEqual(goal["progress_percent"], 0)
            self.assertFalse(goal["active"])
            self.assertFalse(goal["complete"])
            self.assertIsNone(goal["final_balance"])

    def test_positive_goal_after_zero_resumes_the_original_balance_and_date(self):
        disabled = parse_goal_command("0", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", None, "NA", "101")
        reactivated = parse_goal_command("2000000", "balance_growth", disabled,
            "2026-10-19T15:00:00Z", 23500000, "NA", "101")
        goal = balance_goal(reactivated, "NA", "101", 23500000)
        self.assertTrue(goal["active"])
        self.assertFalse(goal["complete"])
        self.assertEqual(goal["baseline"], 22000000)
        self.assertEqual(goal["since_utc"], "2026-10-18T00:00:00Z")
        self.assertEqual(goal["target"], 2000000)
        self.assertEqual(goal["current"], 1500000)
        self.assertEqual(goal["progress_percent"], 75)
        self.assertEqual(goal["final_balance"], 24000000)
        self.assertEqual(disabled["account_goals"]["NA:101"]["target"], 0)

    def test_disabled_goal_retains_account_change_including_later_losses(self):
        disabled = parse_goal_command("0", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", 22500000, "NA", "101")
        for balance, change in ((22500000, 500000), (23000000, 1000000), (21750000, -250000)):
            inactive = balance_goal(disabled, "NA", "101", balance)
            self.assertEqual(inactive["current"], change)
            self.assertEqual(inactive["progress_percent"], 0)
            self.assertEqual(inactive["remaining"], 0)
            self.assertFalse(inactive["active"])
            resumed = parse_goal_command("2000000", "balance_growth", disabled,
                "2026-10-19T15:00:00Z", balance, "NA", "101")
            goal = balance_goal(resumed, "NA", "101", balance)
            self.assertEqual(goal["current"], change)
            self.assertEqual(goal["baseline"], 22000000)
            self.assertEqual(goal["since_utc"], "2026-10-18T00:00:00Z")
        self.assertIsNone(balance_goal(disabled, "NA", "101", None)["current"])

    def test_corrupt_disabled_start_is_rejected_instead_of_silently_restarting(self):
        disabled = parse_goal_command("0", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", None, "NA", "101")
        for changes in ({"baseline": None}, {"since_utc": None}, {"baseline": True},
                        {"since_utc": "bad"}, {"mode": "balance"},
                        {"reset_generation": True}, {"reset_generation": -1}):
            config = copy.deepcopy(disabled)
            config["account_goals"]["NA:101"].update(changes)
            with self.assertRaises(ValueError):
                parse_goal_command("2000000", "balance_growth", config,
                    "2026-10-19T15:00:00Z", 23500000, "NA", "101")

    def test_zero_is_account_scoped_and_keeps_history_wallet_and_other_settings(self):
        self.config["account_goals"]["EU:101"] = {"schema": 2, "mode": "balance_growth",
            "target": 1000000, "baseline": 9000000, "since_utc": "2026-10-17T12:00:00Z"}
        self.config["account_history"] = {"NA:101": {"mode": "daily", "hour": 6,
            "generation": 3, "excluded_battles": ["9001"], "baseline": 22000000}}
        self.config["panel_view_mode"] = "minimized"
        self.config["account_goals"]["NA:101"]["schema"] = 2
        previous = copy.deepcopy(self.config)
        ledger_before = self.ledger.to_dict()
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, "2026-10-17T22:00:00Z")
        wallet_before = copy.deepcopy(wallet.data)
        disabled = parse_goal_command("0", "balance_growth", self.config,
            "2026-10-18T03:00:00Z", None, "NA", "101")
        expected = copy.deepcopy(previous)
        expected["credit_target"] = 0
        expected["account_goals"]["NA:101"]["target"] = 0
        self.assertEqual(disabled, expected)
        self.assertEqual(self.config, previous)
        payload = build_payload(self.ledger, "NA", "101", disabled, 22000000,
                                now_utc="2026-10-18T03:00:00Z", wallet=wallet)
        self.assertFalse(payload["goal"]["active"])
        self.assertFalse(payload["goal"]["complete"])
        self.assertEqual(self.ledger.to_dict(), ledger_before)
        self.assertEqual(wallet.data, wallet_before)
        for region, account_id in ((None, "101"), ("NA", None)):
            with self.assertRaises(ValueError):
                parse_goal_command("0", "balance_growth", previous,
                    "2026-10-18T03:00:00Z", None, region, account_id)


if __name__ == "__main__":
    unittest.main()
