import json
import os
from datetime import datetime

from constants import ACHIEVEMENT_DEFINITIONS
from mechanics.effects import get_builtin_effects
from models.history import get_user_data_dir


PROFILE_FILE_NAME = "profile.json"


def get_profile_file_path():
    return os.path.join(get_user_data_dir(), PROFILE_FILE_NAME)


def _default_profile():
    return {
        "games_played": 0,
        "games_vs_bot": 0,
        "wins_by_name": {},
        "top_effect_counts": {},
        "career_best_score": 0,
        "largest_swing": 0,
        "total_boxes_opened": 0,
        "total_steal_points": 0,
        "builtin_effects_seen": [],
        "achievements": {},
        "last_winner": "",
        "last_played_at": "",
    }


def _sanitize_dict_counts(raw_counts):
    cleaned = {}
    if not isinstance(raw_counts, dict):
        return cleaned
    for key, value in raw_counts.items():
        try:
            cleaned[str(key)] = int(value)
        except (TypeError, ValueError):
            continue
    return cleaned


def sanitize_profile(raw_profile=None):
    profile = _default_profile()
    raw_profile = raw_profile if isinstance(raw_profile, dict) else {}

    for key in ("games_played", "games_vs_bot", "career_best_score", "largest_swing", "total_boxes_opened", "total_steal_points"):
        try:
            profile[key] = max(0, int(raw_profile.get(key, profile[key])))
        except (TypeError, ValueError):
            pass

    profile["wins_by_name"] = _sanitize_dict_counts(raw_profile.get("wins_by_name"))
    profile["top_effect_counts"] = _sanitize_dict_counts(raw_profile.get("top_effect_counts"))
    profile["builtin_effects_seen"] = sorted({str(effect_id) for effect_id in raw_profile.get("builtin_effects_seen", [])})
    achievements = raw_profile.get("achievements")
    profile["achievements"] = achievements if isinstance(achievements, dict) else {}
    profile["last_winner"] = str(raw_profile.get("last_winner", "") or "")
    profile["last_played_at"] = str(raw_profile.get("last_played_at", "") or "")
    return profile


def load_profile():
    filepath = get_profile_file_path()
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_profile()
    return sanitize_profile(data)


def write_profile(profile):
    os.makedirs(get_user_data_dir(), exist_ok=True)
    sanitized = sanitize_profile(profile)
    with open(get_profile_file_path(), "w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=2, ensure_ascii=False)
    return sanitized


def _unlock_achievement(profile, unlocked, achievement_id):
    if achievement_id in profile["achievements"]:
        return
    definition = ACHIEVEMENT_DEFINITIONS.get(achievement_id)
    if not definition:
        return
    unlocked_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profile["achievements"][achievement_id] = {
        "title": definition["title"],
        "description": definition["description"],
        "unlocked_at": unlocked_at,
    }
    unlocked.append({
        "id": achievement_id,
        "title": definition["title"],
        "description": definition["description"],
        "unlocked_at": unlocked_at,
    })


def record_session_progress(session):
    profile = load_profile()
    unlocked = []
    players = list(session.players)
    winner = max(players, key=lambda player: player.score) if players else None

    profile["games_played"] += 1
    profile["games_vs_bot"] += 1 if any(getattr(player, "is_bot", False) for player in players) else 0
    profile["career_best_score"] = max(profile["career_best_score"], max((player.score for player in players), default=0))
    profile["largest_swing"] = max(profile["largest_swing"], max((player.biggest_gain for player in players), default=0))
    profile["total_boxes_opened"] += sum(player.boxes_opened for player in players)
    profile["total_steal_points"] += sum(player.steal_points for player in players)
    profile["last_winner"] = winner.name if winner else ""
    profile["last_played_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if winner:
        profile["wins_by_name"][winner.name] = profile["wins_by_name"].get(winner.name, 0) + 1

    for effect_id, count in session.opened_effect_counts.items():
        profile["top_effect_counts"][effect_id] = profile["top_effect_counts"].get(effect_id, 0) + int(count)

    builtin_ids = {str(effect["id"]) for effect in get_builtin_effects()}
    seen = set(profile["builtin_effects_seen"])
    seen.update(effect_id for effect_id in session.opened_effect_counts if effect_id in builtin_ids)
    profile["builtin_effects_seen"] = sorted(seen)

    _unlock_achievement(profile, unlocked, "first_match")
    if session.opened_effect_counts.get("angel", 0) >= 3:
        _unlock_achievement(profile, unlocked, "angel_favored")
    if any(player.steal_points >= 60 for player in players):
        _unlock_achievement(profile, unlocked, "loot_king")
    if any(player.biggest_gain >= 50 for player in players):
        _unlock_achievement(profile, unlocked, "lucky_burst")
    if int(session.num_boxes) >= 70:
        _unlock_achievement(profile, unlocked, "marathon_clear")
    if winner and session.mode_variant == "challenge" and not getattr(winner, "is_bot", False):
        _unlock_achievement(profile, unlocked, "challenge_cleared")
    if (
        winner
        and session.series_target_wins > 1
        and not getattr(winner, "is_bot", False)
        and "series_champion" in list(getattr(session, "match_notes", []))
    ):
        _unlock_achievement(profile, unlocked, "series_champion")
    if builtin_ids and builtin_ids.issubset(set(profile["builtin_effects_seen"])):
        _unlock_achievement(profile, unlocked, "effect_collector")

    profile = write_profile(profile)
    summary = build_profile_summary(profile)
    return profile, summary, unlocked


def build_profile_summary(profile=None):
    profile = sanitize_profile(profile or load_profile())
    ranked_players = sorted(profile["wins_by_name"].items(), key=lambda item: (-item[1], item[0]))
    ranked_effects = sorted(profile["top_effect_counts"].items(), key=lambda item: (-item[1], item[0]))
    achievements = [item for key, item in profile["achievements"].items() if key != "bot_buster"]
    achievements.sort(key=lambda item: item.get("unlocked_at", ""), reverse=True)

    return {
        "games_played": profile["games_played"],
        "games_vs_bot": profile["games_vs_bot"],
        "career_best_score": profile["career_best_score"],
        "largest_swing": profile["largest_swing"],
        "total_boxes_opened": profile["total_boxes_opened"],
        "total_steal_points": profile["total_steal_points"],
        "top_players": ranked_players[:5],
        "top_effects": ranked_effects[:5],
        "achievements": achievements,
        "achievement_count": len(achievements),
        "last_winner": profile["last_winner"],
        "last_played_at": profile["last_played_at"],
    }
