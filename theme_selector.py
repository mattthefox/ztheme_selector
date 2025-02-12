import os
import subprocess
import json
import configparser
import pprint

DIR = "/home/mantra/Config/polybar"
UPDATERS_DIR = "/home/mantra/.local/share/applications/theme_updaters"
CONFIG = os.path.join(DIR, "config.ini")
THEME_DIR = os.path.join(DIR, "themes")

includeFileUpdaters = [
	{
		"path": "./config.ini",
		"updaters": [
			{"line": "include-file=<x>", "line_number": 0, "replaceWith": "themeFile"}
		]
	},
	{
		"path": "./modules/polywins.sh",
		"updaters": [
			{"line": "ini_file=<x>", "line_number": 3, "replaceWith": "themeFile"}
		]
	},
	{
		"path": "./modules/polybar-now-playing",
		"updaters": [
			{"line": 'theme = "<x>"', "line_number": 13, "replaceWith": "themeFile"}
		]
	},
	{
		"refer": "rofi.json"
	}
]

new_updaters = []
for updater in includeFileUpdaters:
    if isinstance(updater, dict) and "refer" in updater:
        json_path = os.path.join(UPDATERS_DIR, updater["refer"])
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):  
                new_updaters.extend(data)  # Add multiple items **in place of "refer"**
            elif isinstance(data, dict):
                new_updaters.append(data)  # Add single item
        else:
            print(f"Referred '{json_path}' not found!")
    else:
        new_updaters.append(updater)  # Keep original entry

includeFileUpdaters = new_updaters  # Replace with fully processed list

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

# Display the themes with the first line as the description
for i, theme in enumerate(themes, 1):
	with open(theme, 'r') as f:
		first_line = f.readline().strip()[1:]  # Remove the first character
	print(f"{i}. {first_line}")

# Prompt the user to select a theme
try:
	choice = int(input("Select a theme by number: "))
	if 1 <= choice <= len(themes):
		selected_theme = themes[choice - 1]

		config = configparser.ConfigParser()
		config.read(selected_theme)
		theme_data = {section: dict(config[section]) for section in config.sections()}
		print(theme_data)

		print(f"You selected: {selected_theme}")

		# Update configs
		for updater in includeFileUpdaters:
			if "path" not in updater:
				continue
			if updater["path"].startswith("./"): # If we are using a relative path
				# Use joined path and remove the ./
				config_path = os.path.join(DIR, updater["path"][2:])
			else:
				# Use an absolute path
				config_path = updater["path"]
			if not os.path.exists(config_path):
				print(f"Warning: {config_path} not found!")
				continue
			
			with open(config_path, 'r') as f:
				config_lines = f.readlines()
			
			for update in updater.get("updaters", []):
				if update["replaceWith"] == "themeFile":
					config_lines[update["line_number"]] = update["line"].replace("<x>", selected_theme) + "\n"
				else:
					config_lines[update["line_number"]] = update["line"].replace("<x>", theme_data["colors"][update["replaceWith"]]) + "\n"
			
			with open(config_path, 'w') as f:
				f.writelines(config_lines)

		# Reboot polybar
		subprocess.run(["killall", "polybar"])
		subprocess.run(["nohup", os.path.join(DIR, "launch.sh")])
	else:
		print("Invalid selection. Exiting.")
		exit(1)
except ValueError:
	print("Invalid input. Exiting.")
	exit(1)