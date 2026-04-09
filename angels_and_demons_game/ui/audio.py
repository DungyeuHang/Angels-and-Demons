import os
import sys

import pygame

from models.settings import load_settings
from models.settings import sanitize_settings


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


MUSIC_DIR = os.path.join(BASE_DIR, "assets", "music")
SFX_DIR = os.path.join(BASE_DIR, "assets", "sounds")

TRACKS = {
    "menu": {"file": "menu_theme.mp3", "volume": 0.42},
    "game": {"file": "game_theme.ogg", "volume": 0.33},
    "result": {"file": "result_theme.mp3", "volume": 0.46},
    "history": {"file": "history_theme.ogg", "volume": 0.28},
}

SFX_FILES = {
    "angel": "angels.mp3",
    "devil": "devil.mp3",
    "gun": "gun.mp3",
    "lucky": "lucky.mp3",
    "lottery": "lotery.mp3",
    "rps": "rps.mp3",
    "double": "double.mp3",
    "half": "half.mp3",
    "shield": "angels.mp3",
    "swap": "devil.mp3",
    "reverse": "double.mp3",
    "oracle": "lucky.mp3",
    "box_flip": "box_flip.wav",
    "ui_click": "ui_click.wav",
    "point_gain": "point_gain.wav",
    "point_loss": "point_loss.wav",
    "achievement": "achievement.wav",
    "bot_move": "bot_move.wav",
}

_CURRENT_TRACK_KEY = None
_RUNTIME_SETTINGS = load_settings()
_SOUND_CACHE = {}


def sync_audio_settings(settings=None):
    global _RUNTIME_SETTINGS
    _RUNTIME_SETTINGS = sanitize_settings(settings or load_settings())
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        track = TRACKS.get(_CURRENT_TRACK_KEY)
        if track:
            pygame.mixer.music.set_volume(_get_music_volume(float(track.get("volume", 0.4))))
    return dict(_RUNTIME_SETTINGS)


def get_audio_settings():
    return dict(_RUNTIME_SETTINGS)


def _ensure_mixer_ready():
    if pygame.mixer.get_init():
        return True
    try:
        pygame.mixer.init()
        return True
    except pygame.error:
        return False


def _get_music_volume(base_volume):
    if not _RUNTIME_SETTINGS.get("music_enabled", True):
        return 0.0
    return max(0.0, min(1.0, float(base_volume) * float(_RUNTIME_SETTINGS.get("music_volume", 0.6))))


def _get_sfx_volume(base_volume):
    if not _RUNTIME_SETTINGS.get("sfx_enabled", True):
        return 0.0
    return max(0.0, min(1.0, float(base_volume) * float(_RUNTIME_SETTINGS.get("sfx_volume", 0.7))))


def _resolve_track_path(track_key):
    track = TRACKS.get(track_key)
    if not track:
        return None, None
    path = os.path.join(MUSIC_DIR, track["file"])
    if not os.path.exists(path):
        return None, None
    return path, float(track.get("volume", 0.4))


def _load_sound(sound_key):
    if sound_key in _SOUND_CACHE:
        return _SOUND_CACHE[sound_key]

    filename = SFX_FILES.get(sound_key)
    if not filename:
        _SOUND_CACHE[sound_key] = None
        return None

    path = os.path.join(SFX_DIR, filename)
    if not os.path.exists(path) or not _ensure_mixer_ready():
        _SOUND_CACHE[sound_key] = None
        return None

    try:
        sound = pygame.mixer.Sound(path)
    except pygame.error:
        sound = None
    _SOUND_CACHE[sound_key] = sound
    return sound


def play_music(track_key, loops=-1, fade_ms=500, force_restart=False):
    global _CURRENT_TRACK_KEY

    path, base_volume = _resolve_track_path(track_key)
    if path is None or not _ensure_mixer_ready():
        return False

    if not force_restart and _CURRENT_TRACK_KEY == track_key and pygame.mixer.music.get_busy():
        pygame.mixer.music.set_volume(_get_music_volume(base_volume))
        return True

    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_get_music_volume(base_volume))
        pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        _CURRENT_TRACK_KEY = track_key
        return True
    except pygame.error:
        return False


def stop_music(fade_ms=300):
    global _CURRENT_TRACK_KEY
    if not pygame.mixer.get_init():
        return False
    try:
        pygame.mixer.music.fadeout(fade_ms)
        _CURRENT_TRACK_KEY = None
        return True
    except pygame.error:
        return False


def play_sfx(sound_key, volume_multiplier=1.0, stop_others=False):
    sound = _load_sound(sound_key)
    if sound is None or not _ensure_mixer_ready():
        return False

    effective_volume = _get_sfx_volume(volume_multiplier)
    if effective_volume <= 0:
        return False

    if stop_others:
        pygame.mixer.stop()

    try:
        sound.set_volume(effective_volume)
        sound.play()
        return True
    except pygame.error:
        return False
