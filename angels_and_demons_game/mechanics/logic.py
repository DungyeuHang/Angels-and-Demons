import random

from constants import AI_LEVELS
from constants import EFFECT_AI_SCORES
from mechanics.effects import apply_effect
from mechanics.effects import get_effect_definition
from mechanics.effects import get_effect_label
from mechanics.effects import play_effect
from mechanics.randomizer import get_random_effect
from models.game_state import BannerState
from models.game_state import ComboBannerState
from models.game_state import GameSession
from models.game_state import PendingEffectState
from models.game_state import ScorePopupState
from models.game_state import SpotlightState
from models.turn_modes import MANUAL_TURN_MODE
from ui.audio import play_sfx


MAX_RECENT_EVENTS = 5
PREVIEW_REVEAL_COUNT = 3
PREVIEW_REVEAL_DURATION = 3200


def build_box_effects(num_boxes, dist_mode="even", custom_weights=None):
    return {
        box_number: {
            "effect_id": get_random_effect(dist_mode, custom_weights),
            "opened_at": 0,
            "flip_started_at": 0,
            "preview_until": 0,
        }
        for box_number in range(1, int(num_boxes) + 1)
    }


def create_game_session(players, num_boxes, dist_mode="even", custom_weights=None, turn_mode=None, session_options=None):
    session_options = session_options or {}
    session = GameSession(
        players=players,
        num_boxes=num_boxes,
        dist_mode=dist_mode,
        custom_weights=custom_weights,
        turn_mode=turn_mode,
        layout_id=str(session_options.get("layout_id", "classic")),
        match_preset=str(session_options.get("match_preset", "classic")),
        mode_variant=str(session_options.get("mode_variant", "standard")),
        challenge_id=str(session_options.get("challenge_id", "")),
        challenge_title=str(session_options.get("challenge_title", "")),
        series_target_wins=int(session_options.get("series_target_wins", 1) or 1),
        round_number=int(session_options.get("round_number", 1) or 1),
    )
    session.box_effects = build_box_effects(session.num_boxes, dist_mode, custom_weights)
    return session


def set_banner_message(message, effect_id=None, created_at=0):
    return BannerState(
        message=str(message or ""),
        effect_id=effect_id,
        created_at=created_at,
    )


def set_spotlight_message(effect_id, message, created_at=0, player_name=None, box_number=None):
    return SpotlightState(
        effect_id=effect_id,
        message=str(message or ""),
        player_name=str(player_name or ""),
        box_number=box_number,
        title=get_effect_label(effect_id, fallback="Bat ngo"),
        created_at=created_at,
    )


def append_skip_notice(message, skipped_names):
    if not skipped_names:
        return message
    if len(skipped_names) == 1:
        return f"{message} {skipped_names[0]} bi bo qua luot."
    return f"{message} {', '.join(skipped_names)} bi bo qua luot."


def add_recent_event(session, message, effect_id=None, player_name=None):
    session.recent_events.insert(
        0,
        {
            "message": str(message or ""),
            "effect_id": effect_id,
            "player_name": str(player_name or ""),
        },
    )
    session.recent_events = session.recent_events[:MAX_RECENT_EVENTS]


def consume_pending_skip(player):
    if player.consume_skip_turn():
        return f"{player.name} bi mat 1 luot!"
    return None


def snapshot_scores(session):
    return {
        index: player.score
        for index, player in enumerate(session.players)
    }


def register_score_changes(session, score_snapshot, tick, box_number=None):
    positive_seen = False
    negative_seen = False
    best_positive = None
    best_negative = None

    for player_index, player in enumerate(session.players):
        delta = player.score - score_snapshot.get(player_index, player.score)
        if not delta:
            continue

        session.score_popups.append(
            ScorePopupState(
                player_index=player_index,
                delta=delta,
                created_at=tick,
                box_number=box_number,
                label=f"{delta:+} diem",
            )
        )
        session.player_reactions[player_index] = {
            "delta": delta,
            "created_at": tick,
            "until": tick + 900,
        }
        positive_seen = positive_seen or delta > 0
        negative_seen = negative_seen or delta < 0
        if delta > 0 and (best_positive is None or delta > best_positive[1]):
            best_positive = (player.name, delta)
        if delta < 0 and (best_negative is None or delta < best_negative[1]):
            best_negative = (player.name, delta)

    session.score_popups = [popup for popup in session.score_popups if tick - popup.created_at <= 1800]
    session.player_reactions = {
        player_index: reaction
        for player_index, reaction in session.player_reactions.items()
        if int(reaction.get("until", 0)) > tick
    }

    if positive_seen and not negative_seen:
        play_sfx("point_gain", volume_multiplier=0.8)
    elif negative_seen and not positive_seen:
        play_sfx("point_loss", volume_multiplier=0.78)

    if best_positive is not None and best_positive[1] >= 40:
        label = f"Combo dep! {best_positive[0]} +{best_positive[1]} diem"
        session.combo_banner = ComboBannerState(label=label, effect_id="lucky", created_at=tick, player_name=best_positive[0])
    elif best_negative is not None and best_negative[1] <= -28:
        label = f"Pha rung san! {best_negative[0]} {best_negative[1]} diem"
        session.combo_banner = ComboBannerState(label=label, effect_id="devil", created_at=tick, player_name=best_negative[0])


def resolve_next_player(session, current_player=None):
    current_player = session.current_player if current_player is None else current_player
    if current_player is None or not session.players:
        return []

    active_player = session.players[current_player]
    if active_player.consume_bonus_turn():
        session.current_player = current_player
        return []

    if session.turn_mode == MANUAL_TURN_MODE:
        session.current_player = current_player
        return []

    skipped_names = []
    next_player = current_player
    total_players = len(session.players)
    for _ in range(total_players):
        next_player = (next_player + session.turn_direction) % total_players
        if session.players[next_player].consume_skip_turn():
            skipped_names.append(session.players[next_player].name)
            continue
        session.current_player = next_player
        return skipped_names

    session.current_player = next_player
    return skipped_names


def set_selected_player(session, player_index, tick):
    if player_index < 0 or player_index >= len(session.players):
        return False

    skip_message = consume_pending_skip(session.players[player_index])
    if skip_message:
        if session.current_player == player_index:
            session.current_player = None
        session.banner = set_banner_message(skip_message, "skip", tick)
        add_recent_event(session, skip_message, "skip", session.players[player_index].name)
        return True

    session.current_player = player_index
    session.banner = set_banner_message(f"Da chon {session.players[player_index].name}.", "shield", tick)
    return True


def handle_active_player_skip(session, tick):
    if session.current_player is None:
        return False

    active_player = session.players[session.current_player]
    if active_player.skip_turns <= 0:
        return False

    message = consume_pending_skip(active_player)
    skipped_names = resolve_next_player(session, session.current_player)
    full_message = append_skip_notice(message, skipped_names)
    session.banner = set_banner_message(full_message, "skip", tick)
    add_recent_event(session, full_message, "skip", active_player.name)
    return True


def reveal_unopened_boxes(session, tick, preview_count=PREVIEW_REVEAL_COUNT, preview_duration=PREVIEW_REVEAL_DURATION):
    unopened_boxes = [box_number for box_number in session.boxes if box_number not in session.opened]
    if not unopened_boxes:
        return []

    revealed_boxes = random.sample(unopened_boxes, min(preview_count, len(unopened_boxes)))
    preview_until = tick + preview_duration
    for box_number in revealed_boxes:
        session.box_effects[box_number]["preview_until"] = preview_until
    return sorted(revealed_boxes)


def handle_oracle_effect(session, active_player, box_number, tick):
    revealed_boxes = reveal_unopened_boxes(session, tick)
    if revealed_boxes:
        box_list = ", ".join(str(number) for number in revealed_boxes)
        return f"{active_player.name} gap Tien tri! Lo 3 o trong vai giay: {box_list}."
    return f"{active_player.name} gap Tien tri, nhung khong con o nao de soi truoc."


def open_box(session, box_number, tick):
    if box_number in session.opened:
        return False
    if session.current_player is None:
        session.banner = set_banner_message("Hay chon nguoi choi truoc khi mo o.", "shield", tick)
        return False

    active_player = session.players[session.current_player]
    session.opened.add(box_number)
    active_player.record_turn()
    active_player.record_box_opened()
    score_snapshot = snapshot_scores(session)

    box_meta = session.box_effects[box_number]
    effect_id = str(box_meta.get("effect_id"))
    box_meta["opened_at"] = tick
    box_meta["flip_started_at"] = tick
    session.reveal_lock_until = tick + session.flip_duration
    session.opened_effect_counts[effect_id] = session.opened_effect_counts.get(effect_id, 0) + 1
    play_sfx("box_flip", volume_multiplier=0.58)

    if effect_id == "rps":
        play_effect("rps")
        rps_message = f"{active_player.name} mo o {box_number} - Keo bua bao! Nhan 1 de thang, 2 de thua."
        session.banner = set_banner_message(rps_message, "rps", tick)
        session.spotlight = set_spotlight_message("rps", rps_message, tick, active_player.name, box_number)
        session.waiting_effect_input = True
        session.pending_effect = PendingEffectState(effect_id="rps", player_index=session.current_player, box_number=box_number)
        add_recent_event(session, rps_message, "rps", active_player.name)
        return True

    if effect_id == "oracle":
        play_effect("oracle")
        message = handle_oracle_effect(session, active_player, box_number, tick)
    else:
        effect_context = session.build_effect_context()
        message = apply_effect(effect_id, active_player, session.players, effect_context)
        session.sync_effect_context(effect_context)
        register_score_changes(session, score_snapshot, tick, box_number=box_number)

    skipped_names = resolve_next_player(session, session.current_player)
    full_message = append_skip_notice(f"{active_player.name} mo o {box_number} - {message}", skipped_names)
    session.banner = set_banner_message(full_message, effect_id, tick)
    session.spotlight = set_spotlight_message(effect_id, full_message, tick, active_player.name, box_number)
    add_recent_event(session, full_message, effect_id, active_player.name)
    return True


def resolve_rps_result(session, player_won, tick):
    if not session.pending_effect:
        return False

    player_index = session.pending_effect.player_index
    effect_player = session.players[player_index]
    score_snapshot = snapshot_scores(session)
    rps_value = int((get_effect_definition("rps", include_custom=False) or {}).get("value", 12))
    if player_won:
        effect_player.add_score(rps_value)
        base_message = f"{effect_player.name} thang Keo bua bao! +{rps_value} diem."
    else:
        base_message = f"{effect_player.name} thua Keo bua bao."
    register_score_changes(session, score_snapshot, tick, box_number=session.pending_effect.box_number)

    skipped_names = resolve_next_player(session, player_index)
    full_message = append_skip_notice(base_message, skipped_names)
    session.banner = set_banner_message(full_message, "rps", tick)
    session.spotlight = set_spotlight_message("rps", full_message, tick, effect_player.name)
    add_recent_event(session, full_message, "rps", effect_player.name)
    session.waiting_effect_input = False
    session.pending_effect = None
    return True


def get_effect_summary_rows(session, limit=3):
    ranked_effects = sorted(
        session.opened_effect_counts.items(),
        key=lambda item: (-item[1], get_effect_label(item[0])),
    )
    return [
        (effect_id, get_effect_label(effect_id, fallback=effect_id), count)
        for effect_id, count in ranked_effects[:limit]
    ]


def build_history_metadata(session):
    winner = None
    if session.players:
        winner = max(session.players, key=lambda player: player.score)
    return {
        "winner": winner.name if winner else "",
        "winner_score": winner.score if winner else 0,
        "num_boxes": session.num_boxes,
        "opened_count": len(session.opened),
        "turn_mode": session.turn_mode,
        "layout_id": session.layout_id,
        "match_preset": session.match_preset,
        "mode_variant": session.mode_variant,
        "challenge_id": session.challenge_id,
        "challenge_title": session.challenge_title,
        "series_target_wins": session.series_target_wins,
        "round_number": session.round_number,
        "has_bots": session.has_bots,
        "player_roster": [
            {
                "name": player.name,
                "is_bot": bool(getattr(player, "is_bot", False)),
                "ai_level": getattr(player, "ai_level", "normal"),
            }
            for player in session.players
        ],
        "top_effects": [
            {"id": effect_id, "label": label, "count": count}
            for effect_id, label, count in get_effect_summary_rows(session, limit=3)
        ],
    }


def get_bot_think_delay(player):
    ai_level = str(getattr(player, "ai_level", "normal") or "normal")
    return int(AI_LEVELS.get(ai_level, AI_LEVELS["normal"]).get("think_delay_ms", 620))


def score_previewed_box(session, player, box_number):
    effect_id = str(session.box_effects.get(box_number, {}).get("effect_id", ""))
    heuristic = EFFECT_AI_SCORES.get(effect_id, 6)

    if effect_id == "double" and player.score <= 0:
        heuristic = 10
    elif effect_id == "half" and player.score <= 1:
        heuristic = -6
    elif effect_id == "gun" and len(session.players) <= 1:
        heuristic = -8
    elif effect_id == "swap" and len(session.players) <= 1:
        heuristic = -6

    if player.score < 0 and effect_id in {"angel", "lucky", "lottery", "double"}:
        heuristic += 10
    return heuristic


def choose_bot_box(session, tick):
    if session.current_player is None:
        return None

    player = session.players[session.current_player]
    unopened_boxes = [box_number for box_number in session.boxes if box_number not in session.opened]
    if not unopened_boxes:
        return None

    ai_level = str(getattr(player, "ai_level", "normal") or "normal")
    ai_config = AI_LEVELS.get(ai_level, AI_LEVELS["normal"])
    previewed_boxes = [
        box_number
        for box_number in unopened_boxes
        if session.box_effects.get(box_number, {}).get("preview_until", 0) > tick
    ]

    if not previewed_boxes:
        return random.choice(unopened_boxes)

    ranked_previewed = sorted(
        previewed_boxes,
        key=lambda box_number: (score_previewed_box(session, player, box_number), -box_number),
        reverse=True,
    )
    best_preview = ranked_previewed[0]
    best_score = score_previewed_box(session, player, best_preview)
    preview_bias = float(ai_config.get("preview_bias", 0.7))
    hidden_boxes = [box_number for box_number in unopened_boxes if box_number not in previewed_boxes]

    if ai_level == "easy":
        if hidden_boxes and random.random() > preview_bias:
            return random.choice(hidden_boxes)
        return random.choice(ranked_previewed[: min(2, len(ranked_previewed))])

    if ai_level == "normal":
        if best_score >= 0 or not hidden_boxes:
            return best_preview
        return random.choice(hidden_boxes)

    if best_score > 0 or not hidden_boxes:
        return best_preview
    return random.choice(hidden_boxes)
