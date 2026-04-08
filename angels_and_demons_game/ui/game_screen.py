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
from ui.theme import draw_cloud
from ui.theme import draw_glow
from ui.theme import draw_heart
from ui.theme import draw_mascot
from ui.theme import draw_panel
from ui.theme import draw_sparkle
from ui.theme import draw_star


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


def wrap_text_lines(font, text, max_width, max_lines=2):
    if max_width <= 0:
        return []

    words = str(text or "").split()
    if not words:
        return []

    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
            continue

        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines - 1:
            break

    if len(lines) < max_lines and current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if lines:
        remaining_words = words[len(" ".join(lines).split()):]
        if remaining_words:
            lines[-1] = truncate_text(font, f"{lines[-1]} {' '.join(remaining_words)}", max_width)
        elif font.size(lines[-1])[0] > max_width:
            lines[-1] = truncate_text(font, lines[-1], max_width)
    return lines


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


def ease_out_back(progress):
    progress = max(0.0, min(1.0, progress))
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(progress - 1, 3) + c1 * pow(progress - 1, 2)


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


def draw_info_card(surface, label_font, value_font, rect, label, value, fill_color, border_color):
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=18, shadow=False)
    label_surface = label_font.render(label, True, PALETTE["muted"])
    value_text = truncate_text(value_font, value, rect.width - 20)
    value_surface = value_font.render(value_text, True, PALETTE["text"])
    surface.blit(label_surface, (rect.x + 10, rect.y + 6))
    surface.blit(value_surface, (rect.x + 10, rect.bottom - value_surface.get_height() - 7))


def draw_info_helper(surface, font, rect, text):
    draw_panel(surface, rect, fill_color=(247, 241, 233), border_color=PALETTE["lilac"], radius=16, shadow=False)
    lines = []
    words = text.split()
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= rect.width - 20:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for index, line in enumerate(lines[:2]):
        line_surface = font.render(line, True, PALETTE["muted"])
        surface.blit(line_surface, (rect.x + 10, rect.y + 8 + index * 15))


def get_effect_symbol(effect_id):
    effect_definition = get_effect_definition(effect_id) if effect_id else None
    operation = str(effect_definition.get("operation", "")) if effect_definition else ""
    effect_id = str(effect_id or "")

    builtin_symbols = {
        "angel": "A",
        "devil": "D",
        "gun": "!",
        "lucky": "+",
        "lottery": "$",
        "rps": "KB",
        "double": "x2",
        "half": "1/2",
    }
    if effect_id in builtin_symbols:
        return builtin_symbols[effect_id]

    custom_symbols = {
        "add_self": "+",
        "subtract_self": "-",
        "multiply_self": "x",
        "divide_self": "/",
        "steal_random": "!",
        "give_random": ">",
        "swap_random": "<>",
        "others_gain": "++",
        "others_lose": "--",
        "all_gain": "ALL+",
        "all_lose": "ALL-",
        "bonus_turn": "T+",
        "shield_self": "S",
        "skip_random": "Z",
        "reverse_order": "~",
    }
    return custom_symbols.get(operation, "?")


def get_effect_title(effect_id):
    effect_definition = get_effect_definition(effect_id) if effect_id else None
    if effect_definition:
        return str(effect_definition.get("label") or effect_definition.get("name") or effect_id)
    return "Bat ngo"


def get_effect_spotlight_variant(effect_id=None, message=""):
    effect_id = str(effect_id or "")
    effect_definition = get_effect_definition(effect_id) if effect_id else None
    operation = str(effect_definition.get("operation", "")) if effect_definition else ""
    lowered = str(message or "").lower()

    positive_ids = {"angel", "lucky", "lottery", "double"}
    negative_ids = {"devil", "gun", "half"}
    positive_operations = {"add_self", "multiply_self", "others_gain", "all_gain", "bonus_turn", "shield_self"}
    negative_operations = {"subtract_self", "divide_self", "steal_random", "give_random", "swap_random", "others_lose", "all_lose", "skip_random", "reverse_order"}

    if effect_id in positive_ids or operation in positive_operations or any(token in lowered for token in ("thien", "may", "la chan", "them luot", "trung so", "nhan doi")):
        return "angel"
    if effect_id in negative_ids or operation in negative_operations or any(token in lowered for token in ("ac", "cuop", "mat luot", "chia doi", "sung", "doi diem", "dao chieu")):
        return "demon"
    return "angel" if effect_id in {"rps"} else "demon"


def draw_effect_sticker(surface, rect, font, effect_id):
    accent_color, fill_color = get_effect_palette(effect_id)
    sticker_rect = pygame.Rect(rect.right - 28, rect.y + 6, 22, 22)
    draw_panel(surface, sticker_rect, fill_color=fill_color, border_color=accent_color, radius=11, shadow=False)
    symbol = get_effect_symbol(effect_id)
    text_surface = font.render(symbol, True, PALETTE["text"])
    surface.blit(text_surface, (sticker_rect.centerx - text_surface.get_width() // 2, sticker_rect.centery - text_surface.get_height() // 2))


def set_spotlight(effect_id, message, player_name=None, box_number=None):
    return {
        "effect_id": effect_id,
        "message": str(message or ""),
        "player_name": str(player_name or ""),
        "box_number": box_number,
        "title": get_effect_title(effect_id),
        "created_at": pygame.time.get_ticks(),
    }


def draw_effect_spotlight(surface, board_rect, title_font, subtitle_font, body_font, symbol_font, spotlight, tick):
    if not spotlight or not spotlight.get("message"):
        return False

    duration = 1700
    age = tick - spotlight.get("created_at", tick)
    if age >= duration:
        return False

    appear = min(1.0, age / 220)
    fade = 1.0 - max(0.0, age - (duration - 260)) / 260
    opacity = max(0.0, min(1.0, appear * fade))
    pop = ease_out_back(appear)
    accent_color, fill_color = get_effect_palette(spotlight.get("effect_id"), spotlight.get("message", ""))
    mascot_variant = get_effect_spotlight_variant(spotlight.get("effect_id"), spotlight.get("message", ""))

    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((255, 250, 246, int(44 * opacity)))
    surface.blit(overlay, (0, 0))

    base_width = min(board_rect.width - 120, 620)
    base_height = 196
    scale = 0.86 + 0.14 * pop
    card_width = max(360, int(base_width * scale))
    card_height = int(base_height * scale)

    card_surface = pygame.Surface((card_width + 140, card_height + 120), pygame.SRCALPHA)
    card_rect = pygame.Rect(0, 0, card_width, card_height)
    card_rect.center = (card_surface.get_width() // 2, card_surface.get_height() // 2 - int((1.0 - appear) * 18))

    draw_glow(card_surface, card_rect.center, accent_color, int(84 + 22 * pop), int(34 * opacity))
    draw_panel(card_surface, card_rect, fill_color=fill_color, border_color=accent_color, radius=28, shadow=False)
    draw_cloud(card_surface, (card_rect.x + 96, card_rect.y + 44), 0.45, (255, 248, 244))
    draw_star(card_surface, (card_rect.right - 54, card_rect.y + 36), 10, PALETTE["gold"])
    draw_heart(card_surface, (card_rect.right - 92, card_rect.bottom - 34), 11, (255, 218, 224), PALETTE["crimson_dark"])
    draw_sparkle(card_surface, (card_rect.x + 36, card_rect.bottom - 36), 8, accent_color)

    badge_size = max(88, int(102 * scale))
    badge_rect = pygame.Rect(card_rect.x + 24, card_rect.y + 24, badge_size, badge_size)
    draw_glow(card_surface, badge_rect.center, accent_color, int(44 + 8 * pop), int(18 * opacity))
    draw_panel(card_surface, badge_rect, fill_color=(255, 251, 246), border_color=accent_color, radius=24, shadow=False)
    symbol_text = symbol_font.render(get_effect_symbol(spotlight.get("effect_id")), True, PALETTE["text"])
    card_surface.blit(symbol_text, (badge_rect.centerx - symbol_text.get_width() // 2, badge_rect.centery - symbol_text.get_height() // 2))

    title_x = badge_rect.right + 24
    title_width = max(120, card_rect.right - title_x - 128)
    title_surface = title_font.render(truncate_text(title_font, spotlight.get("title", "Bat ngo"), title_width), True, PALETTE["text"])
    card_surface.blit(title_surface, (title_x, card_rect.y + 26))

    if spotlight.get("player_name") and spotlight.get("box_number") is not None:
        subtitle_text = f"{spotlight['player_name']} mo o {spotlight['box_number']}"
    elif spotlight.get("player_name"):
        subtitle_text = spotlight["player_name"]
    else:
        subtitle_text = "Hieu ung vua duoc kich hoat"
    subtitle_surface = subtitle_font.render(truncate_text(subtitle_font, subtitle_text, title_width), True, PALETTE["muted"])
    card_surface.blit(subtitle_surface, (title_x, card_rect.y + 64))

    message_lines = wrap_text_lines(body_font, spotlight.get("message", ""), title_width, max_lines=3)
    for line_index, line in enumerate(message_lines):
        line_surface = body_font.render(line, True, PALETTE["text"])
        card_surface.blit(line_surface, (title_x, card_rect.y + 98 + line_index * 24))

    draw_mascot(card_surface, (card_rect.right - 72, card_rect.y + 82), mascot_variant, tick, 0.5)

    card_surface.set_alpha(int(255 * opacity))
    surface.blit(card_surface, (board_rect.centerx - card_surface.get_width() // 2, board_rect.centery - card_surface.get_height() // 2 - 12))
    return True


def run_game_ui(players, num_boxes, dist_mode, custom_weights=None, turn_mode=SEQUENTIAL_TURN_MODE):
    pygame.init()
    screen = pygame.display.set_mode((1480, 860), pygame.RESIZABLE)
    pygame.display.set_caption("Angels and Demons - Game")

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    font = pygame.font.Font(font_path, 20)
    small_font = pygame.font.Font(font_path, 16)
    tiny_font = pygame.font.Font(font_path, 13)
    ui_font = pygame.font.SysFont("Segoe UI", 19, bold=True)
    ui_small_font = pygame.font.SysFont("Segoe UI", 15)
    ui_tiny_font = pygame.font.SysFont("Segoe UI", 13)
    spotlight_title_font = pygame.font.SysFont("Segoe UI", 31, bold=True)
    spotlight_subtitle_font = pygame.font.SysFont("Segoe UI", 17, bold=True)
    spotlight_symbol_font = pygame.font.SysFont("Segoe UI", 42, bold=True)

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
    spotlight = None
    waiting_effect_input = False
    effect_to_resolve = None
    reveal_lock_until = 0
    flip_duration = 320

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
        draw_cloud(canvas, (sidebar_rect.x + 96, sidebar_rect.y + 42), 0.52, (255, 248, 243))
        draw_cloud(canvas, (board_rect.right - 116, board_rect.y + 42), 0.62, (255, 247, 242))
        draw_mascot(canvas, (sidebar_rect.right - 60, sidebar_rect.y + 74), "angel", tick, 0.42)
        draw_mascot(canvas, (sidebar_rect.x + 54, sidebar_rect.bottom - 72), "demon", tick + 90, 0.34)
        draw_mascot(canvas, (board_rect.x + 72, board_rect.bottom - 82), "angel", tick + 40, 0.34)
        draw_mascot(canvas, (board_rect.right - 74, board_rect.bottom - 92), "demon", tick + 170, 0.4)
        draw_heart(canvas, (sidebar_rect.right - 32, sidebar_rect.y + 116), 11, (255, 219, 225), PALETTE["crimson_dark"])
        draw_heart(canvas, (board_rect.x + 40, board_rect.y + 118), 10, (226, 222, 255), PALETTE["lilac"])
        draw_star(canvas, (board_rect.right - 52, board_rect.y + 104), 8, PALETTE["gold"])
        draw_star(canvas, (sidebar_rect.x + 24, sidebar_rect.bottom - 108), 7, PALETTE["lilac"])

        render_text(canvas, title_font, "Bang diem", (sidebar_rect.x + 28, sidebar_rect.y + 20), PALETTE["text"])

        info_panel_height = 214
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
                score_font = ui_small_font
                max_text_width = max(24, content_right - (card_rect.x + 14))
                name_text = truncate_text(name_font, player.name, max_text_width)
                score_text = truncate_text(score_font, f"{player.score} diem", max_text_width)
                render_text(canvas, name_font, name_text, (card_rect.x + 14, card_rect.y + 7), PALETTE["text"])
                render_text(canvas, score_font, score_text, (card_rect.x + 14, card_rect.y + 32), PALETTE["muted"])
            else:
                name_font = ui_small_font if player_card_height >= 30 else ui_tiny_font
                score_font = ui_tiny_font
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
                    token_text = ui_tiny_font.render(label, True, PALETTE["text"])
                    canvas.blit(token_text, (token_rect.centerx - token_text.get_width() // 2, token_rect.centery - token_text.get_height() // 2))
                    token_x += 32

            if badge_rect is not None:
                draw_button(
                    canvas,
                    ui_tiny_font if badge_rect.height < 24 else ui_small_font,
                    badge_rect,
                    "TURN",
                    PALETTE["gold"],
                    PALETTE["gold_dark"],
                    badge_rect.collidepoint(canvas_mouse),
                    PALETTE["text"],
                )

        info_rect = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.bottom - info_panel_height - 20, sidebar_rect.width - 40, info_panel_height)
        draw_panel(canvas, info_rect, fill_color=(233, 224, 209), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        render_text(canvas, font, "Thong tin", (info_rect.x + 18, info_rect.y + 14), PALETTE["text"])
        draw_star(canvas, (info_rect.right - 18, info_rect.y + 22), 7, PALETTE["gold"])
        draw_heart(canvas, (info_rect.right - 42, info_rect.y + 22), 10, (255, 219, 225), PALETTE["crimson_dark"])
        remaining_boxes = len(boxes) - len(opened)
        selected_name = players[current_player].name if current_player is not None else "Chua chon"
        status_owner = players[current_player] if current_player is not None else None

        status_value = "San sang"
        if status_owner is not None:
            parts = []
            if status_owner.shields:
                parts.append(f"La chan x{status_owner.shields}")
            if status_owner.bonus_turns:
                parts.append(f"Them luot x{status_owner.bonus_turns}")
            if status_owner.skip_turns:
                parts.append(f"Mat luot x{status_owner.skip_turns}")
            if parts:
                status_value = " | ".join(parts)

        info_cards = [
            ("Kieu luot", TURN_MODE_LABELS[turn_mode]),
            ("Nguoi choi", selected_name),
            ("Con lai", f"{remaining_boxes} o"),
            ("Da mo", f"{len(opened)} o"),
        ]
        if turn_mode == SEQUENTIAL_TURN_MODE:
            info_cards[1] = ("Den luot", selected_name)
            info_cards[3] = ("Chieu", get_turn_direction_label(game_state["turn_direction"]))

        card_gap = 10
        card_width = (info_rect.width - 26 - card_gap) // 2
        card_height = 50
        card_top = info_rect.y + 42
        for index, (label, value) in enumerate(info_cards):
            card_x = info_rect.x + 10 + (index % 2) * (card_width + card_gap)
            card_y = card_top + (index // 2) * (card_height + 8)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            fill = (246, 239, 229) if index % 2 == 0 else (242, 233, 224)
            draw_info_card(canvas, ui_tiny_font, ui_font, card_rect, label, value, fill, PALETTE["panel_dark"])

        status_rect = pygame.Rect(info_rect.x + 10, info_rect.y + 156, info_rect.width - 20, 28)
        draw_panel(canvas, status_rect, fill_color=(245, 236, 231), border_color=PALETTE["mint_dark"], radius=14, shadow=False)
        status_label_surface = ui_tiny_font.render("Trang thai", True, PALETTE["muted"])
        status_value_surface = ui_tiny_font.render(truncate_text(ui_tiny_font, status_value, status_rect.width - 112), True, PALETTE["text"])
        canvas.blit(status_label_surface, (status_rect.x + 10, status_rect.y + 5))
        canvas.blit(status_value_surface, (status_rect.x + 88, status_rect.y + 5))
        if waiting_effect_input:
            helper_text = "Nhan 1 neu thang, 2 neu thua."
        elif turn_mode == MANUAL_TURN_MODE and current_player is None:
            helper_text = "Click vao nguoi choi ben trai truoc khi mo o."
        elif turn_mode == MANUAL_TURN_MODE:
            helper_text = "Ban o se mo cho nguoi dang duoc chon."
        else:
            helper_text = "Chon o bat ky de kich hoat hieu ung."
        helper_rect = pygame.Rect(info_rect.x + 10, info_rect.bottom - 44, info_rect.width - 20, 36)
        draw_info_helper(canvas, ui_tiny_font, helper_rect, helper_text)

        render_text(canvas, title_font, "Ban o", (board_rect.x + 26, board_rect.y + 18), PALETTE["text"])
        render_text(canvas, ui_small_font, "Mo o de xem bat ngo nao dang cho va ai se duoc om diem.", (board_rect.x + 28, board_rect.y + 58), PALETTE["muted"])

        progress_track = pygame.Rect(board_rect.x + 28, board_rect.y + 84, board_rect.width - 256, 16)
        progress_fill = pygame.Rect(progress_track.x, progress_track.y, int(progress_track.width * (len(opened) / max(1, len(boxes)))), progress_track.height)
        pygame.draw.rect(canvas, (221, 212, 192), progress_track, border_radius=10)
        if progress_fill.width > 0:
            pygame.draw.rect(canvas, PALETTE["gold"], progress_fill, border_radius=10)
        pygame.draw.rect(canvas, PALETTE["panel_dark"], progress_track, 1, border_radius=10)
        progress_text = f"Tien do {len(opened)}/{len(boxes)}"
        render_text(canvas, ui_tiny_font, progress_text, (progress_track.right + 14, progress_track.y - 1), PALETTE["muted"])
        draw_star(canvas, (progress_track.x - 12, progress_track.centery), 8, PALETTE["gold"])
        draw_star(canvas, (progress_track.right + 102, progress_track.centery), 6, PALETTE["lilac"])
        draw_heart(canvas, (progress_track.right + 118, progress_track.centery - 1), 8, (255, 218, 224), PALETTE["crimson_dark"])

        grid_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 114, board_rect.width - 48, board_rect.height - 192)
        draw_panel(canvas, grid_rect, fill_color=(232, 223, 207), border_color=PALETTE["panel_dark"], radius=24, shadow=False)
        draw_cloud(canvas, (grid_rect.x + 84, grid_rect.y + 52), 0.42, (255, 247, 244))
        draw_cloud(canvas, (grid_rect.right - 88, grid_rect.bottom - 48), 0.45, (255, 248, 243))
        draw_heart(canvas, (grid_rect.x + 42, grid_rect.bottom - 58), 10, (255, 219, 225), PALETTE["crimson_dark"])
        draw_star(canvas, (grid_rect.right - 38, grid_rect.y + 34), 8, PALETTE["lilac"])

        cols = 10
        box_size = 72
        gap = 12
        rows = max(1, math.ceil(len(boxes) / cols))
        board_total_width = cols * box_size + (cols - 1) * gap
        board_total_height = rows * box_size + (rows - 1) * gap
        start_x = grid_rect.x + max(18, (grid_rect.width - board_total_width) // 2)
        start_y = grid_rect.y + max(18, (grid_rect.height - board_total_height) // 2)

        manual_lock = turn_mode == MANUAL_TURN_MODE and current_player is None and not waiting_effect_input
        reveal_in_progress = tick < reveal_lock_until
        board_locked = manual_lock
        interaction_locked = waiting_effect_input or manual_lock or reveal_in_progress
        hovered_index = None
        for index, num in enumerate(boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            if rect.collidepoint(canvas_mouse) and num not in opened and not interaction_locked:
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
                flip_started_at = box_meta.get("flip_started_at", opened_at)
                accent_color, fill_color = get_effect_palette(effect_id)
                age = tick - opened_at
                pulse = max(0.0, 1.0 - age / 520)
                if pulse > 0:
                    draw_glow(canvas, rect.center, accent_color, int(42 + pulse * 22), int(18 + pulse * 16))
                    inflate = int(10 * pulse)
                    draw_rect = rect.inflate(inflate, inflate)
                border_color = accent_color
                text_color = PALETTE["text"]
                flip_progress = min(1.0, max(0.0, (tick - flip_started_at) / flip_duration))
                if flip_progress < 1.0:
                    if flip_progress < 0.5:
                        reveal_phase = flip_progress / 0.5
                        scale = max(0.14, 1.0 - reveal_phase * 0.86)
                        fill_color = (223, 231, 249)
                        border_color = PALETTE["azure_dark"]
                    else:
                        reveal_phase = (flip_progress - 0.5) / 0.5
                        scale = max(0.14, 0.14 + reveal_phase * 0.86)
                        if reveal_phase > 0.2:
                            draw_glow(canvas, rect.center, accent_color, int(38 + reveal_phase * 20), int(12 + reveal_phase * 20))

                    scaled_width = max(12, int(rect.width * scale))
                    draw_rect = pygame.Rect(0, 0, scaled_width, rect.height)
                    draw_rect.center = rect.center
            else:
                idle_bob = 0 if manual_lock else int(math.sin(tick / 220 + index * 0.7) * 3)
                draw_rect = rect.move(0, idle_bob)
                if manual_lock:
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

            max_radius = max(2, min(draw_rect.width // 2 - 1, draw_rect.height // 2 - 1))
            radius = min(18, max_radius)
            draw_panel(canvas, draw_rect, fill_color=fill_color, border_color=border_color, radius=radius, shadow=False)
            if draw_rect.width >= 24:
                num_text = ui_font.render(str(num), True, text_color)
                canvas.blit(num_text, (draw_rect.centerx - num_text.get_width() // 2, draw_rect.centery - num_text.get_height() // 2))
            if num in opened and draw_rect.width >= 46:
                draw_effect_sticker(canvas, draw_rect, ui_tiny_font, box_effects.get(num, {}).get("effect_id"))

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
            slide_progress = min(1.0, age / 240)
            banner_rect = banner_rect.move(int((1.0 - slide_progress) * 40), 0)
            if pulse > 0:
                draw_glow(canvas, banner_rect.center, accent_color, 58, int(10 + pulse * 12))
            draw_panel(canvas, banner_rect, fill_color=fill_color, border_color=accent_color, radius=18, shadow=False)
            text = ui_small_font.render(truncate_text(ui_small_font, banner["message"], banner_rect.width - 30), True, PALETTE["text"])
            canvas.blit(text, (banner_rect.x + 14, banner_rect.centery - text.get_height() // 2))

        if spotlight and not draw_effect_spotlight(
            canvas,
            board_rect,
            spotlight_title_font,
            spotlight_subtitle_font,
            ui_small_font,
            spotlight_symbol_font,
            spotlight,
            tick,
        ):
            spotlight = None

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

                if reveal_in_progress:
                    continue

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
                        box_effects[num] = {
                            "effect_id": effect_id,
                            "opened_at": tick,
                            "flip_started_at": tick,
                        }
                        reveal_lock_until = tick + flip_duration

                        if effect_id == "rps":
                            play_effect("rps")
                            rps_message = f"{active_player.name} mo o {num} - Keo bua bao! Nhan 1 de thang, 2 de thua."
                            banner = set_banner(rps_message, "rps")
                            spotlight = set_spotlight("rps", rps_message, active_player.name, num)
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
                            full_message = append_skip_notice(f"{active_player.name} mo o {num} - {message}", skipped_names)
                            banner = set_banner(full_message, effect_id)
                            spotlight = set_spotlight(effect_id, full_message, active_player.name, num)
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
                    win_message = append_skip_notice(f"{effect_player.name} thang Keo bua bao! +10 diem.", skipped_names)
                    banner = set_banner(win_message, "rps")
                    spotlight = set_spotlight("rps", win_message, effect_player.name)
                    waiting_effect_input = False
                    effect_to_resolve = None
                elif event.key == pygame.K_2:
                    current_player, skipped_names = resolve_next_player(
                        player_index,
                        players,
                        turn_mode,
                        game_state["turn_direction"],
                    )
                    lose_message = append_skip_notice(f"{effect_player.name} thua Keo bua bao.", skipped_names)
                    banner = set_banner(lose_message, "rps")
                    spotlight = set_spotlight("rps", lose_message, effect_player.name)
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
