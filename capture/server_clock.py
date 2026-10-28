# -*- coding: utf-8 -*-
"""Read the account's native game-day calendar without a local-hour fallback."""
import math
import time

try:
    integer_types = (int, long)
except NameError:
    integer_types = (int,)


_STAMP = "%Y-%m-%dT%H:%M:%SZ"
_DAY = 86400


def server_day_clock(server_epoch, reset_offset):
    """Build stable UTC boundaries from one corrected server-time sample."""
    if (isinstance(server_epoch, bool) or
            not isinstance(server_epoch, integer_types + (float,))):
        return None
    if (isinstance(reset_offset, bool) or not isinstance(reset_offset, integer_types) or
            not 0 <= reset_offset < _DAY):
        return None
    # Reject uninitialized clocks and keep every rendered timestamp canonical.
    if not 946684800 <= server_epoch < 4102444800 or math.isnan(server_epoch) or math.isinf(server_epoch):
        return None
    now = int(server_epoch)
    start = ((now - reset_offset) // _DAY) * _DAY + reset_offset
    try:
        stamp = lambda epoch: time.strftime(_STAMP, time.gmtime(epoch))
        return {"cycle_start_utc": stamp(start), "next_reset_utc": stamp(start + _DAY),
                "server_now_utc": stamp(now)}
    except (ValueError, OverflowError, OSError):
        return None


def native_server_clock(player):
    """Account settings define the day; helpers supplies server-corrected UTC."""
    if player is None or not hasattr(player, "battleResultsCache"):
        return None
    try:
        settings = player.serverSettings
        regional = settings.get("regional_settings")
        if not isinstance(regional, dict):
            return None
        # The legacy key is valid only when the newer key is absent.
        if "starting_time_of_a_new_game_day" in regional:
            offset = regional["starting_time_of_a_new_game_day"]
        elif "starting_time_of_a_new_day" in regional:
            offset = regional["starting_time_of_a_new_day"]
        else:
            return None
        from helpers import time_utils
        return server_day_clock(time_utils.getServerUTCTime(), offset)
    except (AttributeError, KeyError, TypeError, ValueError, ImportError, OverflowError):
        return None
