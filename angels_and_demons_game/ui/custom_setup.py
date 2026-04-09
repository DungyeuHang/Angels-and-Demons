import math
import os
import sys

import pygame

from config import SETUP_WINDOW_SIZE
from config import create_display
from constants import AI_LEVELS
from constants import BOARD_LAYOUTS
from constants import CHALLENGE_PRESETS
from constants import MATCH_PRESETS
from constants import MODE_VARIANTS
from models.player import Player
from models.settings import load_settings
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import TURN_MODE_LABELS
from models.turn_modes import normalize_turn_mode
from ui.audio import play_sfx
from ui.brand_assets import apply_window_icon
from ui.theme import PALETTE
from ui.theme import clamp_text
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_glow
from ui.theme import draw_hint_bar
from ui.theme import draw_panel
from ui.theme import draw_subtitle
from ui.theme import draw_title
from ui.theme import get_reveal_progress
from ui.theme import get_reveal_rect
from ui.theme import get_ui_font
from ui.theme import wrap_text


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def placeholder_name(index):
    return f"Nguoi {index + 1}"


def ensure_player_state(state, count):
    count = max(1, int(count))
    while len(state["player_names"]) < count:
        state["player_names"].append(placeholder_name(len(state["player_names"])))
        state["player_bot_flags"].append(False)
    state["player_names"] = state["player_names"][:count]
    state["player_bot_flags"] = state["player_bot_flags"][:count]
    state["editing"] = min(state["editing"], count - 1)


def focus_player_field(state, index):
    if 0 <= index < len(state["player_names"]) and state["player_names"][index] == placeholder_name(index):
        state["player_names"][index] = ""
    state["editing"] = index


def set_player_count(state, count, focus_new=False):
    previous_count = len(state["player_names"])
    ensure_player_state(state, count)
    if focus_new and len(state["player_names"]) > previous_count:
        focus_player_field(state, len(state["player_names"]) - 1)
    else:
        state["editing"] = min(state["editing"], len(state["player_names"]) - 1)


def clear_all_bots(state):
    state["player_bot_flags"] = [False for _ in state["player_bot_flags"]]


def make_players(state):
    players = []
    for index, name in enumerate(state["player_names"]):
        clean_name = str(name).strip() or placeholder_name(index)
        is_bot = bool(state["player_bot_flags"][index])
        players.append(
            Player(
                clean_name,
                is_bot=is_bot,
                ai_level=state["ai_level"],
                avatar_variant="demon" if is_bot else "angel",
            )
        )
    return players


def get_first_human_name(players):
    for player in players:
        if not getattr(player, "is_bot", False):
            return player.name
    return players[0].name if players else placeholder_name(0)


def build_launch_payload(state):
    players = make_players(state)
    match_preset = state["match_preset"]
    num_boxes = MATCH_PRESETS[match_preset]["num_boxes"]
    dist_mode = "even"
    custom_weights = None
    turn_mode = state["turn_mode"]
    mode_variant = str(state.get("mode_variant", "standard") or "standard")
    session_options = {
        "layout_id": state["layout_id"],
        "match_preset": match_preset,
        "mode_variant": mode_variant,
    }

    if any(getattr(player, "is_bot", False) for player in players) and turn_mode == MANUAL_TURN_MODE:
        turn_mode = SEQUENTIAL_TURN_MODE

    if mode_variant == "solo_bot":
        human_name = get_first_human_name(players)
        players = [
            Player(human_name, is_bot=False, ai_level=state["ai_level"], avatar_variant="angel"),
            Player("AI Doi thu", is_bot=True, ai_level=state["ai_level"], avatar_variant="demon"),
        ]
        turn_mode = SEQUENTIAL_TURN_MODE
    elif mode_variant == "challenge":
        challenge_id = str(state.get("challenge_id") or next(iter(CHALLENGE_PRESETS)))
        preset = CHALLENGE_PRESETS.get(challenge_id, next(iter(CHALLENGE_PRESETS.values())))
        num_boxes = MATCH_PRESETS[str(preset.get("match_preset", "quick"))]["num_boxes"]
        dist_mode = "custom"
        custom_weights = dict(preset.get("weights", {}))
        turn_mode = normalize_turn_mode(preset.get("turn_mode"))
        session_options.update(
            {
                "layout_id": str(preset.get("layout_id", state["layout_id"])),
                "match_preset": str(preset.get("match_preset", "quick")),
                "challenge_id": challenge_id,
                "challenge_title": str(preset.get("label", "Challenge")),
            }
        )
    elif mode_variant == "best_of_three":
        session_options["series_target_wins"] = 2

    return players, num_boxes, dist_mode, custom_weights, turn_mode, session_options


def draw_text_box(surface, font, rect, value, active=False, caret_visible=False):
    fill_color = (247, 242, 232) if active else (238, 229, 214)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
    if active:
        draw_glow(surface, rect.center, PALETTE["gold"], max(30, rect.width // 2), 16)
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)
    text_surface = font.render(value, True, PALETTE["text"])
    surface.blit(text_surface, (rect.x + 10, rect.centery - text_surface.get_height() // 2))
    if active and caret_visible:
        caret_x = min(rect.right - 12, rect.x + 14 + text_surface.get_width())
        pygame.draw.line(surface, border_color, (caret_x, rect.y + 10), (caret_x, rect.bottom - 10), 2)


def draw_choice_card(surface, title_font, detail_font, rect, title, detail, active=False, muted=False, reserve_right=0, hovered=False):
    if muted:
        fill_color = (225, 220, 214)
        border_color = (162, 154, 151)
        title_color = (140, 132, 128)
    elif active:
        fill_color = (247, 223, 184)
        border_color = PALETTE["gold_dark"]
        title_color = PALETTE["text"]
    else:
        fill_color = (247, 240, 232)
        border_color = PALETTE["panel_dark"]
        title_color = PALETTE["text"]

    if active or hovered:
        glow_color = PALETTE["gold"] if active else PALETTE["lilac"]
        draw_glow(surface, rect.center, glow_color, max(38, rect.width // 2), 12 if active else 9)
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=20, shadow=False)
    text_width = max(40, rect.width - 32 - reserve_right)
    title_text = clamp_text(title_font, title, text_width)
    title_surface = title_font.render(title_text, True, title_color)
    surface.blit(title_surface, (rect.x + 16, rect.y + 14))

    detail_color = PALETTE["muted"] if not muted else (150, 144, 140)
    detail_line_height = detail_font.get_height() + 2
    detail_max_lines = 1 if rect.height <= 80 else 2
    detail_lines = wrap_text(detail_font, detail, text_width, max_lines=detail_max_lines)
    detail_y = rect.bottom - 14 - len(detail_lines) * detail_line_height
    detail_y = max(rect.y + 40, detail_y)
    for line in detail_lines:
        detail_surface = detail_font.render(line, True, detail_color)
        surface.blit(detail_surface, (rect.x + 16, detail_y))
        detail_y += detail_line_height


def resolve_setup_snapshot(state):
    mode_variant = str(state.get("mode_variant", "standard") or "standard")
    match_preset = str(state.get("match_preset", "classic"))
    layout_id = str(state.get("layout_id", "classic"))
    turn_mode = normalize_turn_mode(state.get("turn_mode"))
    challenge_label = ""

    if mode_variant == "challenge":
        challenge_id = str(state.get("challenge_id") or next(iter(CHALLENGE_PRESETS)))
        challenge = CHALLENGE_PRESETS.get(challenge_id, next(iter(CHALLENGE_PRESETS.values())))
        match_preset = str(challenge.get("match_preset", match_preset))
        layout_id = str(challenge.get("layout_id", layout_id))
        turn_mode = normalize_turn_mode(challenge.get("turn_mode"))
        challenge_label = str(challenge.get("label", "Challenge"))

    match_info = MATCH_PRESETS.get(match_preset, MATCH_PRESETS["classic"])
    layout_info = BOARD_LAYOUTS.get(layout_id, BOARD_LAYOUTS["classic"])
    ai_info = AI_LEVELS.get(str(state.get("ai_level", "normal")), AI_LEVELS["normal"])
    slot_count = 2 if mode_variant == "solo_bot" else len(state.get("player_names", []))
    return {
        "mode_variant": mode_variant,
        "mode_label": MODE_VARIANTS.get(mode_variant, MODE_VARIANTS["standard"])["label"],
        "challenge_label": challenge_label,
        "match_preset": match_preset,
        "match_label": match_info["label"],
        "num_boxes": int(match_info["num_boxes"]),
        "layout_id": layout_id,
        "layout_label": layout_info["label"],
        "layout_columns": int(layout_info["columns"]),
        "turn_mode": turn_mode,
        "turn_label": TURN_MODE_LABELS.get(turn_mode, "Lan luot"),
        "ai_label": ai_info["label"],
        "slot_count": slot_count,
    }


def draw_layout_preview(surface, rect, num_boxes, columns, active=False):
    fill_color = (255, 248, 238) if active else (246, 238, 226)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)

    inner_rect = rect.inflate(-10, -10)
    columns = max(1, int(columns))
    rows = max(1, math.ceil(max(1, int(num_boxes)) / columns))
    sample_rows = min(4, rows)
    sample_count = min(max(1, int(num_boxes)), columns * sample_rows)
    gap = 2
    cell_size = max(
        3,
        min(
            (inner_rect.width - max(0, columns - 1) * gap) // columns,
            (inner_rect.height - max(0, sample_rows - 1) * gap) // sample_rows,
        ),
    )
    total_width = columns * cell_size + max(0, columns - 1) * gap
    total_height = sample_rows * cell_size + max(0, sample_rows - 1) * gap
    start_x = inner_rect.centerx - total_width // 2
    start_y = inner_rect.centery - total_height // 2
    cell_fill = PALETTE["azure"] if active else (208, 219, 236)
    cell_border = PALETTE["azure_dark"] if active else PALETTE["panel_dark"]

    for cell_index in range(sample_count):
        row = cell_index // columns
        col = cell_index % columns
        cell_rect = pygame.Rect(start_x + col * (cell_size + gap), start_y + row * (cell_size + gap), cell_size, cell_size)
        pygame.draw.rect(surface, cell_fill, cell_rect, border_radius=max(2, cell_size // 3))
        pygame.draw.rect(surface, cell_border, cell_rect, 1, border_radius=max(2, cell_size // 3))

    if rows > sample_rows:
        dot_y = rect.bottom - 7
        for dot_index in range(3):
            pygame.draw.circle(surface, PALETTE["muted"], (rect.centerx - 8 + dot_index * 8, dot_y), 1)


def draw_setup_snapshot_card(surface, rect, snapshot, title_font, body_font, tiny_font):
    draw_panel(surface, rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
    preview_rect = pygame.Rect(rect.x + 10, rect.y + 7, 62, rect.height - 14)
    draw_layout_preview(surface, preview_rect, snapshot["num_boxes"], snapshot["layout_columns"], active=True)

    title_prefix = snapshot["challenge_label"] if snapshot["challenge_label"] else snapshot["mode_label"]
    title_copy = clamp_text(title_font, f"{title_prefix} | {snapshot['match_label']} | {snapshot['num_boxes']} o", rect.width - 94)
    detail_copy = clamp_text(
        body_font,
        f"{snapshot['layout_label']} | {snapshot['turn_label']} | AI {snapshot['ai_label']} | {snapshot['slot_count']} slot",
        rect.width - 94,
    )
    surface.blit(title_font.render(title_copy, True, PALETTE["text"]), (rect.x + 82, rect.y + 8))
    surface.blit(body_font.render(detail_copy, True, PALETTE["muted"]), (rect.x + 82, rect.y + 25))
    footer_copy = clamp_text(tiny_font, "Preview layout song theo lua chon hien tai.", rect.width - 94)
    surface.blit(tiny_font.render(footer_copy, True, PALETTE["muted"]), (rect.x + 82, rect.bottom - 15))


def apply_match_hotkey(state, key):
    preset_ids = list(MATCH_PRESETS)
    layout_ids = list(BOARD_LAYOUTS)
    if pygame.K_1 <= key <= pygame.K_3:
        index = key - pygame.K_1
        if index < len(preset_ids):
            state["match_preset"] = preset_ids[index]
            return True
    layout_keys = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r]
    if key in layout_keys:
        index = layout_keys.index(key)
        if index < len(layout_ids):
            state["layout_id"] = layout_ids[index]
            return True
    return False


def apply_rules_hotkey(state, key):
    mode_ids = list(MODE_VARIANTS)
    ai_ids = list(AI_LEVELS)
    if pygame.K_1 <= key <= pygame.K_4:
        index = key - pygame.K_1
        if index < len(mode_ids):
            state["mode_variant"] = mode_ids[index]
            if state["mode_variant"] == "challenge":
                state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
            return True
    if key == pygame.K_a:
        state["turn_mode"] = SEQUENTIAL_TURN_MODE
        return True
    if key == pygame.K_s and not any(state["player_bot_flags"]) and state["mode_variant"] != "challenge":
        state["turn_mode"] = MANUAL_TURN_MODE
        return True
    if key in (pygame.K_z, pygame.K_x, pygame.K_c):
        index = [pygame.K_z, pygame.K_x, pygame.K_c].index(key)
        if index < len(ai_ids):
            state["ai_level"] = ai_ids[index]
            return True
    if state["mode_variant"] == "challenge" and key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_COMMA, pygame.K_PERIOD):
        challenge_ids = list(CHALLENGE_PRESETS)
        current_index = challenge_ids.index(state["challenge_id"])
        step = -1 if key in (pygame.K_LEFT, pygame.K_COMMA) else 1
        state["challenge_id"] = challenge_ids[(current_index + step) % len(challenge_ids)]
        state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
        return True
    return False


def run_custom_setup_ui():
    pygame.init()
    pygame.key.start_text_input()

    settings = load_settings()
    screen = create_display(SETUP_WINDOW_SIZE, "Chuan bi van choi", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    font = get_ui_font(19, bold=True)
    small_font = get_ui_font(15)
    tiny_font = get_ui_font(13)
    clock = pygame.time.Clock()
    reduce_motion = settings.get("reduce_motion", False)
    screen_started_at = pygame.time.get_ticks()
    phase_started_at = screen_started_at

    state = {
        "phase": "players",
        "player_names": [placeholder_name(0), placeholder_name(1)],
        "player_bot_flags": [False, False],
        "editing": 0,
        "match_preset": "classic",
        "layout_id": "classic",
        "turn_mode": SEQUENTIAL_TURN_MODE,
        "ai_level": "normal",
        "mode_variant": "standard",
        "challenge_id": next(iter(CHALLENGE_PRESETS)),
        "error": "",
    }
    focus_player_field(state, 0)

    while True:
        tick = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        caret_visible = (tick // 450) % 2 == 0
        phase_before_events = state["phase"]
        draw_background(screen, tick)
        panel_progress = get_reveal_progress(screen_started_at, tick, duration=380, reduce_motion=reduce_motion)
        phase_progress = get_reveal_progress(phase_started_at, tick, duration=300, reduce_motion=reduce_motion)

        panel_rect = get_reveal_rect(pygame.Rect(34, 22, screen.get_width() - 68, screen.get_height() - 44), panel_progress, offset_y=20)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        draw_title(screen, title_font, "Chuan bi van choi", (panel_rect.centerx, panel_rect.y + 48), PALETTE["text"])
        draw_subtitle(screen, small_font, "Chon nguoi choi, bot, layout va nhip do tran dau truoc khi vao san.", (panel_rect.centerx, panel_rect.y + 82))

        step_labels = [
            ("players", "1. Nguoi choi"),
            ("match", "2. Tran dau"),
            ("rules", "3. Luat & AI"),
        ]
        for index, (phase_key, label) in enumerate(step_labels):
            chip_progress = get_reveal_progress(phase_started_at, tick, duration=280, delay_ms=index * 32, reduce_motion=reduce_motion)
            chip_rect = get_reveal_rect(pygame.Rect(panel_rect.x + 40 + index * 190, panel_rect.y + 108, 174, 34), chip_progress, offset_y=10)
            active = state["phase"] == phase_key
            if active:
                draw_glow(screen, chip_rect.center, PALETTE["gold"], 64, 14)
            draw_panel(
                screen,
                chip_rect,
                fill_color=(247, 223, 184) if active else (241, 234, 221),
                border_color=PALETTE["gold_dark"] if active else PALETTE["panel_dark"],
                radius=16,
                shadow=False,
            )
            chip_text = tiny_font.render(label, True, PALETTE["text"])
            screen.blit(chip_text, (chip_rect.centerx - chip_text.get_width() // 2, chip_rect.centery - chip_text.get_height() // 2))

        main_rect = get_reveal_rect(pygame.Rect(panel_rect.x + 34, panel_rect.y + 158, panel_rect.width - 68, panel_rect.height - 228), phase_progress, offset_y=14)
        draw_panel(screen, main_rect, fill_color=(252, 245, 235), border_color=PALETTE["lilac"], radius=26, shadow=False)
        next_rect = get_reveal_rect(pygame.Rect(panel_rect.right - 224, panel_rect.bottom - 62, 178, 42), phase_progress, offset_y=10)
        back_rect = get_reveal_rect(pygame.Rect(panel_rect.right - 418, panel_rect.bottom - 62, 160, 42), phase_progress, offset_y=10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None, None, None, None, None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state["phase"] == "players":
                        return None, None, None, None, None, None
                    state["phase"] = {
                        "match": "players",
                        "rules": "match",
                    }.get(state["phase"], "players")
                    state["error"] = ""
                elif event.key == pygame.K_TAB and state["phase"] == "players" and state["player_names"]:
                    focus_player_field(state, (state["editing"] + 1) % len(state["player_names"]))
                elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE) and state["phase"] == "players":
                    current = state["player_names"][state["editing"]]
                    state["player_names"][state["editing"]] = current[:-1]
                elif event.key == pygame.K_RETURN:
                    if state["phase"] == "players":
                        if all(str(name).strip() for name in state["player_names"]):
                            state["phase"] = "match"
                            state["error"] = ""
                            play_sfx("ui_click", volume_multiplier=0.5)
                        else:
                            state["error"] = "Hay nhap ten cho tat ca nguoi choi."
                    elif state["phase"] == "match":
                        state["phase"] = "rules"
                        state["error"] = ""
                        play_sfx("ui_click", volume_multiplier=0.5)
                    else:
                        return build_launch_payload(state)
                elif state["phase"] == "match" and apply_match_hotkey(state, event.key):
                    state["error"] = ""
                    play_sfx("ui_click", volume_multiplier=0.42)
                elif state["phase"] == "rules" and apply_rules_hotkey(state, event.key):
                    state["error"] = ""
                    play_sfx("ui_click", volume_multiplier=0.42)
            elif event.type == pygame.TEXTINPUT and state["phase"] == "players" and state["player_names"]:
                state["player_names"][state["editing"]] += event.text

        if state["phase"] != phase_before_events:
            phase_started_at = tick

        if state["phase"] == "players":
            draw_title(screen, font, "Nguoi choi", (main_rect.centerx, main_rect.y + 34), PALETTE["text"])
            draw_subtitle(screen, small_font, "Mac dinh uu tien nguoi voi nguoi. Neu can ban van co the bat bot cho tung slot rieng.", (main_rect.centerx, main_rect.y + 62))

            minus_rect = pygame.Rect(main_rect.x + 38, main_rect.y + 90, 46, 38)
            count_rect = pygame.Rect(main_rect.x + 94, main_rect.y + 90, 70, 38)
            plus_rect = pygame.Rect(main_rect.x + 174, main_rect.y + 90, 46, 38)
            draw_button(screen, font, minus_rect, "-", PALETTE["panel_soft"], PALETTE["panel_dark"], minus_rect.collidepoint(mouse_pos), PALETTE["text"])
            draw_panel(screen, count_rect, fill_color=(246, 239, 225), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
            count_surface = font.render(str(len(state["player_names"])), True, PALETTE["text"])
            screen.blit(count_surface, (count_rect.centerx - count_surface.get_width() // 2, count_rect.centery - count_surface.get_height() // 2))
            draw_button(screen, font, plus_rect, "+", PALETTE["panel_soft"], PALETTE["panel_dark"], plus_rect.collidepoint(mouse_pos), PALETTE["text"])

            quick_label = tiny_font.render("Preset nhanh cho van nguoi voi nguoi", True, PALETTE["muted"])
            screen.blit(quick_label, (main_rect.x + 248, main_rect.y + 98))
            preset_count_rects = []
            for preset_index, count in enumerate((2, 4, 6, 8)):
                rect = pygame.Rect(main_rect.x + 486 + preset_index * 74, main_rect.y + 90, 64, 34)
                active = len(state["player_names"]) == count and not any(state["player_bot_flags"])
                draw_button(
                    screen,
                    tiny_font,
                    rect,
                    f"{count} nguoi",
                    (247, 223, 184) if active else (241, 234, 221),
                    PALETTE["gold_dark"] if active else PALETTE["panel_dark"],
                    rect.collidepoint(mouse_pos),
                    PALETTE["text"],
                )
                preset_count_rects.append((count, rect))

            humans_only_rect = pygame.Rect(main_rect.right - 178, main_rect.y + 90, 140, 34)
            all_human_active = not any(state["player_bot_flags"])
            draw_button(
                screen,
                tiny_font,
                humans_only_rect,
                "Tat ca la nguoi",
                (231, 245, 236) if all_human_active else (241, 234, 221),
                PALETTE["mint_dark"] if all_human_active else PALETTE["panel_dark"],
                humans_only_rect.collidepoint(mouse_pos),
                PALETTE["text"],
            )

            name_rects = []
            per_row = 3
            box_width = (main_rect.width - 110) // per_row
            for index, name in enumerate(state["player_names"]):
                row = index // per_row
                col = index % per_row
                x = main_rect.x + 36 + col * (box_width + 12)
                y = main_rect.y + 176 + row * 94
                name_rect = pygame.Rect(x, y, box_width - 94, 44)
                mode_rect = pygame.Rect(name_rect.right + 10, y, 74, 44)
                draw_text_box(screen, font, name_rect, name, active=index == state["editing"], caret_visible=index == state["editing"] and caret_visible)
                draw_button(
                    screen,
                    small_font,
                    mode_rect,
                    "BOT" if state["player_bot_flags"][index] else "Nguoi",
                    PALETTE["crimson"] if state["player_bot_flags"][index] else PALETTE["mint"],
                    PALETTE["crimson_dark"] if state["player_bot_flags"][index] else PALETTE["mint_dark"],
                    mode_rect.collidepoint(mouse_pos),
                    PALETTE["text"],
                )
                name_rects.append((index, name_rect, mode_rect))

            bot_count = sum(1 for flag in state["player_bot_flags"] if flag)
            helper_text = "Tab de doi o nhap. Van nguoi voi nguoi dang la luong chinh."
            if bot_count:
                helper_text = f"Dang co {bot_count} bot. Neu giu bot, che do Manual se tu doi ve Lan luot khi vao tran."
            helper_rect = pygame.Rect(main_rect.x + 38, main_rect.bottom - 42, main_rect.width - 76, 30)
            draw_hint_bar(screen, tiny_font, helper_rect, helper_text)

            if mouse_clicked:
                if minus_rect.collidepoint(mouse_pos) and len(state["player_names"]) > 1:
                    set_player_count(state, len(state["player_names"]) - 1)
                    play_sfx("ui_click", volume_multiplier=0.45)
                elif plus_rect.collidepoint(mouse_pos):
                    set_player_count(state, len(state["player_names"]) + 1, focus_new=True)
                    play_sfx("ui_click", volume_multiplier=0.45)
                elif humans_only_rect.collidepoint(mouse_pos):
                    clear_all_bots(state)
                    play_sfx("ui_click", volume_multiplier=0.42)
                else:
                    preset_handled = False
                    for count, rect in preset_count_rects:
                        if rect.collidepoint(mouse_pos):
                            set_player_count(state, count)
                            clear_all_bots(state)
                            play_sfx("ui_click", volume_multiplier=0.42)
                            preset_handled = True
                            break
                    if preset_handled:
                        pass
                    else:
                        for index, name_rect, mode_rect in name_rects:
                            if name_rect.collidepoint(mouse_pos):
                                focus_player_field(state, index)
                                play_sfx("ui_click", volume_multiplier=0.42)
                            elif mode_rect.collidepoint(mouse_pos):
                                state["player_bot_flags"][index] = not state["player_bot_flags"][index]
                                play_sfx("ui_click", volume_multiplier=0.45)

        elif state["phase"] == "match":
            draw_title(screen, font, "Nhip do va Ban do", (main_rect.centerx, main_rect.y + 34), PALETTE["text"])
            draw_subtitle(screen, small_font, "Preset quyet dinh so o. Layout thay doi cach board xep hien thi.", (main_rect.centerx, main_rect.y + 62))
            shortcut_rect = pygame.Rect(main_rect.x + 86, main_rect.y + 78, main_rect.width - 172, 24)
            draw_hint_bar(screen, tiny_font, shortcut_rect, "Nhan 1-3 de doi preset | Q W E R de doi layout | Enter de sang buoc tiep theo")

            preset_rects = []
            for index, (preset_id, preset) in enumerate(MATCH_PRESETS.items()):
                rect = pygame.Rect(main_rect.x + 36 + index * 260, main_rect.y + 102, 230, 110)
                draw_choice_card(
                    screen,
                    font,
                    small_font,
                    rect,
                    f"{preset['label']} - {preset['num_boxes']} o",
                    preset["description"],
                    active=state["match_preset"] == preset_id,
                    hovered=rect.collidepoint(mouse_pos),
                )
                preset_rects.append((preset_id, rect))

            layout_rects = []
            for index, (layout_id, layout) in enumerate(BOARD_LAYOUTS.items()):
                row = index // 2
                col = index % 2
                rect = pygame.Rect(main_rect.x + 120 + col * 350, main_rect.y + 258 + row * 132, 300, 108)
                is_active = state["layout_id"] == layout_id
                draw_choice_card(screen, font, small_font, rect, layout["label"], layout["description"], active=is_active, reserve_right=88, hovered=rect.collidepoint(mouse_pos))
                preview_rect = pygame.Rect(rect.right - 80, rect.y + 16, 60, 60)
                draw_layout_preview(screen, preview_rect, MATCH_PRESETS[state["match_preset"]]["num_boxes"], layout["columns"], active=is_active)
                extra = tiny_font.render(f"{layout['columns']} cot | o {layout['box_size']}px", True, PALETTE["muted"])
                screen.blit(extra, (rect.x + 16, rect.bottom - 24))
                layout_rects.append((layout_id, rect))

            if mouse_clicked:
                for preset_id, rect in preset_rects:
                    if rect.collidepoint(mouse_pos):
                        state["match_preset"] = preset_id
                        play_sfx("ui_click", volume_multiplier=0.45)
                for layout_id, rect in layout_rects:
                    if rect.collidepoint(mouse_pos):
                        state["layout_id"] = layout_id
                        play_sfx("ui_click", volume_multiplier=0.45)

        else:
            has_bots = any(state["player_bot_flags"])
            draw_title(screen, font, "Che do, Luat va AI", (main_rect.centerx, main_rect.y + 30), PALETTE["text"])
            draw_subtitle(screen, small_font, "Chon kieu tran dau, cach quay luot va do kho AI cho van sap toi.", (main_rect.centerx, main_rect.y + 58))

            mode_rects = []
            primary_mode_ids = ["standard", "challenge", "best_of_three"]
            mode_card_width = 246
            mode_gap = 16
            mode_y = main_rect.y + 88
            total_primary_width = len(primary_mode_ids) * mode_card_width + max(0, len(primary_mode_ids) - 1) * mode_gap
            mode_start_x = main_rect.centerx - total_primary_width // 2
            for index, mode_id in enumerate(primary_mode_ids):
                mode_data = MODE_VARIANTS[mode_id]
                rect = pygame.Rect(mode_start_x + index * (mode_card_width + mode_gap), mode_y, mode_card_width, 72)
                detail = mode_data["description"]
                if mode_id == "challenge":
                    challenge_title = CHALLENGE_PRESETS[state["challenge_id"]]["label"]
                    detail = f"{challenge_title} | {detail}"
                draw_choice_card(screen, small_font, tiny_font, rect, mode_data["label"], detail, active=state["mode_variant"] == mode_id, hovered=rect.collidepoint(mouse_pos))
                mode_rects.append((mode_id, rect))

            challenge_prev_rect = None
            challenge_card_rect = None
            challenge_next_rect = None
            turn_top = main_rect.y + 196
            if state["mode_variant"] == "challenge":
                challenge_ids = list(CHALLENGE_PRESETS)
                current_preset = CHALLENGE_PRESETS[state["challenge_id"]]
                challenge_prev_rect = pygame.Rect(main_rect.x + 70, main_rect.y + 172, 48, 44)
                challenge_card_rect = pygame.Rect(main_rect.x + 132, main_rect.y + 166, main_rect.width - 264, 56)
                challenge_next_rect = pygame.Rect(main_rect.right - 118, main_rect.y + 172, 48, 44)
                draw_button(screen, small_font, challenge_prev_rect, "<", PALETTE["panel_soft"], PALETTE["panel_dark"], challenge_prev_rect.collidepoint(mouse_pos), PALETTE["text"])
                draw_choice_card(screen, small_font, tiny_font, challenge_card_rect, current_preset["label"], current_preset["description"], active=True, hovered=challenge_card_rect.collidepoint(mouse_pos))
                extra_text = f"{MATCH_PRESETS[current_preset['match_preset']]['label']} | {BOARD_LAYOUTS[current_preset['layout_id']]['label']} | {len(challenge_ids)} preset"
                extra_surface = tiny_font.render(extra_text, True, PALETTE["muted"])
                screen.blit(extra_surface, (challenge_card_rect.x + 16, challenge_card_rect.bottom - 18))
                draw_button(screen, small_font, challenge_next_rect, ">", PALETTE["panel_soft"], PALETTE["panel_dark"], challenge_next_rect.collidepoint(mouse_pos), PALETTE["text"])
                turn_top += 48

            sequential_rect = pygame.Rect(main_rect.x + 68, turn_top, 360, 88)
            manual_rect = pygame.Rect(main_rect.x + 470, turn_top, 360, 88)
            draw_choice_card(
                screen,
                font,
                small_font,
                sequential_rect,
                TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE],
                "Game tu quay vong nguoi choi theo thu tu.",
                active=state["turn_mode"] == SEQUENTIAL_TURN_MODE,
                hovered=sequential_rect.collidepoint(mouse_pos),
            )
            draw_choice_card(
                screen,
                font,
                small_font,
                manual_rect,
                TURN_MODE_LABELS[MANUAL_TURN_MODE],
                "Ban tu click ten nguoi choi truoc khi mo o.",
                active=state["turn_mode"] == MANUAL_TURN_MODE,
                muted=has_bots or state["mode_variant"] == "challenge",
                hovered=manual_rect.collidepoint(mouse_pos),
            )
            if has_bots or state["mode_variant"] == "challenge":
                note_text = "Co bot: che do nay se tu dong chuyen ve Lan luot khi bat dau."
                if state["mode_variant"] == "challenge":
                    note_text = "Challenge su dung luat quay luot co san de giu dung tinh chat thu thach."
                note = tiny_font.render(note_text, True, PALETTE["crimson_dark"])
                screen.blit(note, (manual_rect.x + 16, manual_rect.bottom - 24))

            ai_rects = []
            for index, (ai_level, ai_config) in enumerate(AI_LEVELS.items()):
                rect = pygame.Rect(main_rect.x + 70 + index * 250, turn_top + 102, 220, 86)
                draw_choice_card(screen, font, small_font, rect, ai_config["label"], ai_config["description"], active=state["ai_level"] == ai_level, hovered=rect.collidepoint(mouse_pos))
                ai_rects.append((ai_level, rect))

            snapshot_rect = pygame.Rect(main_rect.x + 74, main_rect.bottom - 68, main_rect.width - 148, 46)
            draw_setup_snapshot_card(screen, snapshot_rect, resolve_setup_snapshot(state), small_font, tiny_font, tiny_font)
            shortcut_rect = pygame.Rect(main_rect.x + 74, snapshot_rect.y - 26, main_rect.width - 364, 24)
            shortcut_text = "1-3 che do chinh | 4 solo bot | A-S luot | Z-X-C AI"
            if state["mode_variant"] == "challenge":
                shortcut_text = "1-3 che do chinh | 4 solo bot | A-S luot | Z-X-C AI | <- -> doi challenge"
            draw_hint_bar(screen, tiny_font, shortcut_rect, shortcut_text)
            solo_rect = pygame.Rect(shortcut_rect.right + 12, snapshot_rect.y - 28, 204, 28)
            solo_active = state["mode_variant"] == "solo_bot"
            draw_panel(
                screen,
                solo_rect,
                fill_color=(247, 223, 184) if solo_active else (241, 234, 221),
                border_color=PALETTE["gold_dark"] if solo_active else PALETTE["panel_dark"],
                radius=14,
                shadow=False,
            )
            solo_label = tiny_font.render("4 | Solo vs Bot | doi gio", True, PALETTE["text"] if solo_active else PALETTE["muted"])
            screen.blit(solo_label, (solo_rect.centerx - solo_label.get_width() // 2, solo_rect.centery - solo_label.get_height() // 2))
            mode_rects.append(("solo_bot", solo_rect))

            if mouse_clicked:
                for mode_id, rect in mode_rects:
                    if rect.collidepoint(mouse_pos):
                        state["mode_variant"] = mode_id
                        if mode_id == "challenge":
                            state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
                        play_sfx("ui_click", volume_multiplier=0.45)
                        break
                else:
                    challenge_ids = list(CHALLENGE_PRESETS)
                    if challenge_prev_rect is not None and challenge_prev_rect.collidepoint(mouse_pos):
                        current_index = challenge_ids.index(state["challenge_id"])
                        state["challenge_id"] = challenge_ids[(current_index - 1) % len(challenge_ids)]
                        state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
                        play_sfx("ui_click", volume_multiplier=0.45)
                    elif challenge_next_rect is not None and challenge_next_rect.collidepoint(mouse_pos):
                        current_index = challenge_ids.index(state["challenge_id"])
                        state["challenge_id"] = challenge_ids[(current_index + 1) % len(challenge_ids)]
                        state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
                        play_sfx("ui_click", volume_multiplier=0.45)
                    elif sequential_rect.collidepoint(mouse_pos):
                        state["turn_mode"] = SEQUENTIAL_TURN_MODE
                        play_sfx("ui_click", volume_multiplier=0.45)
                    elif manual_rect.collidepoint(mouse_pos) and not has_bots and state["mode_variant"] != "challenge":
                        state["turn_mode"] = MANUAL_TURN_MODE
                        play_sfx("ui_click", volume_multiplier=0.45)
                    for ai_level, rect in ai_rects:
                        if rect.collidepoint(mouse_pos):
                            state["ai_level"] = ai_level
                            play_sfx("ui_click", volume_multiplier=0.45)
            if state["mode_variant"] == "challenge":
                info_surface = tiny_font.render("Challenge khoa layout, so o va bo effect theo tung preset. Doi preset bang < >.", True, PALETTE["crimson_dark"])
                screen.blit(info_surface, (main_rect.x + 72, shortcut_rect.y - 22))

        back_label = "Thoat" if state["phase"] == "players" else "Tro lai"
        next_label = {
            "players": "Tiep",
            "match": "Tiep",
            "rules": "Bat dau",
        }[state["phase"]]
        draw_button(screen, small_font, back_rect, back_label, PALETTE["crimson"], PALETTE["crimson_dark"], back_rect.collidepoint(mouse_pos), PALETTE["text"])
        draw_button(screen, small_font, next_rect, next_label, PALETTE["mint"], PALETTE["mint_dark"], next_rect.collidepoint(mouse_pos), PALETTE["text"])

        if mouse_clicked:
            if back_rect.collidepoint(mouse_pos):
                play_sfx("ui_click", volume_multiplier=0.45)
                if state["phase"] == "players":
                    return None, None, None, None, None, None
                state["phase"] = {
                    "match": "players",
                    "rules": "match",
                }[state["phase"]]
                state["error"] = ""
            elif next_rect.collidepoint(mouse_pos):
                play_sfx("ui_click", volume_multiplier=0.48)
                if state["phase"] == "players":
                    if all(str(name).strip() for name in state["player_names"]):
                        state["phase"] = "match"
                        state["error"] = ""
                    else:
                        state["error"] = "Hay nhap ten cho tat ca nguoi choi."
                elif state["phase"] == "match":
                    state["phase"] = "rules"
                    state["error"] = ""
                else:
                    return build_launch_payload(state)

        if state["error"]:
            error_surface = small_font.render(state["error"], True, PALETTE["crimson_dark"])
            screen.blit(error_surface, (panel_rect.x + 42, panel_rect.bottom - 46))

        pygame.display.flip()
        clock.tick(60)


def run_default_setup_ui():
    return run_custom_setup_ui()
