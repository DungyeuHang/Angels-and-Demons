
from models.player import Player
from mechanics.effects import apply_effect
import random

# Tạo người chơi
num_players = int(input("Nhập số người chơi: "))
players = []

for i in range(num_players):
    name = input(f"Nhập tên người chơi {i+1}: ")
    players.append(Player(name))

# Số ô may mắn
n = int(input("Số lượng ô may mắn (ví dụ 12): "))
available_numbers = list(range(1, n + 1))

print("\n--- BẮT ĐẦU TRÒ CHƠI ---\n")

turn = 0
while True:
    if not available_numbers:
        print("🎉 Tất cả các ô may mắn đã được mở! Trò chơi kết thúc.")
        break

    current_player = players[turn % num_players]
    print(f"\n>> Đến lượt: {current_player.name} (Điểm: {current_player.score})")
    print(f"Các ô còn lại: {available_numbers}")

    choice = input("Chọn 1: chọn số ngẫu nhiên | 2: tự chọn số | q: thoát\n> ")

    if choice == "q":
        break
    elif choice == "1":
        number = random.choice(available_numbers)
    elif choice == "2":
        try:
            number = int(input(f"Chọn số từ danh sách trên: "))
            if number not in available_numbers:
                print("Số này đã được chọn rồi hoặc không hợp lệ.")
                continue
        except ValueError:
            print("Lỗi: nhập số không hợp lệ.")
            continue
    else:
        print("Lựa chọn không hợp lệ.")
        continue

    # Loại bỏ số đã chọn
    available_numbers.remove(number)

    # Random hiệu ứng
    effect_id = random.randint(1, 6)
    message = apply_effect(effect_id, current_player, players)
    print(f"Bạn chọn số {number} → {message}")

    # Hiển thị điểm
    print(">>> Bảng điểm:")
    for p in players:
        print(f"{p.name}: {p.score} điểm")

    turn += 1

print("\n--- KẾT THÚC GAME ---")
