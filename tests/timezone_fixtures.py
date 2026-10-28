"""Deterministic OS localtime/mktime replacements; never change process TZ."""
import contextlib
import datetime
import time
from unittest.mock import patch
from zoneinfo import ZoneInfo

from capture import local_clock


@contextlib.contextmanager
def mock_local_timezone(name):
    zone = ZoneInfo(name)

    def localtime(epoch=None):
        if epoch is None:
            epoch = time.time()
        return datetime.datetime.fromtimestamp(epoch, zone).timetuple()

    def mktime(value):
        naive = datetime.datetime(*tuple(value)[:6])
        variants = [naive.replace(tzinfo=zone, fold=0),
                    naive.replace(tzinfo=zone, fold=1)]
        daylight = value[8]
        if daylight in (0, 1):
            matching = [candidate for candidate in variants
                        if bool(candidate.dst()) == bool(daylight)]
            if matching:
                variants = matching
        return variants[0].timestamp()

    with patch.object(local_clock.time, "localtime", side_effect=localtime), \
            patch.object(local_clock.time, "mktime", side_effect=mktime):
        yield
