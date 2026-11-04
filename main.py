
import sys
import pygame

from screens.menu import draw_menu, init_menu_fonts, draw_mode_select
from screens.character_select import (
    CHARACTERS,
    COIN_IMAGE,
    draw_character_select,
    init_character_fonts,
)
from screens.helpers import (
    draw_bolt_icon,
    draw_coin_icon,
    draw_gem_icon,
    draw_heart_icon,
    draw_shield_icon,
)
from systems.audio import init_audio, play_sound, toggle_mute, is_muted
from systems.save_manager import load_save, save_game
from screens.level_map import (
    LEVELS,
    draw_level_map,
    init_level_map_fonts,
)
from screens.game_screen import (
    create_game_state,
    draw_game_screen,
    draw_game_menu,
    get_game_back_rect,
    init_game_fonts,
    update_game,
)

# ==================================================
# PATINTERO: GRID RUSH
# Pause Menu + Results Screen + Shop + Map unlocking
# ==================================================

pygame.init()
import os

icon_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "assets",
    "game_icon.png"
)

try:
    game_icon = pygame.image.load(icon_path)
    pygame.display.set_icon(game_icon)
except (FileNotFoundError, pygame.error):
    print("Game icon not found. Using default window icon.")

WIDTH = 1000
HEIGHT = 650
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Patintero: Grid Rush")

# Set custom game window icon
try:
    icon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets", "game_icon.png"
    )
    game_icon = pygame.image.load(icon_path).convert_alpha()
    pygame.display.set_icon(game_icon)
except (pygame.error, OSError) as e:
    print(f"Game icon could not be loaded: {e}")

clock = pygame.time.Clock()

init_menu_fonts()
init_character_fonts()
init_level_map_fonts()
init_game_fonts()
init_audio()
# Main menu and pause/results background music
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_MUSIC = os.path.join(BASE_DIR, "assets", "audio", "menu_music.mp3")

try:
    pygame.mixer.music.load(MENU_MUSIC)
    pygame.mixer.music.set_volume(0.35)
    pygame.mixer.music.play(-1)
    print("Background music loaded.")
except (pygame.error, OSError) as e:
    print(f"Background music could not be loaded: {e}")

# Colors
SKY = (123, 205, 230)
CREAM = (255, 246, 218)
DARK_GREEN = (30, 105, 57)
DARK = (35, 65, 54)
WHITE = (255, 255, 255)
YELLOW = (255, 205, 75)
RED = (205, 58, 52)
PANEL = (20, 38, 32)
J_RED = (214, 60, 52)
J_BLUE = (47, 110, 190)
J_GREEN = (40, 150, 90)
J_ORANGE = (236, 138, 36)

TITLE_FONT = pygame.font.SysFont("arial", 42, bold=True)
BODY_FONT = pygame.font.SysFont("arial", 23, bold=True)
SMALL_FONT = pygame.font.SysFont("arial", 17)
BUTTON_FONT = pygame.font.SysFont("arial", 22, bold=True)

# Game state
current_screen = "menu"
game_mode = "classic"
running = True

save_data = load_save()

selected_character = None
selected_level = None
selected_level_index = 0
current_map_carousel_index = 0

game_state = None

shop_message = ""
shop_message_until = 0
new_unlock_name = None

paused = False
pause_started = 0
paused_total = 0

buttons = {}
character_buttons = {}
map_buttons = {}
mode_buttons = {}


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def draw_text(text, font, color, center):
    image = font.render(text, True, color)
    screen.blit(image, image.get_rect(center=center))


def make_button(text, rect, mouse_position, enabled=True):
    hovered = rect.collidepoint(mouse_position) and enabled

    if not enabled:
        color = (100, 110, 105)
    elif hovered:
        color = YELLOW
    else:
        color = DARK_GREEN

    text_color = DARK if hovered else WHITE

    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(
        screen,
        CREAM,
        rect,
        width=2,
        border_radius=12,
    )

    draw_text(text, SMALL_FONT, text_color, rect.center)


def draw_overlay():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((8, 20, 15, 205))
    screen.blit(overlay, (0, 0))


def format_time(seconds):
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"


def draw_text_left(text, font, color, x, y):
    image = font.render(text, True, color)
    screen.blit(image, image.get_rect(midleft=(x, y)))


def get_elapsed_seconds():
    # The game keeps its own clock, so the time stops
    # while paused and after the level ends.
    if game_state is None:
        return 0

    return int(game_state["time"])


def get_current_character():
    for character in CHARACTERS:
        if character["id"] == save_data["selected"]:
            return character

    return CHARACTERS[0]


def start_new_game():
    global game_state, current_screen
    global paused, pause_started, paused_total
    global new_unlock_name

    new_unlock_name = None

    game_state = create_game_state(
        WIDTH,
        HEIGHT,
        selected_level,
        get_current_character(),
        game_mode,
    )

    paused = False
    pause_started = 0
    paused_total = 0

    current_screen = "game"


def finalize_game():
    # Runs once when a level ends: bank coins, unlock the next map,
    # and save the best score.
    global new_unlock_name

    state = game_state

    if state is None or state["finalized"]:
        return

    state["finalized"] = True

    earned = state["rare_coins"]

    if state["status"] == "won":
        earned += state["bonus_coins"]
        if game_mode == "classic":
            next_index = selected_level_index + 1

            if (
                next_index < len(LEVELS)
                and save_data["unlocked_maps"] < next_index + 1
            ):
                save_data["unlocked_maps"] = next_index + 1
                new_unlock_name = LEVELS[next_index]["name"]
                play_sound("unlock")
        map_id = selected_level["id"]
        best = save_data["best"].get(map_id, 0)

        if state["points"] > best:
            save_data["best"][map_id] = state["points"]

    state["coins_earned"] = earned
    save_data["rare_coins"] = int(save_data.get("rare_coins", 0)) + earned
    save_game(save_data)


def return_to_menu():
    global current_screen, paused
    paused = False
    current_screen = "menu"


# ==================================================
# PAUSE MENU
# ==================================================

def draw_pause_menu(mouse_position):
    draw_overlay()

    panel = pygame.Rect(300, 145, 400, 365)

    pygame.draw.rect(
        screen,
        CREAM,
        panel,
        border_radius=24,
    )

    pygame.draw.rect(
        screen,
        DARK_GREEN,
        panel,
        width=4,
        border_radius=24,
    )

    draw_text(
        "GAME PAUSED",
        TITLE_FONT,
        DARK_GREEN,
        (WIDTH // 2, 195),
    )

    draw_text(
        "Take a break, runner!",
        SMALL_FONT,
        DARK,
        (WIDTH // 2, 235),
    )

    resume_rect = pygame.Rect(365, 275, 270, 48)
    restart_rect = pygame.Rect(365, 338, 270, 48)
    menu_rect = pygame.Rect(365, 401, 270, 48)

    make_button("RESUME  [P]", resume_rect, mouse_position)
    make_button("RESTART GAME", restart_rect, mouse_position)
    make_button("MAIN MENU", menu_rect, mouse_position)

    return {
        "resume": resume_rect,
        "restart": restart_rect,
        "menu": menu_rect,
    }


# ==================================================
# RESULTS SCREEN
# ==================================================

def draw_results_screen(mouse_position):
    draw_overlay()

    won = game_state["status"] == "won"
    has_next = (
        won
        and selected_level_index + 1 < len(LEVELS)
    )

    panel = pygame.Rect(225, 70, 550, 520)

    # Drop shadow for the panel
    shadow = pygame.Rect(panel.x + 6, panel.y + 8, panel.width, panel.height)
    pygame.draw.rect(screen, (0, 0, 0, 100), shadow, border_radius=26)
    
    # Main panel background
    pygame.draw.rect(screen, CREAM, panel, border_radius=26)
    
    # Retro arcade thick border
    pygame.draw.rect(screen, DARK, panel, width=6, border_radius=26)
    pygame.draw.rect(screen, DARK_GREEN, panel, width=2, border_radius=26)

    title = "LEVEL COMPLETE!" if won else "GAME OVER"
    title_color = DARK_GREEN if won else RED

    # Title with drop shadow
    draw_text(title, TITLE_FONT, (20, 20, 20, 180), (WIDTH // 2 + 3, 118 + 3))
    draw_text(title, TITLE_FONT, title_color, (WIDTH // 2, 118))

    subtitle = (
        f"{selected_level['name']} cleared. Great run!"
        if won
        else "Keep practicing. You can do it!"
    )

    draw_text(subtitle, SMALL_FONT, DARK, (WIDTH // 2, 162))

    # Score summary panel
    score_rect = pygame.Rect(265, 190, 470, 130)

    pygame.draw.rect(screen, (220, 215, 195), score_rect, border_radius=18)
    pygame.draw.rect(screen, DARK_GREEN, score_rect, width=3, border_radius=18)

    draw_text("FINAL SCORE", SMALL_FONT, DARK_GREEN, (WIDTH // 2, 212))
    draw_text(
        f"{game_state['points']} PTS",
        BODY_FONT,
        DARK_GREEN,
        (WIDTH // 2, 242),
    )

    # Stats row - balanced spacing
    stars_y = 275
    draw_text(
        f"STARS  {game_state['stars_collected']}  /  {game_state['total_stars']}",
        SMALL_FONT,
        DARK,
        (WIDTH // 2, stars_y),
    )

    elapsed = get_elapsed_seconds()
    time_y = 305
    draw_text(
        f"TIME PLAYED: {format_time(elapsed)}      LIVES LEFT: {max(0, game_state['lives'])}",
        SMALL_FONT,
        DARK,
        (WIDTH // 2, time_y),
    )

    if won:
        draw_text(
            f"Win bonus: +{game_state['bonus_points']} pts",
            SMALL_FONT,
            DARK_GREEN,
            (WIDTH // 2, 332),
        )

    # Rare coins earned
    earned = game_state.get("coins_earned", 0)

    draw_coin_icon(screen, WIDTH // 2 - 105, 368, 11, pygame.time.get_ticks() / 300)
    draw_text(
        f"+{earned} RARE COINS   (TOTAL {save_data['rare_coins']})",
        SMALL_FONT,
        (130, 60, 190),
        (WIDTH // 2 + 20, 368),
    )

    if new_unlock_name:
        unlock_rect = pygame.Rect(285, 395, 430, 36)

        pygame.draw.rect(screen, YELLOW, unlock_rect, border_radius=12)
        draw_text(
            f"NEW MAP UNLOCKED: {new_unlock_name}",
            SMALL_FONT,
            DARK,
            unlock_rect.center,
        )

    buttons = {}

    # Retro arcade style buttons
    if has_next:
        next_rect = pygame.Rect(290, 455, 420, 52)
        retry_rect = pygame.Rect(290, 518, 195, 52)
        menu_rect = pygame.Rect(515, 518, 195, 52)

        make_button("NEXT MAP  >", next_rect, mouse_position)
        buttons["next"] = next_rect
    else:
        retry_rect = pygame.Rect(290, 475, 195, 52)
        menu_rect = pygame.Rect(515, 475, 195, 52)

    # Style buttons with arcade feel
    for btn_text, rect in [("RETRY", retry_rect), ("MAP SELECT", menu_rect)]:
        hover = rect.collidepoint(mouse_position)
        base_color = J_GREEN if btn_text == "RETRY" else J_BLUE
        hover_color = (min(255, base_color[0] + 30), min(255, base_color[1] + 30), min(255, base_color[2] + 30))
        color = hover_color if hover else base_color
        
        pygame.draw.rect(screen, color, rect, border_radius=14)
        pygame.draw.rect(screen, DARK, rect, width=4, border_radius=14)
        pygame.draw.rect(screen, (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)), 
                        rect.inflate(-8, -8), width=2, border_radius=10)
        
        draw_text(btn_text, BUTTON_FONT, WHITE, rect.center)
        
    buttons["retry"] = retry_rect
    buttons["menu"] = menu_rect

    return buttons


# ==================================================
# SIMPLE INFORMATION SCREEN
# ==================================================

def draw_message(title, subtitle, hint="Press ESC to return"):
    screen.fill(SKY)

    pygame.draw.circle(
        screen,
        YELLOW,
        (WIDTH - 85, 75),
        38,
    )

    pygame.draw.rect(
        screen,
        (85, 165, 85),
        (0, HEIGHT - 100, WIDTH, 100),
    )

    panel = pygame.Rect(
        WIDTH // 2 - 350,
        HEIGHT // 2 - 120,
        700,
        240,
    )

    pygame.draw.rect(
        screen,
        CREAM,
        panel,
        border_radius=24,
    )

    pygame.draw.rect(
        screen,
        DARK_GREEN,
        panel,
        width=4,
        border_radius=24,
    )

    draw_text(
        title,
        TITLE_FONT,
        DARK_GREEN,
        (WIDTH // 2, HEIGHT // 2 - 55),
    )

    draw_text(
        subtitle,
        BODY_FONT,
        DARK,
        (WIDTH // 2, HEIGHT // 2 + 5),
    )

    draw_text(
        hint,
        SMALL_FONT,
        DARK,
        (WIDTH // 2, HEIGHT // 2 + 65),
    )

import os

def load_instruction_sprite(filename, size=(76, 76)):
    """Load an existing character sprite without crashing if missing."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")

    for root, _, files in os.walk(assets_dir):
        for file in files:
            if file.lower() == filename.lower():
                path = os.path.join(root, file)
                try:
                    image = pygame.image.load(path).convert_alpha()
                    return pygame.transform.smoothscale(image, size)
                except (pygame.error, OSError):
                    return None

    return None


def draw_how_to_play(mouse_pos=None):
    screen.fill(SKY)

    # Main panel
    panel = pygame.Rect(100, 50, WIDTH - 200, HEIGHT - 100)
    pygame.draw.rect(screen, CREAM, panel, border_radius=22)
    pygame.draw.rect(screen, DARK_GREEN, panel, width=4, border_radius=22)

    # Title with shadow
    draw_text("HOW TO PLAY", TITLE_FONT, DARK, (WIDTH // 2 + 2, 102))
    draw_text("HOW TO PLAY", TITLE_FONT, DARK_GREEN, (WIDTH // 2, 100))

    draw_text("Collect all the stars and dodge the guards!", BODY_FONT, DARK, (WIDTH // 2, 150))
    
    draw_text(
        "P1: WASD / SHIFT (Sprint) / SPACE (Skill)   |   P2: Arrows / RSHIFT / ENTER",
        SMALL_FONT, DARK_GREEN, (WIDTH // 2, 185)
    )

    pygame.draw.line(screen, DARK_GREEN, (150, 210), (WIDTH - 150, 210), 2)

    # Power-ups Grid
    collectible_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets", "characters", "collectibles"
    )

    items = [
        ("coke-speed.png", "ENERGY", "Fills your sprint bar."),
        ("chippy-life.png", "HEART", "+1 extra life."),
        ("mikmik-shield.png", "SHIELD", "Blocks one guard hit."),
        ("tanzan-gem.png", "EXTRA PTS", "+10 bonus points."),
        ("coin.png", "RARE COIN", "Buy new characters."),
        ("freeze.png", "FREEZE", "Stops guards for 3s."),
    ]

    icon_x = 200
    name_x = 260
    desc_x = 450
    y = 260

    for filename, name, description in items:
        sprite_path = os.path.join(collectible_dir, filename)
        try:
            icon = pygame.image.load(sprite_path).convert_alpha()
            icon = pygame.transform.smoothscale(icon, (32, 32))
            screen.blit(icon, icon.get_rect(center=(icon_x, y)))
        except (pygame.error, OSError, FileNotFoundError):
            draw_text("?", SMALL_FONT, RED, (icon_x, y))

        draw_text_left(name, BODY_FONT, DARK_GREEN, name_x, y)
        draw_text_left(description, SMALL_FONT, DARK, desc_x, y)
        y += 45

    # Footer
    pygame.draw.line(screen, DARK_GREEN, (150, y + 10), (WIDTH - 150, y + 10), 2)
    draw_text("Guards, Slow Zones, and Unlockables await!", SMALL_FONT, DARK, (WIDTH // 2, y + 30))

    # Back Button - positioned lower to avoid overlap
    back_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT - 85, 160, 50)
    hover = back_rect.collidepoint(mouse_pos) if mouse_pos else False
    
    color = J_RED if hover else J_ORANGE
    pygame.draw.rect(screen, color, back_rect, border_radius=12)
    pygame.draw.rect(screen, DARK, back_rect, width=3, border_radius=12)
    
    draw_text("BACK", BUTTON_FONT, WHITE, back_rect.center)
    
    return {"back": back_rect}

    draw_text(
        "Unlock maps by completing the previous map!",
        SMALL_FONT, DARK, (WIDTH // 2, 551)
    )
    draw_text(
        "Press ESC to return",
        SMALL_FONT, DARK_GREEN, (WIDTH // 2, HEIGHT - 30)
    )



# ==================================================
# MAIN LOOP
# ==================================================

while running:
    mouse_position = pygame.mouse.get_pos()
        # Background music state controller
    should_play_music = (
        current_screen != "game"
        or paused
        or (game_state is not None and game_state["status"] != "playing")
    )

    if should_play_music:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)
    else:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

    # ----------------------------------------------
    # DRAW CURRENT SCREEN
    # ----------------------------------------------

    if current_screen == "menu":
        buttons = draw_menu(screen, mouse_position)
        character_buttons = {}
        map_buttons = {}

        # Rare coin counter
        pygame.draw.rect(screen, CREAM, (20, 18, 140, 34), border_radius=17)
        coin_sprite = pygame.transform.smoothscale(COIN_IMAGE, (24, 24))
        coin_rect = coin_sprite.get_rect(center=(42, 35))
        screen.blit(coin_sprite, coin_rect)

        draw_text(
             str(save_data["rare_coins"]),
             BODY_FONT,
             DARK_GREEN,
             (105, 35),
        )
    elif current_screen == "mode_select":
        mode_buttons = draw_mode_select(screen, mouse_position)
        buttons = {}
        character_buttons = {}
        map_buttons = {}

    elif current_screen == "character":
        message = (
            shop_message
            if pygame.time.get_ticks() < shop_message_until
            else ""
        )

        character_buttons = draw_character_select(
            screen,
            mouse_position,
            selected_character,
            save_data["owned"],
            save_data["rare_coins"],
            message,
        )

        buttons = {}
        map_buttons = {}
        mode_buttons = {}

    elif current_screen == "map":
        allowed_maps = (
            ["lote", "playground"]
            if game_mode in ("defender", "time_attack")
            else None
        )

        map_buttons = draw_level_map(
            screen,
            mouse_position,
            save_data["unlocked_maps"],
            save_data["best"],
            save_data["rare_coins"],
            allowed_maps,
            current_map_carousel_index,
        )

        buttons = {}
        character_buttons = {}
        mode_buttons = {}

    elif current_screen == "how_to_play":
        how_to_play_buttons = draw_how_to_play(mouse_position)

        buttons = {}
        character_buttons = {}
        map_buttons = {}
        mode_buttons = {}

    elif current_screen == "game":
        draw_game_screen(screen, game_state)
        draw_game_menu(screen)

        buttons = {}
        character_buttons = {}
        map_buttons = {}
        mode_buttons = {}

        if game_state["status"] != "playing":
            paused = False
            finalize_game()
            result_buttons = draw_results_screen(mouse_position)

        elif paused:
            pause_buttons = draw_pause_menu(mouse_position)

    # ----------------------------------------------
    # EVENTS
    # ----------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_m:
                toggle_mute()

            if current_screen == "game":

                if event.key == pygame.K_ESCAPE:
                    return_to_menu()

                elif (
                    event.key == pygame.K_p
                    and game_state["status"] == "playing"
                ):
                    if not paused:
                        paused = True
                        pause_started = pygame.time.get_ticks()
                    else:
                        paused_total += (
                            pygame.time.get_ticks() - pause_started
                        )
                        paused = False

                elif (
                    event.key == pygame.K_r
                    and game_state["status"] != "playing"
                ):
                    start_new_game()

            elif event.key == pygame.K_ESCAPE:
                if current_screen != "menu":
                    return_to_menu()
                else:
                    running = False

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):

            if current_screen == "menu":

                if buttons["play"].collidepoint(event.pos):
                    play_sound("click")
                    current_screen = "mode_select"

                elif buttons["map"].collidepoint(event.pos):
                    current_map_carousel_index = 0
                    current_screen = "map"

                elif buttons["how_to_play"].collidepoint(event.pos):
                    current_screen = "how_to_play"

                elif buttons["quit"].collidepoint(event.pos):
                    running = False

            elif current_screen == "mode_select":
                if mode_buttons["classic"].collidepoint(event.pos):
                    game_mode = "classic"
                elif mode_buttons["defender"].collidepoint(event.pos):
                    game_mode = "defender"
                elif mode_buttons["time_attack"].collidepoint(event.pos):
                    game_mode = "time_attack"
                elif mode_buttons["coop"].collidepoint(event.pos):
                    game_mode = "coop"
                elif mode_buttons["back"].collidepoint(event.pos):
                    current_screen = "menu"
                    continue
                else:
                    continue

                play_sound("click")
                selected_character = None
                for index, character in enumerate(CHARACTERS):
                    if character["id"] == save_data["selected"]:
                        selected_character = index
                        break
                current_screen = "character"

            elif current_screen == "character":


                if character_buttons["back"].collidepoint(event.pos):
                    current_screen = "mode_select"

                elif character_buttons["confirm"].collidepoint(event.pos):
                    if selected_character is not None:
                        chosen = CHARACTERS[selected_character]

                        if chosen["id"] in save_data["owned"]:
                            save_data["selected"] = chosen["id"]
                            save_game(save_data)
                            play_sound("click")
                            current_screen = "map"

                        elif save_data["rare_coins"] >= chosen["price"]:
                            save_data["rare_coins"] -= chosen["price"]
                            save_data["owned"].append(chosen["id"])
                            save_data["selected"] = chosen["id"]
                            save_game(save_data)
                            play_sound("buy")
                            shop_message = f"{chosen['name']} UNLOCKED!"
                            shop_message_until = pygame.time.get_ticks() + 2500

                        else:
                            need = chosen["price"] - save_data["rare_coins"]
                            play_sound("denied")
                            shop_message = f"Need {need} more rare coins!"
                            shop_message_until = pygame.time.get_ticks() + 2500

                else:
                    for index, rect in enumerate(
                        character_buttons["cards"]
                    ):
                        if rect.collidepoint(event.pos):
                            selected_character = index
                            break

            elif current_screen == "character":

                if character_buttons["back"].collidepoint(event.pos):
                    current_screen = "mode_select"

                elif character_buttons["confirm"].collidepoint(event.pos):
                    if selected_character is not None:
                        chosen = CHARACTERS[selected_character]

                        if chosen["id"] in save_data["owned"]:
                            save_data["selected"] = chosen["id"]
                            save_game(save_data)
                            play_sound("click")
                            current_screen = "map"

                        elif save_data["rare_coins"] >= chosen["price"]:
                            save_data["rare_coins"] -= chosen["price"]
                            save_data["owned"].append(chosen["id"])
                            save_data["selected"] = chosen["id"]
                            save_game(save_data)
                            play_sound("buy")
                            shop_message = f"{chosen['name']} UNLOCKED!"
                            shop_message_until = pygame.time.get_ticks() + 2500

                        else:
                            need = chosen["price"] - save_data["rare_coins"]
                            play_sound("denied")
                            shop_message = f"Need {need} more rare coins!"
                            shop_message_until = pygame.time.get_ticks() + 2500

                else:
                    for index, rect in enumerate(character_buttons["cards"]):
                        if rect.collidepoint(event.pos):
                            selected_character = index
                            break

            elif current_screen == "how_to_play":
                if how_to_play_buttons["back"].collidepoint(event.pos):
                    current_screen = "menu"
                    play_sound("click")

            elif current_screen == "map":
                # Carousel navigation
                if map_buttons["back"].collidepoint(event.pos):
                    play_sound("click")
                    current_screen = "menu"
                elif map_buttons["left"].collidepoint(event.pos):
                    total = map_buttons["total_maps"]
                    current_map_carousel_index = (
                        current_map_carousel_index - 1
                    ) % total
                    play_sound("click")
                elif map_buttons["right"].collidepoint(event.pos):
                    total = map_buttons["total_maps"]
                    current_map_carousel_index = (
                        current_map_carousel_index + 1
                    ) % total
                    play_sound("click")
                elif map_buttons.get("play") and map_buttons["play"].collidepoint(event.pos):
                    original_index = map_buttons["original_index"]
                    if game_mode in ("defender", "time_attack") or original_index < save_data["unlocked_maps"]:
                        selected_level = LEVELS[original_index]
                        selected_level_index = original_index
                        play_sound("click")
                        start_new_game()
                    else:
                        play_sound("denied")


            elif current_screen == "game":

                if game_state["status"] != "playing":
                    if (
                        "next" in result_buttons
                        and result_buttons["next"].collidepoint(event.pos)
                    ):
                        selected_level_index += 1
                        selected_level = LEVELS[selected_level_index]
                        start_new_game()

                    elif result_buttons["retry"].collidepoint(event.pos):
                        start_new_game()

                    elif result_buttons["menu"].collidepoint(event.pos):
                        current_screen = "map"

                elif paused:
                    if pause_buttons["resume"].collidepoint(event.pos):
                        paused_total += (
                            pygame.time.get_ticks() - pause_started
                        )
                        paused = False

                    elif pause_buttons["restart"].collidepoint(event.pos):
                        start_new_game()

                    elif pause_buttons["menu"].collidepoint(event.pos):
                        return_to_menu()

                elif get_game_back_rect(
                    WIDTH, HEIGHT
                ).collidepoint(event.pos):
                    return_to_menu()

    # ----------------------------------------------
    # UPDATE GAME
    # ----------------------------------------------

    if current_screen == "game" and not paused:
        if game_state["status"] == "playing":
            keys = pygame.key.get_pressed()
            update_game(game_state, keys, WIDTH, HEIGHT)

    # Play sound effects queued by the game
    if game_state is not None and game_state["sfx"]:
        for name in game_state["sfx"]:
            play_sound(name)

        game_state["sfx"].clear()

    pygame.display.flip()
    clock.tick(FPS)

# ==================================================
# SHUTDOWN
# ==================================================

pygame.quit()
sys.exit()
