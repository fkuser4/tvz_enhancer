from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QRectF, QTimer, QSize
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QFontMetrics, QCursor, QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtSvg import QSvgRenderer
import os

from src.tvz_enhancer.components.logout_button import LogoutButton
from src.tvz_enhancer.data.course import Course
from src.tvz_enhancer.modules.calendar_module import CalendarModule
from src.tvz_enhancer.modules.home_module import HomeModule
from src.tvz_enhancer.modules.notification_module import NotificationModule
from src.tvz_enhancer.modules.document_module import DocumentModule
from src.tvz_enhancer.modules.reservation_module import ReservationModule


class NavHighlight(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._color = QColor("white")
        self._logout_color = QColor("Red")
        self._radius = 5
        self._width = 5
        self.setFixedWidth(self._width)
        self.setFixedHeight(0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)

        rect = self.rect()
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right() - self._radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + self._radius)
        path.lineTo(rect.right(), rect.bottom() - self._radius)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - self._radius, rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()

        painter.drawPath(path)

class NavButton(QWidget):
    def __init__(self, text, svg_path, base_color="#ffffff", parent=None):
        super().__init__(parent)
        self.text = text
        self._svg_renderer = None
        self.svg_template = None

        self.base_color = QColor(base_color)
        if not self.base_color.isValid():
            self.base_color = QColor("#ffffff")

        self.active_color = self.base_color
        self.inactive_color = self.base_color.darker(160)
        self.hover_color = self.base_color.lighter(120)

        self._color = self.inactive_color
        self._is_active = False

        if svg_path:
            try:
                with open(svg_path, 'r') as f:
                    svg_content = f.read()
                    self.svg_template = svg_content.replace('fill="#000000"', 'fill="{{ICON_COLOR}}"')
                self._svg_renderer = QSvgRenderer()
                self.update_svg_renderer(self._color)
            except Exception as e:
                print(f"Error loading SVG: {e}")

        self.setMinimumWidth(200)
        self.adjust_height_to_text()

    def adjust_height_to_text(self):
        font = QFont("Arial", 13)
        font.setBold(True)
        metrics = QFontMetrics(font)
        text_height = metrics.height()
        self.setFixedHeight(text_height + 10)  # Add some padding

    def set_active(self, active):
        self._is_active = active
        if active:
            self._color = self.active_color
        else:
            self._color = self.inactive_color
        self.update_svg_renderer(self._color)
        self.update()

    def enterEvent(self, event):
        if not self._is_active:
            self._color = self.hover_color
            self.update_svg_renderer(self._color)
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_active:
            self._color = self.inactive_color
            self.update_svg_renderer(self._color)
            self.update()
        super().leaveEvent(event)

    def update_svg_renderer(self, color):
        if self.svg_template and self._svg_renderer:
            svg_colored = self.svg_template.replace('{{ICON_COLOR}}', color.name())
            if not self._svg_renderer.load(bytearray(svg_colored, encoding='utf-8')):
                print("Failed to load SVG with updated color.")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._svg_renderer:
            icon_size = 17
            y_center = (self.height() - icon_size) // 2
            self._svg_renderer.render(painter, QRectF(10, y_center, icon_size, icon_size))

        painter.setPen(self._color)
        font = QFont("Arial", 12)
        font.setWeight(QFont.Weight.DemiBold)
        if self.text == "Odjavite se":
            font.setWeight(QFont.Weight.DemiBold)
            font.setPointSize(10)

        painter.setFont(font)

        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.text)
        text_height = metrics.height()

        text_x = 40
        text_y = (self.height() + text_height) // 2 - metrics.descent()

        painter.drawText(text_x, text_y, self.text)

class MainNavigation(QWidget):
    def __init__(self, activeScreen, app_manager = None, student_name = None, parent=None):
        super().__init__(parent)
        self.student_name = student_name
        self.activeScreen = activeScreen
        self.button_frames = []
        self.current_selected_button = None
        self.app_manager = app_manager
        self.notification_module = NotificationModule()
        self.home_module = HomeModule()

        self.home_module.set_notification_module(self.notification_module)
        self.notification_module.home_module = self.home_module
        self.calendar_module = CalendarModule()
        self.document_module = DocumentModule()
        self.reservation_module = ReservationModule()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("QWidget { background-color: transparent; }")
        self.setFixedWidth(250)
        self.setContentsMargins(20, 0, 20, 0)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setSpacing(8)
        self.setLayout(layout)

        self.highlight = NavHighlight(self)
        self.highlight.hide()

        self.anim = QPropertyAnimation(self.highlight, b"pos")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        svg_path = os.path.normpath(os.path.join(current_dir, '..', 'resources'))

        buttons = [
            ("Pregled", "house.svg"),
            ("Obavijesti", "bell.svg"),
            ("Raspored", "calendar2.svg"),
            ("Datoteke", "file-text.svg"),
            ("Rezervacije labosa", "flask-conical.svg"),
        ]

        for name, icon_filename in buttons:
            frame = QWidget()
            layout_h = QHBoxLayout(frame)
            layout_h.setContentsMargins(0, 0, 0, 0)
            layout_h.setSpacing(0)

            nav_button = NavButton(name, os.path.join(svg_path, icon_filename))
            nav_button.mousePressEvent = lambda e, b=nav_button, f=frame: self.on_button_click(b, f)

            layout_h.addWidget(nav_button)
            layout.addWidget(frame)
            self.button_frames.append((nav_button, frame))

        frame = QWidget()
        layout_h = QHBoxLayout(frame)
        layout_h.setContentsMargins(0, 0, 0, 0)
        layout_h.setSpacing(0)

        logout_button = LogoutButton("Odjavite se", os.path.join(svg_path, "logout.svg"))
        logout_button.mousePressEvent = lambda e, b=logout_button, f=frame: self.handleLogout(b, f)

        layout_h.addWidget(logout_button)

        # Add a spacer to the right of the logout button
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout_h.addItem(spacer)

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)

        layout.addWidget(frame)

        if self.button_frames:
            first_button, first_frame = self.button_frames[0]
            QTimer.singleShot(0, lambda: self.on_button_click(first_button, first_frame))



    def on_button_click(self, clicked_button, clicked_frame):
        self.move_highlight(clicked_frame, clicked_button)
        self.update_button_colors(clicked_button)

        module_map = {
            "Pregled": (self.home_module, f"Pozdrav, {self.student_name}"),
            "Obavijesti": (self.notification_module, "Obavijesti"),
            "Raspored": (self.calendar_module, "Raspored"),
            "Datoteke": (self.document_module, "Datoteke"),
            "Rezervacije labosa": (self.reservation_module, "Rezervacija labosa")
        }

        if clicked_button.text in module_map:
            module, title = module_map[clicked_button.text]

            self.activeScreen.swapModule(module)
            self.activeScreen.top_bar.setText(title)

    def handleLogout(self, clicked_button, clicked_frame):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_file_path = os.path.normpath(os.path.join(current_dir, '..', 'cookies.json'))

        try:
            with open(cookies_file_path, "w", encoding="utf-8") as f:
                f.write("[]")
        except Exception as e:
            print(f"Dogodila se greška prilikom brisanja sadržaja: {e}")

        self.app_manager.switch_to("login")


    def move_highlight(self, target_frame, clicked_button):
        if not self.highlight.isVisible():
            self.init_highlight_geometry(target_frame, clicked_button)
            return

        start_pos = self.highlight.pos()
        text_height = clicked_button.height() - 7
        frame_top = target_frame.mapTo(self, target_frame.rect().topLeft()).y()
        end_y = frame_top + (clicked_button.height() - text_height) // 2

        self.anim.stop()
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(QPoint(0, end_y))
        self.anim.start()
        self.highlight.setFixedHeight(text_height)

    def init_highlight_geometry(self, target_frame, clicked_button):
        text_height = clicked_button.height() - 7
        frame_top = target_frame.mapTo(self, target_frame.rect().topLeft()).y() + 12

        self.highlight.setGeometry(0, frame_top, self.highlight.width(), text_height)
        self.highlight.setFixedHeight(text_height)
        self.highlight.show()

    def update_button_colors(self, clicked_button):
        for button, _ in self.button_frames:
            button.set_active(button == clicked_button)
