import json
import os

from constants import DEFAULT_SETTINGS
from models.history import get_user_data_dir


SETTINGS_FILE_NAME = "settings.json"


def get_settings_file_path():
    return os.path.join(get_user_data_dir(), SETTINGS_FILE_NAME)


def _clamp_volume(value, fallback):
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return float(fallback)


def sanitize_settings(raw_settings=None):
    settings = dict(DEFAULT_SETTINGS)
    raw_settings = raw_settings if isinstance(raw_settings, dict) else {}

    settings["music_enabled"] = bool(raw_settings.get("music_enabled", settings["music_enabled"]))
    settings["sfx_enabled"] = bool(raw_settings.get("sfx_enabled", settings["sfx_enabled"]))
    settings["fullscreen"] = bool(raw_settings.get("fullscreen", settings["fullscreen"]))
    settings["reduce_motion"] = bool(raw_settings.get("reduce_motion", settings["reduce_motion"]))
    settings["music_volume"] = _clamp_volume(raw_settings.get("music_volume"), settings["music_volume"])
    settings["sfx_volume"] = _clamp_volume(raw_settings.get("sfx_volume"), settings["sfx_volume"])
    return settings


def load_settings():
    filepath = get_settings_file_path()
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)
    return sanitize_settings(data)


def write_settings(settings):
    os.makedirs(get_user_data_dir(), exist_ok=True)
    sanitized = sanitize_settings(settings)
    with open(get_settings_file_path(), "w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2, ensure_ascii=False)
    return sanitized


def update_settings(changes):
    settings = load_settings()
    if isinstance(changes, dict):
        settings.update(changes)
    return write_settings(settings)
