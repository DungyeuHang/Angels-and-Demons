import os
import sys

import pygame

from mechanics.effects import get_effect_label
from mechanics.effects import get_effect_help
from models.progression import build_profile_summary
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
from ui.theme import get_title_font
from ui.theme import get_ui_font
from ui.theme import get_reveal_progress
from ui.theme import get_reveal_rect


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def show_stats_screen(screen, font):
    summary = build_profile_summary()
    title_font = get_title_font(30)
    value_font = get_ui_font(24, bold=True)
    heading_font = get_ui_font(18, bold=True)
    small_font = get_ui_font(16)
    tiny_font = get_ui_font(13)
    emblem_surface = get_surface("brand_emblem", (52, 52))
    angel_badge = get_surface("angel_badge", (28, 28))
    demon_badge = get_surface("demon_badge", (28, 28))
    apply_window_icon()
    clock = pygame.time.Clock()
    intro_tick = pygame.time.get_ticks()
    reduce_motion = load_settings().get("reduce_motion", False)
    left_scroll_y = 0
    right_scroll_y = 0
    scroll_speed = 36

    while True:
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)
        mouse_pos = pygame.mouse.get_pos()
        panel_progress = get_reveal_progress(intro_tick, tick, duration=380, reduce_motion=reduce_motion)

        panel_rect = get_reveal_rect(pygame.Rect(40, 26, screen.get_width() - 80, screen.get_height() - 52), panel_progress, offset_y=22)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=28)
        draw_title(screen, title_font, "Thống kê sự nghiệp", (panel_rect.centerx, panel_rect.y + 38), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (panel_rect.right - 86, panel_rect.y + 14))

        card_titles = [
            ("Trận đã chơi", str(summary["games_played"])),
            ("O da mo", str(summary["total_boxes_opened"])),
            ("Điểm cao nhất", str(summary["career_best_score"])),
            ("Big swing", f"+{summary['largest_swing']}"),
        ]
        for index, (title, value) in enumerate(card_titles):
            card_progress = get_reveal_progress(intro_tick, tick, duration=340, delay_ms=60 + index * 45, reduce_motion=reduce_motion)
            card_rect = get_reveal_rect(pygame.Rect(panel_rect.x + 38 + index * 220, panel_rect.y + 84, 196, 82), card_progress, offset_y=14)
            accent = [PALETTE["gold"], PALETTE["azure"], PALETTE["mint"], PALETTE["crimson"]][index % 4]
            fill = {
                PALETTE["gold"]: (247, 239, 212),
                PALETTE["azure"]: (220, 230, 245),
                PALETTE["mint"]: (221, 236, 228),
                PALETTE["crimson"]: (243, 223, 226),
            }[accent]
            draw_panel(screen, card_rect, fill_color=fill, border_color=accent, radius=20, shadow=False)
            screen.blit(tiny_font.render(title, True, PALETTE["muted"]), (card_rect.x + 14, card_rect.y + 12))
            screen.blit(value_font.render(value, True, PALETTE["text"]), (card_rect.x + 14, card_rect.y + 36))

        left_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 38, panel_rect.y + 190, 420, panel_rect.height - 280),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=220, reduce_motion=reduce_motion),
            offset_y=16,
        )
        right_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 482, panel_rect.y + 190, panel_rect.width - 520, panel_rect.height - 280),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=260, reduce_motion=reduce_motion),
            offset_y=16,
        )
        draw_panel(screen, left_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        draw_panel(screen, right_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        hover_hint = None

        screen.blit(heading_font.render("Bảng vàng", True, PALETTE["text"]), (left_rect.x + 16, left_rect.y + 12))
        if angel_badge is not None:
            screen.blit(angel_badge, (left_rect.right - 48, left_rect.y + 10))

        left_body_rect = pygame.Rect(left_rect.x + 8, left_rect.y + 44, left_rect.width - 22, left_rect.height - 54)
        left_y = left_rect.y + 54 - left_scroll_y
        previous_clip = screen.get_clip()
        screen.set_clip(left_body_rect)
        if summary["top_players"]:
            for index, (name, wins) in enumerate(summary["top_players"], start=1):
                row_rect = pygame.Rect(left_rect.x + 14, left_y, left_rect.width - 28, 42)
                draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
                player_label = clamp_text(small_font, f"{index}. {name}", row_rect.width - 118)
                screen.blit(small_font.render(player_label, True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 10))
                wins_surface = small_font.render(f"{wins} thang", True, PALETTE["muted"])
                screen.blit(wins_surface, (row_rect.right - wins_surface.get_width() - 12, row_rect.y + 10))
                left_y += 48
        else:
            screen.blit(small_font.render("Chưa có người chơi nào được lưu thống kê.", True, PALETTE["muted"]), (left_rect.x + 16, left_y))
            left_y += 38

        screen.blit(heading_font.render("Top hiệu ứng", True, PALETTE["text"]), (left_rect.x + 16, left_y + 10))
        left_y += 46
        for effect_id, count in summary["top_effects"]:
            row_rect = pygame.Rect(left_rect.x + 14, left_y, left_rect.width - 28, 38)
            draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=12, shadow=False)
            effect_label = clamp_text(small_font, get_effect_label(effect_id, fallback=effect_id), row_rect.width - 78)
            screen.blit(small_font.render(effect_label, True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 8))
            count_surface = small_font.render(f"x{count}", True, PALETTE["muted"])
            screen.blit(count_surface, (row_rect.right - count_surface.get_width() - 12, row_rect.y + 8))
            if row_rect.collidepoint(mouse_pos):
                hover_hint = f"{get_effect_label(effect_id, fallback=effect_id)}: {get_effect_help(effect_id)}"
            left_y += 44
        left_content_height = max(0, left_y - left_rect.y + 8)
        left_max_scroll = max(0, left_content_height - left_body_rect.height)
        screen.set_clip(previous_clip)
        if left_max_scroll > 0:
            draw_scrollbar(screen, pygame.Rect(left_rect.right - 12, left_body_rect.y + 4, 8, left_body_rect.height - 8), left_content_height, left_body_rect.height, left_scroll_y, accent_color=PALETTE["gold_dark"])

        screen.blit(heading_font.render("Thành tựu", True, PALETTE["text"]), (right_rect.x + 16, right_rect.y + 12))
        if demon_badge is not None:
            screen.blit(demon_badge, (right_rect.right - 48, right_rect.y + 10))

        right_body_rect = pygame.Rect(right_rect.x + 8, right_rect.y + 44, right_rect.width - 22, right_rect.height - 54)
        achievement_y = right_rect.y + 52 - right_scroll_y
        previous_clip = screen.get_clip()
        screen.set_clip(right_body_rect)
        achievements = summary["achievements"]
        if achievements:
            for achievement in achievements:
                row_rect = pygame.Rect(right_rect.x + 14, achievement_y, right_rect.width - 28, 58)
                draw_panel(screen, row_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
                title_text = clamp_text(small_font, achievement["title"], row_rect.width - 24)
                detail_text = clamp_text(tiny_font, achievement["description"], row_rect.width - 24)
                screen.blit(small_font.render(title_text, True, PALETTE["text"]), (row_rect.x + 12, row_rect.y + 10))
                screen.blit(tiny_font.render(detail_text, True, PALETTE["muted"]), (row_rect.x + 12, row_rect.y + 32))
                if row_rect.collidepoint(mouse_pos):
                    hover_hint = f"{achievement['title']}: {achievement['description']}"
                achievement_y += 66
        else:
            screen.blit(small_font.render("Chưa mở khóa thành tựu nào. Chơi thêm để lấp đầy bảng vàng.", True, PALETTE["muted"]), (right_rect.x + 16, achievement_y))
        right_content_height = max(0, achievement_y - right_rect.y + 8)
        right_max_scroll = max(0, right_content_height - right_body_rect.height)
        screen.set_clip(previous_clip)
        if right_max_scroll > 0:
            draw_scrollbar(screen, pygame.Rect(right_rect.right - 12, right_body_rect.y + 4, 8, right_body_rect.height - 8), right_content_height, right_body_rect.height, right_scroll_y, accent_color=PALETTE["lilac"])

        footer_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 38, panel_rect.bottom - 72, panel_rect.width - 76, 44),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=320, reduce_motion=reduce_motion),
            offset_y=10,
        )
        draw_panel(screen, footer_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=16, shadow=False)
        footer_text = f"Da mo {summary['achievement_count']} thanh tuu | {summary['total_boxes_opened']} o da mo | {summary['total_steal_points']} diem da cuop"
        footer_copy = clamp_text(tiny_font, footer_text, footer_rect.width - 24)
        footer_surface = tiny_font.render(footer_copy, True, PALETTE["text"])
        screen.blit(footer_surface, (footer_rect.centerx - footer_surface.get_width() // 2, footer_rect.y + 13))

        hint_rect = get_reveal_rect(
            pygame.Rect(panel_rect.x + 38, panel_rect.bottom - 118, panel_rect.width - 76, 34),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=360, reduce_motion=reduce_motion),
            offset_y=10,
        )
        last_winner = summary.get("last_winner") or "Chưa có"
        last_played_at = summary.get("last_played_at") or "Chưa chơi"
        draw_hint_bar(
            screen,
            tiny_font,
            hint_rect,
            hover_hint or f"Lan gan nhat: {last_winner} | {last_played_at} | Con lan de cuon tung cot | Esc de quay lai",
        )

        back_rect = get_reveal_rect(
            pygame.Rect(panel_rect.centerx - 90, panel_rect.bottom - 30, 180, 40),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=400, reduce_motion=reduce_motion),
            offset_y=8,
        )
        draw_button(screen, small_font, back_rect, "Quay lại", PALETTE["mint"], PALETTE["mint_dark"], back_rect.collidepoint(mouse_pos), PALETTE["text"])

        left_scroll_y = max(0, min(left_scroll_y, left_max_scroll))
        right_scroll_y = max(0, min(right_scroll_y, right_max_scroll))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_RETURN}:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = max(0, left_scroll_y - scroll_speed)
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = max(0, right_scroll_y - scroll_speed)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = min(left_max_scroll, left_scroll_y + scroll_speed)
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = min(right_max_scroll, right_scroll_y + scroll_speed)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = max(0, left_scroll_y - max(120, left_body_rect.height - 100))
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = max(0, right_scroll_y - max(120, right_body_rect.height - 100))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = min(left_max_scroll, left_scroll_y + max(120, left_body_rect.height - 100))
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = min(right_max_scroll, right_scroll_y + max(120, right_body_rect.height - 100))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_HOME:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = 0
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = left_max_scroll
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = right_max_scroll
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 4:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = max(0, left_scroll_y - scroll_speed)
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = max(0, right_scroll_y - scroll_speed)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 5:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = min(left_max_scroll, left_scroll_y + scroll_speed)
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = min(right_max_scroll, right_scroll_y + scroll_speed)
            if event.type == pygame.MOUSEWHEEL:
                if left_rect.collidepoint(mouse_pos):
                    left_scroll_y = max(0, min(left_max_scroll, left_scroll_y - event.y * scroll_speed))
                elif right_rect.collidepoint(mouse_pos):
                    right_scroll_y = max(0, min(right_max_scroll, right_scroll_y - event.y * scroll_speed))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and back_rect.collidepoint(event.pos):
                return
        clock.tick(60)
