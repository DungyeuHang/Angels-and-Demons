# menu.py - Auto-generated menu interface
import pygame
from ui.custom_setup import run_custom_setup_ui
from ui.histories_screen import show_history_screen
from ui.game_screen import run_game_ui
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'
os.chdir(os.path.dirname(__file__))  # đảm bảo chạy từ đúng thư mục chứa main

def run_menu_ui():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Angels and Demons - Menu")
    #font = pygame.font.SysFont("Times New Roman", 32)
    #font = pygame.font.SysFont("Segoe UI Emoji", 32)

    FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    font = pygame.font.Font(FONT_PATH, 20)



    clock = pygame.time.Clock()

    options = ["Chơi (Tùy chỉnh)", "Xem lịch sử", "Thoát"]
    selected = 0

    running = True
    while running:
        #screen.fill((255, 255, 255))
        screen.fill((245, 245, 235))
        title = font.render("Angels and Demons 🎲", True, (0, 0, 0))
        screen.blit(title, (screen.get_width()//2 - title.get_width()//2, 50))

        for i, option in enumerate(options):
            color = (50, 100, 255) if i == selected else (100, 100, 100)
            text = font.render(option, True, color)
            rect = text.get_rect(center=(screen.get_width()//2, 180 + i * 60))
            screen.blit(text, rect)
            if i == selected:
                pygame.draw.rect(screen, (50, 100, 255), rect.inflate(20, 10), 2)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected == 0:
                        players, num_boxes, dist_mode = run_custom_setup_ui()
                        if players:
                            run_game_ui(players, num_boxes, dist_mode)
                    elif selected == 1:
                        show_history_screen(screen, font)

                    elif selected == 2:
                        running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, option in enumerate(options):
                    text = font.render(option, True, (0, 0, 0))
                    rect = text.get_rect(center=(screen.get_width()//2, 180 + i * 60))
                    if rect.collidepoint(event.pos):
                        if i == 0:
                            players, num_boxes, dist_mode = run_custom_setup_ui()
                            if players:
                                run_game_ui(players, num_boxes, dist_mode)
                        elif i == 1:
                            show_history_screen(screen, font)

                        elif i == 2:
                            running = False

        clock.tick(30)
