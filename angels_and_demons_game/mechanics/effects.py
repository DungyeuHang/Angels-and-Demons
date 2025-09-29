# effects.py - Không còn xử lý Kéo Búa Bao trong đây
import random
def apply_effect(effect_id, player, all_players=None):
    if effect_id == 1:  # Thiên thần
        player.add_score(15)
        return "Bạn gặp Thiên Thần! +15 điểm."
    elif effect_id == 2:  # Ác quỷ
        player.subtract_score(25)
        return "Bạn gặp Ác Quỷ! -25 điểm."
    elif effect_id == 3:  # Súng
        if all_players and len(all_players) > 1:
            others = [p for p in all_players if p != player]
            target = random.choice(others)
            target.subtract_score(20)
            player.add_score(20)
            return f"{player.name} đã dùng súng cướp 20 điểm từ {target.name}!"
        return "Không thể cướp điểm, không ai đủ điểm hoặc chỉ có 1 người."
    elif effect_id == 4:  # May mắn
        player.add_score(30)
        return "May mắn đến! +30 điểm."
    elif effect_id == 5:  # Trúng xổ số
        player.add_score(50)
        return "Trúng xổ số! +50 điểm."


