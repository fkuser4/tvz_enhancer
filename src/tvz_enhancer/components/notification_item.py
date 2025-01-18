import re
from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QFrame, QSizePolicy,
    QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime

class NotificationItem(QWidget):
    def __init__(
        self,
        title: str,
        content: str,
        subject: str,
        time_str: str,
        height: int,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.subject = subject
        self.time_original = time_str
        self.height = height
        self.font = "Meta"

        self.is_expanded = False
        self.collapsed_height = 50
        self.expanded_height = 99999

        self.init_ui()

    def init_ui(self):
        time_ago_str = self.time_original

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: 2px solid #1A1A1A;
                border-radius: 4px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(20, 25, 20, 25)
        frame_layout.setSpacing(15)

        subject_frame = QFrame()
        subject_layout = QHBoxLayout(subject_frame)
        subject_layout.setContentsMargins(0, 0, 0, 0)
        subject_layout.setSpacing(0)
        subject_frame.setStyleSheet("background-color: transparent; border: none")

        subject_label_left = QLabel(self.subject)
        subject_label_left.setFont(QFont(self.font, 13))
        subject_label_left.setStyleSheet("color: #4A9EFF; border: none")
        subject_label_left.setAlignment(Qt.AlignmentFlag.AlignLeft)

        time_label = QLabel(f"{time_ago_str}")
        time_label.setFont(QFont("Arial", 10))
        time_label.setStyleSheet("color: #918d8d; border: none;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        subject_layout.addWidget(subject_label_left, alignment=Qt.AlignmentFlag.AlignLeft)
        subject_layout.addStretch()
        subject_layout.addWidget(time_label, alignment=Qt.AlignmentFlag.AlignRight)

        frame_layout.addWidget(subject_frame)

        title_label = QLabel(self.title)
        title_label.setFont(QFont(self.font, 16))
        title_label.setStyleSheet("color: white; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_label.setContentsMargins(0,0,0,12)
        frame_layout.addWidget(title_label)

        self.content = self.content + "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
        self.content_label = QLabel()
        self.content_label.setTextFormat(Qt.TextFormat.RichText)
        self.content_label.setText(f"""
            <div style="
                color: #b8b2b2;
                line-height: 1.6;">
                {self.content}
            </div>
        """)
        self.content_label.setFont(QFont(self.font, 12))
        self.content_label.setStyleSheet("border: none; font-weight: 500;")
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.content_label.setMaximumHeight(self.collapsed_height)
        frame_layout.addWidget(self.content_label)

        self.show_more_button = QPushButton("Show more")
        self.show_more_button.setStyleSheet("""
            QPushButton {
                color: #4A9EFF;
                background: transparent;
                border: none;
                font-size: 14px;
                padding: 0;
                margin: 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        self.show_more_button.clicked.connect(self.toggle_show_more)
        frame_layout.addWidget(self.show_more_button, alignment=Qt.AlignmentFlag.AlignLeft)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

        self.setMinimumHeight(self.height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self.update_show_more_visibility()

    def toggle_show_more(self):
        if not self.is_expanded:
            self.content_label.setMaximumHeight(self.expanded_height)
            self.show_more_button.setText("Show less")
            self.is_expanded = True
        else:
            self.content_label.setMaximumHeight(self.collapsed_height)
            self.show_more_button.setText("Show more")
            self.is_expanded = False

    def update_show_more_visibility(self):
        needed_h = self.content_label.sizeHint().height()
        if needed_h <= self.collapsed_height:
            self.show_more_button.hide()
        else:
            self.show_more_button.show()
