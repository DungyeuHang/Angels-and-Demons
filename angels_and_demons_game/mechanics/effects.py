# effects.py - Không còn xử lý Kéo Búa Bao trong đây
import pygame
pygame.mixer.pre_init(44100, -16, 2, 512)  # xử lý âm thanh mượt hơn
pygame.init()
pygame.mixer.init()

import os

SOUND_DIR = "sounds"

def load_sound(name, default=None, volume=0.6):
    try:
        s = pygame.mixer.Sound(os.path.join(SOUND_DIR, name))
        s.set_volume(volume)
        return s
    except Exception as e:
        print(f"[WARN] Không nạp được {name}: {e}")
        return default

sounds = {
    1: load_sound("angels.mp3"),
    2: load_sound("devil.mp3"),
    3: load_sound("gun.mp3"),
    4: load_sound("lucky.mp3"),
    5: load_sound("lotery.mp3"),
    6: load_sound("rps.mp3"),  # cho kéo-búa-bao
    7: load_sound("double.mp3"),
    8: load_sound("half.mp3"),
}

def play_effect(effect_id, stop_others=True):
    snd = sounds.get(effect_id)
    if snd:
        if stop_others:
            pygame.mixer.stop()
        snd.play()

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
