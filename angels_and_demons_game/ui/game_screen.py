
import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 900, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Angels and Demons")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
BLUE = (100, 149, 237)

try:
    FONT = pygame.font.SysFont("Times New Roman", 28)
    SMALL_FONT = pygame.font.SysFont("Times New Roman", 22)
except:
    FONT = pygame.font.Font(None, 28)
    SMALL_FONT = pygame.font.Font(None, 22)

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0

class Button:
    def __init__(self, rect, text, color=GRAY, text_color=BLACK):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.active = True

    def draw(self, screen):
        color = self.color if self.active else (220, 220, 220)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        txt_surf = SMALL_FONT.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos) and self.active

def apply_effect(effect_id, player, all_players):
    if effect_id == 1:
        player.score += 15
        return "🌤️ Gặp Thiên Thần! +15 điểm"
    elif effect_id == 2:
        player.score -= 25
        return "😈 Gặp Ác Quỷ! -25 điểm"
    elif effect_id == 3:
        player.score += 30
        return "🍀 May mắn đến! +30 điểm"
    elif effect_id == 4:
        player.score += 50
        return "💰 Trúng xổ số! +50 điểm"
    elif effect_id == 5:
        targets = [p for p in all_players if p != player]
        if targets:
            target = random.choice(targets)
            target.score -= 20
            player.score += 20
            return f"🔫 Cướp 20 điểm từ {target.name}"
        return "🔫 Không có ai để cướp điểm"
    elif effect_id == 6:
        outcome = random.choice(["win", "lose"])
        if outcome == "win":
            player.score += 10
            return "✊ Kéo Búa Bao: Bạn thắng! +10 điểm"
        else:
            return "✊ Kéo Búa Bao: Bạn thua!"
    return "❓ Hiệu ứng không xác định"

def show_choice_popup(remaining_numbers):
    running = True
    clock = pygame.time.Clock()
    buttons = []
    SCREEN.fill(WHITE)
    title = FONT.render("Chọn số ô muốn mở", True, BLACK)
    SCREEN.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    for i, num in enumerate(remaining_numbers):
        row = i // 5
        col = i % 5
        x = 100 + col * 120
        y = 150 + row * 100
        btn = Button((x, y, 100, 60), str(num))
        buttons.append((num, btn))

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return  # Quay lại màn hình trước

                    pos = event.pos
                    for num, btn in buttons:
                        if btn.is_clicked(pos):
                            return num

        for _, btn in buttons:
            btn.draw(SCREEN)

        
        # Nút quay lại
        back_button = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)
        pygame.draw.rect(SCREEN, (200, 50, 50), back_button)
        pygame.draw.rect(SCREEN, BLACK, back_button, 2)
        SCREEN.blit(SMALL_FONT.render("↩ Quay lại", True, WHITE), (WIDTH - 120, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(30)

def run_game_ui():
    input_active = True
    input_number = ""
    input_boxes = []
    players = []
    clock = pygame.time.Clock()
    phase = "number"
    info_text = "Nhập số người chơi (tối thiểu 2):"
    editing = 0

    while input_active:
        SCREEN.fill(WHITE)
        text = FONT.render(info_text, True, BLACK)
        SCREEN.blit(text, (50, 50))

        if phase == "number":
            box_rect = pygame.Rect(50, 120, 200, 40)
            pygame.draw.rect(SCREEN, GRAY, box_rect)
            num_surf = FONT.render(input_number, True, BLACK)
            SCREEN.blit(num_surf, (box_rect.x + 10, box_rect.y + 5))
        else:
            for i, val in enumerate(input_boxes):
                r = pygame.Rect(50, 120 + i*50, 300, 40)
                pygame.draw.rect(SCREEN, GRAY, r)
                if i == editing:
                    pygame.draw.rect(SCREEN, (0, 255, 0), r, 3)
                name = FONT.render(val, True, BLACK)
                SCREEN.blit(name, (r.x + 10, r.y + 5))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if phase == "number":
                        try:
                            n = int(input_number)
                            if n >= 2:
                                input_boxes = ["" for _ in range(n)]
                                phase = "names"
                                input_number = ""
                                info_text = "Nhập tên người chơi (click vào ô để gõ, Enter để bắt đầu):"
                        except:
                            input_number = ""
                    else:
                        if all(name.strip() != "" for name in input_boxes):
                            players = [Player(name.strip()) for name in input_boxes]
                            input_active = False
                elif event.key == pygame.K_TAB or event.key == pygame.K_DOWN:
                        editing = (editing + 1) % len(input_boxes)
                elif event.key == pygame.K_BACKSPACE:
                    if phase == "number":
                        input_number = input_number[:-1]
                    elif phase == "names":
                        input_boxes[editing] = input_boxes[editing][:-1]
                else:
                    if phase == "number":
                        input_number += event.unicode
                    elif phase == "names":
                        input_boxes[editing] += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN and phase == "names":
                for i in range(len(input_boxes)):
                    r = pygame.Rect(50, 120 + i*50, 300, 40)
                    if r.collidepoint(event.pos):
                        editing = i

        
        # Nút quay lại
        back_button = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)
        pygame.draw.rect(SCREEN, (200, 50, 50), back_button)
        pygame.draw.rect(SCREEN, BLACK, back_button, 2)
        SCREEN.blit(SMALL_FONT.render("↩ Quay lại", True, WHITE), (WIDTH - 120, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(30)

    # --- Màn chơi chính ---
    current_player_idx = 0
    total_boxes = 10
    box_numbers = list(range(1, total_boxes + 1))
    random.shuffle(box_numbers)
    opened = []
    result_message = ""
    game_over = False

    while True:
        SCREEN.fill(WHITE)
        current_player = players[current_player_idx]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        for i, p in enumerate(players):
            col = BLUE if i == current_player_idx and not game_over else BLACK
            txt = FONT.render(f"{p.name}: {p.score} điểm", True, col)
            SCREEN.blit(txt, (50, 30 + i * 40))

        remaining = [n for n in box_numbers if n not in opened]
        for i, n in enumerate(box_numbers):
            row = i // 5
            col = i % 5
            x = 100 + col * 120
            y = 250 + row * 100
            rect = pygame.Rect(x, y, 100, 60)
            color = GRAY if n not in opened else (230, 230, 230)
            pygame.draw.rect(SCREEN, color, rect)
            pygame.draw.rect(SCREEN, BLACK, rect, 2)
            label = FONT.render(str(n), True, BLACK)
            SCREEN.blit(label, (x + 35, y + 15))

        if not game_over and remaining:
            msg = FONT.render("Chọn: [R]andom | [T]ự chọn", True, RED)
            SCREEN.blit(msg, (50, HEIGHT - 100))
            
        # Nút quay lại
        back_button = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)
        pygame.draw.rect(SCREEN, (200, 50, 50), back_button)
        pygame.draw.rect(SCREEN, BLACK, back_button, 2)
        SCREEN.blit(SMALL_FONT.render("↩ Quay lại", True, WHITE), (WIDTH - 120, HEIGHT - 50))

        pygame.display.flip()
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_r:
                        chosen = random.choice(remaining)
                        waiting = False
                    elif e.key == pygame.K_t:
                        chosen = show_choice_popup(remaining)
                        waiting = False
                elif e.type == pygame.QUIT:

                    
                    pygame.quit()
                    sys.exit()
            if 'chosen' in locals():
                opened.append(chosen)
            effect_id = random.randint(1, 6)
            result_message = apply_effect(effect_id, current_player, players)
            current_player_idx = (current_player_idx + 1) % len(players)

        msg = SMALL_FONT.render(result_message, True, RED)
        SCREEN.blit(msg, (50, HEIGHT - 60))

        if len(opened) == len(box_numbers) and not game_over:
            game_over = True
            players.sort(key=lambda x: -x.score)
            result_message = "🏆 KẾT THÚC GAME:\n" + "\n".join([f"{i+1}. {p.name} - {p.score} điểm" for i, p in enumerate(players)])

        
        # Nút quay lại
        back_button = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)
        pygame.draw.rect(SCREEN, (200, 50, 50), back_button)
        pygame.draw.rect(SCREEN, BLACK, back_button, 2)
        SCREEN.blit(SMALL_FONT.render("↩ Quay lại", True, WHITE), (WIDTH - 120, HEIGHT - 50))

        pygame.display.flip()
        clock.tick(30)
