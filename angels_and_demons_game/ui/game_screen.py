# game_screen.py - Phiên bản đẹp nền
import pygame
import os
import json
from datetime import datetime
from mechanics.effects import apply_effect
from mechanics.randomizer import get_random_effect
import sys



os.environ['SDL_VIDEO_CENTERED'] = '1'

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def save_game_history(players):
    filepath = os.path.join(BASE_DIR, "data", "histories.json")

    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": [{"name": p.name, "score": p.score} for p in players]
    }
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    history.append(data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def run_game_ui(players, num_boxes, dist_mode):
    pygame.init()
    window_size = (1500, 800)
    screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
    pygame.display.set_caption("Angels and Demons - Game")

    #font = pygame.font.SysFont("Comic Sans MS", 28)
    #font = pygame.font.SysFont("Times New Roman", 28)
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    font = pygame.font.Font(font_path, 20)

    clock = pygame.time.Clock()

    canvas_size = (1500, 800)
    canvas = pygame.Surface(canvas_size)

    boxes = list(range(1, num_boxes + 1))
    opened = []
    current_player = 0
    result_message = ""
    waiting_effect_input = False
    effect_to_resolve = None
    running = True

    while running:
        canvas.fill((245, 245, 235))  # nền sáng dịu

        players_per_row = 5
        start_x = 30
        start_y = 30
        spacing_x = 250
        spacing_y = 40

        top_score = max(p.score for p in players)

        for i, player in enumerate(players):
            row = i // players_per_row
            col = i % players_per_row
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            if i == current_player:
                color = (50, 100, 255)
            elif player.score == top_score and top_score > 0:
                color = (220, 170, 0)
            else:
                color = (0, 0, 0)
            score_text = font.render(f"{player.name}: {player.score} điểm", True, color)
            canvas.blit(score_text, (x, y))

        cols = 10
        for i, num in enumerate(boxes):
            x = 100 + (i % cols) * 70
            y = 100 + (i // cols) * 70 + 120
            rect = pygame.Rect(x, y, 60, 60)
            if num in opened:
                pygame.draw.rect(canvas, (230, 230, 230), rect)
                canvas.blit(font.render(str(num), True, (120, 120, 120)), (x + 15, y + 10))
            else:
                pygame.draw.rect(canvas, (180, 180, 255), rect)
                canvas.blit(font.render(str(num), True, (0, 0, 0)), (x + 15, y + 10))
            pygame.draw.rect(canvas, (0, 0, 0), rect, 2)

        quit_rect = pygame.Rect(canvas_size[0] - 160, canvas_size[1] - 50, 140, 40)
        pygame.draw.rect(canvas, (200, 80, 80), quit_rect)
        pygame.draw.rect(canvas, (0, 0, 0), quit_rect, 2)
        canvas.blit(font.render(" Kết thúc", True, (255, 255, 255)), (quit_rect.x + 10, quit_rect.y + 5))

        if result_message:
            text = font.render(result_message, True, (50, 100, 200))
            canvas.blit(text, (canvas_size[0] // 2 - text.get_width() // 2, canvas_size[1] - 80))

        scaled_canvas = pygame.transform.smoothscale(canvas, screen.get_size())
        screen.blit(scaled_canvas, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                scale_x = canvas_size[0] / screen.get_width()
                scale_y = canvas_size[1] / screen.get_height()
                mx, my = event.pos
                pos = (int(mx * scale_x), int(my * scale_y))

                if quit_rect.collidepoint(pos):
                    save_game_history(players)
                    show_final_result(screen, font, players)
                    return

                if not waiting_effect_input:
                    for i, num in enumerate(boxes):
                        x = 100 + (i % cols) * 70
                        y = 100 + (i // cols) * 70 + 120
                        rect = pygame.Rect(x, y, 60, 60)
                        if rect.collidepoint(pos) and num not in opened:
                            opened.append(num)
                            effect_id = get_random_effect(dist_mode)
                            if effect_id == 6:
                                result_message = f"{players[current_player].name} mở ô {num} - Kéo Búa Bao! (Nhấn 1: thắng, 2: thua)"
                                effect_to_resolve = {'player': players[current_player]}
                                waiting_effect_input = True
                            else:
                                result_message = f"{players[current_player].name} mở ô {num} - {apply_effect(effect_id, players[current_player], players)}"
                                current_player = (current_player + 1) % len(players)
                            break

            elif event.type == pygame.KEYDOWN and waiting_effect_input:
                if event.key == pygame.K_1:
                    effect_to_resolve['player'].add_score(10)
                    result_message = f"{effect_to_resolve['player'].name} thắng Kéo Búa Bao! +10 điểm 🎉"
                    current_player = (current_player + 1) % len(players)
                    waiting_effect_input = False
                    effect_to_resolve = None
                elif event.key == pygame.K_2:
                    result_message = f"{effect_to_resolve['player'].name} thua Kéo Búa Bao..."
                    current_player = (current_player + 1) % len(players)
                    waiting_effect_input = False
                    effect_to_resolve = None

        pygame.display.flip()
        clock.tick(30)

def show_final_result(screen, font, players):
    screen.fill((255, 255, 255))
    players.sort(key=lambda p: p.score, reverse=True)
    title = font.render("🏆 KẾT QUẢ CUỐI CÙNG", True, (0, 0, 0))
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 50))
    for i, p in enumerate(players):
        text = font.render(f"{i+1}. {p.name} - {p.score} điểm", True, (0, 0, 0))
        screen.blit(text, (100, 120 + i * 40))

    ok_rect = pygame.Rect(screen.get_width()//2 - 80, 130 + len(players)*40, 160, 50)
    pygame.draw.rect(screen, (80, 180, 80), ok_rect)
    pygame.draw.rect(screen, (0, 0, 0), ok_rect, 2)
    screen.blit(font.render("OK - Thoát", True, (255, 255, 255)), (ok_rect.x + 10, ok_rect.y + 10))

    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ok_rect.collidepoint(event.pos):
                    waiting = False