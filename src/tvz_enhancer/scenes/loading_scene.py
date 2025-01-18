from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from src.tvz_enhancer.backup import SpinningLoader
from src.tvz_enhancer.scenes.dashboard_scene import DashboardScene

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from src.tvz_enhancer.backup import SpinningLoader
from src.tvz_enhancer.scenes.dashboard_scene import DashboardScene


class LoadingScene(QWidget):
    def __init__(self, manager):
        super().__init__()
        self.spinning_loader = None
        self.manager = manager
        self.dashboard_scene = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.spinning_loader = SpinningLoader()
        layout.addWidget(self.spinning_loader, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def load_dashboard(self):
        QTimer.singleShot(300, self._create_dashboard)

    def _create_dashboard(self):
        try:
            self.dashboard_scene = DashboardScene(self.manager)

            QTimer.singleShot(200, self._check_dashboard)

        except Exception as e:
            print(f"Error creating dashboard: {e}")
            self._switch_to_login()

    def _check_dashboard(self):
        try:
            if not self.dashboard_scene or not hasattr(self.dashboard_scene, 'navigation'):
                print("Dashboard initialization incomplete - returning to login")
                self._switch_to_login()
                return

            if not hasattr(self.dashboard_scene, 'login_is') or self.dashboard_scene.login_is is False:
                print("Not logged in - returning to login")
                self._switch_to_login()
                return

            self.manager.add_scene("dashboard", self.dashboard_scene)

            self.dashboard_scene.dataApi.first_load_signal.connect(self._on_first_data_load)

            if not self.dashboard_scene.dataApi.first_load:
                print("Waiting for initial data load...")

        except Exception as e:
            print(f"Error checking dashboard: {e}")
            self._switch_to_login()

    def _on_first_data_load(self, loaded):
        if loaded:
            QTimer.singleShot(100, lambda: self.manager.switch_to("dashboard"))

    def _switch_to_login(self):
        QTimer.singleShot(50, lambda: self.manager.switch_to("login"))