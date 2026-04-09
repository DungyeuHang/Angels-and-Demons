import os
import sys
from functools import lru_cache

import pygame


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")


ASSET_FILES = {
    "app_icon": "friendly_app_icon.png",
    "brand_emblem": "friendly_brand_emblem.png",
    "angel_badge": "angel_badge.png",
    "demon_badge": "demon_badge.png",
    "effect_angel": "effect_angel.png",
    "effect_devil": "effect_devil.png",
    "effect_gun": "effect_gun.png",
    "effect_lucky": "effect_lucky.png",
    "effect_lottery": "effect_lottery.png",
    "effect_rps": "effect_rps.png",
    "effect_double": "effect_double.png",
    "effect_half": "effect_half.png",
}


def get_asset_path(asset_name):
    filename = ASSET_FILES.get(asset_name)
    if not filename:
        return None
    path = os.path.join(IMAGE_DIR, filename)
    if not os.path.exists(path):
        return None
    return path


@lru_cache(maxsize=32)
def _load_scaled_surface(asset_name, width, height):
    path = get_asset_path(asset_name)
    if not path:
        return None

    surface = pygame.image.load(path)
    try:
        surface = surface.convert_alpha()
    except pygame.error:
        pass

    if width and height:
        surface = pygame.transform.smoothscale(surface, (width, height))
    return surface


def get_surface(asset_name, size=None):
    width = height = 0
    if size:
        width, height = int(size[0]), int(size[1])
    return _load_scaled_surface(asset_name, width, height)


def apply_window_icon():
    icon_surface = get_surface("app_icon", (96, 96))
    if icon_surface is None:
        return False
    try:
        pygame.display.set_icon(icon_surface)
        return True
    except pygame.error:
        return False
