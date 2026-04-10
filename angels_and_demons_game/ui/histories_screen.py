import os
import sys

import pygame

from constants import BOARD_LAYOUTS
from constants import MODE_VARIANTS
from mechanics.effects import get_effect_help
from models.history import clear_game_history
from models.history import delete_game_history_entry
from models.history import load_game_history
from models.settings import load_settings
from models.turn_modes import TURN_MODE_LABELS
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.custom_setup import draw_layout_preview
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


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def wrap_history_text(font, text, max_width, max_lines=2):
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
            if len(lines) >= max_lines - 1:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


FILTER_OPTIONS = [
    ("all", "Tat ca"),
    ("human", "Nguoi"),
    ("challenge", "Challenge"),
    ("series", "Best of 3"),
]


def filter_history_entries(history, filter_mode="all"):
    history = history if isinstance(history, list) else []
    if filter_mode == "human":
        return [(index, game) for index, game in enumerate(history) if not game.get("has_bots")]
    if filter_mode == "challenge":
        return [(index, game) for index, game in enumerate(history) if str(game.get("mode_variant", "")) == "challenge"]
    if filter_mode == "series":
        return [(index, game) for index, game in enumerate(history) if str(game.get("mode_variant", "")) == "best_of_three"]
    return list(enumerate(history))


def draw_filter_chip(surface, font, rect, label, active=False, hovered=False):
    fill_color = (247, 223, 184) if active else (247, 239, 223) if hovered else (241, 234, 221)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)
    text_surface = font.render(label, True, PALETTE["text"])
    surface.blit(text_surface, (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2))


def draw_history_meta_chip(surface, font, rect, label, fill_color, border_color, text_color=None):
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=12, shadow=False)
    text_surface = font.render(clamp_text(font, label, rect.width - 14), True, text_color or PALETTE["text"])
    surface.blit(text_surface, (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2))


def draw_history_inspector(surface, title_font, body_font, title, detail):
    rect = pygame.Rect(60, surface.get_height() - 132, surface.get_width() - 120, 52)
    draw_panel(surface, rect, fill_color=(249, 242, 228), border_color=PALETTE["gold_dark"], radius=18, shadow=False)
    title_surface = title_font.render(title, True, PALETTE["text"])
    surface.blit(title_surface, (rect.x + 14, rect.y + 8))
    lines = wrap_history_text(body_font, detail, rect.width - 28, max_lines=2)
    line_y = rect.y + 28
    for line in lines:
        line_surface = body_font.render(line, True, PALETTE["muted"])
        surface.blit(line_surface, (rect.x + 14, line_y))
        line_y += 16


def show_history_screen(screen, font):
    scroll_y = 0
    scroll_speed = 32
    running = True
    active_filter = "all"
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    body_font = get_ui_font(17, bold=True)
    small_font = get_ui_font(15)
    tiny_font = get_ui_font(13)
    emblem_surface = get_surface("brand_emblem", (44, 44))
    apply_window_icon()
    intro_tick = pygame.time.get_ticks()
    reduce_motion = load_settings().get("reduce_motion", False)

    while running:
        history = load_game_history()
        filtered_entries = filter_history_entries(history, active_filter)
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)
        mouse_pos = pygame.mouse.get_pos()
        header_progress = get_reveal_progress(intro_tick, tick, duration=360, reduce_motion=reduce_motion)

        header_rect = get_reveal_rect(pygame.Rect(34, 24, screen.get_width() - 68, 74), header_progress, offset_y=18)
        draw_panel(screen, header_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=24)
        draw_title(screen, title_font, "Lich su cac van choi", (header_rect.centerx, header_rect.centery), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (header_rect.right - 62, header_rect.y + 14))

        clear_all_rect = get_reveal_rect(
            pygame.Rect(screen.get_width() - 210, 116, 170, 46),
            get_reveal_progress(intro_tick, tick, duration=340, delay_ms=80, reduce_motion=reduce_motion),
            offset_y=12,
        )
        if history:
            draw_button(screen, small_font, clear_all_rect, "Xoa tat ca", PALETTE["crimson"], PALETTE["crimson_dark"], clear_all_rect.collidepoint(pygame.mouse.get_pos()))

        filter_rects = []
        chip_x = 40
        chip_y = 118
        chip_widths = {"all": 90, "human": 92, "challenge": 126, "series": 116}
        for filter_index, (filter_key, label) in enumerate(FILTER_OPTIONS):
            rect = get_reveal_rect(
                pygame.Rect(chip_x, chip_y, chip_widths[filter_key], 34),
                get_reveal_progress(intro_tick, tick, duration=320, delay_ms=110 + filter_index * 30, reduce_motion=reduce_motion),
                offset_y=10,
            )
            draw_filter_chip(screen, tiny_font, rect, label, active=active_filter == filter_key, hovered=rect.collidepoint(mouse_pos))
            filter_rects.append((filter_key, rect))
            chip_x = rect.right + 10

        content_top = 170
        content_bottom = screen.get_height() - 90
        content_height = 0
        delete_buttons = []
        hover_entries = []

        y = content_top - scroll_y
        ordered_entries = list(reversed(filtered_entries))
        for display_index, (history_index, game) in enumerate(ordered_entries, start=1):
            players = game.get("players", [])
            top_effects = game.get("top_effects", [])
            extra_lines = 1 if game.get("winner") else 0
            extra_lines += 1 if game.get("num_boxes") else 0
            extra_lines += len(top_effects[:2])
            card_height = 110 + (len(players) + extra_lines) * 24
            row_progress = get_reveal_progress(intro_tick, tick, duration=320, delay_ms=170 + min(display_index - 1, 6) * 32, reduce_motion=reduce_motion)
            card_rect = get_reveal_rect(pygame.Rect(40, y, screen.get_width() - 80, card_height), row_progress, offset_y=12)

            if card_rect.bottom >= content_top and card_rect.top <= content_bottom:
                draw_panel(screen, card_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=20)
                stripe_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 42)
                pygame.draw.rect(screen, PALETTE["panel_dark"], stripe_rect, border_top_left_radius=20, border_top_right_radius=20)

                title_copy = clamp_text(body_font, f"Tran {display_index} - {game.get('timestamp', 'Unknown')}", stripe_rect.width - 150)
                title_text = body_font.render(title_copy, True, PALETTE["white"])
                screen.blit(title_text, (card_rect.x + 18, card_rect.y + 10))

                delete_rect = pygame.Rect(card_rect.right - 118, card_rect.y + 8, 92, 28)
                draw_button(screen, small_font, delete_rect, "Xoa", PALETTE["crimson"], PALETTE["crimson_dark"], delete_rect.collidepoint(pygame.mouse.get_pos()))
                delete_buttons.append((history_index, delete_rect))

                layout_label = BOARD_LAYOUTS.get(str(game.get("layout_id", "classic")), BOARD_LAYOUTS["classic"])["label"]
                preview_rect = pygame.Rect(card_rect.x + 18, card_rect.y + 54, 82, 58)
                draw_layout_preview(screen, preview_rect, game.get("num_boxes", 0), BOARD_LAYOUTS.get(str(game.get("layout_id", "classic")), BOARD_LAYOUTS["classic"])["columns"], active=card_rect.collidepoint(mouse_pos))
                content_x = preview_rect.right + 16
                content_width = card_rect.right - content_x - 18
                player_y = card_rect.y + 54
                winner_name = str(game.get("winner", "")).strip()
                if winner_name:
                    winner_score = game.get("winner_score", 0)
                    winner_copy = clamp_text(body_font, f"Thang: {winner_name} - {winner_score} diem", content_width)
                    winner_text = body_font.render(winner_copy, True, PALETTE["text"])
                    screen.blit(winner_text, (content_x, player_y))
                    player_y += 24

                num_boxes = game.get("num_boxes")
                if num_boxes:
                    turn_mode = game.get("turn_mode")
                    turn_mode_label = TURN_MODE_LABELS.get(turn_mode, "Lan luot")
                    opened_count = game.get("opened_count", num_boxes)
                    mode_variant = str(game.get("mode_variant", "standard"))
                    mode_label = MODE_VARIANTS.get(mode_variant, MODE_VARIANTS["standard"])["label"]
                    if mode_variant == "challenge" and game.get("challenge_title"):
                        mode_label = f"{mode_label}: {game.get('challenge_title')}"
                    elif mode_variant == "best_of_three":
                        mode_label = f"{mode_label} - Round {game.get('round_number', 1)}"
                    meta_copy = clamp_text(
                        small_font,
                        f"{turn_mode_label} | {opened_count}/{num_boxes} o da mo",
                        content_width,
                    )
                    meta_text = small_font.render(meta_copy, True, PALETTE["muted"])
                    screen.blit(meta_text, (content_x, player_y))

                    mode_chip_width = min(194, max(110, tiny_font.size(mode_label)[0] + 18))
                    layout_chip_width = min(122, max(86, tiny_font.size(layout_label)[0] + 18))
                    chip_y = player_y + 22
                    mode_chip_rect = pygame.Rect(content_x, chip_y, mode_chip_width, 22)
                    layout_chip_rect = pygame.Rect(mode_chip_rect.right + 8, chip_y, layout_chip_width, 22)
                    draw_history_meta_chip(screen, tiny_font, mode_chip_rect, mode_label, (255, 241, 224), PALETTE["gold_dark"])
                    draw_history_meta_chip(screen, tiny_font, layout_chip_rect, layout_label, (232, 241, 255), PALETTE["azure_dark"])
                    player_y = chip_y + 30

                for player_index, player in enumerate(players, start=1):
                    bullet_color = PALETTE["gold"] if player_index == 1 else PALETTE["azure"]
                    pygame.draw.circle(screen, bullet_color, (content_x + 8, player_y + 10), 6)
                    player_copy = clamp_text(body_font, f"{player.get('name', 'Unknown')}: {player.get('score', 0)} diem", content_width - 22)
                    player_text = body_font.render(player_copy, True, PALETTE["text"])
                    screen.blit(player_text, (content_x + 22, player_y))
                    player_y += 24

                for effect in top_effects[:2]:
                    effect_label = str(effect.get("label", effect.get("id", "Effect")))
                    effect_count = effect.get("count", 0)
                    effect_copy = clamp_text(small_font, f"Top effect: {effect_label} x{effect_count}", content_width)
                    effect_text = small_font.render(effect_copy, True, PALETTE["muted"])
                    effect_pos = (content_x, player_y)
                    screen.blit(effect_text, effect_pos)
                    hover_entries.append(
                        {
                            "rect": pygame.Rect(effect_pos[0] - 4, effect_pos[1] - 2, min(content_width, effect_text.get_width() + 10), effect_text.get_height() + 4),
                            "title": effect_label,
                            "detail": get_effect_help(effect.get("id")),
                        }
                    )
                    player_y += 22

                achievements = game.get("unlocked_achievements", [])
                if achievements:
                    unlocked_titles = ", ".join(item.get("title", "") for item in achievements[:2])
                    achievement_copy = clamp_text(small_font, f"Thanh tuu moi: {unlocked_titles}", content_width)
                    achievement_text = small_font.render(achievement_copy, True, PALETTE["muted"])
                    screen.blit(achievement_text, (content_x, player_y))
                    player_y += 22

            y += card_height + 16
            content_height += card_height + 16

        if not history:
            empty_rect = pygame.Rect(screen.get_width() // 2 - 220, screen.get_height() // 2 - 70, 440, 140)
            draw_panel(screen, empty_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=24)
            draw_title(screen, title_font, "Chua co lich su", (empty_rect.centerx, empty_rect.centery - 12), PALETTE["text"])
            helper = small_font.render("Bat dau mot tran moi de lap day bo suu tap ky niem.", True, PALETTE["muted"])
            screen.blit(helper, (empty_rect.centerx - helper.get_width() // 2, empty_rect.centery + 22))

        back_rect = get_reveal_rect(
            pygame.Rect(screen.get_width() // 2 - 90, screen.get_height() - 60, 180, 44),
            get_reveal_progress(intro_tick, tick, duration=320, delay_ms=360, reduce_motion=reduce_motion),
            offset_y=8,
        )
        draw_button(screen, small_font, back_rect, "Quay lai", PALETTE["mint"], PALETTE["mint_dark"], back_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])

        scrollbar_rect = pygame.Rect(screen.get_width() - 34, content_top + 4, 10, content_bottom - content_top - 8)
        draw_scrollbar(screen, scrollbar_rect, content_height, content_bottom - content_top, scroll_y, accent_color=PALETTE["gold_dark"])

        hovered_entry = next((entry for entry in hover_entries if entry["rect"].collidepoint(mouse_pos)), None)
        if hovered_entry is not None:
            draw_history_inspector(screen, small_font, tiny_font, hovered_entry["title"], hovered_entry["detail"])
        else:
            hint_rect = pygame.Rect(60, screen.get_height() - 132, screen.get_width() - 120, 40)
            filtered_count = len(filtered_entries)
            draw_hint_bar(
                screen,
                tiny_font,
                hint_rect,
                f"Esc de quay lai | Phim 1-4 de loc | Dang hien {filtered_count}/{len(history)} tran | Re vao Top effect de xem chi tiet",
            )

        pygame.display.flip()

        max_scroll = max(0, content_height - (content_bottom - content_top))
        scroll_y = max(0, min(scroll_y, max_scroll))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_RETURN}:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                active_filter = "all"
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                active_filter = "human"
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_3:
                active_filter = "challenge"
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_4:
                active_filter = "series"
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_UP, pygame.K_w}:
                scroll_y = max(0, scroll_y - scroll_speed)
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_DOWN, pygame.K_s}:
                scroll_y = min(max_scroll, scroll_y + scroll_speed)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEUP:
                scroll_y = max(0, scroll_y - (content_bottom - content_top) + 60)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_PAGEDOWN:
                scroll_y = min(max_scroll, scroll_y + (content_bottom - content_top) - 60)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_HOME:
                scroll_y = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_END:
                scroll_y = max_scroll
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and back_rect.collidepoint(event.pos):
                    running = False
                elif event.button == 1 and history and clear_all_rect.collidepoint(event.pos):
                    clear_game_history()
                    scroll_y = 0
                elif event.button == 1:
                    for filter_key, rect in filter_rects:
                        if rect.collidepoint(event.pos):
                            active_filter = filter_key
                            scroll_y = 0
                            break
                    for history_index, delete_rect in delete_buttons:
                        if delete_rect.collidepoint(event.pos):
                            delete_game_history_entry(history_index)
                            break
                elif event.button == 4:
                    scroll_y = max(0, scroll_y - scroll_speed)
                elif event.button == 5:
                    scroll_y = min(max_scroll, scroll_y + scroll_speed)
