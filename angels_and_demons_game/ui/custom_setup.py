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
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_panel
from ui.theme import draw_subtitle
from ui.theme import draw_title


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
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=14, shadow=False)
    text_surface = font.render(value, True, PALETTE["text"])
    surface.blit(text_surface, (rect.x + 10, rect.centery - text_surface.get_height() // 2))
    if active and caret_visible:
        caret_x = min(rect.right - 12, rect.x + 14 + text_surface.get_width())
        pygame.draw.line(surface, border_color, (caret_x, rect.y + 10), (caret_x, rect.bottom - 10), 2)


def draw_choice_card(surface, title_font, detail_font, rect, title, detail, active=False, muted=False):
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

    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=20, shadow=False)
    title_surface = title_font.render(title, True, title_color)
    detail_surface = detail_font.render(detail, True, PALETTE["muted"] if not muted else (150, 144, 140))
    surface.blit(title_surface, (rect.x + 16, rect.y + 14))
    surface.blit(detail_surface, (rect.x + 16, rect.y + 50))


def run_custom_setup_ui():
    pygame.init()
    pygame.key.start_text_input()

    settings = load_settings()
    screen = create_display(SETUP_WINDOW_SIZE, "Chuan bi van choi", fullscreen=settings.get("fullscreen", False))
    apply_window_icon()

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    title_font = pygame.font.Font(font_path, 30)
    font = pygame.font.Font(font_path, 19)
    small_font = pygame.font.Font(font_path, 15)
    tiny_font = pygame.font.Font(font_path, 12)
    clock = pygame.time.Clock()

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
        draw_background(screen, tick)

        panel_rect = pygame.Rect(34, 22, screen.get_width() - 68, screen.get_height() - 44)
        draw_panel(screen, panel_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=30)
        draw_title(screen, title_font, "Chuan bi van choi", (panel_rect.centerx, panel_rect.y + 48), PALETTE["text"])
        draw_subtitle(screen, small_font, "Chon nguoi choi, bot, layout va nhip do tran dau truoc khi vao san.", (panel_rect.centerx, panel_rect.y + 82))

        step_labels = [
            ("players", "1. Nguoi choi"),
            ("match", "2. Tran dau"),
            ("rules", "3. Luat & AI"),
        ]
        for index, (phase_key, label) in enumerate(step_labels):
            chip_rect = pygame.Rect(panel_rect.x + 40 + index * 190, panel_rect.y + 108, 174, 34)
            active = state["phase"] == phase_key
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

        main_rect = pygame.Rect(panel_rect.x + 34, panel_rect.y + 158, panel_rect.width - 68, panel_rect.height - 228)
        draw_panel(screen, main_rect, fill_color=(252, 245, 235), border_color=PALETTE["lilac"], radius=26, shadow=False)

        next_rect = pygame.Rect(panel_rect.right - 224, panel_rect.bottom - 62, 178, 42)
        back_rect = pygame.Rect(panel_rect.right - 418, panel_rect.bottom - 62, 160, 42)

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
            elif event.type == pygame.TEXTINPUT and state["phase"] == "players" and state["player_names"]:
                state["player_names"][state["editing"]] += event.text

        if state["phase"] == "players":
            draw_title(screen, font, "Nguoi choi va Bot", (main_rect.centerx, main_rect.y + 34), PALETTE["text"])
            draw_subtitle(screen, small_font, "Ban co the bat bot cho tung slot. Bot se dung cung AI level o buoc sau.", (main_rect.centerx, main_rect.y + 62))

            minus_rect = pygame.Rect(main_rect.x + 38, main_rect.y + 90, 46, 38)
            count_rect = pygame.Rect(main_rect.x + 94, main_rect.y + 90, 70, 38)
            plus_rect = pygame.Rect(main_rect.x + 174, main_rect.y + 90, 46, 38)
            draw_button(screen, font, minus_rect, "-", PALETTE["panel_soft"], PALETTE["panel_dark"], minus_rect.collidepoint(mouse_pos), PALETTE["text"])
            draw_panel(screen, count_rect, fill_color=(246, 239, 225), border_color=PALETTE["panel_dark"], radius=14, shadow=False)
            count_surface = font.render(str(len(state["player_names"])), True, PALETTE["text"])
            screen.blit(count_surface, (count_rect.centerx - count_surface.get_width() // 2, count_rect.centery - count_surface.get_height() // 2))
            draw_button(screen, font, plus_rect, "+", PALETTE["panel_soft"], PALETTE["panel_dark"], plus_rect.collidepoint(mouse_pos), PALETTE["text"])

            name_rects = []
            per_row = 3
            box_width = (main_rect.width - 110) // per_row
            for index, name in enumerate(state["player_names"]):
                row = index // per_row
                col = index % per_row
                x = main_rect.x + 36 + col * (box_width + 12)
                y = main_rect.y + 154 + row * 94
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

            helper = tiny_font.render("Tab de doi o nhap. Tip: Manual mode se tu ve Lan luot neu trong tran co bot.", True, PALETTE["muted"])
            screen.blit(helper, (main_rect.x + 38, main_rect.bottom - 32))

            if mouse_clicked:
                if minus_rect.collidepoint(mouse_pos) and len(state["player_names"]) > 1:
                    ensure_player_state(state, len(state["player_names"]) - 1)
                    play_sfx("ui_click", volume_multiplier=0.45)
                elif plus_rect.collidepoint(mouse_pos):
                    ensure_player_state(state, len(state["player_names"]) + 1)
                    focus_player_field(state, len(state["player_names"]) - 1)
                    play_sfx("ui_click", volume_multiplier=0.45)
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

            preset_rects = []
            for index, (preset_id, preset) in enumerate(MATCH_PRESETS.items()):
                rect = pygame.Rect(main_rect.x + 36 + index * 260, main_rect.y + 102, 230, 110)
                draw_choice_card(screen, font, small_font, rect, f"{preset['label']} - {preset['num_boxes']} o", preset["description"], active=state["match_preset"] == preset_id)
                preset_rects.append((preset_id, rect))

            layout_rects = []
            for index, (layout_id, layout) in enumerate(BOARD_LAYOUTS.items()):
                row = index // 2
                col = index % 2
                rect = pygame.Rect(main_rect.x + 120 + col * 350, main_rect.y + 258 + row * 132, 300, 108)
                draw_choice_card(screen, font, small_font, rect, layout["label"], layout["description"], active=state["layout_id"] == layout_id)
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
            mode_items = list(MODE_VARIANTS.items())
            mode_card_width = 206
            mode_gap = 12
            mode_y = main_rect.y + 92
            for index, (mode_id, mode_data) in enumerate(mode_items):
                rect = pygame.Rect(main_rect.x + 32 + index * (mode_card_width + mode_gap), mode_y, mode_card_width, 74)
                detail = mode_data["description"]
                if mode_id == "challenge":
                    challenge_title = CHALLENGE_PRESETS[state["challenge_id"]]["label"]
                    detail = f"{challenge_title} | {detail}"
                draw_choice_card(screen, small_font, tiny_font, rect, mode_data["label"], detail, active=state["mode_variant"] == mode_id)
                mode_rects.append((mode_id, rect))

            sequential_rect = pygame.Rect(main_rect.x + 68, main_rect.y + 190, 360, 102)
            manual_rect = pygame.Rect(main_rect.x + 470, main_rect.y + 190, 360, 102)
            draw_choice_card(
                screen,
                font,
                small_font,
                sequential_rect,
                TURN_MODE_LABELS[SEQUENTIAL_TURN_MODE],
                "Game tu quay vong nguoi choi theo thu tu.",
                active=state["turn_mode"] == SEQUENTIAL_TURN_MODE,
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
            )
            if has_bots or state["mode_variant"] == "challenge":
                note_text = "Co bot: che do nay se tu dong chuyen ve Lan luot khi bat dau."
                if state["mode_variant"] == "challenge":
                    note_text = "Challenge su dung luat quay luot co san de giu dung tinh chat thu thach."
                note = tiny_font.render(note_text, True, PALETTE["crimson_dark"])
                screen.blit(note, (manual_rect.x + 16, manual_rect.bottom - 24))

            ai_rects = []
            for index, (ai_level, ai_config) in enumerate(AI_LEVELS.items()):
                rect = pygame.Rect(main_rect.x + 70 + index * 250, main_rect.y + 316, 220, 100)
                draw_choice_card(screen, font, small_font, rect, ai_config["label"], ai_config["description"], active=state["ai_level"] == ai_level)
                ai_rects.append((ai_level, rect))

            summary_rect = pygame.Rect(main_rect.x + 74, main_rect.bottom - 74, main_rect.width - 148, 48)
            draw_panel(screen, summary_rect, fill_color=(241, 234, 221), border_color=PALETTE["panel_dark"], radius=18, shadow=False)
            mode_label = MODE_VARIANTS[state["mode_variant"]]["label"]
            summary_text = f"{mode_label} | {len(state['player_names'])} slot | {MATCH_PRESETS[state['match_preset']]['num_boxes']} o | {BOARD_LAYOUTS[state['layout_id']]['label']} | AI {AI_LEVELS[state['ai_level']]['label']}"
            if state["mode_variant"] == "challenge":
                challenge_label = CHALLENGE_PRESETS[state["challenge_id"]]["label"]
                summary_text = f"{mode_label} - {challenge_label} | {AI_LEVELS[state['ai_level']]['label']}"
            elif state["mode_variant"] == "solo_bot":
                summary_text = f"{mode_label} | 1 nguoi + 1 bot | {MATCH_PRESETS[state['match_preset']]['num_boxes']} o | AI {AI_LEVELS[state['ai_level']]['label']}"
            elif state["mode_variant"] == "best_of_three":
                summary_text = f"{mode_label} | Can 2 van thang | {MATCH_PRESETS[state['match_preset']]['num_boxes']} o | {BOARD_LAYOUTS[state['layout_id']]['label']}"
            summary_surface = tiny_font.render(summary_text, True, PALETTE["text"])
            screen.blit(summary_surface, (summary_rect.centerx - summary_surface.get_width() // 2, summary_rect.centery - summary_surface.get_height() // 2))

            if mouse_clicked:
                for mode_id, rect in mode_rects:
                    if rect.collidepoint(mouse_pos):
                        state["mode_variant"] = mode_id
                        if mode_id == "challenge":
                            state["turn_mode"] = normalize_turn_mode(CHALLENGE_PRESETS[state["challenge_id"]].get("turn_mode"))
                        play_sfx("ui_click", volume_multiplier=0.45)
                        break
                else:
                    if sequential_rect.collidepoint(mouse_pos):
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
                info_surface = tiny_font.render("Challenge se khoa layout, so o va bo effect theo preset co san.", True, PALETTE["crimson_dark"])
                screen.blit(info_surface, (main_rect.x + 72, main_rect.bottom - 102))

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
