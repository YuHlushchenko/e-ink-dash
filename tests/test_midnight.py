"""
Live test: shifts time to 23:57 so you can watch the scheduler tick through midnight.
Run on Pi: python3 tests/test_midnight.py
Stop with Ctrl+C.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from datetime import datetime
from zoneinfo import ZoneInfo

real_now = datetime.now(tz=ZoneInfo(config.TIMEZONE))
target   = real_now.replace(hour=23, minute=59, second=0, microsecond=0)
config.TIME_OFFSET = target - real_now

import main
main.main()
