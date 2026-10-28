"""Goal restart is an explicit, account-scoped action, separate from deactivation."""
import copy
import unittest

from capture.presentation import balance_goal, parse_goal_command, parse_reset_goal_command


START = "2026-10-18T12:00:00Z"
RESET = "2026-10-19T15:00:00Z"
KEY = "NA:101"
BASE = 22000000


class GoalResetTests(unittest.TestCase):
    def setUp(self):
        self.config = {"credit_target": 1000000, "notifications": True,
            "account_goals": {KEY: {"schema": 2, "mode": "balance_growth",
                "target": 1000000, "baseline": BASE, "since_utc": START,
                "custom_setting": "preserve"},
                "EU:101": {"schema": 2, "mode": "balance_growth", "target": 500000,
                    "baseline": 10000000, "since_utc": START}},
            "account_history": {KEY: {"mode": "daily", "hour": 6,
                "since_utc": START, "generation": 5, "excluded_battles": ["old"]}},
            "panel_view_mode": "details"}

    def reset(self, config=None, value="2000000", stamp=RESET, balance=BASE + 500000,
              region="NA", account_id="101", mode="balance_growth"):
        return parse_reset_goal_command(value, mode, self.config if config is None else config,
            stamp, balance, region, account_id)

    def test_explicit_reset_starts_at_current_balance_and_new_date(self):
        previous = copy.deepcopy(self.config)
        updated = self.reset()
        goal = balance_goal(updated, "NA", "101", BASE + 500000)
        self.assertEqual(goal["target"], 2000000)
        self.assertEqual(goal["baseline"], BASE + 500000)
        self.assertEqual(goal["since_utc"], RESET)
        self.assertEqual(goal["current"], 0)
        self.assertEqual(goal["progress_percent"], 0)
        self.assertEqual(goal["remaining"], 2000000)
        self.assertEqual(goal["final_balance"], BASE + 2500000)
        self.assertEqual(goal["reset_generation"], 1)
        self.assertTrue(goal["active"])
        expected = copy.deepcopy(previous)
        expected["credit_target"] = 2000000
        expected["account_goals"][KEY].update(target=2000000, baseline=BASE + 500000,
            since_utc=RESET, reset_generation=1)
        self.assertEqual(updated, expected)
        self.assertEqual(self.config, previous)

    def test_reset_can_start_a_first_goal_or_an_explicitly_disabled_goal(self):
        for config in ({"notifications": True},
                       parse_goal_command("0", "balance_growth", self.config,
                           START, None, "NA", "101")):
            updated = self.reset(config=config)
            goal = balance_goal(updated, "NA", "101", BASE + 500000)
            self.assertEqual(goal["current"], 0)
            self.assertEqual(goal["baseline"], BASE + 500000)
            self.assertEqual(goal["since_utc"], RESET)
            self.assertEqual(goal["reset_generation"], 1)

    def test_reset_generation_ack_changes_even_for_same_balance_date_and_amount(self):
        first = self.reset()
        second = self.reset(config=first)
        self.assertEqual(first["account_goals"][KEY]["reset_generation"], 1)
        self.assertEqual(second["account_goals"][KEY]["reset_generation"], 2)
        for key in ("target", "baseline", "since_utc"):
            self.assertEqual(first["account_goals"][KEY][key], second["account_goals"][KEY][key])
        disabled = parse_goal_command("0", "balance_growth", second, RESET,
            None, "NA", "101")
        resumed = parse_goal_command("3000000", "balance_growth", disabled, RESET,
            BASE + 600000, "NA", "101")
        edited = parse_goal_command("4000000", "balance_growth", resumed, RESET,
            BASE + 600000, "NA", "101")
        for config in (disabled, resumed, edited):
            goal = balance_goal(config, "NA", "101", BASE + 600000)
            self.assertEqual(goal["reset_generation"], 2)
            self.assertEqual(goal["baseline"], BASE + 500000)
            self.assertEqual(goal["since_utc"], RESET)
            self.assertEqual(goal["current"], 100000)

    def test_reset_rejects_zero_invalid_amounts_missing_balance_account_and_time(self):
        cases = ({"value": "0"}, {"value": "-1"}, {"value": "1.000"},
            {"value": "9007199254740992"}, {"value": True}, {"value": ""},
            {"balance": None}, {"balance": True}, {"balance": -1},
            {"balance": "22000000"}, {"region": None}, {"account_id": None},
            {"mode": "old"}, {"stamp": None}, {"stamp": "2026-02-30T00:00:00Z"})
        previous = copy.deepcopy(self.config)
        for args in cases:
            with self.assertRaises(ValueError):
                self.reset(**args)
            self.assertEqual(self.config, previous)

    def test_reset_validates_sum_limit_and_generation_without_mutating_config(self):
        maximum = 9007199254740991
        allowed = self.reset(value=str(maximum - BASE), balance=BASE)
        self.assertEqual(balance_goal(allowed, "NA", "101", BASE)["final_balance"], maximum)
        with self.assertRaises(ValueError):
            self.reset(value=str(maximum - BASE + 1), balance=BASE)
        for generation in (True, -1, "1", maximum, maximum + 1):
            config = copy.deepcopy(self.config)
            config["account_goals"][KEY]["reset_generation"] = generation
            before = copy.deepcopy(config)
            with self.assertRaises(ValueError):
                self.reset(config=config)
            self.assertEqual(config, before)

    def test_initial_zero_and_first_positive_start_keep_reset_generation_zero(self):
        disabled = parse_goal_command("0", "balance_growth", {}, START, None, "NA", "101")
        self.assertEqual(balance_goal(disabled, "NA", "101", BASE)["reset_generation"], 0)
        started = parse_goal_command("1000000", "balance_growth", disabled, RESET,
            BASE + 500000, "NA", "101")
        goal = balance_goal(started, "NA", "101", BASE + 500000)
        self.assertEqual(goal["current"], 0)
        self.assertEqual(goal["baseline"], BASE + 500000)
        self.assertEqual(goal["since_utc"], RESET)
        self.assertEqual(goal["reset_generation"], 0)


if __name__ == "__main__":
    unittest.main()
