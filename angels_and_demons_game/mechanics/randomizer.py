
import random

# Tỷ lệ mặc định cho 6 hiệu ứng (chia đều)
DEFAULT_WEIGHTS = [1, 1, 1, 1, 1, 1, 0.5,0.5]
CUSTOM_WEIGHTS = None

def set_custom_weights(weights):
    global CUSTOM_WEIGHTS
    CUSTOM_WEIGHTS = weights

def get_random_effect(dist_mode="even"):
    if dist_mode == "even":
        return random.choices([1, 2, 3, 4, 5, 6, 7,8], weights=DEFAULT_WEIGHTS)[0]
    elif dist_mode == "custom" and CUSTOM_WEIGHTS:
        return random.choices([1, 2, 3, 4, 5, 6, 7,8], weights=CUSTOM_WEIGHTS)[0]
    else:
        return random.randint(1, 8)
