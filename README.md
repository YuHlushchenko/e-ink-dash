# e-ink-dash

Personal dashboard for a 7.5" e-ink display, running on Raspberry Pi Zero 2W.

## Hardware

- Raspberry Pi Zero 2W
- Waveshare 7.5" e-Paper HAT (800x480, B&W), Driver HAT Rev2.3
- Driver HAT switches: Display Config B, Interface Config 0 (4-line SPI)

## Setup

**OS:** Raspberry Pi OS Lite 32-bit (Trixie)
**SPI:** enabled (`/dev/spidev0.0`, `/dev/spidev0.1`)

**Dependencies:**

```bash
# Waveshare e-Paper library
pip3 install -e /home/<user>/e-Paper/RaspberryPi_JetsonNano/python --break-system-packages

# Project dependencies
pip3 install -r requirements.txt --break-system-packages

# System library for SVG rendering
sudo apt install libcairo2 fonts-dejavu-core
```

**Font:** DejaVu Sans — `/usr/share/fonts/truetype/dejavu/`
Regular (`DejaVuSans.ttf`) + Bold (`DejaVuSans-Bold.ttf`). No Medium weight — Bold is aliased.

## Stack

- Python + Pillow — rendering, Floyd-Steinberg dithering (grayscale → 1-bit for display)
- Waveshare e-Paper library (`waveshare_epd.epd7in5_V2`)
- cairosvg + libcairo2 — SVG icon rendering
- gpiozero — hardware buttons
- python-dotenv — API credentials from `.env`

## Project Structure

```
e-ink-dash/
├── main.py                      # entry point, scheduler loop, screen switching
├── config.py                    # display size, font paths, GPIO pins, timezone, work hours
├── renderer/
│   └── base.py                  # Renderer: init / display / display_partial / clear / sleep
├── screens/
│   ├── base_screen.py
│   ├── screen1.py               # Clock + calendar + year progress + pixel art (done)
│   ├── screen2.py               # AniList + MangaDex (UI done, API TODO)
│   └── screen3.py               # Full-screen anime art slideshow (done)
├── components/
│   ├── clock.py                 # Time, am/pm, countdown bullets
│   ├── calendar.py              # Monthly grid, Sunday-first, today highlight
│   ├── year_progress.py         # GitHub-style year grid + progress bar
│   ├── art_panel.py             # Notification bar (draw_notif_bar) + pixel art panel
│   ├── section_header.py        # Reusable black rounded rect section header
│   ├── date_separator.py        # Date label + horizontal rule
│   ├── release_card.py          # Upcoming Releases card
│   ├── upcoming_card.py         # Upcoming Episodes card (3-state progress bar)
│   ├── queue_card.py            # In Queue card (2-state progress bar)
│   ├── manga_card.py            # Manga Updates card (chapter progress bar)
│   ├── stats_footer.py          # Bottom stats bar with gradient flanks
│   └── pixel_art/
│       └── starfield.py         # Static starfield scene (moon, stars, shooting star)
├── api/                         # API integrations (AniList GraphQL, MangaDex REST)
├── assets/
│   ├── arts/                    # Local anime art images (.jpg, .png) for screen3
│   └── icons/                   # SVG icons (bell, stars, arrows, refresh)
├── cache/                       # SQLite cache for API responses (gitignored)
├── utils/
│   ├── time.py                  # get_now() — timezone-aware, supports MOCK_NOW / TIME_OFFSET
│   └── drawing.py               # draw_gradient_bar() — shared utility
└── tests/
    ├── test_screen1_preview.py  # Render screen1 on hardware
    ├── test_screen2_preview.py  # Render screen2 on hardware
    ├── test_dates.py            # 13 edge-case dates → PNG files in tests/output/
    ├── test_midnight.py         # Live scheduler test, time offset to 23:57
    ├── test_clock.py            # Clock component on hardware
    ├── test_calendar.py         # Calendar component on hardware
    ├── test_year_progress.py    # Year progress on hardware
    ├── test_art_panel.py        # Art panel on hardware
    ├── test_starfield.py        # Starfield on hardware
    ├── test_screen3.py          # Single art display on hardware
    └── test_screen3_slideshow.py# Slideshow loop on hardware
```

## Screens

| # | Content | Status |
|---|---------|--------|
| 1 | Clock · calendar · year progress · pixel art | Done |
| 2 | AniList upcoming releases · manga updates · queue | UI done, API TODO |
| 3 | Full-screen anime art slideshow (local images) | Done |

Screens are switched via two buttons (next / prev, infinite loop).

## Update Strategy (Screen 1)

- **Every minute** — partial refresh of clock region only (fast, ~0.3s)
- **Every 5 minutes** — full refresh to clear ghosting (~3–5s)
- **At midnight** — forced full refresh so calendar and year progress update immediately
- **On startup** — full refresh

## Dev Workflow

Edit files locally via SSHFS mount; run everything via SSH on the Pi:

```bash
# Mount project locally
sshfs <user>@<hostname>:/home/<user>/e-ink-dash ~/mnt/einkdash

# Run a test on hardware
ssh <user>@<hostname> "python3 /home/<user>/e-ink-dash/tests/test_screen1_preview.py"

# Kill stale process holding GPIO/SPI
ssh <user>@<hostname> "sudo pkill -f python3"
```

## Testing Without Hardware

Use `FakeRenderer` and `config.MOCK_NOW` to render to PNG without a display:

```python
import config
from datetime import datetime
config.MOCK_NOW = datetime(2026, 3, 10, 14, 30)

class FakeRenderer:
    width = 800
    height = 480

from screens.screen1 import Screen1
image = Screen1(FakeRenderer()).render()
image.convert('1', dither=Image.FLOYDSTEINBERG).convert('L').save('preview.png')
```
