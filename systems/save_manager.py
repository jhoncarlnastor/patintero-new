
import json
import os

# ==================================================
# PATINTERO: GRID RUSH - SAVE SYSTEM
# ==================================================

SAVE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "savegame.json",
)

DEFAULT_SAVE = {
    "rare_coins": 0,
    "owned": ["charles"],
    "selected": "charles",
    "unlocked_maps": 1,
    "best": {},
}

# Convert old character IDs from existing save files.
OLD_CHARACTER_IDS = {
    "batang_kalye": "reian",
    "mabilis_runner": "charles",
    "barangay_tanod": "carlo",
}


def load_save():
    data = json.loads(json.dumps(DEFAULT_SAVE))

    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as file:
            loaded = json.load(file)

        if isinstance(loaded, dict):
            for key in DEFAULT_SAVE:
                if key in loaded:
                    data[key] = loaded[key]

    except (OSError, ValueError):
        pass

    # Migrate old character IDs.
    if not isinstance(data.get("owned"), list):
        data["owned"] = ["charles"]

    data["owned"] = list(dict.fromkeys(
        OLD_CHARACTER_IDS.get(character_id, character_id)
        for character_id in data["owned"]
    ))

    # Charles is always the default selected character.
    data["selected"] = "charles"
    
    # Charles is always owned because he is the free character.
    if "charles" not in data["owned"]:
        data["owned"].append("charles")

    data["unlocked_maps"] = max(1, int(data["unlocked_maps"]))
    data["rare_coins"] = max(0, int(data["rare_coins"]))

    return data


def save_game(data):
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
    except OSError:
        # The game still works if saving is not possible.
        pass
