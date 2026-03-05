from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf', 48)

epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()

image = Image.new('L', (epd.width, epd.height), 255)
draw = ImageDraw.Draw(image)

text = 'Hello World!'
bbox = draw.textbbox((0, 0), text, font=font)
x = (epd.width - (bbox[2] - bbox[0])) // 2
y = (epd.height - (bbox[3] - bbox[1])) // 2
draw.text((x, y), text, font=font, fill=0)

# Gradient bar under text
BAR_H = 6
BAR_R = 4
bar_y = y + (bbox[3] - bbox[1]) + 16

BAR_W = int(epd.width * 0.8)
bar_x = (epd.width - BAR_W) // 2

gradient = Image.new('L', (BAR_W, BAR_H))
gradient_draw = ImageDraw.Draw(gradient)
for i in range(BAR_W):
    value = int(i * 255 / (BAR_W - 1))
    gradient_draw.line([(i, 0), (i, BAR_H - 1)], fill=value)

mask = Image.new('L', (BAR_W, BAR_H), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, BAR_W - 1, BAR_H - 1], radius=BAR_R, fill=255)

image.paste(gradient, (bar_x, bar_y), mask)

epd.display(epd.getbuffer(image.convert('1', dither=Image.FLOYDSTEINBERG)))
epd.sleep()
