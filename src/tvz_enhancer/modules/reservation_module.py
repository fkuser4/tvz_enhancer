import sys
import webbrowser
import time
from datetime import datetime
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QImage, QColor, QFont
from PyQt6.QtWidgets import (
    QWidget,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QTimeEdit,
    QComboBox,
    QDialog,
    QGridLayout,
    QScrollArea,
    QStackedWidget,
    QGraphicsDropShadowEffect,
    QApplication,
    QFrame
)
from PyQt6.QtCore import Qt, QDate, QSize
from src.tvz_enhancer.threads.reservation_thread import ReservationThread
from src.tvz_enhancer.utils.local_storage import load_local_events, save_local_events


class ReservationItem(QWidget):
    def __init__(self, course, time, keyword, link, status="Neaktivno", session=None, parent=None, on_delete=None, on_status_change=None):
        super().__init__(parent)
        self.on_delete = on_delete
        self.on_status_change = on_status_change
        self.status = status
        self.course = course
        self.time = time
        self.keyword = keyword
        self.link = link
        self.session = session
        self.thread = None
        self.is_processing = False

        self.setObjectName("reservationItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(120)

        self.pause_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pause"><rect x="14" y="4" width="4" height="16" rx="1"/><rect x="6" y="4" width="4" height="16" rx="1"/></svg>'''
        self.play_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-play"><polygon points="6 3 20 12 6 21 6 3"/></svg>'''
        self.delete_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash-2"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>'''

        self.setStyleSheet("""
            QWidget#reservationItem {
                background-color: #141414;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                border: 1px solid #2e2e2e;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QLabel#courseLabel {
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#timeLabel, QLabel#keywordLabel {
                color: #888;
                font-size: 14px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                min-width: 24px;
                min-height: 24px;
                margin: 2px;
                padding: 4px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)

        left_container = QWidget()
        left_container_layout = QHBoxLayout(left_container)
        left_container_layout.setContentsMargins(0, 0, 0, 0)
        left_container_layout.setSpacing(15)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        course_label = QLabel(self.course)
        course_label.setObjectName("courseLabel")

        time_label = QLabel(f"{self.time}")
        time_label.setObjectName("timeLabel")
        time_label.setWordWrap(True)
        time_label.setContentsMargins(0, 0, 0, 10)

        keyword_label = QLabel(f"{self.keyword}")
        keyword_label.setObjectName("keywordLabel")

        info_layout.addWidget(course_label)
        info_layout.addWidget(time_label)
        info_layout.addWidget(keyword_label)
        info_layout.addStretch()

        left_container_layout.addLayout(info_layout)

        right_layout = QHBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QLabel(self.status.upper())
        self.status_label.setFixedWidth(100)
        self.update_status_style()

        self.status_button = QPushButton()
        self.delete_button = QPushButton()

        svg_size = 26
        self.status_button.setIconSize(QSize(svg_size, svg_size))
        self.delete_button.setIconSize(QSize(svg_size, svg_size))

        self.update_status_button()
        self.update_button_icon(self.delete_button, self.delete_svg, "#e8eaed")

        self.status_button.installEventFilter(self)
        self.delete_button.installEventFilter(self)

        self.status_button.clicked.connect(self.on_status_clicked)
        self.delete_button.clicked.connect(self.on_delete_clicked)

        right_layout.addWidget(self.status_label)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.status_button)
        right_layout.addSpacing(5)
        right_layout.addWidget(self.delete_button)

        main_layout.addWidget(left_container, stretch=4)
        main_layout.addLayout(right_layout, stretch=1)

    def initialize_thread(self):
        try:
            if not all([self.session, self.time, self.keyword, self.link]):
                self.update_status("Neuspjelo")
                return False

            if self.thread is not None:
                self.thread.stop()
                self.thread = None

            keywords = self.keyword.split(",") if self.keyword else []
            if not keywords:
                self.update_status("Neuspjelo")
                return False

            self.thread = ReservationThread(self.session, self.time, keywords, self.link)
            self.thread.statusChanged.connect(self.handle_thread_status)
            self.thread.resultReady.connect(self.handle_result)
            return True

        except Exception:
            self.update_status("Neuspjelo")
            return False

    def cleanup_thread(self):
        try:
            if self.thread is not None:
                self.update_status("Neaktivno")
                self.thread.stop()
                self.thread = None
        except Exception:
            self.thread = None

    def handle_thread_status(self, new_status):
        if new_status in ["Neuspjelo", "Uspjelo"]:
            if self.thread is not None:
                self.thread.stop()
                self.thread = None

        self.update_status(new_status)
        if self.on_status_change:
            self.on_status_change(self.course, self.time, self.keyword, new_status)

    def handle_result(self, result):
        if result is True:
            self.update_status("Uspjelo")
        else:
            self.update_status("Neuspjelo")

        if self.thread is not None:
            self.thread.stop()
            self.thread = None

    def update_button_icon(self, button, svg_template, color):
        svg_content = svg_template.format(color=color)
        icon = QIcon()
        svg_bytes = svg_content.encode('utf-8')
        pixmap = QPixmap()
        pixmap.loadFromData(svg_bytes)
        button.setIcon(QIcon(pixmap))

    def update_status_button(self):
        if self.status in ["Uspjelo", "Neuspjelo"]:
            self.status_button.hide()
        else:
            self.status_button.show()
            if self.status == "Aktivno":
                self.update_button_icon(self.status_button, self.pause_svg, "#e8eaed")
            else:
                self.update_button_icon(self.status_button, self.play_svg, "#4CAF50")

    def update_status_style(self):
        color_map = {
            "Aktivno": "#2196F3",
            "Neaktivno": "#FFA500",
            "Neuspjelo": "#FF5252",
            "Uspjelo": "#4CAF50"
        }
        color = color_map.get(self.status, "#808080")

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                font-weight: 500;
                padding: 4px 10px;
                border: 1px solid {color};
                border-radius: 4px;
                background-color: transparent;
                letter-spacing: 0.5px;
                text-align: center;
            }}
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_status(self, new_status):
        self.status = new_status
        self.status_label.setText(new_status.upper())
        self.update_status_style()
        self.update_status_button()

    def closeEvent(self, event):
        self.cleanup_thread()
        super().closeEvent(event)

    def eventFilter(self, watched, event):
        if event.type() == event.Type.Enter:
            if watched == self.status_button:
                color = "#808080" if self.status == "Aktivno" else "#15d11c"
                svg = self.pause_svg if self.status == "Aktivno" else self.play_svg
                self.update_button_icon(self.status_button, svg, color)
            elif watched == self.delete_button:
                self.update_button_icon(self.delete_button, self.delete_svg, "#ff4444")
        elif event.type() == event.Type.Leave:
            if watched == self.status_button:
                self.update_status_button()
            elif watched == self.delete_button:
                self.update_button_icon(self.delete_button, self.delete_svg, "#e8eaed")
        return super().eventFilter(watched, event)

    def on_status_clicked(self):
        try:
            if self.is_processing:
                return

            self.is_processing = True

            if self.status == "Aktivno":
                self.cleanup_thread()
                self.update_status("Neaktivno")
            elif self.status in ["Neaktivno", "Neuspjelo"]:
                if self.initialize_thread():
                    self.thread.start()
                    self.update_status("Aktivno")
                else:
                    self.update_status("Neuspjelo")
        except Exception:
            self.update_status("Neuspjelo")
        finally:
            self.is_processing = False
            self.update_status_button()

    def cleanup_thread(self):
        try:
            if self.thread is not None:
                self.thread.stop()
                self.thread.wait()
                self.thread.deleteLater()
                self.thread = None
        except Exception:
            self.thread = None

    def update_status_button(self):
        if self.status in ["Uspjelo", "Neuspjelo"]:
            self.status_button.hide()
        else:
            self.status_button.show()
            if self.status == "Aktivno":
                self.update_button_icon(self.status_button, self.pause_svg, "#e8eaed")
            else:
                self.update_button_icon(self.status_button, self.play_svg, "#4CAF50")
        self.status_button.update()

    def on_delete_clicked(self):
        try:
            self.cleanup_thread()
            if self.on_delete:
                self.on_delete(self)
        except Exception:
            try:
                self.deleteLater()
            except:
                pass


class CreateReservationWidget(QWidget):
    def __init__(self, available_courses=None, reservation_module=None, links=None, parent=None):
        super().__init__(parent)
        self.available_courses = available_courses or ["Default Course"]
        self.reservation_module = reservation_module
        self.links = links
        self.setObjectName("createReservationWidget")
        self.setMinimumWidth(500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QWidget(self)
        container.setObjectName("containerWidget")
        container.setStyleSheet("""
            QWidget#containerWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        container.setFixedWidth(450)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Nova rezervacija")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #000000;
            }
        """)
        header_layout.addWidget(title_label)
        container_layout.addLayout(header_layout)

        self.course_label = QLabel("Predmet")
        self.course_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #000000;")
        container_layout.addWidget(self.course_label)

        self.course_combo = QComboBox()
        self.course_combo.addItems(self.available_courses)
        self.course_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 16px;
                color: #000000;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTcgMTBMNyAxMEwxMiAxNUwxNyAxMEw3IDEwWiIgZmlsbD0iIzZCN0NCNCIvPgo8L3N2Zz4=);
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #000000;
                selection-background-color: #e0e0e0;
                selection-color: #000000;
                font-size: 16px;
                border: 1px solid #E5E7EB;
                padding: 7px 5px;
            }
        """)
        container_layout.addWidget(self.course_combo)

        self.time_label = QLabel("Vrijeme")
        self.time_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #000000;")
        container_layout.addWidget(self.time_label)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 16px;
                color: #000000;
                min-height: 30px;
            }
            QTimeEdit::up-button, QTimeEdit::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        container_layout.addWidget(self.time_edit)

        self.keyword_label = QLabel("Ključne riječi")
        self.keyword_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #000000;")
        container_layout.addWidget(self.keyword_label)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("+kolokvij,+G1,+utorak,+10:00,-11:00")
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 16px;
                color: #000000;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        container_layout.addWidget(self.keyword_input)

        self.create_button = QPushButton("Kreiraj rezervaciju")
        self.create_button.clicked.connect(self.create_reservation)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        container_layout.addWidget(self.create_button)

        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet("""
            QWidget#createReservationWidget {
                background-color: transparent;
            }
        """)

        self.validate_inputs()
        self.course_combo.currentTextChanged.connect(self.validate_inputs)
        self.time_edit.timeChanged.connect(self.validate_inputs)
        self.keyword_input.textChanged.connect(self.validate_inputs)

    def find_reservation_module(self):
        parent = self.parent()
        while parent:
            if isinstance(parent, ReservationModule):
                return parent
            parent = parent.parent()
        return None

    def validate_inputs(self):
        course = self.course_combo.currentText()
        time = self.time_edit.time().toString("HH:mm")
        keyword = self.keyword_input.text().strip()

        self.create_button.setEnabled(bool(course and time and keyword))

    def create_reservation(self):
        course = self.course_combo.currentText()
        time = self.time_edit.time().toString("HH:mm")
        keyword = self.keyword_input.text().strip()
        link = self.links[self.find_link_from_course(course)]

        if not all([course, time, keyword, link]):
            return

        if self.reservation_module:
            self.reservation_module.add_reservation(course, time, keyword, link)
            self.reservation_module.hideCreateReservationOverlay()

    def cancel_creation(self):
        if self.reservation_module:
            self.reservation_module.hideCreateReservationOverlay()

    def find_link_from_course(self, course_name):
        try:
            index = self.available_courses.index(course_name)
            return index
        except ValueError:
            return -1


class ReservationModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.session = None
        self.available_courses = []
        self.courses_links = []
        self.reservations = [
            {
                'course': "Administracija računalnih mreža",
                'time': "12:00",
                'keyword': "Labosi",
                'status': "Aktivno"
            },
            {
                'course': "Razvoj računalnih igara",
                'time': "14:00",
                'keyword': "Labosi",
                'status': "Aktivno"
            },
            {
                'course': "Napredno Javascrip programiranje",
                'time': "16:00",
                'keyword': "Labosi",
                'status': "Aktivno"
            }
        ]

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(7, 0, 7, 0)
        self.main_layout.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("mainContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        self.reservation_list_widget = QWidget()
        self.reservation_list_widget.setObjectName("reservationList")
        list_layout = QVBoxLayout(self.reservation_list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent; 
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: transparent;
                width: 0px;
                height: 0px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_content)
        list_layout.addWidget(self.scroll_area)

        self.container_layout.addWidget(self.reservation_list_widget)
        self.main_layout.addWidget(self.container)

        self.setStyleSheet("""
            ReservationModule {
                background-color: #1e1e1e;
                border-radius: 8px;
            }
            QWidget#mainContainer {
                background-color: transparent;
            }
            QWidget#reservationList {
                background-color: transparent;
            }
        """)

    def showCreateReservationOverlay(self):
        main_window = self.window()

        if not hasattr(main_window, 'overlay_container'):
            main_window.overlay_container = QWidget(main_window)
            main_window.overlay_container.setObjectName("overlayContainer")
            overlay_layout = QVBoxLayout(main_window.overlay_container)
            overlay_layout.setContentsMargins(0, 0, 0, 0)
            overlay_layout.setSpacing(0)

            main_window.create_reservation_widget = CreateReservationWidget(
                available_courses=self.available_courses,
                reservation_module=self,
                links=self.courses_links,
                parent=main_window.overlay_container
            )
            overlay_layout.addWidget(main_window.create_reservation_widget, 0, Qt.AlignmentFlag.AlignCenter)

            main_window.overlay_container.setStyleSheet("""
                QWidget#overlayContainer {
                    background-color: rgba(0, 0, 0, 0.5);
                }
            """)
            main_window.overlay_container.installEventFilter(self)

        main_window.overlay_container.setGeometry(main_window.rect())
        main_window.overlay_container.show()
        main_window.overlay_container.raise_()

    def hideCreateReservationOverlay(self):
        main_window = self.window()
        if hasattr(main_window, 'overlay_container'):
            main_window.overlay_container.hide()

    def eventFilter(self, obj, event):
        main_window = self.window()
        if hasattr(main_window, 'overlay_container') and obj == main_window.overlay_container:
            if event.type() == event.Type.MouseButtonPress:
                if not main_window.create_reservation_widget.geometry().contains(event.pos()):
                    self.hideCreateReservationOverlay()
                    return True
        return super().eventFilter(obj, event)

    def add_reservation(self, course, time, keyword, link, append=True):
        reservation = {
            'course': course,
            'time': time,
            'keyword': keyword,
            'link': link,
            'status': 'Neaktivno'
        }

        if append:
            self.reservations.append(reservation)

        reservation_widget = ReservationItem(
            course=course,
            time=time,
            keyword=keyword,
            link=f"{self.courses_links[self.find_link_from_course(course)]}",
            status='Neaktivno',
            session=self.session,
            on_delete=self.remove_reservation,
            on_status_change=self.update_reservation_status
        )
        self.scroll_layout.addWidget(reservation_widget)

    def remove_reservation(self, reservation_widget):
        try:
            for i, reservation in enumerate(self.reservations):
                if (reservation['course'] == reservation_widget.findChild(QLabel, "courseLabel").text() and
                        reservation['time'] in reservation_widget.findChild(QLabel, "timeLabel").text() and
                        reservation['keyword'] == reservation_widget.findChild(QLabel, "keywordLabel").text()):
                    del self.reservations[i]
                    break

            self.scroll_layout.removeWidget(reservation_widget)
            reservation_widget.setParent(None)
            QApplication.processEvents()
            reservation_widget.deleteLater()
        except Exception:
            try:
                reservation_widget.deleteLater()
            except:
                pass

    def update_reservation_status(self, course, time, keyword, new_status):
        for reservation in self.reservations:
            if (reservation['course'] == course and
                    reservation['time'] == time and
                    reservation['keyword'] == keyword):
                reservation['status'] = new_status
                break

    def add_crucial_data(self, subject, session):
        self.set_courses(subject)
        self.session = session

    def set_courses(self, courses_dict):
        for course_name, course_link in courses_dict.items():
            self.available_courses.append(course_name)
            self.courses_links.append(course_link)

    def find_link_from_course(self, course_name):
        try:
            index = self.available_courses.index(course_name)
            return index
        except ValueError:
            return -1
