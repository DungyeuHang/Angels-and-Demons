import os
import sys

import pygame

from config import CUSTOM_WINDOW_SIZE
from config import create_display
from constants import AI_LEVELS
from constants import BOARD_LAYOUTS
from constants import MODE_VARIANTS
from mechanics.effects import get_all_effects
from mechanics.randomizer import build_default_weight_map
from mechanics.randomizer import sanitize_weights
from models.custom_effects import CUSTOM_EFFECT_OPERATION_LABELS
from models.custom_effects import CUSTOM_EFFECT_OPERATION_OPTIONS
from models.custom_effects import delete_custom_effect
from models.custom_effects import save_custom_effect
from models.custom_modes import delete_custom_mode
from models.custom_modes import load_custom_modes
from models.custom_modes import save_custom_mode
from models.player import Player
from models.settings import load_settings
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import TURN_MODE_LABELS
from models.turn_modes import normalize_turn_mode
from ui.audio import play_sfx
from ui.brand_assets import apply_window_icon
from ui.custom_setup import draw_layout_preview
from ui.theme import PALETTE
from ui.theme import clamp_text
from ui.theme import draw_background
from ui.theme import draw_glow
from ui.theme import draw_hint_bar
from ui.theme import draw_panel
from ui.theme import draw_scrollbar
from ui.theme import get_title_font
from ui.theme import get_ui_font


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_font(size=20, ui=False, bold=False):
    if ui:
        return get_ui_font(size, bold=bold)
    return get_title_font(size)


def placeholder_name(index):
    return f"Người {index + 1}"


def refresh_text_input():
    pygame.key.stop_text_input()
    pygame.key.start_text_input()


def draw_button(screen, font, rect, label, bg_color, text_color=(0, 0, 0), border_color=None):
    border_color = border_color or PALETTE["panel_dark"]
    pygame.draw.rect(screen, bg_color, rect, border_radius=8)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)
    text = font.render(label, True, text_color)
    screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def draw_box(screen, font, rect, value, active=False, caret_visible=False):
    fill_color = (247, 242, 232) if active else (234, 226, 210)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]

    pygame.draw.rect(screen, fill_color, rect, border_radius=8)
    pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=8)

    text = font.render(value, True, (0, 0, 0))
    text_x = rect.x + 10
    text_y = rect.centery - text.get_height() // 2
    screen.blit(text, (text_x, text_y))

    if active and caret_visible:
        caret_x = text_x + text.get_width() + 2
        caret_top = rect.centery - text.get_height() // 2
        caret_bottom = rect.centery + text.get_height() // 2
        pygame.draw.line(screen, border_color, (caret_x, caret_top), (caret_x, caret_bottom), 2)


def draw_filter_chip(screen, font, rect, label, active=False, hovered=False):
    fill_color = (247, 223, 184) if active else (247, 239, 223) if hovered else (241, 234, 221)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
    if active or hovered:
        draw_glow(screen, rect.center, PALETTE["gold"] if active else PALETTE["lilac"], max(34, rect.width // 2), 10 if active else 7)
    draw_panel(screen, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)
    text = font.render(label, True, PALETTE["text"])
    screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def draw_preset_tag(screen, font, rect, label, fill_color, border_color, text_color=None):
    if border_color in {PALETTE["gold_dark"], PALETTE["mint_dark"]}:
        draw_glow(screen, rect.center, border_color, max(26, rect.width // 2), 7)
    draw_panel(screen, rect, fill_color=fill_color, border_color=border_color, radius=12, shadow=False)
    text = font.render(label, True, text_color or PALETTE["text"])
    screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


CUSTOM_MODE_PHASE_BADGES = {
    "list": ("Preset list", "Danh sách"),
    "name": ("Bước 1/7", "Tên mode"),
    "players": ("Bước 2/7", "Số slot"),
    "names": ("Bước 3/7", "Người chơi"),
    "boxes": ("Bước 4/7", "Số ô"),
    "turn_mode": ("Bước 5/7", "Luat choi"),
    "weights": ("Bước 6/7", "Tỉ lệ effect"),
    "effect_editor": ("Bước 6/7", "Thêm effect"),
    "save": ("Bước 7/7", "Lưu & chơi"),
}


WEIGHT_FILTER_OPTIONS = [
    ("all", "Tất cả"),
    ("builtin", "Mặc định"),
    ("custom", "Custom"),
]


def draw_phase_badges(screen, font, tiny_font, phase):
    progress_label, phase_label = CUSTOM_MODE_PHASE_BADGES.get(phase, ("Chế độ", "Custom"))
    phase_width = max(104, tiny_font.size(phase_label)[0] + 22)
    progress_width = max(108, tiny_font.size(progress_label)[0] + 22)
    phase_rect = pygame.Rect(screen.get_width() - 176 - phase_width, 34, phase_width, 28)
    progress_rect = pygame.Rect(screen.get_width() - 60 - progress_width, 34, progress_width, 28)
    draw_preset_tag(screen, tiny_font, phase_rect, phase_label, (247, 239, 223), PALETTE["panel_dark"])
    draw_preset_tag(screen, tiny_font, progress_rect, progress_label, (255, 241, 224), PALETTE["gold_dark"])


def filter_weight_effects(effects, filter_mode="all"):
    filtered = []
    for effect in effects:
        is_custom = bool(effect.get("is_custom")) or bool(effect.get("custom_only"))
        if filter_mode == "builtin" and is_custom:
            continue
        if filter_mode == "custom" and not is_custom:
            continue
        filtered.append(effect)
    return filtered


def resize_names(names, count):
    resized = list(names[: max(1, count)])
    while len(resized) < max(1, count):
        resized.append(placeholder_name(len(resized)))
    return resized


def resize_flags(flags, count):
    resized = [bool(flag) for flag in list(flags[: max(1, count)])]
    while len(resized) < max(1, count):
        resized.append(False)
    return resized


def make_players(names, bot_flags=None, ai_level="normal"):
    players = []
    for index, name in enumerate(names):
        players.append(Player(name.strip() or placeholder_name(index), is_bot=False, avatar_variant="angel"))
    return players


def get_first_human_name(names, bot_flags):
    bot_flags = resize_flags(bot_flags or [], len(names))
    for index, name in enumerate(names):
        if not bot_flags[index]:
            return str(name).strip() or placeholder_name(index)
    if names:
        return str(names[0]).strip() or placeholder_name(0)
    return placeholder_name(0)


def build_mode_session_options(mode_data):
    mode_variant = str(mode_data.get("mode_variant", "standard") or "standard")
    session_options = {
        "layout_id": str(mode_data.get("layout_id", "classic")),
        "match_preset": "custom",
        "mode_variant": mode_variant,
    }
    if mode_variant == "best_of_three":
        session_options["series_target_wins"] = 2
    elif mode_variant == "challenge":
        session_options["challenge_id"] = str(mode_data.get("challenge_id", "custom_challenge"))
        session_options["challenge_title"] = str(mode_data.get("challenge_title", mode_data.get("name", "Custom Challenge")))
    return session_options


def build_players_for_mode(mode_data, bot_flags):
    names = mode_data["player_names"]
    return make_players(names)


def make_state(mode=None):
    if not mode:
        return {
            "original_name": None,
            "mode_name": "",
            "num_players_text": "2",
            "player_names": resize_names([], 2),
            "player_bot_flags": resize_flags([], 2),
            "num_boxes_text": "50",
            "turn_mode": SEQUENTIAL_TURN_MODE,
            "layout_id": "classic",
            "ai_level": "normal",
            "mode_variant": "standard",
            "weights": build_default_weight_map(include_custom=True),
        }

    player_specs = mode.get("player_specs")
    if isinstance(player_specs, list) and player_specs:
        names = [str(spec.get("name", "")).strip() or placeholder_name(index) for index, spec in enumerate(player_specs)]
        bot_flags = [bool(spec.get("is_bot", False)) for spec in player_specs]
    else:
        names = [str(name) for name in mode.get("player_names", []) if str(name).strip()]
        bot_flags = resize_flags([], len(names) or 2)
    if not names:
        names = resize_names([], 2)
        bot_flags = resize_flags([], 2)
    return {
        "original_name": str(mode.get("name", "")).strip(),
        "mode_name": str(mode.get("name", "")).strip(),
        "num_players_text": str(len(names)),
        "player_names": names,
        "player_bot_flags": resize_flags([], len(names)),
        "num_boxes_text": str(mode.get("num_boxes", 50)),
        "turn_mode": normalize_turn_mode(mode.get("turn_mode")),
        "layout_id": str(mode.get("layout_id", "classic")),
        "ai_level": "normal",
        "mode_variant": "standard" if str(mode.get("mode_variant", "standard") or "standard") == "solo_bot" else str(mode.get("mode_variant", "standard") or "standard"),
        "weights": sanitize_weights(mode.get("weights"), include_custom=True),
    }


def make_effect_editor():
    return {
        "name": "",
        "value_text": "10",
        "operation": CUSTOM_EFFECT_OPERATION_OPTIONS[0]["id"],
        "field": "name",
        "value_pristine": True,
    }


def valid_number(text):
    return text.isdigit() and int(text) > 0


def valid_positive_number(text):
    try:
        return float(text) > 0
    except (TypeError, ValueError):
        return False


def append_numeric_fragment(text, fragment, allow_decimal=False):
    updated = str(text)
    for char in fragment:
        if char.isdigit():
            updated += char
        elif allow_decimal and char == "." and "." not in updated:
            updated = f"{updated}0." if not updated else f"{updated}."
    return updated


def name_exists(mode_name, original_name):
    for mode in load_custom_modes():
        current = str(mode.get("name", "")).strip()
        if current == mode_name and current != original_name:
            return True
    return False


CUSTOM_MODE_FILTER_OPTIONS = [
    ("all", "Tất cả"),
    ("human", "Toàn người"),
    ("challenge", "Thử thách"),
    ("series", "Best of 3"),
]


def extract_preset_roster(preset):
    player_specs = preset.get("player_specs")
    if isinstance(player_specs, list) and player_specs:
        names = [str(spec.get("name", "")).strip() for spec in player_specs if str(spec.get("name", "")).strip()]
        bot_flags = [bool(spec.get("is_bot", False)) for spec in player_specs][: len(names)]
    else:
        names = [str(name).strip() for name in preset.get("player_names", []) if str(name).strip()]
        bot_flags = resize_flags([], len(names))
    return names, resize_flags(bot_flags, len(names))


def filter_custom_mode_presets(presets, filter_mode="all"):
    filtered = []
    for preset in presets:
        names, bot_flags = extract_preset_roster(preset)
        mode_variant = str(preset.get("mode_variant", "standard") or "standard")
        if mode_variant == "solo_bot":
            mode_variant = "standard"
        if filter_mode == "challenge" and mode_variant != "challenge":
            continue
        if filter_mode == "series" and mode_variant != "best_of_three":
            continue
        filtered.append((preset, names, bot_flags))
    return filtered


def keep_selected_card_visible(scroll_y, selected_index, card_height, card_gap, viewport_height):
    if selected_index < 0:
        return max(0, scroll_y)
    item_offset = selected_index * (card_height + card_gap)
    item_bottom = item_offset + card_height
    if item_offset < scroll_y:
        return item_offset
    if item_bottom > scroll_y + viewport_height:
        return max(0, item_bottom - viewport_height)
    return max(0, scroll_y)


def build_preset_launch_payload(preset):
    names, bot_flags = extract_preset_roster(preset)
    num_boxes = int(preset.get("num_boxes", 0))
    if not names or num_boxes <= 0:
        return None

    turn_mode = normalize_turn_mode(preset.get("turn_mode"))

    mode_data = dict(preset)
    mode_data["player_names"] = names
    mode_data["mode_variant"] = "standard" if str(preset.get("mode_variant", "standard") or "standard") == "solo_bot" else str(preset.get("mode_variant", "standard") or "standard")
    return (
        build_players_for_mode(mode_data, bot_flags),
        num_boxes,
        "custom",
        sanitize_weights(preset.get("weights"), include_custom=True),
        turn_mode,
        build_mode_session_options(mode_data),
    )


def build_mode_data(state):
    mode_variant = str(state.get("mode_variant", "standard") or "standard")
    if mode_variant == "solo_bot":
        mode_variant = "standard"
    return {
        "name": state["mode_name"].strip(),
        "player_names": [name.strip() for name in state["player_names"]],
        "player_specs": [
            {
                "name": name.strip(),
                "is_bot": False,
            }
            for index, name in enumerate(state["player_names"])
        ],
        "num_boxes": int(state["num_boxes_text"]),
        "turn_mode": normalize_turn_mode(state.get("turn_mode")),
        "layout_id": str(state.get("layout_id", "classic")),
        "ai_level": "normal",
        "mode_variant": mode_variant,
        "challenge_id": "custom_challenge" if mode_variant == "challenge" else "",
        "challenge_title": state["mode_name"].strip() if mode_variant == "challenge" else "",
        "weights": sanitize_weights(state["weights"], include_custom=True),
    }


def focus_player_field(state, index):
    if 0 <= index < len(state["player_names"]) and state["player_names"][index] == placeholder_name(index):
        state["player_names"][index] = ""
    return index


def set_mode_player_count(state, editing, count, focus_new=False):
    previous_count = len(state["player_names"])
    state["player_names"] = resize_names(state["player_names"], count)
    state["player_bot_flags"] = resize_flags(state["player_bot_flags"], len(state["player_names"]))
    state["num_players_text"] = str(len(state["player_names"]))
    if focus_new and len(state["player_names"]) > previous_count:
        return focus_player_field(state, len(state["player_names"]) - 1)
    return min(editing, len(state["player_names"]) - 1)


def clear_all_mode_bots(state):
    state["player_bot_flags"] = [False for _ in state["player_bot_flags"]]


def resolve_custom_mode_snapshot(state, effective_turn_mode=None):
    layout_id = str(state.get("layout_id", "classic") or "classic")
    layout_info = BOARD_LAYOUTS.get(layout_id, BOARD_LAYOUTS["classic"])
    mode_variant = str(state.get("mode_variant", "standard") or "standard")
    if mode_variant == "solo_bot":
        mode_variant = "standard"
    slot_count = len(state.get("player_names", []))
    try:
        num_boxes = max(1, int(state.get("num_boxes_text", "0")))
    except (TypeError, ValueError):
        num_boxes = 0
    turn_mode = normalize_turn_mode(effective_turn_mode or state.get("turn_mode"))
    return {
        "mode_label": MODE_VARIANTS.get(mode_variant, MODE_VARIANTS["standard"])["label"],
        "layout_label": layout_info["label"],
        "layout_columns": int(layout_info["columns"]),
        "num_boxes": num_boxes,
        "turn_label": TURN_MODE_LABELS.get(turn_mode, TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE]),
        "slot_count": slot_count,
    }


def draw_custom_mode_snapshot_card(surface, rect, snapshot, title_font, body_font, tiny_font):
    draw_panel(surface, rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
    preview_rect = pygame.Rect(rect.x + 10, rect.y + 7, 62, rect.height - 14)
    draw_layout_preview(surface, preview_rect, snapshot["num_boxes"], snapshot["layout_columns"], active=True)
    title_copy = clamp_text(title_font, f"{snapshot['mode_label']} | {snapshot['num_boxes']} o | {snapshot['layout_label']}", rect.width - 94)
    detail_copy = clamp_text(
        body_font,
        f"{snapshot['turn_label']} | {snapshot['slot_count']} slot",
        rect.width - 94,
    )
    surface.blit(title_font.render(title_copy, True, PALETTE["text"]), (rect.x + 82, rect.y + 8))
    surface.blit(body_font.render(detail_copy, True, PALETTE["muted"]), (rect.x + 82, rect.y + 25))
    footer_copy = clamp_text(tiny_font, "Preview nhanh cho custom mode hiện tại.", rect.width - 94)
    surface.blit(tiny_font.render(footer_copy, True, PALETTE["muted"]), (rect.x + 82, rect.bottom - 15))


def apply_custom_turn_hotkey(state, key):
    if key == pygame.K_a:
        state["turn_mode"] = SEQUENTIAL_TURN_MODE
        return True
    if key == pygame.K_s:
        state["turn_mode"] = MANUAL_TURN_MODE
        return True

    layout_ids = list(BOARD_LAYOUTS)
    if key in (pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r):
        index = [pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_r].index(key)
        if index < len(layout_ids):
            state["layout_id"] = layout_ids[index]
            return True
    return False


def apply_custom_variant_hotkey(state, key):
    variant_ids = ["standard", "challenge", "best_of_three"]
    if pygame.K_1 <= key <= pygame.K_3:
        index = key - pygame.K_1
        if index < len(variant_ids):
            state["mode_variant"] = variant_ids[index]
            return True
    return False


def handle_backspace(state, phase, editing, effect_editor):
    if phase == "name":
        state["mode_name"] = state["mode_name"][:-1]
    elif phase == "players":
        state["num_players_text"] = state["num_players_text"][:-1]
    elif phase == "names" and state["player_names"]:
        state["player_names"][editing] = state["player_names"][editing][:-1]
    elif phase == "boxes":
        state["num_boxes_text"] = state["num_boxes_text"][:-1]
    elif phase == "effect_editor":
        if effect_editor["field"] == "name":
            effect_editor["name"] = effect_editor["name"][:-1]
        else:
            effect_editor["value_text"] = effect_editor["value_text"][:-1]
            effect_editor["value_pristine"] = False


def focus_effect_editor_field(effect_editor, field_name):
    effect_editor["field"] = field_name
    if field_name == "value" and effect_editor.get("value_pristine", False):
        effect_editor["value_text"] = ""
        effect_editor["value_pristine"] = False
    return effect_editor


def build_effect_description(effect):
    if effect.get("custom_only"):
        return "Hiệu ứng đặc biệt | chỉ có trong custom"
    if effect.get("is_custom"):
        operation_label = CUSTOM_EFFECT_OPERATION_LABELS.get(effect.get("operation"), effect.get("operation", "custom"))
        value = float(effect.get("value", 0))
        value_text = str(int(value)) if value.is_integer() else f"{value:.1f}"
        return f"{operation_label} | gia tri {value_text}"
    return "Hiệu ứng có sẵn"


def run_custom_mode_ui():
    pygame.init()
    pygame.key.start_text_input()
    settings = load_settings()
    screen = create_display(CUSTOM_WINDOW_SIZE, "Chế độ custom", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()
    title_font = get_font(27)
    font = get_font(16, ui=True, bold=True)
    small_font = get_font(12, ui=True)
    tiny_font = get_font(11, ui=True)
    clock = pygame.time.Clock()

    phase = "list"
    state = make_state()
    effect_editor = make_effect_editor()
    editing = 0
    scroll_y = 0
    active_list_filter = "all"
    selected_list_index = 0
    weights_filter = "all"
    error = ""
    last_tab_time = 0
    backspace_held = False
    backspace_repeat_delay = 170
    backspace_repeat_interval = 24
    next_backspace_time = 0

    while True:
        presets = load_custom_modes()
        filtered_presets = filter_custom_mode_presets(presets, active_list_filter)
        if filtered_presets:
            selected_list_index = max(0, min(selected_list_index, len(filtered_presets) - 1))
        else:
            selected_list_index = 0
        draw_background(screen, pygame.time.get_ticks())
        draw_panel(
            screen,
            pygame.Rect(28, 20, screen.get_width() - 56, screen.get_height() - 40),
            fill_color=(248, 241, 225),
            border_color=PALETTE["gold_dark"],
            radius=28,
        )
        draw_phase_badges(screen, font, tiny_font, phase)

        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        current_time = pygame.time.get_ticks()
        caret_visible = (current_time // 500) % 2 == 0
        max_scroll = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None, None, None, None, None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True
                elif phase in {"list", "weights"} and event.button == 4:
                    scroll_y = max(0, scroll_y - 40)
                elif phase in {"list", "weights"} and event.button == 5:
                    scroll_y += 40
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if phase == "list":
                        return None, None, None, None, None, None
                    phase = {
                        "save": "weights",
                        "weights": "turn_mode",
                        "turn_mode": "boxes",
                        "boxes": "names",
                        "names": "players",
                        "players": "name",
                        "name": "list",
                        "effect_editor": "weights",
                    }[phase]
                    if phase == "weights":
                        state["weights"] = sanitize_weights(state["weights"], include_custom=True)
                    refresh_text_input()
                    error = ""
                elif phase == "list":
                    if pygame.K_1 <= event.key <= pygame.K_4:
                        active_list_filter = CUSTOM_MODE_FILTER_OPTIONS[event.key - pygame.K_1][0]
                        selected_list_index = 0
                        scroll_y = 0
                    elif event.key == pygame.K_n:
                        state, editing, error, phase = make_state(), 0, "", "name"
                        scroll_y = 0
                        refresh_text_input()
                    elif event.key in (pygame.K_UP, pygame.K_w) and filtered_presets:
                        selected_list_index = max(0, selected_list_index - 1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s) and filtered_presets:
                        selected_list_index = min(len(filtered_presets) - 1, selected_list_index + 1)
                    elif event.key == pygame.K_HOME and filtered_presets:
                        selected_list_index = 0
                    elif event.key == pygame.K_END and filtered_presets:
                        selected_list_index = len(filtered_presets) - 1
                    elif event.key == pygame.K_PAGEUP:
                        scroll_y = max(0, scroll_y - 220)
                    elif event.key == pygame.K_PAGEDOWN:
                        scroll_y += 220
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and filtered_presets:
                        launch_payload = build_preset_launch_payload(filtered_presets[selected_list_index][0])
                        if launch_payload:
                            return launch_payload
                    elif event.key == pygame.K_e and filtered_presets:
                        state, editing, error, phase = make_state(filtered_presets[selected_list_index][0]), 0, "", "name"
                        scroll_y = 0
                        refresh_text_input()
                    elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and filtered_presets:
                        delete_custom_mode(str(filtered_presets[selected_list_index][0].get("name", "")).strip())
                        selected_list_index = max(0, selected_list_index - 1)
                elif phase == "name":
                    if event.key == pygame.K_RETURN and state["mode_name"].strip():
                        phase = "players"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "players":
                    if event.key == pygame.K_RETURN and valid_number(state["num_players_text"]):
                        state["player_names"] = resize_names(state["player_names"], int(state["num_players_text"]))
                        state["player_bot_flags"] = resize_flags(state["player_bot_flags"], int(state["num_players_text"]))
                        editing = focus_player_field(state, 0)
                        phase = "names"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "names":
                    if event.key == pygame.K_TAB:
                        now = pygame.time.get_ticks()
                        if now - last_tab_time >= 180 and state["player_names"]:
                            editing = focus_player_field(state, (editing + 1) % len(state["player_names"]))
                            refresh_text_input()
                            last_tab_time = now
                    elif event.key in (pygame.K_2, pygame.K_4, pygame.K_6, pygame.K_8):
                        editing = set_mode_player_count(state, editing, int(event.unicode), focus_new=False)
                        clear_all_mode_bots(state)
                        refresh_text_input()
                    elif event.key == pygame.K_RETURN and all(name.strip() for name in state["player_names"]):
                        phase = "boxes"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "boxes":
                    if event.key == pygame.K_RETURN and valid_number(state["num_boxes_text"]):
                        phase = "turn_mode"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "turn_mode":
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        state["turn_mode"] = SEQUENTIAL_TURN_MODE
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_TAB):
                        state["turn_mode"] = MANUAL_TURN_MODE
                    elif apply_custom_turn_hotkey(state, event.key):
                        pass
                    elif event.key == pygame.K_RETURN:
                        phase = "weights"
                        scroll_y = 0
                elif phase == "weights":
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        weights_filter = WEIGHT_FILTER_OPTIONS[event.key - pygame.K_1][0]
                        scroll_y = 0
                    elif event.key == pygame.K_RETURN:
                        if any(weight > 0 for weight in state["weights"].values()):
                            phase = "save"
                        else:
                            error = "Phai co it nhat mot ti le > 0."
                elif phase == "effect_editor":
                    if event.key == pygame.K_TAB:
                        next_field = "value" if effect_editor["field"] == "name" else "name"
                        focus_effect_editor_field(effect_editor, next_field)
                        refresh_text_input()
                    elif event.key == pygame.K_RETURN:
                        if effect_editor["name"].strip() and valid_positive_number(effect_editor["value_text"]):
                            saved_effect = save_custom_effect(
                                {
                                    "name": effect_editor["name"].strip(),
                                    "operation": effect_editor["operation"],
                                    "value": float(effect_editor["value_text"]),
                                }
                            )
                            state["weights"][str(saved_effect["id"])] = 1.0
                            state["weights"] = sanitize_weights(state["weights"], include_custom=True)
                            phase = "weights"
                            effect_editor = make_effect_editor()
                            error = ""
                        else:
                            error = "Nhập tên và giá trị hợp lệ cho hiệu ứng mới."
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "save" and apply_custom_variant_hotkey(state, event.key):
                    pass
            elif event.type == pygame.TEXTINPUT:
                if phase == "name":
                    state["mode_name"] += event.text
                elif phase == "players":
                    state["num_players_text"] = append_numeric_fragment(state["num_players_text"], event.text)
                elif phase == "names" and state["player_names"]:
                    state["player_names"][editing] += event.text
                elif phase == "boxes":
                    state["num_boxes_text"] = append_numeric_fragment(state["num_boxes_text"], event.text)
                elif phase == "effect_editor":
                    if effect_editor["field"] == "name":
                        effect_editor["name"] += event.text
                    else:
                        if effect_editor.get("value_pristine", False):
                            effect_editor["value_text"] = ""
                            effect_editor["value_pristine"] = False
                        effect_editor["value_text"] = append_numeric_fragment(
                            effect_editor["value_text"],
                            event.text,
                            allow_decimal=True,
                        )
            elif event.type == pygame.KEYUP and event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                backspace_held = False

        if backspace_held and current_time >= next_backspace_time:
            handle_backspace(state, phase, editing, effect_editor)
            next_backspace_time = current_time + backspace_repeat_interval

        if phase == "list" and filtered_presets:
            viewport_height = screen.get_height() - 214 - 118
            scroll_y = keep_selected_card_visible(scroll_y, selected_list_index, 126, 16, viewport_height)

        if phase == "list":
            screen.blit(title_font.render("Chế độ custom", True, (0, 0, 0)), (60, 28))
            screen.blit(small_font.render("Chọn preset đã lưu, lọc nhanh và vào trận ngay.", True, (90, 90, 90)), (60, 62))
            new_rect = pygame.Rect(766, 44, 180, 42)
            back_rect = pygame.Rect(960, 44, 120, 42)
            draw_button(screen, font, new_rect, "Tao moi", (100, 200, 100))
            draw_button(screen, font, back_rect, "Quay lại", (220, 120, 120))

            filter_rects = []
            chip_x = 60
            chip_y = 108
            chip_widths = {"all": 84, "human": 126, "challenge": 126, "series": 116}
            for filter_key, label in CUSTOM_MODE_FILTER_OPTIONS:
                rect = pygame.Rect(chip_x, chip_y, chip_widths[filter_key], 32)
                draw_filter_chip(screen, tiny_font, rect, label, active=active_list_filter == filter_key, hovered=rect.collidepoint(mouse_pos))
                filter_rects.append((filter_key, rect))
                chip_x = rect.right + 10

            play_buttons, edit_buttons, delete_buttons = [], [], []
            card_clicks = []
            card_top, card_height, card_gap = 160, 126, 16
            content_bottom = screen.get_height() - 110
            card_area_width = screen.get_width() - 142
            if not presets:
                screen.blit(font.render("Chưa có chế độ nào được lưu.", True, (90, 90, 90)), (60, 220))
            elif not filtered_presets:
                empty_rect = pygame.Rect(60, 212, screen.get_width() - 132, 118)
                draw_panel(screen, empty_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=22, shadow=False)
                empty_copy = "Bo loc nay chua co preset nao. Nhan 1-4 de doi bo loc hoac N de tao moi."
                screen.blit(font.render(clamp_text(font, empty_copy, empty_rect.width - 40), True, (90, 90, 90)), (empty_rect.x + 20, empty_rect.y + 40))
            else:
                y = card_top - scroll_y
                for preset_index, (preset, names, bot_flags) in enumerate(filtered_presets):
                    rect = pygame.Rect(60, y, card_area_width, card_height)
                    if rect.bottom >= card_top and rect.top <= content_bottom:
                        hovered = rect.collidepoint(mouse_pos)
                        selected = preset_index == selected_list_index or hovered
                        if hovered:
                            selected_list_index = preset_index

                        fill_color = (250, 244, 231) if selected else (247, 239, 223)
                        border_color = PALETTE["gold_dark"] if selected else PALETTE["panel_dark"]
                        if selected:
                            draw_glow(screen, rect.center, PALETTE["gold"], max(56, rect.width // 2), 12)
                        draw_panel(screen, rect, fill_color=fill_color, border_color=border_color, radius=20, shadow=False)

                        layout_info = BOARD_LAYOUTS.get(str(preset.get("layout_id", "classic")), BOARD_LAYOUTS["classic"])
                        preview_rect = pygame.Rect(rect.x + 18, rect.y + 18, 84, 62)
                        draw_layout_preview(screen, preview_rect, preset.get("num_boxes", 0), layout_info["columns"], active=selected)

                        button_x = rect.right - 108
                        text_x = preview_rect.right + 16
                        text_width = max(120, button_x - text_x - 18)
                        mode_variant = str(preset.get("mode_variant", "standard") or "standard")
                        turn_mode_label = TURN_MODE_LABELS[normalize_turn_mode(preset.get("turn_mode"))]
                        mode_label = MODE_VARIANTS.get(mode_variant, MODE_VARIANTS["standard"])["label"]
                        player_label = "Toan nguoi"
                        summary = f"{len(names)} slot | {preset.get('num_boxes', 0)} o | {turn_mode_label} | {layout_info['label']}"
                        roster_preview = ", ".join(names[:4]) + (" ..." if len(names) > 4 else "")

                        name_copy = clamp_text(font, str(preset.get("name", "Preset")), text_width)
                        summary_copy = clamp_text(small_font, summary, text_width)
                        roster_copy = clamp_text(small_font, roster_preview or "Chưa có tên người chơi", text_width)
                        screen.blit(font.render(name_copy, True, (0, 0, 0)), (text_x, rect.y + 14))
                        screen.blit(small_font.render(summary_copy, True, (90, 90, 90)), (text_x, rect.y + 44))
                        screen.blit(small_font.render(roster_copy, True, (90, 90, 90)), (text_x, rect.y + 68))

                        mode_tag_width = min(138, tiny_font.size(mode_label)[0] + 22)
                        roster_tag_width = min(118, tiny_font.size(player_label)[0] + 22)
                        mode_rect = pygame.Rect(text_x, rect.bottom - 30, mode_tag_width, 22)
                        roster_rect = pygame.Rect(mode_rect.right + 8, rect.bottom - 30, roster_tag_width, 22)
                        draw_preset_tag(screen, tiny_font, mode_rect, mode_label, (255, 241, 224), PALETTE["gold_dark"])
                        draw_preset_tag(
                            screen,
                            tiny_font,
                            roster_rect,
                            player_label,
                            (231, 245, 236),
                            PALETTE["mint_dark"],
                        )

                        play_rect = pygame.Rect(button_x, rect.y + 16, 84, 28)
                        edit_rect = pygame.Rect(button_x, rect.y + 50, 84, 28)
                        delete_rect = pygame.Rect(button_x, rect.y + 84, 84, 28)
                        draw_button(screen, small_font, play_rect, "Choi", (100, 200, 100))
                        draw_button(screen, small_font, edit_rect, "Sua", (120, 180, 230))
                        draw_button(screen, small_font, delete_rect, "Xoa", (220, 120, 120))
                        play_buttons.append((preset, play_rect))
                        edit_buttons.append((preset, edit_rect))
                        delete_buttons.append((preset, delete_rect))
                        card_clicks.append((preset_index, rect))
                    y += card_height + card_gap
                max_scroll = max(0, len(filtered_presets) * (card_height + card_gap) - (content_bottom - card_top))
                scroll_y = max(0, min(scroll_y, max_scroll))
                draw_scrollbar(
                    screen,
                    pygame.Rect(screen.get_width() - 38, card_top, 10, content_bottom - card_top),
                    len(filtered_presets) * (card_height + card_gap),
                    content_bottom - card_top,
                    scroll_y,
                    accent_color=PALETTE["gold_dark"],
                )

            if filtered_presets:
                selected_preset, selected_names, selected_bot_flags = filtered_presets[selected_list_index]
                selected_label = str(selected_preset.get("name", "Preset")).strip() or "Preset"
                status_copy = f"Dang chon {selected_label} | {len(filtered_presets)}/{len(presets)} preset | Enter choi | E sua | Delete xoa | N tao moi"
            else:
                status_copy = "N tao moi | 1-4 de loc preset | bo loc nay dang trong"
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, screen.get_height() - 82, screen.get_width() - 120, 30), status_copy)

            if mouse_clicked:
                if new_rect.collidepoint(mouse_pos):
                    state, editing, error, phase = make_state(), 0, "", "name"
                    scroll_y = 0
                    refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    return None, None, None, None, None, None
                else:
                    filter_handled = False
                    for filter_key, rect in filter_rects:
                        if rect.collidepoint(mouse_pos):
                            active_list_filter = filter_key
                            selected_list_index = 0
                            scroll_y = 0
                            filter_handled = True
                            break
                    if not filter_handled:
                        for preset, rect in play_buttons:
                            if rect.collidepoint(mouse_pos):
                                launch_payload = build_preset_launch_payload(preset)
                                if launch_payload:
                                    return launch_payload
                        for preset, rect in edit_buttons:
                            if rect.collidepoint(mouse_pos):
                                state, editing, error, phase = make_state(preset), 0, "", "name"
                                scroll_y = 0
                                refresh_text_input()
                        for preset, rect in delete_buttons:
                            if rect.collidepoint(mouse_pos):
                                delete_custom_mode(str(preset.get("name", "")).strip())
                        for preset_index, rect in card_clicks:
                            if rect.collidepoint(mouse_pos):
                                selected_list_index = preset_index
                                break

        elif phase == "name":
            screen.blit(font.render("Dat ten che do", True, (0, 0, 0)), (60, 40))
            draw_box(screen, font, pygame.Rect(60, 120, 520, 46), state["mode_name"], True, caret_visible)
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 182, 560, 28), "Nhập tên preset để phân biệt dễ hơn | Enter để sang bước tiếp")
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiếp", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    error = "" if state["mode_name"].strip() else "Ten che do khong duoc de trong."
                    if not error:
                        phase = "players"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "list", ""
                    refresh_text_input()

        elif phase == "players":
            screen.blit(font.render("So nguoi choi", True, (0, 0, 0)), (60, 40))
            draw_box(screen, font, pygame.Rect(60, 120, 200, 46), state["num_players_text"], True, caret_visible)
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 182, 470, 28), "Nhập số slot bạn muốn tạo | Enter để sang bước đặt tên")
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiếp", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    if valid_number(state["num_players_text"]):
                        state["player_names"] = resize_names(state["player_names"], int(state["num_players_text"]))
                        state["player_bot_flags"] = resize_flags(state["player_bot_flags"], int(state["num_players_text"]))
                        editing, error, phase = focus_player_field(state, 0), "", "names"
                    else:
                        error = "So nguoi choi khong hop le."
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "name", ""
                    refresh_text_input()

        elif phase == "names":
            screen.blit(font.render("Người chơi", True, (0, 0, 0)), (60, 24))
            minus_rect = pygame.Rect(60, 90, 45, 38)
            plus_rect = pygame.Rect(185, 90, 45, 38)
            count_rect = pygame.Rect(115, 90, 60, 38)
            draw_button(screen, font, minus_rect, "-", (230, 230, 230))
            draw_box(screen, font, count_rect, str(len(state["player_names"])))
            draw_button(screen, font, plus_rect, "+", (230, 230, 230))
            quick_label = small_font.render("Preset nhanh cho van nguoi voi nguoi", True, (90, 90, 90))
            screen.blit(quick_label, (262, 100))
            preset_rects = []
            for preset_index, count in enumerate((2, 4, 6, 8)):
                rect = pygame.Rect(566 + preset_index * 74, 92, 64, 34)
                active = len(state["player_names"]) == count
                draw_button(
                    screen,
                    small_font,
                    rect,
                    f"{count} nguoi",
                    (247, 223, 184) if active else (241, 234, 221),
                    (0, 0, 0),
                    PALETTE["gold_dark"] if active else PALETTE["panel_dark"],
                )
                preset_rects.append((count, rect))
            humans_only_rect = pygame.Rect(-200, -200, 1, 1)
            all_human_active = False
            draw_button(
                screen,
                small_font,
                humans_only_rect,
                "Tất cả là người",
                (231, 245, 236) if all_human_active else (241, 234, 221),
                (0, 0, 0),
                PALETTE["mint_dark"] if all_human_active else PALETTE["panel_dark"],
            )
            name_rects = []
            for index, name in enumerate(state["player_names"]):
                x = 60 + (index % 4) * 238
                y = 176 + (index // 4) * 60
                rect = pygame.Rect(x, y, 220, 42)
                toggle_rect = pygame.Rect(-200, -200, 1, 1)
                draw_box(screen, font, rect, name, index == editing, index == editing and caret_visible)
                toggle_label = "BOT" if state["player_bot_flags"][index] else "Người"
                toggle_fill = (244, 217, 223) if state["player_bot_flags"][index] else (225, 241, 230)
                toggle_border = PALETTE["crimson_dark"] if state["player_bot_flags"][index] else PALETTE["mint_dark"]
                draw_button(screen, small_font, toggle_rect, toggle_label, toggle_fill, (0, 0, 0), toggle_border)
                name_rects.append((index, rect, toggle_rect))
            hint_copy = "Tab de doi o, click de chon nhanh. Van nguoi voi nguoi dang la luong chinh."
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 584, 960, 30), hint_copy)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiếp", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if minus_rect.collidepoint(mouse_pos) and len(state["player_names"]) > 1:
                    editing = set_mode_player_count(state, editing, len(state["player_names"]) - 1)
                elif plus_rect.collidepoint(mouse_pos):
                    editing = set_mode_player_count(state, editing, len(state["player_names"]) + 1, focus_new=True)
                    refresh_text_input()
                elif humans_only_rect.collidepoint(mouse_pos):
                    clear_all_mode_bots(state)
                elif next_rect.collidepoint(mouse_pos):
                    error = "" if all(name.strip() for name in state["player_names"]) else "Hay nhap du ten nguoi choi."
                    if not error:
                        phase = "boxes"
                        refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "players", ""
                    refresh_text_input()
                else:
                    preset_handled = False
                    for count, rect in preset_rects:
                        if rect.collidepoint(mouse_pos):
                            editing = set_mode_player_count(state, editing, count)
                            clear_all_mode_bots(state)
                            refresh_text_input()
                            preset_handled = True
                            break
                    if not preset_handled:
                        for index, rect, toggle_rect in name_rects:
                            if rect.collidepoint(mouse_pos):
                                editing = focus_player_field(state, index)
                                refresh_text_input()
                            elif toggle_rect.collidepoint(mouse_pos):
                                state["player_bot_flags"][index] = not state["player_bot_flags"][index]

        elif phase == "boxes":
            screen.blit(font.render("Số ô may mắn", True, (0, 0, 0)), (60, 40))
            draw_box(screen, font, pygame.Rect(60, 120, 200, 46), state["num_boxes_text"], True, caret_visible)
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 182, 520, 28), "Số ô quyết định độ dài ván | Enter để sang bước luật và layout")
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiếp", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    error = "" if valid_number(state["num_boxes_text"]) else "Số ô không hợp lệ."
                    if not error:
                        phase = "turn_mode"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "names", ""
                    refresh_text_input()

        elif phase == "turn_mode":
            screen.blit(font.render("Kieu den luot", True, (0, 0, 0)), (60, 40))
            screen.blit(small_font.render("Chọn cách xác định người mở ô tiếp theo và layout cho custom mode.", True, (90, 90, 90)), (60, 74))
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 102, 960, 28), "A-S den luot | Q-W-E-R layout | Enter de sang buoc effect")
            sequential_rect = pygame.Rect(60, 140, 460, 130)
            manual_rect = pygame.Rect(560, 140, 460, 130)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            options = [
                (SEQUENTIAL_TURN_MODE, sequential_rect, TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE], "Tu dong quay vong tu nguoi dau den nguoi cuoi."),
                (MANUAL_TURN_MODE, manual_rect, TURN_MODE_LABELS[MANUAL_TURN_MODE], "Người chơi tự click chọn tên trước khi mở ô."),
            ]
            for mode_value, rect, title, description in options:
                active = state["turn_mode"] == mode_value
                disabled = False
                fill_color = (226, 221, 214) if disabled else (244, 230, 186) if active else (234, 226, 210)
                border_color = (156, 150, 146) if disabled else PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(title, True, (0, 0, 0)), (rect.x + 18, rect.y + 20))
                screen.blit(small_font.render(description, True, (80, 80, 80)), (rect.x + 18, rect.y + 68))

            layout_rects = []
            for index, (layout_id, layout) in enumerate(BOARD_LAYOUTS.items()):
                rect = pygame.Rect(60 + (index % 2) * 470, 432 + (index // 2) * 78, 420, 62)
                active = state["layout_id"] == layout_id
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(layout["label"], True, (0, 0, 0)), (rect.x + 16, rect.y + 10))
                layout_detail = f"{layout['description']} | {layout['columns']} cot"
                screen.blit(small_font.render(layout_detail, True, (80, 80, 80)), (rect.x + 16, rect.y + 34))
                preview_rect = pygame.Rect(rect.right - 78, rect.y + 7, 58, 48)
                draw_layout_preview(screen, preview_rect, state["num_boxes_text"], layout["columns"], active=active)
                layout_rects.append((layout_id, rect))

            snapshot_rect = pygame.Rect(60, 598, 460, 52)
            draw_custom_mode_snapshot_card(
                screen,
                snapshot_rect,
                resolve_custom_mode_snapshot(state),
                small_font,
                small_font,
                tiny_font,
            )
            draw_button(screen, font, next_rect, "Tiếp", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if sequential_rect.collidepoint(mouse_pos):
                    state["turn_mode"] = SEQUENTIAL_TURN_MODE
                elif manual_rect.collidepoint(mouse_pos):
                    state["turn_mode"] = MANUAL_TURN_MODE
                elif next_rect.collidepoint(mouse_pos):
                    phase = "weights"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "boxes", ""
                else:
                    for layout_id, rect in layout_rects:
                        if rect.collidepoint(mouse_pos):
                            state["layout_id"] = layout_id

        elif phase == "weights":
            effects = get_all_effects(include_custom=True)
            state["weights"] = sanitize_weights(state["weights"], include_custom=True)
            filtered_effects = filter_weight_effects(effects, weights_filter)
            screen.blit(font.render("Chinh ti le hieu ung", True, (0, 0, 0)), (60, 24))
            screen.blit(small_font.render("8 hieu ung mac dinh + nhom dac biet chi xuat hien o custom.", True, (90, 90, 90)), (60, 58))
            add_effect_rect = pygame.Rect(60, 90, 200, 42)
            reset_rect = pygame.Rect(280, 90, 160, 42)
            draw_button(screen, font, add_effect_rect, "Them effect", (120, 180, 230))
            draw_button(screen, font, reset_rect, "Mặc định", (230, 230, 180))
            filter_rects = []
            filter_x = 470
            filter_widths = {"all": 86, "builtin": 100, "custom": 94}
            for filter_key, label in WEIGHT_FILTER_OPTIONS:
                rect = pygame.Rect(filter_x, 96, filter_widths[filter_key], 30)
                draw_filter_chip(screen, tiny_font, rect, label, active=weights_filter == filter_key, hovered=rect.collidepoint(mouse_pos))
                filter_rects.append((filter_key, rect))
                filter_x = rect.right + 10
            active_weight_count = sum(1 for effect in filtered_effects if state["weights"].get(str(effect["id"]), 0.0) > 0)
            summary_rect = pygame.Rect(788, 96, 232, 30)
            draw_hint_bar(screen, tiny_font, summary_rect, f"Lọc {len(filtered_effects)} effect | đang bật {active_weight_count}", fill_color=(247, 239, 223))

            row_top = 150
            row_height = 58
            row_gap = 12
            visible_bottom = screen.get_height() - 130
            buttons = []
            total = sum(state["weights"].get(str(effect["id"]), 0.0) for effect in effects)
            for index, effect in enumerate(filtered_effects):
                y = row_top + index * (row_height + row_gap) - scroll_y
                if y + row_height < row_top or y > visible_bottom:
                    continue

                row = pygame.Rect(60, y, screen.get_width() - 120, row_height)
                pygame.draw.rect(screen, (255, 255, 255), row, border_radius=10)
                pygame.draw.rect(screen, (0, 0, 0), row, 2, border_radius=10)
                effect_id = str(effect["id"])
                weight = state["weights"].get(effect_id, 0.0)
                percent = 0 if total <= 0 else weight / total * 100
                label = str(effect.get("label", effect_id))
                detail = build_effect_description(effect)
                delete_rect = None
                if effect.get("is_custom"):
                    delete_rect = pygame.Rect(row.right - 252, row.y + 13, 44, 32)
                label_copy = clamp_text(font, f"{label} - {percent:.1f}%", row.width - (296 if delete_rect else 248))
                screen.blit(font.render(label_copy, True, (0, 0, 0)), (row.x + 18, row.y + 8))
                screen.blit(small_font.render(detail, True, (90, 90, 90)), (row.x + 18, row.y + 32))
                if delete_rect is not None:
                    draw_button(screen, tiny_font, delete_rect, "Xóa", (244, 220, 224), (0, 0, 0), PALETTE["crimson_dark"])
                minus_rect = pygame.Rect(row.right - 200, row.y + 13, 40, 32)
                plus_rect = pygame.Rect(row.right - 50, row.y + 13, 40, 32)
                draw_button(screen, font, minus_rect, "-", (230, 230, 230))
                draw_box(screen, font, pygame.Rect(row.right - 150, row.y + 13, 90, 32), f"{weight:.1f}")
                draw_button(screen, font, plus_rect, "+", (230, 230, 230))
                buttons.append((effect_id, minus_rect, plus_rect, delete_rect))

            max_scroll = max(0, len(filtered_effects) * (row_height + row_gap) - (visible_bottom - row_top))
            scroll_y = max(0, min(scroll_y, max_scroll))

            back_rect = pygame.Rect(560, 620, 170, 50)
            next_rect = pygame.Rect(760, 620, 170, 50)
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            draw_button(screen, font, next_rect, "Bắt đầu", (100, 200, 100))
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 582, 520, 28), "1-3 để lọc effect | +/- để chỉnh nhanh | Enter sang bước lưu")
            if mouse_clicked:
                handled = False
                for filter_key, rect in filter_rects:
                    if rect.collidepoint(mouse_pos):
                        weights_filter = filter_key
                        scroll_y = 0
                        handled = True
                        break
                for effect_id, minus_rect, plus_rect, delete_rect in buttons:
                    if handled:
                        break
                    if delete_rect is not None and delete_rect.collidepoint(mouse_pos):
                        delete_custom_effect(effect_id)
                        state["weights"].pop(effect_id, None)
                        state["weights"] = sanitize_weights(state["weights"], include_custom=True)
                        handled = True
                    elif minus_rect.collidepoint(mouse_pos):
                        state["weights"][effect_id] = max(0.0, state["weights"].get(effect_id, 0.0) - 0.5)
                        handled = True
                    elif plus_rect.collidepoint(mouse_pos):
                        state["weights"][effect_id] = state["weights"].get(effect_id, 0.0) + 0.5
                        handled = True
                    if handled:
                        break
                if not handled and add_effect_rect.collidepoint(mouse_pos):
                    effect_editor = make_effect_editor()
                    phase = "effect_editor"
                    refresh_text_input()
                elif not handled and reset_rect.collidepoint(mouse_pos):
                    state["weights"] = build_default_weight_map(include_custom=True)
                elif not handled and back_rect.collidepoint(mouse_pos):
                    phase, error = "turn_mode", ""
                    refresh_text_input()
                elif not handled and next_rect.collidepoint(mouse_pos):
                    error = "" if any(weight > 0 for weight in state["weights"].values()) else "Phai co it nhat mot ti le > 0."
                    if not error:
                        phase = "save"

        elif phase == "effect_editor":
            screen.blit(font.render("Them effect moi", True, (0, 0, 0)), (60, 40))
            screen.blit(small_font.render("Dat ten, chon loai tac dong va gia tri. Co them ca effect chien thuat.", True, (90, 90, 90)), (60, 72))
            name_rect = pygame.Rect(60, 130, 420, 46)
            value_rect = pygame.Rect(60, 210, 180, 46)
            draw_box(screen, font, name_rect, effect_editor["name"], effect_editor["field"] == "name", caret_visible and effect_editor["field"] == "name")
            draw_box(screen, font, value_rect, effect_editor["value_text"], effect_editor["field"] == "value", caret_visible and effect_editor["field"] == "value")
            screen.blit(small_font.render("Ten effect", True, (90, 90, 90)), (60, 108))
            screen.blit(small_font.render("Gia tri / so lan", True, (90, 90, 90)), (60, 188))

            option_rects = []
            option_columns = 3
            option_width = 320
            option_gap_x = 20
            option_gap_y = 52
            option_start_y = 300
            for index, option in enumerate(CUSTOM_EFFECT_OPERATION_OPTIONS):
                x = 60 + (index % option_columns) * (option_width + option_gap_x)
                y = option_start_y + (index // option_columns) * option_gap_y
                rect = pygame.Rect(x, y, option_width, 42)
                active = effect_editor["operation"] == option["id"]
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                draw_button(screen, small_font, rect, option["label"], fill_color, (0, 0, 0), border_color)
                option_rects.append((option["id"], rect))

            option_rows = max(1, (len(CUSTOM_EFFECT_OPERATION_OPTIONS) + option_columns - 1) // option_columns)
            preview_y = option_start_y + option_rows * option_gap_y + 14
            preview_rect = pygame.Rect(60, preview_y, screen.get_width() - 120, 42)
            pygame.draw.rect(screen, (255, 255, 255), preview_rect, border_radius=10)
            pygame.draw.rect(screen, PALETTE["panel_dark"], preview_rect, 2, border_radius=10)
            preview_text = f"Preview: {effect_editor['name'].strip() or 'Effect moi'} | {CUSTOM_EFFECT_OPERATION_LABELS[effect_editor['operation']]} | {effect_editor['value_text'] or '0'}"
            preview_copy = clamp_text(small_font, preview_text, preview_rect.width - 28)
            screen.blit(small_font.render(preview_copy, True, (80, 80, 80)), (preview_rect.x + 14, preview_rect.y + 11))
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, preview_rect.bottom + 12, 620, 28), "Tab để đổi field | Enter lưu effect | Esc trở lại danh sách effect")

            save_y = min(screen.get_height() - 80, preview_rect.bottom + 24)
            save_rect = pygame.Rect(760, save_y, 170, 50)
            back_rect = pygame.Rect(560, save_y, 170, 50)
            draw_button(screen, font, save_rect, "Lưu hiệu ứng", (100, 200, 100))
            draw_button(screen, font, back_rect, "Trở lại", (220, 120, 120))
            if mouse_clicked:
                if name_rect.collidepoint(mouse_pos):
                    focus_effect_editor_field(effect_editor, "name")
                    refresh_text_input()
                elif value_rect.collidepoint(mouse_pos):
                    focus_effect_editor_field(effect_editor, "value")
                    refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    phase = "weights"
                    effect_editor = make_effect_editor()
                    refresh_text_input()
                elif save_rect.collidepoint(mouse_pos):
                    if effect_editor["name"].strip() and valid_positive_number(effect_editor["value_text"]):
                        saved_effect = save_custom_effect(
                            {
                                "name": effect_editor["name"].strip(),
                                "operation": effect_editor["operation"],
                                "value": float(effect_editor["value_text"]),
                            }
                        )
                        state["weights"][str(saved_effect["id"])] = 1.0
                        state["weights"] = sanitize_weights(state["weights"], include_custom=True)
                        phase = "weights"
                        effect_editor = make_effect_editor()
                        refresh_text_input()
                        error = ""
                    else:
                        error = "Nhập tên và giá trị hợp lệ cho hiệu ứng mới."
                else:
                    for operation_id, rect in option_rects:
                        if rect.collidepoint(mouse_pos):
                            effect_editor["operation"] = operation_id
                            break

        elif phase == "save":
            screen.blit(font.render("Lưu chế độ này?", True, (0, 0, 0)), (60, 60))
            effective_turn_mode = state["turn_mode"]
            snapshot_rect = pygame.Rect(60, 104, 700, 52)
            draw_custom_mode_snapshot_card(
                screen,
                snapshot_rect,
                resolve_custom_mode_snapshot(state, effective_turn_mode),
                small_font,
                small_font,
                tiny_font,
            )
            lines = [
                f"Ten che do: {state['mode_name'].strip()}",
                f"So nguoi choi: {len(state['player_names'])}",
                f"Số ô: {state['num_boxes_text']}",
                f"Kiểu đến lượt: {TURN_MODE_LABELS[effective_turn_mode]}",
                f"Layout: {BOARD_LAYOUTS.get(state['layout_id'], BOARD_LAYOUTS['classic'])['label']}",
            ]
            for index, line in enumerate(lines):
                line_copy = clamp_text(font, line, screen.get_width() - 120)
                screen.blit(font.render(line_copy, True, (0, 0, 0)), (60, 168 + index * 36))

            mode_rects = []
            primary_mode_ids = ["standard", "challenge", "best_of_three"]
            for index, mode_id in enumerate(primary_mode_ids):
                mode_data = MODE_VARIANTS[mode_id]
                rect = pygame.Rect(60 + index * 270, 362, 242, 64)
                active = state["mode_variant"] == mode_id
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(mode_data["label"], True, (0, 0, 0)), (rect.x + 14, rect.y + 10))
                screen.blit(small_font.render(mode_data["description"], True, (90, 90, 90)), (rect.x + 14, rect.y + 36))
                mode_rects.append((mode_id, rect))

            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 432, 940, 24), "1-3 che do chinh | van custom nay danh cho nguoi voi nguoi")
            draw_hint_bar(screen, tiny_font, pygame.Rect(60, 534, 700, 28), "Enter để chơi và lưu nhanh | Chơi lần này sẽ bỏ qua bước lưu preset vào danh sách")

            save_rect = pygame.Rect(60, 468, 220, 54)
            play_rect = pygame.Rect(300, 468, 220, 54)
            back_rect = pygame.Rect(540, 468, 220, 54)
            draw_button(screen, font, save_rect, "Choi va luu", (100, 200, 100))
            draw_button(screen, font, play_rect, "Chi choi lan nay", (120, 180, 230))
            draw_button(screen, font, back_rect, "Quay lại", (220, 120, 120))
            if mouse_clicked:
                handled_mode = False
                for mode_id, rect in mode_rects:
                    if rect.collidepoint(mouse_pos):
                        state["mode_variant"] = mode_id
                        handled_mode = True
                        break
                if handled_mode:
                    pass
                elif save_rect.collidepoint(mouse_pos):
                    mode_name = state["mode_name"].strip()
                    if not mode_name:
                        error = "Ten che do khong duoc de trong."
                    elif name_exists(mode_name, state["original_name"]):
                        error = "Ten che do da ton tai. Hay dat ten khac."
                    else:
                        mode = build_mode_data(state)
                        save_custom_mode(mode, state["original_name"])
                        return (
                            build_players_for_mode(mode, state["player_bot_flags"]),
                            mode["num_boxes"],
                            "custom",
                            mode["weights"],
                            effective_turn_mode,
                            build_mode_session_options(mode),
                        )
                elif play_rect.collidepoint(mouse_pos):
                    mode = build_mode_data(state)
                    return (
                        build_players_for_mode(mode, state["player_bot_flags"]),
                        mode["num_boxes"],
                        "custom",
                        mode["weights"],
                        effective_turn_mode,
                        build_mode_session_options(mode),
                    )
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "weights", ""

        if error:
            screen.blit(font.render(error, True, (200, 30, 30)), (60, screen.get_height() - 40))

        pygame.display.flip()
        clock.tick(60)
