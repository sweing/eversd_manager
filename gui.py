
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QSplitter, QComboBox, QScrollArea)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class EverSDManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EverSD Game Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # -- Top Controls --
        top_controls_layout = QHBoxLayout()
        main_layout.addLayout(top_controls_layout)
        
        path_label = QLabel("EverSD Path:")
        self.path_select = QComboBox()
        self.path_select.setMinimumWidth(350)
        self.browse_button = QPushButton("Browse...")
        self.add_game_button = QPushButton("Add New Game...")
        self.refresh_button = QPushButton("Refresh List")

        top_controls_layout.addWidget(path_label)
        top_controls_layout.addWidget(self.path_select)
        top_controls_layout.addWidget(self.browse_button)
        top_controls_layout.addStretch()
        top_controls_layout.addWidget(self.add_game_button)
        top_controls_layout.addWidget(self.refresh_button)

        # -- Main Content Area (Splitter) --
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter, 1) # Give it stretch factor

        # -- Left Side: Game List --
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        self.game_list = QListWidget()
        self.delete_button = QPushButton("Delete Selected Game")
        self.edit_button = QPushButton("Edit Selected Game")
        
        left_layout.addWidget(QLabel("Existing Games:"))
        left_layout.addWidget(self.game_list)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        left_layout.addLayout(button_layout)
        
        main_splitter.addWidget(left_widget)

        # -- Right Side: Game Details --
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        right_layout.addWidget(QLabel("Game Details:"))
        
        self.details_grid = QGridLayout()
        right_layout.addLayout(self.details_grid)

        self.title_label = self.add_detail_row("Title:", 0)
        self.platform_label = self.add_detail_row("Platform:", 1)
        self.genre_label = self.add_detail_row("Genre:", 2)
        self.publisher_label = self.add_detail_row("Publisher:", 3)
        self.developer_label = self.add_detail_row("Developer:", 4)
        self.release_date_label = self.add_detail_row("Release Date:", 5)
        self.description_label = self.add_detail_row("Description:", 6, is_multiline=True)

        # Image Previews
        image_layout = QHBoxLayout()
        right_layout.addLayout(image_layout)
        
        self.boxart_preview = self.create_image_preview_label()
        self.banner_preview = self.create_image_preview_label(is_banner=True)

        image_layout.addWidget(self.create_image_group("Box Art", self.boxart_preview))
        image_layout.addWidget(self.create_image_group("Banner", self.banner_preview))

        right_layout.addStretch()
        main_splitter.addWidget(right_widget)
        
        main_splitter.setSizes([300, 700]) # Initial size distribution

        # -- Status Bar --
        self.status_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)

    def add_detail_row(self, label_text, row, is_multiline=False):
        """Helper to add a row to the details grid."""
        label = QLabel(f"<b>{label_text}</b>")
        value = QLabel("N/A")
        
        if is_multiline:
            value.setWordWrap(True)
            value.setAlignment(Qt.AlignTop)
            
            # Create and configure a scroll area
            scroll_area = QScrollArea()
            scroll_area.setWidget(value)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QScrollArea.NoFrame) # Make it blend in
            
            self.details_grid.addWidget(label, row, 0)
            self.details_grid.addWidget(scroll_area, row, 1)
        else:
            self.details_grid.addWidget(label, row, 0)
            self.details_grid.addWidget(value, row, 1)
            
        return value

    def create_image_preview_label(self, is_banner=False):
        """Helper to create a QLabel for image previews."""
        label = QLabel("Image not found")
        label.setAlignment(Qt.AlignCenter)
        label.setFrameShape(QLabel.StyledPanel)
        if is_banner:
            label.setFixedSize(384, 110) # 1920x551 aspect ratio / 5
        else:
            label.setFixedSize(200, 280) # 474x666 aspect ratio / 2.37
        return label

    def create_image_group(self, title, preview_label):
        """Helper to group a title and a preview label into a widget."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        
        layout.addWidget(QLabel(title))
        layout.addWidget(preview_label)
        layout.addStretch()
        
        return container


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EverSDManagerWindow()
    window.show()
    sys.exit(app.exec_())
