import sys
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QDate, QSize
from src.tvz_enhancer.utils.local_storage import load_local_events


class ActionCard(QFrame):


    def __init__(self, title, actions):
        super().__init__()
        self.setObjectName("actionCard")
        self.setStyleSheet("""
            #actionCard {
                background-color: #111111;
                border: 1px solid #2A2A2A;
                border-radius: 8px;
            }
        """)

        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        header = QLabel(title)
        header.setStyleSheet("color: #E0E0E0; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch(1)

        layout.addLayout(header_layout)

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)

        for row in actions:
            row_layout = QHBoxLayout()
            for action, url in row:
                button = QPushButton(action)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #1E1E1E;
                        border: 1px solid #2A2A2A;
                        border-radius: 8px;
                        color: #E0E0E0;
                        font-size: 14px;
                        padding: 10px 20px;
                    }
                    QPushButton:hover {
                        background-color: #2A2A2A;
                    }
                """)
                button.clicked.connect(lambda checked, link=url: self.open_link(link))
                row_layout.addWidget(button)
            actions_layout.addLayout(row_layout)

        layout.addLayout(actions_layout)

    def open_link(self, url):
        webbrowser.open(url)


class HoverableFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            HoverableFrame {
                background-color: #1A1A1A;
                border-radius: 8px;
            }
            HoverableFrame:hover {
                background-color: #2A2A2A;
            }
        """)


class NotificationItem(HoverableFrame):
    def __init__(self, subject, title, message, date_str, max_preview_chars=120):
        super().__init__()
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

        self.subject = subject
        self.title_text = title
        self.full_message = message
        self.date_str = date_str
        self.is_expanded = False
        self.max_preview_chars = max_preview_chars

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(6)

        self.subject_label = QLabel(self.subject)
        self.subject_label.setStyleSheet("color: #54a4ff; font-size: 12px;")

        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 15px;")

        if self.full_message:
            self.message_label = QLabel(self.full_message)
            self.message_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
            self.message_label.setWordWrap(True)
            self.content_layout.addWidget(self.message_label)

        self.content_layout.addWidget(self.subject_label)
        self.content_layout.addWidget(self.title_label)

        layout.addLayout(self.content_layout, stretch=1)

        self.date_label = QLabel(self.date_str)
        self.date_label.setStyleSheet("color: #808080; font-size: 11px;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.date_label)

    def update_message_text(self):
        if self.is_expanded:
            self.message_label.setText(self.full_message)
        else:
            if len(self.full_message) > self.max_preview_chars:
                preview_text = self.full_message[:self.max_preview_chars] + "..."
                self.message_label.setText(preview_text)
            else:
                self.message_label.setText(self.full_message)


class EventItem(HoverableFrame):

    def __init__(self, title, course, date_qdate, event_type, time_str):
        super().__init__()
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        type_colors = {
            "drugo": "#FFA500",
            "ispit": "red",
            "predavanje": "#3BA55D",
            "lab": "#5555FF"
        }

        color = type_colors.get(event_type, "#FFFFFF")

        type_indicator = QFrame()
        type_indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 2px;
        """)
        type_indicator.setFixedSize(4, 36)
        layout.addWidget(type_indicator)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 13px;")

        course_label = QLabel(course)
        course_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")

        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #A0A0A0; font-size: 11px;")

        content_layout.addWidget(title_label)
        content_layout.addWidget(course_label)
        content_layout.addWidget(time_label)

        layout.addLayout(content_layout, stretch=1)

        right_layout = QVBoxLayout()
        right_layout.setSpacing(4)

        date_label = QLabel(date_qdate.toString("d.M."))
        date_label.setStyleSheet("color: #808080; font-size: 11px;")
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        type_label = QLabel(event_type)
        type_label.setStyleSheet("""
            color: #808080;
            font-size: 10px;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 2px 4px;
        """)
        type_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        right_layout.addWidget(date_label)
        right_layout.addWidget(type_label)

        layout.addLayout(right_layout)


class SectionCard(QFrame):
    def __init__(self, title, icon_path, svg_path=None):
        super().__init__()
        self.setObjectName("sectionCard")
        self.setStyleSheet("""
            #sectionCard {
                background-color: #111111;
                border: 1px solid #2A2A2A;
                border-radius: 8px;
            }
        """)
        from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        icon_label = QLabel()
        icon = QIcon(icon_path)
        icon_label.setPixmap(icon.pixmap(QSize(18, 18)))
        header_layout.addWidget(icon_label)

        header = QLabel(title)
        header.setStyleSheet("color: #E0E0E0; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header)

        if svg_path:
            svg_label = QLabel()
            svg_icon = QIcon(svg_path)
            svg_label.setPixmap(svg_icon.pixmap(QSize(16, 16)))
            header_layout.addWidget(svg_label)

        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)

    def add_item(self, item):
        self.content_layout.addWidget(item)


class HomeModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notification_module = None
        self.init_ui()

    def set_notification_module(self, notification_module):
        self.notification_module = notification_module
        self.refresh_recent_notifications()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        self.notifications_card = SectionCard(
            "Nedavne obavijesti",
            "../../resources/bell.svg",
            "../../resources/bell.svg"
        )
        self.populate_recent_notifications([])
        content_layout.addWidget(self.notifications_card, stretch=1)

        events_card = SectionCard(
            "Nadolazeći događaji",
            "../../resources/notification_icon.svg",
            "../../resources/notification_icon.svg"
        )
        upcoming_events = self.load_upcoming_events()
        for evt in upcoming_events:
            events_card.add_item(EventItem(*evt))
        content_layout.addWidget(events_card, stretch=1)

        main_layout.addLayout(content_layout)

        actions = [
            [("TVZ", "https://www.tvz.hr"), ("LMS", "https://lms-2020.tvz.hr/login/index.php"), ("Studomat", "https://www.isvu.hr/studomat/hr/prijava")],
            [("OUTLOOK", "https://outlook.office365.com"), ("MojTVZ", "https://moj.tvz.hr")]
        ]
        action_card = ActionCard("Korisne poveznice", actions)
        main_layout.addWidget(action_card)

        main_layout.addStretch(1)

    def refresh_recent_notifications(self):
        if not self.notification_module:
            return

        all_notifs = self.notification_module.notifications
        recent_notifs = all_notifs[:5]

        while self.notifications_card.content_layout.count():
            item = self.notifications_card.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for notif in recent_notifs:
            subject = getattr(notif, "subject", "Nepoznati predmet")
            title = getattr(notif, "title", "Bez naslova")
            message = getattr(notif, "message", "")
            time_str = getattr(notif, "time", "")
            item = NotificationItem(
                subject,
                title,
                message,
                time_str
            )
            self.notifications_card.add_item(item)

    def populate_recent_notifications(self, notif_widgets):
        while self.notifications_card.content_layout.count():
            item = self.notifications_card.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for w in notif_widgets[:5]:
            subject = getattr(w, "subject", "")
            title = getattr(w, "title", "")
            message = getattr(w, "message", "")
            time_str = getattr(w, "time", "")

            display_time = time_str
            if " u " not in time_str:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    display_time = f"{dt.day}.{dt.month}.{dt.year} u {dt.hour}h"
                except:
                    pass

            item = NotificationItem(subject, title, message, display_time)
            self.notifications_card.add_item(item)

    def load_upcoming_events(self):
        all_data = load_local_events()
        now = datetime.now()
        result_list = []

        for date_str, events in all_data.items():
            for e in events:
                start_str = e.get("Vrijeme početka", "")
                if not start_str:
                    continue
                try:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                if start_dt > now:
                    qdate = QDate(start_dt.year, start_dt.month, start_dt.day)
                    time_str = start_dt.strftime("%H:%M")
                    title = e.get("Naziv", "Neimenovani događaj")
                    course = e.get("Lokacija", "N/A")
                    tip = e.get("Tip", "").lower()
                    event_type = self.map_event_type(tip)
                    result_list.append((title, course, qdate, event_type, time_str))

        events_with_dt = []
        for (title, course, qd, et, time_str) in result_list:
            dt = datetime(qd.year(), qd.month(), qd.day())
            events_with_dt.append((dt, title, course, qd, et, time_str))

        events_with_dt.sort(key=lambda x: x[0])
        events_with_dt = events_with_dt[:4]

        final_list = []
        for (_, title, course, qdate, etype, time_str) in events_with_dt:
            final_list.append((title, course, qdate, etype, time_str))

        return final_list

    def map_event_type(self, tip_str):
        if "predavanja" in tip_str:
            return "predavanje"
        elif "laboratorijske" in tip_str or "lab" in tip_str:
            return "lab"
        elif "ispit" in tip_str:
            return "ispit"
        else:
            return "drugo"
