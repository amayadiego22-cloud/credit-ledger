import calendar
import datetime
import unittest
from unittest.mock import patch

from capture import local_clock
from timezone_fixtures import mock_local_timezone


def epoch(utc):
    return calendar.timegm(datetime.datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").timetuple())


class LocalClockTests(unittest.TestCase):
    def test_six_am_boundaries_use_the_pc_timezone_and_local_date(self):
        cases = (
            ("UTC", "2026-10-18T05:59:59Z", "2026-10-17T06:00:00Z", "2026-10-18T06:00:00Z"),
            ("America/Bogota", "2026-10-18T10:59:59Z", "2026-10-17T11:00:00Z", "2026-10-18T11:00:00Z"),
            ("Asia/Kolkata", "2026-10-18T00:29:59Z", "2026-10-17T00:30:00Z", "2026-10-18T00:30:00Z"),
            ("Asia/Tokyo", "2026-10-17T20:59:59Z", "2026-10-16T21:00:00Z", "2026-10-17T21:00:00Z"),
            ("Europe/Madrid", "2026-10-18T03:59:59Z", "2026-10-17T04:00:00Z", "2026-10-18T04:00:00Z"),
            ("Australia/Sydney", "2026-10-17T18:59:59Z", "2026-10-16T19:00:00Z", "2026-10-17T19:00:00Z"))
        for zone, before, previous, following in cases:
            with mock_local_timezone(zone):
                self.assertEqual(local_clock.daily_boundary_utc(before, 6), previous)
                self.assertEqual(local_clock.next_daily_reset_utc(before, 6), following)
                self.assertEqual(local_clock.daily_boundary_utc(following, 6), following)
                self.assertGreater(local_clock.next_daily_reset_utc(following, 6), following)

    def test_next_calendar_day_is_twenty_three_or_twenty_five_utc_hours_across_dst(self):
        cases = (
            ("Europe/Madrid", "2026-03-28T05:00:00Z", "2026-03-29T04:00:00Z", 23),
            ("Europe/Madrid", "2026-10-24T04:00:00Z", "2026-10-25T05:00:00Z", 25),
            ("Australia/Sydney", "2026-10-02T20:00:00Z", "2026-10-03T19:00:00Z", 23),
            ("Australia/Sydney", "2026-04-03T19:00:00Z", "2026-04-04T20:00:00Z", 25))
        for zone, current, expected, hours in cases:
            with mock_local_timezone(zone):
                following = local_clock.next_daily_reset_utc(current, 6)
                self.assertEqual(following, expected)
                self.assertEqual(epoch(following) - epoch(current), hours * 3600)

    def test_repeated_two_am_is_always_its_first_occurrence(self):
        for zone, first, second, next_day in (
            ("Europe/Madrid", "2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z", "2026-10-26T01:00:00Z"),
            ("Australia/Sydney", "2026-04-04T15:30:00Z", "2026-04-04T16:30:00Z", "2026-04-05T16:00:00Z")):
            with mock_local_timezone(zone):
                boundary = local_clock.daily_boundary_utc(first, 2)
                self.assertEqual(local_clock.daily_boundary_utc(second, 2), boundary)
                self.assertLessEqual(boundary, first)
                self.assertEqual(local_clock.next_daily_reset_utc(second, 2), next_day)

    def test_missing_two_am_moves_forward_to_first_valid_time(self):
        for zone, before, expected in (
            ("Europe/Madrid", "2026-03-29T00:59:59Z", "2026-03-29T01:00:00Z"),
            ("Australia/Sydney", "2026-10-03T15:59:59Z", "2026-10-03T16:00:00Z")):
            with mock_local_timezone(zone):
                self.assertLess(local_clock.daily_boundary_utc(before, 2), before)
                self.assertEqual(local_clock.next_daily_reset_utc(before, 2), expected)
                self.assertEqual(local_clock.daily_boundary_utc(expected, 2), expected)
                self.assertGreater(local_clock.next_daily_reset_utc(expected, 2), expected)

    def test_labels_include_numeric_offset_for_the_exact_instant(self):
        with mock_local_timezone("Asia/Kolkata"):
            self.assertEqual(local_clock.time_label("2026-10-18T00:30:00Z"),
                "18/10/2026 06:00 (hora local, UTC+05:30)")
            self.assertEqual(local_clock.time_label("2026-10-18T00:30:00Z", compact=True), "18/10 06:00")
            self.assertEqual(local_clock.timezone_label("2026-10-18T00:30:00Z"),
                "Hora local del equipo (UTC+05:30)")
        with mock_local_timezone("America/Bogota"):
            self.assertEqual(local_clock.time_label("2026-10-18T00:30:00Z"),
                "17/10/2026 19:30 (hora local, UTC-05:00)")
        with mock_local_timezone("UTC"):
            self.assertEqual(local_clock.timezone_label("2026-10-18T00:30:00Z"),
                "Hora local del equipo (UTC+00:00)")

    def test_label_offsets_change_with_daylight_savings_at_the_target_instant(self):
        for zone, before, after, before_offset, after_offset in (
            ("Europe/Madrid", "2026-03-29T00:30:00Z", "2026-03-29T01:30:00Z", "+01:00", "+02:00"),
            ("Australia/Sydney", "2026-10-03T15:30:00Z", "2026-10-03T16:30:00Z", "+10:00", "+11:00")):
            with mock_local_timezone(zone):
                self.assertIn("UTC" + before_offset, local_clock.timezone_label(before))
                self.assertIn("UTC" + after_offset, local_clock.timezone_label(after))
                self.assertIn("UTC" + before_offset, local_clock.time_label(before))
                self.assertIn("UTC" + after_offset, local_clock.time_label(after))

    def test_invalid_dates_and_os_conversion_failures_do_not_invent_a_reset(self):
        for value in (None, True, "", "2026-02-30T00:00:00Z", "2026-10-18T00:00:00+00:00"):
            self.assertEqual(local_clock.time_label(value), "")
            self.assertEqual(local_clock.timezone_label(value), "")
            with self.assertRaises(ValueError):
                local_clock.daily_boundary_utc(value, 6)
        with patch.object(local_clock.time, "mktime", side_effect=OSError("OS unavailable")):
            with self.assertRaises(ValueError):
                local_clock.next_daily_reset_utc("2026-10-18T00:00:00Z", 6)


if __name__ == "__main__":
    unittest.main()
