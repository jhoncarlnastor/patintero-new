import math
import pygame

# ==================================================
# PATINTERO: GRID RUSH - MAPS
# 6 maps. A new map unlocks every time you finish
# the previous one.
#
# Guard kinds:
#   "h"      patrols a horizontal line
#   "v"      patrols a vertical line (the "patotot")
#   "chaser" slowly follows the player
# ==================================================

CREAM = (255, 246, 218)
WHITE = (255, 255, 255)
BROWN = (120, 76, 45)
DARK = (35, 45, 40)
RED = (205, 58, 52)
YELLOW = (255, 205, 75)

GUARD_RED = (205, 58, 52)
GUARD_DARK = (175, 65, 45)
GUARD_PURPLE = (130, 70, 170)

# Terrain zones slow the player down.
ZONE_SLOW = 0.55

MAPS = [
    {
        "id": "plaza",
        "name": "BARANGAY PLAZA",
        "description": "Learn the basics of Patintero.",
        "difficulty": "EASY",
        "color": (90, 180, 100),
        "stars": 5,
        "spawn_every": 3.2,
        "line_color": (48, 100, 210),
        "guards": [
            {"kind": "h", "f": 0.50, "start": 0.20, "speed": 125, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.75, "start": 0.80, "speed": 160, "dir": -1, "color": GUARD_DARK},
        ],
        "zones": [],
    },
    {
        "id": "kalye",
        "name": "KALYE",
        "description": "Stay on the road!",
        "difficulty": "NORMAL",
        "color": (245, 180, 80),
        "stars": 6,
        "spawn_every": 3.4,
        "line_color": (250, 250, 250),
        "guards": [
            {"kind": "h", "f": 0.25, "start": 0.15, "speed": 150, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.50, "start": 0.85, "speed": 120, "dir": -1, "color": GUARD_DARK},
            {"kind": "h", "f": 0.75, "start": 0.30, "speed": 175, "dir": 1, "color": GUARD_RED},
        ],
        # No decorative puddles: keep the road clear for Patintero gameplay.
        "zones": [],
    },
    {
        "id": "court",
        "name": "BASKETBALL COURT",
        "description": "Fast guards and a patotot.",
        "difficulty": "NORMAL",
        "color": (230, 120, 55),
        "stars": 6,
        "spawn_every": 3.4,
        "line_color": (255, 255, 255),
        "guards": [
            {"kind": "h", "f": 0.25, "start": 0.20, "speed": 170, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.75, "start": 0.80, "speed": 170, "dir": -1, "color": GUARD_DARK},
            {"kind": "v", "f": 0.50, "start": 0.20, "speed": 120, "dir": 1, "color": GUARD_PURPLE},
        ],
        "zones": [],
    },
    {
        "id": "garahe",
        "name": "GARAHE",
        "description": "A wide garage driveway. Watch the guards!",
        "difficulty": "HARD",
        "color": (140, 145, 155),
        "stars": 7,
        "spawn_every": 3.6,
        "line_color": (255, 215, 60),
        "guards": [
            {"kind": "h", "f": 0.25, "start": 0.20, "speed": 160, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.50, "start": 0.80, "speed": 190, "dir": -1, "color": GUARD_DARK},
            {"kind": "v", "f": 0.33, "start": 0.30, "speed": 110, "dir": 1, "color": GUARD_PURPLE},
            {"kind": "v", "f": 0.67, "start": 0.70, "speed": 110, "dir": -1, "color": GUARD_PURPLE},
        ],
        # Remove the old oil-hole overlays from the garage floor.
        "zones": [],
    },
    {
        "id": "playground",
        "name": "PLAYGROUND",
        "description": "A chaser joins the game!",
        "difficulty": "HARD",
        "color": (90, 190, 215),
        "stars": 7,
        "spawn_every": 3.6,
        "line_color": (255, 255, 255),
        "guards": [
            {"kind": "h", "f": 0.25, "start": 0.20, "speed": 175, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.75, "start": 0.80, "speed": 175, "dir": -1, "color": GUARD_DARK},
            {"kind": "v", "f": 0.50, "start": 0.30, "speed": 140, "dir": 1, "color": GUARD_PURPLE},
            {"kind": "chaser", "sx": 0.08, "sy": 0.10, "speed": 55, "color": (60, 150, 130)},
        ],
        # Keep the playground floor clear; no sand obstacle overlays.
        "zones": [],
    },
    {
        "id": "lote",
        "name": "BAKANTENG LOTE",
        "description": "Tall grass, two chasers. Good luck!",
        "difficulty": "EXPERT",
        "color": (160, 120, 80),
        "stars": 8,
        "spawn_every": 3.8,
        "line_color": (245, 245, 235),
        "guards": [
            {"kind": "h", "f": 0.25, "start": 0.20, "speed": 190, "dir": 1, "color": GUARD_RED},
            {"kind": "h", "f": 0.50, "start": 0.80, "speed": 150, "dir": -1, "color": GUARD_DARK},
            {"kind": "h", "f": 0.75, "start": 0.40, "speed": 190, "dir": 1, "color": GUARD_RED},
            {"kind": "v", "f": 0.50, "start": 0.60, "speed": 130, "dir": -1, "color": GUARD_PURPLE},
            {"kind": "chaser", "sx": 0.08, "sy": 0.10, "speed": 62, "color": (60, 150, 130)},
            {"kind": "chaser", "sx": 0.92, "sy": 0.10, "speed": 62, "color": (60, 150, 130)},
        ],
        # Keep the lot's playable ground clear; no green grass obstacle overlays.
        "zones": [],
    },
]


# ==================================================
# SMALL DECORATION HELPERS
# ==================================================

def _house(surface, x, y, wall=CREAM, roof=RED):
    pygame.draw.rect(surface, wall, (x, y, 65, 42))
    pygame.draw.polygon(surface, roof, [(x - 7, y), (x + 32, y - 25), (x + 72, y)])
    pygame.draw.rect(surface, BROWN, (x + 27, y + 20, 13, 22))
    pygame.draw.rect(surface, (123, 205, 230), (x + 7, y + 9, 15, 13))
    pygame.draw.rect(surface, (123, 205, 230), (x + 46, y + 9, 12, 13))


def _tree(surface, x, y, scale=1.0, leaf=(50, 125, 60)):
    trunk_h = int(38 * scale)
    pygame.draw.rect(surface, BROWN, (x - 5, y, 10, trunk_h))
    pygame.draw.circle(surface, leaf, (x, y - 6), int(24 * scale))
    pygame.draw.circle(surface, leaf, (x - 15, y + 6), int(17 * scale))
    pygame.draw.circle(surface, leaf, (x + 15, y + 6), int(17 * scale))


def _building(surface, x, y, w, h, color):
    pygame.draw.rect(surface, color, (x, y, w, h))
    pygame.draw.rect(surface, DARK, (x, y, w, h), 2)
    for wx in range(x + 8, x + w - 14, 22):
        for wy in range(y + 10, y + h - 18, 26):
            pygame.draw.rect(surface, (255, 235, 150), (wx, wy, 12, 14))


def _pole(surface, x, y_top, y_bottom):
    pygame.draw.line(surface, (90, 70, 55), (x, y_top), (x, y_bottom), 6)
    pygame.draw.line(surface, (90, 70, 55), (x - 14, y_top + 10), (x + 14, y_top + 10), 4)


def _jeepney(surface, x, y):
    pygame.draw.rect(surface, (220, 60, 60), (x, y + 14, 150, 36), border_radius=8)
    pygame.draw.rect(surface, (250, 200, 60), (x, y + 30, 150, 8))
    pygame.draw.rect(surface, (80, 90, 105), (x + 50, y + 4, 80, 18), border_radius=4)
    for wx in range(x + 56, x + 124, 22):
        pygame.draw.rect(surface, (150, 210, 235), (wx, y + 7, 16, 12))
    pygame.draw.rect(surface, (150, 210, 235), (x + 8, y + 18, 26, 12))
    for wheel in (x + 28, x + 120):
        pygame.draw.circle(surface, DARK, (wheel, y + 52), 11)
        pygame.draw.circle(surface, (170, 170, 170), (wheel, y + 52), 5)


def _car_top_view(surface, x, y, color):
    pygame.draw.rect(surface, color, (x, y, 58, 118), border_radius=14)
    pygame.draw.rect(surface, (150, 210, 235), (x + 8, y + 22, 42, 20), border_radius=5)
    pygame.draw.rect(surface, (150, 210, 235), (x + 8, y + 74, 42, 18), border_radius=5)
    pygame.draw.rect(surface, DARK, (x, y, 58, 118), 2, border_radius=14)


def _hoop(surface, x, y, facing=1):
    pygame.draw.line(surface, (90, 90, 100), (x, y + 70), (x, y - 40), 7)
    board = pygame.Rect(0, 0, 10, 60)
    board.center = (x + facing * 14, y - 40)
    pygame.draw.rect(surface, WHITE, board)
    pygame.draw.rect(surface, RED, board, 2)
    pygame.draw.circle(surface, (235, 110, 40), (x + facing * 36, y - 22), 12, 3)
    pygame.draw.line(surface, WHITE, (x + facing * 28, y - 20), (x + facing * 36, y - 4), 1)
    pygame.draw.line(surface, WHITE, (x + facing * 44, y - 20), (x + facing * 36, y - 4), 1)


# ==================================================
# SCENERY (area outside the playing field)
# ==================================================

def _scenery_plaza(surface, field):
    width, height = surface.get_size()
    surface.fill((123, 205, 230))
    pygame.draw.ellipse(surface, (160, 205, 120), (-120, 95, 500, 200))
    pygame.draw.ellipse(surface, (110, 180, 100), (width - 420, 100, 520, 190))
    pygame.draw.rect(surface, (72, 145, 76), (0, 125, width, height - 125))
    _house(surface, 18, 75)
    _house(surface, width - 88, 78)
    _tree(surface, 45, 470, 0.9)
    _tree(surface, width - 45, 480, 0.9)


def _scenery_kalye(surface, field):
    width, height = surface.get_size()
    surface.fill((150, 205, 230))
    # Buildings and sari-sari store
    colors = [(235, 190, 120), (170, 200, 150), (225, 150, 140), (180, 175, 220)]
    x = 0
    for i, w in enumerate([115, 95, 125, 100, 110, 105, 120, 100, 110]):
        _building(surface, x, 34 + (i % 3) * 8, w, 100 - (i % 3) * 8, colors[i % 4])
        x += w
    pygame.draw.rect(surface, (210, 70, 60), (18, 90, 90, 22))
    sign_font = pygame.font.SysFont("arial", 13, bold=True)
    sign = sign_font.render("SARI-SARI", True, WHITE)
    surface.blit(sign, sign.get_rect(center=(63, 101)))
    # Wires and poles
    _pole(surface, 60, 40, 150)
    _pole(surface, width - 60, 40, 150)
    pygame.draw.line(surface, DARK, (60, 50), (width - 60, 50), 2)
    # Sidewalk and road
    pygame.draw.rect(surface, (185, 185, 180), (0, 134, width, 16))
    pygame.draw.rect(surface, (95, 98, 105), (0, 150, width, height - 150))
    pygame.draw.rect(surface, (185, 185, 180), (0, 565, width, height - 565))
    _jeepney(surface, 22, 570)
    _jeepney(surface, width - 175, 570)


def _scenery_court(surface, field):
    width, height = surface.get_size()
    surface.fill((135, 195, 225))
    # Fence
    pygame.draw.rect(surface, (95, 135, 95), (0, 120, width, height - 120))
    for fx in range(0, width, 24):
        pygame.draw.line(surface, (110, 115, 125), (fx, 60), (fx, 135), 1)
    for fy in range(60, 135, 20):
        pygame.draw.line(surface, (110, 115, 125), (0, fy), (width, fy), 1)
    for post in range(0, width + 1, 200):
        pygame.draw.line(surface, (70, 75, 85), (post, 55), (post, 140), 6)
    pygame.draw.rect(surface, (80, 85, 95), (0, 135, width, 15))
    # Court surround
    pygame.draw.rect(surface, (55, 90, 160), (0, 150, width, height - 150))
    _hoop(surface, 55, 330, 1)
    _hoop(surface, width - 55, 330, -1)
    # Bench
    pygame.draw.rect(surface, BROWN, (width // 2 - 70, 585, 140, 10))
    pygame.draw.rect(surface, BROWN, (width // 2 - 60, 595, 8, 14))
    pygame.draw.rect(surface, BROWN, (width // 2 + 52, 595, 8, 14))


def _scenery_garahe(surface, field):
    width, height = surface.get_size()
    surface.fill((120, 125, 135))
    # Back wall with roll-up door
    pygame.draw.rect(surface, (170, 160, 150), (0, 0, width, 150))
    door = pygame.Rect(width // 2 - 200, 25, 400, 115)
    pygame.draw.rect(surface, (195, 200, 210), door)
    for dy in range(door.top + 10, door.bottom, 14):
        pygame.draw.line(surface, (150, 155, 165), (door.left, dy), (door.right, dy), 2)
    pygame.draw.rect(surface, DARK, door, 3)
    # Shelf / tools on the left
    pygame.draw.rect(surface, BROWN, (20, 60, 90, 8))
    pygame.draw.rect(surface, BROWN, (20, 100, 90, 8))
    pygame.draw.rect(surface, (200, 60, 50), (30, 44, 18, 16))
    pygame.draw.rect(surface, (60, 110, 180), (60, 84, 22, 16))
    pygame.draw.rect(surface, (250, 200, 60), (28, 82, 16, 18))
    # Floor
    pygame.draw.rect(surface, (115, 118, 125), (0, 150, width, height - 150))
    _car_top_view(surface, 20, 250, (200, 60, 60))
    _car_top_view(surface, width - 78, 330, (60, 110, 190))
    # Tire stack
    for ty in (585, 570, 555):
        pygame.draw.ellipse(surface, (30, 30, 35), (width // 2 + 330, ty, 56, 20))
        pygame.draw.ellipse(surface, (80, 80, 90), (width // 2 + 345, ty + 5, 26, 9))


def _scenery_playground(surface, field):
    width, height = surface.get_size()
    surface.fill((140, 210, 235))
    pygame.draw.rect(surface, (95, 175, 90), (0, 120, width, height - 120))
    # Swing set (top)
    base_x = 300
    pygame.draw.line(surface, (200, 70, 60), (base_x, 40), (base_x + 40, 135), 6)
    pygame.draw.line(surface, (200, 70, 60), (base_x + 240, 40), (base_x + 200, 135), 6)
    pygame.draw.line(surface, (200, 70, 60), (base_x, 40), (base_x + 240, 40), 6)
    for sx in (base_x + 70, base_x + 170):
        pygame.draw.line(surface, DARK, (sx, 42), (sx, 105), 2)
        pygame.draw.rect(surface, (250, 200, 60), (sx - 14, 105, 28, 7))
    # Slide (top right)
    pygame.draw.rect(surface, (60, 110, 190), (760, 50, 34, 8))
    pygame.draw.line(surface, (60, 110, 190), (766, 50), (766, 138), 5)
    pygame.draw.line(surface, (60, 110, 190), (790, 50), (790, 138), 5)
    pygame.draw.polygon(surface, (250, 200, 60), [(794, 54), (800, 54), (900, 135), (885, 135)])
    # Trees
    _tree(surface, 60, 55, 0.9)
    _tree(surface, width - 40, 465, 0.9)
    # Seesaw (left)
    pygame.draw.polygon(surface, (90, 90, 100), [(45, 345), (65, 345), (55, 320)])
    pygame.draw.line(surface, (230, 100, 70), (10, 332), (90, 308), 8)
    # Merry-go-round (right)
    pygame.draw.circle(surface, (230, 100, 70), (width - 50, 330), 34)
    pygame.draw.circle(surface, (250, 200, 60), (width - 50, 330), 34, 4)
    for angle in (0, 60, 120):
        rad = math.radians(angle)
        dx, dy = int(34 * math.cos(rad)), int(34 * math.sin(rad))
        pygame.draw.line(surface, (250, 200, 60), (width - 50 - dx, 330 - dy), (width - 50 + dx, 330 + dy), 3)
    # Ground below
    pygame.draw.rect(surface, (95, 175, 90), (0, 550, width, height - 550))


def _scenery_lote(surface, field):
    image_path = "assets/maps/bakanteng_lote.png"

    try:
        background = pygame.image.load(image_path).convert()
        background = pygame.transform.smoothscale(
            background,
            (field.width, field.height),
        )
        surface.blit(background, field.topleft)

    except (pygame.error, FileNotFoundError) as error:
        print(f"Could not load Bakanteng Lote map: {error}")
SCENERY = {
    "plaza": _scenery_plaza,
    "kalye": _scenery_kalye,
    "court": _scenery_court,
    "garahe": _scenery_garahe,
    "playground": _scenery_playground,
    "lote": _scenery_lote,
}


# ==================================================
# PLAYING FIELD SURFACES
# ==================================================

FIELD_STYLE = {
    "plaza": {"floor": CREAM, "border": (48, 100, 210), "dots": (230, 218, 185)},
    "kalye": {"floor": (78, 80, 88), "border": (250, 205, 60), "dots": (95, 98, 105)},
    "court": {"floor": (222, 140, 70), "border": (255, 255, 255), "dots": (205, 125, 60)},
    "garahe": {"floor": (160, 162, 168), "border": (255, 215, 60), "dots": (145, 147, 153)},
    "playground": {"floor": (240, 205, 130), "border": (150, 70, 190), "dots": (225, 190, 115)},
    "lote": {"floor": (158, 128, 92), "border": (245, 245, 235), "dots": (140, 112, 80)},
}


def _field_details(surface, map_def, field):
    map_id = map_def["id"]

    if map_id == "court":
        # Painted key areas and center circle
        key_h = field.height // 2
        for side in (field.left, field.right - 130):
            key = pygame.Rect(side, field.centery - key_h // 2, 130, key_h)
            pygame.draw.rect(surface, (65, 105, 185), key)
            pygame.draw.rect(surface, WHITE, key, 3)
        pygame.draw.circle(surface, WHITE, field.center, 62, 3)

    elif map_id == "kalye":
        # Dashed road markings between lanes
        for y in (field.top + field.height // 8, field.bottom - field.height // 8):
            for x in range(field.left + 20, field.right - 40, 70):
                pygame.draw.line(surface, (240, 220, 90), (x, y), (x + 35, y), 4)

    elif map_id == "garahe":
        # Parking bay lines
        for x in range(field.left + 80, field.right, 160):
            pygame.draw.line(surface, (255, 255, 255), (x, field.top + 4), (x, field.top + 40), 3)
            pygame.draw.line(surface, (255, 255, 255), (x, field.bottom - 40), (x, field.bottom - 4), 3)

    elif map_id == "playground":
        # Colorful rubber tiles
        tile = 80
        for ix, x in enumerate(range(field.left, field.right, tile)):
            for iy, y in enumerate(range(field.top, field.bottom, tile)):
                if (ix + iy) % 2 == 0:
                    pygame.draw.rect(surface, (232, 190, 115), (x, y, tile, tile))

    elif map_id == "lote":
        # Weeds and pebbles
        for i in range(34):
            x = field.left + 18 + (i * 97) % (field.width - 36)
            y = field.top + 14 + (i * 61) % (field.height - 28)
            pygame.draw.line(surface, (95, 125, 65), (x, y + 8), (x - 3, y), 2)
            pygame.draw.line(surface, (110, 140, 70), (x, y + 8), (x + 4, y + 1), 2)
        for i in range(10):
            x = field.left + 40 + (i * 151) % (field.width - 80)
            y = field.top + 30 + (i * 83) % (field.height - 60)
            pygame.draw.circle(surface, (130, 120, 108), (x, y), 4)


def zone_rect(field, zone):
    return pygame.Rect(
        int(field.left + zone["fx"] * field.width),
        int(field.top + zone["fy"] * field.height),
        int(zone["fw"] * field.width),
        int(zone["fh"] * field.height),
    )


def _draw_zone(surface, rect, kind):
    if kind == "puddle":
        pygame.draw.ellipse(surface, (95, 150, 205), rect)
        pygame.draw.ellipse(surface, (150, 200, 235), rect.inflate(-24, -16))
        pygame.draw.ellipse(surface, (210, 235, 250), rect, 2)
    elif kind == "oil":
        pygame.draw.ellipse(surface, (35, 35, 45), rect)
        pygame.draw.ellipse(surface, (70, 60, 110), rect.inflate(-26, -18))
        pygame.draw.ellipse(surface, (70, 150, 130), rect.inflate(-50, -34))
    elif kind == "sand":
        pygame.draw.ellipse(surface, (225, 195, 130), rect)
        pygame.draw.ellipse(surface, (240, 215, 155), rect.inflate(-22, -14))
        for i in range(10):
            x = rect.left + 14 + (i * 37) % max(1, rect.width - 28)
            y = rect.top + 10 + (i * 23) % max(1, rect.height - 20)
            pygame.draw.circle(surface, (200, 170, 110), (x, y), 2)
    elif kind == "grass":
        pygame.draw.ellipse(surface, (80, 125, 60), rect)
        for i in range(14):
            x = rect.left + 12 + (i * 29) % max(1, rect.width - 24)
            y = rect.top + 12 + (i * 17) % max(1, rect.height - 18)
            pygame.draw.line(surface, (60, 105, 45), (x, y + 10), (x - 3, y), 3)
            pygame.draw.line(surface, (110, 160, 75), (x, y + 10), (x + 4, y + 1), 3)






def background_rect(width, height, map_id=None):
    """Rectangle where map background artwork is displayed."""

    # Same alignment, different size tuning
    MAP_POSITIONS = {
        "kalye":      (40, 70, width - 80, height - 120),
        "court":      (40, 70, width - 80, height - 120),
        "garahe":     (40, 70, width - 80, height - 120),
        "playground": (40, 70, width - 80, height - 120),
        "plaza":      (40, 70, width - 80, height - 120),
        "lote":       (40, 80, width - 80, height - 120),
    }

    x, y, w, h = MAP_POSITIONS.get(
        map_id,
        (40, 70, width - 80, height - 120)
    )

    return pygame.Rect(x, y, w, h)


# Load each background once, then reuse the scaled surface during gameplay.
_BACKGROUND_CACHE = {}


MAP_BACKGROUND_FILES = {
    "plaza": "assets/maps/barangay_plaza.jpg",
    "kalye": "assets/maps/kalye.png",
    "court": "assets/maps/basketball.png",
    "garahe": "assets/maps/garahe.png",
    "playground": "assets/maps/playground.png",
    "lote": "assets/maps/bakanteng_lote.png",
}


def _get_background(map_id, size):
    key = (map_id, size)
    if key not in _BACKGROUND_CACHE:
        image_path = MAP_BACKGROUND_FILES[map_id]
        image = pygame.image.load(image_path).convert()
        _BACKGROUND_CACHE[key] = pygame.transform.smoothscale(image, size)
    return _BACKGROUND_CACHE[key]


def get_playing_field(width, height, map_id):
    """Return the playable area aligned to the open ground in each map image."""
    bg = background_rect(width, height, map_id)

    # Fractions are measured against the displayed background image.
    # They are deliberately inset from houses, sidewalks and decorations.
    bounds = {
        "plaza":      (0.055, 0.18, 0.89, 0.68),
        # Stretch the playing area vertically from gutter to gutter while
        # keeping its full width on the asphalt road only.
        "kalye":      (0.015, 0.245, 0.970, 0.50),
        # Match the full orange court, including its top and bottom edges.
        "court":      (0.095, 0.215, 0.81, 0.69),
        # Use a wider garage driveway area while staying clear of the
        # garage roofs, side houses, and bottom fence.
        "garahe":     (0.10, 0.22, 0.80, 0.58),
        "playground": (0.13, 0.18, 0.74, 0.68),
        "lote":       (0.15, 0.16, 0.70, 0.68),
    }

    if map_id not in bounds:
        return bg

    fx, fy, fw, fh = bounds[map_id]
    return pygame.Rect(
        bg.left + int(bg.width * fx),
        bg.top + int(bg.height * fy),
        int(bg.width * fw),
        int(bg.height * fh),
    )


def _draw_image_map(surface, map_def, field, bg):
    """Draw a supplied map image, then keep the Patintero grid on its open area."""
    map_id = map_def["id"]
    style = FIELD_STYLE[map_id]

    surface.fill((35, 55, 70))
    try:
        surface.blit(_get_background(map_id, bg.size), bg.topleft)
    except (pygame.error, OSError, FileNotFoundError) as error:
        print(f"Could not load {map_id} background: {error}")
        pygame.draw.rect(surface, style["floor"], bg)

    line_color = map_def["line_color"]
    border_color = style["border"]

    pygame.draw.rect(surface, border_color, field, width=5)

    for i in range(1, 4):
        y = field.top + i * field.height // 4
        pygame.draw.line(
            surface, line_color,
            (field.left, y), (field.right, y), 4,
        )

    pygame.draw.line(
        surface, line_color,
        (field.centerx, field.top),
        (field.centerx, field.bottom),
        4,
    )

    for zone in map_def["zones"]:
        _draw_zone(surface, zone_rect(field, zone), zone["kind"])


def draw_map_background(surface, map_def, field):
    map_id = map_def["id"]
    style = FIELD_STYLE[map_id]

    # All supplied map images use the same display area. The playable field
    # is calculated separately so grid lines never cover surrounding scenery.
    if map_id in MAP_BACKGROUND_FILES:
        bg = background_rect(*surface.get_size(), map_id)
        _draw_image_map(surface, map_def, field, bg)
        return

    # Keep the original procedural rendering for any map without an image.
    SCENERY[map_id](surface, field)
    pygame.draw.rect(surface, style["floor"], field)
    _field_details(surface, map_def, field)

    line_color = map_def["line_color"]
    pygame.draw.rect(surface, style["border"], field, width=5)

    for i in range(1, 4):
        y = field.top + i * field.height // 4
        pygame.draw.line(
            surface, line_color,
            (field.left, y), (field.right, y), 4,
        )

    pygame.draw.line(
        surface, line_color,
        (field.centerx, field.top),
        (field.centerx, field.bottom),
        4,
    )

    for zone in map_def["zones"]:
        _draw_zone(surface, zone_rect(field, zone), zone["kind"])
