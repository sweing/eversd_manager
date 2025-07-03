
import sys
import requests
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QListWidget, 
                             QListWidgetItem, QPushButton, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
from duckduckgo_search import DDGS

class ImageUrlSearchThread(QThread):
    """Worker thread to search for image URLs without freezing the GUI."""
    finished = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            with DDGS(headers=headers) as ddgs:
                results = ddgs.images(keywords=self.query, max_results=30)
                if results:
                    self.finished.emit([res['image'] for res in results])
                else:
                    self.finished.emit([])
        except Exception as e:
            print(f"Image URL search failed: {e}")
            self.finished.emit([])

class ImageDownloaderThread(QThread):
    """Worker thread to download a single image."""
    finished = pyqtSignal(QIcon, QListWidgetItem)

    def __init__(self, url, item, headers):
        super().__init__()
        self.url = url
        self.item = item
        self.headers = headers

    def run(self):
        try:
            headers = self.headers.copy()
            headers['Referer'] = 'https://duckduckgo.com/'
            response = requests.get(self.url, stream=True, timeout=5, headers=headers, verify=False)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            icon = QIcon(pixmap)
            self.finished.emit(icon, self.item)
        except Exception as e:
            print(f"Failed to download {self.url}: {e}")
            # Optionally emit a signal with a placeholder for failed downloads
            self.finished.emit(QIcon(), self.item)


class ImageSearchDialog(QDialog):
    def __init__(self, query, parent_controller=None):
        super().__init__(parent_controller.window if parent_controller else None)
        self.setWindowTitle(f"Image Search: '{query}'")
        self.setGeometry(150, 150, 800, 600)
        self.selected_image_url = None
        self.controller = parent_controller
        self.downloader_threads = [] # Keep track of threads

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(150, 150))
        self.image_list.setFlow(QListWidget.LeftToRight)
        self.image_list.setWrapping(True)
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.itemDoubleClicked.connect(self.accept)
        self.layout.addWidget(self.image_list)

        self.select_button = QPushButton("Select Image")
        self.select_button.clicked.connect(self.accept)
        self.layout.addWidget(self.select_button)

        self.url_search_thread = ImageUrlSearchThread(query)
        self.url_search_thread.finished.connect(self.populate_placeholders)
        self.url_search_thread.start()
        if self.controller:
            self.controller.update_status(f"Searching for '{query}'...")

    def populate_placeholders(self, image_urls):
        if self.controller:
            self.controller.update_status("Search complete. Loading thumbnails...")
        if not image_urls:
            QMessageBox.warning(self, "No Results", "Could not find any images for that query.")
            self.reject()
            return

        placeholder_icon = QIcon.fromTheme("image-loading")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        for url in image_urls:
            item = QListWidgetItem(placeholder_icon, "")
            item.setData(Qt.UserRole, url)
            self.image_list.addItem(item)
            # Start downloader for this item
            downloader = ImageDownloaderThread(url, item, headers)
            downloader.finished.connect(self.on_image_downloaded)
            self.downloader_threads.append(downloader)
            downloader.start()

    def on_image_downloaded(self, icon, item):
        if not icon.isNull():
            item.setIcon(icon)
        # Clean up finished threads
        self.downloader_threads = [t for t in self.downloader_threads if not t.isFinished()]
        if not self.downloader_threads and self.controller:
             self.controller.update_status("Image search ready.")

    def accept(self):
        selected_item = self.image_list.currentItem()
        if selected_item:
            # Check if the icon is not the placeholder
            if not selected_item.icon().isNull():
                self.selected_image_url = selected_item.data(Qt.UserRole)
                super().accept()
            else:
                QMessageBox.warning(self, "Image Not Ready", "Please wait for the image to finish loading.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select an image.")

    def closeEvent(self, event):
        # Ensure all downloader threads are terminated when dialog is closed
        for thread in self.downloader_threads:
            thread.quit()
            thread.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    class MockController:
        def __init__(self):
            self.window = None
        def update_status(self, msg):
            print(msg)
    dialog = ImageSearchDialog("Super Mario 64 box art", parent_controller=MockController())
    if dialog.exec_() == QDialog.Accepted:
        print(f"Selected: {dialog.selected_image_url}")
    sys.exit(app.exec_())
