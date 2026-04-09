import os
import sys

import pygame

from config import MENU_WINDOW_SIZE
from config import create_display
from models.settings import load_settings
from models.settings import update_settings
from ui.audio import play_music
from ui.audio import play_sfx
from ui.audio import sync_audio_settings
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_hint_bar
from ui.theme import draw_panel
from ui.theme import draw_title
from ui.theme import get_ui_font
from ui.theme import get_reveal_progress
from ui.theme import get_reveal_rect
from ui.theme import wrap_text


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _slider_value_from_pos(rect, pos_x):
    ratio = (pos_x - rect.x) / max(1, rect.width)
    return max(0.0, min(1.0, ratio))


def _draw_slider(surface, font, rect, label, value):
    label_surface = font.render(label, True, PALETTE["text"])
    value_surface = font.render(f"{int(value * 100)}%", True, PALETTE["muted"])
    surface.blit(label_surface, (rect.x, rect.y - 28))
    surface.blit(value_surface, (rect.right - value_surface.get_width(), rect.y - 28))
    pygame.draw.rect(surface, (220, 210, 190), rect, border_radius=12)
    fill_rect = pygame.Rect(rect.x, rect.y, int(rect.width * value), rect.height)
    if fill_rect.width > 0:
        pygame.draw.rect(surface, PALETTE["gold"], fill_rect, border_radius=12)
    pygame.draw.rect(surface, PALETTE["panel_dark"], rect, 1, border_radius=12)
    knob_x = rect.x + int(rect.width * value)
    knob_x = max(rect.x + 10, min(rect.right - 10, knob_x))
    pygame.draw.circle(surface, PALETTE["white"], (knob_x, rect.centery), 11)
    pygame.draw.circle(surface, PALETTE["panel_dark"], (knob_x, rect.centery), 11, 2)


def _apply_slider_delta(settings, key, delta):
    return update_settings({key: max(0.0, min(1.0, float(settings.get(key, 0.0)) + delta))})


def show_settings_screen():
    pygame.init()
    settings = load_settings()
    sync_audio_settings(settings)
    screen = create_display(MENU_WINDOW_SIZE, "Cai dat", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    font = get_ui_font(18, bold=True)
    small_font = get_ui_font(15)
    emblem_surface = get_surface("brand_emblem", (56, 56))
    clock = pygame.time.Clock()
    dragging = None
    intro_tick = pygame.time.get_ticks()

    while True:
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, tick)
        reduce_motion = settings.get("reduce_motion", False)
        panel_progress = get_reveal_progress(intro_tick, tick, duration=380, reduce_motion=reduce_motion)

        panel_rect = get_reveal_rect(pygame.Rect(86, 48, screen.get_width() - 172, screen.get_height() - 96), panel_progress, offset_y=22)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        draw_title(screen, title_font, "Cai dat", (panel_rect.centerx, panel_rect.y + 48), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (panel_rect.right - 90, panel_rect.y + 20))

        toggle_specs = [
            ("music_enabled", "Nhac nen", "Bat / tat nhac menu, game, result"),
            ("sfx_enabled", "Hieu ung am thanh", "Bat / tat tieng mo o, effect, achievement"),
            ("fullscreen", "Toan man hinh", "Dung fullscreen cho menu va cac screen khac"),
            ("reduce_motion", "Giam chuyen dong", "Lam animation em hon cho may yeu hon"),
        ]
        toggle_rects = []
        start_y = panel_rect.y + 108
        for index, (key, label, detail) in enumerate(toggle_specs):
            row_progress = get_reveal_progress(intro_tick, tick, duration=340, delay_ms=70 + index * 45, reduce_motion=reduce_motion)
            rect = get_reveal_rect(pygame.Rect(panel_rect.x + 48, start_y + index * 78, panel_rect.width - 96, 62), row_progress, offset_y=14)
            draw_panel(surface=screen, rect=rect, fill_color=(244, 236, 222), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
            state_text = "Bat" if settings.get(key, False) else "Tat"
            screen.blit(font.render(label, True, PALETTE["text"]), (rect.x + 18, rect.y + 12))
            screen.blit(small_font.render(detail, True, PALETTE["muted"]), (rect.x + 18, rect.y + 34))
            pill_rect = pygame.Rect(rect.right - 112, rect.y + 14, 82, 32)
            active = settings.get(key, False)
            draw_button(
                screen,
                small_font,
                pill_rect,
                state_text,
                PALETTE["mint"] if active else PALETTE["panel_soft"],
                PALETTE["mint_dark"] if active else PALETTE["panel_dark"],
                pill_rect.collidepoint(mouse_pos),
                PALETTE["text"],
            )
            toggle_rects.append((key, pill_rect))

        music_slider_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 78, panel_rect.y + 448, panel_rect.width - 156, 18),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=260, reduce_motion=reduce_motion),
            offset_y=12,
        )
        sfx_slider_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 78, panel_rect.y + 528, panel_rect.width - 156, 18),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=310, reduce_motion=reduce_motion),
            offset_y=12,
        )
        _draw_slider(screen, font, music_slider_rect, "Am luong nhac", settings["music_volume"])
        _draw_slider(screen, font, sfx_slider_rect, "Am luong SFX", settings["sfx_volume"])

        helper_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 48, panel_rect.bottom - 104, panel_rect.width - 96, 54),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=360, reduce_motion=reduce_motion),
            offset_y=10,
        )
        draw_panel(screen, helper_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
        helper_text = "Moi thay doi duoc luu ngay. Neu doi fullscreen, menu se cap nhat lai sau khi dong man nay."
        helper_lines = wrap_text(small_font, helper_text, helper_rect.width - 32, max_lines=2)
        helper_y = helper_rect.y + 9
        for line in helper_lines:
            helper_surface = small_font.render(line, True, PALETTE["muted"])
            screen.blit(helper_surface, (helper_rect.x + 16, helper_y))
            helper_y += small_font.get_height() + 2

        hint_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 48, panel_rect.bottom - 146, panel_rect.width - 96, 32),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=330, reduce_motion=reduce_motion),
            offset_y=10,
        )
        draw_hint_bar(
            screen,
            small_font,
            hint_rect,
            "Esc: quay lai | M: nhac | S: SFX | F: fullscreen | R: giam chuyen dong | <- ->: nhac | A D: SFX",
        )

        back_rect = get_reveal_rect(
            pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 44, 180, 38),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=400, reduce_motion=reduce_motion),
            offset_y=8,
        )
        draw_button(screen, small_font, back_rect, "Quay lai", PALETTE["crimson"], PALETTE["crimson_dark"], back_rect.collidepoint(mouse_pos), PALETTE["text"])

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                settings = update_settings({"music_enabled": not settings.get("music_enabled", False)})
                sync_audio_settings(settings)
                play_music("menu")
                play_sfx("ui_click", volume_multiplier=0.45)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                settings = update_settings({"sfx_enabled": not settings.get("sfx_enabled", False)})
                sync_audio_settings(settings)
                play_music("menu")
                play_sfx("ui_click", volume_multiplier=0.45)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                settings = update_settings({"fullscreen": not settings.get("fullscreen", False)})
                sync_audio_settings(settings)
                screen = create_display(MENU_WINDOW_SIZE, "Cai dat", fullscreen=settings.get("fullscreen", False))
                apply_window_icon()
                play_music("menu")
                play_sfx("ui_click", volume_multiplier=0.45)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                settings = update_settings({"reduce_motion": not settings.get("reduce_motion", False)})
                sync_audio_settings(settings)
                play_music("menu")
                play_sfx("ui_click", volume_multiplier=0.45)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
                settings = _apply_slider_delta(settings, "music_volume", -0.05)
                sync_audio_settings(settings)
                play_music("menu")
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                settings = _apply_slider_delta(settings, "music_volume", 0.05)
                sync_audio_settings(settings)
                play_music("menu")
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_a, pygame.K_COMMA}:
                settings = _apply_slider_delta(settings, "sfx_volume", -0.05)
                sync_audio_settings(settings)
                play_sfx("ui_click", volume_multiplier=0.45)
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_d, pygame.K_PERIOD}:
                settings = _apply_slider_delta(settings, "sfx_volume", 0.05)
                sync_audio_settings(settings)
                play_sfx("ui_click", volume_multiplier=0.45)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(event.pos):
                    play_sfx("ui_click", volume_multiplier=0.45)
                    return
                for key, rect in toggle_rects:
                    if rect.collidepoint(event.pos):
                        settings = update_settings({key: not settings.get(key, False)})
                        sync_audio_settings(settings)
                        play_music("menu")
                        play_sfx("ui_click", volume_multiplier=0.45)
                        if key == "fullscreen":
                            screen = create_display(MENU_WINDOW_SIZE, "Cai dat", fullscreen=settings.get("fullscreen", False))
                            apply_window_icon()
                        break
                if music_slider_rect.collidepoint(event.pos):
                    dragging = "music_volume"
                    settings = update_settings({"music_volume": _slider_value_from_pos(music_slider_rect, event.pos[0])})
                    sync_audio_settings(settings)
                    play_music("menu")
                elif sfx_slider_rect.collidepoint(event.pos):
                    dragging = "sfx_volume"
                    settings = update_settings({"sfx_volume": _slider_value_from_pos(sfx_slider_rect, event.pos[0])})
                    sync_audio_settings(settings)
                    play_sfx("ui_click", volume_multiplier=0.55)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = None
            elif event.type == pygame.MOUSEMOTION and dragging:
                if dragging == "music_volume":
                    settings = update_settings({"music_volume": _slider_value_from_pos(music_slider_rect, event.pos[0])})
                    sync_audio_settings(settings)
                    play_music("menu")
                elif dragging == "sfx_volume":
                    settings = update_settings({"sfx_volume": _slider_value_from_pos(sfx_slider_rect, event.pos[0])})
                    sync_audio_settings(settings)

        clock.tick(60)
