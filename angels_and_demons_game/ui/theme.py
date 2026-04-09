import math
import os
import sys

import pygame


PALETTE = {
    "bg_top": (248, 241, 255),
    "bg_bottom": (255, 236, 218),
    "panel": (255, 249, 241),
    "panel_soft": (245, 231, 216),
    "panel_dark": (124, 93, 115),
    "text": (78, 52, 77),
    "muted": (139, 111, 133),
    "gold": (236, 194, 112),
    "gold_dark": (189, 144, 74),
    "crimson": (228, 122, 139),
    "crimson_dark": (173, 83, 104),
    "azure": (124, 183, 224),
    "azure_dark": (79, 131, 175),
    "mint": (149, 205, 176),
    "mint_dark": (92, 148, 119),
    "peach": (247, 181, 155),
    "lilac": (196, 171, 231),
    "cocoa": (150, 110, 90),
    "shadow": (66, 47, 62),
    "white": (255, 252, 248),
}


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

UI_FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "PlaywriteAUNSW-Regular.ttf")
_FONT_CACHE = {}


def normalize_display_text(text):
    value = str(text or "")
    if not any(marker in value for marker in ("Ã", "Â", "Ä", "Æ", "á", "º", "»", "â")):
        return value

    fixed = value
    for _ in range(2):
        try:
            repaired = fixed.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == fixed:
            break
        fixed = repaired
    return fixed


def get_ui_font(size, bold=False, italic=False):
    cache_key = (int(size), bool(bold), bool(italic))
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    try:
        adjustment = 2 if int(size) >= 14 else 1
        adjusted_size = max(10, int(size) - adjustment)
        font = pygame.font.Font(UI_FONT_PATH, adjusted_size)
    except Exception:
        try:
            font = pygame.font.SysFont(["segoeui", "calibri", "arial"], size, bold=bold, italic=italic)
        except Exception:
            font = pygame.font.Font(None, size)

    _FONT_CACHE[cache_key] = font
    return font


def clamp_text(font, text, max_width, suffix="..."):
    text = normalize_display_text(text)
    if max_width <= 0:
        return ""
    if font.size(text)[0] <= max_width:
        return text

    truncated = text
    while truncated and font.size(f"{truncated}{suffix}")[0] > max_width:
        truncated = truncated[:-1]
    return f"{truncated.rstrip()}{suffix}" if truncated else suffix


def wrap_text(font, text, max_width, max_lines=None):
    words = normalize_display_text(text).split()
    if not words:
        return []

    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
            continue

        if current:
            lines.append(current)
        current = word

        if max_lines and len(lines) >= max_lines:
            return lines

    if current and (not max_lines or len(lines) < max_lines):
        lines.append(current)

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
    if max_lines and len(lines) == max_lines:
        lines[-1] = clamp_text(font, lines[-1], max_width)
    return lines


def ease_out_cubic(value):
    value = max(0.0, min(1.0, float(value)))
    return 1.0 - (1.0 - value) ** 3


def get_reveal_progress(start_tick, current_tick, duration=420, delay_ms=0, reduce_motion=False):
    if reduce_motion:
        return 1.0
    elapsed = max(0, int(current_tick) - int(start_tick) - int(delay_ms))
    if elapsed <= 0:
        return 0.0
    return ease_out_cubic(min(1.0, elapsed / max(1, duration)))


def get_reveal_rect(rect, progress, offset_y=18, offset_x=0):
    progress = max(0.0, min(1.0, float(progress)))
    return rect.move(int(round((1.0 - progress) * offset_x)), int(round((1.0 - progress) * offset_y)))


def lerp_color(start_color, end_color, factor):
    return tuple(
        int(start + (end - start) * factor)
        for start, end in zip(start_color, end_color)
    )


def draw_glow(surface, center, color, radius, alpha):
    glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for step in range(radius, 0, -8):
        step_alpha = max(0, int(alpha * (step / max(1, radius))))
        pygame.draw.circle(glow_surface, (*color, step_alpha), (radius, radius), step)
    surface.blit(glow_surface, (center[0] - radius, center[1] - radius))


def draw_cloud(surface, center, scale=1.0, fill_color=None, border_color=None, alpha=220):
    fill_color = fill_color or PALETTE["white"]
    border_color = border_color or PALETTE["panel_dark"]

    width = max(40, int(120 * scale))
    height = max(22, int(46 * scale))
    cloud_surface = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA)

    circles = [
        (int(width * 0.25), int(height * 0.58), int(height * 0.44)),
        (int(width * 0.45), int(height * 0.34), int(height * 0.52)),
        (int(width * 0.62), int(height * 0.52), int(height * 0.46)),
        (int(width * 0.8), int(height * 0.6), int(height * 0.38)),
    ]
    base_rect = pygame.Rect(int(width * 0.15), int(height * 0.45), int(width * 0.7), int(height * 0.44))
    pygame.draw.rect(cloud_surface, (*fill_color, alpha), base_rect, border_radius=int(height * 0.28))
    for x, y, radius in circles:
        pygame.draw.circle(cloud_surface, (*fill_color, alpha), (x, y), radius)

    outline_alpha = min(255, alpha + 10)
    pygame.draw.rect(cloud_surface, (*border_color, outline_alpha), base_rect, 2, border_radius=int(height * 0.28))
    for x, y, radius in circles:
        pygame.draw.circle(cloud_surface, (*border_color, outline_alpha), (x, y), radius, 2)

    surface.blit(cloud_surface, (center[0] - cloud_surface.get_width() // 2, center[1] - cloud_surface.get_height() // 2))


def draw_star(surface, center, radius, color, inner_ratio=0.48):
    points = []
    for index in range(10):
        angle = math.radians(-90 + index * 36)
        current_radius = radius if index % 2 == 0 else radius * inner_ratio
        points.append(
            (
                center[0] + math.cos(angle) * current_radius,
                center[1] + math.sin(angle) * current_radius,
            )
        )
    pygame.draw.polygon(surface, color, points)


def draw_sparkle(surface, center, radius, color):
    pygame.draw.line(surface, color, (center[0] - radius, center[1]), (center[0] + radius, center[1]), 2)
    pygame.draw.line(surface, color, (center[0], center[1] - radius), (center[0], center[1] + radius), 2)
    pygame.draw.line(surface, color, (center[0] - radius * 0.65, center[1] - radius * 0.65), (center[0] + radius * 0.65, center[1] + radius * 0.65), 1)
    pygame.draw.line(surface, color, (center[0] - radius * 0.65, center[1] + radius * 0.65), (center[0] + radius * 0.65, center[1] - radius * 0.65), 1)


def draw_heart(surface, center, size, color, outline_color=None):
    outline_color = outline_color or PALETTE["panel_dark"]
    heart_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    left_center = (int(size * 0.62), int(size * 0.58))
    right_center = (int(size * 1.12), int(size * 0.58))
    radius = max(4, int(size * 0.34))
    bottom_point = (int(size * 0.87), int(size * 1.7))
    points = [left_center, right_center, bottom_point]

    pygame.draw.circle(heart_surface, color, left_center, radius)
    pygame.draw.circle(heart_surface, color, right_center, radius)
    pygame.draw.polygon(
        heart_surface,
        color,
        [
            (int(size * 0.32), int(size * 0.72)),
            (int(size * 1.42), int(size * 0.72)),
            bottom_point,
        ],
    )

    pygame.draw.circle(heart_surface, outline_color, left_center, radius, 2)
    pygame.draw.circle(heart_surface, outline_color, right_center, radius, 2)
    pygame.draw.lines(heart_surface, outline_color, False, points, 2)

    surface.blit(heart_surface, (center[0] - heart_surface.get_width() // 2, center[1] - heart_surface.get_height() // 2))


def draw_mascot(surface, center, variant="angel", tick=0, scale=1.0):
    scale = max(0.4, scale)
    width = int(170 * scale)
    height = int(190 * scale)
    mascot_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    bob = math.sin(tick / 260 + center[0] * 0.01) * 6 * scale
    face_color = (255, 242, 229)
    outline = PALETTE["panel_dark"]
    cheek = PALETTE["peach"]
    eye_color = PALETTE["text"]
    body_rect = pygame.Rect(int(width * 0.28), int(height * 0.76), int(width * 0.44), int(height * 0.18))
    face_center = (width // 2, int(height * 0.42))
    face_radius = int(38 * scale)

    wing_color = (252, 250, 246)
    wing_outline = (176, 158, 138)
    if variant == "angel":
        left_wing = [(int(width * 0.24), int(height * 0.56)), (int(width * 0.1), int(height * 0.46)), (int(width * 0.14), int(height * 0.7))]
        right_wing = [(int(width * 0.76), int(height * 0.56)), (int(width * 0.9), int(height * 0.46)), (int(width * 0.86), int(height * 0.7))]
        pygame.draw.polygon(mascot_surface, wing_color, left_wing)
        pygame.draw.polygon(mascot_surface, wing_color, right_wing)
        pygame.draw.polygon(mascot_surface, wing_outline, left_wing, 2)
        pygame.draw.polygon(mascot_surface, wing_outline, right_wing, 2)
        halo_rect = pygame.Rect(int(width * 0.33), int(height * 0.08), int(width * 0.34), int(height * 0.1))
        pygame.draw.ellipse(mascot_surface, PALETTE["gold"], halo_rect, 6)
    else:
        horn_left = [(int(width * 0.37), int(height * 0.16)), (int(width * 0.31), int(height * 0.03)), (int(width * 0.45), int(height * 0.12))]
        horn_right = [(int(width * 0.63), int(height * 0.16)), (int(width * 0.69), int(height * 0.03)), (int(width * 0.55), int(height * 0.12))]
        pygame.draw.polygon(mascot_surface, PALETTE["crimson"], horn_left)
        pygame.draw.polygon(mascot_surface, PALETTE["crimson"], horn_right)
        tail_points = [
            (int(width * 0.74), int(height * 0.83)),
            (int(width * 0.88), int(height * 0.94)),
            (int(width * 0.78), int(height * 0.78)),
        ]
        pygame.draw.lines(mascot_surface, PALETTE["crimson_dark"], False, tail_points, 4)
        heart = [
            (int(width * 0.89), int(height * 0.95)),
            (int(width * 0.95), int(height * 0.9)),
            (int(width * 0.91), int(height * 0.84)),
            (int(width * 0.85), int(height * 0.9)),
        ]
        pygame.draw.polygon(mascot_surface, PALETTE["crimson"], heart)

    pygame.draw.ellipse(mascot_surface, PALETTE["shadow"], body_rect.move(0, 6))
    pygame.draw.ellipse(
        mascot_surface,
        PALETTE["mint"] if variant == "angel" else PALETTE["crimson"],
        body_rect,
    )
    pygame.draw.ellipse(mascot_surface, outline, body_rect, 2)

    pygame.draw.circle(mascot_surface, face_color, face_center, face_radius)
    pygame.draw.circle(mascot_surface, outline, face_center, face_radius, 2)

    eye_y = int(height * 0.41)
    eye_offset = int(14 * scale)
    eye_radius = max(2, int(3 * scale))
    if variant == "angel":
        left_eye_rect = pygame.Rect(face_center[0] - eye_offset - eye_radius - 2, eye_y - eye_radius, eye_radius * 3, eye_radius * 2)
        right_eye_rect = pygame.Rect(face_center[0] + eye_offset - eye_radius, eye_y - eye_radius, eye_radius * 3, eye_radius * 2)
        pygame.draw.arc(mascot_surface, eye_color, left_eye_rect, math.radians(200), math.radians(340), 2)
        pygame.draw.arc(mascot_surface, eye_color, right_eye_rect, math.radians(200), math.radians(340), 2)
    else:
        pygame.draw.circle(mascot_surface, eye_color, (face_center[0] - eye_offset, eye_y), eye_radius)
        pygame.draw.circle(mascot_surface, eye_color, (face_center[0] + eye_offset, eye_y), eye_radius)
    pygame.draw.circle(mascot_surface, cheek, (face_center[0] - int(21 * scale), int(height * 0.47)), max(4, int(6 * scale)))
    pygame.draw.circle(mascot_surface, cheek, (face_center[0] + int(21 * scale), int(height * 0.47)), max(4, int(6 * scale)))
    if variant == "angel":
        smile_points = [
            (face_center[0] - int(12 * scale), int(height * 0.5)),
            (face_center[0] - int(7 * scale), int(height * 0.53)),
            (face_center[0], int(height * 0.55)),
            (face_center[0] + int(7 * scale), int(height * 0.53)),
            (face_center[0] + int(12 * scale), int(height * 0.5)),
        ]
        pygame.draw.lines(mascot_surface, outline, False, smile_points, 2)
    else:
        grin_points = [
            (face_center[0] - int(12 * scale), int(height * 0.52)),
            (face_center[0] - int(2 * scale), int(height * 0.5)),
            (face_center[0] + int(10 * scale), int(height * 0.54)),
        ]
        pygame.draw.lines(mascot_surface, outline, False, grin_points, 2)

    paw_y = int(height * 0.78)
    pygame.draw.circle(mascot_surface, face_color, (int(width * 0.39), paw_y), max(6, int(8 * scale)))
    pygame.draw.circle(mascot_surface, face_color, (int(width * 0.61), paw_y), max(6, int(8 * scale)))
    pygame.draw.circle(mascot_surface, outline, (int(width * 0.39), paw_y), max(6, int(8 * scale)), 2)
    pygame.draw.circle(mascot_surface, outline, (int(width * 0.61), paw_y), max(6, int(8 * scale)), 2)

    if variant == "angel":
        draw_star(mascot_surface, (int(width * 0.18), int(height * 0.22)), max(6, int(10 * scale)), PALETTE["gold"])
        draw_sparkle(mascot_surface, (int(width * 0.82), int(height * 0.28)), max(6, int(8 * scale)), PALETTE["gold_dark"])
    else:
        draw_star(mascot_surface, (int(width * 0.2), int(height * 0.24)), max(6, int(9 * scale)), PALETTE["crimson"])
        draw_sparkle(mascot_surface, (int(width * 0.82), int(height * 0.28)), max(6, int(8 * scale)), PALETTE["crimson_dark"])

    surface.blit(mascot_surface, (center[0] - width // 2, center[1] - height // 2 + int(bob)))


def draw_background(surface, tick):
    width, height = surface.get_size()
    for y in range(height):
        factor = y / max(1, height - 1)
        color = lerp_color(PALETTE["bg_top"], PALETTE["bg_bottom"], factor)
        pygame.draw.line(surface, color, (0, y), (width, y))

    draw_glow(surface, (width * 0.18, height * 0.2), PALETTE["gold"], 180, 38)
    draw_glow(surface, (width * 0.82, height * 0.2), PALETTE["crimson"], 170, 30)
    draw_glow(surface, (width * 0.55, height * 0.82), PALETTE["azure"], 240, 28)

    drift = tick / 22
    cloud_specs = [
        (0.14, 0.18, 0.95, PALETTE["white"]),
        (0.82, 0.14, 1.15, (255, 248, 243)),
        (0.68, 0.34, 0.72, (251, 247, 242)),
    ]
    for index, (x_ratio, y_ratio, scale, color) in enumerate(cloud_specs):
        offset_x = math.sin(drift * 0.03 + index) * 16
        offset_y = math.cos(drift * 0.04 + index) * 7
        draw_cloud(surface, (int(width * x_ratio + offset_x), int(height * y_ratio + offset_y)), scale, color)

    for index in range(9):
        angle = tick / 900 + index * 0.7
        sparkle_x = int(width * (0.08 + (index * 0.11) % 0.84))
        sparkle_y = int(height * (0.12 + ((index * 0.17) % 0.7)))
        sparkle_size = 5 + index % 3
        sparkle_color = PALETTE["gold"] if index % 2 == 0 else PALETTE["lilac"]
        draw_sparkle(
            surface,
            (
                sparkle_x + int(math.sin(angle) * 7),
                sparkle_y + int(math.cos(angle * 1.3) * 5),
            ),
            sparkle_size,
            sparkle_color,
        )


def draw_panel(surface, rect, fill_color=None, border_color=None, radius=22, shadow=True):
    fill_color = fill_color or PALETTE["panel"]
    border_color = border_color or PALETTE["panel_dark"]

    if shadow:
        shadow_rect = rect.move(0, 10)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (*PALETTE["shadow"], 78),
            shadow_surface.get_rect(),
            border_radius=radius,
        )
        surface.blit(shadow_surface, shadow_rect.topleft)

    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=radius)

    highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 46), pygame.Rect(6, 5, rect.width - 12, max(18, rect.height // 3)), border_radius=max(10, radius - 6))
    surface.blit(highlight, rect.topleft)


def draw_button(surface, font, rect, label, base_color, accent_color, hovered=False, text_color=None):
    button_rect = rect.inflate(0, -4 if hovered else 0).move(0, -3 if hovered else 0)
    text_color = text_color or PALETTE["white"]
    fill = accent_color if hovered else base_color
    draw_panel(surface, button_rect, fill_color=fill, border_color=accent_color, radius=18, shadow=True)

    shine = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(shine, (255, 255, 255, 42), pygame.Rect(8, 6, button_rect.width - 16, max(16, button_rect.height // 3)), border_radius=16)
    surface.blit(shine, button_rect.topleft)

    text = font.render(normalize_display_text(label), True, text_color)
    surface.blit(text, (button_rect.centerx - text.get_width() // 2, button_rect.centery - text.get_height() // 2))


def draw_title(surface, font, text, center, color=None):
    color = color or PALETTE["text"]
    text = normalize_display_text(text)
    shadow = font.render(text, True, PALETTE["white"])
    shadow_rect = shadow.get_rect(center=(center[0] + 3, center[1] + 4))
    surface.blit(shadow, shadow_rect)

    title = font.render(text, True, color)
    rect = title.get_rect(center=center)
    surface.blit(title, rect)
    return rect


def draw_subtitle(surface, font, text, center, color=None):
    color = color or PALETTE["muted"]
    text = normalize_display_text(text)
    subtitle = font.render(text, True, color)
    rect = subtitle.get_rect(center=center)
    surface.blit(subtitle, rect)
    return rect


def draw_hint_bar(surface, font, rect, text, fill_color=None, border_color=None, text_color=None):
    fill_color = fill_color or (247, 239, 223)
    border_color = border_color or PALETTE["panel_dark"]
    text_color = text_color or PALETTE["muted"]
    draw_panel(surface, rect, fill_color=fill_color, border_color=border_color, radius=16, shadow=False)
    text_surface = font.render(clamp_text(font, normalize_display_text(text), rect.width - 24), True, text_color)
    surface.blit(text_surface, (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2))
    return rect


def draw_scrollbar(surface, track_rect, content_height, viewport_height, scroll_y, accent_color=None):
    accent_color = accent_color or PALETTE["gold_dark"]
    if content_height <= viewport_height or track_rect.height <= 0:
        return None

    pygame.draw.rect(surface, (233, 223, 206), track_rect, border_radius=max(8, track_rect.width // 2))
    pygame.draw.rect(surface, PALETTE["panel_dark"], track_rect, 1, border_radius=max(8, track_rect.width // 2))

    thumb_height = max(34, int(track_rect.height * (viewport_height / max(1, content_height))))
    scroll_ratio = scroll_y / max(1, content_height - viewport_height)
    thumb_y = track_rect.y + int((track_rect.height - thumb_height) * scroll_ratio)
    thumb_rect = pygame.Rect(track_rect.x + 2, thumb_y, max(6, track_rect.width - 4), thumb_height)
    pygame.draw.rect(surface, accent_color, thumb_rect, border_radius=max(8, thumb_rect.width // 2))
    pygame.draw.rect(surface, PALETTE["white"], thumb_rect.inflate(-2, -6), 1, border_radius=max(6, thumb_rect.width // 2))
    return thumb_rect
