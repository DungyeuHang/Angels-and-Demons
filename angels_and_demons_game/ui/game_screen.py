import math
import os
import random
import sys

import pygame

from config import GAME_WINDOW_SIZE
from config import create_display
from constants import BOARD_LAYOUTS
from constants import MATCH_PRESETS
from constants import MODE_VARIANTS
from mechanics.effects import get_effect_definition
from mechanics.effects import get_effect_help
from mechanics.effects import get_effect_label
from mechanics.logic import build_history_metadata
from mechanics.logic import choose_bot_box
from mechanics.logic import create_game_session
from mechanics.logic import get_bot_think_delay
from mechanics.logic import get_effect_summary_rows
from mechanics.logic import handle_active_player_skip
from mechanics.logic import open_box
from mechanics.logic import resolve_rps_result
from mechanics.logic import set_selected_player
from models.history import save_game_history_entry
from models.player import Player
from models.progression import record_session_progress
from models.settings import load_settings
from models.settings import update_settings
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import TURN_MODE_LABELS
from models.turn_modes import normalize_turn_mode
from ui.audio import play_music
from ui.audio import play_sfx
from ui.audio import sync_audio_settings
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
from ui.effect_book_screen import show_effect_book_screen
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


def finalize_session_records(session):
    if session.result_saved:
        return

    _, profile_summary, unlocked_achievements = record_session_progress(session)
    session.profile_summary = profile_summary
    session.unlocked_achievements = unlocked_achievements

    metadata = build_history_metadata(session)
    metadata["unlocked_achievements"] = unlocked_achievements
    save_game_history_entry(session.players, metadata)
    session.result_saved = True

    if unlocked_achievements:
        play_sfx("achievement", volume_multiplier=0.85)


def clone_players(players):
    return [
        Player(
            player.name,
            is_bot=getattr(player, "is_bot", False),
            ai_level=getattr(player, "ai_level", "normal"),
            avatar_variant=getattr(player, "avatar_variant", None),
        )
        for player in players
    ]


def render_text(surface, font, text, pos, color):
    surface.blit(font.render(text, True, color), pos)


def get_effect_icon_key(effect_id):
    if effect_id in {"angel", "devil", "gun", "lucky", "lottery", "rps", "double", "half"}:
        return f"effect_{effect_id}"
    return None


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
    lowered = str(message or "").lower()

    if effect_id in {"angel", "lottery", "double"} or operation in {"add_self", "multiply_self", "others_gain", "all_gain"} or "thien" in lowered:
        return PALETTE["gold"], (247, 239, 212)
    if effect_id in {"devil", "half"} or operation in {"subtract_self", "divide_self", "others_lose", "all_lose"} or "ac" in lowered:
        return PALETTE["crimson"], (243, 223, 226)
    if effect_id in {"lucky"} or operation in {"bonus_turn"} or "may" in lowered or "them luot" in lowered:
        return PALETTE["mint"], (221, 236, 228)
    if effect_id in {"shield"} or operation in {"shield_self"} or "la chan" in lowered:
        return PALETTE["azure"], (224, 234, 246)
    if effect_id in {"swap"} or operation in {"steal_random", "give_random", "swap_random"} or "doi diem" in lowered or "cuop" in lowered:
        return (150, 101, 63), (240, 224, 204)
    if effect_id in {"reverse"} or operation in {"skip_random", "reverse_order"} or "mat luot" in lowered or "dao chieu" in lowered:
        return (112, 77, 122), (233, 223, 236)
    if effect_id in {"oracle"} or "tien tri" in lowered or "soi" in lowered:
        return PALETTE["lilac"], (236, 230, 246)
    if effect_id in {"rps"}:
        return (132, 119, 96), (236, 231, 220)
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
    surface.blit(label_surface, (rect.x + 10, rect.y + 7))
    value_y = rect.y + 23 + max(0, (rect.height - 23 - value_surface.get_height()) // 2)
    surface.blit(value_surface, (rect.x + 10, value_y))


def draw_info_helper(surface, font, rect, text):
    draw_panel(surface, rect, fill_color=(247, 241, 233), border_color=PALETTE["lilac"], radius=16, shadow=False)
    lines = wrap_text_lines(font, text, rect.width - 20, max_lines=2)
    total_height = len(lines) * 15
    start_y = rect.y + max(6, (rect.height - total_height) // 2)
    for index, line in enumerate(lines):
        line_surface = font.render(line, True, PALETTE["muted"])
        surface.blit(line_surface, (rect.x + 10, start_y + index * 15))


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
        "shield": "S",
        "swap": "<>",
        "reverse": "~",
        "oracle": "?",
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
    return get_effect_label(effect_id, fallback="Bat ngo")


def get_effect_spotlight_variant(effect_id=None, message=""):
    effect_id = str(effect_id or "")
    effect_definition = get_effect_definition(effect_id) if effect_id else None
    operation = str(effect_definition.get("operation", "")) if effect_definition else ""
    lowered = str(message or "").lower()

    positive_ids = {"angel", "lucky", "lottery", "double", "shield", "oracle"}
    negative_ids = {"devil", "gun", "half", "swap", "reverse"}
    positive_operations = {"add_self", "multiply_self", "others_gain", "all_gain", "bonus_turn", "shield_self"}
    negative_operations = {"subtract_self", "divide_self", "steal_random", "give_random", "swap_random", "others_lose", "all_lose", "skip_random", "reverse_order"}

    if effect_id in positive_ids or operation in positive_operations or any(token in lowered for token in ("thien", "may", "la chan", "them luot", "trung so", "nhan doi", "tien tri")):
        return "angel"
    if effect_id in negative_ids or operation in negative_operations or any(token in lowered for token in ("ac", "cuop", "mat luot", "chia doi", "sung", "doi diem", "dao chieu")):
        return "demon"
    return "angel" if effect_id in {"rps"} else "demon"


def draw_effect_sticker(surface, rect, font, effect_id, compact=False):
    accent_color, fill_color = get_effect_palette(effect_id)
    sticker_size = 18 if compact else 22
    sticker_rect = pygame.Rect(rect.right - sticker_size - 6, rect.y + 6, sticker_size, sticker_size)
    draw_panel(surface, sticker_rect, fill_color=fill_color, border_color=accent_color, radius=sticker_size // 2, shadow=False)
    icon_key = get_effect_icon_key(str(effect_id))
    icon_size = 14 if compact else 18
    icon_surface = get_surface(icon_key, (icon_size, icon_size)) if icon_key else None
    if icon_surface is not None:
        surface.blit(icon_surface, (sticker_rect.centerx - icon_surface.get_width() // 2, sticker_rect.centery - icon_surface.get_height() // 2))
    else:
        symbol = get_effect_symbol(effect_id)
        text_surface = font.render(symbol, True, PALETTE["text"])
        surface.blit(text_surface, (sticker_rect.centerx - text_surface.get_width() // 2, sticker_rect.centery - text_surface.get_height() // 2))


def draw_opened_box_effect(surface, rect, effect_id, symbol_font):
    accent_color, fill_color = get_effect_palette(effect_id)
    inset = max(10, min(16, rect.width // 5))
    inner_rect = rect.inflate(-inset * 2, -inset * 2)
    if inner_rect.width < 16 or inner_rect.height < 16:
        return

    radius = min(18, max(8, min(inner_rect.width, inner_rect.height) // 2))
    draw_panel(surface, inner_rect, fill_color=(255, 251, 246), border_color=accent_color, radius=radius, shadow=False)
    draw_glow(surface, inner_rect.center, accent_color, max(18, inner_rect.width // 2 + 8), 12)

    icon_key = get_effect_icon_key(str(effect_id))
    icon_size = max(20, min(inner_rect.width - 10, inner_rect.height - 10, 38))
    icon_surface = get_surface(icon_key, (icon_size, icon_size)) if icon_key else None
    if icon_surface is not None:
        surface.blit(icon_surface, (inner_rect.centerx - icon_surface.get_width() // 2, inner_rect.centery - icon_surface.get_height() // 2))
        return

    symbol_surface = symbol_font.render(get_effect_symbol(effect_id), True, PALETTE["text"])
    surface.blit(symbol_surface, (inner_rect.centerx - symbol_surface.get_width() // 2, inner_rect.centery - symbol_surface.get_height() // 2))


def draw_effect_spotlight(surface, board_rect, title_font, subtitle_font, body_font, symbol_font, spotlight, tick):
    if not spotlight or not spotlight.message:
        return False

    duration = 1700
    age = tick - spotlight.created_at
    if age >= duration:
        return False

    appear = min(1.0, age / 220)
    fade = 1.0 - max(0.0, age - (duration - 260)) / 260
    opacity = max(0.0, min(1.0, appear * fade))
    pop = ease_out_back(appear)
    accent_color, fill_color = get_effect_palette(spotlight.effect_id, spotlight.message)
    mascot_variant = get_effect_spotlight_variant(spotlight.effect_id, spotlight.message)

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
    symbol_text = symbol_font.render(get_effect_symbol(spotlight.effect_id), True, PALETTE["text"])
    card_surface.blit(symbol_text, (badge_rect.centerx - symbol_text.get_width() // 2, badge_rect.centery - symbol_text.get_height() // 2))

    title_x = badge_rect.right + 24
    title_width = max(120, card_rect.right - title_x - 128)
    title_surface = title_font.render(truncate_text(title_font, spotlight.title, title_width), True, PALETTE["text"])
    card_surface.blit(title_surface, (title_x, card_rect.y + 26))

    if spotlight.player_name and spotlight.box_number is not None:
        subtitle_text = f"{spotlight.player_name} mo o {spotlight.box_number}"
    elif spotlight.player_name:
        subtitle_text = spotlight.player_name
    else:
        subtitle_text = "Hieu ung vua duoc kich hoat"
    subtitle_surface = subtitle_font.render(truncate_text(subtitle_font, subtitle_text, title_width), True, PALETTE["muted"])
    card_surface.blit(subtitle_surface, (title_x, card_rect.y + 64))

    message_lines = wrap_text_lines(body_font, spotlight.message, title_width, max_lines=3)
    for line_index, line in enumerate(message_lines):
        line_surface = body_font.render(line, True, PALETTE["text"])
        card_surface.blit(line_surface, (title_x, card_rect.y + 98 + line_index * 24))

    draw_mascot(card_surface, (card_rect.right - 72, card_rect.y + 82), mascot_variant, tick, 0.5)

    card_surface.set_alpha(int(255 * opacity))
    surface.blit(card_surface, (board_rect.centerx - card_surface.get_width() // 2, board_rect.centery - card_surface.get_height() // 2 - 12))
    return True


def draw_effect_summary(surface, title_font, body_font, rect, rows):
    draw_panel(surface, rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
    header = title_font.render("Top hieu ung", True, PALETTE["muted"])
    surface.blit(header, (rect.x + 12, rect.y + 8))

    if not rows:
        empty_text = body_font.render("Chua mo o nao.", True, PALETTE["muted"])
        surface.blit(empty_text, (rect.x + 12, rect.y + 30))
        return

    chip_gap = 8
    chip_width = (rect.width - 24 - chip_gap * max(0, len(rows) - 1)) // max(1, len(rows))
    for index, (effect_id, label, count) in enumerate(rows):
        chip_rect = pygame.Rect(rect.x + 12 + index * (chip_width + chip_gap), rect.y + 28, chip_width, rect.height - 38)
        accent_color, fill_color = get_effect_palette(effect_id, label)
        draw_panel(surface, chip_rect, fill_color=fill_color, border_color=accent_color, radius=14, shadow=False)
        icon_key = get_effect_icon_key(str(effect_id))
        icon_surface = get_surface(icon_key, (18, 18)) if icon_key else None
        label_surface = title_font.render(truncate_text(title_font, label, chip_rect.width - 56), True, PALETTE["text"])
        count_surface = title_font.render(f"x{count}", True, PALETTE["muted"])
        if icon_surface is not None:
            surface.blit(icon_surface, (chip_rect.x + 8, chip_rect.centery - icon_surface.get_height() // 2))
        else:
            symbol_surface = body_font.render(get_effect_symbol(effect_id), True, PALETTE["text"])
            surface.blit(symbol_surface, (chip_rect.x + 10, chip_rect.centery - symbol_surface.get_height() // 2))
        surface.blit(label_surface, (chip_rect.x + 34, chip_rect.y + 6))
        surface.blit(count_surface, (chip_rect.x + 34, chip_rect.bottom - count_surface.get_height() - 6))


def draw_event_feed(surface, title_font, body_font, rect, recent_events):
    draw_panel(surface, rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
    header = title_font.render("Nhat ky gan day", True, PALETTE["muted"])
    surface.blit(header, (rect.x + 12, rect.y + 8))

    if not recent_events:
        empty_text = body_font.render("Su kien se hien o day sau moi lan mo o.", True, PALETTE["muted"])
        surface.blit(empty_text, (rect.x + 12, rect.y + 34))
        return

    line_y = rect.y + 34
    for event in recent_events[:2]:
        accent_color, fill_color = get_effect_palette(event.get("effect_id"), event.get("message", ""))
        bullet_rect = pygame.Rect(rect.x + 12, line_y + 1, 14, 14)
        draw_panel(surface, bullet_rect, fill_color=fill_color, border_color=accent_color, radius=7, shadow=False)
        icon_key = get_effect_icon_key(str(event.get("effect_id") or ""))
        icon_surface = get_surface(icon_key, (12, 12)) if icon_key else None
        if icon_surface is not None:
            surface.blit(icon_surface, (bullet_rect.centerx - icon_surface.get_width() // 2, bullet_rect.centery - icon_surface.get_height() // 2))
        else:
            bullet_text = title_font.render(get_effect_symbol(event.get("effect_id")), True, PALETTE["text"])
            surface.blit(bullet_text, (bullet_rect.centerx - bullet_text.get_width() // 2, bullet_rect.centery - bullet_text.get_height() // 2))
        message_text = truncate_text(body_font, event.get("message", ""), rect.width - 40)
        message_surface = body_font.render(message_text, True, PALETTE["text"])
        surface.blit(message_surface, (rect.x + 34, line_y))
        line_y += 20


def draw_help_overlay(surface, title_font, body_font, small_font):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((61, 45, 57, 170))
    surface.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(surface.get_width() // 2 - 300, surface.get_height() // 2 - 190, 600, 380)
    draw_panel(surface, panel_rect, fill_color=(250, 243, 228), border_color=PALETTE["gold_dark"], radius=30)
    render_text(surface, title_font, "Huong dan nhanh", (panel_rect.x + 28, panel_rect.y + 24), PALETTE["text"])
    emblem_surface = get_surface("brand_emblem", (58, 58))
    if emblem_surface is not None:
        surface.blit(emblem_surface, (panel_rect.right - 88, panel_rect.y + 14))

    lines = [
        "Click vao o de mo hieu ung moi.",
        "Manual mode: click ten nguoi choi ben trai de doi nguoi mo o.",
        "Gap Keo bua bao: nhan 1 de thang, 2 de thua.",
        "Bot se tu mo o, ke ca khi gap Keo bua bao.",
        "Nhan H hoac Esc de dong bang nay. Nhan M de mute nhanh, B de mo So tay.",
        "Che do thuong chi co 8 effect mac dinh.",
        "Che do custom co them: La chan, Doi menh, Dao chieu, Tien tri.",
        "Rê chuot vao o da mo hoac o duoc soi de xem tooltip nhanh.",
    ]

    line_y = panel_rect.y + 78
    for line in lines:
        wrapped = wrap_text_lines(body_font, line, panel_rect.width - 56, max_lines=2)
        for text_line in wrapped:
            text_surface = body_font.render(text_line, True, PALETTE["text"])
            surface.blit(text_surface, (panel_rect.x + 30, line_y))
            line_y += 20
        line_y += 4

    footer_rect = pygame.Rect(panel_rect.x + 28, panel_rect.bottom - 62, panel_rect.width - 56, 34)
    draw_info_helper(surface, small_font, footer_rect, "Tip: su dung nhat ky gan day de theo doi combo, lat o va cac effect chien thuat.")


def draw_header_chip(surface, font, rect, text, fill_color, border_color, text_color=None):
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)
    text_surface = font.render(truncate_text(font, text, rect.width - 18), True, text_color or PALETTE["text"])
    surface.blit(text_surface, (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2))


def draw_score_popups(surface, font, player_hitboxes, session, tick):
    player_rects = {index: rect for index, rect in player_hitboxes}
    remaining_popups = []
    for popup in session.score_popups:
        age = tick - popup.created_at
        if age > 1300:
            continue
        remaining_popups.append(popup)

        progress = age / 1300
        alpha = max(0, 255 - int(progress * 255))
        lift = int(progress * 28)
        anchor_rect = player_rects.get(popup.player_index)
        if anchor_rect is None:
            continue

        color = PALETTE["mint_dark"] if popup.delta > 0 else PALETTE["crimson_dark"]
        popup_surface = font.render(popup.label or f"{popup.delta:+}", True, color)
        popup_surface.set_alpha(alpha)
        surface.blit(popup_surface, (anchor_rect.right - popup_surface.get_width() - 12, anchor_rect.y - 6 - lift))

    session.score_popups = remaining_popups


def get_mode_badge_text(session):
    mode_label = MODE_VARIANTS.get(session.mode_variant, MODE_VARIANTS["standard"])["label"]
    if session.mode_variant == "challenge" and session.challenge_title:
        return f"{mode_label}: {session.challenge_title}"
    if session.series_target_wins > 1:
        return f"{mode_label} - Round {session.round_number}"
    return mode_label


def draw_hover_tooltip(surface, title_font, body_font, effect_id, anchor_pos, max_width=300):
    if not effect_id:
        return

    title = get_effect_label(effect_id, fallback="Effect")
    body_lines = wrap_text_lines(body_font, get_effect_help(effect_id), max_width - 28, max_lines=3)
    tooltip_height = 42 + len(body_lines) * 18
    tooltip_rect = pygame.Rect(anchor_pos[0] + 18, anchor_pos[1] - tooltip_height - 18, max_width, tooltip_height)
    bounds = surface.get_rect()
    if tooltip_rect.right > bounds.right - 18:
        tooltip_rect.x = max(18, anchor_pos[0] - max_width - 18)
    if tooltip_rect.y < 18:
        tooltip_rect.y = min(bounds.bottom - tooltip_height - 18, anchor_pos[1] + 18)

    draw_glow(surface, tooltip_rect.center, PALETTE["gold"], max_width // 2, 14)
    draw_panel(surface, tooltip_rect, fill_color=(251, 245, 233), border_color=PALETTE["gold_dark"], radius=18, shadow=False)
    title_surface = title_font.render(title, True, PALETTE["text"])
    surface.blit(title_surface, (tooltip_rect.x + 14, tooltip_rect.y + 10))

    line_y = tooltip_rect.y + 34
    for line in body_lines:
        line_surface = body_font.render(line, True, PALETTE["text"])
        surface.blit(line_surface, (tooltip_rect.x + 14, line_y))
        line_y += 18


def draw_box_particles(surface, rect, effect_id, opened_at, tick, reduce_motion=False):
    if reduce_motion:
        return

    age = tick - int(opened_at or 0)
    if age < 0 or age > 700:
        return

    progress = age / 700
    alpha_strength = max(0, 1.0 - progress)
    orbit = 10 + int(progress * 16)
    accents = {
        "angel": PALETTE["gold"],
        "lucky": PALETTE["mint"],
        "lottery": PALETTE["gold_dark"],
        "double": PALETTE["azure_dark"],
        "devil": PALETTE["crimson_dark"],
        "half": PALETTE["lilac"],
        "gun": PALETTE["crimson"],
    }
    accent = accents.get(str(effect_id or ""), PALETTE["gold"])

    draw_sparkle(surface, (rect.centerx, rect.y - orbit // 2), 5, accent)
    draw_sparkle(surface, (rect.right - 10, rect.centery), 4, accent)
    if alpha_strength > 0.45:
        draw_star(surface, (rect.x + 10, rect.centery - orbit // 3), 6, accent)
    if str(effect_id or "") in {"angel", "lucky", "lottery"} and alpha_strength > 0.3:
        draw_heart(surface, (rect.centerx + orbit // 2, rect.bottom - 10), 7, (255, 220, 226), PALETTE["crimson_dark"])


def update_series_score(series_state, session):
    winner = max(session.players, key=lambda player: player.score) if session.players else None
    if winner is None:
        return None
    series_state["wins"][winner.name] = series_state["wins"].get(winner.name, 0) + 1
    if series_state["wins"][winner.name] >= series_state["target_wins"]:
        series_state["champion"] = winner.name
    return winner


def show_series_round_result(screen, fonts, session, series_state):
    title_font = fonts["title"]
    font = fonts["font"]
    small_font = fonts["small"]
    tiny_font = pygame.font.Font(font.path, 14) if hasattr(font, "path") else font
    play_music("result", force_restart=True)

    winner = max(session.players, key=lambda player: player.score) if session.players else None
    scores = sorted(series_state["wins"].items(), key=lambda item: (-item[1], item[0]))

    while True:
        draw_background(screen, pygame.time.get_ticks())
        panel_rect = pygame.Rect(160, 120, screen.get_width() - 320, screen.get_height() - 240)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=28)

        heading = f"Round {series_state['round_number']} hoan tat"
        render_text(screen, title_font, heading, (panel_rect.x + 34, panel_rect.y + 24), PALETTE["text"])
        winner_text = winner.name if winner is not None else "Khong co"
        render_text(screen, font, f"Nguoi thang van nay: {winner_text}", (panel_rect.x + 36, panel_rect.y + 74), PALETTE["muted"])

        score_rect = pygame.Rect(panel_rect.x + 34, panel_rect.y + 118, panel_rect.width - 68, 190)
        draw_panel(screen, score_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
        render_text(screen, font, "Ti so series", (score_rect.x + 18, score_rect.y + 14), PALETTE["text"])
        for index, (name, wins) in enumerate(scores):
            line_surface = small_font.render(f"{name}: {wins} van", True, PALETTE["text"])
            screen.blit(line_surface, (score_rect.x + 20, score_rect.y + 54 + index * 28))

        helper_text = tiny_font.render(f"Can {series_state['target_wins']} van thang de vo dich.", True, PALETTE["muted"])
        screen.blit(helper_text, (score_rect.x + 20, score_rect.bottom - 28))

        continue_rect = pygame.Rect(panel_rect.centerx - 200, panel_rect.bottom - 66, 180, 42)
        quit_rect = pygame.Rect(panel_rect.centerx + 20, panel_rect.bottom - 66, 180, 42)
        draw_button(screen, font, continue_rect, "Van tiep", PALETTE["mint"], PALETTE["mint_dark"], continue_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])
        draw_button(screen, font, quit_rect, "Dung series", PALETTE["crimson"], PALETTE["crimson_dark"], quit_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key in {pygame.K_RETURN, pygame.K_SPACE}:
                return "continue"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    return "continue"
                if quit_rect.collidepoint(event.pos):
                    return "quit"


def run_round(screen, canvas, canvas_size, fonts, players, num_boxes, dist_mode, custom_weights, turn_mode, session_options=None, series_state=None):
    title_font = fonts["title"]
    font = fonts["font"]
    small_font = fonts["small"]
    ui_font = fonts["ui"]
    ui_small_font = fonts["ui_small"]
    ui_tiny_font = fonts["ui_tiny"]
    spotlight_title_font = fonts["spotlight_title"]
    spotlight_subtitle_font = fonts["spotlight_subtitle"]
    spotlight_symbol_font = fonts["spotlight_symbol"]
    clock = pygame.time.Clock()
    audio_settings = sync_audio_settings()
    brand_emblem = get_surface("brand_emblem", (46, 46))
    angel_badge = get_surface("angel_badge", (28, 28))
    demon_badge = get_surface("demon_badge", (28, 28))

    session = create_game_session(clone_players(players), num_boxes, dist_mode, custom_weights, turn_mode, session_options=session_options)
    if audio_settings.get("reduce_motion", False):
        session.flip_duration = 170

    while True:
        tick = pygame.time.get_ticks()
        if not session.help_visible and tick >= session.reveal_lock_until:
            if not session.waiting_effect_input:
                handle_active_player_skip(session, tick)
            if session.waiting_effect_input and session.pending_effect is not None:
                pending_player = session.players[session.pending_effect.player_index]
                if getattr(pending_player, "is_bot", False):
                    if session.bot_action_due_at <= 0:
                        session.bot_action_due_at = tick + get_bot_think_delay(pending_player)
                    elif tick >= session.bot_action_due_at:
                        win_chance = {"easy": 0.52, "normal": 0.64, "smart": 0.74}.get(getattr(pending_player, "ai_level", "normal"), 0.64)
                        resolve_rps_result(session, random.random() < win_chance, tick)
                        session.bot_action_due_at = 0
            elif session.current_player is not None and getattr(session.players[session.current_player], "is_bot", False):
                active_bot = session.players[session.current_player]
                if session.bot_action_due_at <= 0:
                    session.bot_action_due_at = tick + get_bot_think_delay(active_bot)
                elif tick >= session.bot_action_due_at:
                    bot_choice = choose_bot_box(session, tick)
                    session.bot_action_due_at = 0
                    if bot_choice is not None:
                        play_sfx("bot_move", volume_multiplier=0.46)
                        open_box(session, bot_choice, tick)
            else:
                session.bot_action_due_at = 0

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
        if brand_emblem is not None:
            canvas.blit(brand_emblem, (sidebar_rect.right - 96, sidebar_rect.y + 14))

        info_panel_height = 360
        player_cards_top = sidebar_rect.y + 82
        players_area_bottom = sidebar_rect.bottom - info_panel_height - 24
        players_area_height = max(80, players_area_bottom - player_cards_top)
        players_area_width = sidebar_rect.width - 40
        col_gap = 10

        player_columns = 1
        layout_found = False
        for candidate_columns in (1, 2, 3):
            player_rows = max(1, math.ceil(len(session.players) / candidate_columns))
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

        player_rows = max(1, math.ceil(len(session.players) / player_columns))
        row_gap = 10 if player_rows <= 6 else 8 if player_rows <= 10 else 6
        player_card_width = (players_area_width - col_gap * (player_columns - 1)) // player_columns
        player_card_height = max(24, (players_area_height - row_gap * max(0, player_rows - 1)) // player_rows)

        player_hitboxes = []
        for index, player in enumerate(session.players):
            row = index // player_columns
            col = index % player_columns
            card_x = sidebar_rect.x + 20 + col * (player_card_width + col_gap)
            card_y = player_cards_top + row * (player_card_height + row_gap)
            card_rect = pygame.Rect(card_x, card_y, player_card_width, player_card_height)
            reaction = session.player_reactions.get(index)
            if reaction:
                delta = int(reaction.get("delta", 0))
                if delta < 0:
                    shake_offset = int(math.sin((tick - int(reaction.get("created_at", tick))) / 45) * 5)
                    card_rect = card_rect.move(shake_offset, 0)
                elif delta > 0:
                    draw_glow(canvas, card_rect.center, PALETTE["mint"], max(30, player_card_height + 10), 18)
            player_hitboxes.append((index, card_rect))

            if index == session.current_player:
                fill_color = (242, 228, 188)
                border_color = PALETTE["gold_dark"]
                draw_glow(canvas, card_rect.center, PALETTE["gold"], max(34, player_card_height + 10), 26)
            else:
                fill_color = (233, 224, 209)
                border_color = PALETTE["panel_dark"]

            draw_panel(canvas, card_rect, fill_color=fill_color, border_color=border_color, radius=20, shadow=False)

            badge_rect = None
            content_right = card_rect.right - 12
            show_turn_badge = index == session.current_player and player_card_width >= 150 and player_card_height >= 30
            if show_turn_badge:
                badge_width = 58
                badge_height = min(26, max(18, player_card_height - 8))
                badge_y = card_rect.y + max(4, (player_card_height - badge_height) // 2)
                badge_rect = pygame.Rect(card_rect.right - badge_width - 8, badge_y, badge_width, badge_height)
                content_right = badge_rect.x - 8
            elif index == session.current_player:
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
                if getattr(player, "is_bot", False):
                    token_rect = pygame.Rect(token_x, token_y, 34, 16)
                    draw_panel(canvas, token_rect, fill_color=(243, 223, 226), border_color=PALETTE["crimson_dark"], radius=8, shadow=False)
                    token_text = ui_tiny_font.render("BOT", True, PALETTE["text"])
                    canvas.blit(token_text, (token_rect.centerx - token_text.get_width() // 2, token_rect.centery - token_text.get_height() // 2))
                    token_x += 38
                for label, token_color in status_tokens[:3]:
                    token_rect = pygame.Rect(token_x, token_y, 28, 16)
                    draw_panel(canvas, token_rect, fill_color=token_color, border_color=PALETTE["panel_dark"], radius=8, shadow=False)
                    token_text = ui_tiny_font.render(label, True, PALETTE["text"])
                    canvas.blit(token_text, (token_rect.centerx - token_text.get_width() // 2, token_rect.centery - token_text.get_height() // 2))
                    token_x += 32
            elif getattr(player, "is_bot", False) and player_card_height >= 34:
                token_rect = pygame.Rect(card_rect.x + 12, card_rect.bottom - 20 if player_card_height >= 54 else card_rect.y + 6, 34, 16)
                draw_panel(canvas, token_rect, fill_color=(243, 223, 226), border_color=PALETTE["crimson_dark"], radius=8, shadow=False)
                token_text = ui_tiny_font.render("BOT", True, PALETTE["text"])
                canvas.blit(token_text, (token_rect.centerx - token_text.get_width() // 2, token_rect.centery - token_text.get_height() // 2))

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
        render_text(canvas, font, "Thong tin van", (info_rect.x + 18, info_rect.y + 14), PALETTE["text"])
        draw_star(canvas, (info_rect.right - 18, info_rect.y + 22), 7, PALETTE["gold"])
        draw_heart(canvas, (info_rect.right - 42, info_rect.y + 22), 10, (255, 219, 225), PALETTE["crimson_dark"])

        selected_name = session.players[session.current_player].name if session.current_player is not None else "Chua chon"
        status_owner = session.players[session.current_player] if session.current_player is not None else None
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
            ("Che do luot", TURN_MODE_LABELS[session.turn_mode]),
            ("Nguoi choi", selected_name),
            ("O con lai", f"{session.remaining_boxes} o"),
            ("Da lat", f"{len(session.opened)} o"),
        ]
        if session.turn_mode == SEQUENTIAL_TURN_MODE:
            info_cards[1] = ("Nguoi dang luot", selected_name)
            info_cards[3] = ("Huong luot", get_turn_direction_label(session.turn_direction))

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

        summary_rect = pygame.Rect(info_rect.x + 10, info_rect.y + 192, info_rect.width - 20, 60)
        draw_effect_summary(canvas, ui_tiny_font, ui_small_font, summary_rect, get_effect_summary_rows(session, limit=3))

        feed_rect = pygame.Rect(info_rect.x + 10, info_rect.y + 260, info_rect.width - 20, 58)
        draw_event_feed(canvas, ui_tiny_font, ui_tiny_font, feed_rect, session.recent_events)

        if session.waiting_effect_input:
            helper_text = "Nhan 1 neu thang, 2 neu thua."
        elif session.help_visible:
            helper_text = "Nhan H hoac Esc de dong bang huong dan."
        elif session.current_player is not None and getattr(session.players[session.current_player], "is_bot", False):
            helper_text = f"{session.players[session.current_player].name} dang suy nghi..."
        elif session.turn_mode == MANUAL_TURN_MODE and session.current_player is None:
            helper_text = "Click vao nguoi choi ben trai truoc khi mo o."
        elif session.turn_mode == MANUAL_TURN_MODE:
            helper_text = "Ban o se mo cho nguoi dang duoc chon."
        else:
            helper_text = "Nhan H de xem hotkey, B de mo so tay va M de mute nhanh."
        helper_rect = pygame.Rect(info_rect.x + 10, info_rect.bottom - 38, info_rect.width - 20, 28)
        draw_info_helper(canvas, ui_tiny_font, helper_rect, helper_text)

        render_text(canvas, title_font, "Ban choi", (board_rect.x + 26, board_rect.y + 18), PALETTE["text"])
        if angel_badge is not None:
            canvas.blit(angel_badge, (board_rect.x + 182, board_rect.y + 16))
        if demon_badge is not None:
            canvas.blit(demon_badge, (board_rect.x + 216, board_rect.y + 16))
        layout_definition = BOARD_LAYOUTS.get(session.layout_id, BOARD_LAYOUTS["classic"])
        preset_definition = MATCH_PRESETS.get(session.match_preset, MATCH_PRESETS["classic"])
        subtitle_text = f"{layout_definition['label']} | {preset_definition['label']} | Hieu ung da duoc chia san tu dau tran de can bang hon."
        render_text(canvas, ui_small_font, truncate_text(ui_small_font, subtitle_text, board_rect.width - 390), (board_rect.x + 28, board_rect.y + 56), PALETTE["muted"])
        mode_chip_rect = pygame.Rect(board_rect.right - 274, board_rect.y + 48, 118, 28)
        draw_header_chip(canvas, ui_tiny_font, mode_chip_rect, get_mode_badge_text(session), (245, 236, 231), PALETTE["panel_dark"], PALETTE["muted"])
        if series_state:
            series_summary = " | ".join(
                f"{name}:{wins}"
                for name, wins in sorted(series_state["wins"].items(), key=lambda item: (-item[1], item[0]))
            )
            series_chip_rect = pygame.Rect(board_rect.right - 150, board_rect.y + 48, 118, 28)
            draw_header_chip(canvas, ui_tiny_font, series_chip_rect, f"Series {series_summary}", (231, 245, 236), PALETTE["mint_dark"], PALETTE["text"])

        progress_track = pygame.Rect(board_rect.x + 28, board_rect.y + 84, board_rect.width - 410, 16)
        progress_fill = pygame.Rect(progress_track.x, progress_track.y, int(progress_track.width * (len(session.opened) / max(1, len(session.boxes)))), progress_track.height)
        pygame.draw.rect(canvas, (221, 212, 192), progress_track, border_radius=10)
        if progress_fill.width > 0:
            pygame.draw.rect(canvas, PALETTE["gold"], progress_fill, border_radius=10)
        pygame.draw.rect(canvas, PALETTE["panel_dark"], progress_track, 1, border_radius=10)
        progress_chip_rect = pygame.Rect(progress_track.right + 14, board_rect.y + 78, 108, 28)
        progress_text = f"Tien do {len(session.opened)}/{len(session.boxes)}"
        draw_header_chip(canvas, ui_tiny_font, progress_chip_rect, progress_text, (245, 236, 231), PALETTE["panel_dark"], PALETTE["muted"])
        draw_star(canvas, (progress_track.x - 12, progress_track.centery), 8, PALETTE["gold"])
        draw_star(canvas, (progress_chip_rect.right + 18, progress_track.centery), 6, PALETTE["lilac"])
        draw_heart(canvas, (progress_chip_rect.right + 34, progress_track.centery - 1), 8, (255, 218, 224), PALETTE["crimson_dark"])

        has_oracle_box = any(str(meta.get("effect_id")) == "oracle" for meta in session.box_effects.values())
        legend_rect = None
        if has_oracle_box:
            legend_rect = pygame.Rect(board_rect.right - 208, board_rect.y + 76, 176, 30)
            draw_header_chip(canvas, ui_tiny_font, legend_rect, "Preview = o duoc soi", (245, 236, 231), PALETTE["azure_dark"], PALETTE["muted"])

        grid_rect = pygame.Rect(board_rect.x + 24, board_rect.y + 118, board_rect.width - 48, board_rect.height - 204)
        draw_panel(canvas, grid_rect, fill_color=(232, 223, 207), border_color=PALETTE["panel_dark"], radius=24, shadow=False)
        draw_cloud(canvas, (grid_rect.x + 84, grid_rect.y + 52), 0.42, (255, 247, 244))
        draw_cloud(canvas, (grid_rect.right - 88, grid_rect.bottom - 48), 0.45, (255, 248, 243))
        draw_heart(canvas, (grid_rect.x + 42, grid_rect.bottom - 58), 10, (255, 219, 225), PALETTE["crimson_dark"])
        draw_star(canvas, (grid_rect.right - 38, grid_rect.y + 34), 8, PALETTE["lilac"])

        cols = int(layout_definition.get("columns", 10))
        box_size = int(layout_definition.get("box_size", 72))
        gap = int(layout_definition.get("gap", 12))
        rows = max(1, math.ceil(len(session.boxes) / cols))
        board_total_width = cols * box_size + (cols - 1) * gap
        board_total_height = rows * box_size + (rows - 1) * gap
        start_x = grid_rect.x + max(18, (grid_rect.width - board_total_width) // 2)
        start_y = grid_rect.y + max(18, (grid_rect.height - board_total_height) // 2)

        manual_lock = session.turn_mode == MANUAL_TURN_MODE and session.current_player is None and not session.waiting_effect_input
        reveal_in_progress = tick < session.reveal_lock_until
        interaction_locked = session.waiting_effect_input or manual_lock or reveal_in_progress or session.help_visible
        hovered_index = None
        hovered_effect_id = None
        hovered_rect = None
        for index, box_number in enumerate(session.boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            box_meta = session.box_effects.get(box_number, {})
            if rect.collidepoint(canvas_mouse) and box_number in session.opened:
                hovered_effect_id = box_meta.get("effect_id")
                hovered_rect = rect
            elif rect.collidepoint(canvas_mouse) and box_meta.get("preview_until", 0) > tick and box_number not in session.opened:
                hovered_effect_id = box_meta.get("effect_id")
                hovered_rect = rect
            if rect.collidepoint(canvas_mouse) and box_number not in session.opened and not interaction_locked:
                hovered_index = index

        for index, box_number in enumerate(session.boxes):
            x = start_x + (index % cols) * (box_size + gap)
            y = start_y + (index // cols) * (box_size + gap)
            rect = pygame.Rect(x, y, box_size, box_size)
            draw_rect = rect
            box_meta = session.box_effects.get(box_number, {})
            preview_active = box_meta.get("preview_until", 0) > tick and box_number not in session.opened
            show_opened_effect = box_number in session.opened

            if box_number in session.opened:
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
                flip_progress = min(1.0, max(0.0, (tick - flip_started_at) / session.flip_duration))
                show_opened_effect = flip_progress >= 0.55
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
                idle_bob = 0 if manual_lock or audio_settings.get("reduce_motion", False) else int(math.sin(tick / 220 + index * 0.7) * 3)
                draw_rect = rect.move(0, idle_bob)
                if manual_lock:
                    fill_color = (216, 211, 203)
                    border_color = (152, 147, 160)
                    text_color = PALETTE["muted"]
                else:
                    fill_color = (223, 231, 249)
                    border_color = PALETTE["azure_dark"]
                    text_color = PALETTE["text"]

                if preview_active:
                    border_color, fill_color = get_effect_palette(box_meta.get("effect_id"))
                    draw_glow(canvas, rect.center, border_color, 44, 18)

            if hovered_index == index:
                fill_color = (244, 230, 186)
                border_color = PALETTE["gold_dark"]
                draw_glow(canvas, rect.center, PALETTE["gold"], 52, 24)

            max_radius = max(2, min(draw_rect.width // 2 - 1, draw_rect.height // 2 - 1))
            radius = min(18, max_radius)
            draw_panel(canvas, draw_rect, fill_color=fill_color, border_color=border_color, radius=radius, shadow=False)
            if box_number not in session.opened and draw_rect.width >= 24:
                num_text = ui_font.render(str(box_number), True, text_color)
                canvas.blit(num_text, (draw_rect.centerx - num_text.get_width() // 2, draw_rect.centery - num_text.get_height() // 2))
            if box_number in session.opened and show_opened_effect and draw_rect.width >= 34:
                draw_opened_box_effect(canvas, draw_rect, box_meta.get("effect_id"), ui_font)
                draw_box_particles(canvas, rect, box_meta.get("effect_id"), box_meta.get("opened_at", 0), tick, audio_settings.get("reduce_motion", False))
            elif preview_active and draw_rect.width >= 46:
                draw_effect_sticker(canvas, draw_rect, ui_tiny_font, box_meta.get("effect_id"), compact=True)

        if session.tooltips_visible and hovered_effect_id and hovered_rect is not None and not session.help_visible:
            draw_hover_tooltip(canvas, ui_small_font, ui_tiny_font, hovered_effect_id, (hovered_rect.right, hovered_rect.y))

        quit_rect = pygame.Rect(board_rect.right - 192, board_rect.bottom - 62, 152, 38)
        help_badge_rect = pygame.Rect(quit_rect.x - 164, board_rect.bottom - 62, 150, 38)
        book_rect = pygame.Rect(help_badge_rect.x - 142, board_rect.bottom - 62, 128, 38)
        audio_rect = pygame.Rect(book_rect.x - 118, board_rect.bottom - 62, 104, 38)
        draw_button(
            canvas,
            small_font,
            quit_rect,
            "Ket thuc",
            PALETTE["crimson"],
            PALETTE["crimson_dark"],
            quit_rect.collidepoint(canvas_mouse),
        )

        draw_button(
            canvas,
            small_font,
            help_badge_rect,
            "H - Tro giup",
            PALETTE["azure"],
            PALETTE["azure_dark"],
            help_badge_rect.collidepoint(canvas_mouse),
            PALETTE["text"],
        )
        draw_button(
            canvas,
            small_font,
            book_rect,
            "B - So tay",
            PALETTE["lilac"],
            PALETTE["panel_dark"],
            book_rect.collidepoint(canvas_mouse),
            PALETTE["text"],
        )
        draw_button(
            canvas,
            small_font,
            audio_rect,
            "Mute" if audio_settings.get("music_enabled", True) and audio_settings.get("sfx_enabled", True) else "Unmute",
            PALETTE["panel_soft"],
            PALETTE["panel_dark"],
            audio_rect.collidepoint(canvas_mouse),
            PALETTE["text"],
        )

        if session.banner and session.banner.message:
            accent_color, fill_color = get_effect_palette(session.banner.effect_id, session.banner.message)
            banner_x = board_rect.x + 26
            banner_width = max(260, audio_rect.x - banner_x - 16)
            banner_rect = pygame.Rect(banner_x, board_rect.bottom - 64, banner_width, 40)
            age = tick - session.banner.created_at
            pulse = max(0.0, 1.0 - min(age, 1800) / 1800)
            slide_progress = min(1.0, age / 240)
            banner_rect = banner_rect.move(int((1.0 - slide_progress) * 40), 0)
            if pulse > 0:
                draw_glow(canvas, banner_rect.center, accent_color, 58, int(10 + pulse * 12))
            draw_panel(canvas, banner_rect, fill_color=fill_color, border_color=accent_color, radius=18, shadow=False)
            text = ui_small_font.render(truncate_text(ui_small_font, session.banner.message, banner_rect.width - 30), True, PALETTE["text"])
            canvas.blit(text, (banner_rect.x + 14, banner_rect.centery - text.get_height() // 2))

        draw_score_popups(canvas, ui_small_font, player_hitboxes, session, tick)

        if session.spotlight and not draw_effect_spotlight(
            canvas,
            board_rect,
            spotlight_title_font,
            spotlight_subtitle_font,
            ui_small_font,
            spotlight_symbol_font,
            session.spotlight,
            tick,
        ):
            session.spotlight = None

        if session.help_visible:
            draw_help_overlay(canvas, font, ui_small_font, ui_tiny_font)

        scaled_canvas = pygame.transform.smoothscale(canvas, screen.get_size())
        screen.blit(scaled_canvas, (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", session

            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                session.help_visible = not session.help_visible
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                book_result = show_effect_book_screen(screen)
                if book_result == "quit":
                    return "quit", session
                play_music("game", force_restart=True)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                new_enabled = not (audio_settings.get("music_enabled", True) and audio_settings.get("sfx_enabled", True))
                audio_settings = update_settings({"music_enabled": new_enabled, "sfx_enabled": new_enabled})
                sync_audio_settings(audio_settings)
                play_music("game")
                continue

            if session.help_visible:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    session.help_visible = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    session.help_visible = False
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = (int(event.pos[0] * scale_x), int(event.pos[1] * scale_y))

                if help_badge_rect.collidepoint(pos):
                    session.help_visible = True
                    continue
                if book_rect.collidepoint(pos):
                    book_result = show_effect_book_screen(screen)
                    if book_result == "quit":
                        return "quit", session
                    play_music("game", force_restart=True)
                    continue
                if audio_rect.collidepoint(pos):
                    new_enabled = not (audio_settings.get("music_enabled", True) and audio_settings.get("sfx_enabled", True))
                    audio_settings = update_settings({"music_enabled": new_enabled, "sfx_enabled": new_enabled})
                    sync_audio_settings(audio_settings)
                    play_music("game")
                    continue

                if quit_rect.collidepoint(pos):
                    if series_state:
                        return "quit", session
                    finalize_session_records(session)
                    result = show_final_result(screen, title_font, font, session)
                    return result, session

                if reveal_in_progress:
                    continue

                if session.turn_mode == MANUAL_TURN_MODE and not session.waiting_effect_input:
                    selected_player = False
                    for index, card_rect in player_hitboxes:
                        if card_rect.collidepoint(pos):
                            set_selected_player(session, index, tick)
                            selected_player = True
                            break
                    if selected_player:
                        continue

                if session.waiting_effect_input:
                    continue

                if handle_active_player_skip(session, tick):
                    continue

                for index, box_number in enumerate(session.boxes):
                    x = start_x + (index % cols) * (box_size + gap)
                    y = start_y + (index // cols) * (box_size + gap)
                    rect = pygame.Rect(x, y, box_size, box_size)
                    if rect.collidepoint(pos) and box_number not in session.opened:
                        open_box(session, box_number, tick)
                        break

            elif event.type == pygame.KEYDOWN and session.waiting_effect_input:
                if event.key == pygame.K_1:
                    resolve_rps_result(session, True, tick)
                elif event.key == pygame.K_2:
                    resolve_rps_result(session, False, tick)

        if session.remaining_boxes == 0 and not session.waiting_effect_input and tick >= session.reveal_lock_until:
            if series_state:
                return "series_round_complete", session
            finalize_session_records(session)
            result = show_final_result(screen, title_font, font, session)
            return result, session

        clock.tick(60)


def run_game_ui(players, num_boxes, dist_mode, custom_weights=None, turn_mode=SEQUENTIAL_TURN_MODE, session_options=None):
    pygame.init()
    settings = load_settings()
    sync_audio_settings(settings)
    screen = create_display(GAME_WINDOW_SIZE, "Game", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    fonts = {
        "title": pygame.font.Font(font_path, 30),
        "font": pygame.font.Font(font_path, 20),
        "small": pygame.font.Font(font_path, 16),
        "tiny": pygame.font.Font(font_path, 13),
        "ui": pygame.font.SysFont("Segoe UI", 19, bold=True),
        "ui_small": pygame.font.SysFont("Segoe UI", 15),
        "ui_tiny": pygame.font.SysFont("Segoe UI", 13),
        "spotlight_title": pygame.font.SysFont("Segoe UI", 31, bold=True),
        "spotlight_subtitle": pygame.font.SysFont("Segoe UI", 17, bold=True),
        "spotlight_symbol": pygame.font.SysFont("Segoe UI", 42, bold=True),
    }

    canvas_size = GAME_WINDOW_SIZE
    canvas = pygame.Surface(canvas_size)
    turn_mode = normalize_turn_mode(turn_mode)
    base_session_options = dict(session_options or {})
    series_target_wins = int(base_session_options.get("series_target_wins", 1) or 1)
    series_state = None
    if series_target_wins > 1:
        series_state = {
            "target_wins": series_target_wins,
            "round_number": 1,
            "wins": {player.name: 0 for player in players},
            "champion": None,
        }

    while True:
        play_music("game", force_restart=True)
        round_options = dict(base_session_options)
        if series_state:
            round_options["round_number"] = series_state["round_number"]
            round_options["series_target_wins"] = series_state["target_wins"]
        result, session = run_round(
            screen,
            canvas,
            canvas_size,
            fonts,
            players,
            num_boxes,
            dist_mode,
            custom_weights,
            turn_mode,
            session_options=round_options,
            series_state=series_state,
        )
        if result == "rematch":
            if series_state:
                series_state["round_number"] = 1
                series_state["wins"] = {player.name: 0 for player in players}
                series_state["champion"] = None
            continue
        if result == "series_round_complete" and series_state:
            winner = update_series_score(series_state, session)
            if series_state.get("champion"):
                session.match_notes.append("series_champion")
                finalize_session_records(session)
                result = show_final_result(screen, fonts["title"], fonts["font"], session, series_state=series_state)
                if result == "rematch":
                    series_state["round_number"] = 1
                    series_state["wins"] = {player.name: 0 for player in players}
                    series_state["champion"] = None
                    continue
                return
            finalize_session_records(session)
            intermission_result = show_series_round_result(screen, fonts, session, series_state)
            if intermission_result == "continue":
                series_state["round_number"] += 1
                continue
            return
        return


def show_final_result(screen, title_font, font, session, series_state=None):
    play_music("result", force_restart=True)
    players = sorted(session.players, key=lambda player: player.score, reverse=True)
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    small_font = pygame.font.Font(font_path, 16)
    tiny_font = pygame.font.Font(font_path, 14)
    animation_start = pygame.time.get_ticks()
    effect_rows = get_effect_summary_rows(session, limit=3)
    emblem_surface = get_surface("brand_emblem", (76, 76))
    angel_badge = get_surface("angel_badge", (32, 32))
    demon_badge = get_surface("demon_badge", (32, 32))

    while True:
        tick = pygame.time.get_ticks()
        reveal_progress = min(1.0, (tick - animation_start) / 900)
        draw_background(screen, tick)

        panel_rect = pygame.Rect(100, 54, screen.get_width() - 200, screen.get_height() - 108)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        render_text(screen, title_font, "Ket qua cuoi cung", (panel_rect.x + 36, panel_rect.y + 24), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (panel_rect.right - 110, panel_rect.y + 18))

        winner = players[0]
        winner_text = f"Nguoi thang: {winner.name} - {winner.score} diem"
        if series_state and series_state.get("champion"):
            winner_text = f"Vo dich series: {series_state['champion']} | Round {series_state.get('round_number', 1)}"
        render_text(screen, small_font, winner_text, (panel_rect.x + 38, panel_rect.y + 70), PALETTE["muted"])

        meta_rect = pygame.Rect(panel_rect.x + 38, panel_rect.y + 98, panel_rect.width - 76, 42)
        draw_panel(screen, meta_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=16, shadow=False)
        layout_label = BOARD_LAYOUTS.get(session.layout_id, BOARD_LAYOUTS["classic"])["label"]
        preset_label = MATCH_PRESETS.get(session.match_preset, MATCH_PRESETS["classic"])["label"]
        bot_label = "Co bot" if session.has_bots else "Toan nguoi"
        mode_label = MODE_VARIANTS.get(session.mode_variant, MODE_VARIANTS["standard"])["label"]
        meta_text = f"{mode_label} | {TURN_MODE_LABELS[session.turn_mode]} | {preset_label} | {layout_label} | {bot_label}"
        if session.mode_variant == "challenge" and session.challenge_title:
            meta_text = f"{mode_label}: {session.challenge_title} | {layout_label} | {bot_label}"
        elif series_state:
            score_text = ", ".join(f"{name}:{wins}" for name, wins in sorted(series_state["wins"].items(), key=lambda item: (-item[1], item[0])))
            meta_text = f"{mode_label} | Ti so {score_text}"
        render_text(screen, small_font, truncate_text(small_font, meta_text, meta_rect.width - 24), (meta_rect.x + 12, meta_rect.y + 10), PALETTE["text"])

        stat_cards = get_stat_cards(players)
        stat_top = panel_rect.y + 158
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

        chart_top = stat_top + 110
        if effect_rows:
            summary_rect = pygame.Rect(panel_rect.x + 38, chart_top, panel_rect.width - 76, 60)
            draw_effect_summary(screen, tiny_font, small_font, summary_rect, effect_rows)
            chart_top = summary_rect.bottom + 18

        if session.unlocked_achievements:
            achievement_rect = pygame.Rect(panel_rect.x + 38, chart_top, panel_rect.width - 76, 64)
            draw_panel(screen, achievement_rect, fill_color=(231, 245, 236), border_color=PALETTE["mint_dark"], radius=20, shadow=False)
            titles = ", ".join(item.get("title", "") for item in session.unlocked_achievements[:2])
            if len(session.unlocked_achievements) > 2:
                titles = f"{titles} +{len(session.unlocked_achievements) - 2}"
            render_text(screen, tiny_font, "Thanh tuu moi", (achievement_rect.x + 14, achievement_rect.y + 10), PALETTE["muted"])
            render_text(screen, small_font, truncate_text(small_font, titles, achievement_rect.width - 28), (achievement_rect.x + 14, achievement_rect.y + 32), PALETTE["text"])
            chart_top = achievement_rect.bottom + 18

        chart_rect = pygame.Rect(panel_rect.x + 38, chart_top, panel_rect.width - 76, panel_rect.height - (chart_top - panel_rect.y) - 92)
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

        replay_rect = pygame.Rect(screen.get_width() // 2 - 190, panel_rect.bottom - 58, 170, 42)
        exit_rect = pygame.Rect(screen.get_width() // 2 + 20, panel_rect.bottom - 58, 170, 42)
        draw_button(
            screen,
            font,
            replay_rect,
            "Choi lai",
            PALETTE["mint"],
            PALETTE["mint_dark"],
            replay_rect.collidepoint(pygame.mouse.get_pos()),
            PALETTE["text"],
        )
        draw_button(
            screen,
            font,
            exit_rect,
            "Thoat",
            PALETTE["crimson"],
            PALETTE["crimson_dark"],
            exit_rect.collidepoint(pygame.mouse.get_pos()),
            PALETTE["text"],
        )
        if angel_badge is not None:
            screen.blit(angel_badge, (replay_rect.x - 42, replay_rect.y + 5))
        if demon_badge is not None:
            screen.blit(demon_badge, (exit_rect.right + 10, exit_rect.y + 5))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if replay_rect.collidepoint(event.pos):
                    return "rematch"
                if exit_rect.collidepoint(event.pos):
                    return "quit"
