import os
import sys

import pygame

from ui.custom_mode_setup import run_custom_mode_ui
from ui.custom_setup import run_default_setup_ui
from ui.game_screen import run_game_ui
from ui.histories_screen import show_history_screen
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_cloud
from ui.theme import draw_glow
from ui.theme import draw_mascot
from ui.theme import draw_panel
from ui.theme import draw_star
from ui.theme import draw_subtitle
from ui.theme import draw_title


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def activate_option(index, screen, font):
    if index == 0:
        players, num_boxes, dist_mode, custom_weights, turn_mode = run_default_setup_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights, turn_mode)
    elif index == 1:
        players, num_boxes, dist_mode, custom_weights, turn_mode = run_custom_mode_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights, turn_mode)
    elif index == 2:
        show_history_screen(screen, font)
    elif index == 3:
        return False
    return True


def draw_chip(surface, font, rect, label, fill_color, border_color):
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=18, shadow=False)
    text = font.render(label, True, PALETTE["text"])
    surface.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def wrap_text(font, text, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        trial = word if not current_line else f"{current_line} {word}"
        if font.size(trial)[0] <= max_width:
            current_line = trial
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines


def draw_menu_option(surface, title_font, detail_font, rect, title, detail, fill_color, border_color, hovered=False):
    if hovered:
        draw_glow(surface, rect.center, border_color, max(40, rect.width // 2), 18)

    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=26, shadow=True)

    title_surface = title_font.render(title, True, PALETTE["text"])
    title_y = rect.y + 11
    surface.blit(title_surface, (rect.centerx - title_surface.get_width() // 2, title_y))

    detail_lines = wrap_text(detail_font, detail, rect.width - 48)[:2]
    detail_y = rect.y + 39
    for line in detail_lines:
        line_surface = detail_font.render(line, True, PALETTE["muted"])
        surface.blit(line_surface, (rect.x + 24, detail_y))
        detail_y += line_surface.get_height() + 1


def run_menu_ui():
    pygame.init()
    screen = pygame.display.set_mode((940, 680))
    pygame.display.set_caption("Angels and Demons - Menu")

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 42)
    font = pygame.font.Font(font_path, 18)
    small_font = pygame.font.Font(font_path, 15)
    tiny_font = pygame.font.Font(font_path, 12)
    clock = pygame.time.Clock()

    options = [
        ("Choi mac dinh", "Vao game nhanh voi bo hieu ung co san."),
        ("Che do custom", "Tu tao luat choi va ti le hieu ung."),
        ("Xem lich su", "Nhin lai nhung van choi da luu."),
        ("Thoat", "Dong game sau khi thuong hai xong."),
    ]
    selected = 0

    while True:
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, tick)

        draw_cloud(screen, (142, 118), 0.82, (255, 249, 246))
        draw_cloud(screen, (812, 96), 0.92, (255, 246, 241))
        draw_glow(screen, (screen.get_width() * 0.5, 110), PALETTE["gold"], 170, 28)

        main_rect = pygame.Rect(72, 42, screen.get_width() - 144, screen.get_height() - 84)
        draw_panel(screen, main_rect, fill_color=(255, 247, 240), border_color=PALETTE["gold_dark"], radius=34)

        hero_rect = pygame.Rect(main_rect.x + 34, main_rect.y + 28, main_rect.width - 68, 184)
        draw_panel(screen, hero_rect, fill_color=(252, 241, 231), border_color=PALETTE["lilac"], radius=30, shadow=False)

        draw_mascot(screen, (hero_rect.x + 92, hero_rect.centery + 18), "angel", tick, 0.72)
        draw_mascot(screen, (hero_rect.right - 92, hero_rect.centery + 22), "demon", tick + 140, 0.7)
        draw_star(screen, (hero_rect.x + 162, hero_rect.y + 36), 10, PALETTE["gold"])
        draw_star(screen, (hero_rect.right - 162, hero_rect.y + 44), 8, PALETTE["crimson"])

        draw_title(screen, title_font, "Angels and Demons", (hero_rect.centerx, hero_rect.y + 52), PALETTE["text"])
        draw_subtitle(screen, small_font, "Mo o, nhan diem, pha game theo cach dang yeu hon mot chut.", (hero_rect.centerx, hero_rect.y + 92))
        draw_subtitle(screen, tiny_font, "Lan luot hoac custom, nghich vui nhung van de nhin va de choi.", (hero_rect.centerx, hero_rect.y + 118))

        chip_y = hero_rect.y + 142
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx - 170, chip_y, 96, 28), "De thuong", (255, 236, 225), PALETTE["peach"])
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx - 54, chip_y, 108, 28), "Co animation", (232, 241, 255), PALETTE["azure_dark"])
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx + 74, chip_y, 126, 28), "Custom vui hon", (231, 245, 236), PALETTE["mint_dark"])

        section_title_y = hero_rect.bottom + 18
        section_label = small_font.render("Chon mot cach de bat dau", True, PALETTE["muted"])
        screen.blit(section_label, (main_rect.x + 42, section_title_y))
        draw_star(screen, (main_rect.x + 26, section_title_y + 10), 7, PALETTE["gold"])
        draw_star(screen, (main_rect.right - 28, section_title_y + 8), 6, PALETTE["lilac"])
        draw_cloud(screen, (main_rect.right - 90, main_rect.bottom - 36), 0.45, (255, 247, 243))

        option_rects = []
        for index, (label, detail) in enumerate(options):
            rect = pygame.Rect(main_rect.x + 44, section_title_y + 24 + index * 74, main_rect.width - 88, 64)
            hovered = rect.collidepoint(mouse_pos)
            if hovered:
                selected = index

            if index == 3:
                base_color = (245, 213, 219)
                accent_color = PALETTE["crimson_dark"]
            elif index == selected:
                base_color = (247, 223, 184)
                accent_color = PALETTE["gold_dark"]
            else:
                base_color = (247, 240, 232)
                accent_color = PALETTE["panel_dark"]

            draw_menu_option(screen, font, tiny_font, rect, label, detail, base_color, accent_color, hovered or index == selected)
            option_rects.append(rect)

        footer_text = tiny_font.render("Tip: phim mui ten + Enter van hoat dong nhe.", True, PALETTE["muted"])
        screen.blit(footer_text, (main_rect.x + 42, main_rect.bottom - 20))

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
