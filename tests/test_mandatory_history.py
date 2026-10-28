"""Server scheduling is built in; manual reset is an action, not an opt-out."""
import copy
import unittest

from capture.history import (ensure_mandatory_server_history, get_history_state,
                             server_reset_due)


NOW = "2026-10-19T12:00:00Z"
CLOCK = {"cycle_start_utc": "2026-10-19T10:00:00Z", "next_reset_utc": "2026-10-20T10:00:00Z"}


class MandatoryHistoryTests(unittest.TestCase):
    def test_every_previous_schedule_migrates_without_resetting_a_period_or_goal(self):
        for mode in ("manual", "daily", "server"):
            config = {"account_history": {"NA:101": {"mode": mode, "hour": 6,
                "settings_schema": 1, "since_utc": "2026-10-18T12:00:00Z", "baseline": 22000000,
                "generation": 4, "excluded_battles": ["123"], "preserve_goal": True}},
                "account_goals": {"NA:101": {"target": 500000, "baseline": 22000000}},
                "credit_target": 500000}
            before = copy.deepcopy(config)
            changed = ensure_mandatory_server_history(config, "NA", "101", NOW, CLOCK)
            state = get_history_state(changed, "NA", "101")
            self.assertEqual(state["mode"], "server")
            self.assertEqual(state["reset_policy"], 2)
            self.assertEqual(state["generation"], 4)
            self.assertEqual(state["excluded_battles"], ["123"])
            self.assertEqual(state["baseline"], 22000000)
            self.assertEqual(changed["account_goals"], before["account_goals"])
            self.assertEqual(config, before)
            self.assertIsNone(ensure_mandatory_server_history(changed, "NA", "101", NOW, CLOCK))

    def test_existing_overdue_server_cycle_is_not_rearmed_by_policy_migration(self):
        config = {"account_history": {"NA:101": {"mode": "server", "clock": "server_v1",
            "server_cycle": "2026-10-18T10:00:00Z", "generation": 5}}}
        changed = ensure_mandatory_server_history(config, "NA", "101", NOW, CLOCK)
        self.assertTrue(server_reset_due(changed, "NA", "101", NOW, CLOCK))
        self.assertEqual(get_history_state(changed, "NA", "101")["generation"], 5)

    def test_policy_marker_does_not_prevent_repairing_a_stale_clock(self):
        for clock in (None, "local_v1"):
            config = {"account_history": {"NA:101": {"mode": "server", "reset_policy": 2,
                "clock": clock, "preserve_goal": False,
                "server_cycle": "2026-10-18T10:00:00Z", "generation": 5}}}
            changed = ensure_mandatory_server_history(config, "NA", "101", NOW, CLOCK)
            state = get_history_state(changed, "NA", "101")
            self.assertEqual(state["clock"], "server_v1")
            self.assertFalse(state["preserve_goal"])
            self.assertEqual(state["generation"], 5)
            self.assertTrue(server_reset_due(changed, "NA", "101", NOW, CLOCK))

    def test_missing_clock_waits_then_arms_without_inventing_a_local_cutoff(self):
        pending = ensure_mandatory_server_history({}, "NA", "101", NOW)
        state = get_history_state(pending, "NA", "101", NOW)
        self.assertEqual(state["mode"], "server")
        self.assertIsNone(state["server_cycle"])
        self.assertIsNone(state["next_reset_utc"])
        self.assertIsNone(ensure_mandatory_server_history(pending, "NA", "101", NOW))
        armed = ensure_mandatory_server_history(pending, "NA", "101", NOW, CLOCK)
        self.assertEqual(get_history_state(armed, "NA", "101")["server_cycle"], CLOCK["cycle_start_utc"])
        self.assertFalse(server_reset_due(armed, "NA", "101", NOW, CLOCK))

    def test_other_accounts_are_unchanged_and_invalid_policy_marker_is_replaced(self):
        other = {"mode": "daily", "hour": 9, "reset_policy": 2}
        config = {"account_history": {"NA:202": other, "NA:101": {"mode": "server", "reset_policy": True}}}
        changed = ensure_mandatory_server_history(config, "NA", "101", NOW, CLOCK)
        self.assertEqual(changed["account_history"]["NA:202"], other)
        self.assertEqual(changed["account_history"]["NA:101"]["reset_policy"], 2)
