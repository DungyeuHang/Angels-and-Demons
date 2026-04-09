import json
import os
from datetime import datetime


APP_DIR_NAME = "Angels and Demons"
HISTORY_FILE_NAME = "histories.json"


def get_user_data_dir():
    appdata = os.getenv("APPDATA")
    if appdata:
        return os.path.join(appdata, APP_DIR_NAME)

    fallback_root = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(fallback_root, APP_DIR_NAME)


def get_history_file_path():
    return os.path.join(get_user_data_dir(), HISTORY_FILE_NAME)


def load_game_history():
    filepath = get_history_file_path()
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            history = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    return history if isinstance(history, list) else []


def write_game_history(history):
    os.makedirs(get_user_data_dir(), exist_ok=True)
    with open(get_history_file_path(), "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2, ensure_ascii=False)


def save_game_history_entry(players, metadata=None):
    metadata = metadata or {}
    history = load_game_history()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": [{"name": player.name, "score": player.score} for player in players],
    }
    for key in (
        "winner",
        "winner_score",
        "num_boxes",
        "opened_count",
        "turn_mode",
        "layout_id",
        "match_preset",
        "mode_variant",
        "challenge_id",
        "challenge_title",
        "series_target_wins",
        "round_number",
        "has_bots",
        "player_roster",
        "top_effects",
        "unlocked_achievements",
    ):
        if key in metadata:
            entry[key] = metadata[key]
    history.append(entry)
    write_game_history(history)


def delete_game_history_entry(index):
    history = load_game_history()
    if 0 <= index < len(history):
        del history[index]
        write_game_history(history)


def clear_game_history():
    write_game_history([])
