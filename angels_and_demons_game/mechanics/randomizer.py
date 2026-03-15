import random


EFFECT_IDS = [1, 2, 3, 4, 5, 6, 7, 8]
EFFECT_LABELS = [
    "Thien than",
    "Ac quy",
    "Sung",
    "May man",
    "Trung so",
    "Keo bua bao",
    "Nhan doi",
    "Chia doi",
]
DEFAULT_WEIGHTS = [1, 1, 1, 1, 1, 1, 0.5, 0.5]


def sanitize_weights(weights):
    if not isinstance(weights, list) or len(weights) != len(EFFECT_IDS):
        return DEFAULT_WEIGHTS.copy()

    cleaned_weights = []
    for weight in weights:
        try:
            cleaned_weights.append(max(0.0, float(weight)))
        except (TypeError, ValueError):
            cleaned_weights.append(0.0)

    return cleaned_weights if any(cleaned_weights) else DEFAULT_WEIGHTS.copy()


def get_random_effect(dist_mode="even", custom_weights=None):
    if dist_mode == "custom":
        weights = sanitize_weights(custom_weights)
    else:
        weights = DEFAULT_WEIGHTS

    return random.choices(EFFECT_IDS, weights=weights)[0]
