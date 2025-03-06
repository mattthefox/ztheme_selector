import os
import subprocess
import configparser
import curses
import shutil

DIR = "/home/mantra/Config/polybar"
UPDATERS_DIR = "/home/mantra/.local/share/applications/theme_updaters"
CONFIG = os.path.join(DIR, "config.ini")
THEME_DIR = os.path.join(DIR, "themes")

# Basic injector types.


class Injector:
    def __init__(self, file_path, theme_colors):
        if file_path[0] == ".":
            self.file_path = file_path.replace(".", DIR, 1)
        else:
            self.file_path = file_path
        self.theme_colors = theme_colors
        self.load()

    # Basic methods
    def load(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    def inject(self):
        return self.lines

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.writelines(self.lines)

    # Shared methods
    def replaceLine(self, pattern, line, replacement):
        if 0 <= (line - 1) < len(self.lines):
            self.lines[line - 1] = pattern.replace("<x>", replacement) + "\n"
        return self.lines

class ReplaceLineInjector(Injector):
    def __init__(self, file_path, search_pattern, line_number, replacement):
        super().__init__(file_path, {})
        self.search_pattern = search_pattern
        self.line_number = line_number 
        self.replacement = replacement

    def inject(self):
        super().replaceLine(self.search_pattern, self.line_number, self.replacement)
        return self.lines

class RofiInjector(Injector):
    def __init__(self, file_path, theme_colors):
        super().__init__(file_path, theme_colors)

    def inject(self):
        print(self.theme_colors)
        super().replaceLine("\tbg-col: <x>;", 2, self.theme_colors["base"])        # Replaces the background color with base
        super().replaceLine("\tbg-col-light: <x>;", 4, self.theme_colors["subtle"]) # Replaces the light background color
        super().replaceLine("\tborder-col: <x>;", 5, self.theme_colors["surface"])  # Replaces the border color
        super().replaceLine("\tselected-col: <x>;", 6, self.theme_colors["accent"]) # Replaces the selected color
        super().replaceLine("\tblue: <x>;", 7, self.theme_colors["accent"])         # Replaces the blue color
        super().replaceLine("\tfg-col: <x>;", 8, self.theme_colors["muted"])         # Replaces the foreground color 1
        super().replaceLine("\tfg-col2: <x>;", 9, self.theme_colors["text"])         # Replaces the foreground color 2
        return self.lines

class ColorDictInjector(Injector):
    def __init__(self, file_path, theme_colors, mapping):
        super().__init__(file_path, theme_colors)
        self.mapping = mapping

    def inject(self):
        # Check if the backup already exists
        self.backup_file_path = self.file_path + ".themebak"
        if not os.path.exists(self.backup_file_path):
            # If not, create the backup file
            shutil.copy(self.file_path, self.backup_file_path)
        
        # Open the backup file and apply replacements
        with open(self.backup_file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

        # Perform replacements based on the mapping
        for color_name, color_value in self.mapping.items():
            # Iterate over each line and replace the color name with the corresponding hex value
            self.lines = [line.replace(color_value.upper(), self.theme_colors[color_name].upper()) for line in self.lines]

        return self.lines


# Check if the directory exists
if not os.path.isdir(THEME_DIR):
    print("Theme directory not found!")
    exit(1)

# List theme files and extract their first lines
themes = []
for root, _, files in os.walk(THEME_DIR):
    for file in files:
        theme_path = os.path.join(root, file)
        themes.append(theme_path)

if len(themes) == 0:
    print("No themes found!")
    exit(1)

# Display themes with the first line as the description for the user to select
def select_theme(stdscr):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()
    stdscr.addstr(0, 0, "Select a theme using arrow keys and press Enter:")

    for i, theme in enumerate(themes, 1):
        with open(theme, 'r') as f:
            first_line = f.readline().strip()[1:]  # Remove the first character
        themes[i-1] = (theme, first_line)

    current_row = 0
    while True:
        # Display themes with an arrow indicating the selected one
        for idx, (theme, description) in enumerate(themes):
            if idx == current_row:
                stdscr.addstr(2 + idx, 0, f"-> {description}")  # Arrow at the selected theme
            else:
                stdscr.addstr(2 + idx, 0, f"   {description}")  # Normal theme line

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(themes) - 1:
            current_row += 1
        elif key == 10:  # Enter key
            break

        stdscr.refresh()

    return themes[current_row][0]  # Return the selected theme's path

# Initialize curses and select theme
selected_theme = curses.wrapper(select_theme)

# Continue the original logic to read the selected theme and update configs
config = configparser.ConfigParser()
config.read(selected_theme)
theme_data = {section: dict(config[section]) for section in config.sections()}

print(f"You selected: {selected_theme}")

# Update configs
injectors = [
    ReplaceLineInjector("./config.ini", "include-file=<x>", 1, selected_theme),
    ReplaceLineInjector("./modules/polywins.sh", "ini_file=<x>", 4, selected_theme),
    ReplaceLineInjector("./modules/polybar-now-playing", "theme = \"<x>\"", 14, selected_theme),
    RofiInjector("/home/mantra/.local/share/rofi/themes/catppuccin-mocha.rasi", theme_data["colors"]),
    ColorDictInjector("/home/mantra/.vscode/extensions/catppuccin.catppuccin-vsc-3.16.1/themes/mocha.json", theme_data["colors"],
                      {
                        "crust": "#11111b",
                        "base": "#1e1e2e",
                        "surface": "#313244",
                        "overlay": "#6c7086",
                        "subtle": "#9399b2",
                        "muted": "#bac2de",
                        "text": "#cdd6f4",
                        "purple": "#cba6f7",
                        "blue": "#89b4fa",
                        "green": "#a6e3a1",
                        "yellow": "#f9e2af",
                        "orange": "#fab387",
                        "red": "#f38ba8"
                      }) # VSCode Catpuccin Mocha Injector
]


for injector in injectors:
    injector.lines = injector.inject()
    injector.save()

# Reboot polybar
subprocess.run(["killall", "polybar"])
subprocess.run(["nohup", os.path.join(DIR, "launch.sh")])
