import time

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.tvz_enhancer.components.flow_layout import FlowLayout
from src.tvz_enhancer.components.notification_item import NotificationItem
from src.tvz_enhancer.components.notification_tag import NotificationTag


class NotificationModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications = []
        self.active_tag = "all"
        self.tag_buttons = {}
        self.tags = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;  /* Željena pozadinska boja sekcije*/
                border: none;
                border-radius: 0px;
            }
        """)
        main_layout.addWidget(main_frame)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(20)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Pretraži obavijesti...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 10px 15px;
                margin-left: 7px;
                border: 2px solid #1A1A1A;
                border-radius: 6px;
                font-size: 16px;
                background-color: #141414;
                color: #918d8d;
            }
            QLineEdit:focus {
                border-color: red;
                border-color: white;
                border: 1px solid #d1cfcf;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_notifications)
        frame_layout.addWidget(self.search_bar)

        self.tags_layout = FlowLayout()
        self.tags_layout.setContentsMargins(7, 0, 7, 0)
        self.tags_layout.setSpacing(10)
        frame_layout.addLayout(self.tags_layout)

        allBtn = self.create_tag_button("All", is_all=False)
        if allBtn:
            allBtn.click()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QScrollBar:vertical {
                width: 0px;
                background: transparent;
            }
        """)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)

        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.scroll_area)

        self.notifications_frame = QFrame()
        self.notifications_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.notifications_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-radius: 0;
                margin: 0;
            }
        """)
        self.notifications_frame.setContentsMargins(10, 20, 0, 0)

        self.notifications_layout = QVBoxLayout()
        self.notifications_layout.setContentsMargins(0, 0, 0, 0)
        self.notifications_layout.setSpacing(10)

        self.notifications_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.notifications_frame.setLayout(self.notifications_layout)

        self.scroll_area.setWidget(self.notifications_frame)

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        super().closeEvent(event)

    def create_tag_button(self, subject, is_all=False):
        normalized_subject = subject.strip().lower()
        if normalized_subject in self.tag_buttons:
            return

        tag_button = NotificationTag(subject)
        tag_button.clicked.connect(self.toggle_tag)
        self.tags_layout.addWidget(tag_button)
        self.tag_buttons[normalized_subject] = tag_button

        if is_all:
            tag_button.setChecked(True)
            self.active_tag = normalized_subject

        return tag_button

    def toggle_tag(self):
        sender = self.sender()
        normalized_subject = sender.text().strip().lower()

        if sender.isChecked():
            if self.active_tag and self.active_tag != normalized_subject:
                previous_button = self.tag_buttons.get(self.active_tag)
                if previous_button:
                    previous_button.setChecked(False)
            self.active_tag = normalized_subject
        else:
            if normalized_subject != "all":
                sender.setChecked(True)
                return
            else:
                self.active_tag = "all"

        self.filter_notifications()

    def add_notification(self, notification):
        for predmet, vrijednosti in notification.items():
            if predmet not in self.tags:
                self.tags.insert(0, predmet)
                self.create_tag_button(predmet)

            notification = NotificationItem(vrijednosti["title"], vrijednosti["message"], predmet, vrijednosti["time"], 150)
            self.notifications.insert(0, notification)
            self.notifications_layout.insertWidget(0, notification)

            if hasattr(self, 'home_module') and self.home_module:
                self.home_module.refresh_recent_notifications()

    def filter_notifications(self, text=None):
        search_text = self.search_bar.text().lower()
        for notification in self.notifications:
            matches_search = (
                search_text in notification.title.lower() or
                search_text in notification.content.lower() or
                search_text in notification.subject.lower()
            )

            normalized_subject = notification.subject.strip().lower()

            if self.active_tag == "all":
                matches_tag = True
            else:
                matches_tag = (
                    normalized_subject == self.active_tag
                )

            if matches_search and matches_tag:
                notification.show()
            else:
                notification.hide()
