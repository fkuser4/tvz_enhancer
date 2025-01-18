import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QFrame
)

from src.tvz_enhancer.components.active_screen import ActiveScreen
from src.tvz_enhancer.components.main_navigation import MainNavigation
from src.tvz_enhancer.data.data_api import DataApiThread
from src.tvz_enhancer.modules.home_module import HomeModule


class DashboardScene(QWidget):
    def __init__(self, app_manager=None):
        super().__init__()
        self.app_manager = app_manager
        self.name = QLabel("Name")
        self.navigation = None
        self.login_is = True
        self.main_layout_frame = None

        self.dataApi = DataApiThread()
        self.student_name = self.dataApi.get_student_name()

        if not self.student_name:
            self.login_is = False
            return

        self.init_ui()

        if self.main_layout_frame:
            self.main_layout_frame.hide()

        self.dataApi.first_load_signal.connect(self.on_first_load)

    def on_first_load(self, loaded):
        if loaded and self.main_layout_frame:
            self.main_layout_frame.show()

    def init_ui(self):
        activeScreen = ActiveScreen(HomeModule())
        self.navigation = MainNavigation(activeScreen, self.app_manager, self.student_name)

        self.dataApi.notification_updated.connect(self.navigation.notification_module.add_notification)
        self.dataApi.files_updated.connect(self.navigation.document_module.add_new_file)
        self.dataApi.reservation_links_signal.connect(self.navigation.reservation_module.add_crucial_data)
        self.dataApi.start()

        dashboard_layout = QVBoxLayout(self)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout_frame = QFrame()
        self.main_layout_frame.setObjectName("MainFrame")
        self.main_layout_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.main_layout_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.main_layout_frame.setStyleSheet("""
            #MainFrame {
                border-top: 0px solid #283039;
            }
        """)

        frame_layout = QHBoxLayout(self.main_layout_frame)
        frame_layout.setSpacing(20)
        frame_layout.setContentsMargins(0, 10, 10, 10)


        self.navigation.setFixedWidth(270)
        activeScreen.setContentsMargins(0, 10, 0, 0)

        frame_layout.addWidget(self.navigation)
        frame_layout.addWidget(activeScreen, stretch=1)

        dashboard_layout.addWidget(self.main_layout_frame)

        self.setLayout(dashboard_layout)