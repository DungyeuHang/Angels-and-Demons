import os
import sys

import pygame

from ui.custom_mode_setup import run_custom_mode_ui
from ui.custom_setup import run_default_setup_ui
from ui.game_screen import run_game_ui
from ui.histories_screen import show_history_screen
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_glow
from ui.theme import draw_panel


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def render_centered_text(surface, font, text, center, color):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, rect)
    return rect


def activate_option(index, screen, font):
    if index == 0:
        players, num_boxes, dist_mode, custom_weights = run_default_setup_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights)
    elif index == 1:
        players, num_boxes, dist_mode, custom_weights = run_custom_mode_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights)
    elif index == 2:
        show_history_screen(screen, font)
    elif index == 3:
        return False
    return True


def run_menu_ui():
    pygame.init()
    screen = pygame.display.set_mode((900, 640))
    pygame.display.set_caption("Angels and Demons - Menu")

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 52)
    font = pygame.font.Font(font_path, 20)
    clock = pygame.time.Clock()

    options = [
        "Choi mac dinh",
        "Che do custom",
        "Xem lich su",
        "Thoat",
    ]
    selected = 0

    while True:
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, tick)

        draw_glow(screen, (screen.get_width() * 0.5, 120), PALETTE["gold"], 200, 26)
        main_rect = pygame.Rect(120, 60, screen.get_width() - 240, 520)
        draw_panel(screen, main_rect, fill_color=(245, 237, 220), border_color=PALETTE["gold_dark"], radius=30)

        render_centered_text(screen, title_font, "Angels and Demons", (main_rect.centerx, 128), PALETTE["text"])

        option_rects = []
        for index, label in enumerate(options):
            rect = pygame.Rect(main_rect.x + 120, 190 + index * 82, main_rect.width - 240, 62)
            hovered = rect.collidepoint(mouse_pos)
            if hovered:
                selected = index

            if index == 3:
                base_color = (195, 108, 121)
                accent_color = PALETTE["crimson_dark"]
                text_color = PALETTE["white"]
            else:
                base_color = (226, 216, 198)
                accent_color = PALETTE["azure_dark"] if index != selected else PALETTE["gold_dark"]
                text_color = PALETTE["text"]

            draw_button(screen, font, rect, label, base_color, accent_color, hovered or index == selected, text_color)
            option_rects.append(rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if not activate_option(selected, screen, font):
                        return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, rect in enumerate(option_rects):
                    if rect.collidepoint(event.pos):
                        selected = index
                        if not activate_option(index, screen, font):
                            return

        clock.tick(60)
