from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QSvgWidget
import os
import logging

# Configure logging level
logging.basicConfig(level=logging.DEBUG)


class ColorChangingSvgButton(QPushButton):
    def __init__(self, svg_path, parent=None):
        super().__init__(parent)
        self.svg_path = svg_path
        self.default_color = "#808080"  # Grey
        self.hover_color = "#FFFFFF"    # White
        self.current_color = self.default_color
        self.setFixedSize(25, 25)
        self.setStyleSheet("QPushButton { border: none; background-color: transparent; }")
        self.updateIconColor(self.default_color)

    def updateIconColor(self, color):
        if os.path.exists(self.svg_path):
            with open(self.svg_path, 'r') as file:
                svg_content = file.read()
                colored_svg = (svg_content
                    .replace('fill="currentColor"', f'fill="{color}"')
                    .replace('stroke="currentColor"', f'stroke="{color}"'))
                self.setIcon(QIcon(self.createColoredPixmap(colored_svg)))
                self.setIconSize(self.size())
        else:
            logging.warning(f"SVG icon not found: {self.svg_path}")
            self.setText("X" if "close" in self.svg_path else "_")

    def enterEvent(self, event):
        self.updateIconColor(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.updateIconColor(self.default_color)
        super().leaveEvent(event)

    def createColoredPixmap(self, svg_content):
        renderer = QSvgRenderer(bytes(svg_content, encoding='utf-8'))
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap


class DragArea(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")

        self._startPos = None
        self._is_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._startPos = event.globalPosition().toPoint()
            self._is_dragging = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and self._startPos:
            delta = event.globalPosition().toPoint() - self._startPos
            new_pos = self.parent.pos() + delta
            self.parent.move(new_pos)
            self._startPos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._startPos = None
            event.accept()

class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(80)  # Visina TopBar-a ostaje ista
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 0, 10, 0)
        main_layout.setSpacing(10)

        self.setup_logo(main_layout)

        right_layout = QHBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.drag_area = DragArea(self.parent)
        self.drag_area.setFixedHeight(25)  # Ograničite visinu drag_area
        self.drag_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        right_layout.addWidget(self.drag_area, alignment=Qt.AlignmentFlag.AlignTop)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 18, 10, 0)  # Minimalne margine
        button_layout.setSpacing(5)

        vertical_spacer = QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        button_layout.addSpacerItem(vertical_spacer)

        minimize_icon_path = os.path.join("resources", "minimize.svg")
        self.minimize_button = ColorChangingSvgButton(minimize_icon_path)
        self.minimize_button.setFixedSize(25, 25)
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        button_layout.addWidget(self.minimize_button, alignment=Qt.AlignmentFlag.AlignTop)

        close_icon_path = os.path.join("resources", "close.svg")
        self.close_button = ColorChangingSvgButton(close_icon_path)
        self.close_button.setFixedSize(25, 25)
        self.close_button.clicked.connect(self.parent.close)
        button_layout.addWidget(self.close_button, alignment=Qt.AlignmentFlag.AlignTop)

        right_layout.addLayout(button_layout)

        right_layout.setStretch(0, 1)
        right_layout.setStretch(1, 0)

        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def setup_logo(self, main_layout):
        logo_path = os.path.join("resources", "logo.svg")
        logging.debug(f"Attempting to load logo from: {logo_path}")
        if not os.path.exists(logo_path):
            self._setup_fallback_logo(main_layout)
        else:
            renderer = QSvgRenderer(logo_path)
            if not renderer.isValid():
                self._setup_fallback_logo(main_layout)
            else:
                self._setup_svg_logo(logo_path, renderer, main_layout)

    def _setup_fallback_logo(self, main_layout):
        logging.error("SVG Logo not found or invalid. Falling back to text logo.")
        self.logo_label = QLabel("LOGO")
        self.logo_label.setStyleSheet("color: white; font-size: 16px;")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(150, 50)
        main_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignLeft)

    def _setup_svg_logo(self, logo_path, renderer, main_layout):
        svg_size = renderer.defaultSize()
        desired_height = 50
        scaling_factor = desired_height / svg_size.height()
        desired_width = int(svg_size.width() * scaling_factor)

        self.logo_widget = QSvgWidget(logo_path)
        self.logo_widget.setFixedSize(desired_width, desired_height)
        self.logo_widget.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(self.logo_widget, alignment=Qt.AlignmentFlag.AlignLeft)
