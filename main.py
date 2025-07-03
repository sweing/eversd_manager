import sys
import os
import webbrowser
import requests
import tempfile
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QDialog, QListWidgetItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from gui import EverSDManagerWindow
from logic import EverSDLogic
from image_search import ImageSearchDialog
from vimm_scraper import get_vimm_info
from add_game_dialog import AddGameDialog
from edit_game_dialog import EditGameDialog

class AppController:
    def __init__(self, window, logic):
        self.window = window
        self.logic = logic
        self.connect_signals()
        self.auto_detect_sd_cards()

    def connect_signals(self):
        self.window.browse_button.clicked.connect(self.select_eversd_path)
        self.window.path_select.currentIndexChanged.connect(self.refresh_game_list)
        self.window.refresh_button.clicked.connect(self.refresh_game_list)
        self.window.add_game_button.clicked.connect(self.open_add_game_dialog)
        self.window.edit_button.clicked.connect(self.open_edit_game_dialog)
        self.window.delete_button.clicked.connect(self.delete_selected_game)
        self.window.game_list.currentItemChanged.connect(self.display_game_details)

    def auto_detect_sd_cards(self):
        """Auto-detects SD cards on Arch Linux."""
        self.window.path_select.clear()
        
        # Simple check for Arch Linux
        if os.path.exists("/etc/arch-release"):
            user = os.getlogin()
            media_path = f"/run/media/{user}"
            if os.path.isdir(media_path):
                try:
                    # Construct the full path for each detected directory
                    mounted_dirs = [os.path.join(media_path, d) for d in os.listdir(media_path) if os.path.isdir(os.path.join(media_path, d))]
                    if mounted_dirs:
                        self.window.path_select.addItems(mounted_dirs)
                        self.update_status(f"Auto-detected {len(mounted_dirs)} potential SD card(s).")
                        return
                except OSError as e:
                    self.update_status(f"Error reading media path: {e}")

        self.update_status("No SD cards auto-detected. Please browse manually.")

    def update_status(self, message):
        self.window.status_label.setText(f"Status: {message}")

    def select_eversd_path(self):
        path = QFileDialog.getExistingDirectory(self.window, "Select EverSD Root Directory")
        if path:
            self.window.path_select.addItem(path)
            self.window.path_select.setCurrentText(path)
            # The currentIndexChanged signal will trigger the refresh

    def refresh_game_list(self):
        self.window.game_list.clear()
        self.clear_details()
        eversd_path = self.window.path_select.currentText()
        if not eversd_path or not os.path.isdir(eversd_path):
            self.update_status("Set a valid EverSD path to see games.")
            return
        
        games = self.logic.scan_for_games(eversd_path)
        if games:
            # Sort games by title
            sorted_games = sorted(games, key=lambda g: g['title'])
            for game in sorted_games:
                item = QListWidgetItem(game['title'])
                item.setData(Qt.UserRole, game['base_name']) # Store base_name in the item
                self.window.game_list.addItem(item)

            self.update_status(f"Found {len(games)} games.")
        elif "Error" not in self.window.status_label.text():
            self.update_status("No games found. Add a new one!")

    def display_game_details(self, current_item, previous_item):
        """Triggered when the selection in the game list changes."""
        if not current_item:
            self.clear_details()
            return

        game_base_name = current_item.data(Qt.UserRole) # Retrieve base_name
        eversd_path = self.window.path_select.currentText()
        self.update_status(f"Loading details for {current_item.text()}...")
        
        details = self.logic.get_game_details(eversd_path, game_base_name)

        if details.get("error"):
            self.update_status(f"Error: {details['error']}")
            self.clear_details()
            return

        meta = details.get("metadata", {})
        self.window.title_label.setText(meta.get("romTitle", "N/A"))
        self.window.platform_label.setText(meta.get("romPlatform", "N/A"))
        self.window.genre_label.setText(meta.get("romGenre", "N/A"))
        self.window.publisher_label.setText(meta.get("romPublisher", "N/A"))
        self.window.developer_label.setText(meta.get("romDeveloper", "N/A"))
        self.window.release_date_label.setText(meta.get("romReleaseDate", "N/A"))
        self.window.description_label.setText(meta.get("romDescription", "N/A"))

        # Update images and their visibility
        boxart_path = details.get("boxart_path")
        banner_path = details.get("banner_path")
        
        self.update_image_preview(self.window.boxart_preview, boxart_path)
        self.window.boxart_preview.parent().setVisible(bool(boxart_path))

        self.update_image_preview(self.window.banner_preview, banner_path)
        self.window.banner_preview.parent().setVisible(bool(banner_path))
        
        self.update_status(f"Displayed details for {current_item.text()}.")

    def clear_details(self):
        """Clears the game detail view."""
        self.window.title_label.setText("N/A")
        self.window.platform_label.setText("N/A")
        self.window.genre_label.setText("N/A")
        self.window.publisher_label.setText("N/A")
        self.window.developer_label.setText("N/A")
        self.window.release_date_label.setText("N/A")
        self.window.description_label.setText("N/A")
        
        self.update_image_preview(self.window.boxart_preview, None)
        self.window.boxart_preview.parent().setVisible(False)
        
        self.update_image_preview(self.window.banner_preview, None)
        self.window.banner_preview.parent().setVisible(False)

    def update_image_preview(self, label, image_path):
        """Updates a QLabel with a scaled pixmap."""
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(label.size(), 
                                          Qt.KeepAspectRatio, 
                                          Qt.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
        else:
            label.setText("Image not found")
            label.setPixmap(QPixmap()) # Clear existing pixmap

    def delete_selected_game(self):
        selected_item = self.window.game_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self.window, "No Game Selected", "Please select a game to delete.")
            return

        game_base_name = selected_item.data(Qt.UserRole) # Retrieve base_name
        game_title = selected_item.text() # Get the title before the item is deleted
        eversd_path = self.window.path_select.currentText()

        reply = QMessageBox.question(self.window, 'Confirm Deletion',
                                     f"Are you sure you want to permanently delete all files for '{game_title}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.update_status(f"Deleting {game_title}...")
            success = self.logic.delete_game(eversd_path, game_base_name)
            if success:
                self.refresh_game_list()
                self.update_status(f"Successfully deleted {game_title}.")
            else:
                QMessageBox.critical(self.window, "Error", "Failed to delete game. Check status for details.")

    def open_add_game_dialog(self):
        eversd_path = self.window.path_select.currentText()
        if not eversd_path or not os.path.isdir(eversd_path):
            QMessageBox.warning(self.window, "Invalid Path", "Please set a valid EverSD path before adding a game.")
            return

        dialog = AddGameDialog(self.logic, eversd_path, self.window)
        
        dialog.find_boxart_button.clicked.connect(lambda: self.find_boxart_for_dialog(dialog))
        dialog.find_banner_button.clicked.connect(lambda: self.find_banner_for_dialog(dialog))
        dialog.vimm_fetch_button.clicked.connect(lambda: self.fetch_vimm_info_for_dialog(dialog))

        if dialog.exec_() == QDialog.Accepted:
            self.create_game_entry(dialog.get_data())

    def open_edit_game_dialog(self):
        selected_item = self.window.game_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self.window, "No Game Selected", "Please select a game from the list to edit.")
            return

        game_base_name = selected_item.data(Qt.UserRole) # Retrieve base_name
        eversd_path = self.window.path_select.currentText()
        
        game_data = self.logic.get_game_details(eversd_path, game_base_name)
        if game_data.get("error"):
            QMessageBox.critical(self.window, "Error", f"Could not load game data: {game_data['error']}")
            return
        
        game_data['base_name'] = game_base_name

        dialog = EditGameDialog(self.logic, eversd_path, game_data, self.window)
        
        dialog.find_boxart_button.clicked.connect(lambda: self.find_boxart_for_dialog(dialog))
        dialog.find_banner_button.clicked.connect(lambda: self.find_banner_for_dialog(dialog))

        if dialog.exec_() == QDialog.Accepted:
            self.update_game_entry(dialog.get_data())

    def find_boxart_for_dialog(self, dialog):
        game_title = dialog.title_input.text()
        if not game_title:
            QMessageBox.warning(dialog, "Missing Title", "Please enter a Game Title first.")
            return

        search_dialog = ImageSearchDialog(f"{game_title} box art", parent_controller=self)
        if search_dialog.exec_() == QDialog.Accepted and search_dialog.selected_image_url:
            self.download_and_set_boxart(search_dialog.selected_image_url, dialog)

    def find_banner_for_dialog(self, dialog):
        game_title = dialog.title_input.text()
        if not game_title:
            QMessageBox.warning(dialog, "Missing Title", "Please enter a Game Title first.")
            return

        search_dialog = ImageSearchDialog(f"{game_title} banner", parent_controller=self)
        if search_dialog.exec_() == QDialog.Accepted and search_dialog.selected_image_url:
            self.download_and_set_banner(search_dialog.selected_image_url, dialog)

    def fetch_vimm_info_for_dialog(self, dialog):
        url = dialog.vimm_url_input.text()
        if not url:
            QMessageBox.warning(dialog, "Missing URL", "Please enter a Vimm.net URL.")
            return

        self.update_status("Fetching info from Vimm.net...")
        QApplication.processEvents()
        info, error = get_vimm_info(url)

        if error:
            self.update_status(f"Error: {error}")
            QMessageBox.critical(dialog, "Scraping Error", error)
            return

        dialog.title_input.setText(info.get('title', ''))
        dialog.genre_input.setText(info.get('genre', ''))
        dialog.publisher_input.setText(info.get('publisher', ''))
        dialog.developer_input.setText(info.get('developer', ''))
        dialog.release_date_input.setText(info.get('release_date', ''))
        self.update_status("Successfully fetched and populated game info.")

    def download_and_set_boxart(self, url, dialog):
        try:
            self.update_status(f"Downloading image from {url}...")
            response = requests.get(url, timeout=10, verify=False)
            response.raise_for_status()
            temp_dir = tempfile.gettempdir()
            extension = os.path.splitext(url.split("?")[0])[-1] or ".png"
            temp_path = os.path.join(temp_dir, f"downloaded_boxart{extension}")
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            dialog.boxart_path = temp_path
            dialog.boxart_label.setText(f"Downloaded: {os.path.basename(temp_path)}")
            dialog.update_image_preview(temp_path)
            self.update_status("Successfully downloaded and set boxart.")

        except Exception as e:
            error_msg = f"Failed to download image: {e}"
            self.update_status(error_msg)
            QMessageBox.critical(dialog, "Download Error", error_msg)

    def download_and_set_banner(self, url, dialog):
        try:
            self.update_status(f"Downloading image from {url}...")
            response = requests.get(url, timeout=10, verify=False)
            response.raise_for_status()
            temp_dir = tempfile.gettempdir()
            extension = os.path.splitext(url.split("?")[0])[-1] or ".png"
            temp_path = os.path.join(temp_dir, f"downloaded_banner{extension}")
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            dialog.banner_path = temp_path
            dialog.banner_label.setText(f"Downloaded: {os.path.basename(temp_path)}")
            self.update_status("Successfully downloaded and set banner.")

        except Exception as e:
            error_msg = f"Failed to download image: {e}"
            self.update_status(error_msg)
            QMessageBox.critical(dialog, "Download Error", error_msg)

    def create_game_entry(self, data):
        required_fields = ["eversd_path", "title", "rom_path"]
        if any(not data[field] for field in required_fields):
            QMessageBox.warning(self.window, "Missing Information", "Please provide the Game Title and a ROM file.")
            return

        self.update_status("Processing new game entry...")
        QApplication.processEvents()
        success, new_base_name = self.logic.create_game_entry(data)
        QApplication.processEvents()

        if success:
            QMessageBox.information(self.window, "Success", "Game entry created successfully!")
            self.refresh_game_list()
            self.select_game_by_base_name(new_base_name)
        else:
            QMessageBox.critical(self.window, "Error", "Failed to create game entry. Check status for details.")

    def update_game_entry(self, data):
        self.update_status("Processing game entry update...")
        QApplication.processEvents()
        success, updated_base_name = self.logic.update_game_entry(data)
        QApplication.processEvents()

        if success:
            QMessageBox.information(self.window, "Success", "Game entry updated successfully!")
            self.refresh_game_list()
            self.select_game_by_base_name(updated_base_name)
        else:
            QMessageBox.critical(self.window, "Error", "Failed to update game entry. Check status for details.")

    def select_game_by_base_name(self, base_name):
        """Finds and selects an item in the game list by its base_name."""
        for index in range(self.window.game_list.count()):
            item = self.window.game_list.item(index)
            if item.data(Qt.UserRole) == base_name:
                self.window.game_list.setCurrentItem(item)
                break

def main():
    app = QApplication(sys.argv)
    window = EverSDManagerWindow()
    logic = EverSDLogic(status_callback=lambda msg: window.status_label.setText(f"Status: {msg}"))
    controller = AppController(window, logic)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()