import pygame


PALETTE = {
    "bg_top": (30, 21, 54),
    "bg_bottom": (11, 14, 29),
    "panel": (248, 241, 225),
    "panel_soft": (231, 220, 199),
    "panel_dark": (58, 44, 77),
    "text": (33, 23, 47),
    "muted": (109, 91, 126),
    "gold": (223, 184, 97),
    "gold_dark": (173, 129, 57),
    "crimson": (180, 70, 81),
    "crimson_dark": (125, 40, 61),
    "azure": (96, 137, 219),
    "azure_dark": (55, 82, 150),
    "mint": (119, 180, 154),
    "mint_dark": (66, 110, 93),
    "shadow": (9, 7, 18),
    "white": (255, 248, 240),
}


def lerp_color(start_color, end_color, factor):
    return tuple(
        int(start + (end - start) * factor)
        for start, end in zip(start_color, end_color)
    )


def draw_background(surface, tick):
    width, height = surface.get_size()
    for y in range(height):
        factor = y / max(1, height - 1)
        color = lerp_color(PALETTE["bg_top"], PALETTE["bg_bottom"], factor)
        pygame.draw.line(surface, color, (0, y), (width, y))

    draw_glow(surface, (width * 0.18, height * 0.2), PALETTE["gold"], 180, 52)
    draw_glow(surface, (width * 0.85, height * 0.25), PALETTE["azure"], 220, 44)
    draw_glow(surface, (width * 0.55, height * 0.82), PALETTE["crimson"], 260, 30)

    offset = tick // 14
    for index in range(8):
        x = int((index * 173 + offset * (index + 1) * 0.35) % (width + 160)) - 80
        y = int((height * 0.18 + index * 67 + offset * 0.5) % (height + 180)) - 90
        radius = 24 + (index % 3) * 10
        color = PALETTE["gold"] if index % 2 == 0 else PALETTE["azure"]
        draw_glow(surface, (x, y), color, radius * 2, 18)


def draw_glow(surface, center, color, radius, alpha):
    glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for step in range(radius, 0, -8):
        step_alpha = max(0, int(alpha * (step / max(1, radius))))
        pygame.draw.circle(
            glow_surface,
            (*color, step_alpha),
            (radius, radius),
            step,
        )
    surface.blit(glow_surface, (center[0] - radius, center[1] - radius))


def draw_panel(surface, rect, fill_color=None, border_color=None, radius=22, shadow=True):
    fill_color = fill_color or PALETTE["panel"]
    border_color = border_color or PALETTE["panel_dark"]

    if shadow:
        shadow_rect = rect.move(0, 10)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (*PALETTE["shadow"], 120),
            shadow_surface.get_rect(),
            border_radius=radius,
        )
        surface.blit(shadow_surface, shadow_rect.topleft)

    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    pygame.draw.rect(surface, border_color, rect, 2, border_radius=radius)


def draw_button(surface, font, rect, label, base_color, accent_color, hovered=False, text_color=None):
    color = accent_color if hovered else base_color
    text_color = text_color or PALETTE["white"]
    draw_panel(surface, rect, fill_color=color, border_color=accent_color, radius=18, shadow=True)
    text = font.render(label, True, text_color)
    surface.blit(
        text,
        (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2),
    )


def draw_title(surface, font, text, center, color=None):
    color = color or PALETTE["panel"]
    shadow = font.render(text, True, PALETTE["shadow"])
    shadow_rect = shadow.get_rect(center=(center[0] + 3, center[1] + 4))
    surface.blit(shadow, shadow_rect)

    title = font.render(text, True, color)
    rect = title.get_rect(center=center)
    surface.blit(title, rect)
    return rect


def draw_subtitle(surface, font, text, center, color=None):
    color = color or PALETTE["panel_soft"]
    subtitle = font.render(text, True, color)
    rect = subtitle.get_rect(center=center)
    surface.blit(subtitle, rect)
    return rect
