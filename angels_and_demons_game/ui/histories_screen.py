import pygame

from constants import BOARD_LAYOUTS
from constants import MODE_VARIANTS
from models.history import clear_game_history
from models.history import delete_game_history_entry
from models.history import load_game_history
from models.turn_modes import TURN_MODE_LABELS
from ui.brand_assets import apply_window_icon
from ui.brand_assets import get_surface
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
    emblem_surface = get_surface("brand_emblem", (44, 44))
    apply_window_icon()

    while running:
        history = load_game_history()
        tick = pygame.time.get_ticks()
        draw_background(screen, tick)

        header_rect = pygame.Rect(34, 24, screen.get_width() - 68, 74)
        draw_panel(screen, header_rect, fill_color=(248, 241, 225), border_color=PALETTE["gold_dark"], radius=24)
        draw_title(screen, font, "Lich su cac van choi", (header_rect.centerx, header_rect.centery), PALETTE["text"])
        if emblem_surface is not None:
            screen.blit(emblem_surface, (header_rect.right - 62, header_rect.y + 14))

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
            top_effects = game.get("top_effects", [])
            extra_lines = 1 if game.get("winner") else 0
            extra_lines += 1 if game.get("num_boxes") else 0
            extra_lines += len(top_effects[:2])
            card_height = 84 + (len(players) + extra_lines) * 26
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
                winner_name = str(game.get("winner", "")).strip()
                if winner_name:
                    winner_score = game.get("winner_score", 0)
                    winner_text = font.render(f"Thang: {winner_name} - {winner_score} diem", True, PALETTE["text"])
                    screen.blit(winner_text, (card_rect.x + 20, player_y))
                    player_y += 26

                num_boxes = game.get("num_boxes")
                if num_boxes:
                    turn_mode = game.get("turn_mode")
                    turn_mode_label = TURN_MODE_LABELS.get(turn_mode, "Lan luot")
                    opened_count = game.get("opened_count", num_boxes)
                    layout_label = BOARD_LAYOUTS.get(str(game.get("layout_id", "classic")), BOARD_LAYOUTS["classic"])["label"]
                    bot_label = "Co bot" if game.get("has_bots") else "Toan nguoi"
                    mode_variant = str(game.get("mode_variant", "standard"))
                    mode_label = MODE_VARIANTS.get(mode_variant, MODE_VARIANTS["standard"])["label"]
                    if mode_variant == "challenge" and game.get("challenge_title"):
                        mode_label = f"{mode_label}: {game.get('challenge_title')}"
                    elif mode_variant == "best_of_three":
                        mode_label = f"{mode_label} - Round {game.get('round_number', 1)}"
                    meta_text = small_font.render(f"{mode_label} | {turn_mode_label} | {opened_count}/{num_boxes} o da mo | {layout_label} | {bot_label}", True, PALETTE["muted"])
                    screen.blit(meta_text, (card_rect.x + 20, player_y))
                    player_y += 24

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

                for effect in top_effects[:2]:
                    effect_label = str(effect.get("label", effect.get("id", "Effect")))
                    effect_count = effect.get("count", 0)
                    effect_text = small_font.render(f"Top effect: {effect_label} x{effect_count}", True, PALETTE["muted"])
                    screen.blit(effect_text, (card_rect.x + 20, player_y))
                    player_y += 22

                achievements = game.get("unlocked_achievements", [])
                if achievements:
                    unlocked_titles = ", ".join(item.get("title", "") for item in achievements[:2])
                    achievement_text = small_font.render(f"Thanh tuu moi: {unlocked_titles}", True, PALETTE["muted"])
                    screen.blit(achievement_text, (card_rect.x + 20, player_y))
                    player_y += 22

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
