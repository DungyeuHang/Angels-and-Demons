import pygame

from constants import APP_TITLE


MENU_WINDOW_SIZE = (1280, 720)
SETUP_WINDOW_SIZE = (1280, 720)
CUSTOM_WINDOW_SIZE = (1280, 720)
GAME_WINDOW_SIZE = (1280, 720)


def build_display_flags(fullscreen=False, resizable=True):
    flags = 0
    if fullscreen:
        flags |= pygame.FULLSCREEN
    elif resizable:
        flags |= pygame.RESIZABLE
    return flags


def create_display(size, caption, fullscreen=False, resizable=True):
    display_size = (0, 0) if fullscreen else size
    screen = pygame.display.set_mode(display_size, build_display_flags(fullscreen=fullscreen, resizable=resizable))
    pygame.display.set_caption(f"{APP_TITLE} - {caption}")
    return screen
