# histories_screen.py - auto-generated
import pygame
import json
import os

def show_histories_screen():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("📜 Lịch sử chơi")

    font = pygame.font.SysFont("Times New Roman", 28)
    clock = pygame.time.Clock()

    history_path = os.path.join("data", "histories.json")
    histories = []

    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            histories = json.load(f)

    back_button = pygame.Rect(650, 520, 120, 40)

    running = True
    while running:
        screen.fill((240, 240, 240))
        title = font.render("📜 LỊCH SỬ CÁC TRẬN ĐẤU", True, (0, 0, 0))
        screen.blit(title, (200, 40))

        for i, record in enumerate(histories[-10:][::-1]):  # Hiện 10 gần nhất
            text = font.render(record, True, (50, 50, 50))
            screen.blit(text, (60, 100 + i * 35))

        pygame.draw.rect(screen, (200, 50, 50), back_button)
        pygame.draw.rect(screen, (0, 0, 0), back_button, 2)
        label = font.render("↩ Quay lại", True, (255, 255, 255))
        screen.blit(label, (back_button.x + 5, back_button.y + 5))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and back_button.collidepoint(event.pos):
                running = False

    pygame.quit()
