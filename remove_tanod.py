import re

# Read the file
with open('screens/game_screen.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the tanod elif block in make_guards
content = content.replace(
    '        elif kind == "tanod":\n            cx = field.left + spec["start"] * field.width\n            cy = field.top + spec["f"] * field.height\n',
    ''
)

# Remove the tanod-specific guard_data code
content = content.replace(
    '        # Pass extra parameters for tanod\n        if kind == "tanod":\n            guard_data["start_x"] = cx\n            guard_data["patrol_axis"] = spec.get("patrol_axis", "h")\n            guard_data["detection_range"] = spec.get("detection_range", 200)\n\n',
    ''
)

# Write the file back
with open('screens/game_screen.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done removing tanod from make_guards")