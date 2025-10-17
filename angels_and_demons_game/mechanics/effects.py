# đặt gần đầu file, sau import
import os
from pathlib import Path
import pygame

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

# === ĐƯỜNG DẪN TUYỆT ĐỐI TỚI THƯ MỤC SOUNDS ===
BASE_DIR = Path(__file__).resolve().parent.parent      # lùi lên 1 cấp (ra khỏi /mechanics)
SOUND_DIR = BASE_DIR / "assets" / "sounds"             # trỏ đúng vào thư mục chứa mp3
                        # AngelsAndDemons/sounds

def load_sound(filename, default=None, volume=0.6):
    path = SOUND_DIR / filename
    if not path.exists():
        # In chẩn đoán cho bạn nhìn thấy ngay lỗi ở console
        print(f"[ERROR] Không thấy file: {path}")
        try:
            print("[DEBUG] SOUND_DIR:", SOUND_DIR)
            print("[DEBUG] Có các file:", os.listdir(SOUND_DIR))
        except Exception as e:
            print("[DEBUG] Không đọc được SOUND_DIR:", e)
        return default
    try:
        s = pygame.mixer.Sound(str(path))  # dùng đường dẫn tuyệt đối
        s.set_volume(volume)
        return s
    except Exception as e:
        print(f"[ERROR] Lỗi nạp {path}: {e}")
        return default

# Map đúng TÊN FILE đang có trong thư mục sounds (đúng chữ hoa/thường + đuôi .mp3)
sounds = {
    1: load_sound("angels.mp3"),   # Thiên thần
    2: load_sound("devil.mp3"),    # Ác quỷ
    3: load_sound("gun.mp3"),      # Súng
    4: load_sound("lucky.mp3"),    # May mắn
    5: load_sound("lotery.mp3"),   # Trúng xổ số (bạn đang đặt 'lotery.mp3')
    6: load_sound("rps.mp3"),    # Kéo búa bao (tạm thời)
    7: load_sound("double.mp3"),   # Nhân đôi
    8: load_sound("half.mp3"),     # Chia đôi
}

def play_effect(effect_id, stop_others=True):
    snd = sounds.get(effect_id)
    if snd:
        if stop_others:
            pygame.mixer.stop()
        snd.play()
    else:
        print(f"[WARN] Chưa có sound cho effect_id={effect_id}")


import random
def apply_effect(effect_id, player, all_players=None):
    
    if effect_id == 1:  # Thiên thần
        play_effect(effect_id)
        player.add_score(15)
        return "Bạn gặp Thiên Thần! +15 điểm."
    elif effect_id == 2:  # Ác quỷ
        play_effect(effect_id)
        player.subtract_score(25)
        return "Bạn gặp Ác Quỷ! -25 điểm."
    elif effect_id == 3:  # Súng
        play_effect(effect_id)
        if all_players and len(all_players) > 1:
            others = [p for p in all_players if p != player]
            target = random.choice(others)
            target.subtract_score(20)
            player.add_score(20)
            return f"{player.name} đã dùng súng cướp 20 điểm từ {target.name}!"
        return "Không thể cướp điểm, không ai đủ điểm hoặc chỉ có 1 người."
    elif effect_id == 4:  # May mắn
        play_effect(effect_id)
        player.add_score(30)
        return "May mắn đến! +30 điểm."
    elif effect_id == 5:  # Trúng xổ số
        play_effect(effect_id)
        player.add_score(50)
        return "Trúng xổ số! +50 điểm."
    elif effect_id == 7:
        play_effect(effect_id)
        player.add_score(player.score)
        return f"{player.name} được nhân đôi số điểm hiện tại! 🎉"   
    elif effect_id == 8:  # Chia đôi điểm
        play_effect(effect_id)
        old_score = player.score
        lost = old_score // 2
        player.subtract_score(lost)  # trừ một nửa điểm
        return f"{player.name} bị chia đôi điểm, mất {lost} điểm! 😢"
