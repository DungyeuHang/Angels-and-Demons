from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFilter
from PIL import ImageFont


ROOT_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT_DIR / "angels_and_demons_game" / "assets" / "images"


def make_canvas(size):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def draw_circle(draw, center, radius, fill, outline=None, width=1):
    box = (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
    )
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def draw_arc(draw, center, radius, start, end, fill, width=3):
    box = (
        center[0] - radius,
        center[1] - radius,
        center[0] + radius,
        center[1] + radius,
    )
    draw.arc(box, start=start, end=end, fill=fill, width=width)


def add_glow(base, center, radius, color, alpha=110, blur=24):
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse(
        (
            center[0] - radius,
            center[1] - radius,
            center[0] + radius,
            center[1] + radius,
        ),
        fill=(*color, alpha),
    )
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(blur)))


def draw_wing(draw, anchor_x, anchor_y, scale, fill, outline):
    feather_1 = [
        (anchor_x, anchor_y),
        (anchor_x - 30 * scale, anchor_y - 10 * scale),
        (anchor_x - 54 * scale, anchor_y + 28 * scale),
        (anchor_x - 6 * scale, anchor_y + 26 * scale),
    ]
    feather_2 = [
        (anchor_x + 8 * scale, anchor_y + 2 * scale),
        (anchor_x - 18 * scale, anchor_y + 18 * scale),
        (anchor_x - 38 * scale, anchor_y + 54 * scale),
        (anchor_x + 10 * scale, anchor_y + 44 * scale),
    ]
    draw.polygon(feather_1, fill=fill, outline=outline)
    draw.polygon(feather_2, fill=fill, outline=outline)


def draw_halo(draw, center_x, center_y, scale, fill, outline):
    rect = (
        center_x - 38 * scale,
        center_y - 10 * scale,
        center_x + 38 * scale,
        center_y + 10 * scale,
    )
    draw.ellipse(rect, outline=outline, width=max(2, int(5 * scale)))
    inner = (
        center_x - 34 * scale,
        center_y - 6 * scale,
        center_x + 34 * scale,
        center_y + 6 * scale,
    )
    draw.ellipse(inner, outline=fill, width=max(1, int(2 * scale)))


def draw_horns(draw, center_x, center_y, scale, fill, outline):
    left = [
        (center_x - 42 * scale, center_y + 18 * scale),
        (center_x - 28 * scale, center_y - 14 * scale),
        (center_x - 8 * scale, center_y + 18 * scale),
    ]
    right = [
        (center_x + 42 * scale, center_y + 18 * scale),
        (center_x + 28 * scale, center_y - 14 * scale),
        (center_x + 8 * scale, center_y + 18 * scale),
    ]
    draw.polygon(left, fill=fill, outline=outline)
    draw.polygon(right, fill=fill, outline=outline)


def draw_star(draw, center_x, center_y, radius, fill):
    points = [
        (center_x, center_y - radius),
        (center_x + radius * 0.32, center_y - radius * 0.32),
        (center_x + radius, center_y),
        (center_x + radius * 0.32, center_y + radius * 0.32),
        (center_x, center_y + radius),
        (center_x - radius * 0.32, center_y + radius * 0.32),
        (center_x - radius, center_y),
        (center_x - radius * 0.32, center_y - radius * 0.32),
    ]
    draw.polygon(points, fill=fill)


def draw_heart(draw, center_x, center_y, size, fill):
    left_box = (center_x - size, center_y - size, center_x, center_y)
    right_box = (center_x, center_y - size, center_x + size, center_y)
    draw.ellipse(left_box, fill=fill)
    draw.ellipse(right_box, fill=fill)
    draw.polygon(
        [
            (center_x - size * 1.2, center_y - size * 0.2),
            (center_x + size * 1.2, center_y - size * 0.2),
            (center_x, center_y + size * 1.6),
        ],
        fill=fill,
    )


def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_centered_text(draw, center, text, fill, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.text((center[0] - width / 2, center[1] - height / 2 - 1), text, fill=fill, font=font)


def draw_clover(draw, center_x, center_y, scale, fill, outline):
    radius = 20 * scale
    offsets = [(-18, 0), (18, 0), (0, -18), (0, 18)]
    for offset_x, offset_y in offsets:
        draw_circle(
            draw,
            (center_x + int(offset_x * scale), center_y + int(offset_y * scale)),
            int(radius),
            fill,
            outline=outline,
            width=max(2, int(4 * scale)),
        )
    stem = [
        (center_x + int(8 * scale), center_y + int(18 * scale)),
        (center_x + int(30 * scale), center_y + int(52 * scale)),
        (center_x + int(6 * scale), center_y + int(30 * scale)),
    ]
    draw.line(stem, fill=outline, width=max(2, int(4 * scale)))


def draw_ticket(draw, center_x, center_y, width, height, fill, outline):
    rect = (
        center_x - width // 2,
        center_y - height // 2,
        center_x + width // 2,
        center_y + height // 2,
    )
    draw.rounded_rectangle(rect, radius=height // 4, fill=fill, outline=outline, width=3)
    cut_radius = max(6, height // 6)
    for x in (rect[0], rect[2]):
        draw_circle(draw, (x, center_y), cut_radius, (0, 0, 0, 0), outline=fill, width=cut_radius + 2)


def build_effect_icon(effect_id, size=256):
    image = make_canvas(size)
    draw = ImageDraw.Draw(image)
    scale = size / 256
    outline = (103, 74, 98)
    panels = {
        "angel": ((255, 238, 204), (236, 194, 112)),
        "devil": ((255, 220, 231), (228, 122, 139)),
        "gun": ((236, 229, 214), (150, 110, 90)),
        "lucky": ((227, 244, 233), (149, 205, 176)),
        "lottery": ((255, 241, 208), (236, 194, 112)),
        "rps": ((242, 237, 228), (132, 119, 96)),
        "double": ((227, 244, 233), (149, 205, 176)),
        "half": ((255, 227, 232), (228, 122, 139)),
    }
    fill, accent = panels.get(effect_id, ((245, 239, 229), (124, 93, 115)))
    add_glow(image, (size // 2, size // 2), int(size * 0.28), accent, alpha=115, blur=24)
    draw.rounded_rectangle((20, 20, size - 20, size - 20), radius=int(58 * scale), fill=fill, outline=outline, width=max(3, int(6 * scale)))
    draw.rounded_rectangle((34, 34, size - 34, size - 34), radius=int(48 * scale), outline=accent, width=max(2, int(4 * scale)))

    title_font = load_font(int(70 * scale))
    small_font = load_font(int(42 * scale))

    if effect_id == "angel":
        draw_halo(draw, size // 2, int(size * 0.28), scale * 0.9, accent, accent)
        draw_wing(draw, int(size * 0.28), int(size * 0.44), scale * 0.7, (255, 252, 248), outline)
        mirrored = image.transpose(Image.FLIP_LEFT_RIGHT)
        image.alpha_composite(mirrored.crop((0, 0, size // 2, size)))
        draw_circle(draw, (size // 2, int(size * 0.57)), int(40 * scale), (255, 245, 236), outline=outline, width=max(2, int(5 * scale)))
        draw_arc(draw, (size // 2, int(size * 0.58)), int(24 * scale), 20, 160, outline, width=max(2, int(4 * scale)))
    elif effect_id == "devil":
        draw_horns(draw, size // 2, int(size * 0.27), scale * 0.9, accent, accent)
        draw_circle(draw, (size // 2, int(size * 0.57)), int(40 * scale), (255, 236, 241), outline=outline, width=max(2, int(5 * scale)))
        eye_y = int(size * 0.56)
        draw_circle(draw, (int(size * 0.44), eye_y), int(4 * scale), outline)
        draw_circle(draw, (int(size * 0.56), eye_y), int(4 * scale), outline)
        draw_arc(draw, (size // 2, int(size * 0.62)), int(24 * scale), 200, 340, outline, width=max(2, int(4 * scale)))
    elif effect_id == "gun":
        star = [
            (size * 0.34, size * 0.34),
            (size * 0.54, size * 0.46),
            (size * 0.46, size * 0.56),
            (size * 0.64, size * 0.68),
            (size * 0.70, size * 0.60),
            (size * 0.78, size * 0.66),
            (size * 0.80, size * 0.54),
            (size * 0.70, size * 0.46),
        ]
        draw.polygon(star, fill=accent, outline=outline)
        draw_centered_text(draw, (int(size * 0.40), int(size * 0.72)), "!", fill=outline, font=title_font)
    elif effect_id == "lucky":
        draw_clover(draw, size // 2, int(size * 0.54), scale, accent, outline)
        draw_star(draw, int(size * 0.78), int(size * 0.28), int(18 * scale), (236, 194, 112))
    elif effect_id == "lottery":
        draw_ticket(draw, size // 2, int(size * 0.56), int(130 * scale), int(90 * scale), (255, 250, 238), outline)
        draw_centered_text(draw, (size // 2, int(size * 0.56)), "$", fill=accent, font=title_font)
        draw_star(draw, int(size * 0.26), int(size * 0.30), int(16 * scale), accent)
    elif effect_id == "rps":
        draw_centered_text(draw, (size // 2, int(size * 0.46)), "KBB", fill=outline, font=small_font)
        draw_centered_text(draw, (size // 2, int(size * 0.66)), "1 / 2", fill=accent, font=small_font)
    elif effect_id == "double":
        draw_centered_text(draw, (size // 2, int(size * 0.54)), "x2", fill=accent, font=title_font)
        draw_star(draw, int(size * 0.26), int(size * 0.34), int(15 * scale), accent)
        draw_star(draw, int(size * 0.74), int(size * 0.72), int(13 * scale), accent)
    elif effect_id == "half":
        draw_centered_text(draw, (size // 2, int(size * 0.54)), "1/2", fill=accent, font=title_font)
        draw.line((size * 0.32, size * 0.72, size * 0.68, size * 0.36), fill=outline, width=max(3, int(5 * scale)))

    return image


def build_brand_emblem(size=512):
    image = make_canvas(size)
    draw = ImageDraw.Draw(image)
    scale = size / 512

    colors = {
        "cream": (255, 248, 241),
        "angel": (255, 233, 193),
        "demon": (255, 210, 224),
        "gold": (236, 194, 112),
        "gold_dark": (189, 144, 74),
        "crimson": (228, 122, 139),
        "crimson_dark": (173, 83, 104),
        "lilac": (196, 171, 231),
        "outline": (103, 74, 98),
        "peach": (247, 181, 155),
        "mint": (149, 205, 176),
        "shadow": (78, 52, 77),
    }

    center = (size // 2, size // 2)
    add_glow(image, (int(size * 0.37), int(size * 0.38)), int(size * 0.19), colors["gold"], alpha=120, blur=28)
    add_glow(image, (int(size * 0.66), int(size * 0.38)), int(size * 0.19), colors["crimson"], alpha=100, blur=28)

    draw_circle(draw, center, int(182 * scale), colors["cream"], outline=colors["outline"], width=max(3, int(8 * scale)))
    draw_wing(draw, int(size * 0.24), int(size * 0.30), scale, (250, 250, 246), colors["outline"])
    draw_halo(draw, int(size * 0.33), int(size * 0.16), scale, colors["gold"], colors["gold_dark"])
    draw_horns(draw, int(size * 0.67), int(size * 0.15), scale, colors["crimson"], colors["crimson_dark"])

    face_radius = int(116 * scale)
    face_box = (
        center[0] - face_radius,
        center[1] - face_radius + int(8 * scale),
        center[0] + face_radius,
        center[1] + face_radius + int(8 * scale),
    )
    draw.pieslice(face_box, start=90, end=270, fill=colors["angel"])
    draw.pieslice(face_box, start=270, end=90, fill=colors["demon"])
    draw.ellipse(face_box, outline=colors["outline"], width=max(3, int(7 * scale)))

    draw.rectangle(
        (
            center[0] - int(4 * scale),
            center[1] - int(74 * scale),
            center[0] + int(4 * scale),
            center[1] + int(98 * scale),
        ),
        fill=(255, 255, 255, 140),
    )

    eye_y = center[1] - int(8 * scale)
    draw_arc(draw, (center[0] - int(44 * scale), eye_y), int(18 * scale), 200, 340, colors["shadow"], width=max(2, int(5 * scale)))
    draw_arc(draw, (center[0] + int(44 * scale), eye_y), int(18 * scale), 200, 340, colors["shadow"], width=max(2, int(5 * scale)))

    draw_circle(draw, (center[0] - int(62 * scale), center[1] + int(28 * scale)), int(13 * scale), colors["peach"])
    draw_circle(draw, (center[0] + int(62 * scale), center[1] + int(28 * scale)), int(13 * scale), colors["peach"])
    draw_arc(draw, (center[0], center[1] + int(18 * scale)), int(38 * scale), 20, 160, colors["shadow"], width=max(2, int(5 * scale)))

    body_rect = (
        center[0] - int(96 * scale),
        center[1] + int(112 * scale),
        center[0] + int(96 * scale),
        center[1] + int(176 * scale),
    )
    draw.rounded_rectangle(body_rect, radius=int(30 * scale), fill=colors["mint"], outline=colors["outline"], width=max(2, int(6 * scale)))

    tail = [
        (center[0] + int(86 * scale), center[1] + int(140 * scale)),
        (center[0] + int(138 * scale), center[1] + int(178 * scale)),
        (center[0] + int(116 * scale), center[1] + int(120 * scale)),
    ]
    draw.line(tail, fill=colors["crimson_dark"], width=max(2, int(6 * scale)))
    draw_heart(draw, center[0] + int(140 * scale), center[1] + int(184 * scale), int(12 * scale), colors["crimson"])

    draw_star(draw, int(size * 0.19), int(size * 0.20), int(18 * scale), colors["gold"])
    draw_star(draw, int(size * 0.81), int(size * 0.23), int(16 * scale), colors["lilac"])
    draw_heart(draw, int(size * 0.77), int(size * 0.75), int(12 * scale), colors["crimson"])

    return image


def build_side_badge(size=256, variant="angel"):
    image = make_canvas(size)
    draw = ImageDraw.Draw(image)
    scale = size / 256
    colors = {
        "angel_fill": (255, 236, 205),
        "demon_fill": (255, 219, 231),
        "gold": (236, 194, 112),
        "gold_dark": (189, 144, 74),
        "crimson": (228, 122, 139),
        "crimson_dark": (173, 83, 104),
        "outline": (103, 74, 98),
        "peach": (247, 181, 155),
        "white": (255, 251, 247),
        "shadow": (78, 52, 77),
    }

    fill = colors["angel_fill"] if variant == "angel" else colors["demon_fill"]
    draw_circle(draw, (size // 2, size // 2), int(86 * scale), fill, outline=colors["outline"], width=max(2, int(5 * scale)))
    if variant == "angel":
        draw_halo(draw, size // 2, int(size * 0.18), scale * 0.72, colors["gold"], colors["gold_dark"])
    else:
        draw_horns(draw, size // 2, int(size * 0.15), scale * 0.78, colors["crimson"], colors["crimson_dark"])

    eye_y = int(size * 0.50)
    draw_arc(draw, (int(size * 0.40), eye_y), int(13 * scale), 200, 340, colors["shadow"], width=max(2, int(4 * scale)))
    draw_arc(draw, (int(size * 0.60), eye_y), int(13 * scale), 200, 340, colors["shadow"], width=max(2, int(4 * scale)))
    draw_circle(draw, (int(size * 0.36), int(size * 0.60)), int(9 * scale), colors["peach"])
    draw_circle(draw, (int(size * 0.64), int(size * 0.60)), int(9 * scale), colors["peach"])
    draw_arc(draw, (size // 2, int(size * 0.58)), int(24 * scale), 20, 160, colors["shadow"], width=max(2, int(4 * scale)))
    return image


def save_outputs():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    emblem = build_brand_emblem(1024)
    emblem.save(IMAGE_DIR / "friendly_brand_emblem.png")
    emblem.resize((512, 512), Image.LANCZOS).save(IMAGE_DIR / "friendly_app_icon.png")
    emblem.resize((512, 512), Image.LANCZOS).save(
        IMAGE_DIR / "friendly_app_icon.ico",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )

    build_side_badge(256, "angel").save(IMAGE_DIR / "angel_badge.png")
    build_side_badge(256, "demon").save(IMAGE_DIR / "demon_badge.png")

    for effect_id in ("angel", "devil", "gun", "lucky", "lottery", "rps", "double", "half"):
        build_effect_icon(effect_id, 256).save(IMAGE_DIR / f"effect_{effect_id}.png")


if __name__ == "__main__":
    save_outputs()
    print("brand assets generated")
