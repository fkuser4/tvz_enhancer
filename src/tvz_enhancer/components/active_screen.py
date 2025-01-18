import sys

from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import Qt

from src.tvz_enhancer.components.top_bar import TopBar
from src.tvz_enhancer.modules.home_module import HomeModule
from src.tvz_enhancer.modules.reservation_module import ReservationModule


class ActiveScreen(QWidget):
    def __init__(self, homeWidget, parent=None):
        super().__init__(parent)
        self.homeWidget = homeWidget
        self.scene_stack = QStackedWidget()
        self.scene_stack.addWidget(homeWidget)

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)

        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.setContentsMargins(14, 0, 14, 10)

        self.top_bar = QLabel("Home")
        self.top_bar.setStyleSheet("color: white; font-weight: 500;")
        self.top_bar.setFont(QFont("Helvetica", 23))
        self.top_bar_layout.addWidget(self.top_bar, alignment=Qt.AlignmentFlag.AlignLeft)

        self.reservation_button = QPushButton()

        plus_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-plus"><path d="M5 12h14"/><path d="M12 5v14"/></svg>'''

        svg_bytes = plus_svg.encode('utf-8')
        pixmap = QPixmap()
        pixmap.loadFromData(svg_bytes)

        self.reservation_button.setIcon(QIcon(pixmap))
        self.reservation_button.setText(" Rezervacija")
        self.reservation_button.setStyleSheet("""
            QPushButton {
                border: 1px solid transparent;
                background-color: #141414; 
                color: white;
                font-size: 16px;
                padding: 5px 15px;
                padding-left: 10px;
                border-radius: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #1e1e1e;
                border: 1px solid white;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)

        self.reservation_button.setFixedHeight(self.top_bar.fontMetrics().height() + 10)
        self.reservation_button.hide()  # Initially hidden
        self.reservation_button.clicked.connect(self.handle_reservation_button)
        self.top_bar_layout.addWidget(self.reservation_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.top_bar_widget = QWidget()
        self.top_bar_widget.setStyleSheet("background-color: transparent;")
        self.top_bar_widget.setLayout(self.top_bar_layout)

        self.main_layout.addWidget(self.top_bar_widget)
        self.main_layout.addWidget(self.scene_stack)

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: none;")
        layout = self.main_layout
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def handle_reservation_button(self):
        current_widget = self.scene_stack.currentWidget()
        if isinstance(current_widget, ReservationModule):
            current_widget.showCreateReservationOverlay()

    def swapModule(self, widget):
        if self.scene_stack.indexOf(widget) == -1:
            self.scene_stack.addWidget(widget)

        self.scene_stack.setCurrentWidget(widget)

        module_name = getattr(widget, "module_name", widget.__class__.__name__)
        self.top_bar.setText(module_name)

        if module_name == "ReservationModule":
            self.reservation_button.show()
            self.top_bar.setContentsMargins(0, 0, 0, 10)
        else:
            self.reservation_button.hide()

