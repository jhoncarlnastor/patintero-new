import random
import pygame

# ==================================================
# Themed surroundings for the game screen.
# Built once per map, then reused every frame.
# Uses map_def["id"] and map_def["color"] (both already
# used by level_map.py).
# ==================================================

CURB = (200, 195, 180)
ASPHALT = (58, 60, 66)
CHALK = (225, 225, 215)

_CACHE = {}


def _mix(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))


def _build(size, field, map_def):
    w, h = size
    rng = random.Random(sum(ord(c) for c in str(map_def.get("id", "map"))))

    accent = map_def.get("color", (60, 110, 170))
    base = _mix(accent, (72, 74, 82), 0.6)

    s = pygame.Surface(size)
    s.fill(base)

    # ---------- Concrete slabs ----------
    grout = _mix(base, (0, 0, 0), 0.22)
    light = _mix(base, (255, 255, 255), 0.07)
    slab = 60

    for row, y in enumerate(range(0, h, slab)):
        pygame.draw.line(s, grout, (0, y), (w, y), 2)
        offset = (row % 2) * (slab // 2)

        for x in range(offset, w, slab):
            pygame.draw.line(s, grout, (x, y), (x, y + slab), 2)

    for _ in range(700):
        px, py = rng.randint(0, w - 1), rng.randint(0, h - 1)
        s.set_at((px, py), light if rng.random() < 0.5 else grout)

    # Hairline cracks
    for _ in range(7):
        x, y = rng.randint(20, w - 20), rng.randint(160, h - 20)
        points = [(x, y)]

        for _ in range(5):
            x += rng.randint(-14, 14)
            y += rng.randint(4, 14)
            points.append((x, y))

        pygame.draw.lines(s, grout, False, points, 1)

    # ---------- Brick wall at the top ----------
    wall_h = 150
    wall = _mix(accent, (40, 40, 50), 0.55)
    mortar = _mix(wall, (255, 255, 255), 0.16)

    pygame.draw.rect(s, wall, (0, 0, w, wall_h))

    for row, y in enumerate(range(0, wall_h, 16)):
        pygame.draw.line(s, mortar, (0, y), (w, y), 1)
        offset = (row % 2) * 20

        for x in range(offset, w, 40):
            pygame.draw.line(s, mortar, (x, y), (x, y + 16), 1)

    pygame.draw.rect(s, CURB, (0, wall_h, w, 8))

    for i in range(12):
        shade = _mix(base, (0, 0, 0), 0.4 * (1 - i / 12))
        pygame.draw.line(s, shade, (0, wall_h + 8 + i), (w, wall_h + 8 + i))

    # ---------- Curb and street at the bottom ----------
    curb_y = field.bottom + 10
    pygame.draw.rect(s, CURB, (0, curb_y, w, 10))
    pygame.draw.rect(s, (150, 146, 134), (0, curb_y + 8, w, 3))
    pygame.draw.rect(s, ASPHALT, (0, curb_y + 11, w, h - curb_y - 11))

    street_mid = curb_y + 11 + (h - curb_y - 11) // 2

    for x in range(24, w, 76):
        pygame.draw.rect(s, CHALK, (x, street_mid - 3, 38, 6))

    # ---------- Soft shadow + frame around the field ----------
    shadow = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(
        shadow, (0, 0, 0, 110),
        field.inflate(36, 36).move(0, 6), border_radius=14,
    )
    s.blit(shadow, (0, 0))

    pygame.draw.rect(s, (198, 192, 172), field.inflate(18, 18), border_radius=8)
    pygame.draw.rect(s, (70, 56, 40), field.inflate(8, 8), width=3)

    # ---------- Vignette ----------
    vignette = pygame.Surface(size, pygame.SRCALPHA)
    steps, ring = 36, 4

    for i in range(steps):
        alpha = int(130 * (1 - i / steps) ** 2.2)
        rect = pygame.Rect(i * ring, i * ring, w - 2 * i * ring, h - 2 * i * ring)
        pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, ring)

    s.blit(vignette, (0, 0))

    return s


def draw_surroundings(surface, state):
    """Draw this before draw_map_background()."""
    key = (state["map"].get("id", "map"), surface.get_size())

    if key not in _CACHE:
        _CACHE[key] = _build(surface.get_size(), state["field"], state["map"])

    surface.blit(_CACHE[key], (0, 0))