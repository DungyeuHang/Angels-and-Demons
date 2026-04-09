import os
import sys

import pygame

from mechanics.effects import get_builtin_effects
from mechanics.effects import get_custom_only_effects
from mechanics.effects import get_effect_help
from models.settings import load_settings
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.theme import PALETTE
from ui.theme import clamp_text
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_hint_bar
from ui.theme import draw_panel
from ui.theme import draw_scrollbar
from ui.theme import draw_title
from ui.theme import get_ui_font
from ui.theme import get_reveal_progress
from ui.theme import get_reveal_rect
from ui.theme import wrap_text


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


ICON_KEYS = {
    "angel": "effect_angel",
    "devil": "effect_devil",
    "gun": "effect_gun",
    "lucky": "effect_lucky",
    "lottery": "effect_lottery",
    "rps": "effect_rps",
    "double": "effect_double",
    "half": "effect_half",
}

FILTER_OPTIONS = [
    ("all", "Tat ca"),
    ("builtin", "Mac dinh"),
    ("custom", "Custom"),
]


def build_effect_sections(filter_mode="all"):
    builtin_effects = get_builtin_effects()
    custom_effects = get_custom_only_effects()
    if filter_mode == "builtin":
        return [("8 hieu ung co san", "Che do thuong luon dung 8 hieu ung nay.", builtin_effects)]
    if filter_mode == "custom":
        return [("Chi co trong custom", "Nhom chien thuat dac biet, chi mo trong custom va challenge mo rong.", custom_effects)]
    return [
        ("8 hieu ung co san", "Che do thuong luon dung 8 hieu ung nay.", builtin_effects),
        ("Chi co trong custom", "Nhom chien thuat dac biet, chi mo trong custom va challenge mo rong.", custom_effects),
    ]


def draw_filter_chip(surface, font, rect, label, active=False, hovered=False):
    fill_color = (247, 223, 184) if active else (247, 239, 223) if hovered else (241, 234, 221)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=16, shadow=False)
    text_surface = font.render(label, True, PALETTE["text"])
    surface.blit(text_surface, (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2))

def draw_effect_row(surface, fonts, rect, effect, hovered=False):
    title_font = fonts["font"]
    body_font = fonts["small"]
    tiny_font = fonts["tiny"]
    icon_key = ICON_KEYS.get(str(effect.get("id", "")))
    icon_surface = get_surface(icon_key, (34, 34)) if icon_key else None

    fill_color = (252, 244, 232) if hovered else (248, 241, 230)
    border_color = PALETTE["gold_dark"] if hovered else PALETTE["panel_dark"]
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=18, shadow=False)
    if icon_surface is not None:
        surface.blit(icon_surface, (rect.x + 16, rect.y + 12))
    else:
        badge_rect = pygame.Rect(rect.x + 16, rect.y + 12, 34, 34)
        draw_panel(surface, badge_rect, fill_color=(238, 229, 214), border_color=PALETTE["panel_dark"], radius=17, shadow=False)
        fallback = tiny_font.render(str(effect.get("label", "?"))[:1], True, PALETTE["text"])
        surface.blit(fallback, (badge_rect.centerx - fallback.get_width() // 2, badge_rect.centery - fallback.get_height() // 2))

    title_text = clamp_text(title_font, str(effect.get("label", effect.get("id", "Effect"))), rect.width - 120)
    title = title_font.render(title_text, True, PALETTE["text"])
    surface.blit(title, (rect.x + 62, rect.y + 10))

    subtitle = "Custom only" if effect.get("custom_only") else "Mac dinh"
    subtitle_surface = tiny_font.render(subtitle, True, PALETTE["muted"])
    surface.blit(subtitle_surface, (rect.x + 62, rect.y + 34))

    help_lines = wrap_text(body_font, get_effect_help(effect.get("id")), rect.width - 86, max_lines=3)
    line_y = rect.y + 56
    for line in help_lines:
        line_surface = body_font.render(line, True, PALETTE["text"])
        surface.blit(line_surface, (rect.x + 16, line_y))
        line_y += 18


def show_effect_book_screen(screen):
    apply_window_icon()
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    fonts = {
        "title": pygame.font.Font(font_path, 30),
        "font": get_ui_font(18, bold=True),
        "small": get_ui_font(14),
        "tiny": get_ui_font(12),
    }
    clock = pygame.time.Clock()
    scroll_y = 0
    active_filter = "all"
    intro_tick = pygame.time.get_ticks()
    reduce_motion = load_settings().get("reduce_motion", False)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)
        panel_progress = get_reveal_progress(intro_tick, tick, duration=360, reduce_motion=reduce_motion)

        panel_rect = get_reveal_rect(pygame.Rect(42, 28, screen.get_width() - 84, screen.get_height() - 56), panel_progress, offset_y=22)
        draw_panel(screen, panel_rect, fill_color=(249, 242, 228), border_color=PALETTE["gold_dark"], radius=28)
        draw_title(screen, fonts["title"], "So tay hieu ung", (panel_rect.centerx, panel_rect.y + 42), PALETTE["text"])

        subtitle = fonts["small"].render("Nhan B hoac Esc de dong. Day la bang mo ta nhanh de tra effect trong luc choi.", True, PALETTE["muted"])
        screen.blit(subtitle, (panel_rect.centerx - subtitle.get_width() // 2, panel_rect.y + 74))

        builtin_count = len(get_builtin_effects())
        custom_count = len(get_custom_only_effects())
        filter_rects = []
        chip_y = panel_rect.y + 104
        chip_x = panel_rect.x + 36
        chip_widths = {"all": 110, "builtin": 136, "custom": 124}
        count_lookup = {"all": builtin_count + custom_count, "builtin": builtin_count, "custom": custom_count}
        for filter_index, (filter_key, label) in enumerate(FILTER_OPTIONS):
            rect = get_reveal_rect(
                pygame.Rect(chip_x, chip_y, chip_widths[filter_key], 30),
                get_reveal_progress(intro_tick, tick, duration=320, delay_ms=80 + filter_index * 36, reduce_motion=reduce_motion),
                offset_y=10,
            )
            draw_filter_chip(
                screen,
                fonts["tiny"],
                rect,
                f"{label} {count_lookup[filter_key]}",
                active=active_filter == filter_key,
                hovered=rect.collidepoint(mouse_pos),
            )
            filter_rects.append((filter_key, rect))
            chip_x = rect.right + 10

        content_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 24, panel_rect.y + 142, panel_rect.width - 48, panel_rect.height - 218),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=140, reduce_motion=reduce_motion),
            offset_y=14,
        )
        draw_panel(screen, content_rect, fill_color=(252, 246, 236), border_color=PALETTE["lilac"], radius=22, shadow=False)

        sections = build_effect_sections(active_filter)
        y = content_rect.y + 18 - scroll_y
        content_height = 0
        hovered_effect = None
        for title, helper, effects in sections:
            title_surface = fonts["font"].render(title, True, PALETTE["text"])
            helper_surface = fonts["small"].render(helper, True, PALETTE["muted"])
            screen.blit(title_surface, (content_rect.x + 18, y))
            screen.blit(helper_surface, (content_rect.x + 18, y + 24))
            y += 54
            content_height += 54

            for effect_index, effect in enumerate(effects):
                row_progress = get_reveal_progress(intro_tick, tick, duration=300, delay_ms=180 + min(effect_index, 5) * 28, reduce_motion=reduce_motion)
                row_rect = get_reveal_rect(pygame.Rect(content_rect.x + 14, y, content_rect.width - 28, 112), row_progress, offset_y=10)
                if row_rect.bottom >= content_rect.y + 8 and row_rect.top <= content_rect.bottom - 8:
                    is_hovered = row_rect.collidepoint(mouse_pos)
                    draw_effect_row(screen, fonts, row_rect, effect, hovered=is_hovered)
                    if is_hovered:
                        hovered_effect = effect
                y += 124
                content_height += 124
            y += 8
            content_height += 8

        scrollbar_rect = pygame.Rect(content_rect.right - 14, content_rect.y + 14, 10, content_rect.height - 28)
        draw_scrollbar(screen, scrollbar_rect, content_height, content_rect.height - 8, scroll_y, accent_color=PALETTE["lilac"])

        inspector_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 28, panel_rect.bottom - 106, panel_rect.width - 56, 42),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=260, reduce_motion=reduce_motion),
            offset_y=10,
        )
        if hovered_effect is not None:
            detail = get_effect_help(hovered_effect.get("id"))
            draw_hint_bar(
                screen,
                fonts["small"],
                inspector_rect,
                f"{hovered_effect.get('label', hovered_effect.get('id', 'Effect'))}: {detail}",
                fill_color=(249, 242, 228),
                border_color=PALETTE["gold_dark"],
                text_color=PALETTE["text"],
            )
        else:
            draw_hint_bar(
                screen,
                fonts["small"],
                inspector_rect,
                "Re chuot vao tung effect de xem mo ta nhanh. Phim 1-3 de doi bo loc, mui ten de cuon.",
            )

        close_rect = get_reveal_rect(
            pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 56, 180, 40),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=300, reduce_motion=reduce_motion),
            offset_y=8,
        )
        draw_button(
            screen,
            fonts["font"],
            close_rect,
            "Dong so tay",
            PALETTE["mint"],
            PALETTE["mint_dark"],
            close_rect.collidepoint(mouse_pos),
            PALETTE["text"],
        )

        pygame.display.flip()

        max_scroll = max(0, content_height - content_rect.height + 18)
        scroll_y = max(0, min(scroll_y, max_scroll))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_b}:
                return "back"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                active_filter = "all"
                scroll_y = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                active_filter = "builtin"
                scroll_y = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_3:
                active_filter = "custom"
                scroll_y = 0
            if event.type == pygame.KEYDOWN and event.key in {pygame.K_UP, pygame.K_w}:
                scroll_y = max(0, scroll_y - 36)
            if event.type == pygame.KEYDOWN and event.key in {pygame.K_DOWN, pygame.K_s}:
                scroll_y = min(max_scroll, scroll_y + 36)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                scroll_y = max(0, scroll_y - content_rect.height + 80)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                scroll_y = min(max_scroll, scroll_y + content_rect.height - 80)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_HOME:
                scroll_y = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                scroll_y = max_scroll
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and close_rect.collidepoint(event.pos):
                    return "back"
                if event.button == 1:
                    for filter_key, rect in filter_rects:
                        if rect.collidepoint(event.pos):
                            active_filter = filter_key
                            scroll_y = 0
                            break
                if event.button == 4:
                    scroll_y = max(0, scroll_y - 36)
                if event.button == 5:
                    scroll_y = min(max_scroll, scroll_y + 36)

        clock.tick(60)
