
import sys
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QFileDialog,
                             QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class AddGameDialog(QDialog):
    def __init__(self, logic, eversd_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Game Entry")
        self.setGeometry(150, 150, 700, 500)
        
        self.logic = logic
        self.eversd_path = eversd_path

        # Store selected file paths
        self.rom_path = None
        self.boxart_path = None
        self.banner_path = None

        self.initUI()
        self.connect_signals()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # -- Vimm.net URL Fetcher --
        vimm_layout = QHBoxLayout()
        main_layout.addLayout(vimm_layout)
        vimm_label = QLabel("Vimm.net URL:")
        self.vimm_url_input = QLineEdit()
        self.vimm_fetch_button = QPushButton("Fetch Info")
        vimm_layout.addWidget(vimm_label)
        vimm_layout.addWidget(self.vimm_url_input)
        vimm_layout.addWidget(self.vimm_fetch_button)

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
        self.create_button = QPushButton("Create Game Entry")
        self.cancel_button = QPushButton("Cancel")
        self.status_label = QLabel("Status: Ready")
        action_layout.addWidget(self.create_button)
        action_layout.addWidget(self.cancel_button)
        action_layout.addStretch()
        action_layout.addWidget(self.status_label)

        self.populate_emulators()

    def connect_signals(self):
        self.rom_button.clicked.connect(self.select_rom)
        self.boxart_button.clicked.connect(self.select_boxart)
        self.banner_button.clicked.connect(self.select_banner)
        self.create_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        # Connections for find_boxart and vimm_fetch will be in the controller

    def populate_emulators(self):
        self.emulator_select.clear()
        emulators = self.logic.find_emulator_files(self.eversd_path)
        if emulators:
            self.emulator_select.addItems(emulators)
        else:
            self.emulator_select.addItem("No emulators found")

    def select_rom(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ROM File")
        if path:
            self.rom_path = path
            # Only set the title if the field is currently empty
            if not self.title_input.text():
                base_name = os.path.splitext(os.path.basename(path))[0]
                self.title_input.setText(base_name)
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
            "rom_path": self.rom_path,
            "boxart_path": self.boxart_path,
            "banner_path": self.banner_path,
        }

if __name__ == '__main__':
    # This is for testing the dialog independently
    class MockLogic:
        def find_emulator_files(self, path):
            print(f"Searching for emulators in: {path}")
            return ["dummy_emu1.so", "dummy_emu2.so"]

    app = QApplication(sys.argv)
    dialog = AddGameDialog(logic=MockLogic(), eversd_path="/fake/path")
    if dialog.exec_() == QDialog.Accepted:
        print("Dialog Accepted")
        print(dialog.get_data())
    else:
        print("Dialog Canceled")
    sys.exit()
