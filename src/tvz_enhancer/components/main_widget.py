from PyQt6.QtCore import QSequentialAnimationGroup, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self._colorValue = 0.0

        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(pal)

        self.bgAnimForward = QPropertyAnimation(self, b"colorValue", self)
        self.bgAnimForward.setDuration(1300)  # 2s
        self.bgAnimForward.setStartValue(0.0)
        self.bgAnimForward.setEndValue(1.0)

        self.bgAnimBackward = QPropertyAnimation(self, b"colorValue", self)
        self.bgAnimBackward.setDuration(1300)
        self.bgAnimBackward.setStartValue(1.0)
        self.bgAnimBackward.setEndValue(0.0)

        self.animGroup = QSequentialAnimationGroup(self)
        self.animGroup.addAnimation(self.bgAnimForward)
        self.animGroup.addAnimation(self.bgAnimBackward)
        self.animGroup.setLoopCount(-1)

    def start_pulsing(self):
        if not self.animGroup.state() == QPropertyAnimation.State.Running:
            self.animGroup.start()
    def stop_pulsing(self):
        if self.animGroup.state() == QPropertyAnimation.State.Running:
            self.animGroup.stop()

    @pyqtProperty(float)
    def colorValue(self):
        return self._colorValue

    @colorValue.setter
    def colorValue(self, val):
        self._colorValue = val

        c1 = QColor("#000000")
        c2 = QColor("#1a1a1a")
        r = c1.red() + (c2.red() - c1.red()) * val
        g = c1.green() + (c2.green() - c1.green()) * val
        b = c1.blue() + (c2.blue() - c1.blue()) * val

        newColor = QColor(int(r), int(g), int(b))
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, newColor)
        self.setPalette(pal)