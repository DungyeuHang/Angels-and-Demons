import random
from pathlib import Path

import pygame

from models.custom_effects import CUSTOM_EFFECT_OPERATION_LABELS
from models.custom_effects import load_custom_effects


pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
SOUND_DIR = BASE_DIR / "assets" / "sounds"

BUILTIN_EFFECTS = [
    {"id": "angel", "label": "Thien than", "default_weight": 1.0},
    {"id": "devil", "label": "Ac quy", "default_weight": 1.0},
    {"id": "gun", "label": "Sung", "default_weight": 1.0},
    {"id": "lucky", "label": "May man", "default_weight": 1.0},
    {"id": "lottery", "label": "Trung so", "default_weight": 1.0},
    {"id": "rps", "label": "Keo bua bao", "default_weight": 1.0},
    {"id": "double", "label": "Nhan doi", "default_weight": 0.5},
    {"id": "half", "label": "Chia doi", "default_weight": 0.5},
]

NEGATIVE_BUILTIN_IDS = {"devil", "half"}
NEGATIVE_CUSTOM_OPERATIONS = {"subtract_self", "divide_self", "give_random", "all_lose"}


def load_sound(filename, default=None, volume=0.6):
    path = SOUND_DIR / filename
    if not path.exists():
        return default
    try:
        sound = pygame.mixer.Sound(str(path))
        sound.set_volume(volume)
        return sound
    except Exception:
        return default


SOUNDS = {
    "angel": load_sound("angels.mp3"),
    "devil": load_sound("devil.mp3"),
    "gun": load_sound("gun.mp3"),
    "lucky": load_sound("lucky.mp3"),
    "lottery": load_sound("lotery.mp3"),
    "rps": load_sound("rps.mp3"),
    "double": load_sound("double.mp3"),
    "half": load_sound("half.mp3"),
}


def format_number(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)

    if numeric_value.is_integer():
        return str(int(numeric_value))
    return f"{numeric_value:.1f}"


def get_builtin_effects():
    return [dict(effect) for effect in BUILTIN_EFFECTS]


def get_all_effects(include_custom=True):
    effects = get_builtin_effects()
    if include_custom:
        for effect in load_custom_effects():
            custom_effect = dict(effect)
            custom_effect["default_weight"] = 0.0
            effects.append(custom_effect)
    return effects


def get_effect_definition(effect_id, include_custom=True):
    effect_id = str(effect_id)
    for effect in get_all_effects(include_custom=include_custom):
        if str(effect.get("id")) == effect_id:
            return effect
    return None


def play_effect(effect_id, stop_others=True):
    if not pygame.mixer.get_init():
        return
    sound = SOUNDS.get(str(effect_id))
    if sound:
        if stop_others:
            pygame.mixer.stop()
        sound.play()


def choose_random_other(player, all_players):
    if not all_players:
        return None
    others = [other for other in all_players if other != player]
    if not others:
        return None
    return random.choice(others)


def normalize_whole_value(value):
    return max(1, int(round(abs(float(value)))))


def protected_from_negative(player, effect_name):
    if player.consume_shield():
        return f"{player.name} da dung La chan de chan {effect_name}!"
    return None


def swap_scores(player, target):
    player_score = player.score
    target_score = target.score
    player.set_score(target_score)
    target.set_score(player_score)


def apply_builtin_effect(effect_id, player, all_players=None, game_state=None):
    play_effect(effect_id)

    if effect_id in NEGATIVE_BUILTIN_IDS:
        blocked_message = protected_from_negative(player, get_effect_definition(effect_id, include_custom=False)["label"])
        if blocked_message:
            return blocked_message

    if effect_id == "angel":
        player.add_score(15)
        return "Ban gap Thien than! +15 diem."
    if effect_id == "devil":
        player.subtract_score(25)
        return "Ban gap Ac quy! -25 diem."
    if effect_id == "gun":
        target = choose_random_other(player, all_players)
        if target is None:
            return "Khong the cuop diem vi khong co nguoi choi khac."
        target.subtract_score(20)
        player.add_score(20)
        player.record_steal(20)
        return f"{player.name} da cuop 20 diem tu {target.name}!"
    if effect_id == "lucky":
        player.add_score(30)
        return "May man den! +30 diem."
    if effect_id == "lottery":
        player.add_score(50)
        return "Trung so! +50 diem."
    if effect_id == "double":
        current_score = player.score
        player.add_score(current_score)
        return f"{player.name} duoc nhan doi so diem hien tai!"
    if effect_id == "half":
        lost_score = player.score // 2
        player.subtract_score(lost_score)
        return f"{player.name} bi chia doi diem, mat {lost_score} diem!"
    if effect_id == "rps":
        return "Keo bua bao!"
    return "Khong co hieu ung nao xay ra."


def apply_custom_effect(effect, player, all_players=None, game_state=None):
    effect_name = str(effect.get("name", "Hieu ung moi")).strip() or "Hieu ung moi"
    operation = str(effect.get("operation", "add_self"))
    value = abs(float(effect.get("value", 0)))
    value_text = format_number(value)

    if operation in NEGATIVE_CUSTOM_OPERATIONS:
        blocked_message = protected_from_negative(player, effect_name)
        if blocked_message:
            return blocked_message

    if operation == "add_self":
        player.add_score(value)
        return f"{player.name} gap {effect_name}! +{value_text} diem."
    if operation == "subtract_self":
        player.subtract_score(value)
        return f"{player.name} gap {effect_name}! -{value_text} diem."
    if operation == "multiply_self":
        old_score = player.score
        player.set_score(player.score * value)
        delta = player.score - old_score
        return f"{player.name} gap {effect_name}! Diem x{value_text} ({delta:+} diem)."
    if operation == "divide_self":
        if value == 0:
            return f"{effect_name} khong hop le vi khong the chia cho 0."
        old_score = player.score
        player.set_score(player.score / value)
        delta = player.score - old_score
        return f"{player.name} gap {effect_name}! Diem /{value_text} ({delta:+} diem)."
    if operation == "steal_random":
        target = choose_random_other(player, all_players)
        if target is None:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        transfer_amount = normalize_whole_value(value)
        target.subtract_score(transfer_amount)
        player.add_score(transfer_amount)
        player.record_steal(transfer_amount)
        return f"{player.name} dung {effect_name} va lay {transfer_amount} diem tu {target.name}!"
    if operation == "give_random":
        target = choose_random_other(player, all_players)
        if target is None:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        transfer_amount = normalize_whole_value(value)
        player.subtract_score(transfer_amount)
        target.add_score(transfer_amount)
        return f"{player.name} dung {effect_name} va cho {target.name} {transfer_amount} diem."
    if operation == "swap_random":
        target = choose_random_other(player, all_players)
        if target is None:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        swap_scores(player, target)
        return f"{player.name} dung {effect_name} va doi diem voi {target.name}!"
    if operation == "others_gain":
        others = [other for other in all_players or [] if other != player]
        if not others:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        transfer_amount = normalize_whole_value(value)
        for other in others:
            other.add_score(transfer_amount)
        return f"{effect_name}: tat ca nguoi choi khac duoc +{transfer_amount} diem."
    if operation == "others_lose":
        others = [other for other in all_players or [] if other != player]
        if not others:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        transfer_amount = normalize_whole_value(value)
        for other in others:
            other.subtract_score(transfer_amount)
        return f"{effect_name}: tat ca nguoi choi khac bi -{transfer_amount} diem."
    if operation == "all_gain":
        transfer_amount = normalize_whole_value(value)
        for current in all_players or [player]:
            current.add_score(transfer_amount)
        return f"{effect_name}: tat ca nguoi choi duoc +{transfer_amount} diem."
    if operation == "all_lose":
        transfer_amount = normalize_whole_value(value)
        for current in all_players or [player]:
            current.subtract_score(transfer_amount)
        return f"{effect_name}: tat ca nguoi choi bi -{transfer_amount} diem."
    if operation == "bonus_turn":
        extra_turns = normalize_whole_value(value)
        player.grant_bonus_turn(extra_turns)
        return f"{player.name} dung {effect_name} va nhan them {extra_turns} luot!"
    if operation == "shield_self":
        shield_count = normalize_whole_value(value)
        player.grant_shield(shield_count)
        return f"{player.name} dung {effect_name} va nhan {shield_count} La chan!"
    if operation == "skip_random":
        target = choose_random_other(player, all_players)
        if target is None:
            return f"{effect_name} can co nguoi choi khac moi dung duoc."
        skip_turns = normalize_whole_value(value)
        target.grant_skip_turn(skip_turns)
        return f"{player.name} dung {effect_name}! {target.name} se mat {skip_turns} luot."
    if operation == "reverse_order":
        if game_state is not None:
            current_direction = int(game_state.get("turn_direction", 1) or 1)
            game_state["turn_direction"] = -1 if current_direction > 0 else 1
        return f"{effect_name}: thu tu luot da bi dao chieu!"

    operation_label = CUSTOM_EFFECT_OPERATION_LABELS.get(operation, operation)
    return f"{effect_name} chua ho tro thao tac {operation_label}."


def apply_effect(effect_id, player, all_players=None, game_state=None):
    effect_definition = get_effect_definition(effect_id)
    if effect_definition is None:
        return "Khong tim thay hieu ung."

    effect_id = str(effect_definition.get("id"))
    builtin_ids = {effect["id"] for effect in BUILTIN_EFFECTS}
    if effect_id in builtin_ids:
        return apply_builtin_effect(effect_id, player, all_players, game_state)

    return apply_custom_effect(effect_definition, player, all_players, game_state)
