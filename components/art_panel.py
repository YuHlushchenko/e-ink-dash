import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

import config

ARTS_DIR = Path(__file__).parent.parent / 'assets' / 'arts'
ICONS_DIR = Path(__file__).parent.parent / 'assets' / 'icons'
SUPPORTED = ('*.jpg', '*.jpeg', '*.png')

NOTIF_H = 28   # height of notification bar
NOTIF_R = 4    # corner radius of notification bar
NOTIF_GAP = 8  # gap between notif bar and art image


def draw(image, x=14, y=14, w=202, art_path=None):
    import components.year_progress as _yp
    # Art fills from below notif bar down to 10px above year_progress
    art_y = y + NOTIF_H + NOTIF_GAP
    art_bottom = 480 - 14 - _yp.HEIGHT - 10
    art_h = art_bottom - art_y

    draw_ctx = ImageDraw.Draw(image)

    # 1. Notification bar: white bg, black border, small radius
    draw_ctx.rounded_rectangle(
        [x, y, x + w - 1, y + NOTIF_H - 1],
        radius=NOTIF_R, fill=255, outline=0,
    )

    # 2. Icons inside notification bar (black on white)
    _draw_notif_icons(image, x, y, w)

    # 3. Art image below notification bar
    _draw_art(image, x, art_y, w, art_h, art_path)


def _draw_notif_icons(image, panel_x, panel_y, panel_w):
    ICON_SIZE = 20
    icon_y = panel_y + (NOTIF_H - ICON_SIZE) // 2  # vertically centered in bar

    icons = [
        ('bell.svg',  panel_x + 5),
        ('stars.svg', panel_x + 23),
    ]

    for filename, icon_x in icons:
        _paste_svg_icon(image, ICONS_DIR / filename, icon_x, icon_y, ICON_SIZE)


def _paste_svg_icon(image, svg_path, x, y, size):
    try:
        import cairosvg
        svg_bytes = Path(svg_path).read_bytes()
        png_bytes = cairosvg.svg2png(
            bytestring=svg_bytes,
            output_width=size, output_height=size,
            background_color='white',
        )
        icon = Image.open(io.BytesIO(png_bytes)).convert('L')
        image.paste(icon, (x, y))
    except Exception as e:
        print(f'[art_panel] icon error ({svg_path.name}): {e}')



def _draw_art(image, x, y, w, h, art_path):
    if art_path is None:
        arts = [f for pattern in SUPPORTED for f in ARTS_DIR.glob(pattern)]
        if not arts:
            return
        art_path = random.choice(arts)

    try:
        art = Image.open(art_path).convert('L')
        art = ImageOps.fit(art, (w, h), method=Image.LANCZOS)
        image.paste(art, (x, y))
    except Exception:
        pass
