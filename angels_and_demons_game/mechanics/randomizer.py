
import random

# Danh sách hiệu ứng từ 1 đến 6 đúng theo thứ tự trong effects.py
# 1: Thiên Thần, 2: Ác Quỷ, 3: May mắn, 4: Trúng xổ số, 5: Súng, 6: Kéo Búa Bao
EFFECT_IDS = [1, 2, 3, 4, 5, 6]

_saved_distribution = None  # Cache sau khi người dùng chọn xong

def get_even_distribution():
    return EFFECT_IDS, [1/6] * 6

def get_custom_distribution():
    print("Nhập tỷ lệ phần trăm cho từng hiệu ứng (tổng = 100):")
    labels = [
        "1. Thiên Thần",      # ID 1
        "2. Ác Quỷ",          # ID 2
        "3. May mắn",         # ID 3
        "4. Trúng xổ số",     # ID 4
        "5. Súng",            # ID 5
    ]
    weights = []
    total = 0
    for i, label in enumerate(labels):
        print(label)
        try:
            w = float(input(f"Hiệu ứng {i+1}: "))
            weights.append(w)
            total += w
        except ValueError:
            print("Giá trị không hợp lệ. Gán = 0.")
            weights.append(0)

    # Tự động tính phần còn lại cho hiệu ứng cuối cùng: Kéo Búa Bao (ID 6)
    remaining = max(0, 100 - total)
    weights.append(remaining)
    print(f"6. Kéo Búa Bao (tự động): {remaining:.2f}%")

    total_final = sum(weights)
    if total_final == 0:
        print("Tổng bằng 0, chuyển sang chia đều.")
        return get_even_distribution()

    probabilities = [w / total_final for w in weights]
    return EFFECT_IDS, probabilities

def choose_effect(distribution_type="even"):
    global _saved_distribution
    if _saved_distribution is None:
        if distribution_type == "custom":
            _saved_distribution = get_custom_distribution()
        else:
            _saved_distribution = get_even_distribution()

    ids, probs = _saved_distribution
    return random.choices(ids, weights=probs, k=1)[0]
