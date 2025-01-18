# src/tvz_enhancer/data/course.py
import logging

from PyQt6.QtCore import QObject, pyqtSignal
import datetime
import json
import os
from pathlib import Path


class Course(QObject):
    notificationsChanged = pyqtSignal()
    RELATIVE_JSON_PATH = os.path.join('..', 'courses_data.json')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notifications = []
        self._files = []
        self._load_and_parse_data()

    def _load_and_parse_data(self) -> None:
        base_path = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(base_path, self.RELATIVE_JSON_PATH)

        if not os.path.exists(json_file_path):
            print(f"Error: JSON datoteka nije pronađena na putanji {json_file_path}")
            return

        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._parse_data(data)
        except json.JSONDecodeError as e:
            print(f"Error pri parsiranju JSON datoteke: {e}")
        except Exception as e:
            print(f"Neočekivana greška pri učitavanju JSON datoteke: {e}")

    def _parse_data(self, data: dict) -> None:
        courses = data.get("courses", [])

        for course in courses:
            course_name = course.get("name", "")
            notifications = course.get("notifications", [])
            for notif in notifications:
                new_notif = {
                    "title": notif.get("title", ""),
                    "message": notif.get("message", ""),
                    "time": notif.get("time", ""),
                    "course": course_name,
                }
                self._notifications.append(new_notif)

            files = course.get("files", [])
            self._files.extend(files)

        self._notifications.sort(
            key=lambda x: self._parse_time(x["time"]),
            reverse=True
        )

        logging.debug(f"Total notifications parsed: {len(self._notifications)}")
        logging.debug(f"Total files parsed: {len(self._files)}")

    def _parse_time(self, time_str: str) -> datetime.datetime:
        replaced = time_str.replace(" u ", " ").replace("h", "")
        try:
            return datetime.datetime.strptime(replaced, "%d.%m.%Y %H")
        except ValueError:
            return datetime.datetime.min

    def add_notification(self, title: str, message: str, time_: str, course: str) -> None:
        new_notif = {
            "title": title,
            "message": message,
            "time": time_,
            "course": course
        }
        self._notifications.insert(0, new_notif)
        self.notificationsChanged.emit()

    def get_last_10_notifications(self) -> list:
        return self._notifications[:10]

    def get_files(self) -> list:
        return self._files

    def get_last_10_files(self) -> list:
        return self._files[:10]
