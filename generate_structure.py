import os

# Define the folder structure
structure = {
    "angels_and_demons_game": [
        "main.py",
        "config.py",
        "constants.py",
        "models/player.py",
        "models/game_state.py",
        "models/history.py",
        "mechanics/effects.py",
        "mechanics/randomizer.py",
        "mechanics/logic.py",
        "ui/menu.py",
        "ui/custom_setup.py",
        "ui/game_screen.py",
        "ui/histories_screen.py",
        "data/histories.json",
        "data/saved_sets.json",
        "assets/images/.gitkeep",
        "assets/sounds/.gitkeep"
    ]
}

# Create folders and empty files
base_path = "."

for root, files in structure.items():
    full_root_path = os.path.join(base_path, root)
    os.makedirs(full_root_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(full_root_path, file)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                if file.endswith(".py"):
                    f.write(f"# {os.path.basename(file)} - auto-generated\n")
                elif file.endswith(".json"):
                    f.write("[]\n" if "histories" in file else "{}\n")
                else:
                    f.write("")

f"✅ Đã tạo xong cấu trúc thư mục cho game tại: {os.path.join(base_path, 'angels_and_demons_game')}"
