"""
e-ink dashboard — main entry point.

Update strategy:
  • Every minute   : partial refresh of clock region (fast, no full-screen flash).
  • Every 5 min    : full refresh (clears ghosting).
  • At midnight    : forced full refresh (calendar + year_progress update immediately).
  • On startup     : full refresh.

Clock partial-refresh region (x must be multiple of 8):
  Clock widget sits at x=228, y=14, W=263, H=254.
  Region expanded to nearest byte boundaries: X0=224, Y0=8, X1=496, Y1=272.
"""
import time
import signal
from gpiozero import Button
from renderer.base import Renderer
from screens.screen1 import Screen1
from screens.screen2 import Screen2
from utils.time import get_now
from config import BTN_NEXT_PIN, BTN_PREV_PIN

# Partial refresh region for the clock widget (8-pixel-aligned x)
CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1 = 224, 8, 496, 272

# Full refresh every N partial refreshes to clear ghosting
GHOST_CLEAR_AFTER = 5


def main():
    renderer = Renderer()
    renderer.init()
    renderer.clear()

    screen1 = Screen1(renderer)
    screen2 = Screen2(renderer)

    current_screen = 0   # 0 = screen1, 1 = screen2
    partial_count  = 0

    def full_refresh(dt=None):
        nonlocal partial_count
        if dt is None:
            dt = get_now()
        img = screen1.render(dt) if current_screen == 0 else screen2.render()
        renderer.init()
        renderer.display(img)
        partial_count = 0

    def switch_to(screen_idx):
        nonlocal current_screen
        current_screen = screen_idx
        full_refresh()
        if current_screen == 0:
            renderer.init_partial()

    btn_next = Button(BTN_NEXT_PIN)
    btn_prev = Button(BTN_PREV_PIN)
    btn_next.when_pressed = lambda: switch_to((current_screen + 1) % 2)
    btn_prev.when_pressed = lambda: switch_to((current_screen - 1) % 2)

    # Initial render
    full_refresh()
    renderer.init_partial()

    last_date = get_now().date()

    # Scheduler loop — wakes on each minute boundary
    while True:
        now = get_now()
        secs_to_next = 60 - now.second - now.microsecond / 1_000_000
        time.sleep(max(0.5, secs_to_next))

        if current_screen != 0:
            continue   # screen2 is static; nothing to update

        dt = get_now()

        # Force full refresh at midnight so calendar/year_progress update immediately
        if dt.date() != last_date:
            last_date = dt.date()
            full_refresh(dt)
            renderer.init_partial()
        elif partial_count >= GHOST_CLEAR_AFTER:
            full_refresh(dt)
            renderer.init_partial()
        else:
            img = screen1.render(dt)
            renderer.display_partial(img, CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1)
            partial_count += 1


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: exit(0))
    main()
