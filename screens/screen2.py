from datetime import datetime
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from screens.base_screen import BaseScreen
from components.art_panel import draw_notif_bar
from components.section_header import draw as draw_header, SECTION_H
from components.date_separator import draw as draw_date_sep
from components.release_card import draw as draw_release_card
from components.upcoming_card import draw as draw_upcoming_card
from components.queue_card import draw as draw_queue_card
from components.manga_card import draw as draw_manga_card
from components.stats_footer import draw as draw_stats_footer, HEIGHT as FOOTER_H
import config
import api.screen2_data as data_layer

PAD = 14
GAP = 8
COL_W = (800 - 2 * PAD - 2 * GAP) // 3   # 252px
COL1_X = PAD
COL2_X = PAD + COL_W + GAP
COL3_X = PAD + 2 * COL_W + 2 * GAP

GAP_AFTER_HEADER = 6
GAP_AFTER_DATE   = 4
GAP_AFTER_CARD   = 6

# Height estimates for overflow checks (col2/col3 cards have progress bar)
_CARD_H_EST    = 62   # PAD*2 + 2 lines + bar + bar_gap
_DATE_H_EST    = 20   # date_separator.HEIGHT=18 + small buffer
_MORE_H_EST    = 20   # "+N more" text
_SECTION_H_EST = SECTION_H + GAP_AFTER_HEADER

CARD_AREA_BOTTOM = 480 - PAD - FOOTER_H - GAP   # ≈ 434


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def _fits(y, card_h=None, needs_date_sep=False, needs_section=False):
    """Return True if there is room for a card (+ optional separator/header)."""
    if card_h is None:
        card_h = _CARD_H_EST
    extra = (_DATE_H_EST if needs_date_sep else 0) + (_SECTION_H_EST if needs_section else 0)
    return y + extra + card_h + _MORE_H_EST <= CARD_AREA_BOTTOM


def _draw_more(draw_ctx, x, y, remaining):
    draw_ctx.text(
        (x + COL_W // 2, y + 2),
        f'+{remaining} more',
        font=_font(config.FONT_PATH, 13), fill=0, anchor='mt',
    )


def _draw_empty(draw_ctx, x, y, message='No updates'):
    font = _font(config.FONT_BOLD_PATH, 15)

    # Word-wrap into lines that fit COL_W
    words = message.split()
    lines, current = [], ''
    for word in words:
        candidate = (current + ' ' + word).strip()
        if draw_ctx.textlength(candidate, font=font) <= COL_W - 8:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_h = draw_ctx.textbbox((0, 0), 'A', font=font)[3] + 4
    cx = x + COL_W // 2
    ty = y + 2
    for line in lines:
        draw_ctx.text((cx, ty), line, font=font, fill=0, anchor='mt')
        ty += line_h
    return ty  # bottom of last line


class Screen2(BaseScreen):
    def render(self) -> Image.Image:
        image    = Image.new('L', (self.width, self.height), 255)
        draw_ctx = ImageDraw.Draw(image)

        releases, err_rel = data_layer.get_upcoming_releases()
        episodes, err_ep  = data_layer.get_upcoming_episodes()
        queue,    err_q   = data_layer.get_queue()
        manga,    err_mg  = data_layer.get_manga_updates()
        stats,    _       = data_layer.get_stats()

        # ── Col 1 — Upcoming Releases ──────────────────────────────────────
        y1 = draw_notif_bar(image, x=COL1_X, y=PAD, w=COL_W) + GAP_AFTER_HEADER
        y1 = draw_header(image, COL1_X, y1, COL_W, 'Upcoming Releases') + GAP_AFTER_HEADER

        if err_rel and not releases:
            _draw_empty(draw_ctx, COL1_X, y1, f'Error: {err_rel}')
        elif not releases:
            _draw_empty(draw_ctx, COL1_X, y1)
        else:
            MAX_RELEASES = 4
            last_date = None
            for item in releases[:MAX_RELEASES]:
                need_sep = item['airing_date'] != last_date
                if need_sep:
                    y1 = draw_date_sep(image, COL1_X, y1, COL_W, item['airing_date']) + GAP_AFTER_DATE
                    last_date = item['airing_date']
                y1 = draw_release_card(
                    image, COL1_X, y1, COL_W,
                    item['title'], item['eps_count'],
                    item['starts_in'], item['final_ep'],
                ) + GAP_AFTER_CARD
            remaining = max(0, len(releases) - MAX_RELEASES)
            if remaining > 0:
                _draw_more(draw_ctx, COL1_X, y1, remaining)

        # ── Col 2 — Upcoming Episodes ──────────────────────────────────────
        y2 = draw_header(image, COL2_X, PAD, COL_W, 'Upcoming Episodes') + GAP_AFTER_HEADER

        if err_ep and not episodes:
            _draw_empty(draw_ctx, COL2_X, y2, f'Error: {err_ep}')
        elif not episodes:
            _draw_empty(draw_ctx, COL2_X, y2)
        else:
            last_date = None
            shown = 0
            for item in episodes:
                need_sep = item['airing_date'] != last_date
                if not _fits(y2, needs_date_sep=need_sep):
                    break
                if need_sep:
                    y2 = draw_date_sep(image, COL2_X, y2, COL_W, item['airing_date']) + GAP_AFTER_DATE
                    last_date = item['airing_date']
                y2 = draw_upcoming_card(
                    image, COL2_X, y2, COL_W,
                    item['title'], item['ep_label'],
                    item['time_until'], item['final_date'],
                    item['watched'], item['total'], item['behind'],
                    highlight=item['highlight'],
                ) + GAP_AFTER_CARD
                shown += 1
            remaining = len(episodes) - shown
            if remaining > 0:
                _draw_more(draw_ctx, COL2_X, y2, remaining)

        # ── Col 3 — In Queue + Manga Updates ──────────────────────────────
        y3 = draw_header(image, COL3_X, PAD, COL_W, 'In Queue') + GAP_AFTER_HEADER

        if err_q and not queue:
            y3 = _draw_empty(draw_ctx, COL3_X, y3, f'Error: {err_q}') + GAP_AFTER_CARD
        elif not queue:
            y3 = _draw_empty(draw_ctx, COL3_X, y3) + GAP_AFTER_CARD
        else:
            shown = 0
            for item in queue:
                if not _fits(y3):
                    break
                y3 = draw_queue_card(
                    image, COL3_X, y3, COL_W,
                    item['title'], item['watched'],
                    item['total'], item['last_updated'],
                ) + GAP_AFTER_CARD
                shown += 1
            remaining = len(queue) - shown
            if remaining > 0:
                _draw_more(draw_ctx, COL3_X, y3, remaining)
                y3 += _MORE_H_EST

        # Manga section — only if there's enough space for header + 1 card
        if _fits(y3, needs_section=True):
            y3 += GAP
            y3 = draw_header(image, COL3_X, y3, COL_W, 'Manga Updates') + GAP_AFTER_HEADER

            if err_mg and not manga:
                _draw_empty(draw_ctx, COL3_X, y3, f'Error: {err_mg}')
            elif not manga:
                _draw_empty(draw_ctx, COL3_X, y3)
            else:
                shown = 0
                for item in manga:
                    if not _fits(y3):
                        break
                    y3 = draw_manga_card(
                        image, COL3_X, y3, COL_W,
                        item['title'], item['current_ch'],
                        item['total_ch'], item['status'],
                    ) + GAP_AFTER_CARD
                    shown += 1
                remaining = len(manga) - shown
                if remaining > 0:
                    _draw_more(draw_ctx, COL3_X, y3, remaining)

        # ── Footer ────────────────────────────────────────────────────────
        year = datetime.now().year
        draw_stats_footer(image, stats=[
            ('Watching: ',           str(stats['watching'])),
            ('Planning: ',           str(stats['planning'])),
            (f'Completed {year}: ',  str(stats['completed_year'])),
            (f'Hours {year}: ',      str(stats['total_hours'])),
            ('Reading manga: ',       str(stats['manga_reading'])),
        ])

        return image
