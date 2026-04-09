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
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_panel


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_font(size=20):
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    return pygame.font.Font(font_path, size)


def placeholder_name(index):
    return f"Nguoi {index + 1}"


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
    bot_flags = resize_flags(bot_flags or [], len(names))
    players = []
    for index, name in enumerate(names):
        players.append(
            Player(
                name.strip(),
                is_bot=bot_flags[index],
                ai_level=ai_level,
                avatar_variant="demon" if bot_flags[index] else "angel",
            )
        )
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
    mode_variant = str(mode_data.get("mode_variant", "standard") or "standard")
    names = mode_data["player_names"]
    ai_level = mode_data["ai_level"]
    if mode_variant == "solo_bot":
        human_name = get_first_human_name(names, bot_flags)
        return [
            Player(human_name, is_bot=False, ai_level=ai_level, avatar_variant="angel"),
            Player("AI Doi thu", is_bot=True, ai_level=ai_level, avatar_variant="demon"),
        ]
    return make_players(names, bot_flags, ai_level)


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
        "player_bot_flags": resize_flags(bot_flags, len(names)),
        "num_boxes_text": str(mode.get("num_boxes", 50)),
        "turn_mode": normalize_turn_mode(mode.get("turn_mode")),
        "layout_id": str(mode.get("layout_id", "classic")),
        "ai_level": str(mode.get("ai_level", "normal")),
        "mode_variant": str(mode.get("mode_variant", "standard") or "standard"),
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


def build_mode_data(state):
    mode_variant = str(state.get("mode_variant", "standard") or "standard")
    return {
        "name": state["mode_name"].strip(),
        "player_names": [name.strip() for name in state["player_names"]],
        "player_specs": [
            {
                "name": name.strip(),
                "is_bot": bool(state["player_bot_flags"][index]),
            }
            for index, name in enumerate(state["player_names"])
        ],
        "num_boxes": int(state["num_boxes_text"]),
        "turn_mode": normalize_turn_mode(state.get("turn_mode")),
        "layout_id": str(state.get("layout_id", "classic")),
        "ai_level": str(state.get("ai_level", "normal")),
        "mode_variant": mode_variant,
        "challenge_id": "custom_challenge" if mode_variant == "challenge" else "",
        "challenge_title": state["mode_name"].strip() if mode_variant == "challenge" else "",
        "weights": sanitize_weights(state["weights"], include_custom=True),
    }


def focus_player_field(state, index):
    if 0 <= index < len(state["player_names"]) and state["player_names"][index] == placeholder_name(index):
        state["player_names"][index] = ""
    return index


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
        return "Hieu ung dac biet | chi co trong custom"
    if effect.get("is_custom"):
        operation_label = CUSTOM_EFFECT_OPERATION_LABELS.get(effect.get("operation"), effect.get("operation", "custom"))
        value = float(effect.get("value", 0))
        value_text = str(int(value)) if value.is_integer() else f"{value:.1f}"
        return f"{operation_label} | gia tri {value_text}"
    return "Hieu ung co san"


def run_custom_mode_ui():
    pygame.init()
    pygame.key.start_text_input()
    settings = load_settings()
    screen = create_display(CUSTOM_WINDOW_SIZE, "Che do custom", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()
    font = get_font(20)
    small_font = get_font(16)
    clock = pygame.time.Clock()

    phase = "list"
    state = make_state()
    effect_editor = make_effect_editor()
    editing = 0
    scroll_y = 0
    error = ""
    last_tab_time = 0
    backspace_held = False
    backspace_repeat_delay = 170
    backspace_repeat_interval = 24
    next_backspace_time = 0

    while True:
        presets = load_custom_modes()
        draw_background(screen, pygame.time.get_ticks())
        draw_panel(
            screen,
            pygame.Rect(28, 20, screen.get_width() - 56, screen.get_height() - 40),
            fill_color=(248, 241, 225),
            border_color=PALETTE["gold_dark"],
            radius=28,
        )

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
                    elif event.key == pygame.K_RETURN:
                        phase = "weights"
                        scroll_y = 0
                elif phase == "weights" and event.key == pygame.K_RETURN:
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
                            error = "Nhap ten va gia tri hop le cho effect moi."
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing, effect_editor)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
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

        if phase == "list":
            screen.blit(font.render("Che do custom", True, (0, 0, 0)), (60, 28))
            screen.blit(small_font.render("Chon preset da luu hoac tao moi", True, (90, 90, 90)), (60, 62))
            new_rect = pygame.Rect(60, 110, 180, 46)
            back_rect = pygame.Rect(260, 110, 160, 46)
            draw_button(screen, font, new_rect, "Tao moi", (100, 200, 100))
            draw_button(screen, font, back_rect, "Quay lai", (220, 120, 120))

            play_buttons, edit_buttons, delete_buttons = [], [], []
            card_top, card_height = 180, 110
            if not presets:
                screen.blit(font.render("Chua co che do nao duoc luu.", True, (90, 90, 90)), (60, 220))
            else:
                y = card_top - scroll_y
                for preset in presets:
                    rect = pygame.Rect(60, y, screen.get_width() - 120, card_height)
                    if rect.bottom >= card_top and rect.top <= screen.get_height() - 20:
                        pygame.draw.rect(screen, (255, 255, 255), rect, border_radius=10)
                        pygame.draw.rect(screen, (0, 0, 0), rect, 2, border_radius=10)
                        names = preset.get("player_names", [])
                        turn_mode_label = TURN_MODE_LABELS[normalize_turn_mode(preset.get("turn_mode"))]
                        layout_label = BOARD_LAYOUTS.get(str(preset.get("layout_id", "classic")), BOARD_LAYOUTS["classic"])["label"]
                        mode_label = MODE_VARIANTS.get(str(preset.get("mode_variant", "standard")), MODE_VARIANTS["standard"])["label"]
                        summary = f"{mode_label} | {len(names)} players | {preset.get('num_boxes', 0)} boxes | {turn_mode_label} | {layout_label}"
                        screen.blit(font.render(str(preset.get("name", "Preset")), True, (0, 0, 0)), (rect.x + 20, rect.y + 14))
                        screen.blit(small_font.render(summary, True, (90, 90, 90)), (rect.x + 20, rect.y + 48))
                        screen.blit(small_font.render(", ".join(names[:5]), True, (90, 90, 90)), (rect.x + 20, rect.y + 74))
                        play_rect = pygame.Rect(rect.right - 320, rect.y + 28, 90, 42)
                        edit_rect = pygame.Rect(rect.right - 215, rect.y + 28, 90, 42)
                        delete_rect = pygame.Rect(rect.right - 110, rect.y + 28, 90, 42)
                        draw_button(screen, font, play_rect, "Choi", (100, 200, 100))
                        draw_button(screen, font, edit_rect, "Sua", (120, 180, 230))
                        draw_button(screen, font, delete_rect, "Xoa", (220, 120, 120))
                        play_buttons.append((preset, play_rect))
                        edit_buttons.append((preset, edit_rect))
                        delete_buttons.append((preset, delete_rect))
                    y += card_height + 16
                max_scroll = max(0, len(presets) * (card_height + 16) - (screen.get_height() - card_top - 20))
                scroll_y = max(0, min(scroll_y, max_scroll))

            if mouse_clicked:
                if new_rect.collidepoint(mouse_pos):
                    state, editing, error, phase = make_state(), 0, "", "name"
                    scroll_y = 0
                    refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    return None, None, None, None, None, None
                else:
                    for preset, rect in play_buttons:
                        if rect.collidepoint(mouse_pos):
                            player_specs = preset.get("player_specs")
                            if isinstance(player_specs, list) and player_specs:
                                names = [str(spec.get("name", "")).strip() for spec in player_specs if str(spec.get("name", "")).strip()]
                                bot_flags = [bool(spec.get("is_bot", False)) for spec in player_specs][: len(names)]
                            else:
                                names = [str(name).strip() for name in preset.get("player_names", []) if str(name).strip()]
                                bot_flags = resize_flags([], len(names))
                            num_boxes = int(preset.get("num_boxes", 0))
                            if names and num_boxes > 0:
                                turn_mode = normalize_turn_mode(preset.get("turn_mode"))
                                if (any(bot_flags) or str(preset.get("mode_variant", "standard")) == "solo_bot") and turn_mode == MANUAL_TURN_MODE:
                                    turn_mode = SEQUENTIAL_TURN_MODE
                                mode_data = dict(preset)
                                mode_data["player_names"] = names
                                mode_data["ai_level"] = str(preset.get("ai_level", "normal"))
                                return (
                                    build_players_for_mode(mode_data, bot_flags),
                                    num_boxes,
                                    "custom",
                                    sanitize_weights(preset.get("weights"), include_custom=True),
                                    turn_mode,
                                    build_mode_session_options(mode_data),
                                )
                    for preset, rect in edit_buttons:
                        if rect.collidepoint(mouse_pos):
                            state, editing, error, phase = make_state(preset), 0, "", "name"
                            scroll_y = 0
                            refresh_text_input()
                    for preset, rect in delete_buttons:
                        if rect.collidepoint(mouse_pos):
                            delete_custom_mode(str(preset.get("name", "")).strip())

        elif phase == "name":
            screen.blit(font.render("Dat ten che do", True, (0, 0, 0)), (60, 40))
            draw_box(screen, font, pygame.Rect(60, 120, 520, 46), state["mode_name"], True, caret_visible)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
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
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
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
            screen.blit(font.render("Ten nguoi choi", True, (0, 0, 0)), (60, 24))
            minus_rect = pygame.Rect(60, 90, 45, 38)
            plus_rect = pygame.Rect(185, 90, 45, 38)
            count_rect = pygame.Rect(115, 90, 60, 38)
            draw_button(screen, font, minus_rect, "-", (230, 230, 230))
            draw_box(screen, font, count_rect, str(len(state["player_names"])))
            draw_button(screen, font, plus_rect, "+", (230, 230, 230))
            name_rects = []
            for index, name in enumerate(state["player_names"]):
                x = 60 + (index % 4) * 238
                y = 160 + (index // 4) * 60
                rect = pygame.Rect(x, y, 156, 42)
                toggle_rect = pygame.Rect(x + 164, y, 56, 42)
                draw_box(screen, font, rect, name, index == editing, index == editing and caret_visible)
                toggle_label = "BOT" if state["player_bot_flags"][index] else "Nguoi"
                toggle_fill = (244, 217, 223) if state["player_bot_flags"][index] else (225, 241, 230)
                toggle_border = PALETTE["crimson_dark"] if state["player_bot_flags"][index] else PALETTE["mint_dark"]
                draw_button(screen, small_font, toggle_rect, toggle_label, toggle_fill, (0, 0, 0), toggle_border)
                name_rects.append((index, rect, toggle_rect))
            hint_text = small_font.render("Tab de doi o, click de chon nhanh. Moi bot se dung cung AI level.", True, (80, 80, 80))
            screen.blit(hint_text, (60, 590))
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            if mouse_clicked:
                if minus_rect.collidepoint(mouse_pos) and len(state["player_names"]) > 1:
                    state["player_names"] = resize_names(state["player_names"], len(state["player_names"]) - 1)
                    state["player_bot_flags"] = resize_flags(state["player_bot_flags"], len(state["player_names"]))
                    state["num_players_text"] = str(len(state["player_names"]))
                    editing = min(editing, len(state["player_names"]) - 1)
                elif plus_rect.collidepoint(mouse_pos):
                    state["player_names"] = resize_names(state["player_names"], len(state["player_names"]) + 1)
                    state["player_bot_flags"] = resize_flags(state["player_bot_flags"], len(state["player_names"]))
                    state["num_players_text"] = str(len(state["player_names"]))
                    editing = focus_player_field(state, len(state["player_names"]) - 1)
                    refresh_text_input()
                elif next_rect.collidepoint(mouse_pos):
                    error = "" if all(name.strip() for name in state["player_names"]) else "Hay nhap du ten nguoi choi."
                    if not error:
                        phase = "boxes"
                        refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "players", ""
                    refresh_text_input()
                else:
                    for index, rect, toggle_rect in name_rects:
                        if rect.collidepoint(mouse_pos):
                            editing = focus_player_field(state, index)
                            refresh_text_input()
                        elif toggle_rect.collidepoint(mouse_pos):
                            state["player_bot_flags"][index] = not state["player_bot_flags"][index]

        elif phase == "boxes":
            screen.blit(font.render("So o may man", True, (0, 0, 0)), (60, 40))
            draw_box(screen, font, pygame.Rect(60, 120, 200, 46), state["num_boxes_text"], True, caret_visible)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    error = "" if valid_number(state["num_boxes_text"]) else "So o khong hop le."
                    if not error:
                        phase = "turn_mode"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "names", ""
                    refresh_text_input()

        elif phase == "turn_mode":
            screen.blit(font.render("Kieu den luot", True, (0, 0, 0)), (60, 40))
            screen.blit(small_font.render("Chon cach xac dinh nguoi mo o tiep theo, layout va do kho cua bot.", True, (90, 90, 90)), (60, 74))
            sequential_rect = pygame.Rect(60, 140, 460, 130)
            manual_rect = pygame.Rect(560, 140, 460, 130)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            has_bots = any(state["player_bot_flags"])
            options = [
                (SEQUENTIAL_TURN_MODE, sequential_rect, TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE], "Tu dong quay vong tu nguoi dau den nguoi cuoi."),
                (MANUAL_TURN_MODE, manual_rect, TURN_MODE_LABELS[MANUAL_TURN_MODE], "Nguoi choi tu click chon ten truoc khi mo o."),
            ]
            for mode_value, rect, title, description in options:
                active = state["turn_mode"] == mode_value
                disabled = has_bots and mode_value == MANUAL_TURN_MODE
                fill_color = (226, 221, 214) if disabled else (244, 230, 186) if active else (234, 226, 210)
                border_color = (156, 150, 146) if disabled else PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(title, True, (0, 0, 0)), (rect.x + 18, rect.y + 20))
                screen.blit(small_font.render(description, True, (80, 80, 80)), (rect.x + 18, rect.y + 68))
                if disabled:
                    disabled_text = small_font.render("Co bot: khi bat dau se dung Lan luot.", True, PALETTE["crimson_dark"])
                    screen.blit(disabled_text, (rect.x + 18, rect.bottom - 28))

            ai_rects = []
            for index, (ai_level, ai_config) in enumerate(AI_LEVELS.items()):
                rect = pygame.Rect(60 + index * 320, 306, 280, 90)
                active = state["ai_level"] == ai_level
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(ai_config["label"], True, (0, 0, 0)), (rect.x + 18, rect.y + 14))
                screen.blit(small_font.render(ai_config["description"], True, (80, 80, 80)), (rect.x + 18, rect.y + 46))
                ai_rects.append((ai_level, rect))

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
                layout_rects.append((layout_id, rect))
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            if mouse_clicked:
                if sequential_rect.collidepoint(mouse_pos):
                    state["turn_mode"] = SEQUENTIAL_TURN_MODE
                elif manual_rect.collidepoint(mouse_pos) and not has_bots:
                    state["turn_mode"] = MANUAL_TURN_MODE
                elif next_rect.collidepoint(mouse_pos):
                    phase = "weights"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "boxes", ""
                else:
                    for ai_level, rect in ai_rects:
                        if rect.collidepoint(mouse_pos):
                            state["ai_level"] = ai_level
                    for layout_id, rect in layout_rects:
                        if rect.collidepoint(mouse_pos):
                            state["layout_id"] = layout_id

        elif phase == "weights":
            effects = get_all_effects(include_custom=True)
            state["weights"] = sanitize_weights(state["weights"], include_custom=True)
            screen.blit(font.render("Chinh ti le hieu ung", True, (0, 0, 0)), (60, 24))
            screen.blit(small_font.render("8 hieu ung mac dinh + nhom dac biet chi xuat hien o custom.", True, (90, 90, 90)), (60, 58))
            add_effect_rect = pygame.Rect(60, 90, 200, 42)
            reset_rect = pygame.Rect(280, 90, 160, 42)
            draw_button(screen, font, add_effect_rect, "Them effect", (120, 180, 230))
            draw_button(screen, font, reset_rect, "Mac dinh", (230, 230, 180))

            row_top = 150
            row_height = 58
            row_gap = 12
            visible_bottom = screen.get_height() - 130
            buttons = []
            total = sum(state["weights"].get(str(effect["id"]), 0.0) for effect in effects)
            for index, effect in enumerate(effects):
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
                screen.blit(font.render(f"{label} - {percent:.1f}%", True, (0, 0, 0)), (row.x + 18, row.y + 8))
                screen.blit(small_font.render(detail, True, (90, 90, 90)), (row.x + 18, row.y + 32))
                minus_rect = pygame.Rect(row.right - 200, row.y + 13, 40, 32)
                plus_rect = pygame.Rect(row.right - 50, row.y + 13, 40, 32)
                draw_button(screen, font, minus_rect, "-", (230, 230, 230))
                draw_box(screen, font, pygame.Rect(row.right - 150, row.y + 13, 90, 32), f"{weight:.1f}")
                draw_button(screen, font, plus_rect, "+", (230, 230, 230))
                buttons.append((effect_id, minus_rect, plus_rect))

            max_scroll = max(0, len(effects) * (row_height + row_gap) - (visible_bottom - row_top))
            scroll_y = max(0, min(scroll_y, max_scroll))

            back_rect = pygame.Rect(560, 620, 170, 50)
            next_rect = pygame.Rect(760, 620, 170, 50)
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            draw_button(screen, font, next_rect, "Bat dau", (100, 200, 100))
            if mouse_clicked:
                handled = False
                for effect_id, minus_rect, plus_rect in buttons:
                    if minus_rect.collidepoint(mouse_pos):
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
            screen.blit(small_font.render(preview_text, True, (80, 80, 80)), (preview_rect.x + 14, preview_rect.y + 11))

            save_y = min(screen.get_height() - 80, preview_rect.bottom + 24)
            save_rect = pygame.Rect(760, save_y, 170, 50)
            back_rect = pygame.Rect(560, save_y, 170, 50)
            draw_button(screen, font, save_rect, "Luu effect", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
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
                        error = "Nhap ten va gia tri hop le cho effect moi."
                else:
                    for operation_id, rect in option_rects:
                        if rect.collidepoint(mouse_pos):
                            effect_editor["operation"] = operation_id
                            break

        elif phase == "save":
            screen.blit(font.render("Luu che do nay?", True, (0, 0, 0)), (60, 60))
            effective_turn_mode = state["turn_mode"]
            if (any(state["player_bot_flags"]) or state["mode_variant"] == "solo_bot") and effective_turn_mode == MANUAL_TURN_MODE:
                effective_turn_mode = SEQUENTIAL_TURN_MODE
            lines = [
                f"Ten che do: {state['mode_name'].strip()}",
                f"So nguoi choi: {len(state['player_names'])}",
                f"So o: {state['num_boxes_text']}",
                f"Kieu den luot: {TURN_MODE_LABELS[effective_turn_mode]}",
                f"Layout: {BOARD_LAYOUTS.get(state['layout_id'], BOARD_LAYOUTS['classic'])['label']} | AI: {AI_LEVELS.get(state['ai_level'], AI_LEVELS['normal'])['label']}",
            ]
            for index, line in enumerate(lines):
                screen.blit(font.render(line, True, (0, 0, 0)), (60, 130 + index * 40))

            mode_rects = []
            mode_items = list(MODE_VARIANTS.items())
            for index, (mode_id, mode_data) in enumerate(mode_items):
                rect = pygame.Rect(60 + index * 270, 356, 242, 64)
                active = state["mode_variant"] == mode_id
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(mode_data["label"], True, (0, 0, 0)), (rect.x + 14, rect.y + 10))
                screen.blit(small_font.render(mode_data["description"], True, (90, 90, 90)), (rect.x + 14, rect.y + 36))
                mode_rects.append((mode_id, rect))

            save_rect = pygame.Rect(60, 468, 220, 54)
            play_rect = pygame.Rect(300, 468, 220, 54)
            back_rect = pygame.Rect(540, 468, 220, 54)
            draw_button(screen, font, save_rect, "Choi va luu", (100, 200, 100))
            draw_button(screen, font, play_rect, "Chi choi lan nay", (120, 180, 230))
            draw_button(screen, font, back_rect, "Quay lai", (220, 120, 120))
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
