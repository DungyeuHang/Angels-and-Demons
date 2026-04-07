import math
import os
import sys

import pygame

from mechanics.effects import apply_effect
from mechanics.effects import get_effect_definition
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


def get_effect_palette(effect_id=None, message=""):
    effect_id = str(effect_id or "")
    effect_definition = get_effect_definition(effect_id) if effect_id else None
    operation = str(effect_definition.get("operation", "")) if effect_definition else ""
    lowered = message.lower()

    if effect_id in {"angel", "lottery", "double"} or operation in {"add_self", "multiply_self", "others_gain", "all_gain"} or "thien" in lowered:
        return PALETTE["gold"], (247, 239, 212)
    if effect_id in {"devil", "half"} or operation in {"subtract_self", "divide_self", "others_lose", "all_lose"} or "ac" in lowered:
        return PALETTE["crimson"], (243, 223, 226)
    if effect_id in {"lucky"} or operation in {"bonus_turn"} or "may" in lowered or "them luot" in lowered:
        return PALETTE["mint"], (221, 236, 228)
    if effect_id in {"rps"} or operation in {"shield_self"} or "la chan" in lowered:
        return (132, 119, 96), (236, 231, 220)
    if operation in {"steal_random", "give_random", "swap_random"} or "cuop" in lowered or "cho " in lowered or "doi diem" in lowered:
        return (150, 101, 63), (240, 224, 204)
    if operation in {"skip_random", "reverse_order"} or "mat luot" in lowered or "dao chieu" in lowered:
        return (112, 77, 122), (233, 223, 236)
    return (101, 87, 71), (235, 228, 218)


def get_turn_direction_label(turn_direction):
    return "Xuoi" if turn_direction >= 0 else "Nguoc"


def build_status_tokens(player):
    tokens = []
    if player.shields > 0:
        tokens.append((f"S{player.shields}", PALETTE["azure"]))
    if player.bonus_turns > 0:
        tokens.append((f"+{player.bonus_turns}", PALETTE["mint"]))
    if player.skip_turns > 0:
        tokens.append((f"-{player.skip_turns}", PALETTE["crimson"]))
    return tokens


def consume_pending_skip(player):
    if player.consume_skip_turn():
        return f"{player.name} bi mat 1 luot!"
    return None


def resolve_next_player(current_player, players, turn_mode, turn_direction):
    if current_player is None or not players:
        return current_player, []

    active_player = players[current_player]
    if active_player.consume_bonus_turn():
        return current_player, []

    if turn_mode == MANUAL_TURN_MODE:
        return current_player, []

    skipped_names = []
    total_players = len(players)
    for _ in range(total_players):
        current_player = (current_player + turn_direction) % total_players
        if players[current_player].consume_skip_turn():
            skipped_names.append(players[current_player].name)
            continue
        return current_player, skipped_names
    return current_player, skipped_names


def set_banner(message, effect_id=None):
    return {
        "message": message,
        "effect_id": effect_id,
        "created_at": pygame.time.get_ticks(),
    }


def append_skip_notice(message, skipped_names):
    if not skipped_names:
        return message
    if len(skipped_names) == 1:
        return f"{message} {skipped_names[0]} bi bo qua luot."
    return f"{message} {', '.join(skipped_names)} bi bo qua luot."


def get_stat_cards(players):
    if not players:
        return []

    opened_star = max(players, key=lambda player: (player.boxes_opened, player.score, -player.biggest_loss))
    steal_star = max(players, key=lambda player: (player.steal_points, player.score))
    shield_star = max(players, key=lambda player: (player.shield_blocks, player.shields, player.score))
    combo_star = max(players, key=lambda player: (player.biggest_gain, player.score))

    return [
        ("Mo o nhieu", opened_star.name, f"{opened_star.boxes_opened} o"),
        ("Cuop diem", steal_star.name, f"{steal_star.steal_points} diem"),
        ("Dung la chan", shield_star.name, f"{shield_star.shield_blocks} lan"),
        ("Bung no lon", combo_star.name, f"+{combo_star.biggest_gain} diem"),
    ]


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
    game_state = {"turn_direction": 1, "turn_mode": turn_mode}

    boxes = list(range(1, num_boxes + 1))
    opened = set()
    box_effects = {}
    current_player = 0 if turn_mode == SEQUENTIAL_TURN_MODE else None
    banner = None
    waiting_effect_input = False
    effect_to_resolve = None

    while True:
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

        info_panel_height = 196 if len(players) <= 8 else 170 if len(players) <= 16 else 146
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
                badge_width = 58
                badge_height = min(26, max(18, player_card_height - 8))
                badge_y = card_rect.y + max(4, (player_card_height - badge_height) // 2)
                badge_rect = pygame.Rect(card_rect.right - badge_width - 8, badge_y, badge_width, badge_height)
                content_right = badge_rect.x - 8
            elif index == current_player:
                pygame.draw.circle(
                    canvas,
                    PALETTE["gold_dark"],
                    (card_rect.right - 12, card_rect.y + max(12, 10)),
                    5 if player_card_height >= 32 else 4,
                )

            if player_card_height >= 54 and player_card_width >= 150:
                name_font = font
                score_font = small_font
                max_text_width = max(24, content_right - (card_rect.x + 14))
                name_text = truncate_text(name_font, player.name, max_text_width)
                score_text = truncate_text(score_font, f"{player.score} diem", max_text_width)
                render_text(canvas, name_font, name_text, (card_rect.x + 14, card_rect.y + 7), PALETTE["text"])
                render_text(canvas, score_font, score_text, (card_rect.x + 14, card_rect.y + 30), PALETTE["muted"])
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

            status_tokens = build_status_tokens(player)
            if status_tokens and player_card_height >= 34:
                token_x = card_rect.x + 12
                token_y = card_rect.bottom - 20 if player_card_height >= 54 else card_rect.y + 6
                for label, token_color in status_tokens[:3]:
                    token_rect = pygame.Rect(token_x, token_y, 28, 16)
                    draw_panel(canvas, token_rect, fill_color=token_color, border_color=PALETTE["panel_dark"], radius=8, shadow=False)
                    token_text = tiny_font.render(label, True, PALETTE["text"])
                    canvas.blit(token_text, (token_rect.centerx - token_text.get_width() // 2, token_rect.centery - token_text.get_height() // 2))
                    token_x += 32

            if badge_rect is not None:
                draw_button(
                    canvas,
                    tiny_font if badge_rect.height < 24 else small_font,
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
        stats_y = info_rect.y + 48
        stats_gap = 23 if info_panel_height >= 170 else 19
        selected_name = players[current_player].name if current_player is not None else "Chua chon"
        render_text(canvas, small_font, f"Kieu luot: {TURN_MODE_LABELS[turn_mode]}", (info_rect.x + 18, stats_y), PALETTE["muted"])
        if turn_mode == MANUAL_TURN_MODE:
            render_text(canvas, small_font, f"Dang chon: {selected_name}", (info_rect.x + 18, stats_y + stats_gap), PALETTE["muted"])
        else:
            render_text(canvas, small_font, f"Dang den luot: {selected_name}", (info_rect.x + 18, stats_y + stats_gap), PALETTE["muted"])
            render_text(
                canvas,
                small_font,
                f"Chieu luot: {get_turn_direction_label(game_state['turn_direction'])}",
                (info_rect.x + 18, stats_y + stats_gap * 2),
                PALETTE["muted"],
            )
        status_owner = players[current_player] if current_player is not None else None
        status_text = "Trang thai: Chua co"
        if status_owner is not None:
            parts = []
            if status_owner.shields:
                parts.append(f"La chan x{status_owner.shields}")
            if status_owner.bonus_turns:
                parts.append(f"Them luot x{status_owner.bonus_turns}")
            if status_owner.skip_turns:
                parts.append(f"Mat luot x{status_owner.skip_turns}")
            if parts:
                status_text = "Trang thai: " + " | ".join(parts)
        status_line_y = stats_y + stats_gap * (3 if turn_mode == SEQUENTIAL_TURN_MODE else 2)
        render_text(canvas, small_font, f"Con lai: {remaining_boxes} | Da mo: {len(opened)}", (info_rect.x + 18, status_line_y), PALETTE["muted"])
        render_text(canvas, small_font, status_text, (info_rect.x + 18, status_line_y + stats_gap), PALETTE["muted"])
        if waiting_effect_input:
            helper_text = "Nhan 1 neu thang, 2 neu thua."
        elif turn_mode == MANUAL_TURN_MODE and current_player is None:
            helper_text = "Click vao nguoi choi ben trai truoc khi mo o."
        elif turn_mode == MANUAL_TURN_MODE:
            helper_text = "Ban o se mo cho nguoi dang duoc chon."
        else:
            helper_text = "Chon o bat ky de kich hoat hieu ung."
        render_text(canvas, small_font, helper_text, (info_rect.x + 18, info_rect.bottom - 28), PALETTE["muted"])

        render_text(canvas, title_font, "Ban o", (board_rect.x + 26, board_rect.y + 18), PALETTE["text"])
        render_text(canvas, small_font, "Mo o de kich hoat hieu ung va tranh bi dao diem ngoan muc.", (board_rect.x + 28, board_rect.y + 58), PALETTE["muted"])

        progress_track = pygame.Rect(board_rect.x + 28, board_rect.y + 84, board_rect.width - 256, 16)
        progress_fill = pygame.Rect(progress_track.x, progress_track.y, int(progress_track.width * (len(opened) / max(1, len(boxes)))), progress_track.height)
        pygame.draw.rect(canvas, (221, 212, 192), progress_track, border_radius=10)
        if progress_fill.width > 0:
            pygame.draw.rect(canvas, PALETTE["gold"], progress_fill, border_radius=10)
        pygame.draw.rect(canvas, PALETTE["panel_dark"], progress_track, 1, border_radius=10)
        progress_text = f"Tien do {len(opened)}/{len(boxes)}"
        render_text(canvas, tiny_font, progress_text, (progress_track.right + 14, progress_track.y - 1), PALETTE["muted"])

        grid_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 114, board_rect.width - 48, board_rect.height - 192)
        draw_panel(canvas, grid_rect, fill_color=(232, 223, 207), border_color=PALETTE["panel_dark"], radius=24, shadow=False)

        cols = 10
        box_size = 72
        gap = 12
        rows = max(1, math.ceil(len(boxes) / cols))
        board_total_width = cols * box_size + (cols - 1) * gap
        board_total_height = rows * box_size + (rows - 1) * gap
        start_x = grid_rect.x + max(18, (grid_rect.width - board_total_width) // 2)
        start_y = grid_rect.y + max(18, (grid_rect.height - board_total_height) // 2)

        board_locked = turn_mode == MANUAL_TURN_MODE and current_player is None and not waiting_effect_input
        hovered_index = None
        for index, num in enumerate(boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            if rect.collidepoint(canvas_mouse) and num not in opened and not waiting_effect_input and not board_locked:
                hovered_index = index

        for index, num in enumerate(boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            draw_rect = rect

            if num in opened:
                box_meta = box_effects.get(num, {})
                effect_id = box_meta.get("effect_id")
                opened_at = box_meta.get("opened_at", 0)
                accent_color, fill_color = get_effect_palette(effect_id)
                age = tick - opened_at
                pulse = max(0.0, 1.0 - age / 520)
                if pulse > 0:
                    draw_glow(canvas, rect.center, accent_color, int(42 + pulse * 22), int(18 + pulse * 16))
                    inflate = int(10 * pulse)
                    draw_rect = rect.inflate(inflate, inflate)
                border_color = accent_color
                text_color = PALETTE["text"]
            else:
                if board_locked:
                    fill_color = (216, 211, 203)
                    border_color = (152, 147, 160)
                    text_color = PALETTE["muted"]
                else:
                    fill_color = (223, 231, 249)
                    border_color = PALETTE["azure_dark"]
                    text_color = PALETTE["text"]

            if hovered_index == index:
                fill_color = (244, 230, 186)
                border_color = PALETTE["gold_dark"]
                draw_glow(canvas, rect.center, PALETTE["gold"], 52, 24)

            draw_panel(canvas, draw_rect, fill_color=fill_color, border_color=border_color, radius=18, shadow=False)
            num_text = font.render(str(num), True, text_color)
            canvas.blit(num_text, (draw_rect.centerx - num_text.get_width() // 2, draw_rect.centery - num_text.get_height() // 2))

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

        if banner and banner.get("message"):
            accent_color, fill_color = get_effect_palette(banner.get("effect_id"), banner.get("message", ""))
            banner_rect = pygame.Rect(board_rect.x + 26, board_rect.bottom - 64, board_rect.width - 236, 40)
            age = tick - banner.get("created_at", tick)
            pulse = max(0.0, 1.0 - min(age, 1800) / 1800)
            if pulse > 0:
                draw_glow(canvas, banner_rect.center, accent_color, 58, int(10 + pulse * 12))
            draw_panel(canvas, banner_rect, fill_color=fill_color, border_color=accent_color, radius=18, shadow=False)
            text = small_font.render(truncate_text(small_font, banner["message"], banner_rect.width - 30), True, PALETTE["text"])
            canvas.blit(text, (banner_rect.x + 14, banner_rect.centery - text.get_height() // 2))

        scaled_canvas = pygame.transform.smoothscale(canvas, screen.get_size())
        screen.blit(scaled_canvas, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = (int(event.pos[0] * scale_x), int(event.pos[1] * scale_y))

                if quit_rect.collidepoint(pos):
                    save_game_history(players)
                    show_final_result(screen, title_font, font, players)
                    return

                if turn_mode == MANUAL_TURN_MODE and not waiting_effect_input:
                    selected_player = False
                    for index, card_rect in player_hitboxes:
                        if card_rect.collidepoint(pos):
                            skip_message = consume_pending_skip(players[index])
                            if skip_message:
                                current_player = None if current_player == index else current_player
                                banner = set_banner(skip_message, "reverse")
                            else:
                                current_player = index
                            selected_player = True
                            break
                    if selected_player:
                        continue

                if waiting_effect_input:
                    continue

                if turn_mode == MANUAL_TURN_MODE and current_player is None:
                    banner = set_banner("Hay chon nguoi choi truoc khi mo o.", "shield")
                    continue

                active_player = players[current_player]
                if active_player.skip_turns > 0:
                    banner = set_banner(consume_pending_skip(active_player), "reverse")
                    if turn_mode == SEQUENTIAL_TURN_MODE:
                        current_player, skipped_names = resolve_next_player(
                            current_player,
                            players,
                            turn_mode,
                            game_state["turn_direction"],
                        )
                        if skipped_names:
                            banner = set_banner(append_skip_notice(banner["message"], skipped_names), "reverse")
                    continue

                for index, num in enumerate(boxes):
                    x = start_x + (index % cols) * (box_size + gap)
                    y = start_y + (index // cols) * (box_size + gap)
                    rect = pygame.Rect(x, y, box_size, box_size)
                    if rect.collidepoint(pos) and num not in opened:
                        opened.add(num)
                        active_player.record_turn()
                        active_player.record_box_opened()
                        effect_id = get_random_effect(dist_mode, custom_weights)
                        box_effects[num] = {"effect_id": effect_id, "opened_at": tick}

                        if effect_id == "rps":
                            play_effect("rps")
                            banner = set_banner(
                                f"{active_player.name} mo o {num} - Keo bua bao! Nhan 1 de thang, 2 de thua.",
                                "rps",
                            )
                            effect_to_resolve = {"player_index": current_player}
                            waiting_effect_input = True
                        else:
                            message = apply_effect(effect_id, active_player, players, game_state)
                            current_player, skipped_names = resolve_next_player(
                                current_player,
                                players,
                                turn_mode,
                                game_state["turn_direction"],
                            )
                            banner = set_banner(
                                append_skip_notice(f"{active_player.name} mo o {num} - {message}", skipped_names),
                                effect_id,
                            )
                        break

            elif event.type == pygame.KEYDOWN and waiting_effect_input:
                player_index = effect_to_resolve["player_index"]
                effect_player = players[player_index]
                if event.key == pygame.K_1:
                    effect_player.add_score(10)
                    current_player, skipped_names = resolve_next_player(
                        player_index,
                        players,
                        turn_mode,
                        game_state["turn_direction"],
                    )
                    banner = set_banner(
                        append_skip_notice(f"{effect_player.name} thang Keo bua bao! +10 diem.", skipped_names),
                        "rps",
                    )
                    waiting_effect_input = False
                    effect_to_resolve = None
                elif event.key == pygame.K_2:
                    current_player, skipped_names = resolve_next_player(
                        player_index,
                        players,
                        turn_mode,
                        game_state["turn_direction"],
                    )
                    banner = set_banner(
                        append_skip_notice(f"{effect_player.name} thua Keo bua bao.", skipped_names),
                        "rps",
                    )
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
    animation_start = pygame.time.get_ticks()

    while waiting:
        tick = pygame.time.get_ticks()
        reveal_progress = min(1.0, (tick - animation_start) / 900)
        draw_background(screen, tick)

        panel_rect = pygame.Rect(100, 70, screen.get_width() - 200, screen.get_height() - 140)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        render_text(screen, title_font, "Ket qua cuoi cung", (panel_rect.x + 36, panel_rect.y + 24), PALETTE["text"])

        winner = players[0]
        winner_text = f"Nguoi thang: {winner.name} - {winner.score} diem"
        render_text(screen, small_font, winner_text, (panel_rect.x + 38, panel_rect.y + 70), PALETTE["muted"])

        stat_cards = get_stat_cards(players)
        stat_top = panel_rect.y + 110
        stat_gap = 18
        stat_width = (panel_rect.width - 76 - stat_gap * 3) // 4
        for index, (title, name, detail) in enumerate(stat_cards):
            card_rect = pygame.Rect(panel_rect.x + 38 + index * (stat_width + stat_gap), stat_top, stat_width, 88)
            accent = [PALETTE["gold"], PALETTE["azure"], PALETTE["mint"], PALETTE["crimson"]][index % 4]
            fill = {
                PALETTE["gold"]: (247, 239, 212),
                PALETTE["azure"]: (220, 230, 245),
                PALETTE["mint"]: (221, 236, 228),
                PALETTE["crimson"]: (243, 223, 226),
            }[accent]
            draw_panel(screen, card_rect, fill_color=fill, border_color=accent, radius=20, shadow=False)
            render_text(screen, tiny_font, title, (card_rect.x + 14, card_rect.y + 12), PALETTE["muted"])
            render_text(screen, small_font, truncate_text(small_font, name, card_rect.width - 28), (card_rect.x + 14, card_rect.y + 34), PALETTE["text"])
            render_text(screen, tiny_font, detail, (card_rect.x + 14, card_rect.y + 60), PALETTE["text"])

        chart_rect = pygame.Rect(panel_rect.x + 38, stat_top + 110, panel_rect.width - 76, panel_rect.height - 250)
        draw_panel(screen, chart_rect, fill_color=(240, 232, 214), border_color=PALETTE["panel_dark"], radius=24, shadow=False)

        label_width = min(220, max(140, chart_rect.width // 4))
        score_width = 96
        bar_left = chart_rect.x + label_width + 28
        bar_right = chart_rect.right - score_width - 20
        bar_width = max(140, bar_right - bar_left)
        min_score = min(player.score for player in players)
        score_offset = -min(0, min_score)
        max_score = max(1, max(player.score + score_offset for player in players))
        row_gap = 12 if len(players) <= 8 else 8 if len(players) <= 12 else 4
        row_height = max(18, min(54, (chart_rect.height - 34 - row_gap * max(0, len(players) - 1)) // max(1, len(players))))
        colors = [PALETTE["gold"], PALETTE["azure"], PALETTE["mint"]]

        for index, player in enumerate(players):
            row_y = chart_rect.y + 18 + index * (row_height + row_gap)
            row_rect = pygame.Rect(chart_rect.x + 16, row_y, chart_rect.width - 32, row_height)
            track_rect = pygame.Rect(bar_left, row_y + max(4, row_height // 5), bar_width, max(10, row_height - 10))
            normalized_score = player.score + score_offset
            raw_width = max(14, int(track_rect.width * (normalized_score / max_score))) if normalized_score > 0 else 0
            fill_width = int(raw_width * reveal_progress)
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

        ok_rect = pygame.Rect(screen.get_width() // 2 - 90, panel_rect.bottom - 70, 180, 46)
        draw_button(
            screen,
            font,
            ok_rect,
            "OK - Thoat",
            PALETTE["mint"],
            PALETTE["mint_dark"],
            ok_rect.collidepoint(pygame.mouse.get_pos()),
            PALETTE["text"],
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ok_rect.collidepoint(event.pos):
                waiting = False
