import pygame

from models.history import clear_game_history
from models.history import delete_game_history_entry
from models.history import load_game_history
from ui.theme import PALETTE
from ui.theme import draw_background
from ui.theme import draw_button
from ui.theme import draw_panel
from ui.theme import draw_title


def show_history_screen(screen, font):
    scroll_y = 0
    scroll_speed = 32
    running = True
    small_font = pygame.font.Font(font.path, 16) if hasattr(font, "path") else font

    while running:
        history = load_game_history()
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)

        header_rect = pygame.Rect(34, 24, screen.get_width() - 68, 74)
        draw_panel(screen, header_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=24)
        draw_title(screen, font, "Lich su cac van choi", (header_rect.centerx, header_rect.centery), PALETTE["text"])

        clear_all_rect = pygame.Rect(screen.get_width() - 210, 116, 170, 46)
        if history:
            draw_button(screen, font, clear_all_rect, "Xoa tat ca", PALETTE["crimson"], PALETTE["crimson_dark"], clear_all_rect.collidepoint(pygame.mouse.get_pos()))

        content_top = 176
        content_bottom = screen.get_height() - 90
        content_height = 0
        delete_buttons = []

        y = content_top - scroll_y
        for display_index, history_index in enumerate(range(len(history) - 1, -1, -1), start=1):
            game = history[history_index]
            players = game.get("players", [])
            card_height = 84 + len(players) * 28
            card_rect = pygame.Rect(40, y, screen.get_width() - 80, card_height)

            if card_rect.bottom >= content_top and card_rect.top <= content_bottom:
                draw_panel(screen, card_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=20)
                stripe_rect = pygame.Rect(card_rect.x, card_rect.y, card_rect.width, 42)
                pygame.draw.rect(screen, PALETTE["panel_dark"], stripe_rect, border_top_left_radius=20, border_top_right_radius=20)

                title_text = font.render(f"Tran {display_index} - {game.get('timestamp', 'Unknown')}", True, PALETTE["white"])
                screen.blit(title_text, (card_rect.x + 18, card_rect.y + 10))

                delete_rect = pygame.Rect(card_rect.right - 118, card_rect.y + 8, 92, 28)
                draw_button(screen, small_font, delete_rect, "Xoa", PALETTE["crimson"], PALETTE["crimson_dark"], delete_rect.collidepoint(pygame.mouse.get_pos()))
                delete_buttons.append((history_index, delete_rect))

                player_y = card_rect.y + 56
                for player_index, player in enumerate(players, start=1):
                    bullet_color = PALETTE["gold"] if player_index == 1 else PALETTE["azure"]
                    pygame.draw.circle(screen, bullet_color, (card_rect.x + 26, player_y + 10), 6)
                    player_text = font.render(
                        f"{player.get('name', 'Unknown')}: {player.get('score', 0)} diem",
                        True,
                        PALETTE["text"],
                    )
                    screen.blit(player_text, (card_rect.x + 42, player_y))
                    player_y += 26

            y += card_height + 16
            content_height += card_height + 16

        if not history:
            empty_rect = pygame.Rect(screen.get_width() // 2 - 220, screen.get_height() // 2 - 70, 440, 140)
            draw_panel(screen, empty_rect, fill_color=(247, 239, 223), border_color=PALETTE["panel_dark"], radius=24)
            draw_title(screen, font, "Chua co lich su", (empty_rect.centerx, empty_rect.centery - 12), PALETTE["text"])
            helper = small_font.render("Bat dau mot tran moi de lap day bo suu tap ky niem.", True, PALETTE["muted"])
            screen.blit(helper, (empty_rect.centerx - helper.get_width() // 2, empty_rect.centery + 22))

        back_rect = pygame.Rect(screen.get_width() // 2 - 90, screen.get_height() - 60, 180, 44)
        draw_button(screen, font, back_rect, "Quay lai", PALETTE["mint"], PALETTE["mint_dark"], back_rect.collidepoint(pygame.mouse.get_pos()), PALETTE["text"])

        pygame.display.flip()

        max_scroll = max(0, content_height - (content_bottom - content_top))
        scroll_y = max(0, min(scroll_y, max_scroll))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and back_rect.collidepoint(event.pos):
                    running = False
                elif event.button == 1 and history and clear_all_rect.collidepoint(event.pos):
                    clear_game_history()
                    scroll_y = 0
                elif event.button == 1:
                    for history_index, delete_rect in delete_buttons:
                        if delete_rect.collidepoint(event.pos):
                            delete_game_history_entry(history_index)
                            break
                elif event.button == 4:
                    scroll_y = max(0, scroll_y - scroll_speed)
                elif event.button == 5:
                    scroll_y = min(max_scroll, scroll_y + scroll_speed)
