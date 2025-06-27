
import pygame
from mechanics.effects import apply_effect
from mechanics.randomizer import get_random_effect

def run_game_ui(players, num_boxes, dist_mode):
    pygame.init()
    screen = pygame.display.set_mode((1000, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Angels and Demons - Game")
    font_name = "Times New Roman"
    font = pygame.font.SysFont(font_name, 24)
    big_font = pygame.font.SysFont(font_name, 36)
    clock = pygame.time.Clock()

    boxes = list(range(1, num_boxes + 1))
    opened = []
    current_player = 0
    result_message = ""
    chosen_box = None
    waiting_effect_input = False
    effect_to_resolve = None

    running = True
    while running:
        screen.fill((255, 255, 255))

        # Hiển thị người chơi + điểm
        box_w = 160 if len(players) <= 5 else 130
        per_row = 5
        for i, p in enumerate(players):
            row = i // per_row
            col = i % per_row
            text = f"{p.name}: {p.score} điểm"
            font_dynamic = font if len(text) < 15 else pygame.font.SysFont(font_name, 20)
            txt_surf = font_dynamic.render(text, True, (0, 0, 255) if i == current_player else (0, 0, 0))
            screen.blit(txt_surf, (50 + col * box_w, 30 + row * 35))

        # Hiển thị các ô may mắn
        start_y = 150 if len(players) <= 5 else 180
        box_per_row = 10 if num_boxes > 30 else 8
        box_size = 50 if num_boxes > 30 else 60
        for i, n in enumerate(boxes):
            row = i // box_per_row
            col = i % box_per_row
            x = 50 + col * (box_size + 10)
            y = start_y + row * (box_size + 10)
            rect = pygame.Rect(x, y, box_size, box_size)
            if n in opened:
                pygame.draw.rect(screen, (200, 200, 200), rect)
            else:
                pygame.draw.rect(screen, (180, 180, 255), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
            label = font.render(str(n), True, (0, 0, 0))
            screen.blit(label, (x + (box_size - label.get_width())//2, y + 5))

        # Hiển thị kết quả hiệu ứng nếu có

        # Nút kết thúc và quay lại
        quit_rect = pygame.Rect(screen.get_width() - 180, screen.get_height() - 60, 140, 40)
        pygame.draw.rect(screen, (200, 50, 50), quit_rect)
        pygame.draw.rect(screen, (0, 0, 0), quit_rect, 2)
        screen.blit(font.render("⛔ Kết thúc", True, (255, 255, 255)), (quit_rect.x + 15, quit_rect.y + 8))

        back_rect = pygame.Rect(screen.get_width() - 350, screen.get_height() - 60, 140, 40)
        pygame.draw.rect(screen, (180, 180, 180), back_rect)
        pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
        screen.blit(font.render("↩ Quay lại", True, (0, 0, 0)), (back_rect.x + 15, back_rect.y + 8))

        if result_message:
            msg = big_font.render(result_message, True, (0, 102, 204))
            screen.blit(msg, (50, screen.get_height() - 80))

        pygame.display.flip()

        for event in pygame.event.get():
            # Bấm nút kết thúc/quay lại
            if event.type == pygame.MOUSEBUTTONDOWN:
                if quit_rect.collidepoint(event.pos):
                    running = False
                    break
                elif back_rect.collidepoint(event.pos):
                    return  # Quay lại menu (nếu cần gọi từ menu)

            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN and waiting_effect_input:
                if event.key == pygame.K_1:
                    effect_to_resolve['win'] = True
                    waiting_effect_input = False
                elif event.key == pygame.K_2:
                    effect_to_resolve['win'] = False
                    waiting_effect_input = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not waiting_effect_input:
                pos = pygame.mouse.get_pos()
                for i, n in enumerate(boxes):
                    if n in opened:
                        continue
                    row = i // box_per_row
                    col = i % box_per_row
                    x = 50 + col * (box_size + 10)
                    y = start_y + row * (box_size + 10)
                    rect = pygame.Rect(x, y, box_size, box_size)
                    if rect.collidepoint(pos):
                        chosen_box = n
                        opened.append(n)
                        player = players[current_player]
                        effect_id = get_random_effect(dist_mode)

                        if effect_id == 6:  # Kéo Búa Bao
                            result_message = f"{player.name} chọn ô số {n} - Kéo Búa Bao! Nhấn 1: thắng, 2: thua"
                            effect_to_resolve = {'player': player}
                            waiting_effect_input = True
                        else:
                            result_message = f"{player.name} chọn ô số {n} - {apply_effect(effect_id, player, players)}"

        # Nếu vừa nhập kết quả Kéo Búa Bao xong
        if not waiting_effect_input and effect_to_resolve:
            player = effect_to_resolve['player']
            if effect_to_resolve['win']:
                player.score += 10
                result_message = f"{player.name} thắng Kéo Búa Bao! +10 điểm"
            else:
                result_message = f"{player.name} thua Kéo Búa Bao! Không có điểm"
            effect_to_resolve = None
            waiting_effect_input = False
            # Chưa tăng lượt vội, chờ tick sau
            player = effect_to_resolve['player']
            if effect_to_resolve['win']:
                player.score += 10
                result_message = f"{player.name} thắng Kéo Búa Bao! +10 điểm"
                pygame.time.delay(1000)
            else:
                result_message = f"{player.name} thua Kéo Búa Bao! Không có điểm"
                pygame.time.delay(1000)
                effect_to_resolve = None

            players.sort(key=lambda p: p.score, reverse=True)
            end_running = True
            while end_running:
                screen.fill((255, 255, 255))
                title = big_font.render('🏆 KẾT THÚC GAME', True, (200, 50, 50))
                screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 50))
                for i, p in enumerate(players):
                    text = font.render(f'{i+1}. {p.name}: {p.score} điểm', True, (0, 0, 0))
                    screen.blit(text, (100, 120 + i * 35))
                # Nút
                quit_rect = pygame.Rect(screen.get_width() - 180, screen.get_height() - 60, 140, 40)
                pygame.draw.rect(screen, (200, 50, 50), quit_rect)
                pygame.draw.rect(screen, (0, 0, 0), quit_rect, 2)
                screen.blit(font.render('❌ Thoát', True, (255, 255, 255)), (quit_rect.x + 25, quit_rect.y + 8))
                back_rect = pygame.Rect(screen.get_width() - 350, screen.get_height() - 60, 140, 40)
                pygame.draw.rect(screen, (180, 180, 180), back_rect)
                pygame.draw.rect(screen, (0, 0, 0), back_rect, 2)
                screen.blit(font.render('↩ Menu', True, (0, 0, 0)), (back_rect.x + 30, back_rect.y + 8))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if quit_rect.collidepoint(event.pos):
                            pygame.quit()
                            exit()
                        elif back_rect.collidepoint(event.pos):
                            return
                clock.tick(30)
