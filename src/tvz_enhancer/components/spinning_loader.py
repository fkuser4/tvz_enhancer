from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QColor, QPainter
from PyQt6.QtWidgets import QWidget


class SpinningLoader(QWidget):

    def __init__(self, diameter=80, parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)

        self._angle = 0
        self.timerID = self.startTimer(16)

    def timerEvent(self, event):
        if event.timerId() == self.timerID:
            self._angle = (self._angle + 5) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        radius = self.diameter / 2.0
        pen_width = 4

        x = y = -radius + pen_width / 2
        w = h = 2 * radius - pen_width

        painter.setPen(QPen(QColor("#ffffff"), pen_width, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        startAngle = 90 * 16
        spanAngle  = 270 * 16

        painter.drawArc(int(x), int(y), int(w), int(h), startAngle, spanAngle)
