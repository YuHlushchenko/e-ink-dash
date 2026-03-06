from datetime import date
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from screens.base_screen import BaseScreen
from components.art_panel import draw_notif_bar
from components.section_header import draw as draw_header, SECTION_H
import config
from components.date_separator import draw as draw_date_sep
from components.release_card import draw as draw_release_card
from components.stats_footer import draw as draw_stats_footer

PAD = 14
GAP = 8
COL_W = (800 - 2 * PAD - 2 * GAP) // 3   # 252px
COL1_X = PAD
COL2_X = PAD + COL_W + GAP
COL3_X = PAD + 2 * COL_W + 2 * GAP
NOTIF_H = 28
NOTIF_GAP = 6


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


class Screen2(BaseScreen):
    def render(self) -> Image.Image:
        image = Image.new('L', (self.width, self.height), 255)

        GAP_AFTER_HEADER = 6
        GAP_AFTER_DATE   = 4
        GAP_AFTER_CARD   = 6

        # --- Col 1 ---
        y1 = draw_notif_bar(image, x=COL1_X, y=PAD, w=COL_W) + GAP_AFTER_HEADER
        y1 = draw_header(image, COL1_X, y1, COL_W, 'Upcoming Releases') + GAP_AFTER_HEADER

        y1 = draw_date_sep(image, COL1_X, y1, COL_W, date(2026, 4, 1)) + GAP_AFTER_DATE
        y1 = draw_release_card(image, COL1_X, y1, COL_W,
                               'Classroom of the Elite 2nd Year', 12, '11d 3h', 'Jun 28') + GAP_AFTER_CARD

        y1 = draw_date_sep(image, COL1_X, y1, COL_W, date(2026, 4, 8)) + GAP_AFTER_DATE
        y1 = draw_release_card(image, COL1_X, y1, COL_W,
                               'Dungeon Meshi Season 2', 24, '18d 5h', 'Sep 12') + GAP_AFTER_CARD

        y1 = draw_date_sep(image, COL1_X, y1, COL_W, date(2026, 5, 3)) + GAP_AFTER_DATE
        y1 = draw_release_card(image, COL1_X, y1, COL_W,
                               'Vinland Saga Season 3', 13, '43d 1h', 'Aug 2') + GAP_AFTER_CARD

        y1 = draw_date_sep(image, COL1_X, y1, COL_W, date(2026, 5, 15)) + GAP_AFTER_DATE
        y1 = draw_release_card(image, COL1_X, y1, COL_W,
                               'Attack on Titan Final Season', 8, '55d 2h', 'Oct 5') + GAP_AFTER_CARD

        draw = ImageDraw.Draw(image)
        draw.text((COL1_X + COL_W // 2, y1 + 2), '+3 more',
                  font=_font(config.FONT_PATH, 13), fill=0, anchor='mt')

        # --- Col 2 ---
        y2 = PAD
        y2 = draw_header(image, COL2_X, y2, COL_W, 'Upcoming Episodes') + GAP_AFTER_HEADER

        # --- Col 3 ---
        y3 = PAD
        y3 = draw_header(image, COL3_X, y3, COL_W, 'In Queue') + GAP_AFTER_HEADER
        # (In Queue items will go here)
        y3 = draw_header(image, COL3_X, y3, COL_W, 'Manga Updates') + GAP_AFTER_HEADER

        # --- Footer ---
        draw_stats_footer(image, stats=[
            ('Watching: ',        '12'),
            ('Planning: ',        '3'),
            ('Completed 2026: ',  '8'),
            ('Total hours: ',     '342'),
            ('Manga chapters: ',  '15'),
        ])

        return image
