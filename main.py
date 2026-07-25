"""
e-ink dashboard — main entry point.

Screen 1 update strategy:
  • Every minute   : partial refresh of clock region.
  • Every 5 min    : full refresh (clears ghosting).
  • At midnight    : forced full refresh (calendar + github_contribution update immediately).

Screen 1 GitHub contributions strategy:
  • On startup, at midnight, and every GHOST_CLEAR_AFTER partials (~hourly): background
    thread calls api.github.fetch_contributions(), then (if still on Screen 1) partial-
    refreshes just the grid region — never blocks the per-minute clock tick.
  • On switch to Screen 1: same background fetch, fired from switch_to(0).
  • GITHUB_FETCH_MIN_INTERVAL dedupes near-simultaneous triggers (e.g. switching to
    Screen 1 right after an hourly fetch just ran).
  • render_lock now also guards Screen 1's render/display calls (previously Screen-2-only)
    since this background thread is a second writer to the EPD for Screen 1.

Screen 2 update strategy:
  • On switch      : show animated "Loading..." screen (screens/loading_screen.py)
                      while cache invalidation + prefetch run on a background thread,
                      then full refresh with fresh data (_show_loading_while()).
  • Any timer < 24h: partial refresh Col1+Col2 every minute; full every 5 partials (anti-ghosting).
  • All timers ≥ 1d: full refresh every hour + cache invalidation.
  • Timer hits 0   : detect via has_aired() → invalidate cache + full refresh immediately.

Screen 3 update strategy:
  • Auto-slideshow: new random art every SLIDESHOW_INTERVAL seconds (config.py).
  • On manual switch: immediate new random art regardless of interval.

Network status strategy (wifi icon in the shared Screen 1/2 notif bar):
  • utils.network_status.check_and_update() runs once synchronously at startup (so the
    first frame shows a real status), then every NETWORK_CHECK_INTERVAL seconds forever
    on its own background thread — independent of which screen is showing, so status
    never goes stale while parked on Screen 3.
  • The display is only touched if the status actually changed AND Screen 1 or 2 is
    currently showing (the only screens with a notif bar); then just S1_WIFI_REGION is
    partial-refreshed. A stable connection therefore never triggers a partial refresh
    from this path at all — components/art_panel.py reads the cached status on every
    full render anyway, so switch-in/hourly/midnight refreshes always show it fresh
    without any extra work here.

Clock partial-refresh region (x must be multiple of 8):
  CLOCK_X0=224, CLOCK_Y0=8, CLOCK_X1=496, CLOCK_Y1=272

Screen 2 partial-refresh regions (x must be multiple of 8):
  Col2 (upcoming episodes): x0=272, x1=528, y0=46, y1=442
  Col1 (upcoming releases): x0=0,   x1=272, y0=80, y1=442

render_lock guards renderer/EPD access shared between the gpiozero button-callback
thread (Screen 2's loading animation, Screen 1 switch-in), the GitHub background-fetch
thread (Screen 1's contributions grid), the network-status poll thread (wifi icon), and
this function's scheduler loop. Screen 1 and Screen 2 are now both covered; Screen 3
render calls remain unlocked (accepted gap — Screen 3 has no background writer thread
of its own).
"""
import time
import signal
import threading
import itertools
from gpiozero import Button
from renderer.base import Renderer
from screens.screen1 import Screen1
from screens.screen2 import Screen2
from screens.screen3 import Screen3
from screens.loading_screen import LoadingScreen
from utils.time import get_now
import api.screen2_data as data_layer
import api.github as github_api
import utils.network_status as network_status
from config import BTN_NEXT_PIN, BTN_PREV_PIN, BTN_BOUNCE_TIME, SLIDESHOW_INTERVAL

# Screen 2 loading animation — seconds between dot-frame updates
DOT_INTERVAL = 0.8

# Screen 1 — clock partial-refresh region (8-pixel-aligned x)
CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1 = 224, 8, 496, 272

# Screen 1 — GitHub contributions grid partial-refresh region (8-pixel-aligned x)
S1_GITHUB_REGION = (0, 274, 800, 466)

# Minimum seconds between GitHub contribution fetches — dedupes near-simultaneous
# triggers (nightly/hourly/on-switch can coincide).
GITHUB_FETCH_MIN_INTERVAL = 300

# Screen 1/2 — wifi status icon partial-refresh region (8-pixel-aligned x), inside
# the shared notif bar (x=14, y=14, w=202) drawn by both screens.
S1_WIFI_REGION = (56, 14, 80, 42)

# Seconds between network connectivity checks — background poll loop, independent
# of which screen is currently shown (see "Network status helpers" below).
NETWORK_CHECK_INTERVAL = 30

# Screen 2 — partial-refresh regions (x must be multiple of 8)
# Col2: upcoming episodes timers (after header at y=40, before footer at y=442)
S2_COL2 = (272, 46, 528, 442)
# Col1: upcoming releases timers (after notif bar + header at y=74, before footer)
S2_COL1 = (0, 80, 272, 442)

# Full refresh every N partial refreshes to clear ghosting.
# Real-world projects use 30-60 partials between full refreshes (Byron Knoll, mendhak).
# 60 = full refresh every hour (1 partial/min × 60 min).
GHOST_CLEAR_AFTER = 60

# Screen 2 hourly full refresh interval (seconds)
S2_REFRESH_INTERVAL = 3600


def main():
    renderer = Renderer()
    renderer.init()
    renderer.clear()

    screen1 = Screen1(renderer)
    screen2 = Screen2(renderer)
    screen3 = Screen3(renderer)
    loading = LoadingScreen(renderer)

    # Guards renderer/EPD access shared between the gpiozero button-callback thread
    # (Screen 2 loading animation, Screen 1 switch-in), the GitHub background-fetch
    # thread (Screen 1 contributions grid), and this function's scheduler loop.
    render_lock = threading.Lock()

    current_screen      = 0
    s1_partial_count    = 0
    s2_partial_count    = 0
    last_s2_full        = 0.0   # epoch time of last Screen 2 full refresh
    s3_tick             = 0     # loop iterations since last Screen 3 art change
    last_maintenance    = None  # date of last display_maintenance() call
    last_github_fetch   = 0.0   # epoch time of last GitHub contributions fetch attempt

    # ── Screen 1 helpers ────────────────────────────────────────────────────

    def _show(image, maintenance=False):
        """Display full screen — maintenance mode once daily for display longevity."""
        if maintenance:
            renderer.display_maintenance(image)
        else:
            renderer.display(image)

    def s1_full_refresh(dt=None, maintenance=False):
        nonlocal s1_partial_count
        if dt is None:
            dt = get_now()
        _show(screen1.render(dt), maintenance)
        s1_partial_count = 0

    def _github_fetch_async():
        """Fetch fresh GitHub contributions off the render path, deduped by
        GITHUB_FETCH_MIN_INTERVAL. On success, partial-refreshes just the grid
        region — but only if Screen 1 is still showing, so it never draws over
        Screen 2/3 content if the user switched away while the fetch was in flight."""
        nonlocal last_github_fetch
        now_ts = time.time()
        if now_ts - last_github_fetch < GITHUB_FETCH_MIN_INTERVAL:
            return
        last_github_fetch = now_ts

        def _work():
            _, err = github_api.fetch_contributions()
            if err is None and current_screen == 0:
                with render_lock:
                    img = screen1.render(get_now())
                    renderer.display_partial(img, *S1_GITHUB_REGION)

        threading.Thread(target=_work, daemon=True).start()

    # ── Screen 2 helpers ────────────────────────────────────────────────────

    def s2_full_refresh(maintenance=False):
        nonlocal s2_partial_count, last_s2_full
        _show(screen2.render(), maintenance)
        s2_partial_count = 0
        last_s2_full = time.time()

    def s2_partial_refresh():
        nonlocal s2_partial_count
        # Ghost-clear: after N partials do a true full refresh, resume next minute
        if s2_partial_count >= GHOST_CLEAR_AFTER:
            s2_full_refresh(maintenance=True)
            return
        # First partial after a full refresh: switch hardware to partial mode
        if s2_partial_count == 0:
            renderer.init_partial()
        img = screen2.render()
        renderer.display_partial(img, *S2_COL2)
        renderer.display_partial(img, *S2_COL1)
        s2_partial_count += 1

    # ── Network status helpers ──────────────────────────────────────────────

    def _network_check_loop():
        """Poll connectivity every NETWORK_CHECK_INTERVAL seconds, forever, regardless
        of which screen is showing (so the status never goes stale while on Screen 3).
        Only touches the display if the status actually changed AND Screen 1/2 (the
        only screens with a notif bar) is currently showing."""
        while True:
            time.sleep(NETWORK_CHECK_INTERVAL)
            old = network_status.get_status()
            new = network_status.check_and_update()
            if new != old and current_screen in (0, 1):
                with render_lock:
                    if current_screen == 0:
                        img = screen1.render(get_now())
                    else:
                        img = screen2.render()
                    renderer.display_partial(img, *S1_WIFI_REGION)

    # ── Screen switching ─────────────────────────────────────────────────────

    def s3_show(maintenance=False):
        _show(screen3.render(), maintenance)

    def _show_loading_while(work_fn, finish_fn):
        """Show an animated 'Loading...' screen while work_fn() runs on a
        background thread, then call finish_fn() to render the real content.
        Reusable for any screen switch that needs to block on a network
        fetch first — not tied to Screen 2 specifically."""
        with render_lock:
            _show(loading.render(0))   # full white "Loading" — confirms the press

        thread = threading.Thread(target=work_fn)
        thread.start()

        region = loading.text_region()
        dots = itertools.cycle([0, 1, 2, 3, 2, 1])
        next(dots)   # skip the 0 already drawn above
        while thread.is_alive():
            with render_lock:
                renderer.display_partial(loading.render(next(dots)), *region)
            thread.join(timeout=DOT_INTERVAL)

        with render_lock:
            finish_fn()

    def switch_to(idx):
        nonlocal current_screen, s3_tick
        current_screen = idx
        if idx == 0:
            with render_lock:
                s1_full_refresh()
                renderer.init_partial()
            _github_fetch_async()
        elif idx == 1:
            def _prefetch():
                data_layer.invalidate_cache()
                data_layer.prefetch_all()

            _show_loading_while(_prefetch, s2_full_refresh)
        else:   # idx == 2
            screen3.pick_random()
            s3_show()
            s3_tick = 0

    btn_next = Button(BTN_NEXT_PIN, bounce_time=BTN_BOUNCE_TIME)
    btn_prev = Button(BTN_PREV_PIN, bounce_time=BTN_BOUNCE_TIME)
    btn_next.when_pressed = lambda: switch_to((current_screen + 1) % 3)
    btn_prev.when_pressed = lambda: switch_to((current_screen - 1) % 3)

    # ── Initial render ───────────────────────────────────────────────────────

    network_status.check_and_update()   # synchronous — first frame should show real status

    now = get_now()
    last_date        = now.date()
    last_maintenance = now.date()
    with render_lock:
        s1_full_refresh(maintenance=True)   # startup counts as daily maintenance
        renderer.init_partial()
    _github_fetch_async()   # warm the contributions grid on boot
    threading.Thread(target=_network_check_loop, daemon=True).start()

    # ── Scheduler loop — wakes on each minute boundary ───────────────────────

    while True:
        now = get_now()
        secs_to_next = 60 - now.second - now.microsecond / 1_000_000
        time.sleep(max(0.5, secs_to_next))

        today = get_now().date()
        do_maintenance = last_maintenance != today

        if current_screen == 0:
            dt = get_now()
            if dt.date() != last_date:
                last_date = dt.date()
                with render_lock:
                    s1_full_refresh(dt, maintenance=True)
                    renderer.init_partial()
                last_maintenance = today
                _github_fetch_async()   # nightly refresh
            elif do_maintenance:
                with render_lock:
                    s1_full_refresh(dt, maintenance=True)
                    renderer.init_partial()
                last_maintenance = today
                _github_fetch_async()   # nightly refresh (maintenance-day fallback path)
            elif s1_partial_count >= GHOST_CLEAR_AFTER:
                with render_lock:
                    s1_full_refresh(dt, maintenance=True)  # true full refresh every 5 partials
                    renderer.init_partial()
                _github_fetch_async()   # hourly refresh
            else:
                with render_lock:
                    img = screen1.render(dt)
                    renderer.display_partial(img, CLOCK_X0, CLOCK_Y0, CLOCK_X1, CLOCK_Y1)
                s1_partial_count += 1

        elif current_screen == 1:
            if data_layer.has_aired():
                # Episode aired since last cache — get fresh data immediately
                data_layer.invalidate_cache()
                data_layer.prefetch_all()
                with render_lock:
                    s2_full_refresh(maintenance=do_maintenance)
                if do_maintenance:
                    last_maintenance = today
            elif data_layer.has_imminent():
                # At least one timer < 24h — keep minutes up-to-date
                if do_maintenance:
                    with render_lock:
                        s2_full_refresh(maintenance=True)
                    last_maintenance = today
                else:
                    with render_lock:
                        s2_partial_refresh()
            elif time.time() - last_s2_full >= S2_REFRESH_INTERVAL:
                # Hourly refresh — pull fresh API data
                data_layer.invalidate_cache()
                data_layer.prefetch_all()
                with render_lock:
                    s2_full_refresh(maintenance=do_maintenance)
                if do_maintenance:
                    last_maintenance = today

        elif current_screen == 2:
            s3_tick += 1
            if s3_tick >= max(1, SLIDESHOW_INTERVAL // 60):
                s3_tick = 0
                screen3.pick_random()
                s3_show(maintenance=do_maintenance)
                if do_maintenance:
                    last_maintenance = today


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: exit(0))
    main()
