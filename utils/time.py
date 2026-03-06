"""
Central time source for all components.

Uses the Pi's local time via TIMEZONE from config.
Set config.MOCK_NOW = datetime(...) to freeze time for testing.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import config


def get_now() -> datetime:
    """Return current datetime in the configured timezone (or MOCK_NOW if set)."""
    if config.MOCK_NOW is not None:
        mock = config.MOCK_NOW
        if mock.tzinfo is None:
            return mock.replace(tzinfo=ZoneInfo(config.TIMEZONE))
        return mock
    now = datetime.now(tz=ZoneInfo(config.TIMEZONE))
    if config.TIME_OFFSET is not None:
        now += config.TIME_OFFSET
    return now
