from PIL import Image, ImageDraw


def draw_gradient_bar(image, x, y, w, h, radius, reverse=False):
    """Horizontal gradient bar: black→white (or white→black if reverse=True)."""
    if w <= 0:
        return
    gradient = Image.new('L', (w, h))
    g_draw = ImageDraw.Draw(gradient)
    for i in range(w):
        value = int(i * 255 / max(w - 1, 1))
        if reverse:
            value = 255 - value
        g_draw.line([(i, 0), (i, h - 1)], fill=value)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    image.paste(gradient, (x, y), mask)
