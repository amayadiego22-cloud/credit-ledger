import copy
import unittest

from capture.history import (daily_boundary, next_daily_reset, get_history_state,
    parse_history_settings, daily_reset_due, reset_history_config,
    record_visible, receipt_visible, ensure_local_history_clock)
from timezone_fixtures import mock_local_timezone


NOW = "2026-10-18T15:30:00Z"


class HistoryTests(unittest.TestCase):
    def setUp(self):
        timezone = mock_local_timezone("America/Bogota")
        timezone.__enter__()
        self.addCleanup(timezone.__exit__, None, None, None)
        self.previous = {"notifications": True,
            "account_history": {"NA:202": {"mode": "manual", "hour": 9}},
            "account_goals": {"NA:101": {"schema": 2, "mode": "balance_growth",
                "target": 3000000, "baseline": 22000000,
                "since_utc": "2026-10-17T12:00:00Z"},
                "NA:202": {"target": 100, "baseline": 50}}}

    def daily(self, hour=6, preserve_goal=False, now=NOW):
        return parse_history_settings({"mode": "daily", "hour": hour,
            "preserve_goal": preserve_goal}, self.previous, "NA", "101", now)

    def test_defaults_are_manual_and_account_scoped(self):
        state = get_history_state(self.previous, "NA", "101")
        self.assertEqual(state, {"mode": "manual", "hour": 6, "preserve_goal": False,
            "since_utc": None, "baseline": None, "excluded_battles": [],
            "excluded_receipts": [], "generation": 0, "daily_cycle": None})
        self.assertEqual(get_history_state(self.previous, "NA", "202")["hour"], 9)
        self.assertEqual(get_history_state(self.previous, "EU", "202")["hour"], 6)
        self.assertIsNone(get_history_state({}, "NA", None, NOW)["next_reset_utc"])
        state["excluded_battles"].append("old")
        self.assertEqual(get_history_state(self.previous, "NA", "101")["excluded_battles"], [])

    def test_daily_boundary_before_at_and_after_six_colombia(self):
        before = "2026-10-18T10:59:59Z"
        boundary = "2026-10-18T11:00:00Z"
        self.assertEqual(daily_boundary(before, 6), "2026-10-17T11:00:00Z")
        self.assertEqual(next_daily_reset(before, 6), boundary)
        self.assertEqual(daily_boundary(boundary, 6), boundary)
        self.assertEqual(next_daily_reset(boundary, 6), "2026-10-19T11:00:00Z")
        self.assertEqual(daily_boundary("2026-10-18T11:00:01Z", 6), boundary)
        # 06:00 UTC is 01:00 in Colombia, not the requested 06:00 reset.
        self.assertEqual(daily_boundary("2026-10-18T06:00:00Z", 6), "2026-10-17T11:00:00Z")

    def test_midnight_and_twenty_three_use_colombian_calendar(self):
        self.assertEqual(daily_boundary("2026-10-18T04:59:59Z", 0), "2026-10-17T05:00:00Z")
        self.assertEqual(daily_boundary("2026-10-18T05:00:00Z", 0), "2026-10-18T05:00:00Z")
        self.assertEqual(next_daily_reset("2026-10-18T00:00:00Z", 0), "2026-10-18T05:00:00Z")
        self.assertEqual(daily_boundary("2026-10-18T04:00:00Z", 23), "2026-10-18T04:00:00Z")
        self.assertEqual(next_daily_reset("2026-10-18T04:00:00Z", 23), "2026-10-19T04:00:00Z")

    def test_enabling_daily_waits_until_next_cutoff_and_survives_days_offline(self):
        settings = self.daily(now="2026-10-18T10:59:59Z")
        state = get_history_state(settings, "NA", "101", "2026-10-18T10:59:59Z")
        self.assertEqual(state["daily_cycle"], "2026-10-17T11:00:00Z")
        self.assertEqual(state["next_reset_utc"], "2026-10-18T11:00:00Z")
        self.assertFalse(daily_reset_due(settings, "NA", "101", "2026-10-18T10:59:59Z"))
        self.assertTrue(daily_reset_due(settings, "NA", "101", "2026-10-18T11:00:00Z"))
        self.assertTrue(daily_reset_due(settings, "NA", "101", "2026-10-22T15:00:00Z"))
        reset = reset_history_config(settings, "NA", "101", 25000000,
            "2026-10-22T15:00:00Z", [], [], automatic=True)
        state = get_history_state(reset, "NA", "101")
        self.assertEqual(state["generation"], 1)
        self.assertEqual(state["daily_cycle"], "2026-10-22T11:00:00Z")
        self.assertEqual(state["since_utc"], "2026-10-22T15:00:00Z")
        self.assertFalse(daily_reset_due(reset, "NA", "101", "2026-10-22T23:00:00Z"))

    def test_changing_daily_hour_does_not_apply_a_retroactive_reset(self):
        old = self.daily(hour=6, now="2026-10-17T12:00:00Z")
        changed = parse_history_settings({"hour": 8}, old, "NA", "101", NOW)
        self.assertEqual(get_history_state(changed, "NA", "101")["daily_cycle"], "2026-10-18T13:00:00Z")
        self.assertFalse(daily_reset_due(changed, "NA", "101", NOW))
        self.assertTrue(daily_reset_due(changed, "NA", "101", "2026-10-19T13:00:00Z"))
        self.assertIsNone(get_history_state(changed, "NA", "101")["since_utc"])
        self.assertEqual(get_history_state(changed, "NA", "101")["generation"], 0)

    def test_legacy_daily_clock_migration_rearms_without_resetting_history_or_goal(self):
        legacy = copy.deepcopy(self.previous)
        legacy["account_history"]["NA:101"] = {"mode": "daily", "hour": 9,
            "preserve_goal": False, "since_utc": "2026-10-17T15:00:00Z",
            "baseline": 23000000, "excluded_battles": ["old-battle"],
            "excluded_receipts": ["old-receipt"], "generation": 4,
            "daily_cycle": "2026-10-17T14:00:00Z"}
        original = copy.deepcopy(legacy)
        with mock_local_timezone("Europe/Madrid"):
            migrated = ensure_local_history_clock(legacy, "NA", "101", NOW)
            state = get_history_state(migrated, "NA", "101", NOW)
            self.assertEqual(state["daily_cycle"], "2026-10-18T07:00:00Z")
            self.assertEqual(state["next_reset_utc"], "2026-10-19T07:00:00Z")
            self.assertEqual(state["clock"], "local_v1")
            self.assertFalse(daily_reset_due(migrated, "NA", "101", NOW))
            self.assertIsNone(ensure_local_history_clock(migrated, "NA", "101", NOW))
        for name in ("mode", "hour", "preserve_goal", "since_utc", "baseline",
                     "excluded_battles", "excluded_receipts", "generation"):
            self.assertEqual(state[name], legacy["account_history"]["NA:101"][name])
        self.assertEqual(migrated["account_goals"], original["account_goals"])
        self.assertEqual(migrated["account_history"]["NA:202"], original["account_history"]["NA:202"])
        self.assertEqual(legacy, original)

    def test_manual_clock_migration_does_not_change_or_write_config(self):
        original = copy.deepcopy(self.previous)
        self.assertIsNone(ensure_local_history_clock(self.previous, "NA", "101", NOW))
        self.assertIsNone(ensure_local_history_clock(self.previous, "NA", "202", NOW))
        self.assertEqual(self.previous, original)

    def test_local_daily_cycle_does_not_repeat_when_dst_hour_is_repeated(self):
        for zone, before, first, second in (
                ("Europe/Madrid", "2026-10-24T12:00:00Z", "2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z"),
                ("Australia/Sydney", "2026-04-04T12:00:00Z", "2026-04-04T15:30:00Z", "2026-04-04T16:30:00Z")):
            with mock_local_timezone(zone):
                settings = self.daily(hour=2, now=before)
                self.assertTrue(daily_reset_due(settings, "NA", "101", first))
                reset = reset_history_config(settings, "NA", "101", 23000000,
                    first, [], [], automatic=True)
                self.assertFalse(daily_reset_due(reset, "NA", "101", second))
                self.assertEqual(get_history_state(reset, "NA", "101")["generation"], 1)

    def test_saving_same_daily_settings_does_not_hide_a_due_reset(self):
        old = self.daily(now="2026-10-17T12:00:00Z")
        saved = parse_history_settings({"preserve_goal": False}, old, "NA", "101", NOW)
        self.assertTrue(daily_reset_due(saved, "NA", "101", NOW))
        manual = parse_history_settings({"mode": "manual"}, saved, "NA", "101", NOW)
        self.assertFalse(daily_reset_due(manual, "NA", "101", "2026-10-25T12:00:00Z"))
        enabled = parse_history_settings({"mode": "daily"}, manual, "NA", "101", NOW)
        self.assertFalse(daily_reset_due(enabled, "NA", "101", NOW))

    def test_settings_are_validated_without_mutating_input(self):
        original = copy.deepcopy(self.previous)
        invalid = [{"mode": "weekly"}, {"mode": True}, {"hour": True},
            {"hour": -1}, {"hour": 24}, {"hour": 6.0}, {"hour": "6"},
            {"preserve_goal": 1}, {"preserve_goal": "false"}, [], None]
        for args in invalid:
            with self.assertRaises(ValueError):
                parse_history_settings(args, self.previous, "NA", "101", NOW)
        for hour in (True, -1, 24, 6.0, "6", None):
            with self.assertRaises(ValueError):
                daily_boundary(NOW, hour)
        for now in (None, True, "2026-10-18", "2026-02-30T11:00:00Z", "2026-10-18T11:00:00+00:00"):
            with self.assertRaises(ValueError):
                daily_boundary(now, 6)
        self.assertEqual(self.previous, original)

    def test_corrupt_saved_state_never_enables_guessed_daily_resets(self):
        invalid = {"account_history": {"NA:101": {"mode": "daily", "hour": True,
            "preserve_goal": "false", "since_utc": "yesterday", "baseline": True,
            "generation": -1, "daily_cycle": "corrupt", "excluded_battles": ["1", 1, True, None, {}, ""],
            "excluded_receipts": "not-a-list"}}}
        state = get_history_state(invalid, "NA", "101", NOW)
        self.assertEqual(state["mode"], "manual")
        self.assertEqual(state["hour"], 6)
        self.assertFalse(state["preserve_goal"])
        self.assertIsNone(state["since_utc"])
        self.assertIsNone(state["baseline"])
        self.assertIsNone(state["daily_cycle"])
        self.assertEqual(state["generation"], 0)
        self.assertEqual(state["excluded_battles"], ["1"])
        self.assertEqual(state["excluded_receipts"], [])
        self.assertFalse(daily_reset_due(invalid, "NA", "101", NOW))
        for config in (None, [], {"account_history": []}, {"account_history": {"NA:101": []}}):
            self.assertEqual(get_history_state(config, "NA", "101")["mode"], "manual")
        missing_cycle = {"account_history": {"NA:101": {"mode": "daily", "hour": 6}}}
        self.assertFalse(daily_reset_due(missing_cycle, "NA", "101", NOW))

    def test_manual_reset_excludes_existing_ids_from_same_second(self):
        updated = reset_history_config(self.previous, "NA", "101", 23000000, NOW,
            ["9001", "9001", 9002], ["token:1", "token:1"])
        state = get_history_state(updated, "NA", "101")
        self.assertEqual(state["baseline"], 23000000)
        self.assertEqual(state["since_utc"], NOW)
        self.assertEqual(state["generation"], 1)
        self.assertEqual(state["excluded_battles"], ["9001", "9002"])
        self.assertFalse(record_visible({"battle_id": "9001", "completed_at": NOW}, state))
        self.assertFalse(record_visible({"battle_id": 9002, "completed_at": NOW}, state))
        self.assertTrue(record_visible({"battle_id": "9003", "completed_at": NOW}, state))
        self.assertFalse(receipt_visible({"id": "token:1", "occurred_at": NOW}, state))
        self.assertTrue(receipt_visible({"id": "token:2", "occurred_at": NOW}, state))

    def test_completed_time_wins_over_battle_start_and_falls_back_when_missing(self):
        state = {"since_utc": NOW}
        old = "2026-10-18T15:29:59Z"
        self.assertTrue(record_visible({"battle_id": "1", "occurred_at": old,
                                      "completed_at": NOW}, state))
        self.assertFalse(record_visible({"battle_id": "2", "occurred_at": NOW,
                                       "completed_at": old}, state))
        self.assertTrue(record_visible({"battle_id": "3", "occurred_at": NOW}, state))
        self.assertTrue(record_visible({"battle_id": "4", "completed_at": "invalid",
                                      "occurred_at": NOW}, state))
        self.assertFalse(record_visible({"battle_id": "5", "occurred_at": old}, state))
        self.assertFalse(record_visible({"battle_id": "6", "occurred_at": "invalid"}, state))
        self.assertFalse(receipt_visible({"id": "r", "occurred_at": old}, state))
        self.assertFalse(receipt_visible({"id": "r", "occurred_at": "invalid"}, state))
        self.assertTrue(record_visible({"battle_id": "old", "occurred_at": old}, {}))
        self.assertFalse(record_visible(None, state))

    def test_visibility_accepts_list_set_and_frozen_set_exclusions(self):
        for collection in (list, set, frozenset):
            state = {"since_utc": NOW, "excluded_battles": collection(["1"]),
                     "excluded_receipts": collection(["token:1"])}
            self.assertFalse(record_visible({"battle_id": "1", "completed_at": NOW}, state))
            self.assertTrue(record_visible({"battle_id": "2", "completed_at": NOW}, state))
            self.assertFalse(receipt_visible({"id": "token:1", "occurred_at": NOW}, state))
            self.assertTrue(receipt_visible({"id": "token:2", "occurred_at": NOW}, state))
        config = {"account_history": {"NA:101": {"excluded_battles": ["1"],
                                                "excluded_receipts": ["token:1"]}}}
        saved = get_history_state(config, "NA", "101")
        self.assertIsInstance(saved["excluded_battles"], list)
        self.assertIsInstance(saved["excluded_receipts"], list)

    def test_set_membership_does_not_enumerate_the_exclusions(self):
        class MembershipOnlySet(set):
            def __iter__(self):
                raise AssertionError("A reader must use the prebuilt exclusion index directly")

        state = {"excluded_battles": MembershipOnlySet(["1"]),
                 "excluded_receipts": MembershipOnlySet(["token:1"])}
        self.assertFalse(record_visible({"battle_id": "1"}, state))
        self.assertTrue(record_visible({"battle_id": "2"}, state))
        self.assertFalse(receipt_visible({"id": "token:1"}, state))
        self.assertTrue(receipt_visible({"id": "token:2"}, state))

    def test_reset_is_account_scoped_copies_everything_and_preserves_goal_explicitly(self):
        settings = parse_history_settings({"preserve_goal": True}, self.previous,
            "NA", "101", NOW)
        original = copy.deepcopy(settings)
        updated = reset_history_config(settings, "NA", "101", 23000000, NOW, ["1"], ["r"])
        self.assertEqual(updated["account_goals"], original["account_goals"])
        self.assertEqual(updated["account_history"]["NA:202"], original["account_history"]["NA:202"])
        self.assertTrue(updated["notifications"])
        updated["account_history"]["NA:202"]["hour"] = 12
        updated["account_goals"]["NA:202"]["target"] = 300
        self.assertEqual(settings, original)
        another = reset_history_config(updated, "EU", "101", 0, NOW, [], [])
        self.assertEqual(another["account_history"]["EU:101"]["baseline"], 0)
        self.assertEqual(another["account_history"]["NA:101"]["baseline"], 23000000)

    def test_option_restarts_goal_progress_but_keeps_target(self):
        settings = self.daily(preserve_goal=False)
        before = copy.deepcopy(settings)
        updated = reset_history_config(settings, "NA", "101", 24000000, NOW,
            [], [], automatic=True)
        goal = updated["account_goals"]["NA:101"]
        self.assertEqual(goal["target"], 3000000)
        self.assertEqual(goal["baseline"], 24000000)
        self.assertEqual(goal["since_utc"], NOW)
        self.assertEqual(goal["mode"], "balance_growth")
        self.assertEqual(goal["schema"], 2)
        self.assertEqual(settings, before)
        settings["account_goals"]["NA:101"] = {"target": 0, "baseline": None, "since_utc": None}
        inactive = reset_history_config(settings, "NA", "101", 24000000, NOW, [], [])
        self.assertEqual(inactive["account_goals"]["NA:101"], settings["account_goals"]["NA:101"])

    def test_default_reset_restarts_goal_from_current_balance_and_keeps_target(self):
        updated = reset_history_config(self.previous, "NA", "101", 24000000,
            NOW, [], [])
        goal = updated["account_goals"]["NA:101"]
        self.assertFalse(updated["account_history"]["NA:101"]["preserve_goal"])
        self.assertEqual(goal["target"], 3000000)
        self.assertEqual(goal["baseline"], 24000000)
        self.assertEqual(goal["since_utc"], NOW)

    def test_reset_requires_a_real_nonnegative_exact_balance(self):
        for balance in (None, True, False, -1, 1.0, "100", 9007199254740992):
            with self.assertRaises(ValueError):
                reset_history_config(self.previous, "NA", "101", balance, NOW, [], [])
        with self.assertRaises(ValueError):
            reset_history_config(self.previous, "NA", None, 0, NOW, [], [])
        with self.assertRaises(ValueError):
            reset_history_config(self.previous, "NA", "101", 0, NOW, [], [], automatic=1)


if __name__ == "__main__":
    unittest.main()
