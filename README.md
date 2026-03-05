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
pip3 install pillow
```

**Font:** `fonts-liberation` — `LiberationMono-Regular.ttf`

## Stack

- Python
- Pillow — rendering, Floyd-Steinberg dithering for gradients
- Waveshare e-Paper library (`waveshare_epd.epd7in5_V2`)

## Dev Workflow

Code is edited locally via SSHFS mount, files live on Pi. Run scripts via SSH:

```bash
ssh <user>@<hostname> "python3 /home/<user>/e-ink-dash/<script>.py"
```

## Files

- `hello.py` — display test: centered text + dithered gradient bar
