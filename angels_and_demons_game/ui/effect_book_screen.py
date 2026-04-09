import os
import sys

import pygame

from mechanics.effects import get_builtin_effects
from mechanics.effects import get_custom_only_effects
from mechanics.effects import get_effect_help
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_panel
from ui.theme import draw_title


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


def wrap_text(font, text, max_width):
    words = str(text or "").split()
    if not words:
        return []

    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_effect_row(surface, fonts, rect, effect):
    title_font = fonts["font"]
    body_font = fonts["small"]
    tiny_font = fonts["tiny"]
    icon_key = ICON_KEYS.get(str(effect.get("id", "")))
    icon_surface = get_surface(icon_key, (34, 34)) if icon_key else None

    draw_panel(surface, rect, fill_color=(248, 241, 230), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
    if icon_surface is not None:
        surface.blit(icon_surface, (rect.x + 16, rect.y + 12))
    else:
        badge_rect = pygame.Rect(rect.x + 16, rect.y + 12, 34, 34)
        draw_panel(surface, badge_rect, fill_color=(238, 229, 214), border_color=PALETTE["panel_dark"], radius=17, shadow=False)
        fallback = tiny_font.render(str(effect.get("label", "?"))[:1], True, PALETTE["text"])
        surface.blit(fallback, (badge_rect.centerx - fallback.get_width() // 2, badge_rect.centery - fallback.get_height() // 2))

    title = title_font.render(str(effect.get("label", effect.get("id", "Effect"))), True, PALETTE["text"])
    surface.blit(title, (rect.x + 62, rect.y + 10))

    subtitle = "Custom only" if effect.get("custom_only") else "Mac dinh"
    subtitle_surface = tiny_font.render(subtitle, True, PALETTE["muted"])
    surface.blit(subtitle_surface, (rect.x + 62, rect.y + 34))

    help_lines = wrap_text(body_font, get_effect_help(effect.get("id")), rect.width - 86)[:3]
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
        "font": pygame.font.Font(font_path, 18),
        "small": pygame.font.Font(font_path, 14),
        "tiny": pygame.font.Font(font_path, 12),
    }
    clock = pygame.time.Clock()
    scroll_y = 0
    sections = [
        ("8 hieu ung co san", "Che do thuong luon dung 8 hieu ung nay.", get_builtin_effects()),
        ("Chi co trong custom", "Nhom chien thuat dac biet, chi mo trong custom va challenge mo rong.", get_custom_only_effects()),
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, pygame.time.get_ticks())

        panel_rect = pygame.Rect(42, 28, screen.get_width() - 84, screen.get_height() - 56)
        draw_panel(screen, panel_rect, fill_color=(249, 242, 228), border_color=PALETTE["gold_dark"], radius=28)
        draw_title(screen, fonts["title"], "So tay hieu ung", (panel_rect.centerx, panel_rect.y + 42), PALETTE["text"])

        subtitle = fonts["small"].render("Nhan B hoac Esc de dong. Day la bang mo ta nhanh de tra effect trong luc choi.", True, PALETTE["muted"])
        screen.blit(subtitle, (panel_rect.centerx - subtitle.get_width() // 2, panel_rect.y + 74))

        content_rect = pygame.Rect(panel_rect.x + 24, panel_rect.y + 112, panel_rect.width - 48, panel_rect.height - 188)
        draw_panel(screen, content_rect, fill_color=(252, 246, 236), border_color=PALETTE["lilac"], radius=22, shadow=False)

        y = content_rect.y + 18 - scroll_y
        content_height = 0
        for title, helper, effects in sections:
            title_surface = fonts["font"].render(title, True, PALETTE["text"])
            helper_surface = fonts["small"].render(helper, True, PALETTE["muted"])
            screen.blit(title_surface, (content_rect.x + 18, y))
            screen.blit(helper_surface, (content_rect.x + 18, y + 24))
            y += 54
            content_height += 54

            for effect in effects:
                row_rect = pygame.Rect(content_rect.x + 14, y, content_rect.width - 28, 112)
                if row_rect.bottom >= content_rect.y + 8 and row_rect.top <= content_rect.bottom - 8:
                    draw_effect_row(screen, fonts, row_rect, effect)
                y += 124
                content_height += 124
            y += 8
            content_height += 8

        close_rect = pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 56, 180, 40)
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and close_rect.collidepoint(event.pos):
                    return "back"
                if event.button == 4:
                    scroll_y = max(0, scroll_y - 36)
                if event.button == 5:
                    scroll_y = min(max_scroll, scroll_y + 36)

        clock.tick(60)
