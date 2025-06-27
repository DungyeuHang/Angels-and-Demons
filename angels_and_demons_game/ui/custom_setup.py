# custom_setup.py - auto-generated
import pygame
from models.player import Player
from mechanics.randomizer import set_custom_weights

def run_custom_setup_ui():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Tùy chỉnh trò chơi")
    font = pygame.font.SysFont("Times New Roman", 28)
    clock = pygame.time.Clock()

    input_boxes = []
    num_players = 2
    input_number = ""
    input_active = True
    editing = 0
    phase = "number"  # "number" -> "names" -> "boxes"
    num_boxes = 30
    dist_mode = "even"
    error = ""
    players = []

    running = True
    while running:
        screen.fill((255, 255, 255))

        if phase == "number":
            text = font.render("Nhập số người chơi:", True, (0, 0, 0))
            screen.blit(text, (50, 50))
            input_box_rect = pygame.Rect(300, 45, 140, 40)
            pygame.draw.rect(screen, (200, 200, 200), input_box_rect)
            pygame.draw.rect(screen, (0, 120, 215), input_box_rect, 3)
            screen.blit(font.render(input_number, True, (0, 0, 0)), (310, 50))

        elif phase == "names":
            title = font.render("Nhập tên người chơi (nhấn Enter hoặc ↓ để chuyển, Esc để quay lại):", True, (0, 0, 0))
            screen.blit(title, (50, 30))
            for i, box in enumerate(input_boxes):
                is_selected = (i == editing)
                color = (200, 200, 200)
                x, y = 50 + (i % 5) * 190, 80 + (i // 5) * 60
                rect = pygame.Rect(x, y, 180, 40)
                pygame.draw.rect(screen, color, rect)
                if is_selected:
                    pygame.draw.rect(screen, (0, 120, 215), rect, 3)
                name_text = font.render(box if box else str(i+1), True, (0, 0, 0))
                screen.blit(name_text, (x + 10, y + 5))

            if all(name.strip() != "" for name in input_boxes):
                start_rect = pygame.Rect(800, 620, 150, 50)
                pygame.draw.rect(screen, (50, 180, 50), start_rect)
                pygame.draw.rect(screen, (0, 120, 215), start_rect, 3)
                screen.blit(font.render("Bắt đầu", True, (255, 255, 255)), (start_rect.x + 20, start_rect.y + 10))

        elif phase == "boxes":
            text = font.render("Nhập số ô may mắn:", True, (0, 0, 0))
            screen.blit(text, (50, 50))
            input_box_rect = pygame.Rect(300, 45, 140, 40)
            pygame.draw.rect(screen, (200, 200, 200), input_box_rect)
            pygame.draw.rect(screen, (0, 120, 215), input_box_rect, 3)
            screen.blit(font.render(input_number, True, (0, 0, 0)), (310, 50))

        if error:
            error_text = font.render(error, True, (255, 0, 0))
            screen.blit(error_text, (50, 650))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if phase == "names":
                        phase = "number"
                        input_number = str(num_players)
                    elif phase == "boxes":
                        phase = "names"
                        input_number = ""
                    else:
                        return None, None, None

                if phase in ["number", "boxes"]:
                    if event.key == pygame.K_RETURN:
                        if input_number.isdigit() and int(input_number) > 0:
                            if phase == "number":
                                num_players = int(input_number)
                                input_boxes = ["" for _ in range(num_players)]
                                phase = "names"
                                editing = 0
                                input_number = ""
                                error = ""
                            elif phase == "boxes":
                                num_boxes = int(input_number)
                                return players, num_boxes, dist_mode
                        else:
                            error = "Số không hợp lệ."
                    elif event.key == pygame.K_BACKSPACE:
                        input_number = input_number[:-1]
                    else:
                        input_number += event.unicode

                elif phase == "names":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_DOWN:
                        editing = (editing + 1) % len(input_boxes)
                    elif event.key == pygame.K_BACKSPACE:
                        input_boxes[editing] = input_boxes[editing][:-1]
                    elif event.key == pygame.K_TAB:
                        editing = (editing + 1) % len(input_boxes)
                    else:
                        input_boxes[editing] += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if phase == "names":
                    for i in range(len(input_boxes)):
                        x, y = 50 + (i % 5) * 190, 80 + (i // 5) * 60
                        if pygame.Rect(x, y, 180, 40).collidepoint(event.pos):
                            editing = i
                            break

                    if all(name.strip() != "" for name in input_boxes):
                        start_rect = pygame.Rect(800, 620, 150, 50)
                        if start_rect.collidepoint(event.pos):
                            players = [Player(name.strip()) for name in input_boxes]
                            phase = "boxes"
                            input_number = ""
                            error = ""

        pygame.display.flip()
        clock.tick(30)
