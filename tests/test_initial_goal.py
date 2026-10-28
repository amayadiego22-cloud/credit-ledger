import copy
import unittest

from capture.presentation import ensure_balance_goal, balance_goal, parse_goal_command


class InitialGoalTests(unittest.TestCase):
    now = "2026-10-28T18:00:00Z"

    def test_each_new_regional_account_starts_from_its_own_balance(self):
        config = {"notifications": True}
        for realm, balance in (("NA", 0), ("EU", 22000000), ("ASIA", 90000)):
            config = ensure_balance_goal(config, realm, "101", balance, self.now)
            goal = balance_goal(config, realm, "101", balance)
            self.assertTrue(goal["active"])
            self.assertEqual(goal["target"], 100000)
            self.assertEqual(goal["baseline"], balance)
            self.assertEqual(goal["current"], 0)
            self.assertEqual(goal["progress_percent"], 0)
        self.assertEqual(len(config["account_goals"]), 3)

    def test_saved_disabled_goal_does_not_restart_at_login(self):
        config = ensure_balance_goal({}, "NA", "101", 22000000, self.now)
        config = parse_goal_command("0", "balance_growth", config, self.now, 22050000, "NA", "101")
        before = copy.deepcopy(config)
        self.assertIsNone(ensure_balance_goal(config, "NA", "101", 22050000, self.now))
        self.assertEqual(config, before)
        self.assertEqual(balance_goal(config, "NA", "101", 22050000)["target"], 0)
        self.assertEqual(balance_goal(config, "NA", "101", 22050000)["current"], 50000)

    def test_saved_progress_survives_new_default_and_amount_updates(self):
        config = ensure_balance_goal({}, "EU", "101", 22000000, self.now)
        config = parse_goal_command("3000000", "balance_growth", config, self.now, 22050000, "EU", "101")
        before = copy.deepcopy(config)
        self.assertIsNone(ensure_balance_goal(config, "EU", "101", 22500000, self.now))
        self.assertEqual(config, before)
        goal = balance_goal(config, "EU", "101", 22500000)
        self.assertEqual(goal["target"], 3000000)
        self.assertEqual(goal["baseline"], 22000000)
        self.assertEqual(goal["current"], 500000)

    def test_waits_for_exact_balance_and_valid_start_without_touching_config(self):
        config = {"notifications": True}
        for balance, now in ((None, self.now), (True, self.now), (-1, self.now),
                             (22.5, self.now), (9007199254740991, self.now), (100, "invalid")):
            self.assertIsNone(ensure_balance_goal(config, "NA", "101", balance, now))
            self.assertEqual(config, {"notifications": True})


if __name__ == "__main__":
    unittest.main()
