import math
import os
import pygame

# ==================================================
# SHARED DRAWING HELPERS
# Icons used by the HUD, shop and pickups.
# ==================================================

WHITE = (255, 255, 255)
YELLOW = (255, 205, 75)
RED = (205, 58, 52)
BLUE = (48, 100, 210)
BROWN = (120, 76, 45)
DARK = (35, 45, 40)


def draw_text(surface, text, font, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_heart_icon(surface, x, y, size=9, color=RED):
    pygame.draw.circle(surface, color, (x - size // 2, y - size // 3), size // 2 + 1)
    pygame.draw.circle(surface, color, (x + size // 2, y - size // 3), size // 2 + 1)
    pygame.draw.polygon(
        surface,
        color,
        [
            (x - size, y - size // 4),
            (x + size, y - size // 4),
            (x, y + size),
        ],
    )


def draw_bolt_icon(surface, x, y, size=12, color=(255, 225, 60)):
    points = [
        (x + size // 3, y - size),
        (x - size // 2, y + 1),
        (x, y + 1),
        (x - size // 3, y + size),
        (x + size // 2, y - 2),
        (x, y - 2),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, BROWN, points, 2)


def draw_shield_icon(surface, x, y, size=12, color=(70, 170, 235)):
    points = [
        (x - size, y - size),
        (x + size, y - size),
        (x + size, y),
        (x, y + size + 3),
        (x - size, y),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, WHITE, points, 2)
    pygame.draw.line(surface, WHITE, (x, y - size + 3), (x, y + size - 2), 2)


def draw_gem_icon(surface, x, y, size=11, color=(70, 220, 150)):
    points = [
        (x, y - size),
        (x + size, y),
        (x, y + size),
        (x - size, y),
    ]
    pygame.draw.polygon(surface, color, points)
    pygame.draw.polygon(surface, WHITE, points, 2)
    pygame.draw.line(surface, WHITE, (x - size // 2, y - 1), (x, y - size // 2), 2)


def draw_coin_icon(surface, x, y, size=11, spin=0.0):
    coin_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets",
        "characters",
        "collectibles",
        "coin.png",
    )

    try:
        coin_image = pygame.image.load(coin_path)
        coin_image = pygame.transform.smoothscale(
            coin_image, (size * 2, size * 2)
        )
        coin_rect = coin_image.get_rect(center=(x, y))
        surface.blit(coin_image, coin_rect)
    except (pygame.error, OSError):
        pygame.draw.circle(surface, (255, 205, 75), (x, y), size)
        pygame.draw.circle(surface, BROWN, (x, y), size, 2)


def draw_star_icon(surface, x, y, radius=11):
    points = []

    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = radius if i % 2 == 0 else radius * 0.45
        points.append((
            int(x + r * math.cos(angle)),
            int(y + r * math.sin(angle))
        ))

    pygame.draw.polygon(surface, YELLOW, points)
    pygame.draw.polygon(surface, BROWN, points, 2)