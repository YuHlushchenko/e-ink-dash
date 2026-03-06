from datetime import date
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from screens.base_screen import BaseScreen
from components.art_panel import draw_notif_bar
from components.section_header import draw as draw_header, SECTION_H
import config
from components.date_separator import draw as draw_date_sep
from components.release_card import draw as draw_release_card
from components.upcoming_card import draw as draw_upcoming_card
from components.queue_card import draw as draw_queue_card
from components.manga_card import draw as draw_manga_card
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

        y2 = draw_date_sep(image, COL2_X, y2, COL_W, date(2026, 3, 25)) + GAP_AFTER_DATE
        # Two episodes on the same date — no separator between them
        y2 = draw_upcoming_card(image, COL2_X, y2, COL_W,
             "Hell's Paradise Season 2", '9 ep', '4d 3h', 'Apr 28',
             watched=6, total=12, behind=2) + GAP_AFTER_CARD
        y2 = draw_upcoming_card(image, COL2_X, y2, COL_W,
             'Witch Hat Atelier', 'FINAL', '4d 3h', 'Apr 28',
             watched=9, total=12, behind=2, highlight=True) + GAP_AFTER_CARD

        y2 = draw_date_sep(image, COL2_X, y2, COL_W, date(2026, 4, 1)) + GAP_AFTER_DATE
        y2 = draw_upcoming_card(image, COL2_X, y2, COL_W,
             'Frieren: Beyond Journey\'s End', '28 ep', '12d 1h', '∞',
             watched=10, total=28, behind=3) + GAP_AFTER_CARD

        draw = ImageDraw.Draw(image)
        draw.text((COL2_X + COL_W // 2, y2 + 2), '+3 more',
                  font=_font(config.FONT_PATH, 13), fill=0, anchor='mt')

        # --- Col 3 ---
        y3 = PAD
        y3 = draw_header(image, COL3_X, y3, COL_W, 'In Queue') + GAP_AFTER_HEADER
        y3 = draw_queue_card(image, COL3_X, y3, COL_W,
             "Hell's Paradise Season 2", watched=0, total=12, last_updated='Mar 15, 2025') + GAP_AFTER_CARD
        y3 = draw_queue_card(image, COL3_X, y3, COL_W,
             "Hell's Paradise Season 2", watched=10, total=12, last_updated='Mar 15, 2025') + GAP_AFTER_CARD

        draw = ImageDraw.Draw(image)
        draw.text((COL3_X + COL_W // 2, y3 + 2), '+3 more',
                  font=_font(config.FONT_PATH, 13), fill=0, anchor='mt')
        y3 += 20

        y3 = draw_header(image, COL3_X, y3, COL_W, 'Manga Updates') + GAP_AFTER_HEADER
        y3 = draw_manga_card(image, COL3_X, y3, COL_W,
             'Dungeon Meshi', current_ch=45, total_ch=97,
             status='New chapter available') + GAP_AFTER_CARD
        y3 = draw_manga_card(image, COL3_X, y3, COL_W,
             'Berserk', current_ch=364, total_ch=374,
             status='2 new chapters') + GAP_AFTER_CARD

        draw = ImageDraw.Draw(image)
        draw.text((COL3_X + COL_W // 2, y3 + 2), '+3 more',
                  font=_font(config.FONT_PATH, 13), fill=0, anchor='mt')

        # --- Footer ---
        draw_stats_footer(image, stats=[
            ('Watching: ',        '12'),
            ('Planning: ',        '3'),
            ('Completed 2026: ',  '8'),
            ('Total hours: ',     '342'),
            ('Manga chapters: ',  '15'),
        ])

        return image
