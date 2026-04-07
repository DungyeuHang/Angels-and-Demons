import random

from mechanics.effects import get_all_effects
from mechanics.effects import get_builtin_effects


def build_default_weight_map(include_custom=True):
    effects = get_all_effects(include_custom=include_custom)
    weights = {}
    for effect in effects:
        effect_id = str(effect["id"])
        if effect.get("is_custom"):
            weights[effect_id] = 0.0
        else:
            weights[effect_id] = float(effect.get("default_weight", 1.0))
    return weights


def sanitize_weights(weights, include_custom=True, fallback_to_defaults=True):
    effects = get_all_effects(include_custom=include_custom)
    default_weights = build_default_weight_map(include_custom=include_custom)
    cleaned_weights = {}

    if isinstance(weights, list):
        builtin_effects = get_builtin_effects()
        for index, effect in enumerate(builtin_effects):
            effect_id = str(effect["id"])
            try:
                cleaned_weights[effect_id] = max(0.0, float(weights[index]))
            except (IndexError, TypeError, ValueError):
                cleaned_weights[effect_id] = default_weights[effect_id]
    elif isinstance(weights, dict):
        for effect in effects:
            effect_id = str(effect["id"])
            raw_weight = weights.get(effect_id, weights.get(effect["id"])) if isinstance(weights, dict) else None
            try:
                cleaned_weights[effect_id] = max(0.0, float(raw_weight))
            except (TypeError, ValueError):
                cleaned_weights[effect_id] = default_weights[effect_id]

    for effect in effects:
        effect_id = str(effect["id"])
        if effect_id not in cleaned_weights:
            cleaned_weights[effect_id] = default_weights[effect_id]

    if fallback_to_defaults and not any(cleaned_weights.values()):
        return default_weights
    return cleaned_weights


def get_effect_labels(include_custom=True):
    return {
        str(effect["id"]): str(effect.get("label", effect.get("name", effect["id"])))
        for effect in get_all_effects(include_custom=include_custom)
    }


def get_random_effect(dist_mode="even", custom_weights=None):
    if dist_mode == "custom":
        effects = get_all_effects(include_custom=True)
        weights = sanitize_weights(custom_weights, include_custom=True)
    else:
        effects = get_builtin_effects()
        weights = build_default_weight_map(include_custom=False)

    effect_ids = [str(effect["id"]) for effect in effects]
    weight_values = [weights[str(effect["id"])] for effect in effects]
    return random.choices(effect_ids, weights=weight_values)[0]
