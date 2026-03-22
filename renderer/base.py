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
        """Fast full-screen refresh via display_Partial — saturated blacks, ~2-3s.
        No Clear(): init_part() hardware reset leaves frame buffer undefined, so
        display_Partial treats all pixels as changed and drives them all.
        Use for regular anti-ghosting cycles (every 5 min). Not a true full waveform
        cycle — call display_maintenance() at least once daily to prevent burn-in.
        """
        self.epd.init_part()
        raw = image.convert('1', dither=Image.FLOYDSTEINBERG).tobytes('raw')
        buf = list(bytes(b ^ 0xFF for b in raw))
        self.epd.display_Partial(buf, 0, 0, self.epd.width, self.epd.height)

    def display_maintenance(self, image: Image.Image):
        """Full-health refresh — required every 5 partial refreshes to prevent burn-in.
        Pass 1: true epd.display() cycles all pixels through complete waveform,
                physically resetting microcapsule voltages (DC bias reset).
        Pass 2: display_Partial for saturated blacks (no second Clear() needed —
                frame buffer after display() is valid, init_part() reset drives all pixels).
        Takes ~5-7s.
        """
        buf_full = self.epd.getbuffer(image.convert('1', dither=Image.FLOYDSTEINBERG))
        self.epd.init()
        self.epd.display(buf_full)
        self.epd.init_part()
        self.epd.Clear()
        raw = image.convert('1', dither=Image.FLOYDSTEINBERG).tobytes('raw')
        buf_partial = list(bytes(b ^ 0xFF for b in raw))
        self.epd.display_Partial(buf_partial, 0, 0, self.epd.width, self.epd.height)

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
