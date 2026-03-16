import math
import os
import sys

import pygame

from mechanics.effects import apply_effect
from mechanics.effects import play_effect
from mechanics.randomizer import get_random_effect
from models.history import save_game_history_entry
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import TURN_MODE_LABELS
from models.turn_modes import normalize_turn_mode
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


def save_game_history(players):
    save_game_history_entry(players)


def render_text(surface, font, text, pos, color):
    surface.blit(font.render(text, True, color), pos)


def truncate_text(font, text, max_width):
    if max_width <= 0:
        return ""
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    ellipsis_width = font.size(ellipsis)[0]
    if ellipsis_width >= max_width:
        return ellipsis

    trimmed = text
    while trimmed and font.size(trimmed)[0] + ellipsis_width > max_width:
        trimmed = trimmed[:-1]
    return f"{trimmed.rstrip()}{ellipsis}"


def get_banner_style(message):
    lowered = message.lower()
    if "thien" in lowered or "angel" in lowered:
        return PALETTE["gold"], (244, 233, 196)
    if "ac" in lowered or "devil" in lowered:
        return PALETTE["crimson"], (239, 209, 213)
    if "may" in lowered or "lucky" in lowered:
        return PALETTE["mint"], (214, 232, 223)
    return PALETTE["azure"], (216, 226, 242)


def get_next_player_index(current_player, total_players, turn_mode):
    if turn_mode == SEQUENTIAL_TURN_MODE:
        return (current_player + 1) % total_players
    return current_player


def run_game_ui(players, num_boxes, dist_mode, custom_weights=None, turn_mode=SEQUENTIAL_TURN_MODE):
    pygame.init()
    screen = pygame.display.set_mode((1480, 860), pygame.RESIZABLE)
    pygame.display.set_caption("Angels and Demons - Game")

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    font = pygame.font.Font(font_path, 20)
    small_font = pygame.font.Font(font_path, 16)
    tiny_font = pygame.font.Font(font_path, 13)

    clock = pygame.time.Clock()
    canvas_size = (1480, 860)
    canvas = pygame.Surface(canvas_size)
    turn_mode = normalize_turn_mode(turn_mode)

    boxes = list(range(1, num_boxes + 1))
    opened = []
    current_player = 0 if turn_mode == SEQUENTIAL_TURN_MODE else None
    result_message = ""
    waiting_effect_input = False
    effect_to_resolve = None
    running = True

    while running:
        tick = pygame.time.get_ticks()
        draw_background(canvas, tick)

        scale_x = canvas_size[0] / max(1, screen.get_width())
        scale_y = canvas_size[1] / max(1, screen.get_height())
        mouse_x, mouse_y = pygame.mouse.get_pos()
        canvas_mouse = (int(mouse_x * scale_x), int(mouse_y * scale_y))

        sidebar_rect = pygame.Rect(28, 26, 330, canvas_size[1] - 52)
        board_rect = pygame.Rect(384, 26, canvas_size[0] - 412, canvas_size[1] - 52)
        draw_panel(canvas, sidebar_rect, fill_color=(244, 236, 219), border_color=PALETTE["gold_dark"], radius=28)
        draw_panel(canvas, board_rect, fill_color=(245, 239, 227), border_color=PALETTE["panel_dark"], radius=28)

        render_text(canvas, title_font, "Bang diem", (sidebar_rect.x + 28, sidebar_rect.y + 20), PALETTE["text"])

        info_panel_height = 176 if len(players) <= 8 else 150 if len(players) <= 16 else 128
        player_cards_top = sidebar_rect.y + 82
        players_area_bottom = sidebar_rect.bottom - info_panel_height - 24
        players_area_height = max(80, players_area_bottom - player_cards_top)
        players_area_width = sidebar_rect.width - 40
        col_gap = 10

        player_columns = 1
        layout_found = False
        for candidate_columns in (1, 2, 3):
            player_rows = max(1, math.ceil(len(players) / candidate_columns))
            candidate_row_gap = 10 if player_rows <= 6 else 8 if player_rows <= 10 else 6
            candidate_width = (players_area_width - col_gap * (candidate_columns - 1)) // candidate_columns
            candidate_height = (players_area_height - candidate_row_gap * max(0, player_rows - 1)) // player_rows
            min_width = 190 if candidate_columns == 1 else 130 if candidate_columns == 2 else 86
            min_height = 46 if candidate_columns == 1 else 36 if candidate_columns == 2 else 28
            if candidate_width >= min_width and candidate_height >= min_height:
                player_columns = candidate_columns
                layout_found = True
                break

        if not layout_found:
            player_columns = 3

        player_rows = max(1, math.ceil(len(players) / player_columns))
        row_gap = 10 if player_rows <= 6 else 8 if player_rows <= 10 else 6
        player_card_width = (players_area_width - col_gap * (player_columns - 1)) // player_columns
        player_card_height = max(24, (players_area_height - row_gap * max(0, player_rows - 1)) // player_rows)

        player_hitboxes = []
        for index, player in enumerate(players):
            row = index // player_columns
            col = index % player_columns
            card_x = sidebar_rect.x + 20 + col * (player_card_width + col_gap)
            card_y = player_cards_top + row * (player_card_height + row_gap)
            card_rect = pygame.Rect(card_x, card_y, player_card_width, player_card_height)
            player_hitboxes.append((index, card_rect))

            if index == current_player:
                fill_color = (242, 228, 188)
                border_color = PALETTE["gold_dark"]
                draw_glow(canvas, card_rect.center, PALETTE["gold"], max(34, player_card_height + 10), 26)
            else:
                fill_color = (233, 224, 209)
                border_color = PALETTE["panel_dark"]

            draw_panel(canvas, card_rect, fill_color=fill_color, border_color=border_color, radius=20, shadow=False)
            badge_rect = None
            content_right = card_rect.right - 12
            show_turn_badge = index == current_player and player_card_width >= 150 and player_card_height >= 30
            if show_turn_badge:
                badge_width = 58 if player_card_width >= 150 else 52 if player_card_width >= 110 else 44
                badge_height = min(26, max(18, player_card_height - 8))
                badge_y = card_rect.y + max(4, (player_card_height - badge_height) // 2)
                badge_rect = pygame.Rect(card_rect.right - badge_width - 8, badge_y, badge_width, badge_height)
                content_right = badge_rect.x - 8
            elif index == current_player:
                indicator_radius = 5 if player_card_height >= 32 else 4
                pygame.draw.circle(
                    canvas,
                    PALETTE["gold_dark"],
                    (card_rect.right - 12, card_rect.y + max(12, indicator_radius + 6)),
                    indicator_radius,
                )

            if player_card_height >= 54 and player_card_width >= 150:
                name_font = font
                score_font = small_font
                max_text_width = max(24, content_right - (card_rect.x + 14))
                name_text = truncate_text(name_font, player.name, max_text_width)
                score_text = truncate_text(score_font, f"{player.score} diem", max_text_width)
                render_text(canvas, name_font, name_text, (card_rect.x + 14, card_rect.y + 9), PALETTE["text"])
                render_text(canvas, score_font, score_text, (card_rect.x + 14, card_rect.y + 33), PALETTE["muted"])
            else:
                name_font = small_font if player_card_height >= 30 else tiny_font
                score_font = tiny_font
                score_text = f"{player.score}d"
                score_surface = score_font.render(score_text, True, PALETTE["muted"])
                score_x = max(card_rect.x + 12, content_right - score_surface.get_width())
                max_name_width = max(24, score_x - card_rect.x - 20)
                name_text = truncate_text(name_font, player.name, max_name_width)
                name_surface = name_font.render(name_text, True, PALETTE["text"])
                baseline_y = card_rect.centery - max(name_surface.get_height(), score_surface.get_height()) // 2
                canvas.blit(name_surface, (card_rect.x + 10, baseline_y))
                canvas.blit(score_surface, (score_x, card_rect.centery - score_surface.get_height() // 2))

            if badge_rect is not None:
                draw_button(
                    canvas,
                    tiny_font if badge_height < 24 else small_font,
                    badge_rect,
                    "TURN",
                    PALETTE["gold"],
                    PALETTE["gold_dark"],
                    badge_rect.collidepoint(canvas_mouse),
                    PALETTE["text"],
                )

        info_rect = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.bottom - info_panel_height - 20, sidebar_rect.width - 40, info_panel_height)
        draw_panel(canvas, info_rect, fill_color=(233, 224, 209), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        render_text(canvas, font, "Thong tin", (info_rect.x + 18, info_rect.y + 16), PALETTE["text"])
        remaining_boxes = len(boxes) - len(opened)
        stats_y = info_rect.y + 52
        stats_gap = 24 if info_panel_height >= 150 else 20
        selected_name = players[current_player].name if current_player is not None else "Chua chon"
        render_text(canvas, small_font, f"Kieu luot: {TURN_MODE_LABELS[turn_mode]}", (info_rect.x + 18, stats_y), PALETTE["muted"])
        if turn_mode == MANUAL_TURN_MODE:
            render_text(canvas, small_font, f"Dang chon: {selected_name}", (info_rect.x + 18, stats_y + stats_gap), PALETTE["muted"])
        else:
            render_text(canvas, small_font, f"Dang den luot: {selected_name}", (info_rect.x + 18, stats_y + stats_gap), PALETTE["muted"])
        render_text(canvas, small_font, f"Con lai: {remaining_boxes} | Da mo: {len(opened)}", (info_rect.x + 18, stats_y + stats_gap * 2), PALETTE["muted"])
        if waiting_effect_input:
            helper_text = "Nhan 1 neu thang, 2 neu thua."
        elif turn_mode == MANUAL_TURN_MODE and current_player is None:
            helper_text = "Click vao nguoi choi ben trai truoc khi mo o."
        elif turn_mode == MANUAL_TURN_MODE:
            helper_text = "Co the doi nguoi choi ben trai truoc khi mo o."
        else:
            helper_text = "Chon o bat ky de mo."
        render_text(canvas, small_font, helper_text, (info_rect.x + 18, info_rect.bottom - 30), PALETTE["muted"])

        render_text(canvas, title_font, "Ban co", (board_rect.x + 26, board_rect.y + 18), PALETTE["text"])
        render_text(canvas, small_font, "Click vao mot o de kich hoat hieu ung.", (board_rect.x + 28, board_rect.y + 58), PALETTE["muted"])

        grid_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 92, board_rect.width - 48, board_rect.height - 170)
        draw_panel(canvas, grid_rect, fill_color=(232, 223, 207), border_color=PALETTE["panel_dark"], radius=24, shadow=False)

        cols = 10
        box_size = 72
        gap = 12
        rows = max(1, math.ceil(len(boxes) / cols))
        board_total_width = cols * box_size + (cols - 1) * gap
        board_total_height = rows * box_size + (rows - 1) * gap
        start_x = grid_rect.x + max(18, (grid_rect.width - board_total_width) // 2)
        start_y = grid_rect.y + max(18, (grid_rect.height - board_total_height) // 2)

        hovered_index = None
        for index, num in enumerate(boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            if rect.collidepoint(canvas_mouse) and num not in opened and not waiting_effect_input:
                hovered_index = index

        for index, num in enumerate(boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)

            if num in opened:
                fill_color = (202, 197, 206)
                border_color = PALETTE["panel_dark"]
                text_color = PALETTE["muted"]
            else:
                fill_color = (223, 231, 249)
                border_color = PALETTE["azure_dark"]
                text_color = PALETTE["text"]

            if hovered_index == index:
                fill_color = (244, 230, 186)
                border_color = PALETTE["gold_dark"]
                draw_glow(canvas, rect.center, PALETTE["gold"], 52, 24)

            draw_panel(canvas, rect, fill_color=fill_color, border_color=border_color, radius=18, shadow=False)
            num_text = font.render(str(num), True, text_color)
            canvas.blit(num_text, (rect.centerx - num_text.get_width() // 2, rect.centery - num_text.get_height() // 2))

        quit_rect = pygame.Rect(board_rect.right - 192, board_rect.bottom - 62, 152, 38)
        draw_button(
            canvas,
            small_font,
            quit_rect,
            "Ket thuc",
            PALETTE["crimson"],
            PALETTE["crimson_dark"],
            quit_rect.collidepoint(canvas_mouse),
        )

        if result_message:
            accent_color, fill_color = get_banner_style(result_message)
            banner_rect = pygame.Rect(board_rect.x + 26, board_rect.bottom - 64, board_rect.width - 236, 40)
            draw_panel(canvas, banner_rect, fill_color=fill_color, border_color=accent_color, radius=18, shadow=False)
            text = small_font.render(result_message, True, PALETTE["text"])
            canvas.blit(text, (banner_rect.x + 14, banner_rect.centery - text.get_height() // 2))

        scaled_canvas = pygame.transform.smoothscale(canvas, screen.get_size())
        screen.blit(scaled_canvas, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = (int(event.pos[0] * scale_x), int(event.pos[1] * scale_y))

                if quit_rect.collidepoint(pos):
                    save_game_history(players)
                    show_final_result(screen, title_font, font, players)
                    return

                if turn_mode == MANUAL_TURN_MODE and not waiting_effect_input:
                    selected_player = False
                    for index, card_rect in player_hitboxes:
                        if card_rect.collidepoint(pos):
                            current_player = index
                            selected_player = True
                            break
                    if selected_player:
                        continue

                if not waiting_effect_input:
                    if turn_mode == MANUAL_TURN_MODE and current_player is None:
                        result_message = "Hay chon nguoi choi truoc khi mo o."
                        continue
                    for index, num in enumerate(boxes):
                        x = start_x + (index % cols) * (box_size + gap)
                        y = start_y + (index // cols) * (box_size + gap)
                        rect = pygame.Rect(x, y, box_size, box_size)
                        if rect.collidepoint(pos) and num not in opened:
                            opened.append(num)
                            effect_id = get_random_effect(dist_mode, custom_weights)
                            if effect_id == 6:
                                play_effect(6)
                                result_message = f"{players[current_player].name} mo o {num} - Keo bua bao! Nhan 1 de thang, 2 de thua."
                                effect_to_resolve = {"player": players[current_player]}
                                waiting_effect_input = True
                            else:
                                result_message = (
                                    f"{players[current_player].name} mo o {num} - "
                                    f"{apply_effect(effect_id, players[current_player], players)}"
                                )
                                current_player = get_next_player_index(current_player, len(players), turn_mode)
                            break
            elif event.type == pygame.KEYDOWN and waiting_effect_input:
                if event.key == pygame.K_1:
                    effect_to_resolve["player"].add_score(10)
                    result_message = f"{effect_to_resolve['player'].name} thang Keo bua bao! +10 diem."
                    current_player = get_next_player_index(current_player, len(players), turn_mode)
                    waiting_effect_input = False
                    effect_to_resolve = None
                elif event.key == pygame.K_2:
                    result_message = f"{effect_to_resolve['player'].name} thua Keo bua bao."
                    current_player = get_next_player_index(current_player, len(players), turn_mode)
                    waiting_effect_input = False
                    effect_to_resolve = None

        pygame.display.flip()
        clock.tick(60)


def show_final_result(screen, title_font, font, players):
    players.sort(key=lambda player: player.score, reverse=True)
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    small_font = pygame.font.Font(font_path, 16)
    tiny_font = pygame.font.Font(font_path, 14)
    waiting = True

    while waiting:
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)

        panel_rect = pygame.Rect(120, 80, screen.get_width() - 240, screen.get_height() - 160)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        render_text(screen, title_font, "Ket qua cuoi cung", (panel_rect.x + 40, panel_rect.y + 28), PALETTE["text"])

        winner = players[0]
        winner_text = f"Nguoi thang: {winner.name} - {winner.score} diem"
        render_text(screen, small_font, winner_text, (panel_rect.x + 42, panel_rect.y + 72), PALETTE["muted"])

        chart_rect = pygame.Rect(panel_rect.x + 42, panel_rect.y + 122, panel_rect.width - 84, panel_rect.height - 220)
        draw_panel(screen, chart_rect, fill_color=(240, 232, 214), border_color=PALETTE["panel_dark"], radius=24, shadow=False)

        label_width = min(220, max(140, chart_rect.width // 4))
        score_width = 96
        bar_left = chart_rect.x + label_width + 28
        bar_right = chart_rect.right - score_width - 20
        bar_width = max(140, bar_right - bar_left)
        max_score = max(1, max(player.score for player in players))
        row_gap = 12 if len(players) <= 8 else 8 if len(players) <= 12 else 4
        row_height = max(18, min(54, (chart_rect.height - 34 - row_gap * max(0, len(players) - 1)) // max(1, len(players))))
        colors = [PALETTE["gold"], PALETTE["azure"], PALETTE["mint"]]

        for index, player in enumerate(players):
            row_y = chart_rect.y + 18 + index * (row_height + row_gap)
            row_rect = pygame.Rect(chart_rect.x + 16, row_y, chart_rect.width - 32, row_height)
            track_rect = pygame.Rect(bar_left, row_y + max(4, row_height // 5), bar_width, max(10, row_height - 10))
            fill_width = max(14, int(track_rect.width * (player.score / max_score))) if player.score > 0 else 0
            fill_rect = pygame.Rect(track_rect.x, track_rect.y, fill_width, track_rect.height)
            bar_color = colors[index] if index < 3 else (190, 174, 145)

            draw_panel(screen, row_rect, fill_color=(246, 239, 225), border_color=PALETTE["panel_dark"], radius=16, shadow=False)
            name_text = truncate_text(small_font if row_height >= 36 else tiny_font, f"{index + 1}. {player.name}", label_width - 26)
            render_text(
                screen,
                small_font if row_height >= 36 else tiny_font,
                name_text,
                (row_rect.x + 14, row_rect.y + max(6, (row_height - 20) // 2)),
                PALETTE["text"],
            )

            pygame.draw.rect(screen, (220, 210, 190), track_rect, border_radius=12)
            if fill_width > 0:
                pygame.draw.rect(screen, bar_color, fill_rect, border_radius=12)
                pygame.draw.rect(screen, PALETTE["panel_dark"], fill_rect, 1, border_radius=12)
            pygame.draw.rect(screen, PALETTE["panel_dark"], track_rect, 1, border_radius=12)

            score_text = f"{player.score} diem"
            score_surface = (small_font if row_height >= 36 else tiny_font).render(score_text, True, PALETTE["text"])
            score_x = row_rect.right - score_surface.get_width() - 12
            score_y = row_rect.y + (row_height - score_surface.get_height()) // 2
            screen.blit(score_surface, (score_x, score_y))

        ok_rect = pygame.Rect(screen.get_width() // 2 - 90, panel_rect.bottom - 74, 180, 46)
        draw_button(screen, font, ok_rect, "OK - Thoat", PALETTE["mint"], PALETTE["mint_dark"], ok_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ok_rect.collidepoint(event.pos):
                waiting = False
