import pygame

from constants import APP_TITLE


MENU_WINDOW_SIZE = (940, 680)
SETUP_WINDOW_SIZE = (1100, 760)
CUSTOM_WINDOW_SIZE = (1200, 760)
GAME_WINDOW_SIZE = (1480, 860)


def build_display_flags(fullscreen=False, resizable=True):
    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    elif resizable:
        flags |= pygame.RESIZABLE
    return flags


def create_display(size, caption, fullscreen=False, resizable=True):
    screen = pygame.display.set_mode(size, build_display_flags(fullscreen=fullscreen, resizable=resizable))
    pygame.display.set_caption(f"{APP_TITLE} - {caption}")
    return screen
