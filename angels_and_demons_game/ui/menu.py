# menu.py - auto-generated
def run_menu_ui():
    import pygame
    from ui.custom_setup import run_custom_setup_ui
    from ui.histories_screen import show_histories_screen
    from ui.game_screen import run_game_ui
    import sys

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Angels and Demons - Menu")

    font = pygame.font.SysFont("Times New Roman", 36)
    clock = pygame.time.Clock()

    options = ["Chơi (Tùy chỉnh)", "Xem lịch sử", "Thoát"]
    option_rects = []
    option_rects = []
    selected = 0

    while True:
        screen.fill((240, 240, 240))
        title = font.render("🌟 Angels and Demons 🌟", True, (0, 0, 0))
        screen.blit(title, (230, 50))

        for i, option in enumerate(options):
            option_rects.clear()
            color = (0, 100, 200) if i == selected else (0, 0, 0)
            text = font.render(option, True, color)
            screen.blit(text, (250, 150 + i * 60))
        option_rects.append(pygame.Rect(250, 150 + i * 60, 300, 50))
        option_rects.append(pygame.Rect(250, 150 + i * 60, 300, 50))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for i, rect in enumerate(option_rects):
                    if rect.collidepoint(mx, my):
                        selected = i
                        if selected == 0:
                            players, num_boxes, dist_mode = run_custom_setup_ui()
                            if players:
                                run_game_ui(players, num_boxes, dist_mode)
                        elif selected == 1:
                            show_histories_screen()
                        elif selected == 2:
                            pygame.quit()
                            sys.exit()
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

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
                        show_histories_screen()
                    elif selected == 2:
                        pygame.quit()
                        sys.exit()
