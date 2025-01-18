from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRectF, QSize
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QFontMetrics, QCursor, QBrush
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtSvg import QSvgRenderer
import os


class LogoutButton(QWidget):
    def __init__(self, text, svg_path, parent=None):
        super().__init__(parent)

        self._text = text
        self._svg_renderer = None
        self.svg_template = None
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._black = QColor("#000000")
        self._ch_black = QColor("#141414")
        self._eer_black = QColor("#1b1b1b")
        self._night_rider = QColor("#262626")
        self._white = QColor("#ffffff")
        self._af_white = QColor("#f3f3f3")
        self._ch_white = QColor("#e1e1e1")

        self._background_color = self._night_rider

        self.text_visible = False

        if svg_path:
            try:
                with open(svg_path, 'r') as f:
                    svg_content = f.read()
                    self.svg_template = svg_content.replace('fill="#000000"', 'fill="{{ICON_COLOR}}"')
                self._svg_renderer = QSvgRenderer()
                self.update_svg_renderer(self._af_white)
            except Exception as e:
                print(f"Error loading SVG: {e}")

        self.setMinimumSize(40, 40)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.anim = QPropertyAnimation(self, b"size")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def update_svg_renderer(self, color):
        if self.svg_template and self._svg_renderer:
            svg_colored = self.svg_template.replace('{{ICON_COLOR}}', color.name())
            if not self._svg_renderer.load(bytearray(svg_colored, encoding='utf-8')):
                print("Failed to load SVG with updated color.")

    def get_text_width(self):
        font = QFont("Arial", 12, QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        return metrics.horizontalAdvance(self._text)

    def get_text_height(self):
        font = QFont("Arial", 12, QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        return metrics.height()

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.size())
        self.anim.setEndValue(QSize(140, 40))
        self.anim.start()
        self.text_visible = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.size())
        self.anim.setEndValue(QSize(40, 40))
        self.anim.start()
        self.text_visible = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.move(self.pos().x() + 2, self.pos().y() + 2)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.move(self.pos().x() - 2, self.pos().y() - 2)
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(self._background_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 5, 5)

        icon_size = 17
        y_center = (self.height() - icon_size) // 2
        if self._svg_renderer:
            self._svg_renderer.render(painter, QRectF(10, y_center, icon_size, icon_size))

        if self.text_visible:
            text_x = 45
            text_y = (self.height() + self.get_text_height()) // 2 - 2
            painter.setPen(self._af_white)
            font = QFont("Arial", 12, QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(text_x, text_y, self._text)