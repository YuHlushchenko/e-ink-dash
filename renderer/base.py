from PIL import Image
from waveshare_epd import epd7in5_V2


class Renderer:
    def __init__(self):
        self.epd    = epd7in5_V2.EPD()
        self.width  = self.epd.width
        self.height = self.epd.height

    def init(self):
        """Full-refresh mode."""
        self.epd.init()

    def init_partial(self):
        """Partial-refresh mode. Call before display_partial()."""
        self.epd.init_part()

    def display(self, image: Image.Image):
        """Full screen refresh (slow, no ghosting)."""
        buf = self.epd.getbuffer(image.convert('1', dither=Image.FLOYDSTEINBERG))
        self.epd.display(buf)

    def display_partial(self, image: Image.Image, x0: int, y0: int, x1: int, y1: int):
        """
        Partial refresh — only the [x0,y0]→[x1,y1] region updates on screen.
        x0 and x1 must be multiples of 8 (hardware byte-alignment).
        display_Partial expects a cropped region buffer and inverts bytes internally.
        """
        cropped = image.crop((x0, y0, x1, y1))
        raw = cropped.convert('1', dither=Image.FLOYDSTEINBERG).tobytes('raw')
        buf = list(bytes(b ^ 0xFF for b in raw))   # match getbuffer polarity (partial LUT is inverted)
        self.epd.display_Partial(buf, x0, y0, x1, y1)

    def clear(self):
        self.epd.Clear()

    def sleep(self):
        self.epd.sleep()
