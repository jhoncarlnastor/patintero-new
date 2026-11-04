
import os
import pygame

from screens.helpers import draw_coin_icon

# Character sprite assets
CHARACTER_ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "characters",
)

CHARACTER_IMAGES = {}
COIN_IMAGE = None

COIN_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "characters",
    "collectibles",
    "coin.png",
)

try:
    COIN_IMAGE = pygame.image.load(COIN_PATH)
except (pygame.error, OSError) as error:
    print(f"Could not load rare coin sprite: {error}")

for character_id in (
    "reian",
    "charles",
    "carlo",
):
    image_path = os.path.join(
        CHARACTER_ASSET_DIR,
        f"{character_id}.png",
    )

    try:
        CHARACTER_IMAGES[character_id] = pygame.image.load(image_path)
    except (pygame.error, OSError):
        CHARACTER_IMAGES[character_id] = None

# Tropical Filipino color palette
SKY = (123, 205, 230)
CREAM = (255, 246, 218)
DARK_GREEN = (30, 105, 57)
GREEN = (55, 145, 76)
YELLOW = (255, 205, 75)
BROWN = (120, 76, 45)
WHITE = (255, 255, 255)
DARK = (35, 65, 54)
RED = (195, 75, 55)
BLUE = (70, 135, 205)
ORANGE = (230, 145, 55)

TITLE_FONT = None
BODY_FONT = None
SMALL_FONT = None


# ==================================================
# CHARACTERS
# price        -> rare coins needed to unlock
# base_speed   -> pixels per second
# start_lives  -> lives at the start of a map
# max_lives    -> hearts can't go above this
# sprint_mult  -> speed multiplier while holding SHIFT
# sprint_drain -> energy used per second while sprinting
# dash         -> can press SPACE for a quick dash
# start_shield -> seconds of free shield at map start
# shield_time  -> how long a shield pickup lasts
# ==================================================

CHARACTERS = [
    {
        "id": "reian",
        "name": "REIAN",
        "role": "ALL-AROUND RUNNER",
        "description": "Throw a slipper to stun guards.",
        "speed": 6,
        "agility": 7,
        "stamina": 7,
        "color": RED,
        "ability": "TSINELAS STUN",
        "price": 12,
        "base_speed": 240.0,
        "start_lives": 3,
        "max_lives": 5,
        "sprint_mult": 1.7,
        "sprint_drain": 28.0,
        "dash": False,
        "stun_ability": True,
        "start_shield": 0.0,
        "shield_time": 9.0,
    },
    {
        "id": "charles",
        "name": "CHARLES",
        "role": "SPEED SPECIALIST",
        "description": "Fast + Quick Dash (SPACE).",
        "speed": 9,
        "agility": 8,
        "stamina": 5,
        "color": BLUE,
        "ability": "QUICK DASH",
        "price": 0,
        "base_speed": 275.0,
        "start_lives": 3,
        "max_lives": 4,
        "sprint_mult": 1.8,
        "sprint_drain": 36.0,
        "dash": True,
        "start_shield": 0.0,
        "shield_time": 9.0,
    },
    {
        "id": "carlo",
        "name": "CARLO",
        "role": "SHIELD SPECIALIST",
        "description": "Heavy tank + Barangay Shield.",
        "speed": 5,
        "agility": 6,
        "stamina": 9,
        "color": ORANGE,
        "ability": "BARANGAY SHIELD",
        "price": 20,
        "base_speed": 215.0,
        "start_lives": 4,
        "max_lives": 6,
        "sprint_mult": 1.6,
        "sprint_drain": 20.0,
        "dash": False,
        "shield_ability": True,
        "start_shield": 6.0,
        "shield_time": 14.0,
    },
]


def init_character_fonts():
    global TITLE_FONT, BODY_FONT, SMALL_FONT

    TITLE_FONT = pygame.font.SysFont("arial", 34, bold=True)
    BODY_FONT = pygame.font.SysFont("arial", 22, bold=True)
    SMALL_FONT = pygame.font.SysFont("arial", 16)


def get_character(character_id):
    for character in CHARACTERS:
        if character["id"] == character_id:
            return character
    return next(
    character for character in CHARACTERS
    if character["id"] == "charles"
)


def draw_text(surface, text, font, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_character_art(surface, center, shirt_color, selected=False, char_id=None):
    x, y = center

   
    # Use the selected character's image
    sprite = CHARACTER_IMAGES.get(char_id)

    if sprite is not None:
        sprite = sprite.copy()
        sprite = pygame.transform.smoothscale(sprite, (120, 120))

        # Draw the image centered on the portrait area
        sprite_rect = sprite.get_rect(center=(x, y + 5))
        surface.blit(sprite, sprite_rect)
    else:
        # Fallback if the image is missing
        pygame.draw.circle(surface, (230, 185, 140), (x, y - 35), 25)
        pygame.draw.rect(
            surface,
            shirt_color,
            (x - 23, y - 12, 46, 62),
            border_radius=10,
        )

    

def draw_padlock(surface, x, y):
    pygame.draw.arc(surface, (90, 90, 95), (x - 9, y - 18, 18, 22), 0, 3.14159, 4)
    pygame.draw.rect(surface, (110, 110, 118), (x - 12, y - 4, 24, 18), border_radius=4)
    pygame.draw.circle(surface, (45, 45, 50), (x, y + 4), 3)


def draw_stat_bar(surface, label, value, x, y, width=170):
    draw_text(
        surface, label, SMALL_FONT,
        DARK, (x + 30, y + 7)
    )

    bar_x = x + 72
    bar_y = y
    bar_width = width - 78
    bar_height = 13

    pygame.draw.rect(
        surface, (220, 220, 205),
        (bar_x, bar_y, bar_width, bar_height),
        border_radius=6
    )

    fill_width = int(bar_width * value / 10)

    pygame.draw.rect(
        surface, GREEN,
        (bar_x, bar_y, fill_width, bar_height),
        border_radius=6
    )


def draw_button(surface, text, rect, hovered=False, enabled=True):
    if not enabled:
        color = (120, 130, 125)
    else:
        color = YELLOW if hovered else DARK_GREEN

    text_color = DARK if (hovered and enabled) else WHITE

    pygame.draw.rect(
        surface, color, rect, border_radius=12
    )
    pygame.draw.rect(
        surface, CREAM, rect, width=2, border_radius=12
    )

    draw_text(
        surface, text, BODY_FONT,
        text_color, rect.center
    )


def draw_character_select(
    surface,
    mouse_position,
    selected_index=None,
    owned_ids=None,
    coins=0,
    message="",
):
    if owned_ids is None:
        owned_ids = ["charles"]

    width, height = surface.get_size()
    now = pygame.time.get_ticks() / 1000.0

    # Background
    surface.fill(SKY)

    # Decorative hills
    pygame.draw.ellipse(
        surface, (105, 180, 112),
        (-100, 430, 600, 230)
    )
    pygame.draw.ellipse(
        surface, GREEN,
        (430, 440, 700, 240)
    )

    # Main panel
    panel = pygame.Rect(35, 25, width - 70, height - 105)

    pygame.draw.rect(
        surface, CREAM, panel, border_radius=24
    )
    pygame.draw.rect(
        surface, DARK_GREEN, panel,
        width=4, border_radius=24
    )

    draw_text(
        surface, "CHOOSE YOUR RUNNER",
        TITLE_FONT, DARK_GREEN,
        (width // 2, 65)
    )

    draw_text(
        surface, "Collect rare coins in the game to unlock new characters",
        SMALL_FONT, DARK,
        (width // 2, 100)
    )

        # Rare coin balance
    coin_box = pygame.Rect(width - 215, 45, 150, 34)
    pygame.draw.rect(surface, (235, 225, 195), coin_box, border_radius=17)

    if COIN_IMAGE is not None:
        coin_sprite = pygame.transform.smoothscale(COIN_IMAGE, (24, 24))
        coin_rect = coin_sprite.get_rect(
            center=(coin_box.left + 25, coin_box.centery)
        )
        surface.blit(coin_sprite, coin_rect)
    else:
        draw_coin_icon(
            surface,
            coin_box.left + 20,
            coin_box.centery,
            11,
            now * 3
        )

    draw_text(
        surface,
        str(coins),
        BODY_FONT,
        DARK_GREEN,
        (coin_box.centerx + 12, coin_box.centery)
    )

    card_width = 270
    card_height = 355
    gap = 20
    total_width = card_width * 3 + gap * 2
    start_x = (width - total_width) // 2
    card_y = 125

    cards = []

    for index, character in enumerate(CHARACTERS):
        rect = pygame.Rect(
            start_x + index * (card_width + gap),
            card_y,
            card_width,
            card_height
        )
        cards.append(rect)

        owned = character["id"] in owned_ids
        is_selected = selected_index == index
        is_hovered = rect.collidepoint(mouse_position)

        card_color = (255, 250, 232) if not is_hovered else WHITE
        border_color = YELLOW if is_selected else (210, 220, 195)

        pygame.draw.rect(
            surface, card_color, rect, border_radius=18
        )
        pygame.draw.rect(
            surface, border_color, rect,
            width=4 if is_selected else 2,
            border_radius=18
        )

        # Character portrait
        draw_character_art(
            surface,
            (rect.centerx, rect.y + 105),
            character["color"],
            is_selected,
            character["id"],
        )

        if not owned:
            shade = pygame.Surface((card_width - 8, 160), pygame.SRCALPHA)
            shade.fill((90, 95, 100, 95))
            surface.blit(shade, (rect.x + 4, rect.y + 4))
            draw_padlock(surface, rect.right - 30, rect.y + 32)

        draw_text(
            surface, character["name"],
            BODY_FONT, DARK_GREEN,
            (rect.centerx, rect.y + 185)
        )

        draw_text(
            surface, character["role"],
            SMALL_FONT, RED,
            (rect.centerx, rect.y + 211)
        )

        draw_text(
            surface, character["description"],
            SMALL_FONT, DARK,
            (rect.centerx, rect.y + 235)
        )

        draw_stat_bar(
            surface, "SPD", character["speed"],
            rect.x + 35, rect.y + 264, 200
        )
        draw_stat_bar(
            surface, "AGI", character["agility"],
            rect.x + 35, rect.y + 289, 200
        )
        draw_stat_bar(
            surface, "STA", character["stamina"],
            rect.x + 35, rect.y + 314, 200
        )

        # Status line (bottom of card)
        status_y = rect.y + 343

        if owned:
            draw_text(
                surface,
                "SELECTED" if is_selected else "OWNED",
                SMALL_FONT, DARK_GREEN,
                (rect.centerx, status_y)
            )
        else:
            draw_coin_icon(
                surface, rect.centerx - 52, status_y, 8, now * 3
            )
            draw_text(
                surface, f"{character['price']} RARE COINS",
                SMALL_FONT, (130, 60, 190),
                (rect.centerx + 10, status_y)
            )

    back_rect = pygame.Rect(65, height - 65, 145, 45)
    confirm_rect = pygame.Rect(
        width - 245, height - 65, 180, 45
    )

    draw_button(
        surface, "BACK", back_rect,
        back_rect.collidepoint(mouse_position)
    )

    # CONFIRM turns into BUY when the selected character is locked.
    if selected_index is None:
        confirm_text = "CONFIRM"
        confirm_enabled = False
    else:
        chosen = CHARACTERS[selected_index]

        if chosen["id"] in owned_ids:
            confirm_text = "CONFIRM"
            confirm_enabled = True
        else:
            confirm_text = f"BUY  {chosen['price']}"
            confirm_enabled = True

    draw_button(
        surface, confirm_text, confirm_rect,
        confirm_rect.collidepoint(mouse_position),
        confirm_enabled,
    )

    if message:
        pill = pygame.Rect(0, 0, 420, 36)
        pill.center = (width // 2, height - 42)
        pygame.draw.rect(surface, DARK_GREEN, pill, border_radius=18)
        draw_text(
            surface, message,
            SMALL_FONT, WHITE,
            pill.center
        )

    return {
        "cards": cards,
        "back": back_rect,
        "confirm": confirm_rect
    }
