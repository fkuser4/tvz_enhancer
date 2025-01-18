
import logging
import subprocess
import requests
from pathlib import Path

from PyQt6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget, QHBoxLayout, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QMouseEvent, QDesktopServices
from urllib.parse import urlparse, parse_qs
import sys
import os

from src.tvz_enhancer.components.document_tags import DocumentTag
from src.tvz_enhancer.components.flow_layout import FlowLayout
from src.tvz_enhancer.components.notification_tag import NotificationTag
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
import webbrowser

from src.tvz_enhancer.data.data_api import DataApiThread

import faulthandler

faulthandler.enable()

class SvgIcon(QSvgWidget):
    def __init__(self, svg_path, size=16, color="#d3d3d3"):
        super().__init__(svg_path)
        self.setFixedSize(QSize(size, size))
        self._svg_renderer = self.renderer()
        self.setStyleSheet("background-color: transparent;")

        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_svg_path = os.path.join(script_dir, svg_path)

        with open(full_svg_path, 'rb') as f:
            self.svg_template = f.read().decode('utf-8')
        self.update_svg_renderer(QColor(color))
        self.set_color(color)

    def update_svg_renderer(self, color):
        if self.svg_template and self._svg_renderer:
            svg_colored = self.svg_template.replace('currentColor', color.name())
            if not self._svg_renderer.load(bytearray(svg_colored, encoding='utf-8')):
                print("Failed to load SVG with updated color.")

    def set_color(self, color):
        self.update_svg_renderer(QColor(color))

class DocumentModule(QWidget):
    def __init__(self):
        super().__init__()
        self.course_sections = {}

        self.data_api_thread = DataApiThread()
        student_name = self.data_api_thread.get_student_name()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 20, 20, 20)
        main_layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget { 
                background: transparent; 
            }
            QScrollBar:vertical {
                width: 0px; /* Sakrij scroll bar ako nije potreban */
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)

        try:
            self.create_course_sections()
        except Exception as e:
            print(f"Error during create_course_sections: {e}")
        scroll.setWidget(scroll_content)

        main_layout.addWidget(scroll)
        self.setStyleSheet("background-color: transparent;")

    def create_course_sections(self):
        for course in self.course_data():
            try:
                self.add_course_section(course)
            except Exception as e:
                print(f"Error creating course section for {course.get('name', 'Unknown')}: {e}")

        self.scroll_layout.addStretch()

    def add_course_section(self, course):
        course_name = course["name"]
        if course_name not in self.course_sections:
            print(f"Creating new course section for: {course_name}")
            try:
                section = QFrame()
                section_layout = QVBoxLayout(section)
                section_layout.setContentsMargins(0, 0, 0, 0)
                section_layout.setSpacing(4)

                header_button = QPushButton(course_name)
                header_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #181818; 
                        color: white; 
                        padding: 4px 8px; 
                        padding-left: 16px; 
                        min-height: 60px; 
                        border-radius: 6px; 
                        text-align: left; 
                        font-size: 16px; 
                        font-weight: 550;
                        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; 
                    }
                    QPushButton:hover { 
                        background-color: #252525; 
                    }
                """)

                chevron_icon = SvgIcon("../resources/chevron-down.svg", 16)
                header_layout = QHBoxLayout(header_button)
                header_layout.addStretch()
                header_layout.addWidget(chevron_icon)
                header_button.setProperty("chevron_icon", chevron_icon)

                content_widget = QWidget()
                content_layout = QVBoxLayout(content_widget)
                content_layout.setContentsMargins(16, 8, 16, 8)
                content_layout.setSpacing(4)

                section_info = {
                    'frame': section,
                    'content': content_widget,
                    'layout': content_layout,
                    'categories': {}
                }

                content_widget.hide()
                header_button.clicked.connect(lambda: self.toggle_section(content_widget, header_button))

                section_layout.addWidget(header_button)
                section_layout.addWidget(content_widget)

                self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, section)
                self.course_sections[course_name] = section_info

                for category in course.get("categories", []):
                    self.add_category_to_section(course_name, category["name"])
                    for file in category["files"]:
                        self.add_file_to_category(course_name, category["name"], file)

            except Exception as e:
                print(f"Error creating course section: {e}")

    def add_category_to_section(self, course_name, category_name):
        if course_name in self.course_sections:
            section_info = self.course_sections[course_name]
            if category_name not in section_info['categories']:
                category_label = QLabel(category_name)
                category_label.setStyleSheet("color: #e5e5e5; font-size: 13px; font-weight: bold;")
                section_info['layout'].addWidget(category_label)
                section_info['categories'][category_name] = category_label

    def add_file_to_category(self, course_name, category_name, file_info):
        if course_name in self.course_sections:
            section_info = self.course_sections[course_name]
            file_widget = self.create_file_widget(file_info)
            if file_widget:
                section_info['layout'].addWidget(file_widget)

    def toggle_section(self, content_widget, header_button):
        try:
            content_widget.setVisible(not content_widget.isVisible())
            chevron_icon = header_button.property("chevron_icon")

            if content_widget.isVisible():
                new_icon = SvgIcon("../resources/chevron-up.svg", 16, "#d3d3d3")
            else:
                new_icon = SvgIcon("../resources/chevron-down.svg", 16, "#d3d3d3")

            header_button.layout().removeWidget(chevron_icon)
            chevron_icon.deleteLater()
            header_button.layout().addWidget(new_icon)
            header_button.setProperty("chevron_icon", new_icon)
        except Exception as e:
            print(f"Error during toggle_section function: {e}")

    def create_file_widget(self, file):
        try:
            widget = QFrame()
            widget.setStyleSheet(
                "QFrame { background-color: transparent; padding: 8px; border-radius: 6px; }"
                "QFrame:hover { background-color: #181818; }"
            )
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(8, 4, 8, 4)
            layout.setSpacing(10)

            icon = SvgIcon("../resources/file-text2.svg", 16)
            layout.addWidget(icon)

            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(15, 0, 0, 0)

            inner_layout = QVBoxLayout()
            inner_layout.setSpacing(4)
            inner_layout.setContentsMargins(0, 0, 0, 0)

            name_label = QLabel(file["name"])
            name_label.setStyleSheet("color: white; font-size: 14px; margin: 0; padding: 0;")

            details_layout = QHBoxLayout()
            details_layout.setSpacing(5)
            details_layout.setContentsMargins(0, 0, 0, 0)
            type_date_label = QLabel(f"{file['type']} • {file['date']}")
            type_date_label.setStyleSheet("color: #9ca3af; font-size: 12px; margin: 0; padding: 0;")
            details_layout.addWidget(type_date_label)
            details_layout.addStretch()

            inner_layout.addWidget(name_label)
            inner_layout.addLayout(details_layout)

            info_layout.addLayout(inner_layout)

            action_button = QPushButton()
            action_button.setFixedSize(28, 28)
            action_button.setStyleSheet("QPushButton { background-color: transparent; border: none; }")

            is_downloadable = file.get('download', False)
            icon_widget = SvgIcon("../resources/download.svg" if is_downloadable else "../resources/external-link.svg",
                                  16, "#d3d3d3")

            button_layout = QHBoxLayout(action_button)
            button_layout.setContentsMargins(6, 6, 6, 6)
            button_layout.addWidget(icon_widget)

            action_button.hide()

            if is_downloadable:
                action_button.clicked.connect(lambda checked, f=file:
                                              self.download_file(f['extension'], f['name']))
            else:
                action_button.clicked.connect(lambda: self.open_link(file.get('extension', '')))

            def on_button_hover(event):
                if event.type() == event.Type.Enter:
                    action_button.setStyleSheet(
                        "QPushButton { background-color: #ffffff; border: none; border-radius: 6px; }")
                    icon_widget.set_color("#000000")
                else:
                    action_button.setStyleSheet(
                        "QPushButton { background-color: transparent; border: none; border-radius: 6px;}")
                    icon_widget.set_color("#d3d3d3")

            def on_widget_hover(event):
                if event.type() == event.Type.Enter:
                    action_button.show()
                else:
                    action_button.hide()

            widget.enterEvent = on_widget_hover
            widget.leaveEvent = on_widget_hover

            action_button.enterEvent = on_button_hover
            action_button.leaveEvent = on_button_hover

            layout.addLayout(info_layout)
            layout.addWidget(action_button)
            return widget
        except Exception as e:
            print(f"Error during create_file_widget: {e}")
            return None

    def download_file(self):
        pass

    def open_link(self, url):
        webbrowser.open(url)

    def add_new_file(self, file_data):
        course_name = list(file_data.keys())[0]
        file_info = file_data[course_name]
        file_info['download'] = not file_info.get('extension', '').startswith("http")

        if course_name not in self.course_sections:
            new_course = {
                "name": course_name,
                "categories": [
                    {
                        "name": file_info["section"],
                        "files": [file_info]
                    }
                ]
            }
            self.add_course_section(new_course)
        else:
            self.add_category_to_section(course_name, file_info["section"])
            self.add_file_to_category(course_name, file_info["section"], file_info)

    def course_data(self):
        return []

    def count_total_files(self):
        total = 0
        for section_info in self.course_sections.values():
            file_count = sum(1 for _ in section_info['content'].findChildren(QFrame) if _ != section_info['frame'])
            total += file_count
        return total

    def download_file(self, extension, filename):
        try:
            self.data_api_thread.download_file(extension, filename)
        except Exception as e:
            print(f"Error during file download: {e}")