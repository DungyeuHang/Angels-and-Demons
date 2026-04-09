from dataclasses import dataclass
from dataclasses import field
from typing import Any

from models.turn_modes import SEQUENTIAL_TURN_MODE
from models.turn_modes import normalize_turn_mode


@dataclass
class BannerState:
    message: str = ""
    effect_id: str | None = None
    created_at: int = 0


@dataclass
class SpotlightState:
    effect_id: str | None = None
    message: str = ""
    player_name: str = ""
    box_number: int | None = None
    title: str = "Bat ngo"
    created_at: int = 0


@dataclass
class PendingEffectState:
    effect_id: str
    player_index: int
    box_number: int | None = None


@dataclass
class ScorePopupState:
    player_index: int
    delta: int
    created_at: int
    box_number: int | None = None
    label: str = ""


@dataclass
class ComboBannerState:
    label: str = ""
    effect_id: str | None = None
    created_at: int = 0
    player_name: str = ""


@dataclass
class GameSession:
    players: list
    num_boxes: int
    dist_mode: str = "even"
    custom_weights: dict | None = None
    turn_mode: str = SEQUENTIAL_TURN_MODE
    layout_id: str = "classic"
    match_preset: str = "classic"
    mode_variant: str = "standard"
    challenge_id: str = ""
    challenge_title: str = ""
    series_target_wins: int = 1
    round_number: int = 1
    turn_direction: int = 1
    boxes: list[int] = field(default_factory=list)
    opened: set[int] = field(default_factory=set)
    box_effects: dict[int, dict[str, Any]] = field(default_factory=dict)
    current_player: int | None = None
    banner: BannerState | None = None
    spotlight: SpotlightState | None = None
    waiting_effect_input: bool = False
    pending_effect: PendingEffectState | None = None
    reveal_lock_until: int = 0
    flip_duration: int = 320
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    opened_effect_counts: dict[str, int] = field(default_factory=dict)
    help_visible: bool = False
    score_popups: list[ScorePopupState] = field(default_factory=list)
    combo_banner: ComboBannerState | None = None
    player_reactions: dict[int, dict[str, Any]] = field(default_factory=dict)
    bot_action_due_at: int = 0
    result_saved: bool = False
    unlocked_achievements: list[dict[str, Any]] = field(default_factory=list)
    profile_summary: dict[str, Any] = field(default_factory=dict)
    match_notes: list[str] = field(default_factory=list)
    tooltips_visible: bool = True

    def __post_init__(self):
        self.turn_mode = normalize_turn_mode(self.turn_mode)
        self.num_boxes = max(1, int(self.num_boxes))
        self.series_target_wins = max(1, int(self.series_target_wins or 1))
        self.round_number = max(1, int(self.round_number or 1))
        if not self.boxes:
            self.boxes = list(range(1, self.num_boxes + 1))
        if self.current_player is None and self.turn_mode == SEQUENTIAL_TURN_MODE and self.players:
            self.current_player = 0

    @property
    def remaining_boxes(self):
        return len(self.boxes) - len(self.opened)

    def build_effect_context(self):
        return {
            "turn_direction": self.turn_direction,
            "turn_mode": self.turn_mode,
        }

    def sync_effect_context(self, context):
        direction = int(context.get("turn_direction", self.turn_direction) or self.turn_direction)
        self.turn_direction = 1 if direction >= 0 else -1

    @property
    def has_bots(self):
        return any(getattr(player, "is_bot", False) for player in self.players)
