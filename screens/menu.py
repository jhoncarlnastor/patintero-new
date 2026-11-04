import math
import random
import os
import pygame

# ==================================================
# PATINTERO: GRID RUSH - Larong Kalye main menu
# Same API as before: init_menu_fonts(), draw_menu()
# Extra: draw_coin_pill() for the rare coin counter
# ==================================================

# Palette
SKY = (123, 205, 230)
GREEN = (55, 145, 76)
DARK_GREEN = (30, 105, 57)
SUN_YELLOW = (255, 205, 75)
CREAM = (255, 246, 218)
BROWN = (120, 76, 45)
WHITE = (255, 255, 255)
DARK = (35, 65, 54)

WOOD = (170, 112, 64)
WOOD_DARK = (106, 66, 36)
ASPHALT = (68, 70, 78)
SIDEWALK = (176, 172, 160)
CURB = (208, 203, 190)
CHALK = (232, 232, 222)

# Jeepney colors
J_RED = (214, 60, 52)
J_BLUE = (47, 110, 190)
J_GREEN = (40, 150, 90)
J_ORANGE = (236, 138, 36)

TITLE_FONT = None
SUBTITLE_FONT = None
BUTTON_FONT = None
SIGN_FONT = None

_bg_cache = {}
_title_cache = {}


def init_menu_fonts():
    """Initialize fonts after pygame.init()."""
    global TITLE_FONT, SUBTITLE_FONT, BUTTON_FONT, SIGN_FONT

    TITLE_FONT = pygame.font.SysFont("arial", 52, bold=True)
    SUBTITLE_FONT = pygame.font.SysFont("arial", 21)
    BUTTON_FONT = pygame.font.SysFont("arial", 23, bold=True)
    SIGN_FONT = pygame.font.SysFont("arial", 15, bold=True)


# ==================================================
# SMALL HELPERS
# ==================================================

def _mix(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))


def draw_text(surface, text, font, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_shadow_text(surface, text, font, color, center, offset=2):
    shadow = font.render(text, True, (20, 20, 20))
    image = font.render(text, True, color)
    rect = image.get_rect(center=center)
    surface.blit(shadow, rect.move(offset, offset))
    surface.blit(image, rect)


def draw_outlined_text(surface, text, font, color, outline, center, thickness=3):
    base = font.render(text, True, color)
    edge = font.render(text, True, outline)
    rect = base.get_rect(center=center)

    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if (dx or dy) and dx * dx + dy * dy <= thickness * thickness + 1:
                surface.blit(edge, rect.move(dx, dy))

    surface.blit(base, rect)


def draw_tansan(surface, cx, cy, radius, inner_color, spin=0.0):
    """Bottle cap with serrated edge."""
    points = []
    teeth = 12

    for i in range(teeth * 2):
        angle = spin + i * math.pi / teeth
        r = radius if i % 2 == 0 else radius - 3
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

    pygame.draw.polygon(surface, (215, 215, 222), points)
    pygame.draw.polygon(surface, (120, 120, 130), points, 1)
    pygame.draw.circle(surface, inner_color, (cx, cy), radius - 5)
    pygame.draw.circle(
        surface, _mix(inner_color, WHITE, 0.45),
        (cx - 3, cy - 3), max(2, radius // 5)
    )


# ==================================================
# STATIC BACKGROUND (built once, then reused)
# ==================================================

def _draw_sari_sari_store(s, x, y, w, h):
    # Body
    pygame.draw.rect(s, CREAM, (x, y, w, h))
    pygame.draw.rect(s, (200, 185, 150), (x, y, w, h), 3)

    # Roof (yero)
    roof = pygame.Rect(x - 10, y - 20, w + 20, 22)
    pygame.draw.rect(s, (150, 62, 48), roof)
    for rx in range(roof.x + 6, roof.right, 10):
        pygame.draw.line(s, (120, 46, 36), (rx, roof.y), (rx, roof.bottom), 2)

    # Signboard
    sign = pygame.Rect(x + 22, y + 6, w - 44, 26)
    pygame.draw.rect(s, J_RED, sign, border_radius=6)
    pygame.draw.rect(s, WOOD_DARK, sign, 3, border_radius=6)
    draw_text(s, "SARI-SARI", SIGN_FONT, SUN_YELLOW, sign.center)

    # Awning stripes
    awning_top = y + 38
    stripe = 20
    for i, ax in enumerate(range(x + 8, x + w - 8, stripe)):
        color = J_RED if i % 2 == 0 else WHITE
        pygame.draw.rect(
            s, color, (ax, awning_top, min(stripe, x + w - 8 - ax), 14)
        )

    # Shop window with products
    window = pygame.Rect(x + 12, awning_top + 14, w - 24, 34)
    pygame.draw.rect(s, (88, 58, 42), window)
    rng = random.Random(7)
    palette = [J_RED, SUN_YELLOW, J_BLUE, J_GREEN, J_ORANGE, WHITE]
    for px in range(window.x + 5, window.right - 12, 14):
        pygame.draw.rect(s, rng.choice(palette), (px, window.y + 5, 9, 12))
        pygame.draw.rect(s, rng.choice(palette), (px, window.y + 20, 9, 10))

    # Counter
    pygame.draw.rect(s, WOOD, (x + 8, window.bottom, w - 16, 7))
    pygame.draw.rect(s, WOOD_DARK, (x + 8, window.bottom, w - 16, 7), 2)


def _draw_concrete_house(s, x, y, w, h):
    pygame.draw.rect(s, (236, 190, 128), (x, y, w, h))
    pygame.draw.rect(s, (190, 150, 100), (x, y, w, h), 3)

    # Flat roof slab
    pygame.draw.rect(s, (150, 150, 155), (x - 8, y - 12, w + 16, 14))

    # Door
    pygame.draw.rect(s, J_BLUE, (x + 22, y + 40, 36, h - 40))
    pygame.draw.circle(s, SUN_YELLOW, (x + 50, y + 72), 3)

    # Window with grills
    win = pygame.Rect(x + 90, y + 24, 56, 42)
    pygame.draw.rect(s, SKY, win)
    for gx in range(win.x + 14, win.right, 14):
        pygame.draw.line(s, (60, 60, 65), (gx, win.y), (gx, win.bottom), 2)
    pygame.draw.line(
        s, (60, 60, 65), (win.x, win.centery), (win.right, win.centery), 2
    )
    pygame.draw.rect(s, (60, 60, 65), win, 3)


def _draw_poste(s, x, top, ground):
    pygame.draw.rect(s, (112, 88, 66), (x - 4, top, 8, ground - top))
    pygame.draw.rect(s, (112, 88, 66), (x - 28, top + 6, 56, 6))
    pygame.draw.rect(s, (80, 62, 46), (x - 4, top, 8, ground - top), 1)


def _draw_piko(s, cx, bottom, size):
    chalk_font = SIGN_FONT
    rows = [1, 1, 2, 1, 2]
    number = 1

    for i, count in enumerate(rows):
        top = bottom - (i + 1) * size

        if count == 1:
            rects = [pygame.Rect(cx - size // 2, top, size, size)]
        else:
            rects = [
                pygame.Rect(cx - size, top, size, size),
                pygame.Rect(cx, top, size, size),
            ]

        for rect in rects:
            pygame.draw.rect(s, CHALK, rect, 2)
            draw_text(s, str(number), chalk_font, CHALK, rect.center)
            number += 1

    top_y = bottom - len(rows) * size
    pygame.draw.arc(
        s, CHALK, (cx - size, top_y - size, size * 2, size * 2), 0, math.pi, 2
    )


def _draw_patintero_court(s, x, y, w, h):
    pygame.draw.rect(s, CHALK, (x, y, w, h), 2)
    pygame.draw.line(s, CHALK, (x + w // 2, y), (x + w // 2, y + h), 2)

    for i in (1, 2):
        ly = y + i * h // 3
        pygame.draw.line(s, CHALK, (x, ly), (x + w, ly), 2)


def _build_background(width, height):
    s = pygame.Surface((width, height))
    s.fill(SKY)

    # Sun
    pygame.draw.circle(s, SUN_YELLOW, (width - 100, 85), 42)

    # Hills
    pygame.draw.ellipse(s, (105, 180, 112), (-100, 250, 650, 300))
    pygame.draw.ellipse(s, GREEN, (350, 280, 800, 300))
    pygame.draw.rect(s, (77, 160, 77), (0, 405, width, 50))

    # Buildings
    _draw_sari_sari_store(s, 40, 335, 190, 105)
    _draw_concrete_house(s, width - 235, 340, 190, 100)

    # Poste + kable
    left_x, right_x = 300, width - 285
    _draw_poste(s, left_x, 285, 442)
    _draw_poste(s, right_x, 285, 442)

    for base in (296, 304):
        span = right_x - left_x
        pts = [
            (x, base + 26 * math.sin(math.pi * (x - left_x) / span))
            for x in range(left_x, right_x + 1, 8)
        ]
        pygame.draw.lines(s, (40, 40, 44), False, pts, 2)

    # Bangketa + gilid
    pygame.draw.rect(s, SIDEWALK, (0, 440, width, 30))
    for jx in range(0, width, 80):
        pygame.draw.line(s, (150, 146, 136), (jx, 440), (jx, 470), 2)
    pygame.draw.rect(s, CURB, (0, 468, width, 8))

    # Kalsada
    pygame.draw.rect(s, ASPHALT, (0, 476, width, height - 476))
    rng = random.Random(3)
    for _ in range(170):
        px = rng.randint(0, width - 1)
        py = rng.randint(480, height - 1)
        s.set_at((px, py), (86, 88, 96))
        s.set_at((px + 1, py), (58, 60, 66))

    # Center dashes
    for dx in range(230, 780, 64):
        pygame.draw.rect(s, (240, 240, 235), (dx, 566, 38, 6))

    # Chalk games
    _draw_piko(s, 120, 638, 26)
    _draw_patintero_court(s, 820, 500, 140, 128)

    return s


def _get_background(surface):
    size = surface.get_size()

    if size not in _bg_cache:
        bg_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "background1.png",
        )
        bg_loaded = False
        try:
            if os.path.isfile(bg_path):
                img = pygame.image.load(bg_path).convert()
                _bg_cache[size] = pygame.transform.smoothscale(img, size)
                bg_loaded = True
        except (pygame.error, OSError) as e:
            print(f"Could not load assets/background1.png: {e}")

        if not bg_loaded:
            _bg_cache[size] = _build_background(*size)

    return _bg_cache[size]


# ==================================================
# TITLE SIGNBOARD (built once)
# ==================================================

def _build_title_board():
    pad_x, pad_top, pad_bottom = 20, 40, 20
    board_w, board_h = 600, 190

    surf = pygame.Surface(
        (board_w + pad_x * 2, board_h + pad_top + pad_bottom), pygame.SRCALPHA
    )
    board = pygame.Rect(pad_x, pad_top, board_w, board_h)

    # Hanging ropes
    for rx in (board.x + 90, board.right - 90):
        pygame.draw.line(surf, (205, 175, 115), (rx, 0), (rx, board.y + 6), 4)

    # Drop shadow
    shadow = pygame.Rect(board.x + 6, board.y + 9, board_w, board_h)
    pygame.draw.rect(surf, (0, 0, 0, 80), shadow, border_radius=12)

    # Wooden planks
    pygame.draw.rect(surf, WOOD, board, border_radius=12)
    rng = random.Random(11)

    for i in range(1, 4):
        py = board.y + i * board_h // 4
        pygame.draw.line(surf, WOOD_DARK, (board.x + 4, py), (board.right - 4, py), 2)

    for _ in range(40):
        gx = rng.randint(board.x + 12, board.right - 40)
        gy = rng.randint(board.y + 8, board.bottom - 8)
        pygame.draw.line(
            surf, _mix(WOOD, WOOD_DARK, 0.5), (gx, gy), (gx + rng.randint(12, 34), gy), 1
        )

    pygame.draw.rect(surf, WOOD_DARK, board, 6, border_radius=12)

    # Nails
    for nx, ny in [
        (board.x + 18, board.y + 18),
        (board.right - 18, board.y + 18),
        (board.x + 18, board.bottom - 18),
        (board.right - 18, board.bottom - 18),
    ]:
        pygame.draw.circle(surf, (90, 90, 96), (nx, ny), 5)
        pygame.draw.circle(surf, (190, 190, 196), (nx - 1, ny - 1), 2)

    # Title text
    cx = board.centerx
    draw_outlined_text(
        surf, "PATINTERO", TITLE_FONT, SUN_YELLOW, (80, 36, 18),
        (cx, board.y + 44), 3
    )
    draw_outlined_text(
        surf, "GRID RUSH", TITLE_FONT, (232, 66, 54), CREAM,
        (cx, board.y + 98), 3
    )

    # Subtitle ribbon
    ribbon = pygame.Rect(0, 0, 390, 32)
    ribbon.center = (cx, board.y + 152)
    pygame.draw.rect(surf, (70, 44, 28), ribbon, border_radius=9)
    pygame.draw.rect(surf, SUN_YELLOW, ribbon, 2, border_radius=9)
    draw_text(
        surf, "A Filipino Street Game Adventure",
        SUBTITLE_FONT, CREAM, ribbon.center
    )

    return pygame.transform.rotozoom(surf, 1.2, 1.0)


def _get_title_board():
    if "board" not in _title_cache:
        _title_cache["board"] = _build_title_board()

    return _title_cache["board"]


# ==================================================
# ANIMATED DECORATIONS
# ==================================================

def draw_clouds(surface, t):
    width = surface.get_width()
    clouds = [(60, 105, 1.0, 14), (430, 62, 0.8, 9), (720, 150, 1.2, 17)]

    for x0, y, sc, speed in clouds:
        x = (x0 + t * speed) % (width + 240) - 120
        color = (250, 252, 255)

        for ox, oy, ew, eh in [
            (0, 0, 80, 30), (22, -14, 54, 36), (-18, 4, 46, 24), (44, 2, 52, 26)
        ]:
            rect = pygame.Rect(0, 0, int(ew * sc), int(eh * sc))
            rect.center = (int(x + ox * sc), int(y + oy * sc))
            pygame.draw.ellipse(surface, color, rect)


def draw_kite(surface, t):
    cx = 105 + 8 * math.sin(t * 1.3)
    cy = 160 + 9 * math.sin(t * 1.9)
    cx, cy = int(cx), int(cy)

    top, right = (cx, cy - 28), (cx + 18, cy)
    bottom, left = (cx, cy + 34), (cx - 18, cy)

    pygame.draw.polygon(surface, J_RED, [top, right, (cx, cy)])
    pygame.draw.polygon(surface, SUN_YELLOW, [top, left, (cx, cy)])
    pygame.draw.polygon(surface, J_BLUE, [(cx, cy), right, bottom])
    pygame.draw.polygon(surface, J_GREEN, [(cx, cy), left, bottom])
    pygame.draw.polygon(surface, (50, 40, 30), [top, right, bottom, left], 2)

    # Tail with bows
    tail = []
    for i in range(7):
        ty = bottom[1] + i * 10
        tx = cx + 7 * math.sin(t * 3 + i * 0.9)
        tail.append((tx, ty))

    pygame.draw.lines(surface, (60, 45, 35), False, [bottom] + tail, 2)

    for i, (tx, ty) in enumerate(tail[1::2]):
        pygame.draw.circle(
            surface, [J_RED, SUN_YELLOW, J_BLUE][i % 3], (int(tx), int(ty)), 4
        )


def draw_banderitas(surface, t):
    width = surface.get_width()
    colors = [J_RED, SUN_YELLOW, J_BLUE, J_GREEN, J_ORANGE]
    sag = 26

    def rope_y(x):
        return 4 + sag * math.sin(math.pi * x / width)

    pts = [(x, rope_y(x)) for x in range(0, width + 1, 10)]
    pygame.draw.lines(surface, (80, 55, 40), False, pts, 2)

    for i, x in enumerate(range(22, width, 44)):
        sway = math.sin(t * 2.2 + i * 0.7) * 4
        left_y, right_y = rope_y(x - 15), rope_y(x + 15)
        mid_y = rope_y(x)

        pygame.draw.polygon(
            surface, colors[i % len(colors)],
            [(x - 15, left_y), (x + 15, right_y), (x + sway, mid_y + 34)]
        )


# ==================================================
# UI PIECES
# ==================================================

def draw_button(surface, text, rect, hovered=False, color=J_RED, t=0.0):
    body = rect.inflate(12, 6) if hovered else rect.copy()
    body.y -= 4 if hovered else 0

    fill = _mix(color, WHITE, 0.18) if hovered else color

    # Shadow + dark outline
    pygame.draw.rect(surface, (30, 34, 38), body.move(0, 6), border_radius=16)
    pygame.draw.rect(surface, (40, 28, 20), body.inflate(6, 6), border_radius=18)

    # Body, highlight and cream border
    pygame.draw.rect(surface, fill, body, border_radius=14)
    highlight = pygame.Rect(body.x + 8, body.y + 5, body.w - 16, body.h // 3)
    pygame.draw.rect(
        surface, _mix(fill, WHITE, 0.25), highlight, border_radius=10
    )
    pygame.draw.rect(surface, CREAM, body, width=3, border_radius=14)

    # Tansan icon (spins on hover)
    spin = t * 4 if hovered else 0.0
    draw_tansan(
        surface, body.x + 34, body.centery, 15, _mix(color, (40, 20, 10), 0.25), spin
    )

    draw_shadow_text(
        surface, text, BUTTON_FONT, WHITE, (body.centerx + 14, body.centery)
    )


def draw_coin_pill(surface, amount):
    """Wooden pill for the rare coin counter.

    Draw the coin icon on top of it at (42, 35) from main.py.
    """
    pill = pygame.Rect(20, 18, 140, 34)

    pygame.draw.rect(surface, (30, 34, 38), pill.move(0, 3), border_radius=17)
    pygame.draw.rect(surface, WOOD, pill, border_radius=17)
    pygame.draw.rect(surface, WOOD_DARK, pill, width=3, border_radius=17)

    draw_shadow_text(
        surface, str(amount), BUTTON_FONT, CREAM, (105, 35), offset=2
    )


# ==================================================
# MAIN MENU
# ==================================================

def draw_menu(surface, mouse_position):
    t = pygame.time.get_ticks() / 1000
    width, height = surface.get_size()

    surface.blit(_get_background(surface), (0, 0))

    draw_clouds(surface, t)
    draw_kite(surface, t)
    draw_banderitas(surface, t)

    board = _get_title_board()
    surface.blit(board, board.get_rect(center=(width // 2, 120)))

    button_width = 300
    button_height = 52
    start_x = width // 2 - button_width // 2

    buttons = {
        "play": pygame.Rect(start_x, 255, button_width, button_height),
        "map": pygame.Rect(start_x, 322, button_width, button_height),
        "how_to_play": pygame.Rect(start_x, 389, button_width, button_height),
        "quit": pygame.Rect(start_x, 456, button_width, button_height),
    }

    labels = {
        "play": "PLAY GAME",
        "map": "WORLD MAP",
        "how_to_play": "HOW TO PLAY",
        "quit": "EXIT GAME",
    }

    colors = {
        "play": J_RED,
        "map": J_BLUE,
        "how_to_play": J_GREEN,
        "quit": J_ORANGE,
    }

    for name, rect in buttons.items():
        draw_button(
            surface,
            labels[name],
            rect,
            rect.collidepoint(mouse_position),
            colors[name],
            t,
        )

    # Chalk-style footer on the road
    draw_shadow_text(
        surface,
        "CELEBRATING FILIPINO STREET GAMES",
        SUBTITLE_FONT,
        CHALK,
        (width // 2, 603),
        offset=2,
    )

    return buttons

def draw_mode_select(surface, mouse_position):
    """Draw the mode selection screen and return clickable button rects."""
    width, height = surface.get_size()
    t = pygame.time.get_ticks() / 1000.0
    background = _get_background(surface)
    surface.blit(background, (0, 0))
    draw_clouds(surface, t)
    draw_banderitas(surface, t)

    draw_outlined_text(
        surface, "CHOOSE GAME MODE", TITLE_FONT, SUN_YELLOW, DARK,
        (width // 2, 105), thickness=3,
    )
    draw_text(
        surface, "Pick how you want to play!", SUBTITLE_FONT, DARK,
        (width // 2, 150),
    )

    specs = [
        ("classic", "CLASSIC MODE", "Complete 3 round trips", J_GREEN),
        ("defender", "DEFENDER MODE", "More guards block your path", J_BLUE),
        ("time_attack", "TIME ATTACK", "Score as much as you can in 60 seconds", J_ORANGE),
        ("coop", "2-PLAYER CO-OP", "Mag-Barkada Mode: Play with a friend!", J_RED),
    ]
    buttons = {}
    button_w, button_h, gap = 510, 78, 18
    total_h = len(specs) * button_h + (len(specs) - 1) * gap
    y = max(195, (height - total_h) // 2 - 5)

    for key, title, subtitle, color in specs:
        rect = pygame.Rect((width - button_w) // 2, y, button_w, button_h)
        hovered = rect.collidepoint(mouse_position)
        draw_button(surface, title, rect, hovered=hovered, color=color, t=t)
        draw_text(surface, subtitle, SIGN_FONT, DARK, (rect.centerx, rect.bottom - 17))
        buttons[key] = rect
        y += button_h + gap

    back_rect = pygame.Rect(30, height - 65, 150, 44)
    draw_button(surface, "BACK", back_rect, hovered=back_rect.collidepoint(mouse_position), color=J_RED, t=t)
    buttons["back"] = back_rect
    return buttons
