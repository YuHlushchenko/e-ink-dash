"""
e-ink dashboard — main entry point.

Screen 1 update strategy:
  • Every minute   : partial refresh of clock region.
  • Every 5 min    : full refresh (clears ghosting).
  • At midnight    : forced full refresh (calendar + year_progress update immediately).

Screen 2 update strategy:
  • On switch      : invalidate API cache + full refresh (always fresh data).
  • Any timer < 24h: partial refresh Col1+Col2 every minute; full every 5 partials (anti-ghosting).
  • All timers ≥ 1d: full refresh every hour + cache invalidation.
  • Timer hits 0   : detect via has_aired() → invalidate cache + full refresh immediately.

Screen 3: static art, refreshes only on manual switch (new random art each time).

Clock partial-refresh region (x must be multiple of 8):
  CLOCK_X0=224, CLOCK_Y0=8, CLOCK_X1=496, CLOCK_Y1=272

Screen 2 partial-refresh regions (x must be multiple of 8):
  Col2 (upcoming episodes): x0=272, x1=528, y0=46, y1=442
  Col1 (upcoming releases): x0=0,   x1=272, y0=80, y1=442
"""
import time
import signal
from gpiozero import Button
from renderer.base import Renderer
from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from utils.time import get_now
import api.screen2_data as data_layer
from config import BTN_NEXT_PIN, BTN_PREV_PIN, BTN_BOUNCE_TIME

# Screen 1 — clock partial-refresh region (8-pixel-aligned x)
CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1 = 224, 8, 496, 272

# Screen 2 — partial-refresh regions (x must be multiple of 8)
# Col2: upcoming episodes timers (after header at y=40, before footer at y=442)
S2_COL2 = (272, 46, 528, 442)
# Col1: upcoming releases timers (after notif bar + header at y=74, before footer)
S2_COL1 = (0, 80, 272, 442)

# Full refresh every N partial refreshes to clear ghosting
GHOST_CLEAR_AFTER = 5

# Screen 2 hourly full refresh interval (seconds)
S2_REFRESH_INTERVAL = 3600


def main():
    renderer = Renderer()
    renderer.init()
    renderer.clear()

    screen1 = Screen1(renderer)
    screen2 = Screen2(renderer)
    screen3 = Screen3(renderer)

    current_screen  = 0
    s1_partial_count = 0
    s2_partial_count = 0
    last_s2_full     = 0.0   # epoch time of last Screen 2 full refresh

    # ── Screen 1 helpers ────────────────────────────────────────────────────

    def s1_full_refresh(dt=None):
        nonlocal s1_partial_count
        if dt is None:
            dt = get_now()
        renderer.init()
        renderer.display(screen1.render(dt))
        s1_partial_count = 0

    # ── Screen 2 helpers ────────────────────────────────────────────────────

    def s2_full_refresh():
        nonlocal s2_partial_count, last_s2_full
        renderer.init()
        renderer.display(screen2.render())
        s2_partial_count = 0
        last_s2_full = time.time()

    def s2_partial_refresh():
        nonlocal s2_partial_count
        # Ghost-clear: after N partials do a full refresh, resume next minute
        if s2_partial_count >= GHOST_CLEAR_AFTER:
            s2_full_refresh()
            return
        # First partial after a full refresh: switch hardware to partial mode
        if s2_partial_count == 0:
            renderer.init_partial()
        img = screen2.render()
        renderer.display_partial(img, *S2_COL2)
        renderer.display_partial(img, *S2_COL1)
        s2_partial_count += 1

    # ── Screen switching ─────────────────────────────────────────────────────

    def switch_to(idx):
        nonlocal current_screen
        current_screen = idx
        if idx == 0:
            s1_full_refresh()
            renderer.init_partial()
        elif idx == 1:
            data_layer.invalidate_cache()
            s2_full_refresh()
        else:   # idx == 2
            screen3.pick_random()
            renderer.init()
            renderer.display(screen3.render())

    btn_next = Button(BTN_NEXT_PIN, bounce_time=BTN_BOUNCE_TIME)
    btn_prev = Button(BTN_PREV_PIN, bounce_time=BTN_BOUNCE_TIME)
    btn_next.when_pressed = lambda: switch_to((current_screen + 1) % 3)
    btn_prev.when_pressed = lambda: switch_to((current_screen - 1) % 3)

    # ── Initial render ───────────────────────────────────────────────────────

    s1_full_refresh()
    renderer.init_partial()
    last_date = get_now().date()

    # ── Scheduler loop — wakes on each minute boundary ───────────────────────

    while True:
        now = get_now()
        secs_to_next = 60 - now.second - now.microsecond / 1_000_000
        time.sleep(max(0.5, secs_to_next))

        if current_screen == 0:
            dt = get_now()
            if dt.date() != last_date:
                last_date = dt.date()
                s1_full_refresh(dt)
                renderer.init_partial()
            elif s1_partial_count >= GHOST_CLEAR_AFTER:
                s1_full_refresh(dt)
                renderer.init_partial()
            else:
                img = screen1.render(dt)
                renderer.display_partial(img, CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1)
                s1_partial_count += 1

        elif current_screen == 1:
            if data_layer.has_aired():
                # Episode aired since last cache — get fresh data immediately
                data_layer.invalidate_cache()
                s2_full_refresh()
            elif data_layer.has_imminent():
                # At least one timer < 24h — keep minutes up-to-date
                s2_partial_refresh()
            elif time.time() - last_s2_full >= S2_REFRESH_INTERVAL:
                # Hourly refresh — pull fresh API data
                data_layer.invalidate_cache()
                s2_full_refresh()

        # current_screen == 2: Screen 3 is static, nothing to update


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: exit(0))
    main()
