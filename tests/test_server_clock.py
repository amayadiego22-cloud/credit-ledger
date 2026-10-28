"""Native server settings, corrected time, and stable day boundaries."""
import calendar
import datetime
import sys
import types
import unittest
from unittest.mock import patch

from capture.server_clock import native_server_clock, server_day_clock


def epoch(stamp):
    return calendar.timegm(datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").timetuple())


class ServerClockTests(unittest.TestCase):
    def test_exact_boundary_and_fractional_samples_have_stable_keys(self):
        reset = epoch("2026-10-19T09:30:00Z")
        self.assertEqual(server_day_clock(reset - .01, 34200)["cycle_start_utc"], "2026-10-18T09:30:00Z")
        for fraction in (0, .01, .5, .999):
            clock = server_day_clock(reset + fraction, 34200)
            self.assertEqual(clock["cycle_start_utc"], "2026-10-19T09:30:00Z")
            self.assertEqual(clock["next_reset_utc"], "2026-10-20T09:30:00Z")
            self.assertEqual(clock["server_now_utc"], "2026-10-19T09:30:00Z")

    def test_epoch_does_not_depend_on_pc_timezone_or_six_am(self):
        for offset, expected in ((0, "00:00:00"), (1, "00:00:01"), (86399, "23:59:59")):
            clock = server_day_clock(epoch("2026-10-19T23:59:59Z"), offset)
            self.assertEqual(clock["cycle_start_utc"], "2026-10-19T" + expected + "Z")

    def test_invalid_or_uninitialized_input_never_guesses_a_day(self):
        now = epoch("2026-10-19T10:00:00Z")
        for stamp in (None, True, "123", 0, -1, float("inf"), float("nan"), 10 ** 10000):
            self.assertIsNone(server_day_clock(stamp, 36000))
        for offset in (None, True, "36000", 36000.0, -1, 86400, float("nan")):
            self.assertIsNone(server_day_clock(now, offset))

    def native(self, regional, value=None, error=None):
        calls = []
        def server_now():
            calls.append(1)
            if error:
                raise error
            return epoch("2026-10-19T11:00:00Z") if value is None else value
        helper = types.ModuleType("helpers")
        helper.time_utils = types.SimpleNamespace(getServerUTCTime=server_now)
        player = types.SimpleNamespace(battleResultsCache=None,
                                       serverSettings={"regional_settings": regional})
        with patch.dict(sys.modules, {"helpers": helper}):
            return native_server_clock(player), calls

    def test_current_key_wins_and_time_is_sampled_once(self):
        clock, calls = self.native({"starting_time_of_a_new_game_day": 36000,
                                    "starting_time_of_a_new_day": 21600})
        self.assertEqual(clock["cycle_start_utc"], "2026-10-19T10:00:00Z")
        self.assertEqual(calls, [1])

    def test_legacy_key_only_when_current_key_absent(self):
        clock, _ = self.native({"starting_time_of_a_new_day": 21600})
        self.assertEqual(clock["cycle_start_utc"], "2026-10-19T06:00:00Z")
        clock, _ = self.native({"starting_time_of_a_new_game_day": None,
                                "starting_time_of_a_new_day": 21600})
        self.assertIsNone(clock)

    def test_missing_settings_or_non_account_has_no_midnight_fallback(self):
        self.assertIsNone(native_server_clock(None))
        self.assertIsNone(native_server_clock(types.SimpleNamespace(serverSettings={})))
        for regional in ({}, None, []):
            clock, calls = self.native(regional)
            self.assertIsNone(clock)
            self.assertEqual(calls, [])

    def test_clock_failure_leaves_optional_calendar_unavailable(self):
        clock, _ = self.native({"starting_time_of_a_new_game_day": 36000}, error=ValueError("not ready"))
        self.assertIsNone(clock)


if __name__ == "__main__":
    unittest.main()
