import os
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QColor, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget


class AnimatedButton(QWidget):
    clicked = pyqtSignal()

    def __init__(self, text="Button", svg_path="../tvz_enhancer/resources/windows.svg", parent=None):
        super().__init__(parent)
        self._bgValue = 0.0
        self._glowAlpha = 0.0
        self._text = text
        self._svg_path = svg_path
        self._svg_renderer = None
        self.svg_template = None

        if svg_path:
            absolute_svg_path = os.path.abspath(svg_path)
            try:
                with open(absolute_svg_path, 'r') as f:
                    svg_content = f.read()
                    self.svg_template = svg_content.replace('fill="#000000"', 'fill="{{ICON_COLOR}}"')
            except Exception as e:
                print(f"Error reading SVG file: {absolute_svg_path}\n{e}")

            if self.svg_template:
                self._svg_renderer = QSvgRenderer()
                self.update_svg_renderer(QColor("#000000"))
                if not self._svg_renderer.isValid():
                    print(f"Failed to load modified SVG from: {absolute_svg_path}")

        self.setFixedHeight(48)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(255, 255, 255, 0))
        self.setGraphicsEffect(self.shadow)

        self.animBg = QPropertyAnimation(self, b"bgValue")
        self.animBg.setDuration(500)
        self.animGlow = QPropertyAnimation(self, b"glowAlpha")
        self.animGlow.setDuration(500)

        self.setMouseTracking(True)

    @pyqtProperty(float)
    def bgValue(self):
        return self._bgValue

    @bgValue.setter
    def bgValue(self, val):
        self._bgValue = val
        self.update()

    @pyqtProperty(float)
    def glowAlpha(self):
        return self._glowAlpha

    @glowAlpha.setter
    def glowAlpha(self, val):
        self._glowAlpha = val
        c = QColor(255, 255, 255, int(val * 255))
        self.shadow.setColor(c)

    def update_svg_renderer(self, color):
        if self.svg_template and self._svg_renderer:
            svg_colored = self.svg_template.replace('{{ICON_COLOR}}', color.name())
            if not self._svg_renderer.load(bytearray(svg_colored, encoding='utf-8')):
                print("Failed to load colored SVG into QSvgRenderer.")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        black_bg = QColor("#000000")
        white_bg = QColor("#ffffff")

        br = black_bg.red() + (white_bg.red() - black_bg.red()) * self._bgValue
        bg = black_bg.green() + (white_bg.green() - black_bg.green()) * self._bgValue
        bb = black_bg.blue() + (white_bg.blue() - black_bg.blue()) * self._bgValue
        backgroundColor = QColor(int(br), int(bg), int(bb))

        white_fg = QColor("#ffffff")
        black_fg = QColor("#000000")
        fr = white_fg.red() + (black_fg.red() - white_fg.red()) * self._bgValue
        fg = white_fg.green() + (black_fg.green() - white_fg.green()) * self._bgValue
        fb = white_fg.blue() + (black_fg.blue() - white_fg.blue()) * self._bgValue
        textColor = QColor(int(fr), int(fg), int(fb))

        self.update_svg_renderer(textColor)

        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(backgroundColor)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.drawRect(rect)

        if self._svg_renderer:
            icon_size = 19
            icon_rect = QRectF(45, (self.height() - icon_size) / 2, icon_size, icon_size)
            self._svg_renderer.render(painter, icon_rect)

        painter.setPen(textColor)
        font = painter.font()
        font.setPointSize(13)
        painter.setFont(font)
        text_rect = self.rect().adjusted(45, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self._text)

    def enterEvent(self, event):
        self.animBg.stop()
        self.animBg.setStartValue(self._bgValue)
        self.animBg.setEndValue(1.0)
        self.animBg.start()

        self.animGlow.stop()
        self.animGlow.setStartValue(self._glowAlpha)
        self.animGlow.setEndValue(1.0)
        self.animGlow.start()

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animBg.stop()
        self.animBg.setStartValue(self._bgValue)
        self.animBg.setEndValue(0.0)
        self.animBg.start()

        self.animGlow.stop()
        self.animGlow.setStartValue(self._glowAlpha)
        self.animGlow.setEndValue(0.0)
        self.animGlow.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def setText(self, text):
        self._text = text
        self.update()

