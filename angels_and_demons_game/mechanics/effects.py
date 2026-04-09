import random

from models.custom_effects import CUSTOM_EFFECT_OPERATION_LABELS
from models.custom_effects import load_custom_effects
from ui.audio import play_sfx

BUILTIN_EFFECTS = [
    {
        "id": "angel",
        "label": "Thien than",
        "default_weight": 1.0,
        "value": 18,
        "tooltip": "Nhan ngay 18 diem. On dinh, an toan va hop de gap luc dang am diem.",
    },
    {
        "id": "devil",
        "label": "Ac quy",
        "default_weight": 1.0,
        "value": 22,
        "tooltip": "Mat 22 diem, nhung co the duoc La chan chan lai.",
    },
    {
        "id": "gun",
        "label": "Sung",
        "default_weight": 1.0,
        "value": 18,
        "tooltip": "Lay 18 diem tu mot nguoi choi ngau nhien. Hieu qua trong tran dong nguoi.",
    },
    {
        "id": "lucky",
        "label": "May man",
        "default_weight": 1.0,
        "value": 26,
        "tooltip": "Nhan 26 diem. Tot hon Thien than mot chut va de lap combo.",
    },
    {
        "id": "lottery",
        "label": "Trung so",
        "default_weight": 1.0,
        "value": 42,
        "tooltip": "No diem lon voi 42 diem. Ty le trung van hiem hon cac effect cong diem thuong.",
    },
    {
        "id": "rps",
        "label": "Keo bua bao",
        "default_weight": 1.0,
        "value": 12,
        "tooltip": "Nhan 1 de thang, 2 de thua. Neu thang duoc 12 diem.",
    },
    {
        "id": "double",
        "label": "Nhan doi",
        "default_weight": 0.5,
        "tooltip": "Nhan doi diem hien tai. Neu dang 0 hoac am se nhan cuu tro nho de khong qua hut hang.",
    },
    {
        "id": "half",
        "label": "Chia doi",
        "default_weight": 0.5,
        "tooltip": "Mat mot nua tong diem hien tai. Cang cao diem cang nguy hiem.",
    },
]

CUSTOM_ONLY_EFFECTS = [
    {
        "id": "shield",
        "label": "La chan",
        "default_weight": 0.0,
        "custom_only": True,
        "tooltip": "Nhan 1 la chan. Tu dong chan mot effect xau sap toi.",
    },
    {
        "id": "swap",
        "label": "Doi menh",
        "default_weight": 0.0,
        "custom_only": True,
        "tooltip": "Hoan doi tong diem voi mot nguoi choi ngau nhien.",
    },
    {
        "id": "reverse",
        "label": "Dao chieu",
        "default_weight": 0.0,
        "custom_only": True,
        "tooltip": "Dao nguoc huong luot hien tai. Cang dong nguoi cang kho doan.",
    },
    {
        "id": "oracle",
        "label": "Tien tri",
        "default_weight": 0.0,
        "custom_only": True,
        "tooltip": "Soi truoc 3 o chua mo trong vai giay, cuc hop de set combo.",
    },
]

NEGATIVE_BUILTIN_IDS = {"devil", "half"}
NEGATIVE_CUSTOM_OPERATIONS = {"subtract_self", "divide_self", "give_random", "all_lose"}


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


def get_custom_only_effects():
    return [dict(effect) for effect in CUSTOM_ONLY_EFFECTS]


def get_all_effects(include_custom=True):
    effects = get_builtin_effects()
    if include_custom:
        effects.extend(get_custom_only_effects())
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


def get_effect_label(effect_id, fallback=None):
    effect_definition = get_effect_definition(effect_id)
    if effect_definition:
        return str(effect_definition.get("label") or effect_definition.get("name") or effect_id)
    return str(fallback if fallback is not None else effect_id)


def get_effect_help(effect_id):
    effect_definition = get_effect_definition(effect_id)
    if effect_definition is None:
        return "Khong tim thay mo ta cho effect nay."

    tooltip = str(effect_definition.get("tooltip", "")).strip()
    if tooltip:
        return tooltip

    if effect_definition.get("is_custom"):
        operation_label = CUSTOM_EFFECT_OPERATION_LABELS.get(effect_definition.get("operation"), effect_definition.get("operation", "custom"))
        value = format_number(effect_definition.get("value", 0))
        return f"Effect custom: {operation_label}, gia tri {value}."

    return f"Effect {get_effect_label(effect_id)}."


def play_effect(effect_id, stop_others=True):
    play_sfx(str(effect_id), stop_others=stop_others)


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
    effect_definition = get_effect_definition(effect_id, include_custom=False) or {}

    if effect_id in NEGATIVE_BUILTIN_IDS:
        blocked_message = protected_from_negative(player, effect_definition.get("label", effect_id))
        if blocked_message:
            return blocked_message

    if effect_id == "angel":
        gain = int(effect_definition.get("value", 18))
        player.add_score(gain)
        return f"Ban gap Thien than! +{gain} diem."
    if effect_id == "devil":
        loss = int(effect_definition.get("value", 22))
        player.subtract_score(loss)
        return f"Ban gap Ac quy! -{loss} diem."
    if effect_id == "gun":
        target = choose_random_other(player, all_players)
        if target is None:
            return "Khong the cuop diem vi khong co nguoi choi khac."
        transfer_amount = int(effect_definition.get("value", 18))
        target.subtract_score(transfer_amount)
        player.add_score(transfer_amount)
        player.record_steal(transfer_amount)
        return f"{player.name} da cuop {transfer_amount} diem tu {target.name}!"
    if effect_id == "lucky":
        gain = int(effect_definition.get("value", 26))
        player.add_score(gain)
        return f"May man den! +{gain} diem."
    if effect_id == "lottery":
        gain = int(effect_definition.get("value", 42))
        player.add_score(gain)
        return f"Trung so! +{gain} diem."
    if effect_id == "double":
        current_score = player.score
        if current_score <= 0:
            rescue_gain = 10
            player.add_score(rescue_gain)
            return f"{player.name} gap Nhan doi khi diem thap, nhan +{rescue_gain} diem cuu tro!"
        player.add_score(current_score)
        return f"{player.name} duoc nhan doi so diem hien tai!"
    if effect_id == "half":
        lost_score = player.score // 2
        player.subtract_score(lost_score)
        return f"{player.name} bi chia doi diem, mat {lost_score} diem!"
    if effect_id == "shield":
        player.grant_shield(1)
        return f"{player.name} nhan 1 La chan!"
    if effect_id == "swap":
        target = choose_random_other(player, all_players)
        if target is None:
            return "Khong the doi diem vi khong co nguoi choi khac."
        swap_scores(player, target)
        return f"{player.name} da doi diem voi {target.name}!"
    if effect_id == "reverse":
        if game_state is not None:
            current_direction = int(game_state.get("turn_direction", 1) or 1)
            game_state["turn_direction"] = -1 if current_direction > 0 else 1
        return "Thu tu luot da bi dao chieu!"
    if effect_id == "oracle":
        return "Tien tri dang soi cac o an."
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
    system_effect_ids = {effect["id"] for effect in BUILTIN_EFFECTS + CUSTOM_ONLY_EFFECTS}
    if effect_id in system_effect_ids:
        return apply_builtin_effect(effect_id, player, all_players, game_state)

    return apply_custom_effect(effect_definition, player, all_players, game_state)
