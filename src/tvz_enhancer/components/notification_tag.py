from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class NotificationTag(QPushButton):
    def __init__(self, subject, parent=None):
        super().__init__(subject, parent)
        self.subject = subject
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Helvetica", 11))
        self.init_style()

    def init_style(self):
        self.setStyleSheet("""
            QPushButton {
                font-family: 'Segoe UI';
                padding: 10px 15px; /* Povećan horizontalni padding */
                border-radius: 4px;
                background-color: #141414;
                color: #cccccc;
            }
            QPushButton:checked {
                color: white;
                border-color: white;
                border: 1px solid #d1cfcf;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        self.setMinimumHeight(30)