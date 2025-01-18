from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QParallelAnimationGroup
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.uic.properties import QtCore

from src.tvz_enhancer.components import AnimatedButton
from src.tvz_enhancer.components.sso_login_window import SSOLoginWindow


class LoginScene(QWidget):

    def __init__(self, app_manager):
        super().__init__()
        self.sso_window = None
        self.app_manager = app_manager
        self.loginButton = None
        self.loginContent = None
        self.mainLayout = None
        self.fadeOutLogin = None
        self.loginOpacity = None
        self.fadeGroup = None
        self.init_ui()

    def init_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAutoFillBackground(True)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.mainLayout)

        self.loginContent = QWidget()
        self.loginContent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        loginLayout = QVBoxLayout(self.loginContent)
        loginLayout.setContentsMargins(20, 20, 20, 100)
        loginLayout.setSpacing(20)
        loginLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titleLabel = QLabel("Prijava")
        titleLabel.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.loginButton = AnimatedButton("Microsoft SSO")
        self.loginButton.clicked.connect(self.onLoginClicked)

        infoLabel = QLabel("Prijavite se koristeći svoj Microsoft račun.")
        infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        infoLabel.setStyleSheet("color: #a0a0a0; font-size: 12px;")

        loginLayout.addWidget(titleLabel)
        loginLayout.addWidget(self.loginButton)
        loginLayout.addWidget(infoLabel)

        self.mainLayout.addWidget(self.loginContent)

    def onLoginClicked(self):
        self.loginButton.setEnabled(False)
        self.loginButton.setText("Prijava u tijeku...")

        self.sso_window = SSOLoginWindow()
        self.sso_window.login_completed.connect(self.onLoginContentFaded)
        self.sso_window.login_canceled.connect(self.onLoginCanceled)
        self.sso_window.show()

    def onLoginCanceled(self):
        self.loginButton.setEnabled(True)
        self.loginButton.setText("Microsoft SSO")

    def onLoginContentFaded(self):
        self.loginOpacity = QGraphicsOpacityEffect(self.loginContent)
        self.loginContent.setGraphicsEffect(self.loginOpacity)
        self.fadeOutLogin = QPropertyAnimation(self.loginOpacity, b"opacity")
        self.fadeOutLogin.setDuration(1300)
        self.fadeOutLogin.setStartValue(0.80)
        self.fadeOutLogin.setEndValue(0.0)
        self.fadeOutLogin.finished.connect(self.switchToLoading)
        self.fadeOutLogin.start()

    def switchToLoading(self):
        self.app_manager.switch_to("loading")

