from PyQt6.QtWidgets import QPushButton, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class DocumentTag(QPushButton):
    def __init__(self, label, parent=None):
        super().__init__(label, parent)
        self.label = label
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFont(QFont("Arial", 10))
        self.init_style()

    def init_style(self):
        self.setStyleSheet("""
            QPushButton {
                padding: 5px 15px; /* Povećan horizontalni padding */
                padding-top: 5px;   /* Povećan vertikalni padding */
                padding-bottom: 5px;
                border: 2px solid white;
                border-radius: 15px;
                background-color: #283039;
                color: white;
            }
            QPushButton:checked {
                background-color: #4A90E2;
                color: white;
                border: 1px solid #4A90E2;
            }
            QPushButton:hover {
                background-color: #3E454B;
            }
        """)
        self.setMinimumHeight(30)