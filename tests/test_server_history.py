import copy
import unittest

from capture.history import (ensure_server_history_clock, get_history_state,
    parse_history_settings, receipt_visible, record_visible, reset_history_config,
    server_reset_due)
from capture.presentation import parse_goal_command


NOW = "2026-10-19T12:30:00Z"
FIRST = {"cycle_start_utc": "2026-10-19T11:00:00Z",
         "next_reset_utc": "2026-10-20T11:00:00Z"}
SECOND = {"cycle_start_utc": "2026-10-20T11:00:00Z",
          "next_reset_utc": "2026-10-21T11:00:00Z"}
TOMORROW = "2026-10-20T12:30:00Z"


class ServerHistoryTests(unittest.TestCase):
    def setUp(self):
        self.config = {"credit_target": 3000000,
            "account_history": {"NA:101": {"mode": "manual", "hour": 6,
                "since_utc": "2026-10-18T12:00:00Z", "baseline": 20000000,
                "excluded_battles": ["old"], "excluded_receipts": ["old-receipt"],
                "generation": 3}, "EU:101": {"mode": "manual", "hour": 9}},
            "account_goals": {"NA:101": {"schema": 2, "mode": "balance_growth",
                "target": 3000000, "baseline": 20000000,
                "since_utc": "2026-10-18T12:00:00Z", "reset_generation": 4},
                "EU:101": {"target": 100, "baseline": 50}},
            "unrelated": {"keep": [1, 2, 3]}}

    def server(self, native=FIRST):
        return parse_history_settings({"mode": "server", "preserve_goal": True},
            self.config, "NA", "101", NOW, server_clock=native)

    def test_legacy_manual_default_migrates_once_without_clearing_anything(self):
        before = copy.deepcopy(self.config)
        migrated = ensure_server_history_clock(self.config, "NA", "101", NOW, FIRST)
        old = get_history_state(self.config, "NA", "101")
        state = get_history_state(migrated, "NA", "101", NOW, FIRST)
        self.assertEqual(state["mode"], "server")
        self.assertEqual(state["settings_schema"], 1)
        self.assertEqual(state["clock"], "server_v1")
        self.assertEqual(state["server_cycle"], FIRST["cycle_start_utc"])
        self.assertEqual(state["next_reset_utc"], FIRST["next_reset_utc"])
        for field in ("since_utc", "baseline", "excluded_battles", "excluded_receipts", "generation"):
            self.assertEqual(state[field], old[field])
        self.assertEqual(migrated["account_goals"], before["account_goals"])
        self.assertEqual(migrated["account_history"]["EU:101"], before["account_history"]["EU:101"])
        self.assertEqual(self.config, before)
        self.assertIsNone(ensure_server_history_clock(migrated, "NA", "101", NOW, FIRST))
        self.assertFalse(server_reset_due(migrated, "NA", "101", NOW, FIRST))

    def test_unconfigured_account_arms_without_retroactive_reset(self):
        migrated = ensure_server_history_clock({}, "NA", "101", NOW, FIRST)
        state = get_history_state(migrated, "NA", "101")
        self.assertIsNone(state["since_utc"])
        self.assertIsNone(state["baseline"])
        self.assertEqual(state["generation"], 0)
        self.assertNotIn("account_goals", migrated)

    def test_pending_server_clock_never_guesses_and_arms_only_once_ready(self):
        pending = ensure_server_history_clock(self.config, "NA", "101", NOW)
        self.assertEqual(get_history_state(pending, "NA", "101")["mode"], "server")
        self.assertIsNone(get_history_state(pending, "NA", "101")["server_cycle"])
        self.assertIsNone(ensure_server_history_clock(pending, "NA", "101", NOW))
        self.assertFalse(server_reset_due(pending, "NA", "101", NOW))
        armed = ensure_server_history_clock(pending, "NA", "101", NOW, FIRST)
        self.assertEqual(get_history_state(armed, "NA", "101")["server_cycle"], FIRST["cycle_start_utc"])
        self.assertFalse(server_reset_due(armed, "NA", "101", NOW, FIRST))
        self.assertEqual(armed["account_goals"], self.config["account_goals"])

    def test_explicit_new_manual_choice_is_never_migrated(self):
        explicit = parse_history_settings({"mode": "manual"}, self.config, "NA", "101", NOW)
        self.assertEqual(get_history_state(explicit, "NA", "101")["settings_schema"], 1)
        self.assertIsNone(ensure_server_history_clock(explicit, "NA", "101", TOMORROW, SECOND))
        self.assertFalse(server_reset_due(explicit, "NA", "101", TOMORROW, SECOND))

    def test_explicit_legacy_daily_schedule_is_preserved(self):
        daily = parse_history_settings({"mode": "daily", "hour": 9}, self.config, "NA", "101", NOW)
        daily["account_history"]["NA:101"].pop("settings_schema")
        self.assertIsNone(ensure_server_history_clock(daily, "NA", "101", NOW, FIRST))
        self.assertEqual(get_history_state(daily, "NA", "101")["mode"], "daily")

    def test_server_setting_arms_current_cycle_and_forces_goal_clear_policy(self):
        selected = self.server()
        state = get_history_state(selected, "NA", "101", NOW, FIRST)
        self.assertEqual(state["server_cycle"], FIRST["cycle_start_utc"])
        self.assertFalse(state["preserve_goal"])
        self.assertEqual(state["generation"], 3)
        self.assertEqual(selected["account_goals"], self.config["account_goals"])
        self.assertFalse(server_reset_due(selected, "NA", "101", NOW, FIRST))

    def test_saving_same_settings_does_not_consume_a_due_server_day(self):
        selected = self.server()
        saved = parse_history_settings({"mode": "server"}, selected, "NA", "101", TOMORROW, SECOND)
        self.assertEqual(get_history_state(saved, "NA", "101")["server_cycle"], FIRST["cycle_start_utc"])
        self.assertTrue(server_reset_due(saved, "NA", "101", TOMORROW, SECOND))

    def test_reenabling_server_mode_rearms_current_cycle_without_reset(self):
        selected = self.server()
        manual = parse_history_settings({"mode": "manual"}, selected, "NA", "101", TOMORROW, SECOND)
        resumed = parse_history_settings({"mode": "server"}, manual, "NA", "101", TOMORROW, SECOND)
        self.assertEqual(get_history_state(resumed, "NA", "101")["server_cycle"], SECOND["cycle_start_utc"])
        self.assertFalse(server_reset_due(resumed, "NA", "101", TOMORROW, SECOND))
        self.assertEqual(resumed["account_goals"], selected["account_goals"])

    def test_server_day_advance_resets_once_with_observed_balance_and_disables_goal(self):
        selected = self.server()
        before = copy.deepcopy(selected)
        self.assertTrue(server_reset_due(selected, "NA", "101", TOMORROW, SECOND))
        reset = reset_history_config(selected, "NA", "101", 25901536, TOMORROW,
            ["same-second-old"], ["same-second-receipt"], automatic=True, server_clock=SECOND)
        state = get_history_state(reset, "NA", "101", TOMORROW, SECOND)
        self.assertEqual(state["baseline"], 25901536)
        self.assertEqual(state["since_utc"], TOMORROW)
        self.assertEqual(state["generation"], 4)
        self.assertEqual(state["server_cycle"], SECOND["cycle_start_utc"])
        self.assertEqual(reset["account_goals"]["NA:101"], {"schema": 2,
            "mode": "balance_growth", "target": 0, "baseline": None,
            "since_utc": None, "reset_generation": 5})
        self.assertEqual(reset["credit_target"], 0)
        self.assertFalse(server_reset_due(reset, "NA", "101", TOMORROW, SECOND))
        self.assertEqual(selected, before)
        self.assertEqual(reset["account_goals"]["EU:101"], before["account_goals"]["EU:101"])
        self.assertEqual(reset["unrelated"], before["unrelated"])

    def test_days_offline_apply_one_reset_from_first_observed_balance(self):
        selected = self.server()
        later = {"cycle_start_utc": "2026-10-24T09:30:00Z", "next_reset_utc": "2026-10-25T09:30:00Z"}
        now = "2026-10-24T16:00:00Z"
        self.assertTrue(server_reset_due(selected, "NA", "101", now, later))
        reset = reset_history_config(selected, "NA", "101", 28000000, now,
            [], [], automatic=True, server_clock=later)
        state = get_history_state(reset, "NA", "101")
        self.assertEqual(state["generation"], 4)
        self.assertEqual(state["since_utc"], now)
        self.assertEqual(state["baseline"], 28000000)
        self.assertFalse(server_reset_due(reset, "NA", "101", now, later))

    def test_stale_clock_reconnect_and_backward_cycle_cannot_reset(self):
        selected = self.server()
        self.assertFalse(server_reset_due(selected, "NA", "101", NOW, FIRST))
        self.assertFalse(server_reset_due(selected, "NA", "101", TOMORROW, FIRST))
        older = {"cycle_start_utc": "2026-10-18T11:00:00Z", "next_reset_utc": "2026-10-19T11:00:00Z"}
        self.assertFalse(server_reset_due(selected, "NA", "101", "2026-10-18T12:30:00Z", older))
        self.assertIsNone(ensure_server_history_clock(selected, "NA", "101", "2026-10-18T12:30:00Z", older))

    def test_invalid_native_context_never_enables_or_reports_a_guessed_cutoff(self):
        for context in (None, [], {}, {"next_reset_utc": FIRST["next_reset_utc"]},
                {"cycle_start_utc": True, "next_reset_utc": FIRST["next_reset_utc"]},
                {"cycle_start_utc": "invalid", "next_reset_utc": FIRST["next_reset_utc"]},
                {"cycle_start_utc": FIRST["next_reset_utc"], "next_reset_utc": FIRST["cycle_start_utc"]},
                {"cycle_start_utc": "2026-10-19T13:00:00Z", "next_reset_utc": FIRST["next_reset_utc"]},
                {"cycle_start_utc": FIRST["cycle_start_utc"], "next_reset_utc": NOW}):
            pending = self.server(context)
            state = get_history_state(pending, "NA", "101", NOW, context)
            self.assertIsNone(state["server_cycle"])
            self.assertIsNone(state["next_reset_utc"])
            self.assertFalse(server_reset_due(pending, "NA", "101", NOW, context))

    def test_late_previous_day_battles_receipts_and_same_second_ids_stay_hidden(self):
        reset = reset_history_config(self.server(), "NA", "101", 25901536,
            TOMORROW, ["existing"], ["receipt-existing"], automatic=True, server_clock=SECOND)
        state = get_history_state(reset, "NA", "101")
        self.assertFalse(record_visible({"battle_id": "late", "occurred_at": NOW, "completed_at": NOW}, state))
        self.assertFalse(receipt_visible({"id": "receipt-late", "occurred_at": NOW}, state))
        self.assertFalse(record_visible({"battle_id": "existing", "completed_at": TOMORROW}, state))
        self.assertTrue(record_visible({"battle_id": "new", "completed_at": TOMORROW}, state))
        self.assertFalse(receipt_visible({"id": "receipt-existing", "occurred_at": TOMORROW}, state))
        self.assertTrue(receipt_visible({"id": "receipt-new", "occurred_at": TOMORROW}, state))

    def test_old_goal_cannot_resume_after_a_server_reset(self):
        reset = reset_history_config(self.server(), "NA", "101", 25901536,
            TOMORROW, [], [], automatic=True, server_clock=SECOND)
        resumed = parse_goal_command("1000000", "balance_growth", reset,
            "2026-10-20T13:00:00Z", 26000000, "NA", "101")
        goal = resumed["account_goals"]["NA:101"]
        self.assertEqual(goal["baseline"], 26000000)
        self.assertEqual(goal["since_utc"], "2026-10-20T13:00:00Z")
        self.assertEqual(goal["target"], 1000000)
        self.assertEqual(goal["reset_generation"], 5)

    def test_server_reset_requires_known_clock_and_balance_before_any_mutation(self):
        selected = self.server()
        before = copy.deepcopy(selected)
        for native in (None, {}, FIRST):
            with self.assertRaises(ValueError):
                reset_history_config(selected, "NA", "101", 25901536,
                    TOMORROW, [], [], automatic=True, server_clock=native)
        with self.assertRaises(ValueError):
            reset_history_config(selected, "NA", "101", None,
                TOMORROW, [], [], automatic=True, server_clock=SECOND)
        self.assertEqual(selected, before)

    def test_explicit_manual_clear_also_disables_goal_and_ignores_preserve(self):
        manual = parse_history_settings({"mode": "manual", "preserve_goal": True},
            self.config, "NA", "101", NOW)
        reset = reset_history_config(manual, "NA", "101", 25901536, NOW,
            [], [], clear_goal=True)
        goal = reset["account_goals"]["NA:101"]
        self.assertEqual(goal["target"], 0)
        self.assertIsNone(goal["baseline"])
        self.assertIsNone(goal["since_utc"])
        self.assertEqual(goal["reset_generation"], 5)

    def test_clearing_goal_creates_an_inactive_goal_if_missing(self):
        selected = parse_history_settings({"mode": "server"}, {}, "NA", "101", NOW, FIRST)
        reset = reset_history_config(selected, "NA", "101", 0,
            TOMORROW, [], [], automatic=True, server_clock=SECOND)
        self.assertEqual(reset["account_history"]["NA:101"]["baseline"], 0)
        self.assertEqual(reset["account_goals"]["NA:101"]["reset_generation"], 1)
        self.assertEqual(reset["account_goals"]["NA:101"]["target"], 0)

    def test_bad_goal_counter_and_nonboolean_clear_are_rejected_atomically(self):
        for counter in (True, -1, "4", 9007199254740991):
            selected = self.server()
            selected["account_goals"]["NA:101"]["reset_generation"] = counter
            before = copy.deepcopy(selected)
            with self.assertRaises(ValueError):
                reset_history_config(selected, "NA", "101", 25901536,
                    TOMORROW, [], [], automatic=True, server_clock=SECOND)
            self.assertEqual(selected, before)
        with self.assertRaises(ValueError):
            reset_history_config(self.config, "NA", "101", 25901536,
                NOW, [], [], clear_goal=1)

    def test_schema_marker_must_be_integer_one_and_is_account_scoped(self):
        for marker in (True, "1", 1.0, None, -1):
            config = copy.deepcopy(self.config)
            config["account_history"]["NA:101"]["settings_schema"] = marker
            self.assertNotIn("settings_schema", get_history_state(config, "NA", "101"))
        selected = self.server()
        self.assertFalse(server_reset_due(selected, "NA", "202", TOMORROW, SECOND))
        self.assertFalse(server_reset_due(selected, "EU", "101", TOMORROW, SECOND))


if __name__ == "__main__":
    unittest.main()
