import json
import os
import uuid

from models.history import get_user_data_dir


CUSTOM_EFFECTS_FILE_NAME = "custom_effects.json"

CUSTOM_EFFECT_OPERATION_OPTIONS = [
    {"id": "add_self", "label": "+ diem ban than"},
    {"id": "subtract_self", "label": "- diem ban than"},
    {"id": "multiply_self", "label": "x diem ban than"},
    {"id": "divide_self", "label": "/ diem ban than"},
    {"id": "steal_random", "label": "lay diem nguoi ngau nhien"},
    {"id": "give_random", "label": "cho diem nguoi ngau nhien"},
    {"id": "swap_random", "label": "doi diem voi nguoi ngau nhien"},
    {"id": "others_gain", "label": "nguoi khac + diem"},
    {"id": "others_lose", "label": "nguoi khac - diem"},
    {"id": "all_gain", "label": "tat ca + diem"},
    {"id": "all_lose", "label": "tat ca - diem"},
    {"id": "bonus_turn", "label": "them luot cho ban than"},
    {"id": "shield_self", "label": "nhan la chan"},
    {"id": "skip_random", "label": "nguoi ngau nhien mat luot"},
    {"id": "reverse_order", "label": "dao chieu thu tu luot"},
]

CUSTOM_EFFECT_OPERATION_LABELS = {
    option["id"]: option["label"]
    for option in CUSTOM_EFFECT_OPERATION_OPTIONS
}


def get_custom_effects_file_path():
    return os.path.join(get_user_data_dir(), CUSTOM_EFFECTS_FILE_NAME)


def sanitize_custom_effect(effect):
    if not isinstance(effect, dict):
        return None

    effect_id = str(effect.get("id", "")).strip()
    effect_name = str(effect.get("name", "")).strip()
    operation = str(effect.get("operation", "")).strip()

    if not effect_name or operation not in CUSTOM_EFFECT_OPERATION_LABELS:
        return None

    try:
        value = abs(float(effect.get("value", 0)))
    except (TypeError, ValueError):
        return None

    if value <= 0:
        return None

    if not effect_id:
        effect_id = f"custom_{uuid.uuid4().hex[:8]}"

    return {
        "id": effect_id,
        "name": effect_name,
        "operation": operation,
        "value": value,
        "is_custom": True,
        "label": effect_name,
    }


def load_custom_effects():
    filepath = get_custom_effects_file_path()
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            effects = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(effects, list):
        return []

    sanitized_effects = []
    for effect in effects:
        clean_effect = sanitize_custom_effect(effect)
        if clean_effect is not None:
            sanitized_effects.append(clean_effect)
    return sanitized_effects


def write_custom_effects(effects):
    os.makedirs(get_user_data_dir(), exist_ok=True)
    with open(get_custom_effects_file_path(), "w", encoding="utf-8") as file:
        json.dump(effects, file, indent=2, ensure_ascii=False)


def save_custom_effect(effect_data, original_id=None):
    clean_effect = sanitize_custom_effect(effect_data)
    if clean_effect is None:
        raise ValueError("Custom effect data is invalid.")

    effects = load_custom_effects()
    updated_effects = []
    replaced = False
    for effect in effects:
        effect_id = str(effect.get("id", "")).strip()
        if original_id and effect_id == original_id:
            updated_effects.append(clean_effect)
            replaced = True
        elif not original_id and effect_id == clean_effect["id"]:
            updated_effects.append(clean_effect)
            replaced = True
        else:
            updated_effects.append(effect)

    if not replaced:
        updated_effects.append(clean_effect)

    write_custom_effects(updated_effects)
    return clean_effect


def delete_custom_effect(effect_id):
    filtered_effects = [
        effect for effect in load_custom_effects()
        if str(effect.get("id", "")).strip() != str(effect_id).strip()
    ]
    write_custom_effects(filtered_effects)
