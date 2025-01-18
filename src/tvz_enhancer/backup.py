import sys
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QSequentialAnimationGroup,
    pyqtProperty, pyqtSignal
)
from PyQt6.QtGui import (
    QGuiApplication, QPainter, QPalette, QColor, QPen
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QGraphicsOpacityEffect, QGraphicsDropShadowEffect
)

###############################################################################
# Pulsing Background
###############################################################################
class PulsingBackground(QWidget):
    """
    Background that smoothly fades #000000 <-> #1a1a1a over 4s total (2s each way).
    Starts pulsing only when start_pulsing() is called.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self._colorValue = 0.0

        # Initial color: black
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(pal)

        # Forward animation: 0.0 -> 1.0 (black -> #1a1a1a)
        self.bgAnimForward = QPropertyAnimation(self, b"colorValue", self)
        self.bgAnimForward.setDuration(2000)  # 2s
        self.bgAnimForward.setStartValue(0.0)
        self.bgAnimForward.setEndValue(1.0)

        # Backward animation: 1.0 -> 0.0 (#1a1a1a -> black)
        self.bgAnimBackward = QPropertyAnimation(self, b"colorValue", self)
        self.bgAnimBackward.setDuration(2000)  # 2s
        self.bgAnimBackward.setStartValue(1.0)
        self.bgAnimBackward.setEndValue(0.0)

        # Sequence them in a loop
        self.animGroup = QSequentialAnimationGroup(self)
        self.animGroup.addAnimation(self.bgAnimForward)
        self.animGroup.addAnimation(self.bgAnimBackward)
        self.animGroup.setLoopCount(-1)  # Infinite loop

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
        # Interpolate black(0.0) -> #1a1a1a(1.0)
        c1 = QColor("#000000")
        c2 = QColor("#1a1a1a")
        r = c1.red()   + (c2.red()   - c1.red())   * val
        g = c1.green() + (c2.green() - c1.green()) * val
        b = c1.blue()  + (c2.blue()  - c1.blue())  * val

        newColor = QColor(int(r), int(g), int(b))
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, newColor)
        self.setPalette(pal)


###############################################################################
# Spinning Loader
###############################################################################
class SpinningLoader(QWidget):
    """
    A typical "border-top: transparent" CSS spinner:
      - White arc for 270°,
      - Transparent 90° at the top.
      - Slow rotation for a smooth effect (~60 FPS, +5° per frame).
    """
    def __init__(self, diameter=80, parent=None):
        super().__init__(parent)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)

        self._angle = 0
        # ~60 FPS refresh => 16 ms timer
        self.timerID = self.startTimer(16)

    def timerEvent(self, event):
        if event.timerId() == self.timerID:
            # Rotate slower: +5 deg per frame => one full rotation ~72 frames => ~1.15s
            self._angle = (self._angle + 5) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Move origin to center & rotate
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        radius = self.diameter / 2.0
        pen_width = 4

        # We will draw an arc from 90° to 360° => 270° total in white,
        # leaving the top 90° effectively "transparent."
        x = y = -radius + pen_width / 2
        w = h = 2 * radius - pen_width

        # White pen for the arc
        painter.setPen(QPen(QColor("#ffffff"), pen_width, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Start angle = 90°, span = 270°
        # Angles in Qt are specified in 1/16 deg => 90*16 to 360*16
        startAngle = 90 * 16
        spanAngle  = 270 * 16

        painter.drawArc(int(x), int(y), int(w), int(h), startAngle, spanAngle)


###############################################################################
# Animated Button
###############################################################################
class AnimatedButton(QWidget):
    """
    Hover-animated button:
      - Black<->White background fade,
      - White<->Black text fade,
      - White glow on hover,
      - Emits "clicked" signal on left click.
    """
    clicked = pyqtSignal()

    def __init__(self, text="Button", parent=None):
        super().__init__(parent)
        self._bgValue = 0.0
        self._glowAlpha = 0.0
        self._text = text

        self.setFixedHeight(48)

        # Glow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(255, 255, 255, 0))  # alpha=0 initially
        self.setGraphicsEffect(self.shadow)

        # Animations
        self.animBg = QPropertyAnimation(self, b"bgValue")
        self.animBg.setDuration(500)  # longer => smoother
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
        # White glow alpha 0->255
        c = QColor(255, 255, 255, int(val * 255))
        self.shadow.setColor(c)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Interpolate background black->white
        black_bg = QColor("#000000")
        white_bg = QColor("#ffffff")
        br = black_bg.red()   + (white_bg.red()   - black_bg.red())   * self._bgValue
        bg = black_bg.green() + (white_bg.green() - black_bg.green()) * self._bgValue
        bb = black_bg.blue()  + (white_bg.blue()  - black_bg.blue())  * self._bgValue
        backgroundColor = QColor(int(br), int(bg), int(bb))

        # Interpolate text white->black
        white_fg = QColor("#ffffff")
        black_fg = QColor("#000000")
        fr = white_fg.red()   + (black_fg.red()   - white_fg.red())   * self._bgValue
        fg = white_fg.green() + (black_fg.green() - white_fg.green()) * self._bgValue
        fb = white_fg.blue()  + (black_fg.blue()  - white_fg.blue())  * self._bgValue
        textColor = QColor(int(fr), int(fg), int(fb))

        # Draw background + border
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(backgroundColor)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.drawRect(rect)

        # Draw text
        painter.setPen(textColor)
        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._text)

    def enterEvent(self, event):
        # Animate to "hover" state: bgValue=1, glowAlpha=1
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
        # Animate back to "normal" state: bgValue=0, glowAlpha=0
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


###############################################################################
# Main Window
###############################################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prijava")

        # 75% screen size
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = int(screen.width() * 0.75)
        h = int(screen.height() * 0.75)
        self.resize(w, h)

        # Pulsing background
        self.bgWidget = PulsingBackground()
        self.setCentralWidget(self.bgWidget)

        # Main layout
        self.mainLayout = QVBoxLayout(self.bgWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # -- Login container --
        self.loginContent = QWidget()
        self.loginLayout = QVBoxLayout(self.loginContent)
        self.loginLayout.setContentsMargins(20, 20, 20, 20)
        self.loginLayout.setSpacing(20)
        self.loginLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loginContent.setMaximumWidth(320)

        # Title
        self.titleLabel = QLabel("Prijava")
        self.titleLabel.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Animated button
        self.loginButton = AnimatedButton("Microsoft SSO")
        self.loginButton.clicked.connect(self.onLoginClicked)

        # Info label
        self.infoLabel = QLabel("Prijavite se koristeći svoj Microsoft račun.")
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infoLabel.setStyleSheet("color: #a0a0a0; font-size: 12px;")

        # Add to layout
        self.loginLayout.addWidget(self.titleLabel)
        self.loginLayout.addWidget(self.loginButton)
        self.loginLayout.addWidget(self.infoLabel)

        # Opacity effect for fade-out
        self.loginOpacity = QGraphicsOpacityEffect(self.loginContent)
        self.loginContent.setGraphicsEffect(self.loginOpacity)

        self.mainLayout.addWidget(self.loginContent, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spinner
        self.spinner = SpinningLoader(diameter=80)
        self.spinner.setVisible(False)
        self.spinnerOpacity = QGraphicsOpacityEffect()
        self.spinner.setGraphicsEffect(self.spinnerOpacity)
        self.spinnerOpacity.setOpacity(0.0)

        self.mainLayout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Fade animations
        self.fadeOutLogin = QPropertyAnimation(self.loginOpacity, b"opacity")
        self.fadeOutLogin.setDuration(1300)
        self.fadeOutLogin.setStartValue(0.75)
        self.fadeOutLogin.setEndValue(0.0)
        self.fadeOutLogin.finished.connect(self.onLoginContentFaded)

        self.fadeInSpinner = QPropertyAnimation(self.spinnerOpacity, b"opacity")
        self.fadeInSpinner.setDuration(800)
        self.fadeInSpinner.setStartValue(0.0)
        self.fadeInSpinner.setEndValue(1.0)

        self._animations = [self.fadeOutLogin, self.fadeInSpinner]  # keep references

    def onLoginClicked(self):
        """
        1) Change the button text to "Prijava u tijeku..."
        2) Disable the button
        3) After 3s, fade out the login content, fade in the spinner.
        """
        self.loginButton.setEnabled(False)
        self.loginButton.setText("Prijava u tijeku...")

        QTimer.singleShot(3000, self.fadeOutLogin.start)

    def onLoginContentFaded(self):
        # Hide the login content
        self.loginContent.hide()
        # Show spinner, fade it in
        self.spinner.show()
        self.fadeInSpinner.start()
        # Start the background pulsing after spinner is visible
        self.bgWidget.start_pulsing()

def main():
    app = QApplication(sys.argv)

    # Global style: black background, white text, Arial
    app.setStyleSheet("""
        QWidget:not(.PulsingBackground) {
            background-color: #000000;
            color: #ffffff;
            font-family: Arial, sans-serif;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()