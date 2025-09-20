import sys
import os
import pathlib
import vlc
import pickle
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QTextEdit, QFrame, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class FileViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Viewer")
        self.setGeometry(200, 200, 800, 600)

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Top section for navigation buttons
        self.top_buttons_layout = QHBoxLayout()
        self.choose_button = QPushButton("Choose File")
        self.choose_button.clicked.connect(self.open_file)
        self.choose_button.setMinimumHeight(40)
        self.top_buttons_layout.addWidget(self.choose_button)

        self.back_button = QPushButton("⬅ Back")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.hide()
        self.back_button.setMinimumHeight(40)
        self.top_buttons_layout.addWidget(self.back_button)
        
        self.layout.addLayout(self.top_buttons_layout)

        # Content area for displaying files
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("background-color: #2c2f33; border-radius: 10px;")
        self.content_frame.setFrameShape(QFrame.StyledPanel)
        self.content_frame.setFrameShadow(QFrame.Raised)
        self.content_frame.setLineWidth(2)
        
        self.content_layout = QVBoxLayout(self.content_frame)

        # Image Viewer
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: none;")
        self.image_label.hide()
        self.content_layout.addWidget(self.image_label)

        # Text Viewer
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #36393e;
                color: #ffffff;
                border: none;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
                padding: 10px;
            }
        """)
        self.text_edit.hide()
        self.content_layout.addWidget(self.text_edit)

        # Video Frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black; border-radius: 10px;")
        self.video_frame.hide()
        self.content_layout.addWidget(self.video_frame)
        
        self.layout.addWidget(self.content_frame)

        # Video Controls
        self.video_controls = QHBoxLayout()
        self.video_controls.setSpacing(10)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)
        self.play_button.setMinimumHeight(35)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        self.pause_button.setMinimumHeight(35)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_video)
        self.stop_button.setMinimumHeight(35)

        for btn in [self.play_button, self.pause_button, self.stop_button]:
            self.video_controls.addWidget(btn)
            btn.hide()
        self.layout.addLayout(self.video_controls)

        # VLC player 
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.current_pixmap = None
        self.current_video_path = None

        self.setLayout(self.layout)

        # Apply global stylesheet for a dark, modern theme
        self.setStyleSheet("""
            QWidget {
                background-color: #23272a;
                color: #ffffff;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QPushButton {
                background-color: #7289da;
                border: 2px solid #7289da;
                border-radius: 8px;
                color: #ffffff;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #677bc4;
                border-color: #677bc4;
            }
            QPushButton:pressed {
                background-color: #5b6eae;
                border-color: #5b6eae;
            }
            QFrame {
                border-radius: 10px;
            }
        """)

    def resizeEvent(self, event):
        if self.current_pixmap and not self.current_pixmap.isNull():
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio
            )
            self.image_label.setPixmap(scaled_pixmap)
        super().resizeEvent(event)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Videos (*.mp4 *.avi *.mkv *.mov);;Images (*.png *.jpg *.jpeg *.bmp);;Text Files (*.txt);;Pickle Files (*.pkl);;All Files (*)"
        )
        if not file_path:
            return

        # commands while displaying video
        self.image_label.hide()
        self.text_edit.hide()
        self.video_frame.hide()
        self.media_player.stop()
        self.play_button.hide()
        self.pause_button.hide()
        self.stop_button.hide()
        self.current_video_path = None

        # Images opening
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            self.current_pixmap = QPixmap(file_path)
            if self.current_pixmap.isNull():
                QMessageBox.warning(self, "Error", "Failed to load image.")
                return
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(), Qt.KeepAspectRatio
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.show()
            self.content_frame.layout().addWidget(self.image_label)


        # Text files opening
        elif file_path.lower().endswith('.txt'):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"Failed to read file: {e}"
            self.text_edit.setText(content)
            self.text_edit.show()
            self.content_frame.layout().addWidget(self.text_edit)


        # Videos opening
        elif file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "Video file not found.")
                return
            try:
                self.current_video_path = pathlib.Path(file_path).absolute().as_uri()
                media = self.instance.media_new(self.current_video_path)
                self.media_player.set_media(media)

                # Attach video to frame
                if sys.platform.startswith("win"):
                    self.media_player.set_hwnd(int(self.video_frame.winId()))
                else:
                    self.media_player.set_xwindow(int(self.video_frame.winId()))

                self.video_frame.show()
                for btn in [self.play_button, self.pause_button, self.stop_button]:
                    btn.show()
                self.play_video()
                self.content_frame.layout().addWidget(self.video_frame)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cannot play video: {e}")

        # Pickle files opening (New Code)
        elif file_path.lower().endswith('.pkl'):
            try:
                with open(file_path, "rb") as f:
                    data = pickle.load(f)
                    content = f"Fetched data: \n{data}"
            except Exception as e:
                content = f"Failed to read pickle file: {e}"
            self.text_edit.setText(content)
            self.text_edit.show()
            self.content_frame.layout().addWidget(self.text_edit)

        # Show back button, hide choose button
        self.choose_button.hide()
        self.back_button.show()

    def play_video(self):
        if self.current_video_path:
            try:
                self.media_player.play()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Cannot play video: {e}")

    def pause_video(self):
        if self.current_video_path:
            self.media_player.pause()

    def stop_video(self):
        if self.current_video_path:
            self.media_player.stop()

    def go_back(self):
        self.image_label.hide()
        self.text_edit.hide()
        self.video_frame.hide()
        self.media_player.stop()
        self.play_button.hide()
        self.pause_button.hide()
        self.stop_button.hide()
        self.back_button.hide()
        self.choose_button.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileViewer()
    window.show()
    sys.exit(app.exec_())
