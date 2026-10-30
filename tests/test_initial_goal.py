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
        self.assertTrue(config["account_goals"]["NA:101"]["disabled_by_user"])
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

    def test_unstarted_zero_from_an_older_reset_migrates_once_at_current_balance(self):
        config = {"notifications": True, "credit_target": 0,
                  "account_history": {"NA:101": {"generation": 4}},
                  "account_goals": {"NA:101": {
                      "schema": 2, "mode": "balance_growth", "target": 0,
                      "baseline": None, "since_utc": None, "reset_generation": 4}}}
        before = copy.deepcopy(config)
        updated = ensure_balance_goal(config, "NA", "101", 23000000, self.now)
        self.assertIsNotNone(updated)
        self.assertEqual(config, before)
        goal = balance_goal(updated, "NA", "101", 23000000)
        self.assertTrue(goal["active"])
        self.assertEqual(goal["target"], 100000)
        self.assertEqual(goal["baseline"], 23000000)
        self.assertEqual(goal["since_utc"], self.now)
        self.assertEqual(goal["reset_generation"], 4)
        self.assertEqual(goal["current"], 0)
        self.assertEqual(goal["progress_percent"], 0)
        self.assertEqual(updated["credit_target"], 100000)
        self.assertEqual(updated["account_history"], before["account_history"])
        saved = copy.deepcopy(updated)
        self.assertIsNone(ensure_balance_goal(updated, "NA", "101", 23025000, self.now))
        self.assertEqual(updated, saved)
        self.assertEqual(balance_goal(updated, "NA", "101", 23025000)["current"], 25000)

    def test_explicit_zero_before_first_goal_stays_disabled_without_a_baseline(self):
        config = parse_goal_command("0", "balance_growth", {}, self.now, None, "NA", "101")
        self.assertTrue(config["account_goals"]["NA:101"]["disabled_by_user"])
        before = copy.deepcopy(config)
        for balance in (0, 22000000, 22500000):
            with self.subTest(balance=balance):
                self.assertIsNone(ensure_balance_goal(config, "NA", "101", balance, self.now))
                self.assertEqual(config, before)
                goal = balance_goal(config, "NA", "101", balance)
                self.assertFalse(goal["active"])
                self.assertEqual(goal["target"], 0)
                self.assertIsNone(goal["baseline"])

    def test_positive_amount_reactivates_explicit_zero_and_removes_its_marker(self):
        config = ensure_balance_goal({}, "NA", "101", 22000000, self.now)
        disabled = parse_goal_command("0", "balance_growth", config, self.now,
                                      22050000, "NA", "101")
        active = parse_goal_command("500000", "balance_growth", disabled, self.now,
                                    22075000, "NA", "101")
        self.assertNotIn("disabled_by_user", active["account_goals"]["NA:101"])
        self.assertIsNone(ensure_balance_goal(active, "NA", "101", 22100000, self.now))
        goal = balance_goal(active, "NA", "101", 22100000)
        self.assertEqual(goal["target"], 500000)
        self.assertEqual(goal["baseline"], 22000000)
        self.assertEqual(goal["current"], 100000)
        self.assertTrue(disabled["account_goals"]["NA:101"]["disabled_by_user"])

    def test_legacy_zero_with_saved_progress_is_preserved_without_a_marker(self):
        config = {"credit_target": 0, "account_goals": {"NA:101": {
            "schema": 2, "mode": "balance_growth", "target": 0,
            "baseline": 22000000, "since_utc": self.now, "reset_generation": 2}}}
        before = copy.deepcopy(config)
        self.assertIsNone(ensure_balance_goal(config, "NA", "101", 22200000, self.now))
        self.assertEqual(config, before)
        goal = balance_goal(config, "NA", "101", 22200000)
        self.assertEqual(goal["target"], 0)
        self.assertEqual(goal["current"], 200000)
        self.assertEqual(goal["reset_generation"], 2)

    def test_migration_is_scoped_to_one_account_and_region(self):
        unstarted = {"schema": 2, "mode": "balance_growth", "target": 0,
                     "baseline": None, "since_utc": None, "reset_generation": 3}
        config = {"credit_target": 0, "account_goals": {
            "NA:101": copy.deepcopy(unstarted),
            "NA:202": copy.deepcopy(unstarted),
            "EU:101": dict(unstarted, disabled_by_user=True),
            "ASIA:101": {"schema": 2, "mode": "balance_growth", "target": 300000,
                         "baseline": 20000000, "since_utc": self.now, "reset_generation": 1}}}
        before = copy.deepcopy(config)
        updated = ensure_balance_goal(config, "NA", "101", 22000000, self.now)
        self.assertEqual(config, before)
        for key in ("NA:202", "EU:101", "ASIA:101"):
            self.assertEqual(updated["account_goals"][key], before["account_goals"][key])
        self.assertIsNone(ensure_balance_goal(updated, "EU", "101", 23000000, self.now))
        self.assertIsNone(ensure_balance_goal(updated, "ASIA", "101", 23500000, self.now))

    def test_legacy_zero_migration_waits_for_a_valid_synced_start(self):
        config = {"credit_target": 0, "account_goals": {"NA:101": {
            "schema": 2, "mode": "balance_growth", "target": 0,
            "baseline": None, "since_utc": None, "reset_generation": 1}}}
        before = copy.deepcopy(config)
        for balance, now in ((None, self.now), (True, self.now), (-1, self.now),
                             (22.5, self.now), (9007199254740991, self.now), (100, "invalid")):
            with self.subTest(balance=balance, now=now):
                self.assertIsNone(ensure_balance_goal(config, "NA", "101", balance, now))
                self.assertEqual(config, before)

    def test_waits_for_exact_balance_and_valid_start_without_touching_config(self):
        config = {"notifications": True}
        for balance, now in ((None, self.now), (True, self.now), (-1, self.now),
                             (22.5, self.now), (9007199254740991, self.now), (100, "invalid")):
            self.assertIsNone(ensure_balance_goal(config, "NA", "101", balance, now))
            self.assertEqual(config, {"notifications": True})


if __name__ == "__main__":
    unittest.main()
