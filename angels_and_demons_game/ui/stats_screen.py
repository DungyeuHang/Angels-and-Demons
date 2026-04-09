import os
import sys

import pygame

from mechanics.effects import get_effect_label
from models.progression import build_profile_summary
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


def show_stats_screen(screen, font):
    summary = build_profile_summary()
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    small_font = pygame.font.Font(font_path, 16)
    tiny_font = pygame.font.Font(font_path, 13)
    emblem_surface = get_surface("brand_emblem", (52, 52))
    angel_badge = get_surface("angel_badge", (28, 28))
    demon_badge = get_surface("demon_badge", (28, 28))
    apply_window_icon()
    clock = pygame.time.Clock()

    while True:
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)

        panel_rect = pygame.Rect(40, 26, screen.get_width() - 80, screen.get_height() - 52)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=28)
        draw_title(screen, font, "Thong ke su nghiep", (panel_rect.centerx, panel_rect.y + 38), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (panel_rect.right - 86, panel_rect.y + 14))

        card_titles = [
            ("Tran da choi", str(summary["games_played"])),
            ("Tran co bot", str(summary["games_vs_bot"])),
            ("Diem cao nhat", str(summary["career_best_score"])),
            ("Big swing", f"+{summary['largest_swing']}"),
        ]
        for index, (title, value) in enumerate(card_titles):
            card_rect = pygame.Rect(panel_rect.x + 38 + index * 220, panel_rect.y + 84, 196, 82)
            accent = [PALETTE["gold"], PALETTE["azure"], PALETTE["mint"], PALETTE["crimson"]][index % 4]
            fill = {
                PALETTE["gold"]: (247, 239, 212),
                PALETTE["azure"]: (220, 230, 245),
                PALETTE["mint"]: (221, 236, 228),
                PALETTE["crimson"]: (243, 223, 226),
            }[accent]
            draw_panel(screen, card_rect, fill_color=fill, border_color=accent, radius=20, shadow=False)
            screen.blit(tiny_font.render(title, True, PALETTE["muted"]), (card_rect.x + 14, card_rect.y + 12))
            screen.blit(font.render(value, True, PALETTE["text"]), (card_rect.x + 14, card_rect.y + 40))

        left_rect = pygame.Rect(panel_rect.x + 38, panel_rect.y + 190, 420, panel_rect.height - 280)
        right_rect = pygame.Rect(panel_rect.x + 482, panel_rect.y + 190, panel_rect.width - 520, panel_rect.height - 280)
        draw_panel(screen, left_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        draw_panel(screen, right_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=22, shadow=False)

        screen.blit(font.render("Bang vang", True, PALETTE["text"]), (left_rect.x + 16, left_rect.y + 12))
        if angel_badge is not None:
            screen.blit(angel_badge, (left_rect.right - 48, left_rect.y + 10))

        left_y = left_rect.y + 54
        if summary["top_players"]:
            for index, (name, wins) in enumerate(summary["top_players"][:5], start=1):
                row_rect = pygame.Rect(left_rect.x + 14, left_y, left_rect.width - 28, 42)
                draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
                screen.blit(small_font.render(f"{index}. {name}", True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 10))
                wins_surface = small_font.render(f"{wins} thang", True, PALETTE["muted"])
                screen.blit(wins_surface, (row_rect.right - wins_surface.get_width() - 12, row_rect.y + 10))
                left_y += 48
        else:
            screen.blit(small_font.render("Chua co nguoi choi nao duoc luu thong ke.", True, PALETTE["muted"]), (left_rect.x + 16, left_y))
            left_y += 38

        screen.blit(font.render("Top effect", True, PALETTE["text"]), (left_rect.x + 16, left_y + 10))
        left_y += 46
        for effect_id, count in summary["top_effects"][:5]:
            row_rect = pygame.Rect(left_rect.x + 14, left_y, left_rect.width - 28, 38)
            draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=12, shadow=False)
            screen.blit(small_font.render(get_effect_label(effect_id, fallback=effect_id), True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 8))
            count_surface = small_font.render(f"x{count}", True, PALETTE["muted"])
            screen.blit(count_surface, (row_rect.right - count_surface.get_width() - 12, row_rect.y + 8))
            left_y += 44

        screen.blit(font.render("Thanh tuu", True, PALETTE["text"]), (right_rect.x + 16, right_rect.y + 12))
        if demon_badge is not None:
            screen.blit(demon_badge, (right_rect.right - 48, right_rect.y + 10))

        achievement_y = right_rect.y + 52
        achievements = summary["achievements"]
        if achievements:
            for achievement in achievements[:6]:
                row_rect = pygame.Rect(right_rect.x + 14, achievement_y, right_rect.width - 28, 58)
                draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
                screen.blit(small_font.render(achievement["title"], True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 10))
                screen.blit(tiny_font.render(achievement["description"], True, PALETTE["muted"]), (row_rect.x + 12, row_rect.y + 30))
                achievement_y += 66
        else:
            screen.blit(small_font.render("Chua mo khoa thanh tuu nao. Choi them de lap day bang vang.", True, PALETTE["muted"]), (right_rect.x + 16, achievement_y))

        footer_rect = pygame.Rect(panel_rect.x + 38, panel_rect.bottom - 72, panel_rect.width - 76, 44)
        draw_panel(screen, footer_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=16, shadow=False)
        footer_text = f"Da mo {summary['achievement_count']} thanh tuu | {summary['total_boxes_opened']} o da mo | {summary['total_steal_points']} diem da cuop"
        screen.blit(small_font.render(footer_text, True, PALETTE["text"]), (footer_rect.centerx - small_font.size(footer_text)[0] // 2, footer_rect.y + 12))

        back_rect = pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 30, 180, 40)
        draw_button(screen, small_font, back_rect, "Quay lai", PALETTE["mint"], PALETTE["mint_dark"], back_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and back_rect.collidepoint(event.pos):
                return
        clock.tick(60)
