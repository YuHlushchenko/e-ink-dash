# e-ink-dash

Personal dashboard for a 7.5" e-ink display, running on Raspberry Pi Zero 2W.

## Hardware

- Raspberry Pi Zero 2W
- Waveshare 7.5" e-Paper HAT (800x480, B&W), Driver HAT Rev2.3
- Driver HAT switches: Display Config B, Interface Config 0 (4-line SPI)
- 2× tactile push buttons (next / prev screen)

### Button Wiring

| Button | Pi Pin | Pi GPIO |
|--------|--------|---------|
| Next   | Board 29 | GPIO 5 |
| Prev   | Board 31 | GPIO 6 |
| GND (shared) | Board 30 | GND |

Each button connects between its GPIO pin and GND. No external pull-up resistor needed — gpiozero enables the internal pull-up automatically (`pull_up=True` by default).

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

**Autostart (systemd):**

```bash
# 1. Copy the example and fill in your username
cp einkdash.service.example einkdash.service
# Edit einkdash.service — replace all <your-username> with your Pi username

# 2. Install and enable
sudo cp einkdash.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable einkdash
sudo systemctl start einkdash

# Check status / logs
sudo systemctl status einkdash
journalctl -u einkdash -f
```

> `einkdash.service` is gitignored (contains local paths). `einkdash.service.example` is the template.

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
│   ├── screen2.py               # AniList + MangaDex dashboard (done)
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
├── api/
│   ├── anilist.py               # AniList GraphQL client, SQLite cache, (data, error) returns
│   ├── mangadex.py              # MangaDex REST client, OAuth2, SQLite cache, (data, error) returns
│   └── screen2_data.py          # Transforms AniList + MangaDex responses into card-ready dicts
├── assets/
│   ├── arts/                    # Local anime art images (.jpg, .png) for screen3
│   └── icons/                   # SVG icons (bell, stars, arrows, refresh)
├── .env.example                 # Template for AniList + MangaDex credentials
├── cache/                       # SQLite cache for API responses (gitignored)
├── utils/
│   ├── time.py                  # get_now() — timezone-aware, supports MOCK_NOW / TIME_OFFSET
│   └── drawing.py               # draw_gradient_bar() — shared utility
└── tests/
    ├── test_screen1_preview.py  # Render screen1 on hardware
    ├── test_screen2_preview.py  # Render screen2 on hardware (live cache data)
    ├── test_screen2_screenshots.py # Screen 2 PNG tests: 9 cases with mocked data (no hardware)
    ├── test_dates.py            # 13 edge-case dates → PNG files in tests/output/
    ├── test_midnight.py         # Live scheduler test, time offset to 23:57
    ├── test_clock.py            # Clock component on hardware
    ├── test_calendar.py         # Calendar component on hardware
    ├── test_year_progress.py    # Year progress on hardware
    ├── test_art_panel.py        # Art panel on hardware
    ├── test_starfield.py        # Starfield on hardware
    ├── test_screen3.py          # Single art display on hardware
    ├── test_screen3_slideshow.py# Slideshow loop on hardware
    ├── test_buttons.py          # GPIO button smoke test (prints on press)
    ├── test_screen3_preview.py  # Screen 3 PNG tests: render, empty fallback, no-repeat
    ├── test_anilist.py          # Smoke test for AniList API (all methods)
    └── test_mangadex.py         # Smoke test for MangaDex API
```

## Screens

| # | Content | Status |
|---|---------|--------|
| 1 | Clock · calendar · year progress · pixel art | Done |
| 2 | AniList upcoming releases · episodes · queue + MangaDex manga · stats footer | Done |
| 3 | Full-screen anime art slideshow (local images) | Done |

Screens are switched via two buttons (next / prev, infinite loop).

### Screen 2 — Column Routing Rules

| Column | Shows |
|--------|-------|
| Upcoming Releases | Planning anime where **ep 1 has not yet aired** (`nextAiringEpisode.episode == 1`) |
| Upcoming Episodes | Currently watching anime still airing + planning anime where **ep 1 has already aired** (`episode > 1`) |
| In Queue | Current/planning anime with **no** `nextAiringEpisode` (fully aired, not finished); max 2 cards |
| Manga Updates | MangaDex reading list with unread chapters; max 2 cards |

## Update Strategy

**Screen 1 (Clock)**
- **Every minute** — partial refresh of clock region only (~0.3s)
- **Every 5 minutes** — full refresh to clear ghosting (~3–5s)
- **At midnight** — forced full refresh so calendar and year progress update immediately
- **On startup** — full refresh

**Screen 2 (AniList / MangaDex)**
- **On switch** — API cache invalidated, full refresh with fresh data
- **Any timer < 24h** — partial refresh of Col1 + Col2 every minute; full refresh every 5 partials (anti-ghosting)
- **All timers ≥ 1 day** — full refresh every hour + cache invalidation
- **Timer hits 0** — cache invalidated, full refresh immediately so next episode data loads

**Screen 3 (Art slideshow)**
- **Auto-slideshow** — new random art every `SLIDESHOW_INTERVAL` seconds (set in `config.py`)
- **On manual switch** — immediate new random art regardless of interval
- Never shows the same art twice in a row

## API Credentials (AniList)

### First-time setup

1. Go to [anilist.co/settings/developer](https://anilist.co/settings/developer) → **Create new client**
   - Name: `E-Ink Dashboard`
   - Redirect URL: `http://localhost:3000`
   - Save → copy **Client ID** and **Client Secret**

2. Open in browser (replace `YOUR_CLIENT_ID`):
   ```
   https://anilist.co/api/v2/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:3000&response_type=code
   ```
   Authorize → you'll be redirected to `http://localhost:3000?code=XXXXX` → copy the `code`

3. Exchange code for access token:
   ```bash
   curl -X POST https://anilist.co/api/v2/oauth/token \
     -H 'Content-Type: application/json' \
     -d '{
       "grant_type": "authorization_code",
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "redirect_uri": "http://localhost:3000",
       "code": "YOUR_CODE"
     }'
   ```
   Copy `access_token` from response.

4. Copy `.env.example` → `.env` and fill in all three values:
   ```bash
   cp .env.example .env
   ```

> **Token expiry:** AniList tokens are valid for **1 year** (365 days). AniList does not support refresh tokens — repeat steps 2–4 annually.

### API usage policy

AniList is a free, open-source service. To avoid abuse/blocking:
- All API responses are cached in `cache/anilist.db` (SQLite)
- Media list + airing schedule: TTL 1 hour
- User statistics: TTL 24 hours
- Screen 2 reads from cache on every display refresh — **no API call per screen update**

## API Credentials (MangaDex)

### First-time setup

1. Create a free account at [mangadex.org](https://mangadex.org)

2. Go to [mangadex.org/settings](https://mangadex.org/settings) → **API Clients** → **Create**
   - Name: `E-Ink Dashboard`
   - Description: any text
   - Client type: **Personal** (only option for personal use)
   - Save → you'll get a **Client ID** and **Client Secret**

3. Add to `.env`:
   ```
   MANGADEX_USERNAME=your_username
   MANGADEX_PASSWORD=your_password
   MANGADEX_CLIENT_ID=your_client_id
   MANGADEX_CLIENT_SECRET=your_client_secret
   ```

4. Mark manga you're reading as **Reading** in your MangaDex library, and mark chapters read so the progress tracking works.

> **Auth:** MangaDex uses OAuth2 password flow. Access tokens (~15 min lifetime) are refreshed automatically using the stored refresh token. No manual renewal needed.

### API usage policy

- All responses cached in `cache/mangadex.db` (SQLite), TTL 1 hour
- Manga reading list: fetches status → batch titles → per-manga chapter feed + read markers
- Screen 2 reads from cache — **no API call per screen update**

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
