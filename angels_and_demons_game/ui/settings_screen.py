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


def _slider_value_from_pos(rect, pos_x):
    ratio = (pos_x - rect.x) / max(1, rect.width)
    return max(0.0, min(1.0, ratio))


def _draw_slider(surface, font, rect, label, value):
    label_surface = font.render(label, True, PALETTE["text"])
    value_surface = font.render(f"{int(value * 100)}%", True, PALETTE["muted"])
    surface.blit(label_surface, (rect.x, rect.y - 24))
    surface.blit(value_surface, (rect.right - value_surface.get_width(), rect.y - 24))
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
    screen = create_display(MENU_WINDOW_SIZE, "Cài đặt", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 28)
    font = get_ui_font(15, bold=True)
    small_font = get_ui_font(11)
    tiny_font = get_ui_font(10)
    emblem_surface = get_surface("brand_emblem", (56, 56))
    clock = pygame.time.Clock()
    dragging = None
    intro_tick = pygame.time.get_ticks()
    scroll_y = 0
    scroll_speed = 36

    while True:
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        draw_background(screen, tick)
        reduce_motion = settings.get("reduce_motion", False)
        panel_progress = get_reveal_progress(intro_tick, tick, duration=380, reduce_motion=reduce_motion)

        panel_rect = get_reveal_rect(pygame.Rect(86, 48, screen.get_width() - 172, screen.get_height() - 96), panel_progress, offset_y=22)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        draw_title(screen, title_font, "Cài đặt", (panel_rect.centerx, panel_rect.y + 48), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (panel_rect.right - 90, panel_rect.y + 20))
        content_view_rect = pygame.Rect(panel_rect.x + 24, panel_rect.y + 92, panel_rect.width - 48, panel_rect.height - 154)
        previous_clip = screen.get_clip()
        screen.set_clip(content_view_rect)

        toggle_specs = [
            ("music_enabled", "Nhạc nền", "Bật / tắt nhạc menu, game, result"),
            ("sfx_enabled", "Hiệu ứng âm thanh", "Bật / tắt tiếng mở ô, effect, achievement"),
            ("fullscreen", "Toàn màn hình", "Dùng fullscreen cho menu và các screen khác"),
            ("reduce_motion", "Giảm chuyển động", "Làm animation êm hơn cho máy yếu hơn"),
        ]
        toggle_rects = []
        row_height = 60
        row_gap = 72
        start_y = panel_rect.y + 102 - scroll_y
        for index, (key, label, detail) in enumerate(toggle_specs):
            row_progress = get_reveal_progress(intro_tick, tick, duration=340, delay_ms=70 + index * 45, reduce_motion=reduce_motion)
            rect = get_reveal_rect(
                pygame.Rect(panel_rect.x + 48, start_y + index * row_gap, panel_rect.width - 96, row_height),
                row_progress,
                offset_y=14,
            )
            draw_panel(surface=screen, rect=rect, fill_color=(244, 236, 222), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
            state_text = "Bật" if settings.get(key, False) else "Tắt"
            screen.blit(font.render(label, True, PALETTE["text"]), (rect.x + 18, rect.y + 10))
            screen.blit(small_font.render(detail, True, PALETTE["muted"]), (rect.x + 18, rect.y + 34))
            pill_rect = pygame.Rect(rect.right - 108, rect.y + 14, 80, 30)
            active = settings.get(key, False)
            draw_button(
                screen,
                font,
                pill_rect,
                state_text,
                PALETTE["mint"] if active else PALETTE["panel_soft"],
                PALETTE["mint_dark"] if active else PALETTE["panel_dark"],
                pill_rect.collidepoint(mouse_pos),
                PALETTE["text"],
            )
            toggle_rects.append((key, pill_rect))

        music_slider_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 78, panel_rect.y + 402 - scroll_y, panel_rect.width - 156, 18),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=260, reduce_motion=reduce_motion),
            offset_y=12,
        )
        sfx_slider_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 78, panel_rect.y + 468 - scroll_y, panel_rect.width - 156, 18),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=310, reduce_motion=reduce_motion),
            offset_y=12,
        )
        _draw_slider(screen, small_font, music_slider_rect, "Âm lượng nhạc", settings["music_volume"])
        _draw_slider(screen, small_font, sfx_slider_rect, "Âm lượng SFX", settings["sfx_volume"])

        hint_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 48, panel_rect.y + 518 - scroll_y, panel_rect.width - 96, 30),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=330, reduce_motion=reduce_motion),
            offset_y=10,
        )
        draw_hint_bar(
            screen,
            tiny_font,
            hint_rect,
            "Esc: quay lại | M: nhạc | S: SFX | F: fullscreen | R: giảm chuyển động | <- ->: nhạc | A D: SFX",
        )

        helper_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 48, panel_rect.y + 556 - scroll_y, panel_rect.width - 96, 46),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=360, reduce_motion=reduce_motion),
            offset_y=10,
        )
        draw_panel(screen, helper_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
        helper_text = "Mọi thay đổi được lưu ngay. Nếu đổi fullscreen, menu sẽ cập nhật lại sau khi đóng màn này."
        helper_lines = wrap_text(small_font, helper_text, helper_rect.width - 32, max_lines=2)
        helper_y = helper_rect.y + 8
        for line in helper_lines:
            helper_surface = small_font.render(line, True, PALETTE["muted"])
            screen.blit(helper_surface, (helper_rect.x + 16, helper_y))
            helper_y += small_font.get_height() + 2
        content_height = helper_rect.bottom - panel_rect.y + 16
        max_scroll = max(0, content_height - content_view_rect.height)
        screen.set_clip(previous_clip)
        if max_scroll > 0:
            draw_scrollbar(
                screen,
                pygame.Rect(content_view_rect.right - 10, content_view_rect.y + 6, 8, content_view_rect.height - 12),
                content_height,
                content_view_rect.height,
                scroll_y,
                accent_color=PALETTE["gold_dark"],
            )

        back_rect = get_reveal_rect(
            pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 42, 180, 36),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=400, reduce_motion=reduce_motion),
            offset_y=8,
        )
        draw_button(screen, small_font, back_rect, "Quay lại", PALETTE["crimson"], PALETTE["crimson_dark"], back_rect.collidepoint(mouse_pos), PALETTE["text"])

        scroll_y = max(0, min(scroll_y, max_scroll))
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
                screen = create_display(MENU_WINDOW_SIZE, "Cài đặt", fullscreen=settings.get("fullscreen", False))
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
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_UP, pygame.K_w}:
                scroll_y = max(0, scroll_y - scroll_speed)
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_DOWN, pygame.K_s}:
                scroll_y = min(max_scroll, scroll_y + scroll_speed)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                scroll_y = max(0, scroll_y - max(120, content_view_rect.height - 100))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                scroll_y = min(max_scroll, scroll_y + max(120, content_view_rect.height - 100))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_HOME:
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                scroll_y = max_scroll
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
                            screen = create_display(MENU_WINDOW_SIZE, "Cài đặt", fullscreen=settings.get("fullscreen", False))
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 4 and content_view_rect.collidepoint(mouse_pos):
                scroll_y = max(0, scroll_y - scroll_speed)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 5 and content_view_rect.collidepoint(mouse_pos):
                scroll_y = min(max_scroll, scroll_y + scroll_speed)
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
            elif event.type == pygame.MOUSEWHEEL and content_view_rect.collidepoint(mouse_pos):
                scroll_y = max(0, min(max_scroll, scroll_y - event.y * scroll_speed))

        clock.tick(60)
