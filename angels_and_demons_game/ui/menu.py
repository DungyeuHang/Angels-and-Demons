import os
import sys

import pygame

from config import MENU_WINDOW_SIZE
from config import create_display
from ui.custom_mode_setup import run_custom_mode_ui
from ui.custom_setup import run_default_setup_ui
from ui.audio import play_sfx
from ui.audio import play_music
from ui.audio import sync_audio_settings
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.effect_book_screen import show_effect_book_screen
from ui.game_screen import run_game_ui
from ui.histories_screen import show_history_screen
from ui.settings_screen import show_settings_screen
from ui.stats_screen import show_stats_screen
from models.settings import load_settings
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
        players, num_boxes, dist_mode, custom_weights, turn_mode, session_options = run_default_setup_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights, turn_mode, session_options=session_options)
    elif index == 1:
        players, num_boxes, dist_mode, custom_weights, turn_mode, session_options = run_custom_mode_ui()
        if players:
            run_game_ui(players, num_boxes, dist_mode, custom_weights, turn_mode, session_options=session_options)
    elif index == 2:
        play_music("history", force_restart=True)
        show_stats_screen(screen, font)
    elif index == 3:
        play_music("history", force_restart=True)
        show_history_screen(screen, font)
    elif index == 4:
        show_settings_screen()
    elif index == 5:
        return False, screen

    settings = load_settings()
    sync_audio_settings(settings)
    screen = create_display(MENU_WINDOW_SIZE, "Menu", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()
    play_music("menu", force_restart=True)
    return True, screen


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
    title_y = rect.y + 8
    surface.blit(title_surface, (rect.centerx - title_surface.get_width() // 2, title_y))

    detail_lines = wrap_text(detail_font, detail, rect.width - 48)[:2]
    detail_y = rect.y + 30
    for line in detail_lines:
        line_surface = detail_font.render(line, True, PALETTE["muted"])
        surface.blit(line_surface, (rect.x + 24, detail_y))
        detail_y += line_surface.get_height() + 1


def run_menu_ui():
    pygame.init()
    settings = load_settings()
    sync_audio_settings(settings)
    screen = create_display(MENU_WINDOW_SIZE, "Menu", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()
    play_music("menu", force_restart=True)

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 42)
    font = pygame.font.Font(font_path, 18)
    small_font = pygame.font.Font(font_path, 15)
    tiny_font = pygame.font.Font(font_path, 12)
    clock = pygame.time.Clock()
    emblem_surface = get_surface("brand_emblem", (56, 56))
    angel_badge = get_surface("angel_badge", (32, 32))
    demon_badge = get_surface("demon_badge", (32, 32))

    options = [
        ("Choi mac dinh", "Vao game nhanh voi preset tran, layout moi va bot AI."),
        ("Che do custom", "Tu tao luat choi, ti le hieu ung, bot va map rieng."),
        ("Thong ke", "Xem thanh tuu, top hieu ung, career score va bang vang."),
        ("Xem lich su", "Nhin lai nguoi thang, mode, layout va thanh tuu moi."),
        ("Cai dat", "Bat tat nhac, SFX, fullscreen va dieu chinh volume."),
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

        hero_rect = pygame.Rect(main_rect.x + 34, main_rect.y + 24, main_rect.width - 68, 162)
        draw_panel(screen, hero_rect, fill_color=(252, 241, 231), border_color=PALETTE["lilac"], radius=30, shadow=False)

        draw_mascot(screen, (hero_rect.x + 92, hero_rect.centery + 18), "angel", tick, 0.72)
        draw_mascot(screen, (hero_rect.right - 92, hero_rect.centery + 22), "demon", tick + 140, 0.7)
        draw_star(screen, (hero_rect.x + 162, hero_rect.y + 36), 10, PALETTE["gold"])
        draw_star(screen, (hero_rect.right - 162, hero_rect.y + 44), 8, PALETTE["crimson"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (hero_rect.centerx - emblem_surface.get_width() // 2, hero_rect.y + 8))

        draw_title(screen, title_font, "Angels and Demons", (hero_rect.centerx, hero_rect.y + 62), PALETTE["text"])
        draw_subtitle(screen, small_font, "Mo o, nhan diem, xoay chieu tran dau va nghich effect moi vui hon.", (hero_rect.centerx, hero_rect.y + 96))
        draw_subtitle(screen, tiny_font, "Lan luot hoac custom, co nhat ky su kien, preview va choi lai ngay.", (hero_rect.centerx, hero_rect.y + 118))

        chip_y = hero_rect.y + 130
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx - 190, chip_y, 110, 28), "Board co san", (255, 236, 225), PALETTE["peach"])
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx - 56, chip_y, 108, 28), "Co preview", (232, 241, 255), PALETTE["azure_dark"])
        draw_chip(screen, tiny_font, pygame.Rect(hero_rect.centerx + 74, chip_y, 126, 28), "Replay & history", (231, 245, 236), PALETTE["mint_dark"])
        book_rect = pygame.Rect(hero_rect.right - 174, hero_rect.bottom - 42, 138, 28)
        draw_chip(screen, tiny_font, book_rect, "B - So tay", (240, 234, 248), PALETTE["lilac"])

        section_title_y = hero_rect.bottom + 18
        section_label = small_font.render("Chon mot cach de bat dau", True, PALETTE["muted"])
        screen.blit(section_label, (main_rect.x + 42, section_title_y))
        draw_star(screen, (main_rect.x + 26, section_title_y + 10), 7, PALETTE["gold"])
        draw_star(screen, (main_rect.right - 28, section_title_y + 8), 6, PALETTE["lilac"])
        if angel_badge is not None:
            screen.blit(angel_badge, (main_rect.right - 118, section_title_y - 10))
        if demon_badge is not None:
            screen.blit(demon_badge, (main_rect.right - 78, section_title_y - 10))
        draw_cloud(screen, (main_rect.right - 90, main_rect.bottom - 36), 0.45, (255, 247, 243))

        option_rects = []
        for index, (label, detail) in enumerate(options):
            rect = pygame.Rect(main_rect.x + 44, section_title_y + 20 + index * 58, main_rect.width - 88, 54)
            hovered = rect.collidepoint(mouse_pos)
            if hovered:
                selected = index

            if index == len(options) - 1:
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

        footer_text = tiny_font.render("Tip: phim mui ten + Enter van hoat dong, nhan B de mo so tay effect.", True, PALETTE["muted"])
        screen.blit(footer_text, (main_rect.x + 42, main_rect.bottom - 20))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    play_sfx("ui_click", volume_multiplier=0.35)
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    play_sfx("ui_click", volume_multiplier=0.35)
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    play_sfx("ui_click", volume_multiplier=0.42)
                    keep_running, screen = activate_option(selected, screen, font)
                    if not keep_running:
                        return
                elif event.key == pygame.K_b:
                    play_sfx("ui_click", volume_multiplier=0.36)
                    if show_effect_book_screen(screen) == "quit":
                        return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if book_rect.collidepoint(event.pos):
                    play_sfx("ui_click", volume_multiplier=0.36)
                    if show_effect_book_screen(screen) == "quit":
                        return
                    continue
                for index, rect in enumerate(option_rects):
                    if rect.collidepoint(event.pos):
                        selected = index
                        play_sfx("ui_click", volume_multiplier=0.42)
                        keep_running, screen = activate_option(index, screen, font)
                        if not keep_running:
                            return

        clock.tick(60)
