import os
import sys
from pathlib import Path
from types import SimpleNamespace


os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "angels_and_demons_game"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from constants import CHALLENGE_PRESETS
from constants import MATCH_PRESETS
from models.player import Player
from models.turn_modes import MANUAL_TURN_MODE
from models.turn_modes import SEQUENTIAL_TURN_MODE
from ui.custom_mode_setup import apply_custom_turn_hotkey
from ui.custom_mode_setup import apply_custom_variant_hotkey
from ui.custom_mode_setup import build_effect_description
from ui.custom_mode_setup import build_mode_session_options
from ui.custom_mode_setup import build_players_for_mode
from ui.custom_mode_setup import build_preset_launch_payload
from ui.custom_mode_setup import filter_custom_mode_presets
from ui.custom_mode_setup import filter_weight_effects
from ui.custom_mode_setup import resolve_custom_mode_snapshot
from ui.custom_setup import apply_match_hotkey
from ui.custom_setup import apply_rules_hotkey
from ui.custom_setup import build_launch_payload
from ui.custom_setup import draw_choice_card
from ui.custom_setup import draw_layout_preview
from ui.custom_setup import resolve_setup_snapshot
from ui.effect_book_screen import build_effect_sections
from ui.effect_book_screen import draw_effect_row
from ui.game_screen import build_result_meta_chips
from ui.game_screen import draw_info_helper
from ui.game_screen import draw_result_leaderboard
from ui.game_screen import draw_result_meta_block
from ui.game_screen import draw_result_profile_strip
from ui.game_screen import get_scaled_board_metrics
from ui.histories_screen import filter_history_entries
from ui.histories_screen import draw_history_inspector
from ui.menu import draw_menu_option
from ui.settings_screen import _draw_slider
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_hint_bar
from ui.theme import draw_panel
from ui.theme import draw_scrollbar
from ui.theme import get_reveal_progress
from ui.theme import get_reveal_rect
from ui.theme import get_ui_font


def build_setup_state(**overrides):
    base_state = {
        "player_names": ["Lan", "Minh"],
        "player_bot_flags": [False, False],
        "match_preset": "classic",
        "layout_id": "classic",
        "turn_mode": SEQUENTIAL_TURN_MODE,
        "ai_level": "normal",
        "mode_variant": "standard",
        "challenge_id": next(iter(CHALLENGE_PRESETS)),
    }
    base_state.update(overrides)
    return base_state


def assert_setup_payloads():
    normal_payload = build_launch_payload(build_setup_state())
    assert len(normal_payload[0]) == 2
    assert all(not player.is_bot for player in normal_payload[0])
    assert normal_payload[1] == MATCH_PRESETS["classic"]["num_boxes"]
    assert normal_payload[5]["mode_variant"] == "standard"

    legacy_payload = build_launch_payload(build_setup_state(mode_variant="solo_bot", turn_mode=MANUAL_TURN_MODE))
    assert len(legacy_payload[0]) == 2
    assert all(not player.is_bot for player in legacy_payload[0])
    assert legacy_payload[5]["mode_variant"] == "standard"
    assert legacy_payload[4] == MANUAL_TURN_MODE

    challenge_id = next(iter(CHALLENGE_PRESETS))
    challenge_payload = build_launch_payload(build_setup_state(mode_variant="challenge", challenge_id=challenge_id))
    assert challenge_payload[2] == "custom"
    assert challenge_payload[5]["challenge_id"] == challenge_id
    assert challenge_payload[3]

    challenge_snapshot = resolve_setup_snapshot(build_setup_state(mode_variant="challenge", challenge_id=challenge_id))
    assert challenge_snapshot["challenge_label"] == CHALLENGE_PRESETS[challenge_id]["label"]
    assert challenge_snapshot["layout_id"] == CHALLENGE_PRESETS[challenge_id]["layout_id"]
    assert challenge_snapshot["num_boxes"] == MATCH_PRESETS[CHALLENGE_PRESETS[challenge_id]["match_preset"]]["num_boxes"]

    hotkey_state = build_setup_state()
    assert apply_match_hotkey(hotkey_state, pygame.K_1)
    assert hotkey_state["match_preset"] == "quick"
    assert apply_match_hotkey(hotkey_state, pygame.K_r)
    assert hotkey_state["layout_id"] == "chaos"

    rules_state = build_setup_state(mode_variant="standard")
    assert apply_rules_hotkey(rules_state, pygame.K_3)
    assert rules_state["mode_variant"] == "best_of_three"
    assert apply_rules_hotkey(rules_state, pygame.K_s)
    assert rules_state["turn_mode"] == MANUAL_TURN_MODE
    assert not apply_rules_hotkey(rules_state, pygame.K_4)
    assert not apply_rules_hotkey(rules_state, pygame.K_z)


def assert_custom_mode_helpers():
    mode_data = {
        "name": "Thu thach rieng",
        "player_names": ["Lan", "Minh"],
        "ai_level": "smart",
        "layout_id": "tower",
        "mode_variant": "challenge",
        "challenge_id": "custom_challenge",
        "challenge_title": "Thu thach rieng",
    }
    session_options = build_mode_session_options(mode_data)
    players = build_players_for_mode(
        {
            "player_names": ["Lan", "Minh"],
            "ai_level": "normal",
            "mode_variant": "solo_bot",
        },
        [False, False],
    )
    assert session_options["challenge_title"] == "Thu thach rieng"
    assert len(players) == 2 and all(not player.is_bot for player in players)
    assert "gia tri" in build_effect_description({"is_custom": True, "operation": "add", "value": 12})
    assert "custom" in build_effect_description({"custom_only": True})

    custom_snapshot = resolve_custom_mode_snapshot(
        {
            "player_names": ["Lan", "Minh", "Dung"],
            "player_bot_flags": [False, False, False],
            "num_boxes_text": "64",
            "turn_mode": "manual",
            "layout_id": "tower",
            "ai_level": "smart",
            "mode_variant": "standard",
        }
    )
    assert custom_snapshot["num_boxes"] == 64
    assert custom_snapshot["layout_label"] == "Tower"
    assert custom_snapshot["turn_label"]

    turn_state = {"player_bot_flags": [False, False], "turn_mode": "sequential", "ai_level": "normal", "layout_id": "classic"}
    assert apply_custom_turn_hotkey(turn_state, pygame.K_s)
    assert turn_state["turn_mode"] == "manual"
    assert apply_custom_turn_hotkey(turn_state, pygame.K_r)
    assert turn_state["layout_id"] == "chaos"
    assert not apply_custom_turn_hotkey(turn_state, pygame.K_c)

    variant_state = {"mode_variant": "standard"}
    assert apply_custom_variant_hotkey(variant_state, pygame.K_3)
    assert variant_state["mode_variant"] == "best_of_three"
    assert not apply_custom_variant_hotkey(variant_state, pygame.K_4)

    preset_samples = [
        {"name": "Nguoi", "player_names": ["Lan", "Minh"], "mode_variant": "standard", "num_boxes": 30, "turn_mode": "sequential", "layout_id": "classic", "weights": {"angel": 1.0}},
        {
            "name": "Legacy Bot",
            "player_specs": [{"name": "Lan", "is_bot": False}, {"name": "AI", "is_bot": True}],
            "mode_variant": "solo_bot",
            "num_boxes": 24,
            "turn_mode": "manual",
            "layout_id": "duel",
            "ai_level": "normal",
            "weights": {"angel": 1.0},
        },
        {"name": "Series", "player_names": ["A", "B"], "mode_variant": "best_of_three", "num_boxes": 36, "turn_mode": "sequential", "layout_id": "tower", "weights": {"angel": 1.0}},
    ]
    assert len(filter_custom_mode_presets(preset_samples, "all")) == 3
    assert len(filter_custom_mode_presets(preset_samples, "human")) == 3
    assert len(filter_custom_mode_presets(preset_samples, "series")) == 1

    sample_effects = [
        {"id": "angel"},
        {"id": "shield", "custom_only": True},
        {"id": "my_fx", "is_custom": True},
    ]
    assert len(filter_weight_effects(sample_effects, "all")) == 3
    assert len(filter_weight_effects(sample_effects, "builtin")) == 1
    assert len(filter_weight_effects(sample_effects, "custom")) == 2

    launch_payload = build_preset_launch_payload(preset_samples[1])
    assert launch_payload is not None
    assert all(not player.is_bot for player in launch_payload[0])
    assert launch_payload[4] == MANUAL_TURN_MODE
    assert launch_payload[5]["mode_variant"] == "standard"


def assert_filter_helpers():
    all_sections = build_effect_sections("all")
    builtin_sections = build_effect_sections("builtin")
    custom_sections = build_effect_sections("custom")
    assert len(all_sections) == 2
    assert len(builtin_sections) == 1 and "co san" in builtin_sections[0][0]
    assert len(custom_sections) == 1 and "custom" in custom_sections[0][0].lower()

    sample_history = [
        {"has_bots": False, "mode_variant": "standard"},
        {"has_bots": True, "mode_variant": "standard"},
        {"has_bots": True, "mode_variant": "challenge"},
        {"has_bots": False, "mode_variant": "best_of_three"},
    ]
    assert len(filter_history_entries(sample_history, "all")) == 4
    assert len(filter_history_entries(sample_history, "human")) == 2
    assert len(filter_history_entries(sample_history, "challenge")) == 1
    assert len(filter_history_entries(sample_history, "series")) == 1


def assert_animation_helpers():
    early_progress = get_reveal_progress(1000, 1040, duration=400, reduce_motion=False)
    late_progress = get_reveal_progress(1000, 1400, duration=400, reduce_motion=False)
    reduced_progress = get_reveal_progress(1000, 1010, duration=400, reduce_motion=True)
    assert 0.0 <= early_progress < 1.0
    assert late_progress == 1.0
    assert reduced_progress == 1.0
    moved_rect = get_reveal_rect(pygame.Rect(10, 20, 30, 40), 0.5, offset_y=20, offset_x=10)
    assert moved_rect.x >= 10 and moved_rect.y >= 20


def assert_result_meta():
    session_stub = SimpleNamespace(
        layout_id="classic",
        match_preset="classic",
        has_bots=False,
        mode_variant="best_of_three",
        turn_mode=SEQUENTIAL_TURN_MODE,
        challenge_title="",
        opened=list(range(18)),
        num_boxes=30,
    )
    chips = build_result_meta_chips(session_stub, {"wins": {"Nguoi 1": 2, "Nguoi 2": 1}})
    chip_labels = [chip[0] for chip in chips]
    assert all("bot" not in label.lower() for label in chip_labels)


def render_smoke_surface():
    pygame.init()
    pygame.display.set_mode((1280, 720))
    surface = pygame.display.get_surface()
    surface.fill(PALETTE["white"])
    draw_background(surface, 1600)

    title_font = get_ui_font(19, bold=True)
    body_font = get_ui_font(15)
    tiny_font = get_ui_font(13)

    draw_panel(surface, pygame.Rect(28, 28, 1224, 664), fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"])
    draw_menu_option(
        surface,
        title_font,
        body_font,
        pygame.Rect(58, 84, 420, 76),
        "Choi mac dinh",
        "Vao game nhanh voi preset tran va layout moi.",
        (247, 223, 184),
        PALETTE["gold_dark"],
        hovered=True,
        hotkey_label="1",
    )
    draw_choice_card(
        surface,
        title_font,
        body_font,
        pygame.Rect(58, 178, 420, 110),
        "Best of 3",
        "Danh cho cac keo PvP dai hoi va can ti so ro rang.",
        active=True,
    )
    draw_layout_preview(surface, pygame.Rect(58, 294, 120, 70), 50, 10, active=True)

    _draw_slider(surface, body_font, pygame.Rect(58, 330, 320, 18), "Am luong nhac", 0.63)
    draw_hint_bar(surface, tiny_font, pygame.Rect(58, 370, 420, 32), "Esc de quay lai | Mui ten de cuon")
    draw_scrollbar(surface, pygame.Rect(490, 84, 10, 280), 1200, 320, 180)
    draw_history_inspector(
        surface,
        body_font,
        tiny_font,
        "Ac quy",
        "Tru diem cua ban va tao mot swing ro rang trong tran dau.",
    )
    draw_effect_row(
        surface,
        {"font": title_font, "small": body_font, "tiny": tiny_font},
        pygame.Rect(58, 430, 420, 112),
        {"id": "angel", "label": "Thien than", "custom_only": False},
        hovered=True,
    )
    draw_info_helper(
        surface,
        tiny_font,
        pygame.Rect(58, 612, 420, 36),
        "H: Tro giup | B: So tay | T: Tooltip | M: Mute",
    )

    players = [Player("Nguoi 1"), Player("Nguoi 2"), Player("Nguoi 3")]
    players[0].score = 26
    players[1].score = 18
    players[2].score = 12
    session_stub = SimpleNamespace(
        layout_id="classic",
        match_preset="classic",
        has_bots=False,
        mode_variant="best_of_three",
        turn_mode=SEQUENTIAL_TURN_MODE,
        challenge_title="",
        opened=list(range(18)),
        num_boxes=30,
    )
    draw_result_meta_block(surface, tiny_font, tiny_font, pygame.Rect(540, 58, 650, 86), session_stub, {"wins": {"Nguoi 1": 2, "Nguoi 2": 1}})
    draw_result_profile_strip(
        surface,
        tiny_font,
        body_font,
        pygame.Rect(540, 506, 650, 68),
        {"games_played": 12, "career_best_score": 88, "largest_swing": 34, "achievement_count": 6},
    )
    draw_result_leaderboard(surface, pygame.Rect(540, 100, 650, 400), players, 1.0, body_font, tiny_font)

    box_size, gap, board_width, board_height, start_x, start_y = get_scaled_board_metrics(
        pygame.Rect(0, 0, 780, 470),
        10,
        7,
        86,
        12,
    )
    assert box_size >= 46
    assert gap >= 6
    assert board_width <= 780 and board_height <= 470
    assert start_x >= 0 and start_y >= 0
    assert surface.get_at((120, 120)) != pygame.Color(0, 0, 0, 255)

    pygame.display.flip()
    pygame.quit()


def main():
    assert_setup_payloads()
    assert_custom_mode_helpers()
    assert_filter_helpers()
    assert_animation_helpers()
    assert_result_meta()
    render_smoke_surface()
    print("smoke_ui_checks: ok")


if __name__ == "__main__":
    main()
