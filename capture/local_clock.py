# -*- coding: utf-8 -*-
"""Local Windows/OS calendar conversions without a timezone dependency."""
import calendar
import datetime
import math
import time

try:
    string_types = (basestring,)
    integer_types = (int, long)
except NameError:
    string_types = (str,)
    integer_types = (int,)


_STAMP = "%Y-%m-%dT%H:%M:%SZ"


def _epoch(utc):
    if not isinstance(utc, string_types):
        raise ValueError("a canonical UTC timestamp is required")
    try:
        parsed = datetime.datetime.strptime(utc, _STAMP)
        if parsed.strftime(_STAMP) != utc:
            raise ValueError("a canonical UTC timestamp is required")
        return calendar.timegm(parsed.timetuple())
    except (TypeError, ValueError, OverflowError):
        raise ValueError("a canonical UTC timestamp is required")


def _offset_text(epoch, local):
    # Reinterpret the local calendar as UTC to obtain the offset at this exact
    # instant. Python 2.7 on Windows does not expose tm_gmtoff.
    offset = int(calendar.timegm(local) - epoch)
    minutes = abs(offset) // 60
    return "UTC%s%02d:%02d" % ("+" if offset >= 0 else "-", minutes // 60, minutes % 60)


def time_label(utc, compact=False, language="es"):
    """Render the configured PC timezone; invalid/unknown dates stay empty."""
    try:
        epoch = _epoch(utc)
        local = time.localtime(epoch)
        if language == "en":
            month = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                     "Sep", "Oct", "Nov", "Dec")[local.tm_mon - 1]
            if compact:
                return "%02d %s %02d:%02d" % (local.tm_mday, month, local.tm_hour, local.tm_min)
            return u"%02d %s %04d %02d:%02d (local time, %s)" % (
                local.tm_mday, month, local.tm_year, local.tm_hour, local.tm_min,
                _offset_text(epoch, local))
        if compact:
            return "%02d/%02d %02d:%02d" % (local.tm_mday, local.tm_mon,
                                            local.tm_hour, local.tm_min)
        return u"%02d/%02d/%04d %02d:%02d (hora local, %s)" % (
            local.tm_mday, local.tm_mon, local.tm_year, local.tm_hour,
            local.tm_min, _offset_text(epoch, local))
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def timezone_label(utc, language="es"):
    try:
        epoch = _epoch(utc)
        if language == "en":
            return u"Computer's local time (%s)" % _offset_text(epoch, time.localtime(epoch))
        return u"Hora local del equipo (%s)" % _offset_text(epoch, time.localtime(epoch))
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def _boundary_on_date(day, hour):
    """Choose one stable instant per local date, including DST folds/gaps."""
    desired = (day.year, day.month, day.day, hour, 0, 0)
    exact, forward = set(), []
    for daylight in (-1, 0, 1):
        try:
            candidate = time.mktime(desired + (0, 0, daylight))
            if math.isnan(candidate) or math.isinf(candidate):
                continue
            observed = tuple(time.localtime(candidate)[:6])
            if observed == desired:
                exact.add(int(candidate))
            elif observed > desired:
                forward.append((observed, int(candidate)))
        except (TypeError, ValueError, OverflowError, OSError):
            continue
    if exact:
        # Both occurrences of a repeated hour resolve to its first occurrence.
        return min(exact)
    if forward:
        # A missing hour resolves forward (normally 02:00 -> 03:00).
        return min(forward)[1]
    raise ValueError("the OS could not resolve the local reset time")


def _boundaries(now_utc, hour):
    if isinstance(hour, bool) or not isinstance(hour, integer_types) or not 0 <= hour <= 23:
        raise ValueError("reset hour must be an integer from 0 to 23")
    now = _epoch(now_utc)
    try:
        local = time.localtime(now)
        today = datetime.date(local.tm_year, local.tm_mon, local.tm_mday)
        # These are calendar dates, never a fixed 86400-second UTC increment.
        dates = (today - datetime.timedelta(days=1), today,
                 today + datetime.timedelta(days=1))
        boundaries = set(_boundary_on_date(day, hour) for day in dates)
        latest = max(value for value in boundaries if value <= now)
        following = min(value for value in boundaries if value > now)
        return latest, following
    except (TypeError, ValueError, OverflowError, OSError):
        raise ValueError("the OS could not resolve the local reset schedule")


def _utc_label(epoch):
    return time.strftime(_STAMP, time.gmtime(epoch))


def daily_boundary_utc(now_utc, hour):
    return _utc_label(_boundaries(now_utc, hour)[0])


def next_daily_reset_utc(now_utc, hour):
    return _utc_label(_boundaries(now_utc, hour)[1])
