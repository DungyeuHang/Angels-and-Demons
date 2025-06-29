
# custom_setup.py - Cập nhật: thêm Tab/chọn ô/tương tác nút điều hướng
import pygame
from models.player import Player
import os
import sys


os.environ['SDL_VIDEO_CENTERED'] = '1'

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def run_custom_setup_ui():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Tùy chỉnh trò chơi")

    #font = pygame.font.SysFont("Times New Roman", 28)
    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    font = pygame.font.Font(font_path, 20)

    clock = pygame.time.Clock()

    input_boxes = []
    num_players = 2
    input_number = "10"
    input_number_boxes = "50"
    editing = 0
    phase = "number"
    dist_mode = "even"
    error = ""
    players = []

    running = True
    while running:
        screen.fill((255, 255, 255))

        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        next_rect = pygame.Rect(470, 45, 100, 40)
        back_rect = pygame.Rect(580, 45, 100, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
            elif event.type == pygame.KEYDOWN:
                if phase == "number":
                    if event.key == pygame.K_RETURN:
                        if input_number.isdigit() and int(input_number) > 0:
                            num_players = int(input_number)
                            input_boxes = [f"Người {i+1}" for i in range(num_players)]
                            phase = "names"
                            editing = 0
                            error = ""
                        else:
                            error = "Số không hợp lệ."
                    elif event.key == pygame.K_BACKSPACE:
                        input_number = input_number[:-1]
                    elif event.unicode.isdigit():
                        input_number += event.unicode

                elif phase == "boxes":
                    if event.key == pygame.K_RETURN:
                        if input_number_boxes.isdigit() and int(input_number_boxes) > 0:
                            return players, int(input_number_boxes), dist_mode
                        else:
                            error = "Số không hợp lệ."
                    elif event.key == pygame.K_BACKSPACE:
                        input_number_boxes = input_number_boxes[:-1]
                    elif event.unicode.isdigit():
                        input_number_boxes += event.unicode

                elif phase == "names":
                    if event.key == pygame.K_TAB:
                        editing = (editing + 1) % len(input_boxes)
                    elif event.key == pygame.K_RETURN:
                        if all(name.strip() for name in input_boxes):
                            players = [Player(name.strip()) for name in input_boxes]
                            phase = "boxes"
                            error = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_boxes[editing] = input_boxes[editing][:-1]
                    else:
                        input_boxes[editing] += event.unicode


        if phase == "number":
            screen.blit(font.render("Nhập số người chơi:", True, (0, 0, 0)), (50, 50))
            input_rect = pygame.Rect(300, 45, 140, 40)
            pygame.draw.rect(screen, (200, 200, 200), input_rect)
            pygame.draw.rect(screen, (0, 120, 215), input_rect, 3)
            screen.blit(font.render(input_number, True, (0, 0, 0)), (310, 50))

            # Nút tiếp theo và quay lại
            pygame.draw.rect(screen, (100, 200, 100), next_rect)
            pygame.draw.rect(screen, (0, 0, 0), next_rect, 2)
            screen.blit(font.render("Tiếp", True, (0, 0, 0)), (next_rect.x + 20, next_rect.y + 5))

            pygame.draw.rect(screen, (200, 100, 100), back_rect)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
            screen.blit(font.render("Thoát", True, (0, 0, 0)), (back_rect.x + 15, back_rect.y + 5))

            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    if input_number.isdigit() and int(input_number) > 0:
                        num_players = int(input_number)
                        input_boxes = [f"Người {i+1}" for i in range(num_players)]
                        phase = "names"
                        editing = 0
                        error = ""
                elif back_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    return None, None, None

        elif phase == "names":
            screen.blit(font.render("Nhập tên người chơi (Tab/chọn ô, Enter để tiếp):", True, (0, 0, 0)), (50, 30))
            total = len(input_boxes)
            box_width = 180 if total <= 15 else 140
            box_height = 40
            padding_x = 15
            padding_y = 15
            per_row = 5
            start_x = 50
            start_y = 80
            adjusted_font = pygame.font.Font(font_path, 20)

            for i, box in enumerate(input_boxes):
                x = start_x + (i % per_row) * (box_width + padding_x)
                y = start_y + (i // per_row) * (box_height + padding_y)
                rect = pygame.Rect(x, y, box_width, box_height)
                color = (200, 200, 200)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 120, 215) if i == editing else (0, 0, 0), rect, 2)
                screen.blit(adjusted_font.render(box if box else str(i+1), True, (0, 0, 0)), (x + 10, y + 5))

                if mouse_clicked and rect.collidepoint(mouse_pos):
                    editing = i

            next_rect = pygame.Rect(800, 620, 150, 50)
            back_rect = pygame.Rect(630, 620, 150, 50)
            if all(name.strip() for name in input_boxes):
                start_rect = pygame.Rect(800, 620, 150, 50)
                pygame.draw.rect(screen, (50, 180, 50), next_rect)
                pygame.draw.rect(screen, (0, 120, 215), next_rect, 3)
                screen.blit(font.render("Tiếp theo", True, (255, 255, 255)), (next_rect.x + 20, next_rect.y + 10))
                

                if mouse_clicked and next_rect.collidepoint(mouse_pos):
                    players = [Player(name.strip()) for name in input_boxes]
                    phase = "boxes"
                    error = ""
                elif mouse_clicked and back_rect.collidepoint(mouse_pos):
                    phase = "number"

        elif phase == "boxes":
            screen.blit(font.render("Nhập số ô may mắn:", True, (0, 0, 0)), (50, 50))
            input_rect = pygame.Rect(300, 45, 140, 40)
            pygame.draw.rect(screen, (200, 200, 200), input_rect)
            pygame.draw.rect(screen, (0, 120, 215), input_rect, 3)
            screen.blit(font.render(input_number_boxes, True, (0, 0, 0)), (310, 50))

            # Nút tiếp theo và quay lại
            pygame.draw.rect(screen, (100, 200, 100), next_rect)
            pygame.draw.rect(screen, (0, 0, 0), next_rect, 2)
            screen.blit(font.render("Tiếp", True, (0, 0, 0)), (next_rect.x + 20, next_rect.y + 5))

            pygame.draw.rect(screen, (200, 100, 100), back_rect)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
            screen.blit(font.render("Trở lại", True, (0, 0, 0)), (back_rect.x + 10, back_rect.y + 5))

            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    if input_number_boxes.isdigit():
                        return players, int(input_number_boxes), dist_mode
                elif back_rect.collidepoint(mouse_pos):
                    phase = "names"

        if error:
            screen.blit(font.render(error, True, (255, 0, 0)), (50, 650))

        pygame.display.flip()
        clock.tick(30)
