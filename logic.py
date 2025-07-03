import os
import json
import shutil
import glob
import re # Import regular expressions
from utils import resize_image

class EverSDLogic:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def find_emulator_files(self, eversd_path):
        """Finds all .so emulator files in the EverSD root."""
        if not os.path.isdir(eversd_path):
            return []
        return [f for f in os.listdir(eversd_path) if f.endswith('.so')]

    def scan_for_games(self, eversd_path):
        """Scans the 'game' directory and returns a list of game info dicts."""
        game_path = os.path.join(eversd_path, 'game')
        if not os.path.isdir(game_path):
            self._update_status("Error: 'game' directory not found.")
            return []
        
        game_list = []
        try:
            json_files = glob.glob(os.path.join(game_path, '*.json'))
            for json_path in json_files:
                base_name = os.path.splitext(os.path.basename(json_path))[0]
                try:
                    with open(json_path, 'r') as f:
                        metadata = json.load(f)
                        title = metadata.get("romTitle", base_name) # Fallback to base_name
                        game_list.append({"base_name": base_name, "title": title})
                except (json.JSONDecodeError, IOError):
                    # If JSON is invalid, just use the filename
                    game_list.append({"base_name": base_name, "title": f"{base_name} [JSON ERROR]"})
            return game_list
        except PermissionError:
            self._update_status("PermissionError: Cannot read SD card.")
            return []

    def delete_game(self, eversd_path, game_base_name):
        """Deletes a game and all its associated files."""
        game_path = os.path.join(eversd_path, 'game')
        files_to_delete = glob.glob(os.path.join(game_path, f"{game_base_name}.*"))
        files_to_delete.extend(glob.glob(os.path.join(game_path, f"{game_base_name}0*.*")))
        files_to_delete.extend(glob.glob(os.path.join(game_path, f"{game_base_name}_*.*")))

        if not files_to_delete:
            self._update_status(f"Error: No files found for game '{game_base_name}'.")
            return False
        try:
            for f in set(files_to_delete): # Use set to avoid duplicates
                os.remove(f)
                self._update_status(f"Deleted {os.path.basename(f)}")
            self._update_status(f"Successfully deleted all files for '{game_base_name}'.")
            return True
        except Exception as e:
            self._update_status(f"Error deleting game files: {e}")
            return False

    def get_game_details(self, eversd_path, game_base_name):
        """Retrieves all details for a specific game."""
        game_path = os.path.join(eversd_path, 'game')
        json_path = os.path.join(game_path, f"{game_base_name}.json")

        details = {
            "metadata": {},
            "boxart_path": None,
            "banner_path": None,
            "error": None
        }

        # --- Read Metadata from JSON ---
        if not os.path.exists(json_path):
            details["error"] = f"Metadata file not found: {os.path.basename(json_path)}"
            return details
        
        try:
            with open(json_path, 'r') as f:
                details["metadata"] = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            details["error"] = f"Error reading metadata: {e}"
            return details

        # --- Find Image Files by Convention ---
        # Boxart (e.g., game0.png or game0_1080.png)
        boxart_files = glob.glob(os.path.join(game_path, f"{game_base_name}0*.png"))
        if boxart_files:
            # Prioritize the higher resolution one if available
            hires_boxart = os.path.join(game_path, f"{game_base_name}0_1080.png")
            if hires_boxart in boxart_files:
                details["boxart_path"] = hires_boxart
            else:
                details["boxart_path"] = boxart_files[0]

        # Banner (e.g., game_gamebanner.png)
        banner_file = os.path.join(game_path, f"{game_base_name}_gamebanner.png")
        if os.path.exists(banner_file):
            details["banner_path"] = banner_file
            
        return details

    def update_game_entry(self, data):
        """Updates an existing game's files."""
        try:
            eversd_path = data['eversd_path']
            game_path = os.path.join(eversd_path, 'game')
            original_base_name = data['original_base_name']

            # For simplicity, we'll keep the base filename the same.
            # A more complex implementation could handle renaming all files.
            safe_base_name = original_base_name

            # --- Path Definitions ---
            json_path = os.path.join(game_path, f"{safe_base_name}.json")

            # --- Read existing metadata to preserve what's not editable in the form ---
            with open(json_path, 'r') as f:
                metadata = json.load(f)

            # --- Update Metadata ---
            metadata.update({
                "romTitle": data.get('title', ''),
                "romPlatform": data.get('platform', ''),
                "romCore": data.get('emulator', 'NULL'),
                "romGenre": data.get('genre', ''),
                "romReleaseDate": data.get('release_date', ''),
                "romDescription": data.get('description', ''),
                # Assuming these might be added to the edit dialog in the future
                "romPublisher": data.get('publisher', metadata.get('romPublisher', '')),
                "romDeveloper": data.get('developer', metadata.get('romDeveloper', '')),
            })

            # --- File Operations ---
            # Only replace the ROM if a new one was selected
            if data.get('rom_path'):
                rom_extension = os.path.splitext(data['rom_path'])[1]
                rom_filename = f"{safe_base_name}{rom_extension}"
                dest_rom_path = os.path.join(game_path, rom_filename)
                
                # Remove old rom if extension is different
                if metadata["romFileName"] != rom_filename:
                    old_rom_path = os.path.join(game_path, metadata["romFileName"])
                    if os.path.exists(old_rom_path):
                        os.remove(old_rom_path)

                shutil.copy(data['rom_path'], dest_rom_path)
                metadata["romFileName"] = rom_filename
                self._update_status(f"Replaced ROM with {rom_filename}")

            # Process Boxart
            if data.get('boxart_path'):
                dest_boxart_path_1080 = os.path.join(game_path, f"{safe_base_name}0_1080.png")
                dest_boxart_path_0 = os.path.join(game_path, f"{safe_base_name}0.png")
                resize_image(data['boxart_path'], dest_boxart_path_1080, (474, 666))
                shutil.copy(dest_boxart_path_1080, dest_boxart_path_0)
                self._update_status("Updated boxart.")

            # Process Banner
            if data.get('banner_path'):
                dest_banner_path = os.path.join(game_path, f"{safe_base_name}_gamebanner.png")
                resize_image(data['banner_path'], dest_banner_path, (1920, 551))
                self._update_status("Updated banner.")

            # --- Write Updated JSON ---
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            self._update_status("Updated metadata file.")

            self._update_status("Successfully updated game entry!")
            return True, safe_base_name

        except Exception as e:
            self._update_status(f"An unexpected error occurred during update: {e}")
            return False, None

    def create_game_entry(self, data):
        """Creates the game files in the 'game' directory."""
        try:
            eversd_path = data['eversd_path']
            game_path = os.path.join(eversd_path, 'game')

            # Create 'game' directory if it doesn't exist
            if not os.path.exists(game_path):
                os.makedirs(game_path)
                self._update_status(f"Created directory: {game_path}")

            # --- File Naming ---
            # Sanitize the title to create a safe base filename
            safe_base_name = re.sub(r'[^a-z0-9]', '', data['title'].lower())
            rom_extension = os.path.splitext(data['rom_path'])[1]
            rom_filename = f"{safe_base_name}{rom_extension}"

            # --- Path Definitions ---
            dest_rom_path = os.path.join(game_path, rom_filename)
            json_path = os.path.join(game_path, f"{safe_base_name}.json")

            # --- Metadata Setup ---
            metadata = {
                "romFileName": rom_filename,
                "romTitle": data.get('title', ''),
                "romCore": data.get('emulator', 'NULL'),
                "romLaunchType": "NULL",
                "romPlatform": data.get('platform', 'Unknown'), 
                "romGenre": data.get('genre', ''),
                "romReleaseDate": data.get('release_date', ''),
                "romPlayers": data.get('players', 1), 
                "romDescription": data.get('description', ''),
                "romPublisher": data.get('publisher', ''),
                "romDeveloper": data.get('developer', ''),
                "romMapping": {
                    "a": "NULL", "b": "NULL", "x": "NULL", "y": "NULL",
                    "dpad": "NULL", "select": "NULL", "start": "NULL",
                    "l1": "NULL", "l2": "NULL", "r1": "NULL", "r2": "NULL"
                }
            }

            # --- File Operations ---
            shutil.copy(data['rom_path'], dest_rom_path)
            self._update_status(f"Copied ROM to {dest_rom_path}")

            # Process Boxart if provided. The Evercade finds this by filename convention.
            if data.get('boxart_path'):
                dest_boxart_path_1080 = os.path.join(game_path, f"{safe_base_name}0_1080.png")
                dest_boxart_path_0 = os.path.join(game_path, f"{safe_base_name}0.png")
                resize_image(data['boxart_path'], dest_boxart_path_1080, (474, 666))
                shutil.copy(dest_boxart_path_1080, dest_boxart_path_0)
                self._update_status(f"Created boxart at {dest_boxart_path_1080} and {dest_boxart_path_0}")

            # Process Banner if provided. The Evercade finds this by filename convention.
            if data.get('banner_path'):
                dest_banner_path = os.path.join(game_path, f"{safe_base_name}_gamebanner.png")
                resize_image(data['banner_path'], dest_banner_path, (1920, 551))
                self._update_status(f"Created banner at {dest_banner_path}")

            # --- JSON Metadata Generation ---
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            self._update_status(f"Generated metadata at {json_path}")

            self._update_status("Successfully created game entry!")
            return True, safe_base_name

        except Exception as e:
            self._update_status(f"An unexpected error occurred: {e}")
            return False, None