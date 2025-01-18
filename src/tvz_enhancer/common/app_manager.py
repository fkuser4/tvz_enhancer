from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel
)
from PyQt6.QtCore import Qt, QPoint, QRect, QObject, QEvent, QTimer
import logging

from src.tvz_enhancer.components.main_widget import MainWidget
from src.tvz_enhancer.components.top_bar import TopBar
from src.tvz_enhancer.scenes.loading_scene import LoadingScene

logging.basicConfig(level=logging.DEBUG)


class AppManager(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1000, 600)
        self.setMaximumSize(1890, 1024)

        self.scene_stack = QStackedWidget()
        self.scenes = {}


        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.top_bar = TopBar(self)
        self.top_bar.setContentsMargins(0,0,0,0)
        self.main_layout.addWidget(self.top_bar)

        self.main_layout.addWidget(self.scene_stack)

        self.main_widget = MainWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)

        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.75)
        height = int(screen.height() * 0.75)
        width = 1440
        height = 810
        self.resize(width, height)

        self._startPos = None
        self._resizing = False
        self._resize_direction = None
        self._margin = 5


        self.setMouseTracking(True)
        self.main_widget.setMouseTracking(True)
        self.scene_stack.setMouseTracking(True)

        self.center_window()
        QApplication.instance().installEventFilter(self)

    def center_window(self):
        screen = QScreen.availableGeometry(QApplication.primaryScreen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:

        if event.type() == QEvent.Type.MouseMove:
            return self.handle_mouse_move(event)
        elif event.type() == QEvent.Type.MouseButtonPress:
            return self.handle_mouse_press(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            return self.handle_mouse_release(event)
        return super().eventFilter(obj, event)

    def handle_mouse_move(self, event):

        global_pos = event.globalPosition().toPoint()
        local_pos = self.mapFromGlobal(global_pos)

        if self._resizing and self._resize_direction:
            self._resize_window(global_pos)
            self._set_cursor_for_direction(self._resize_direction)
            return True

        direction = self._get_resize_direction(local_pos)
        if direction:
            self._set_cursor_for_direction(direction)
        else:
            self.unsetCursor()

        return False

    def handle_mouse_press(self, event):

        if event.button() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(global_pos)

            self._resize_direction = self._get_resize_direction(local_pos)
            self._resizing = self._resize_direction is not None

            if self._resizing:
                self._startPos = global_pos
                return True

        return False

    def handle_mouse_release(self, event):

        if event.button() == Qt.MouseButton.LeftButton and self._resizing:
            self._resizing = False
            self._resize_direction = None
            self.unsetCursor()
            return True

        return False

    def _get_resize_direction(self, pos):

        rect = self.rect()
        x, y = pos.x(), pos.y()
        width, height = rect.width(), rect.height()

        directions = {
            'left': x < self._margin,
            'right': x > width - self._margin,
            'top': y < self._margin,
            'bottom': y > height - self._margin
        }

        horizontal = None
        vertical = None

        if directions['left']:
            horizontal = 'left'
        elif directions['right']:
            horizontal = 'right'

        if directions['top']:
            vertical = 'top'
        elif directions['bottom']:
            vertical = 'bottom'

        if horizontal and vertical:
            return f"{vertical}-{horizontal}"
        elif horizontal:
            return horizontal
        elif vertical:
            return vertical
        return None

    def _set_cursor_for_direction(self, direction):

        cursor_map = {
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor
        }
        cursor_shape = cursor_map.get(direction, Qt.CursorShape.ArrowCursor)
        self.setCursor(cursor_shape)

    def _resize_window(self, global_pos):

        if not self._startPos:
            return

        delta = global_pos - self._startPos
        self._startPos = global_pos

        geometry = self.geometry()
        min_width = self.minimumWidth()
        min_height = self.minimumHeight()
        new_geometry = QRect(geometry)

        if "left" in self._resize_direction:
            new_left = geometry.left() + delta.x()
            if geometry.width() - delta.x() >= min_width:
                new_geometry.setLeft(new_left)

        if "right" in self._resize_direction:
            new_right = geometry.right() + delta.x()
            if geometry.width() + delta.x() >= min_width:
                new_geometry.setRight(new_right)

        if "top" in self._resize_direction:
            new_top = geometry.top() + delta.y()
            if geometry.height() - delta.y() >= min_height:
                new_geometry.setTop(new_top)

        if "bottom" in self._resize_direction:
            new_bottom = geometry.bottom() + delta.y()
            if geometry.height() + delta.y() >= min_height:
                new_geometry.setBottom(new_bottom)

        self.setGeometry(new_geometry)

    def add_scene(self, name, widget):

        if name == "loading":
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
            container.setLayout(layout)
            self.scenes[name] = container
            container.setContentsMargins(0,0,0,100)
            self.scene_stack.addWidget(container)
        else:
            self.scenes[name] = widget
            self.scene_stack.addWidget(widget)

        widget.setMouseTracking(True)

    def switch_to(self, name):

        if name in self.scenes:
            if name == "loading":
                self.scene_stack.setCurrentWidget(self.scenes["loading"])
                QTimer.singleShot(100, self._load_dashboard)
            else:
                self.scene_stack.setCurrentWidget(self.scenes[name])
        else:
            raise ValueError(f"Scene '{name}' not found.")

    def _load_dashboard(self):
        loading_scene = self.scenes["loading"].findChild(LoadingScene)
        if loading_scene:
            loading_scene.load_dashboard()

