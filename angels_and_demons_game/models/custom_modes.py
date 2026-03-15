import json
import os

from models.history import get_user_data_dir


CUSTOM_MODES_FILE_NAME = "custom_modes.json"


def get_custom_modes_file_path():
    return os.path.join(get_user_data_dir(), CUSTOM_MODES_FILE_NAME)


def load_custom_modes():
    filepath = get_custom_modes_file_path()
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            modes = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    return modes if isinstance(modes, list) else []


def write_custom_modes(modes):
    os.makedirs(get_user_data_dir(), exist_ok=True)
    with open(get_custom_modes_file_path(), "w", encoding="utf-8") as file:
        json.dump(modes, file, indent=2, ensure_ascii=False)


def save_custom_mode(mode_data, original_name=None):
    modes = load_custom_modes()
    target_name = str(mode_data.get("name", "")).strip()
    updated_modes = []
    replaced = False

    for mode in modes:
        mode_name = str(mode.get("name", "")).strip()
        if original_name and mode_name == original_name:
            updated_modes.append(mode_data)
            replaced = True
        elif not original_name and mode_name == target_name:
            updated_modes.append(mode_data)
            replaced = True
        elif original_name and mode_name == target_name and mode_name != original_name:
            continue
        else:
            updated_modes.append(mode)

    if not replaced:
        updated_modes.append(mode_data)

    write_custom_modes(updated_modes)


def delete_custom_mode(mode_name):
    modes = [mode for mode in load_custom_modes() if str(mode.get("name", "")).strip() != mode_name]
    write_custom_modes(modes)


def get_custom_mode(mode_name):
    for mode in load_custom_modes():
        if str(mode.get("name", "")).strip() == mode_name:
            return mode
    return None
