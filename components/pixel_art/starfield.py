"""
Starfield pixel art — static frozen frame generator.

Renders a black sky with twinkling stars (fixed positions, varied sizes),
a crescent moon, and a shooting star mid-flight.
"""
import math
import random
from PIL import Image, ImageDraw

SHOOT_SPEED = 11
SHOOT_TAIL  = 6
NUM_STARS   = 47
NUM_GIANTS  = 8     # larger stars with spike arms


def render(width: int, height: int) -> Image.Image:
    """Return a single static starfield image of the given size."""
    img  = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(img)

    _draw_moon(draw, width, height)
    _draw_stars(draw, width, height)
    _draw_shooting_star(draw, width, height)

    return img


# ---------------------------------------------------------------------------
# Moon

def _draw_moon(draw: ImageDraw.ImageDraw, width: int, height: int):
    mr = random.randint(16, 22)
    mx = random.randint(mr + 10, width  - mr - 10)
    my = random.randint(mr + 8,  height // 2 - mr)

    draw.ellipse([mx-mr, my-mr, mx+mr, my+mr], fill=255)
    cr = int(mr * 0.9)
    ox = int(mr * 0.45)
    draw.ellipse([mx-cr+ox, my-cr-2, mx+cr+ox, my+cr-2], fill=0)


# ---------------------------------------------------------------------------
# Stars

def _draw_stars(draw: ImageDraw.ImageDraw, width: int, height: int):
    frame = 20   # fixed "time" snapshot for natural brightness distribution

    for _ in range(NUM_STARS):
        x    = random.randint(0, width  - 1)
        y    = random.randint(0, height - 1)
        size = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        t    = frame * random.uniform(0.06, 0.20) + random.uniform(0, 2 * math.pi)
        fill = max(0, min(255, int(145 + 110 * math.sin(t))))
        _draw_small_star(draw, x, y, size, fill, width, height)

    for _ in range(NUM_GIANTS):
        arm_max = random.randint(5, 8)
        x       = random.randint(arm_max + 2, width  - arm_max - 2)
        y       = random.randint(arm_max + 2, height - arm_max - 2)
        t       = frame * random.uniform(0.05, 0.13) + random.uniform(0, 2 * math.pi)
        factor  = (1 + math.sin(t)) / 2
        fill    = int(80 + 175 * factor)
        arm     = max(1, int(1 + (arm_max - 1) * factor))
        _draw_giant_star(draw, x, y, arm, fill, width, height)


def _draw_small_star(draw, x, y, size, fill, W, H):
    draw.point((x, y), fill=fill)
    if size >= 2:
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            px, py = x+dx, y+dy
            if 0 <= px < W and 0 <= py < H:
                draw.point((px, py), fill=fill)
    if size >= 3:
        dim = max(0, fill - 90)
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            px, py = x+dx, y+dy
            if 0 <= px < W and 0 <= py < H:
                draw.point((px, py), fill=dim)


def _draw_giant_star(draw, x, y, arm, fill, W, H):
    draw.point((x, y), fill=255)
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        for step in range(1, arm + 1):
            fade = max(0, fill - int((step / arm) * 160))
            px, py = x + dx*step, y + dy*step
            if 0 <= px < W and 0 <= py < H:
                draw.point((px, py), fill=fade)
    diag = max(1, arm // 2)
    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
        for step in range(1, diag + 1):
            fade = max(0, fill - int((step / diag) * 200))
            px, py = x + dx*step, y + dy*step
            if 0 <= px < W and 0 <= py < H:
                draw.point((px, py), fill=fade)


# ---------------------------------------------------------------------------
# Shooting star

def _draw_shooting_star(draw: ImageDraw.ImageDraw, width: int, height: int):
    angle = math.radians(random.uniform(25, 50))
    vx = SHOOT_SPEED * math.cos(angle) * random.choice([-1, 1])
    vy = SHOOT_SPEED * math.sin(angle)
    cx = random.uniform(width  * 0.25, width  * 0.70)
    cy = random.uniform(height * 0.15, height * 0.55)

    # Build tail stretching backward from head
    tail = [(cx - vx * (SHOOT_TAIL - i) / SHOOT_TAIL,
             cy - vy * (SHOOT_TAIL - i) / SHOOT_TAIL)
            for i in range(SHOOT_TAIL)]

    n = len(tail)
    for i in range(n - 1):
        t_frac   = (i + 1) / n
        brightness = int(255 * t_frac ** 0.6)
        width_px   = 3 if t_frac > 0.80 else (2 if t_frac > 0.45 else 1)
        x1, y1 = int(tail[i][0]),     int(tail[i][1])
        x2, y2 = int(tail[i + 1][0]), int(tail[i + 1][1])
        draw.line([(x1, y1), (x2, y2)], fill=brightness, width=width_px)

    hx, hy = int(cx), int(cy)
    draw.ellipse([hx-2, hy-2, hx+2, hy+2], fill=255)
