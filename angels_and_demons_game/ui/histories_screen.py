import os
import json
import pygame

os.environ['SDL_VIDEO_CENTERED'] = '1'
os.chdir(os.path.dirname(__file__))  # đảm bảo chạy từ đúng thư mục chứa main

def show_history_screen(screen, font):
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", "histories.json")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    scroll_y = 0
    scroll_speed = 30
    running = True

    while running:
        screen.fill((255, 255, 255))
        title = font.render("LỊCH SỬ CÁC VÁN CHƠI", True, (0, 0, 0))
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 30))

        y = 80 - scroll_y
        for i, game in enumerate(reversed(history)):
            time_text = font.render(f"{i+1}. {game['timestamp']}", True, (0, 0, 180))
            screen.blit(time_text, (50, y))
            y += 30
            for player in game["players"]:
                player_text = font.render(f"    {player['name']}: {player['score']} điểm", True, (0, 0, 0))
                screen.blit(player_text, (80, y))
                y += 25
            y += 15

        back_rect = pygame.Rect(screen.get_width()//2 - 80, screen.get_height() - 60, 160, 45)
        pygame.draw.rect(screen, (80, 180, 80), back_rect)
        pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
        screen.blit(font.render("Quay lại", True, (255, 255, 255)), (back_rect.x + 20, back_rect.y + 8))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    running = False
                elif event.button == 4:  # cuộn lên
                    scroll_y = max(0, scroll_y - scroll_speed)
                elif event.button == 5:  # cuộn xuống
                    scroll_y += scroll_speed