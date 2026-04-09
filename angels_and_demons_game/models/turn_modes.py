SEQUENTIAL_TURN_MODE = "sequential"
MANUAL_TURN_MODE = "manual"

TURN_MODE_LABELS = {
    SEQUENTIAL_TURN_MODE: "Lần lượt",
    MANUAL_TURN_MODE: "Tự chọn người chơi",
}


def normalize_turn_mode(turn_mode):
    if turn_mode in TURN_MODE_LABELS:
        return turn_mode
    return SEQUENTIAL_TURN_MODE
