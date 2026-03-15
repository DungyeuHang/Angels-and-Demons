import os
import sys

import pygame

from models.player import Player
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_panel


os.environ["SDL_VIDEO_CENTERED"] = "1"

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def placeholder_name(index):
    return f"Người {index + 1}"


def refresh_text_input():
    pygame.key.stop_text_input()
    pygame.key.start_text_input()


def focus_name_field(input_boxes, index):
    if 0 <= index < len(input_boxes) and input_boxes[index] == placeholder_name(index):
        input_boxes[index] = ""
    return index


def draw_input_box(screen, font, rect, value, active=False, caret_visible=False):
    fill_color = (247, 242, 232) if active else (234, 226, 210)
    border_color = PALETTE["gold_dark"] if active else PALETTE["panel_dark"]

    pygame.draw.rect(screen, fill_color, rect, border_radius=8)
    pygame.draw.rect(screen, border_color, rect, 3 if active else 2, border_radius=8)

    text = font.render(value, True, (0, 0, 0))
    text_x = rect.x + 10
    text_y = rect.centery - text.get_height() // 2
    screen.blit(text, (text_x, text_y))

    if active and caret_visible:
        caret_x = text_x + text.get_width() + 2
        caret_top = rect.centery - text.get_height() // 2
        caret_bottom = rect.centery + text.get_height() // 2
        pygame.draw.line(screen, border_color, (caret_x, caret_top), (caret_x, caret_bottom), 2)


def handle_backspace(input_number, input_boxes, input_number_boxes, phase, editing):
    if phase == "number":
        return input_number[:-1], input_boxes, input_number_boxes
    if phase == "names" and input_boxes:
        input_boxes[editing] = input_boxes[editing][:-1]
        return input_number, input_boxes, input_number_boxes
    if phase == "boxes":
        return input_number, input_boxes, input_number_boxes[:-1]
    return input_number, input_boxes, input_number_boxes


def run_custom_setup_ui():
    pygame.init()
    pygame.key.start_text_input()
    screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Chuẩn bị ván chơi")

    font_path = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
    font = pygame.font.Font(font_path, 20)
    clock = pygame.time.Clock()

    input_boxes = []
    num_players = 2
    input_number = "2"
    input_number_boxes = "50"
    editing = 0
    phase = "number"
    error = ""
    players = []
    last_tab_time = 0
    backspace_held = False
    backspace_repeat_delay = 350
    backspace_repeat_interval = 40
    next_backspace_time = 0

    while True:
        draw_background(screen, pygame.time.get_ticks())
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        current_time = pygame.time.get_ticks()
        caret_visible = (current_time // 500) % 2 == 0
        next_rect = pygame.Rect(470, 45, 120, 40)
        back_rect = pygame.Rect(610, 45, 120, 40)
        draw_panel(screen, pygame.Rect(34, 24, screen.get_width() - 68, screen.get_height() - 48), fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=28)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None, None, None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            elif event.type == pygame.KEYDOWN:
                if phase == "number":
                    if event.key == pygame.K_RETURN:
                        if input_number.isdigit() and int(input_number) > 0:
                            num_players = int(input_number)
                            input_boxes = [placeholder_name(i) for i in range(num_players)]
                            phase = "names"
                            editing = focus_name_field(input_boxes, 0)
                            refresh_text_input()
                            error = ""
                        else:
                            error = "Số không hợp lệ."
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        input_number, input_boxes, input_number_boxes = handle_backspace(
                            input_number, input_boxes, input_number_boxes, phase, editing
                        )
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "names":
                    if event.key == pygame.K_TAB:
                        now = pygame.time.get_ticks()
                        if now - last_tab_time >= 180:
                            editing = focus_name_field(input_boxes, (editing + 1) % len(input_boxes))
                            refresh_text_input()
                            last_tab_time = now
                    elif event.key == pygame.K_RETURN:
                        if all(name.strip() for name in input_boxes):
                            players = [Player(name.strip()) for name in input_boxes]
                            phase = "boxes"
                            refresh_text_input()
                            error = ""
                        else:
                            error = "Hãy nhập tên cho tất cả người chơi."
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        input_number, input_boxes, input_number_boxes = handle_backspace(
                            input_number, input_boxes, input_number_boxes, phase, editing
                        )
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
                elif phase == "boxes":
                    if event.key == pygame.K_RETURN:
                        if input_number_boxes.isdigit() and int(input_number_boxes) > 0:
                            return players, int(input_number_boxes), "even", None
                        error = "Số không hợp lệ."
                    elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        input_number, input_boxes, input_number_boxes = handle_backspace(
                            input_number, input_boxes, input_number_boxes, phase, editing
                        )
                        backspace_held = True
                        next_backspace_time = current_time + backspace_repeat_delay
            elif event.type == pygame.TEXTINPUT:
                if phase == "number":
                    if event.text.isdigit():
                        input_number += event.text
                elif phase == "names":
                    input_boxes[editing] += event.text
                elif phase == "boxes":
                    if event.text.isdigit():
                        input_number_boxes += event.text
            elif event.type == pygame.KEYUP and event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                backspace_held = False

        if backspace_held and current_time >= next_backspace_time:
            input_number, input_boxes, input_number_boxes = handle_backspace(
                input_number, input_boxes, input_number_boxes, phase, editing
            )
            next_backspace_time = current_time + backspace_repeat_interval

        if phase == "number":
            screen.blit(font.render("Nhập số người chơi:", True, (0, 0, 0)), (50, 50))
            input_rect = pygame.Rect(300, 45, 140, 40)
            draw_input_box(screen, font, input_rect, input_number, True, caret_visible)

            pygame.draw.rect(screen, (100, 200, 100), next_rect)
            pygame.draw.rect(screen, (0, 0, 0), next_rect, 2)
            screen.blit(font.render("Tiếp", True, (0, 0, 0)), (next_rect.x + 25, next_rect.y + 5))

            pygame.draw.rect(screen, (200, 100, 100), back_rect)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
            screen.blit(font.render("Thoát", True, (0, 0, 0)), (back_rect.x + 20, back_rect.y + 5))

            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    if input_number.isdigit() and int(input_number) > 0:
                        num_players = int(input_number)
                        input_boxes = [placeholder_name(i) for i in range(num_players)]
                        phase = "names"
                        editing = focus_name_field(input_boxes, 0)
                        refresh_text_input()
                        error = ""
                    else:
                        error = "Số không hợp lệ."
                elif back_rect.collidepoint(mouse_pos):
                    return None, None, None, None

        elif phase == "names":
            screen.blit(font.render("Nhập tên người chơi (Tab để đổi ô):", True, (0, 0, 0)), (50, 30))
            total = len(input_boxes)
            box_width = 180 if total <= 15 else 140
            box_height = 40
            padding_x = 15
            padding_y = 15
            per_row = 5
            start_x = 50
            start_y = 80

            for i, box in enumerate(input_boxes):
                x = start_x + (i % per_row) * (box_width + padding_x)
                y = start_y + (i // per_row) * (box_height + padding_y)
                rect = pygame.Rect(x, y, box_width, box_height)
                draw_input_box(screen, font, rect, box, i == editing, i == editing and caret_visible)

                if mouse_clicked and rect.collidepoint(mouse_pos):
                    editing = focus_name_field(input_boxes, i)
                    refresh_text_input()

            hint = font.render("Ô đang chọn có viền xanh và con trỏ nhấp nháy.", True, (80, 80, 80))
            screen.blit(hint, (50, 560))

            next_rect = pygame.Rect(800, 620, 150, 50)
            back_rect = pygame.Rect(630, 620, 150, 50)
            pygame.draw.rect(screen, (50, 180, 50), next_rect)
            pygame.draw.rect(screen, (0, 120, 215), next_rect, 3)
            screen.blit(font.render("Tiếp theo", True, (255, 255, 255)), (next_rect.x + 18, next_rect.y + 10))
            pygame.draw.rect(screen, (200, 100, 100), back_rect)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
            screen.blit(font.render("Trở lại", True, (0, 0, 0)), (back_rect.x + 20, back_rect.y + 10))

            if mouse_clicked and next_rect.collidepoint(mouse_pos):
                if all(name.strip() for name in input_boxes):
                    players = [Player(name.strip()) for name in input_boxes]
                    phase = "boxes"
                    error = ""
                else:
                    error = "Hãy nhập tên cho tất cả người chơi."
            elif mouse_clicked and back_rect.collidepoint(mouse_pos):
                phase = "number"

        elif phase == "boxes":
            screen.blit(font.render("Nhập số ô may mắn:", True, (0, 0, 0)), (50, 50))
            input_rect = pygame.Rect(300, 45, 140, 40)
            draw_input_box(screen, font, input_rect, input_number_boxes, True, caret_visible)

            pygame.draw.rect(screen, (100, 200, 100), next_rect)
            pygame.draw.rect(screen, (0, 0, 0), next_rect, 2)
            screen.blit(font.render("Bắt đầu", True, (0, 0, 0)), (next_rect.x + 15, next_rect.y + 5))

            pygame.draw.rect(screen, (200, 100, 100), back_rect)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
            screen.blit(font.render("Trở lại", True, (0, 0, 0)), (back_rect.x + 15, back_rect.y + 5))

            if mouse_clicked:
                if next_rect.collidepoint(mouse_pos):
                    if input_number_boxes.isdigit() and int(input_number_boxes) > 0:
                        return players, int(input_number_boxes), "even", None
                    error = "Số không hợp lệ."
                elif back_rect.collidepoint(mouse_pos):
                    phase = "names"

        if error:
            screen.blit(font.render(error, True, (255, 0, 0)), (50, 650))

        pygame.display.flip()
        clock.tick(30)


def run_default_setup_ui():
    return run_custom_setup_ui()
