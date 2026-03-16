import os
import sys

import pygame

from mechanics.randomizer import DEFAULT_WEIGHTS
from mechanics.randomizer import EFFECT_LABELS
from mechanics.randomizer import sanitize_weights
from models.custom_modes import delete_custom_mode
from models.custom_modes import load_custom_modes
from models.custom_modes import save_custom_mode
from models.player import Player
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import TURN_MODE_LABELS
from models.turn_modes import normalize_turn_mode
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


def make_players(names):
    return [Player(name.strip()) for name in names]


def make_state(mode=None):
    if not mode:
        return {
            "original_name": None,
            "mode_name": "",
            "num_players_text": "2",
            "player_names": resize_names([], 2),
            "num_boxes_text": "50",
            "turn_mode": SEQUENTIAL_TURN_MODE,
            "weights": DEFAULT_WEIGHTS.copy(),
        }

    names = [str(name) for name in mode.get("player_names", []) if str(name).strip()]
    if not names:
        names = resize_names([], 2)
    return {
        "original_name": str(mode.get("name", "")).strip(),
        "mode_name": str(mode.get("name", "")).strip(),
        "num_players_text": str(len(names)),
        "player_names": names,
        "num_boxes_text": str(mode.get("num_boxes", 50)),
        "turn_mode": normalize_turn_mode(mode.get("turn_mode")),
        "weights": sanitize_weights(mode.get("weights", DEFAULT_WEIGHTS)),
    }


def valid_number(text):
    return text.isdigit() and int(text) > 0


def name_exists(mode_name, original_name):
    for mode in load_custom_modes():
        current = str(mode.get("name", "")).strip()
        if current == mode_name and current != original_name:
            return True
    return False


def build_mode_data(state):
    return {
        "name": state["mode_name"].strip(),
        "player_names": [name.strip() for name in state["player_names"]],
        "num_boxes": int(state["num_boxes_text"]),
        "turn_mode": normalize_turn_mode(state.get("turn_mode")),
        "weights": sanitize_weights(state["weights"]),
    }


def focus_player_field(state, index):
    if 0 <= index < len(state["player_names"]) and state["player_names"][index] == placeholder_name(index):
        state["player_names"][index] = ""
    return index


def handle_backspace(state, phase, editing):
    if phase == "name":
        state["mode_name"] = state["mode_name"][:-1]
    elif phase == "players":
        state["num_players_text"] = state["num_players_text"][:-1]
    elif phase == "names" and state["player_names"]:
        state["player_names"][editing] = state["player_names"][editing][:-1]
    elif phase == "boxes":
        state["num_boxes_text"] = state["num_boxes_text"][:-1]


def run_custom_mode_ui():
    pygame.init()
    pygame.key.start_text_input()
    screen = pygame.display.set_mode((1200, 760), pygame.RESIZABLE)
    pygame.display.set_caption("Che do custom")
    font = get_font(20)
    small_font = get_font(16)
    clock = pygame.time.Clock()

    phase = "list"
    state = make_state()
    editing = 0
    scroll_y = 0
    error = ""
    last_tab_time = 0
    backspace_held = False
    backspace_repeat_delay = 350
    backspace_repeat_interval = 40
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
                return None, None, None, None, None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True
                elif phase == "list" and event.button == 4:
                    scroll_y = max(0, scroll_y - 40)
                elif phase == "list" and event.button == 5:
                    scroll_y += 40
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if phase == "list":
                        return None, None, None, None, None
                    phase = {
                        "save": "weights",
                        "weights": "turn_mode",
                        "turn_mode": "boxes",
                        "boxes": "names",
                        "names": "players",
                        "players": "name",
                        "name": "list",
                    }[phase]
                    refresh_text_input()
                    error = ""
                elif phase == "name":
                    if event.key == pygame.K_RETURN and state["mode_name"].strip():
                        phase = "players"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "players":
                    if event.key == pygame.K_RETURN and valid_number(state["num_players_text"]):
                        state["player_names"] = resize_names(state["player_names"], int(state["num_players_text"]))
                        editing = focus_player_field(state, 0)
                        phase = "names"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing)
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
                        handle_backspace(state, phase, editing)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "boxes":
                    if event.key == pygame.K_RETURN and valid_number(state["num_boxes_text"]):
                        phase = "turn_mode"
                        refresh_text_input()
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        handle_backspace(state, phase, editing)
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "turn_mode":
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        state["turn_mode"] = SEQUENTIAL_TURN_MODE
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_TAB):
                        state["turn_mode"] = MANUAL_TURN_MODE
                    elif event.key == pygame.K_RETURN:
                        phase = "weights"
                elif phase == "weights" and event.key == pygame.K_RETURN:
                    if any(weight > 0 for weight in state["weights"]):
                        phase = "save"
                    else:
                        error = "Phai co it nhat mot ti le > 0."
            elif event.type == pygame.TEXTINPUT:
                if phase == "name":
                    state["mode_name"] += event.text
                elif phase == "players":
                    if event.text.isdigit():
                        state["num_players_text"] += event.text
                elif phase == "names" and state["player_names"]:
                    state["player_names"][editing] += event.text
                elif phase == "boxes":
                    if event.text.isdigit():
                        state["num_boxes_text"] += event.text
            elif event.type == pygame.KEYUP and event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                backspace_held = False

        if backspace_held and current_time >= next_backspace_time:
            handle_backspace(state, phase, editing)
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
                        summary = f"{len(names)} players | {preset.get('num_boxes', 0)} boxes | {turn_mode_label}"
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
                    refresh_text_input()
                elif back_rect.collidepoint(mouse_pos):
                    return None, None, None, None, None
                else:
                    for preset, rect in play_buttons:
                        if rect.collidepoint(mouse_pos):
                            names = [str(name).strip() for name in preset.get("player_names", []) if str(name).strip()]
                            num_boxes = int(preset.get("num_boxes", 0))
                            if names and num_boxes > 0:
                                return (
                                    make_players(names),
                                    num_boxes,
                                    "custom",
                                    sanitize_weights(preset.get("weights", DEFAULT_WEIGHTS)),
                                    normalize_turn_mode(preset.get("turn_mode")),
                                )
                    for preset, rect in edit_buttons:
                        if rect.collidepoint(mouse_pos):
                            state, editing, error, phase = make_state(preset), 0, "", "name"
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
                rect = pygame.Rect(x, y, 220, 42)
                draw_box(screen, font, rect, name, index == editing, index == editing and caret_visible)
                name_rects.append(rect)
            hint_text = small_font.render("Tab de doi o, click de chon nhanh.", True, (80, 80, 80))
            screen.blit(hint_text, (60, 590))
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            if mouse_clicked:
                if minus_rect.collidepoint(mouse_pos) and len(state["player_names"]) > 1:
                    state["player_names"] = resize_names(state["player_names"], len(state["player_names"]) - 1)
                    state["num_players_text"] = str(len(state["player_names"]))
                    editing = min(editing, len(state["player_names"]) - 1)
                elif plus_rect.collidepoint(mouse_pos):
                    state["player_names"] = resize_names(state["player_names"], len(state["player_names"]) + 1)
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
                    for index, rect in enumerate(name_rects):
                        if rect.collidepoint(mouse_pos):
                            editing = focus_player_field(state, index)
                            refresh_text_input()

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
            screen.blit(small_font.render("Chon cach xac dinh nguoi mo o tiep theo.", True, (90, 90, 90)), (60, 74))
            sequential_rect = pygame.Rect(60, 140, 460, 130)
            manual_rect = pygame.Rect(560, 140, 460, 130)
            next_rect = pygame.Rect(760, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            options = [
                (SEQUENTIAL_TURN_MODE, sequential_rect, TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE], "Tu dong quay vong tu nguoi dau den nguoi cuoi."),
                (MANUAL_TURN_MODE, manual_rect, TURN_MODE_LABELS[MANUAL_TURN_MODE], "Nguoi choi tu click chon ten truoc khi mo o."),
            ]
            for mode_value, rect, title, description in options:
                active = state["turn_mode"] == mode_value
                fill_color = (244, 230, 186) if active else (234, 226, 210)
                border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]
                pygame.draw.rect(screen, fill_color, rect, border_radius=12)
                pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=12)
                screen.blit(font.render(title, True, (0, 0, 0)), (rect.x + 18, rect.y + 20))
                screen.blit(small_font.render(description, True, (80, 80, 80)), (rect.x + 18, rect.y + 68))
            draw_button(screen, font, next_rect, "Tiep", (100, 200, 100))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            if mouse_clicked:
                if sequential_rect.collidepoint(mouse_pos):
                    state["turn_mode"] = SEQUENTIAL_TURN_MODE
                elif manual_rect.collidepoint(mouse_pos):
                    state["turn_mode"] = MANUAL_TURN_MODE
                elif next_rect.collidepoint(mouse_pos):
                    phase = "weights"
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "boxes", ""

        elif phase == "weights":
            screen.blit(font.render("Chinh ti le hieu ung", True, (0, 0, 0)), (60, 24))
            total = sum(state["weights"])
            buttons = []
            for index, label in enumerate(EFFECT_LABELS):
                y = 100 + index * 62
                row = pygame.Rect(60, y, screen.get_width() - 120, 50)
                pygame.draw.rect(screen, (255, 255, 255), row, border_radius=10)
                pygame.draw.rect(screen, (0, 0, 0), row, 2, border_radius=10)
                percent = 0 if total <= 0 else state["weights"][index] / total * 100
                screen.blit(font.render(f"{label} - {percent:.1f}%", True, (0, 0, 0)), (row.x + 18, row.y + 10))
                minus_rect = pygame.Rect(row.right - 200, row.y + 9, 40, 32)
                plus_rect = pygame.Rect(row.right - 50, row.y + 9, 40, 32)
                draw_button(screen, font, minus_rect, "-", (230, 230, 230))
                draw_box(screen, font, pygame.Rect(row.right - 150, row.y + 9, 90, 32), f"{state['weights'][index]:.1f}")
                draw_button(screen, font, plus_rect, "+", (230, 230, 230))
                buttons.append((index, minus_rect, plus_rect))
            reset_rect = pygame.Rect(60, 620, 170, 50)
            back_rect = pygame.Rect(560, 620, 170, 50)
            next_rect = pygame.Rect(760, 620, 170, 50)
            draw_button(screen, font, reset_rect, "Mac dinh", (230, 230, 180))
            draw_button(screen, font, back_rect, "Tro lai", (220, 120, 120))
            draw_button(screen, font, next_rect, "Bat dau", (100, 200, 100))
            if mouse_clicked:
                handled = False
                for index, minus_rect, plus_rect in buttons:
                    if minus_rect.collidepoint(mouse_pos):
                        state["weights"][index] = max(0.0, state["weights"][index] - 0.5)
                        handled = True
                    elif plus_rect.collidepoint(mouse_pos):
                        state["weights"][index] += 0.5
                        handled = True
                    if handled:
                        break
                if not handled and reset_rect.collidepoint(mouse_pos):
                    state["weights"] = DEFAULT_WEIGHTS.copy()
                elif not handled and back_rect.collidepoint(mouse_pos):
                    phase, error = "turn_mode", ""
                    refresh_text_input()
                elif not handled and next_rect.collidepoint(mouse_pos):
                    error = "" if any(weight > 0 for weight in state["weights"]) else "Phai co it nhat mot ti le > 0."
                    if not error:
                        phase = "save"

        elif phase == "save":
            screen.blit(font.render("Luu che do nay?", True, (0, 0, 0)), (60, 60))
            lines = [
                f"Ten che do: {state['mode_name'].strip()}",
                f"So nguoi choi: {len(state['player_names'])}",
                f"So o: {state['num_boxes_text']}",
                f"Kieu den luot: {TURN_MODE_LABELS[state['turn_mode']]}",
            ]
            for index, line in enumerate(lines):
                screen.blit(font.render(line, True, (0, 0, 0)), (60, 130 + index * 40))
            save_rect = pygame.Rect(60, 340, 220, 54)
            play_rect = pygame.Rect(300, 340, 220, 54)
            back_rect = pygame.Rect(540, 340, 220, 54)
            draw_button(screen, font, save_rect, "Choi va luu", (100, 200, 100))
            draw_button(screen, font, play_rect, "Chi choi lan nay", (120, 180, 230))
            draw_button(screen, font, back_rect, "Quay lai", (220, 120, 120))
            if mouse_clicked:
                if save_rect.collidepoint(mouse_pos):
                    mode_name = state["mode_name"].strip()
                    if not mode_name:
                        error = "Ten che do khong duoc de trong."
                    elif name_exists(mode_name, state["original_name"]):
                        error = "Ten che do da ton tai. Hay dat ten khac."
                    else:
                        mode = build_mode_data(state)
                        save_custom_mode(mode, state["original_name"])
                        return make_players(mode["player_names"]), mode["num_boxes"], "custom", mode["weights"], mode["turn_mode"]
                elif play_rect.collidepoint(mouse_pos):
                    mode = build_mode_data(state)
                    return make_players(mode["player_names"]), mode["num_boxes"], "custom", mode["weights"], mode["turn_mode"]
                elif back_rect.collidepoint(mouse_pos):
                    phase, error = "weights", ""

        if error:
            screen.blit(font.render(error, True, (200, 30, 30)), (60, screen.get_height() - 40))

        pygame.display.flip()
        clock.tick(30)
