import pygame

from screens.helpers import draw_coin_icon, draw_star_icon
from screens.maps import MAP_BACKGROUND_FILES, MAPS

SKY = (123, 205, 230)
CREAM = (255, 246, 218)
DARK_GREEN = (30, 105, 57)
GREEN = (65, 155, 75)
J_GREEN = (40, 150, 90)
J_GREEN_HOVER = (60, 190, 120)
YELLOW = (255, 205, 75)
BROWN = (120, 76, 45)
WHITE = (255, 255, 255)
DARK = (35, 65, 54)
GRAY = (120, 130, 125)
LOCK_GRAY = (105, 110, 108)
LOCK_BORDER = (70, 75, 73)
LOCKED_CARD = (205, 205, 195)
NAME_STRIP = (18, 32, 28)
DIVIDER = (214, 205, 175)

TITLE_FONT = None
BODY_FONT = None
SMALL_FONT = None

# The 6 maps live in screens/maps.py
LEVELS = MAPS

DIFFICULTY_COLORS = {
    "EASY": (50, 140, 70),
    "NORMAL": (200, 140, 30),
    "HARD": (200, 90, 40),
    "EXPERT": (170, 50, 60),
}

_PREVIEW_CACHE = {}
_MASK_CACHE = {}


def init_level_map_fonts():
    global TITLE_FONT, BODY_FONT, SMALL_FONT

    TITLE_FONT = pygame.font.SysFont("arial", 36, bold=True)
    BODY_FONT = pygame.font.SysFont("arial", 20, bold=True)
    SMALL_FONT = pygame.font.SysFont("arial", 16)


def draw_text(surface, text, font, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_padlock(
    surface, x, y, scale=1.0,
    shackle_color=(90, 90, 95),
    body_color=(110, 110, 118),
    keyhole_color=(45, 45, 50),
):
    stroke = max(2, int(4 * scale))
    shackle_w = int(16 * scale)
    shackle_h = int(20 * scale)
    body_w = int(22 * scale)
    body_h = int(16 * scale)

    pygame.draw.arc(
        surface,
        shackle_color,
        (
            x - shackle_w // 2,
            y - body_h // 2 - shackle_h // 2,
            shackle_w,
            shackle_h,
        ),
        0,
        3.14159,
        stroke,
    )
    pygame.draw.rect(
        surface,
        body_color,
        (x - body_w // 2, y - body_h // 2, body_w, body_h),
        border_radius=max(2, int(4 * scale)),
    )
    pygame.draw.circle(
        surface, keyhole_color, (x, y), max(2, int(3 * scale))
    )


def _rounded_mask(size, radius):
    key = (size, radius)
    mask = _MASK_CACHE.get(key)

    if mask is None:
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(
            mask,
            (255, 255, 255, 255),
            mask.get_rect(),
            border_radius=radius,
        )
        _MASK_CACHE[key] = mask

    return mask


def _rounded_blit(destination, source, rect, radius):
    """Blit a surface through a rounded-corner alpha mask."""
    if source.get_size() != rect.size:
        source = pygame.transform.smoothscale(source, rect.size)

    clipped = pygame.Surface(rect.size, pygame.SRCALPHA)
    clipped.blit(source, (0, 0))
    clipped.blit(_rounded_mask(rect.size, radius), (0, 0),
                 special_flags=pygame.BLEND_RGBA_MIN)
    destination.blit(clipped, rect.topleft)


def _get_preview(map_id, size):
    """Load and cache the map background preview scaled to size."""
    key = (map_id, size)

    if key in _PREVIEW_CACHE:
        return _PREVIEW_CACHE[key]

    preview = None
    path = MAP_BACKGROUND_FILES.get(map_id)

    if path:
        try:
            image = pygame.image.load(path).convert()
            preview = pygame.transform.smoothscale(image, size)
        except (pygame.error, OSError, FileNotFoundError):
            preview = None

    _PREVIEW_CACHE[key] = preview
    return preview


def _draw_preview(surface, level, rect, unlocked, map_number):
    radius = 16
    preview = _get_preview(level["id"], rect.size)

    if preview is not None:
        _rounded_blit(surface, preview, rect, radius)
    else:
        pygame.draw.rect(surface, level["color"], rect, border_radius=radius)

    if not unlocked:
        dim = pygame.Surface(rect.size, pygame.SRCALPHA)
        dim.fill((10, 20, 15, 140))
        _rounded_blit(surface, dim, rect, radius)

    pygame.draw.rect(surface, WHITE, rect, width=3, border_radius=radius)

    # Map number badge (top-left of the preview)
    badge_center = (rect.x + 36, rect.y + 36)
    badge_color = level["color"] if unlocked else GRAY
    pygame.draw.circle(surface, badge_color, badge_center, 22)
    pygame.draw.circle(surface, WHITE, badge_center, 22, 3)
    draw_text(surface, str(map_number), BODY_FONT, WHITE, badge_center)

    # Difficulty pill (top-right of the preview)
    diff_name = level["difficulty"]
    diff_color = DIFFICULTY_COLORS.get(diff_name, BROWN) if unlocked else GRAY
    diff_rect = pygame.Rect(rect.right - 144, rect.y + 14, 130, 30)
    pygame.draw.rect(surface, diff_color, diff_rect, border_radius=15)
    pygame.draw.rect(surface, WHITE, diff_rect, width=2, border_radius=15)
    draw_text(surface, diff_name, BODY_FONT, WHITE, diff_rect.center)

    # Map name strip (bottom of the preview)
    strip = pygame.Rect(rect.x + 10, rect.bottom - 54, rect.w - 20, 44)
    pygame.draw.rect(surface, NAME_STRIP, strip, border_radius=10)
    draw_text(surface, level["name"], TITLE_FONT, WHITE, strip.center)

    if not unlocked:
        draw_padlock(
            surface,
            rect.centerx,
            rect.centery - 8,
            scale=2.2,
            shackle_color=(235, 238, 240),
            body_color=(245, 247, 248),
            keyhole_color=(90, 95, 100),
        )


def draw_level_map(
    surface,
    mouse_position,
    unlocked_count=1,
    best=None,
    coins=0,
    allowed_map_ids=None,
    current_map_index=0,
):
    if best is None:
        best = {}

    width, height = surface.get_size()

    surface.fill(SKY)

    # Filter maps
    if allowed_map_ids is None:
        visible_levels = list(enumerate(LEVELS))
    else:
        visible_levels = [
            (index, level)
            for index, level in enumerate(LEVELS)
            if level["id"] in allowed_map_ids
        ]

    total_maps = max(1, len(visible_levels))
    idx = current_map_index % total_maps
    original_index, level = visible_levels[idx]

    # Unlocked status
    unlocked = (
        True
        if allowed_map_ids is not None
        else original_index < unlocked_count
    )

    # ---- Title panel ----
    title_panel = pygame.Rect(width // 2 - 280, 12, 560, 74)
    pygame.draw.rect(surface, CREAM, title_panel, border_radius=18)
    pygame.draw.rect(
        surface, DARK_GREEN, title_panel,
        width=3, border_radius=18
    )
    draw_text(
        surface, "BARANGAY WORLD MAP",
        TITLE_FONT, DARK_GREEN,
        (width // 2, 38)
    )
    subtitle = (
        "Choose your map!"
        if allowed_map_ids is not None
        else "Finish a map to unlock the next one!"
    )
    draw_text(
        surface, subtitle,
        SMALL_FONT, DARK,
        (width // 2, 70)
    )

    # ---- Coin balance pill (top-left) ----
    coin_box = pygame.Rect(25, 26, 130, 34)
    pygame.draw.rect(surface, CREAM, coin_box, border_radius=17)
    pygame.draw.rect(surface, DARK_GREEN, coin_box, 2, border_radius=17)
    draw_coin_icon(
        surface, coin_box.left + 20, coin_box.centery, 11, pygame.time.get_ticks() / 300.0
    )
    draw_text(
        surface, str(coins), BODY_FONT, DARK_GREEN,
        (coin_box.centerx + 12, coin_box.centery)
    )

    # ---- Large central card ----
    card_w = min(660, width - 240)
    card_h = min(450, height - 200)
    card = pygame.Rect(0, 0, card_w, card_h)
    card.center = (width // 2, 96 + card_h // 2)

    panel_color = CREAM if unlocked else LOCKED_CARD
    pygame.draw.rect(surface, panel_color, card, border_radius=20)
    pygame.draw.rect(
        surface, YELLOW if unlocked else GRAY,
        card, width=4, border_radius=20
    )

    # ---- Map background preview inside the card ----
    pad = 16
    preview_rect = pygame.Rect(
        card.x + pad, card.y + pad,
        card.w - pad * 2, card_h - 216,
    )
    _draw_preview(surface, level, preview_rect, unlocked, original_index + 1)

    # ---- Description ----
    draw_text(
        surface, level["description"],
        BODY_FONT, DARK if unlocked else GRAY,
        (card.centerx, preview_rect.bottom + 26)
    )

    # ---- High score ----
    record = best.get(level["id"])
    score_y = preview_rect.bottom + 60

    if record:
        draw_star_icon(surface, card.centerx - 80, score_y, 9)
        draw_text(
            surface, f"BEST: {record} PTS",
            BODY_FONT, DARK_GREEN,
            (card.centerx + 10, score_y)
        )
    else:
        draw_text(
            surface, "NO SCORE YET",
            BODY_FONT, GRAY,
            (card.centerx, score_y)
        )

    # ---- Divider ----
    divider_y = preview_rect.bottom + 84
    pygame.draw.line(
        surface, DIVIDER,
        (card.x + 40, divider_y),
        (card.right - 40, divider_y), 2
    )

    # ---- PLAY button or unlock requirement ----
    action_y = card.bottom - pad - 56

    if unlocked:
        play_rect = pygame.Rect(card.centerx - 110, action_y, 220, 56)
        hover = play_rect.collidepoint(mouse_position)
        btn_color = J_GREEN_HOVER if hover else J_GREEN
        pygame.draw.rect(surface, btn_color, play_rect, border_radius=14)
        pygame.draw.rect(surface, DARK, play_rect, width=3, border_radius=14)
        draw_text(
            surface, "PLAY",
            TITLE_FONT, WHITE,
            play_rect.center
        )
        action_rect = play_rect
    else:
        # Exact unlock requirement with a lock icon
        if original_index > 0:
            requirement_text = (
                f"CLEAR {LEVELS[original_index - 1]['name']} TO UNLOCK"
            )
        else:
            requirement_text = "UNLOCKED"

        action_rect = pygame.Rect(
            card.centerx - 230, action_y, 460, 56
        )
        pygame.draw.rect(
            surface, LOCK_GRAY, action_rect, border_radius=14
        )
        pygame.draw.rect(
            surface, LOCK_BORDER, action_rect,
            width=3, border_radius=14
        )
        draw_padlock(
            surface,
            action_rect.x + 34,
            action_rect.centery,
            scale=1.1,
            shackle_color=(235, 238, 240),
            body_color=(245, 247, 248),
            keyhole_color=(90, 95, 100),
        )
        draw_text(
            surface, requirement_text,
            BODY_FONT, WHITE,
            (action_rect.centerx + 18, action_rect.centery)
        )

    # ---- Left / right navigation arrows ----
    arrow_w, arrow_h = 48, 54
    left_rect = pygame.Rect(
        card.x - 64, card.centery - arrow_h // 2, arrow_w, arrow_h
    )
    right_rect = pygame.Rect(
        card.right + 16, card.centery - arrow_h // 2, arrow_w, arrow_h
    )

    for arrow_rect, direction in ((left_rect, -1), (right_rect, 1)):
        hover = arrow_rect.collidepoint(mouse_position)
        fill = YELLOW if hover else CREAM
        pygame.draw.rect(surface, fill, arrow_rect, border_radius=12)
        pygame.draw.rect(
            surface, DARK_GREEN, arrow_rect,
            width=3, border_radius=12
        )

        if direction < 0:
            points = [
                (arrow_rect.right - 15, arrow_rect.y + 14),
                (arrow_rect.right - 15, arrow_rect.bottom - 14),
                (arrow_rect.x + 15, arrow_rect.centery),
            ]
        else:
            points = [
                (arrow_rect.x + 15, arrow_rect.y + 14),
                (arrow_rect.x + 15, arrow_rect.bottom - 14),
                (arrow_rect.right - 15, arrow_rect.centery),
            ]

        pygame.draw.polygon(
            surface, DARK if hover else DARK_GREEN, points
        )

    # ---- Position counter under the card ----
    counter = pygame.Rect(card.centerx - 58, card.bottom + 6, 116, 26)
    pygame.draw.rect(surface, CREAM, counter, border_radius=13)
    pygame.draw.rect(surface, DARK_GREEN, counter, 2, border_radius=13)
    draw_text(
        surface, f"MAP {idx + 1} / {total_maps}",
        SMALL_FONT, DARK_GREEN, counter.center
    )

    # ---- Back button ----
    back_rect = pygame.Rect(25, height - 60, 145, 42)
    back_hover = back_rect.collidepoint(mouse_position)
    pygame.draw.rect(
        surface, YELLOW if back_hover else DARK_GREEN,
        back_rect, border_radius=12
    )
    draw_text(
        surface, "BACK TO MENU",
        SMALL_FONT, DARK if back_hover else WHITE, back_rect.center
    )

    return {
        "card": card,
        "original_index": original_index,
        "left": left_rect,
        "right": right_rect,
        "play": action_rect,
        "back": back_rect,
        "total_maps": total_maps,
        "current_index": idx,
    }
