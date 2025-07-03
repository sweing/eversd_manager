
import sys
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class EditGameDialog(QDialog):
    def __init__(self, logic, eversd_path, game_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Game Entry")
        self.setGeometry(150, 150, 700, 500)
        
        self.logic = logic
        self.eversd_path = eversd_path
        self.game_data = game_data

        # Store selected file paths
        self.rom_path = None
        self.boxart_path = game_data.get('boxart_path')
        self.banner_path = game_data.get('banner_path')

        self.initUI()
        self.connect_signals()
        self.populate_fields()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # -- Game Information Form --
        form_layout = QGridLayout()
        main_layout.addLayout(form_layout)

        form_layout.addWidget(QLabel("Game Title:"), 0, 0)
        self.title_input = QLineEdit()
        form_layout.addWidget(self.title_input, 0, 1)

        form_layout.addWidget(QLabel("Platform:"), 1, 0)
        self.platform_input = QLineEdit()
        form_layout.addWidget(self.platform_input, 1, 1)

        form_layout.addWidget(QLabel("Description:"), 2, 0)
        self.desc_input = QLineEdit()
        form_layout.addWidget(self.desc_input, 2, 1)

        form_layout.addWidget(QLabel("Genre:"), 3, 0)
        self.genre_input = QLineEdit()
        form_layout.addWidget(self.genre_input, 3, 1)

        form_layout.addWidget(QLabel("Publisher:"), 4, 0)
        self.publisher_input = QLineEdit()
        form_layout.addWidget(self.publisher_input, 4, 1)

        form_layout.addWidget(QLabel("Developer:"), 5, 0)
        self.developer_input = QLineEdit()
        form_layout.addWidget(self.developer_input, 5, 1)

        form_layout.addWidget(QLabel("Release Date:"), 6, 0)
        self.release_date_input = QLineEdit()
        form_layout.addWidget(self.release_date_input, 6, 1)

        form_layout.addWidget(QLabel("Emulator (.so):"), 7, 0)
        self.emulator_select = QComboBox()
        form_layout.addWidget(self.emulator_select, 7, 1)

        # -- File Selection & Image Preview --
        file_and_preview_layout = QHBoxLayout()
        main_layout.addLayout(file_and_preview_layout)

        file_layout = QGridLayout()
        file_and_preview_layout.addLayout(file_layout)

        self.rom_button = QPushButton("Select ROM File")
        self.rom_label = QLabel("No ROM selected")
        file_layout.addWidget(self.rom_button, 0, 0)
        file_layout.addWidget(self.rom_label, 0, 1)

        self.boxart_button = QPushButton("Select Boxart")
        self.find_boxart_button = QPushButton("Find Online")
        self.boxart_label = QLabel("No boxart selected")
        boxart_layout = QHBoxLayout()
        boxart_layout.addWidget(self.boxart_button)
        boxart_layout.addWidget(self.find_boxart_button)
        file_layout.addLayout(boxart_layout, 1, 0)
        file_layout.addWidget(self.boxart_label, 1, 1)

        self.banner_button = QPushButton("Select Banner")
        self.find_banner_button = QPushButton("Find Online")
        self.banner_label = QLabel("No banner selected")
        banner_layout = QHBoxLayout()
        banner_layout.addWidget(self.banner_button)
        banner_layout.addWidget(self.find_banner_button)
        file_layout.addLayout(banner_layout, 2, 0)
        file_layout.addWidget(self.banner_label, 2, 1)

        # Image Preview
        self.image_preview_label = QLabel("Image Preview")
        self.image_preview_label.setFixedSize(150, 150)
        file_and_preview_layout.addWidget(self.image_preview_label)

        # -- Actions & Status --
        action_layout = QHBoxLayout()
        main_layout.addLayout(action_layout)
        self.save_button = QPushButton("Save Changes")
        self.cancel_button = QPushButton("Cancel")
        self.status_label = QLabel("Status: Ready")
        action_layout.addWidget(self.save_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addStretch()
        action_layout.addWidget(self.status_label)

        self.populate_emulators()

    def connect_signals(self):
        self.rom_button.clicked.connect(self.select_rom)
        self.boxart_button.clicked.connect(self.select_boxart)
        self.banner_button.clicked.connect(self.select_banner)
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def populate_emulators(self):
        self.emulator_select.clear()
        emulators = self.logic.find_emulator_files(self.eversd_path)
        if emulators:
            self.emulator_select.addItems(emulators)
        else:
            self.emulator_select.addItem("No emulators found")

    def populate_fields(self):
        metadata = self.game_data.get("metadata", {})
        self.title_input.setText(metadata.get("romTitle", ""))
        self.platform_input.setText(metadata.get("romPlatform", ""))
        self.desc_input.setText(metadata.get("romDescription", ""))
        self.genre_input.setText(metadata.get("romGenre", ""))
        self.publisher_input.setText(metadata.get("romPublisher", ""))
        self.developer_input.setText(metadata.get("romDeveloper", ""))
        self.release_date_input.setText(metadata.get("romReleaseDate", ""))
        
        # Set emulator
        current_emulator = metadata.get("romCore")
        if current_emulator:
            index = self.emulator_select.findText(current_emulator)
            if index >= 0:
                self.emulator_select.setCurrentIndex(index)

        # Set rom
        self.rom_label.setText(metadata.get("romFileName", "No ROM selected"))

        # Set images
        if self.boxart_path:
            self.boxart_label.setText(os.path.basename(self.boxart_path))
            self.update_image_preview(self.boxart_path)
        if self.banner_path:
            self.banner_label.setText(os.path.basename(self.banner_path))


    def select_rom(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ROM File")
        if path:
            self.rom_path = path
            self.rom_label.setText(os.path.basename(path))

    def select_boxart(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Boxart Image", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.boxart_path = path
            self.boxart_label.setText(os.path.basename(path))
            self.update_image_preview(path)

    def select_banner(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Banner Image", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.banner_path = path
            self.banner_label.setText(os.path.basename(path))

    def update_image_preview(self, image_path):
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_preview_label.size(), 
                                          Qt.KeepAspectRatio,
                                          Qt.SmoothTransformation)
            self.image_preview_label.setPixmap(scaled_pixmap)
        else:
            self.image_preview_label.setText("Image Preview")

    def get_data(self):
        return {
            "eversd_path": self.eversd_path,
            "title": self.title_input.text(),
            "platform": self.platform_input.text(),
            "description": self.desc_input.text(),
            "genre": self.genre_input.text(),
            "publisher": self.publisher_input.text(),
            "developer": self.developer_input.text(),
            "release_date": self.release_date_input.text(),
            "emulator": self.emulator_select.currentText(),
            "rom_path": self.rom_path, # This will be None if not changed
            "boxart_path": self.boxart_path,
            "banner_path": self.banner_path,
            "original_base_name": self.game_data.get("base_name")
        }
