from PIL import Image
from waveshare_epd import epd7in5_V2


class Renderer:
    def __init__(self):
        self.epd = epd7in5_V2.EPD()
        self.width = self.epd.width
        self.height = self.epd.height

    def init(self):
        self.epd.init()

    def display(self, image: Image.Image):
        image_1bit = image.convert('1', dither=Image.FLOYDSTEINBERG)
        self.epd.display(self.epd.getbuffer(image_1bit))

    def clear(self):
        self.epd.Clear()

    def sleep(self):
        self.epd.sleep()
