# e-ink-dash

Personal dashboard for a 7.5" e-ink display, running on Raspberry Pi Zero 2W.

## Hardware

- Raspberry Pi Zero 2W
- Waveshare 7.5" e-Paper HAT (800x480, B&W), Driver HAT Rev2.3
- Driver HAT switches: Display Config B, Interface Config 0 (4-line SPI)

## Setup

**OS:** Raspberry Pi OS Lite 32-bit (Trixie)
**Hostname:** `your-pi-hostname`, **User:** `your-user`
**SPI:** enabled (`/dev/spidev0.0`, `/dev/spidev0.1`)

**Dependencies:**

```bash
pip3 install -e /home/<user>/e-Paper --break-system-packages
pip3 install -r requirements.txt --break-system-packages
```

**Font:** `fonts-liberation` — `LiberationMono-Regular.ttf`

## Stack

- Python
- Pillow — rendering, Floyd-Steinberg dithering
- Waveshare e-Paper library (`waveshare_epd.epd7in5_V2`)
- gpiozero — buttons

## Project Structure

```
e-ink-dash/
├── main.py              # entry point, screen switching
├── config.py            # display size, font path, GPIO pins
├── renderer/
│   └── base.py          # Renderer: init, display, clear, sleep
├── screens/
│   ├── base_screen.py   # BaseScreen base class
│   ├── screen1.py       # Clock, calendar, year progress
│   ├── screen2.py       # AniList + MangaDex
│   └── screen3.py       # Anime art slideshow (local, random, 15 min)
├── api/                 # API integrations
├── assets/
│   └── arts/            # Local anime art images (.jpg, .png)
├── cache/               # SQLite cache (gitignored)
└── tests/
    ├── hello.py                    # Display test: centered text + dithered gradient bar
    ├── test_screen3.py             # Single art display test
    └── test_screen3_slideshow.py   # Slideshow loop (30s interval for testing)
```

## Dev Workflow

Code is edited locally via SSHFS mount, files live on Pi. Run scripts via SSH:

```bash
ssh <user>@<hostname> "python3 /home/<user>/e-ink-dash/<script>.py"
```

## Screens

| # | Content |
|---|---------|
| 1 | Clock, calendar, year progress |
| 2 | AniList upcoming releases, MangaDex updates |
| 3 | Full-screen anime art slideshow — images from `assets/arts/`, rotates every 15 min |

Screens are switched via buttons (infinite loop: last → first → last).
