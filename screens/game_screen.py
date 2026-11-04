import math
import random
import pygame
import os

# Load character sprites
CHARACTER_ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "characters",
)

GAME_CHARACTER_IMAGES = {}

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
        GAME_CHARACTER_IMAGES[character_id] = pygame.image.load(image_path)
    except (pygame.error, OSError) as error:
        print(f"Could not load {character_id}: {error}")
        GAME_CHARACTER_IMAGES[character_id] = None

# Load collectible item sprites
COLLECTIBLE_ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "characters",
    "collectibles",
)

COLLECTIBLE_IMAGES = {}

COLLECTIBLE_FILES = {
    "energy": "coke-speed.png",
    "heart": "chippy-life.png",
    "shield": "mikmik-shield.png",
    "freeze": "freeze.png",
    "coin": "coin.png",
}

for pickup_kind, filename in COLLECTIBLE_FILES.items():
    image_path = os.path.join(COLLECTIBLE_ASSET_DIR, filename)

    try:
        COLLECTIBLE_IMAGES[pickup_kind] = pygame.image.load(image_path)
    except (pygame.error, OSError) as error:
        print(f"Could not load collectible {filename}: {error}")
        COLLECTIBLE_IMAGES[pickup_kind] = None


# Directional running animation frames
MOTION_ASSET_DIR = os.path.join(CHARACTER_ASSET_DIR, "motion")

GAME_ANIMATIONS = {}

for character_id in (
    "reian",
    "charles",
    "carlo",
):
    GAME_ANIMATIONS[character_id] = {
        "back": [],
        "left": [],
        "right": [],
        "front": [],
    }

    for direction in ("back", "front", "left", "right"):
        frame_number = 1

        while True:
            image_path = os.path.join(
                MOTION_ASSET_DIR,
                f"{character_id}_{direction}{frame_number}.png",
            )

            if not os.path.isfile(image_path):
                break

            try:
                frame = pygame.image.load(image_path)
                GAME_ANIMATIONS[character_id][direction].append(frame)
            except (pygame.error, OSError) as error:
                print(f"Could not load animation frame: {image_path}: {error}")

            frame_number += 1

from screens.helpers import (
    draw_bolt_icon,
    draw_coin_icon,
    draw_gem_icon,
    draw_heart_icon,
    draw_shield_icon,
    draw_star_icon,
)
from screens.maps import ZONE_SLOW, draw_map_background, zone_rect, get_playing_field

# ==================================================
# PATINTERO: GRID RUSH - GAMEPLAY
# Maps, pickups (energy, heart, shield, extra points,
# rare coins), characters and chaser guards.
# ==================================================

SKY = (123, 205, 230)
DARK_GREEN = (30, 85, 48)
CREAM = (255, 246, 218)
WHITE = (255, 255, 255)
RED = (205, 58, 52)
BLUE = (48, 100, 210)
YELLOW = (255, 205, 75)
DARK = (35, 45, 40)
BROWN = (120, 76, 45)
GOLD_LIGHT = (255, 240, 150)
SKIN = (225, 175, 125)

TITLE_FONT = None
BODY_FONT = None
SMALL_FONT = None
POP_FONT = None

PLAYER_SIZE = 28
GUARD_SIZE = 30

HIT_COOLDOWN = 1.5        # seconds of invulnerability after a hit
SHIELD_BREAK_COOLDOWN = 0.8

MAX_ENERGY = 100.0
START_ENERGY = 60.0
ENERGY_PICKUP = 35.0
ENERGY_REGEN = 15.0


MAX_PICKUPS = 3
PICKUP_LIFE = 9.0
COIN_LIFE = 7.0

STAR_POINTS = 100
EXTRA_POINTS = 250
COIN_POINTS = 50
WIN_COIN_BONUS = 2

DASH_TIME = 0.16
DASH_COOLDOWN = 3.0
DASH_SPEED_MULT = 3.2


PICKUP_COLORS = {
    "energy": (255, 215, 60),
    "heart": (235, 70, 90),
    "shield": (70, 170, 235),
    "points": (70, 220, 150),
    "coin": (170, 90, 230),
    "freeze": (80, 220, 255),
}

TIME_FREEZE_DURATION = 5.0
TIME_FREEZE_CHANCE = 0.04



def init_game_fonts():
    global TITLE_FONT, BODY_FONT, SMALL_FONT, POP_FONT

    TITLE_FONT = pygame.font.SysFont("arial", 32, bold=True)
    BODY_FONT = pygame.font.SysFont("arial", 21, bold=True)
    SMALL_FONT = pygame.font.SysFont("arial", 16)
    POP_FONT = pygame.font.SysFont("arial", 18, bold=True)


def draw_text(surface, text, font, color, center):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=center))


def draw_text_left(surface, text, font, color, x, y):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(midleft=(x, y)))


# ==================================================
# SPAWNING HELPERS
# ==================================================

def find_free_spot(field, player, guards, taken):
    for _ in range(300):
        x = random.randint(field.left + 25, field.right - 25)
        y = random.randint(field.top + 25, field.bottom - 25)

        rect = pygame.Rect(x - 14, y - 14, 28, 28)

        if rect.colliderect(player.inflate(90, 90)):
            continue

        if any(rect.colliderect(g["rect"].inflate(30, 30)) for g in guards):
            continue

        if any(abs(x - tx) < 45 and abs(y - ty) < 45 for tx, ty in taken):
            continue

        return x, y

    return field.centerx, field.centery


def in_slow_zone(state, point):
    field = state["field"]

    for zone in state["map"]["zones"]:
        rect = zone_rect(field, zone)
        rx = rect.width / 2
        ry = rect.height / 2

        if rx <= 0 or ry <= 0:
            continue

        nx = (point[0] - rect.centerx) / rx
        ny = (point[1] - rect.centery) / ry

        if nx * nx + ny * ny <= 1.0:
            return True

    return False


def make_guards(field, map_def):
    guards = []

    for spec in map_def["guards"]:
        kind = spec["kind"]

        if kind == "h":
            cx = field.left + spec["start"] * field.width
            cy = field.top + spec["f"] * field.height
        elif kind == "v":
            cx = field.left + spec["f"] * field.width
            cy = field.top + spec["start"] * field.height
        else:
            cx = field.left + spec["sx"] * field.width
            cy = field.top + spec["sy"] * field.height

        rect = pygame.Rect(0, 0, GUARD_SIZE, GUARD_SIZE)
        rect.center = (int(cx), int(cy))

        guard_data = {
            "rect": rect,
            "pos": [float(rect.x), float(rect.y)],
            "kind": kind,
            "direction": spec.get("dir", 1),
            "speed": float(spec["speed"]),
            "color": spec["color"],
        }
        
        guards.append(guard_data)

    return guards


def reset_player_position(state):
    player = state["player"]
    field = state["field"]

    if state.get("mode") == "coop":
        player.centerx = field.centerx - 40
        player.bottom = field.bottom - 25
        state["player_pos"][0] = float(player.x)
        state["player_pos"][1] = float(player.y)

        if state.get("player2"):
            p2 = state["player2"]
            p2.centerx = field.centerx + 40
            p2.bottom = field.bottom - 25
            state["player_pos2"][0] = float(p2.x)
            state["player_pos2"][1] = float(p2.y)
        
        # Reset player2 state
        state["invulnerable_until2"] = 0.0
        state["hit_flash_until2"] = 0.0
        state["shield_until2"] = 0.0
    else:
        player.centerx = field.centerx
        player.bottom = field.bottom - 25
        state["player_pos"][0] = float(player.x)
        state["player_pos"][1] = float(player.y)


def create_game_state(width, height, map_def, character, mode="classic"):
    field = get_playing_field(width, height, map_def["id"])

    player = pygame.Rect(
        field.centerx - PLAYER_SIZE // 2 - (40 if mode == "coop" else 0),
        field.bottom - PLAYER_SIZE - 25,
        PLAYER_SIZE,
        PLAYER_SIZE,
    )

    guards = make_guards(field, map_def)

    # Defender Mode adds two extra patrol defenders and makes the patrols
    # slightly faster. Classic Mode keeps the original guard setup unchanged.
    if mode == "defender":
        extra_specs = [
            {"kind": "h", "start": 0.30, "f": 0.42, "dir": 1,
             "speed": 105, "color": (48, 100, 210)},
            {"kind": "v", "start": 0.66, "f": 0.68, "dir": -1,
             "speed": 95, "color": (205, 58, 52)},
        ]
        for spec in extra_specs:
            if spec["kind"] == "h":
                cx = field.left + spec["start"] * field.width
                cy = field.top + spec["f"] * field.height
            else:
                cx = field.left + spec["f"] * field.width
                cy = field.top + spec["start"] * field.height
            rect = pygame.Rect(0, 0, GUARD_SIZE, GUARD_SIZE)
            rect.center = (int(cx), int(cy))
            guards.append({
                "rect": rect, "pos": [float(rect.x), float(rect.y)],
                "kind": spec["kind"], "direction": spec["dir"],
                "speed": float(spec["speed"]), "color": spec["color"],
            })
        for guard in guards:
            guard["speed"] *= 1.20

    now = pygame.time.get_ticks()

    state = {
        "map": map_def,
        "mode": mode,
        "time_limit": 60.0 if mode == "time_attack" else None,
        "round": 1,
        "total_rounds": 3,
        "round_phase": "outbound",
        "character": character,
        "field": field,
        "player": player,
        "player_pos": [float(player.x), float(player.y)],
        "player2": pygame.Rect(
            field.centerx + 40,
            field.bottom - PLAYER_SIZE - 25,
            PLAYER_SIZE,
            PLAYER_SIZE,
        ) if mode == "coop" else None,
        "player_pos2": [
            float(field.centerx + 40),
            float(field.bottom - PLAYER_SIZE - 25),
        ] if mode == "coop" else [0.0, 0.0],
        "sprinting2": False,
        "moving2": False,
        "movement_time2": 0.0,
        "dash_until2": 0.0,
        "dash_ready2": 0.0,
        "dash_key_down2": False,
        "slippers": [],
        "ghost_trails": [],
        "guards": guards,
        "stars": [],
        "total_stars": map_def["stars"],
        "stars_collected": 0,
        "points": 0,
        "lives": character["start_lives"],
        "max_lives": character["max_lives"],
        "energy": START_ENERGY,
        "shield_until": character["start_shield"],
        "shield_total": max(character["start_shield"], 1.0),
        "invulnerable_until": 0.0,
        "hit_flash_until": 0.0,
        "dash_until": 0.0,
        "dash_ready": 0.0,
        "dash_dir": (0.0, -1.0),
        "dash_key_down": False,
        "sprinting": False,
        "moving": False,
        "dust_timer": 0.0,
        "pickups": [],
        "freeze_until": 0.0,
        "freeze_message_until": 0.0,
        "spawn_timer": 1.5,
        "rare_coins": 0,
        "popups": [],
        "particles": [],
        "collect_effects": [],
        "sfx": [],
        "status": "playing",
        "time": 0.0,
        "movement_time": 0.0,
        "started_at": now,
        "last_update": now,
        "bonus_points": 0,
        "bonus_coins": 0,
        "finalized": False,
        # Player 2 specific state
        "lives2": character["start_lives"],
        "invulnerable_until2": 0.0,
        "hit_flash_until2": 0.0,
        "shield_until2": 0.0,
    }

    for _ in range(state["total_stars"]):
        taken = list(state["stars"])
        state["stars"].append(find_free_spot(field, player, guards, taken))

    return state


# ==================================================
# CHARACTERS
# ==================================================


def add_ghost_trail(state, pos, color):
    state["ghost_trails"].append({
        "pos": pos,
        "color": color,
        "born": state["time"],
        "life": 0.25
    })

def update_ghost_trails(state, dt):
    remaining = []
    for trail in state["ghost_trails"]:
        if state["time"] - trail["born"] < trail["life"]:
            remaining.append(trail)
    state["ghost_trails"] = remaining

def draw_ghost_trails(surface, state):
    for trail in state["ghost_trails"]:
        age = state["time"] - trail["born"]
        alpha = int(150 * (1.0 - age / trail["life"]))
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(s, (*trail["color"], alpha), (16, 16), 14)
        surface.blit(s, (trail["pos"][0] - 16, trail["pos"][1] - 16))

def throw_slipper(state, x, y, direction, thrower=1):
    dx, dy = direction
    if dx == 0 and dy == 0:
        dy = -1.0 # default forward
    state["slippers"].append({
        "x": float(x),
        "y": float(y),
        "vx": dx * 400.0 if dx != 0 or dy != 0 else 0.0,
        "vy": (dy * 400.0) if (dx != 0 or dy != 0) else -400.0,
        "born": state["time"],
        "life": 1.5
    })

def update_slippers(state, dt):
    remaining = []
    for s in state["slippers"]:
        if state["time"] - s["born"] > s["life"]:
            continue
        s["x"] += s["vx"] * dt
        s["y"] += s["vy"] * dt
        
        s_rect = pygame.Rect(s["x"] - 8, s["y"] - 8, 16, 16)
        hit = False
        for g in state["guards"]:
            if s_rect.colliderect(g["rect"]):
                # Freeze guard for 3 seconds
                g["speed"] = 0
                hit = True
                add_popup(state, "TSINELAS HIT! STUNNED", g["rect"]["centerx"], g["rect"]["centery"], (255, 200, 50))
                break
        if not hit:
            remaining.append(s)
    state["slippers"] = remaining

def draw_slippers(surface, state):
    for s in state["slippers"]:
        # Draw slipper with outline for better visibility
        pygame.draw.ellipse(surface, (180, 120, 60), (s["x"] - 7, s["y"] - 5, 14, 10))
        pygame.draw.ellipse(surface, (120, 60, 30), (s["x"] - 6, s["y"] - 4, 12, 8))
        pygame.draw.ellipse(surface, (200, 160, 80), (s["x"] - 4, s["y"] - 3, 8, 5))

def draw_player(
    surface,
    player,
    character,
    blinking,
    moving,
    anim_time,
    direction=(0, 0),
):
    if blinking:
        return

    char_id = character["id"]
    sprite = GAME_CHARACTER_IMAGES.get(char_id)

    dx, dy = direction
    animation_direction = None

    if moving:
        if abs(dx) > abs(dy):
            animation_direction = "right" if dx > 0 else "left"
        else:
            animation_direction = "back" if dy < 0 else "front"

    frames = GAME_ANIMATIONS.get(char_id, {}).get(
        animation_direction, []
    ) if animation_direction else []

    if moving and frames:
        frame_index = int(anim_time * 10) % len(frames)
        sprite = frames[frame_index]

    if moving:
        bounce = int(math.sin(anim_time * 18) * 2)
    else:
        bounce = int(math.sin(anim_time * 3))

    pygame.draw.ellipse(
        surface,
        (45, 95, 48),
        (
            player.centerx - player.width,
            player.bottom - 3,
            player.width * 2,
            9,
        ),
    )

    if sprite is not None:
        is_motion_frame = moving and frames and (sprite in frames)
        scale_size = (30, 34) if is_motion_frame else (42, 42)

        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            scale_size,
        )

        sprite_rect = scaled_sprite.get_rect(
            midbottom=(
                player.centerx,
                player.bottom + bounce,
            )
        )

        surface.blit(scaled_sprite, sprite_rect)

    else:
        shirt = character["color"]
        px = player.x
        py = player.y + bounce

        pygame.draw.circle(
            surface, SKIN, (player.centerx, py + 7), 9
        )
        pygame.draw.rect(
            surface,
            shirt,
            (px + 4, py + 14, player.width - 8, 11),
            border_radius=4,
        )

        leg_offset = (
            int(math.sin(anim_time * 18) * 3)
            if moving else 0
        )

        pygame.draw.line(
            surface,
            DARK,
            (player.centerx - 4, player.bottom - 3),
            (player.centerx - 5 + leg_offset, player.bottom + 3),
            4,
        )
        pygame.draw.line(
            surface,
            DARK,
            (player.centerx + 4, player.bottom - 3),
            (player.centerx + 5 - leg_offset, player.bottom + 3),
            4,
        )



def draw_guard(surface, guard, anim_time=0):
    rect = guard["rect"]
    color = guard["color"]

    # Draw regular guard
    pygame.draw.ellipse(
        surface,
        (45, 95, 48),
        (rect.left + 1, rect.bottom - 3, rect.width - 2, 9),
    )

    # Chasers get a pulsing warning ring.
    if guard["kind"] == "chaser":
        pulse = 20 + int(3 * math.sin(anim_time * 6))
        ring = pygame.Surface((pulse * 2 + 4, pulse * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(
            ring, (255, 80, 60, 110),
            (pulse + 2, pulse + 2), pulse, 3,
        )
        surface.blit(ring, (rect.centerx - pulse - 2, rect.centery - pulse - 2))

    pygame.draw.circle(surface, SKIN, (rect.centerx, rect.top + 7), 9)

    pygame.draw.arc(
        surface,
        DARK_GREEN,
        (rect.centerx - 10, rect.top - 2, 20, 15),
        math.pi,
        2 * math.pi,
        4,
    )

    pygame.draw.rect(
        surface,
        color,
        (rect.left + 3, rect.top + 14, rect.width - 6, 12),
        border_radius=3,
    )

    pygame.draw.line(
        surface, SKIN,
        (rect.left + 4, rect.top + 17), (rect.left, rect.top + 23), 4,
    )
    pygame.draw.line(
        surface, SKIN,
        (rect.right - 4, rect.top + 17), (rect.right, rect.top + 23), 4,
    )

    pygame.draw.line(
        surface, DARK,
        (rect.left + 9, rect.bottom - 3), (rect.left + 7, rect.bottom + 2), 4,
    )
    pygame.draw.line(
        surface, DARK,
        (rect.right - 9, rect.bottom - 3), (rect.right - 7, rect.bottom + 2), 4,
    )



def draw_shield_bubble(surface, player, remaining, anim_time):
    # Blink when the shield is about to run out.
    if remaining < 2.0 and int(anim_time * 8) % 2 == 0:
        return

    radius = 26 + int(2 * math.sin(anim_time * 5))
    bubble = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    center = (radius + 2, radius + 2)

    # Aura effect: if character is Carlo, make it more intense
    color_inner = (90, 190, 255, 60)
    color_outer = (170, 225, 255, 190)

    pygame.draw.circle(bubble, color_inner, center, radius)
    pygame.draw.circle(bubble, color_outer, center, radius, 3)
    
    surface.blit(bubble, (player.centerx - center[0], player.centery - center[1]))
    surface.blit(
        bubble,
        (player.centerx - radius - 2, player.centery - radius + 2),
    )


# ==================================================
# STARS, PICKUPS AND EFFECTS
# ==================================================

def star_points(x, y, outer_radius, inner_radius, rotation=-90):
    points = []

    for i in range(10):
        angle = rotation + i * 36
        radius = outer_radius if i % 2 == 0 else inner_radius
        radians = math.radians(angle)

        points.append(
            (
                int(x + radius * math.cos(radians)),
                int(y + radius * math.sin(radians)),
            )
        )

    return points


def draw_star(surface, x, y, anim_time=0):
    pulse = 1.0 + 0.12 * math.sin(anim_time * 5)
    radius = int(13 * pulse)

    glow = pygame.Surface((58, 58), pygame.SRCALPHA)
    glow_center = (29, 29)

    pygame.draw.circle(glow, (255, 215, 75, 28), glow_center, 27)
    pygame.draw.circle(glow, (255, 230, 120, 40), glow_center, 19)

    surface.blit(glow, (x - 29, y - 29))

    points = star_points(x, y, radius, max(4, int(radius * 0.45)))

    pygame.draw.polygon(surface, YELLOW, points)
    pygame.draw.polygon(surface, BROWN, points, 2)

    pygame.draw.circle(surface, WHITE, (x - 3, y - 3), 2)



def draw_pickup(surface, pickup, state, anim_time):
    remaining = pickup["life"] - (state["time"] - pickup["born"])

    # Blink in the last moments before it disappears.
    if remaining < 2.5 and int(anim_time * 8) % 2 == 0:
        return

    kind = pickup["kind"]
    x = pickup["x"]
    y = pickup["y"] + int(math.sin(anim_time * 4 + pickup["x"]) * 3)

    color = PICKUP_COLORS[kind]

    # Keep the existing colored glow.
    glow = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, 45), (32, 32), 30)
    pygame.draw.circle(glow, (*color, 70), (32, 32), 20)
    surface.blit(glow, (int(x - 32), int(y - 32)))

    # Draw the saved collectible sprite, if it loaded successfully.
    sprite = COLLECTIBLE_IMAGES.get(kind)

    if sprite is not None:
        # Scale the sprite while preserving its aspect ratio.
        target_size = 38
        original_width, original_height = sprite.get_size()
        scale = target_size / max(original_width, original_height)

        new_width = max(1, int(original_width * scale))
        new_height = max(1, int(original_height * scale))

        scaled_sprite = pygame.transform.smoothscale(
            sprite,
            (new_width, new_height),
        )

        sprite_rect = scaled_sprite.get_rect(
            center=(int(x), int(y))
        )
        surface.blit(scaled_sprite, sprite_rect)

    # Fallback icons for items without a loaded sprite.
    elif kind == "energy":
        draw_bolt_icon(surface, x, y, 13)

    elif kind == "heart":
        draw_heart_icon(surface, x, y - 1, 11, (235, 70, 90))

    elif kind == "shield":
        draw_shield_icon(surface, x, y - 2, 12)

    elif kind == "points":
        draw_gem_icon(surface, x, y, 12)

    elif kind == "coin":
        draw_coin_icon(surface, x, y, 13, anim_time * 4)

    elif kind == "freeze":
        pulse = 13 + int(2 * math.sin(anim_time * 8))

        pygame.draw.circle(
            surface,
            (190, 250, 255),
            (int(x), int(y)),
            pulse,
            3,
        )
        pygame.draw.circle(
            surface,
            (50, 180, 255),
            (int(x), int(y)),
            7,
        )
        pygame.draw.line(
            surface,
            WHITE,
            (int(x), int(y - 9)),
            (int(x), int(y + 9)),
            2,
        )
        pygame.draw.line(
            surface,
            WHITE,
            (int(x - 8), int(y)),
            (int(x + 8), int(y)),
            2,
        )



def add_popup(state, text, x, y, color):
    state["popups"].append(
        {"text": text, "x": float(x), "y": float(y), "life": 1.0, "color": color}
    )


def spawn_collection_effect(state, x, y, colors=None):
    if colors is None:
        colors = [YELLOW, GOLD_LIGHT, WHITE, (255, 170, 55)]

    for _ in range(16):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(45, 150)

        state["particles"].append(
            {
                "x": float(x),
                "y": float(y),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.35, 0.65),
                "max_life": 0.65,
                "radius": random.randint(2, 5),
                "color": random.choice(colors),
            }
        )

    state["collect_effects"].append(
        {"x": float(x), "y": float(y), "life": 0.35, "max_life": 0.35}
    )


def spawn_dust(state, x, y):
    state["particles"].append(
        {
            "x": float(x) + random.uniform(-4, 4),
            "y": float(y),
            "vx": random.uniform(-15, 15),
            "vy": random.uniform(-15, 15),
            "life": 0.3,
            "max_life": 0.3,
            "radius": random.randint(2, 4),
            "color": (255, 235, 150),
        }
    )


def update_effects(state, dt):
    for particle in state["particles"][:]:
        particle["life"] -= dt

        particle["x"] += particle["vx"] * dt
        particle["y"] += particle["vy"] * dt

        particle["vx"] *= max(0, 1 - 2.5 * dt)
        particle["vy"] *= max(0, 1 - 2.5 * dt)

        if particle["life"] <= 0:
            state["particles"].remove(particle)

    for effect in state["collect_effects"][:]:
        effect["life"] -= dt

        if effect["life"] <= 0:
            state["collect_effects"].remove(effect)

    for popup in state["popups"][:]:
        popup["life"] -= dt
        popup["y"] -= 38 * dt

        if popup["life"] <= 0:
            state["popups"].remove(popup)


def draw_effects(surface, state):
    for effect in state["collect_effects"]:
        progress = 1 - effect["life"] / effect["max_life"]
        radius = int(8 + progress * 30)
        alpha = max(0, int(200 * (1 - progress)))

        ring = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)

        pygame.draw.circle(
            ring,
            (255, 220, 90, alpha),
            (radius + 2, radius + 2),
            radius,
            width=3,
        )

        surface.blit(
            ring,
            (int(effect["x"] - radius - 2), int(effect["y"] - radius - 2)),
        )

    for particle in state["particles"]:
        alpha_ratio = max(0, particle["life"] / particle["max_life"])
        radius = max(1, int(particle["radius"] * alpha_ratio))

        pygame.draw.circle(
            surface,
            particle["color"],
            (int(particle["x"]), int(particle["y"])),
            radius,
        )

    for popup in state["popups"]:
        image = POP_FONT.render(popup["text"], True, popup["color"])
        shadow = POP_FONT.render(popup["text"], True, DARK)
        alpha = max(0, min(255, int(popup["life"] * 400)))

        image.set_alpha(alpha)
        shadow.set_alpha(alpha)

        pos = (int(popup["x"]), int(popup["y"]))
        surface.blit(shadow, shadow.get_rect(center=(pos[0] + 1, pos[1] + 1)))
        surface.blit(image, image.get_rect(center=pos))


# ==================================================
# HUD
# ==================================================

def draw_hud(surface, state):
    width = surface.get_width()
    character = state["character"]
    now = state["time"]

    panel = pygame.Rect(145, 6, width - 290, 138)

    pygame.draw.rect(surface, CREAM, panel, border_radius=12)
    pygame.draw.rect(surface, DARK_GREEN, panel, width=2, border_radius=12)

    # Title
    mode_label = {
        "classic": "CLASSIC",
        "defender": "DEFENDER",
        "time_attack": "TIME ATTACK",
    }.get(state.get("mode", "classic"), "CLASSIC")
    draw_text(
        surface,
        f"PATINTERO: GRID RUSH  -  {state['map']['name']}  |  {mode_label}",
        BODY_FONT,
        DARK_GREEN,
        (width // 2, 26),
    )

    # Row A: stars, points, rare coins, lives
    row_a = 62
    draw_star_icon(surface, 172, row_a, 10)
    draw_text_left(
        surface,
        f"{state['stars_collected']}/{state['total_stars']}",
        BODY_FONT, DARK, 190, row_a,
    )

    draw_text_left(
        surface, f"PTS {state['points']}", BODY_FONT, DARK, 290, row_a,
    )

    draw_coin_icon(surface, 462, row_a, 10, now * 3)
    draw_text_left(
        surface, f"x {state['rare_coins']}", BODY_FONT, (130, 60, 190), 478, row_a,
    )

    for i in range(state["max_lives"]):
        color = RED if i < state["lives"] else (170, 170, 170)
        draw_heart_icon(surface, 640 + i * 28, row_a, 9, color)

    # Round indicator / Time Attack countdown
    if state.get("mode") == "time_attack":
        remaining = max(0, int(state.get("time_limit", 60) - now + 0.999))
        indicator = f"TIME {remaining // 60:02d}:{remaining % 60:02d}"
    else:
        indicator = f"ROUND {state['round']}/{state['total_rounds']}"
    draw_text_left(
        surface,
        indicator,
        BODY_FONT,
        DARK_GREEN,
        755,
        row_a,
    )

    # Row B: energy, shield, dash
    row_b = 100

    draw_bolt_icon(surface, 170, row_b, 11)
    bar = pygame.Rect(190, row_b - 8, 140, 16)
    pygame.draw.rect(surface, (205, 200, 175), bar, border_radius=8)

    fill = int(bar.width * state["energy"] / MAX_ENERGY)

    if fill > 0:
        low = state["energy"] < 20 and int(now * 6) % 2 == 0
        fill_color = (230, 90, 70) if low else (255, 200, 40)
        pygame.draw.rect(
            surface, fill_color,
            (bar.x, bar.y, fill, bar.height),
            border_radius=8,
        )

    pygame.draw.rect(surface, DARK_GREEN, bar, 2, border_radius=8)

    draw_text_left(surface, "SHIFT", SMALL_FONT, DARK, 340, row_b)

    # Shield timer
    shield_left = max(0.0, state["shield_until"] - now)
    shield_color = (70, 170, 235) if shield_left > 0 else (170, 175, 170)
    draw_shield_icon(surface, 430, row_b - 2, 11, shield_color)

    shield_bar = pygame.Rect(450, row_b - 7, 100, 14)
    pygame.draw.rect(surface, (205, 200, 175), shield_bar, border_radius=7)

    if shield_left > 0:
        ratio = min(1.0, shield_left / state["shield_total"])
        pygame.draw.rect(
            surface, (90, 190, 255),
            (shield_bar.x, shield_bar.y, int(shield_bar.width * ratio), shield_bar.height),
            border_radius=7,
        )

    pygame.draw.rect(surface, DARK_GREEN, shield_bar, 2, border_radius=7)

    # Dash (Mabilis na Runner) or character name
    if character["dash"]:
        wait = max(0.0, state["dash_ready"] - now)
        ready = wait <= 0
        dash_text = "DASH [SPACE] READY" if ready else f"DASH {wait:0.1f}s"
        draw_text_left(
            surface, dash_text, SMALL_FONT,
            DARK_GREEN if ready else (150, 90, 60), 585, row_b,
        )
    else:
        draw_text_left(surface, character["name"], SMALL_FONT, DARK, 585, row_b)

    draw_text(
        surface,
        "MOVE: WASD / ARROWS   |   SHIFT: SPRINT   |   P: PAUSE   |   M: MUTE",
        SMALL_FONT,
        DARK,
        (width // 2, 128),
    )


# ==================================================
# DRAW GAME
# ==================================================

def draw_game_screen(surface, state):
    shake_offset = (0, 0)
    now = state["time"]
    if now < state.get("shake_until", 0.0):
        shake_offset = (random.randint(-4, 4), random.randint(-4, 4))
    
    # Use a temporary surface for screen shake
    game_surf = pygame.Surface(surface.get_size())
    game_surf.fill(SKY)
    
    field = state["field"]
    draw_map_background(game_surf, state["map"], field)

    anim_time = pygame.time.get_ticks() / 1000.0

    draw_ghost_trails(game_surf, state)

    for x, y in state["stars"]:
        draw_star(game_surf, x, y, anim_time)

    for pickup in state["pickups"]:
        draw_pickup(game_surf, pickup, state, anim_time)

    for guard in state["guards"]:
        draw_guard(game_surf, guard, anim_time)

    draw_slippers(game_surf, state)

    blinking1 = (
        now < state["invulnerable_until"]
        and int(now * 10) % 2 == 0
    )

    draw_player(
        game_surf,
        state["player"],
        state["character"],
        blinking1,
        state["moving"],
        state["movement_time"],
        state.get("move_direction", (0, 0)),
    )

    if state.get("mode") == "coop" and state.get("player2"):
        blinking2 = (
            now < state["invulnerable_until2"]
            and int(now * 10) % 2 == 0
        )
        draw_player(
            game_surf,
            state["player2"],
            state["character"],
            blinking2,
            state["moving2"],
            state["movement_time2"],
            state.get("move_direction2", (0, 0)),
        )
    
    shield_left = state["shield_until"] - now

    if shield_left > 0:
        draw_shield_bubble(game_surf, state["player"], shield_left, anim_time)
        if state.get("mode") == "coop" and state.get("player2"):
            draw_shield_bubble(game_surf, state["player2"], shield_left, anim_time)

    draw_effects(game_surf, state)
    
    surface.blit(game_surf, shake_offset)
    draw_hud(surface, state)

    # Red flash when player 1 loses a life
    if now < state["hit_flash_until"]:
        flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash.fill((220, 40, 40, 70))
        surface.blit(flash, (0, 0))

    # Red flash when player 2 loses a life
    if state.get("mode") == "coop" and now < state.get("hit_flash_until2", 0):
        flash = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash.fill((220, 40, 40, 70))
        surface.blit(flash, (0, 0))


# ==================================================
# UPDATE GAME
# ==================================================


def choose_pickup_kind(state):
    weights = {
        "energy": 30,
        "heart": 14,
        "shield": 16,
        "points": 22,
        "coin": 12,
        "freeze": 2,
    }

    if state["lives"] >= state["max_lives"]:
        weights["heart"] = 0

    if state["shield_until"] > state["time"]:
        weights["shield"] = 0

    if state["energy"] > 80:
        weights["energy"] = 8

    kinds = list(weights.keys())
    return random.choices(
        kinds,
        weights=[weights[k] for k in kinds],
    )[0]



def spawn_pickup(state):
    taken = list(state["stars"]) + [(p["x"], p["y"]) for p in state["pickups"]]
    x, y = find_free_spot(
        state["field"], state["player"], state["guards"], taken
    )

    kind = choose_pickup_kind(state)

    state["pickups"].append(
        {
            "kind": kind,
            "x": x,
            "y": y,
            "born": state["time"],
            "life": COIN_LIFE if kind == "coin" else PICKUP_LIFE,
        }
    )


def collect_pickup(state, pickup):
    kind = pickup["kind"]
    x, y = pickup["x"], pickup["y"]
    color = PICKUP_COLORS[kind]
    character = state["character"]

    if kind == "energy":
        state["energy"] = min(MAX_ENERGY, state["energy"] + ENERGY_PICKUP)
        add_popup(state, "+ENERGY", x, y - 18, color)
        state["sfx"].append("pickup")

    elif kind == "heart":
        state["lives"] = min(state["max_lives"], state["lives"] + 1)
        add_popup(state, "+1 LIFE", x, y - 18, color)
        state["sfx"].append("heart")

    elif kind == "shield":
        state["shield_until"] = state["time"] + character["shield_time"]
        state["shield_total"] = character["shield_time"]
        add_popup(state, "SHIELD!", x, y - 18, color)
        state["sfx"].append("shield")

    elif kind == "points":
        state["points"] += EXTRA_POINTS
        add_popup(state, f"+{EXTRA_POINTS}", x, y - 18, color)
        state["sfx"].append("pickup")

    elif kind == "coin":
        state["rare_coins"] = int(state.get("rare_coins", 0)) + 1
        state["points"] += COIN_POINTS
        add_popup(state, "+1 RARE COIN", x, y - 18, (220, 170, 255))
        state["sfx"].append("coin")
        
    elif kind == "freeze":
        state["freeze_until"] = state["time"] + TIME_FREEZE_DURATION
        state["freeze_message_until"] = state["time"] + 1.5
        add_popup(
            state,
            "TIME FREEZE!",
            x,
            y - 18,
            (80, 220, 255),
        )
        state["sfx"].append("shield")


    spawn_collection_effect(state, x, y, [color, WHITE, GOLD_LIGHT])


def handle_guard_hit(state, hit_player=1):
    """Handle guard hit for either player 1 or player 2."""
    now = state["time"]
    player = state["player"]
    field = state["field"]

    if hit_player == 2:
        player = state["player2"]
        invuln_key = "invulnerable_until2"
        shield_key = "shield_until2"
        hit_flash_key = "hit_flash_until2"
        lives_key = "lives2"
    else:
        invuln_key = "invulnerable_until"
        shield_key = "shield_until"
        hit_flash_key = "hit_flash_until"
        lives_key = "lives"

    if now < state[invuln_key]:
        return

    # Shield absorbs one hit.
    if state[shield_key] > now:
        state[shield_key] = 0.0
        state[invuln_key] = now + SHIELD_BREAK_COOLDOWN
        add_popup(state, "BLOCKED!", player.centerx, player.top - 14, (120, 205, 255))
        spawn_collection_effect(
            state, player.centerx, player.centery,
            [(90, 190, 255), WHITE, (170, 225, 255)],
        )
        state["sfx"].append("shield_break")
        return

    state[lives_key] -= 1
    state[invuln_key] = now + HIT_COOLDOWN
    state[hit_flash_key] = now + 0.25
    state["shake_until"] = now + 0.2
    state["sfx"].append("hit")

    reset_player_position(state)
    state["round_phase"] = "outbound"


    if state["lives"] <= 0 or (hit_player == 2 and state.get("lives2", 0) <= 0):
        state["status"] = "lost"
        state["sfx"].append("game_over")



    field = state["field"]
    player = state["player"]

    for guard in state["guards"]:
        rect = guard["rect"]
        pos = guard["pos"]
        kind = guard["kind"]

       
def update_guards(state, dt):
    field = state["field"]
    player = state["player"]

    # Stop all guards while the freeze token is active.
    if state["time"] < state.get("freeze_until", 0.0):
        return

    for guard in state["guards"]:
        rect = guard["rect"]
        pos = guard["pos"]
        kind = guard["kind"]

        if kind == "h":
            pos[0] += guard["speed"] * guard["direction"] * dt

            if pos[0] <= field.left:
                pos[0] = float(field.left)
                guard["direction"] = 1
            elif pos[0] + rect.width >= field.right:
                pos[0] = float(field.right - rect.width)
                guard["direction"] = -1

        elif kind == "v":
            pos[1] += guard["speed"] * guard["direction"] * dt

            if pos[1] <= field.top:
                pos[1] = float(field.top)
                guard["direction"] = 1
            elif pos[1] + rect.height >= field.bottom:
                pos[1] = float(field.bottom - rect.height)
                guard["direction"] = -1

        else:
            dx = player.centerx - (pos[0] + rect.width / 2)
            dy = player.centery - (pos[1] + rect.height / 2)
            distance = math.hypot(dx, dy)

            if distance > 1:
                pos[0] += dx / distance * guard["speed"] * dt
                pos[1] += dy / distance * guard["speed"] * dt

            pos[0] = max(
                float(field.left),
                min(pos[0], float(field.right - rect.width)),
            )
            pos[1] = max(
                float(field.top),
                min(pos[1], float(field.bottom - rect.height)),
            )

        rect.x = round(pos[0])
        rect.y = round(pos[1])



def update_game(state, keys, width, height):
    if state["status"] != "playing":
        return

    now_ticks = pygame.time.get_ticks()

    # Delta time makes movement less dependent on frame rate.
    previous_update = state.get("last_update", now_ticks)
    dt = min((now_ticks - previous_update) / 1000.0, 0.05)
    state["last_update"] = now_ticks

    state["time"] += dt
    now = state["time"]

    # Time Attack ends when its 60-second countdown reaches zero.
    # The player keeps the points earned during the run.
    if state.get("mode") == "time_attack" and now >= state.get("time_limit", 60.0):
        state["status"] = "won"
        state["bonus_points"] = state["lives"] * 50
        state["points"] += state["bonus_points"]
        state["bonus_coins"] = 1 if state["points"] >= 500 else 0
        state["sfx"].append("victory")
        return

    update_effects(state, dt)
    state["movement_time"] += dt

    player = state["player"]
    field = state["field"]
    character = state["character"]

    # ------------------------------------------
    # INPUT & MOVEMENT
    # ------------------------------------------
    dx = 0.0
    dy = 0.0

    # Player 1 Controls (WASD)
    if keys[pygame.K_a]: dx -= 1
    if keys[pygame.K_d]: dx += 1
    if keys[pygame.K_w]: dy -= 1
    if keys[pygame.K_s]: dy += 1

    if dx != 0 and dy != 0:
        factor = 1 / math.sqrt(2)
        dx *= factor
        dy *= factor

    moving = dx != 0 or dy != 0
    state["moving"] = moving
    state["move_direction"] = (dx, dy)
    if moving:
        state["dash_dir"] = (dx, dy)
        state["movement_time"] += dt

    # Player 2 Controls (Arrows)
    dx2, dy2 = 0.0, 0.0
    if state.get("mode") == "coop":
        if keys[pygame.K_LEFT]: dx2 -= 1
        if keys[pygame.K_RIGHT]: dx2 += 1
        if keys[pygame.K_UP]: dy2 -= 1
        if keys[pygame.K_DOWN]: dy2 += 1

        if dx2 != 0 and dy2 != 0:
            factor = 1 / math.sqrt(2)
            dx2 *= factor
            dy2 *= factor

        state["moving2"] = (dx2 != 0 or dy2 != 0)
        state["move_direction2"] = (dx2, dy2)
        if state["moving2"]:
            state["dash_dir2"] = (dx2, dy2)
            state["movement_time2"] = state.get("movement_time2", 0.0) + dt

    # ------------------------------------------
    # SKILLS & DASH
    # ------------------------------------------
    # Player 1 Skills
    dash_down = bool(keys[pygame.K_SPACE])
    if (
        not state["dash_key_down"]
        and dash_down
        and now >= state["dash_ready"]
    ):
        if character["id"] == "charles":
            state["dash_until"] = now + DASH_TIME
            state["dash_ready"] = now + 3.0
            state["sfx"].append("dash")
        elif character["id"] == "reian":
            throw_slipper(state, player.centerx, player.centery, state.get("move_direction", (0, -1)))
            state["dash_ready"] = now + 8.0
            state["sfx"].append("dash")
        elif character["id"] == "carlo":
            state["shield_until"] = now + 4.0
            state["shield_total"] = 4.0
            state["dash_ready"] = now + 10.0
            state["sfx"].append("pickup")
    state["dash_key_down"] = dash_down

    # Player 2 Skills
    if state.get("mode") == "coop":
        dash_down2 = bool(keys[pygame.K_RETURN])
        if (
            not state.get("dash_key_down2", False)
            and dash_down2
            and now >= state.get("dash_ready2", 0.0)
        ):
            if character["id"] == "charles":
                state["dash_until2"] = now + DASH_TIME
                state["dash_ready2"] = now + 3.0
                state["sfx"].append("dash")
            elif character["id"] == "reian":
                throw_slipper(state, state["player2"].centerx, state["player2"].centery, state.get("move_direction2", (0, -1)))
                state["dash_ready2"] = now + 8.0
                state["sfx"].append("dash")
            elif character["id"] == "carlo":
                state["shield_until"] = now + 4.0
                state["shield_total"] = 4.0
                state["dash_ready2"] = now + 10.0
                state["sfx"].append("pickup")
        state["dash_key_down2"] = dash_down2

    # ------------------------------------------
    # POSITION UPDATES (Apply speed and dt)
    # ------------------------------------------
    base_spd = character.get("base_speed", 240.0)

    # Player 1
    spd1 = base_spd
    sprint1 = keys[pygame.K_LSHIFT] and state["moving"] and state["energy"] > 0
    state["sprinting"] = sprint1
    if sprint1:
        spd1 *= character["sprint_mult"]
        state["energy"] = max(0.0, state["energy"] - character["sprint_drain"] * dt)
    elif state["moving"]:
        state["energy"] = min(MAX_ENERGY, state["energy"] + ENERGY_REGEN * dt)

    if now < state["dash_until"]: spd1 *= DASH_SPEED_MULT
    
    state["player_pos"][0] += state["move_direction"][0] * spd1 * dt
    state["player_pos"][1] += state["move_direction"][1] * spd1 * dt
    player.x = int(state["player_pos"][0])
    player.y = int(state["player_pos"][1])
    player.clamp_ip(field)
    state["player_pos"][0] = float(player.x)
    state["player_pos"][1] = float(player.y)

    # Player 2
    if state.get("mode") == "coop":
        player2 = state["player2"]
        spd2 = base_spd
        sprint2 = keys[pygame.K_RSHIFT] and state["moving2"] and state["energy"] > 0
        state["sprinting2"] = sprint2
        if sprint2:
            spd2 *= character["sprint_mult"]
            state["energy"] = max(0.0, state["energy"] - character["sprint_drain"] * dt)

        if now < state.get("dash_until2", 0.0): spd2 *= DASH_SPEED_MULT
        
        state["player_pos2"][0] += state["move_direction2"][0] * spd2 * dt
        state["player_pos2"][1] += state["move_direction2"][1] * spd2 * dt
        player2.x = int(state["player_pos2"][0])
        player2.y = int(state["player_pos2"][1])
        player2.clamp_ip(field)
        state["player_pos2"][0] = float(player2.x)
        state["player_pos2"][1] = float(player2.y)


    # ------------------------------------------
    # PATINTERO ROUND-TRIP (Classic and Defender modes)
    # ------------------------------------------
    if state.get("mode") != "time_attack" and state["round_phase"] == "outbound" and player.top <= field.top + 2:
        state["round_phase"] = "return"
        add_popup(
            state,
            "ENDPOINT! RETURN TO START!",
            player.centerx,
            player.centery - 25,
            (120, 255, 160),
        )
        state["sfx"].append("star")
        state["points"] += 100
        add_popup(
            state,
            "+100 PTS",
            player.centerx,
            player.centery - 45,
            (255, 255, 0),
        )
        
    if state.get("mode") != "time_attack" and state["round_phase"] == "return" and player.bottom >= field.bottom - 10:
        state["round"] += 1
        state["round_phase"] = "outbound"

        if state["round"] <= state["total_rounds"]:
            reset_player_position(state)
            add_popup(
                state,
                f"ROUND {state['round']}/{state['total_rounds']}!",
                player.centerx,
                player.centery - 25,
                (120, 255, 160),
            )
        else:
            state["round"] = state["total_rounds"] + 1


    # ------------------------------------------
    # GUARDS
    # ------------------------------------------
    update_guards(state, dt)

    # Check collision for player 1
    for guard in state["guards"]:
        if player.colliderect(guard["rect"].inflate(-6, -6)):
            handle_guard_hit(state, hit_player=1)
            break

    if state["status"] != "playing":
        return

    # Check collision for player 2 (coop mode)
    if state.get("mode") == "coop" and state.get("player2"):
        player2 = state["player2"]
        for guard in state["guards"]:
            if player2.colliderect(guard["rect"].inflate(-6, -6)):
                handle_guard_hit(state, hit_player=2)
                break

    if state["status"] != "playing":
        return

    # ------------------------------------------
    # STARS
    # ------------------------------------------
    remaining_stars = []

    for x, y in state["stars"]:
        star_rect = pygame.Rect(x - 12, y - 12, 24, 24)

        collected = False
        if player.colliderect(star_rect):
            state["stars_collected"] += 1
            state["points"] += STAR_POINTS
            spawn_collection_effect(state, x, y)
            add_popup(state, f"+{STAR_POINTS}", x, y - 18, YELLOW)
            state["sfx"].append("star")
            collected = True
        elif state.get("mode") == "coop" and state.get("player2") and state["player2"].colliderect(star_rect):
            state["stars_collected"] += 1
            state["points"] += STAR_POINTS
            spawn_collection_effect(state, x, y)
            add_popup(state, f"+{STAR_POINTS}", x, y - 18, YELLOW)
            state["sfx"].append("star")
            collected = True

        if not collected:
            remaining_stars.append((x, y))

    state["stars"] = remaining_stars

    # ------------------------------------------
    # PICKUPS
    # ------------------------------------------
    state["spawn_timer"] -= dt

    if state["spawn_timer"] <= 0 and len(state["pickups"]) < MAX_PICKUPS:
        spawn_pickup(state)
        state["spawn_timer"] = state["map"]["spawn_every"] * random.uniform(0.8, 1.2)

    remaining_pickups = []

    for pickup in state["pickups"]:
        age = now - pickup["born"]

        if age >= pickup["life"]:
            continue

        pickup_rect = pygame.Rect(pickup["x"] - 14, pickup["y"] - 14, 28, 28)

        collected = False
        if player.colliderect(pickup_rect):
            collect_pickup(state, pickup)
            collected = True
        elif state.get("mode") == "coop" and state.get("player2") and state["player2"].colliderect(pickup_rect):
            collect_pickup(state, pickup)
            collected = True

        if not collected:
            remaining_pickups.append(pickup)

    state["pickups"] = remaining_pickups

       # ------------------------------------------
    # WIN
    # Victory after completing all 3 round trips.
    if state.get("mode") != "time_attack" and state["round"] > state["total_rounds"]:
        state["status"] = "won"

        time_bonus = max(0, 90 - int(now)) * 5
        life_bonus = state["lives"] * 150

        state["bonus_points"] = time_bonus + life_bonus
        state["points"] += state["bonus_points"]
        state["bonus_coins"] = WIN_COIN_BONUS
        state["sfx"].append("victory")

# ==================================================
# BACK BUTTON
# ==================================================

def draw_game_menu(surface):
    width, height = surface.get_size()
    rect = get_game_back_rect(width, height)

    pygame.draw.rect(surface, DARK_GREEN, rect, border_radius=10)
    pygame.draw.rect(surface, CREAM, rect, width=2, border_radius=10)

    draw_text(surface, "ESC: BACK TO MENU", SMALL_FONT, WHITE, rect.center)


def get_game_back_rect(width, height):
    return pygame.Rect(
        width // 2 - 110,
        height - 48,
        220,
        36,
    )
