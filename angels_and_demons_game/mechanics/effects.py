# effects.py - auto-generated
import random

def apply_effect(effect_id, player, all_players=None):
    if effect_id == 1:  # Thiên thần
        player.add_score(15)
        return "Bạn gặp Thiên Thần! +15 điểm."

    elif effect_id == 2:  # Ác quỷ
        player.subtract_score(25)
        return "Bạn gặp Ác Quỷ! -25 điểm."

    elif effect_id == 3:  # May mắn
        player.add_score(30)
        return "May mắn đến! +30 điểm."

    elif effect_id == 4:  # Trúng xổ số
        player.add_score(50)
        return "Trúng xổ số! +50 điểm."

    elif effect_id == 5:  # Súng - cướp điểm từ người khác
        if all_players and len(all_players) > 1:
            other_players = [p for p in all_players if p != player]
            target = other_players[0] if len(other_players) == 1 else random.choice(other_players)

            target.subtract_score(20)
            player.add_score(20)

            return f"{player.name} đã dùng súng cướp 20 điểm từ {target.name}!"
        else:
            return "Không thể dùng súng vì chỉ có một người chơi."

    elif effect_id == 6:  # Kéo Búa Bao - nhập người thắng
        if all_players and len(all_players) > 1:
            other_players = [p for p in all_players if p != player]

            print("\n✨ HIỆU ỨNG: Kéo Búa Bao ✊✋✌️")
            print("1. Người chơi THẮNG oẳn tù tì (+10 điểm)")
            print("2. Người chơi THUA oẳn tù tì (0 điểm)")

            try:
                result = int(input("Chọn kết quả (1 hoặc 2): "))
                if result == 1:
                    player.add_score(10)
                    return f"{player.name} thắng oẳn tù tì! +10 điểm."
                else:
                    return f"{player.name} thua oẳn tù tì. Không có điểm."
            except ValueError:
                return "Lựa chọn không hợp lệ. Bỏ qua hiệu ứng."

        else:
            return "Không đủ người để oẳn tù tì."

    else:
        return "Hiệu ứng không xác định."
