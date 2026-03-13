DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

_DEJAVU = '/usr/share/fonts/truetype/dejavu'
FONT_PATH        = f'{_DEJAVU}/DejaVuSans.ttf'
FONT_MEDIUM_PATH = f'{_DEJAVU}/DejaVuSans-Bold.ttf'
FONT_BOLD_PATH   = f'{_DEJAVU}/DejaVuSans-Bold.ttf'

# GPIO pins for buttons (adjust to your wiring)
BTN_NEXT_PIN   = 5
BTN_PREV_PIN   = 6
BTN_BOUNCE_TIME = 0.1   # seconds — increase if double-press, decrease if sluggish

# --- Timezone (IANA name) ---
# Pi reads system time from NTP — this must match the Pi's configured timezone.
# Run `timedatectl set-timezone Europe/Kyiv` on the Pi if needed.
TIMEZONE = 'Europe/Kyiv'

# --- Work hours (24-hour format) ---
# Bullet 1 in clock widget: "Work ends in X" / "Work starts in X"
WORK_START = 10   # work begins at 10:00
WORK_END   = 19   # work ends   at 19:00

# --- Date/time override for testing ---
# MOCK_NOW: freeze time at a specific datetime (all components see this time).
# TIME_OFFSET: shift real time by a timedelta (time still advances).
#   Example: set offset so current time maps to 23:57 → scheduler ticks through midnight live.
# Leave both as None for normal operation.
MOCK_NOW    = None
TIME_OFFSET = None
