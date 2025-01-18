import json
import mimetypes
import os
import re
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QLabel, QApplication, QFrame
from bs4 import BeautifulSoup
from requests.cookies import create_cookie
from datetime import datetime


class DataApiThread(QThread):
    notification_updated = pyqtSignal(dict)
    files_updated = pyqtSignal(dict)
    first_load_signal = pyqtSignal(bool)
    reservation_links_signal = pyqtSignal(object, object)

    def __init__(self, interval: int = 500):
        super().__init__()
        self.session = None
        self.state = None
        self.interval = interval
        self._is_running = True
        self.current_files = {}
        self.current_notifications = {}
        self.first_load = False


    def run(self):
        while self._is_running:
            files, notifications, reservation_links = self.get_course_info()

            if files:
                for course_name, course_files in files.items():
                    sorted_files = sorted(course_files, key=lambda x: datetime.strptime(x['date'], "%d.%m.%y"))
                    for file in sorted_files:
                        if course_name not in self.current_files:
                            self.current_files[course_name] = []

                        if file not in self.current_files[course_name]:
                            self.current_files[course_name].append(file)
                            self.files_updated.emit({course_name: file})

            if notifications:
                combined_notifications = []

                for course_name, course_notifications in notifications.items():
                    for notification in course_notifications:
                        try:
                            notification_time = datetime.strptime(notification['time'], "%d.%m.%Y u %Hh")
                            combined_notifications.append((course_name, notification, notification_time))
                        except ValueError as e:
                            print(f"Error parsing date for notification in {course_name}: {e}")
                            continue

                combined_notifications.sort(key=lambda x: x[2])

                for course_name, notification, _ in combined_notifications:
                    unique_id = (notification['title'], notification['time'])

                    if course_name not in self.current_notifications:
                        self.current_notifications[course_name] = set()

                    if unique_id not in self.current_notifications[course_name]:
                        self.current_notifications[course_name].add(unique_id)
                        self.notification_updated.emit({course_name: notification})

            if self.first_load == False:
                self.first_load = True
                self.reservation_links_signal.emit(reservation_links, self.session)
                self.first_load_signal.emit(True)

            time.sleep(self.interval)

    def stop(self):
        self._is_running = False

    def load_cookies_to_requests(self, cookie_file="cookies.json"):
        session = requests.Session()
        if os.path.exists(cookie_file):

            with open(cookie_file, "r") as file:
                cookies = json.load(file)
                for cookie in cookies:

                    session_cookie = create_cookie(
                        name=cookie['name'],
                        value=cookie['value'],
                        domain=cookie['domain'],
                        path=cookie['path'],
                        secure=cookie['secure'],
                        rest={'HttpOnly': cookie['httpOnly']}
                    )
                    session.cookies.set_cookie(session_cookie)

                    if cookie['name'].startswith("MOJ"):
                        print("name is: " + cookie['name'])
                        self.state = cookie['name']
                        print("state is: " + self.state)

        return session

    def get_student_name(self):
        self.session = self.load_cookies_to_requests()
        try:
            if not self.state:
                print("Error: state is not set.")
                return None

            url = "https://moj.tvz.hr/index.php?state=" + self.state
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            p_tag = soup.find('p', class_='card-text')

            if p_tag:
                text = p_tag.get_text(strip=True)
                parts = text.split()
                if "Student" in parts:
                    student_index = parts.index("Student")
                    if student_index + 1 < len(parts):
                        student_name = parts[student_index + 1]
                        return student_name

            return None
        except Exception as e:
            print(f"Error in get_student_name: {e}")
            return None

    def get_course_info(self):
        try:
            if not self.state:
                print("Error: state is not set.")
                return None

            url = "https://moj.tvz.hr/index.php?state=" + self.state
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            link_tag = soup.find('a', string="Moji predmeti")
            if link_tag:
                link = link_tag['href']
                return self._extract_courses(link)
            else:
                return None

        except Exception as e:
            print(f"get_course_info: {e}")
            return None

    def _extract_courses(self,link):
        try:
            response = self.session.get(link, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            courses_info = {}

            forms = soup.select('div.card-body form')

            for form in forms:
                action_url = form['action']

                match = re.search(r'studij=([^&]+)', action_url)
                if not match:
                    continue
                studij_value = match.group(1)

                link_tag = form.find('a', href=re.compile(rf'studij={studij_value}'))
                if link_tag:
                    link = link_tag['href']
                    course_name = link_tag.text.strip()

                    course_name_clean = re.sub(r'\(.*?\)', '', course_name).strip()

                    if course_name_clean not in courses_info:
                        courses_info[course_name_clean] = link

            return self._get_course_details(courses_info)

        except Exception as e:
            print(f"extract_courses: {e}")
            return None

    def _extract_notifications(self, soup):
        notifications = []
        notification_elements = soup.select('div.card-header')

        for element in notification_elements:
            try:
                title = element.find('h5', class_='card-title').text.strip()
                message = element.find_next_sibling('div', class_='card-body').text.strip()
                time_raw = element.find('h6', class_='card-subtitle').text.strip()

                time_match = re.search(r'\d{1,2}\.\d{1,2}\.\d{4} u \d{1,2}h', time_raw)
                time = time_match.group(0) if time_match else time_raw

                notifications.append({
                    'title': title,
                    'message': message,
                    'time': time
                })
            except Exception as e:
                print(f"Error extracting notification: {e}")
                continue

        return notifications

    def _extract_files(self, soup):
        files = []

        file_containers = soup.select('div.col-sm-3 div.shadow.p-3.mb-5.rounded')

        for container in file_containers:
            try:
                section_variable = container.select_one('h5').get_text(strip=True)

                list_items = container.select('li.list-group-item')
                for item in list_items:
                    try:
                        a_tags = item.find_all('a')
                        if len(a_tags) < 2:
                            raise ValueError("Didn't find two <a> tags in the snippet!")

                        first_a = a_tags[0]
                        second_a = a_tags[1]

                        img_tag = first_a.find('img')
                        type_variable = ""
                        if img_tag and img_tag.has_attr("src"):
                            src = img_tag["src"]
                            filename = src.split('/')[-1]
                            type_variable = filename.split('.')[0]

                        second_href = second_a.get('href', '')

                        extension = ""
                        if "skini/repoz" in second_href:
                            match = re.search(r"(skini/repoz)(.*)", second_href)
                            if match:
                                extension = match.group(2)
                            else:
                                extension = second_href
                        else:
                            extension = second_href

                        second_text = second_a.get_text(strip=True)
                        date_variable = ""
                        name_variable = second_text
                        match_date = re.search(r"\[([^]]+)\]", second_text)
                        if match_date:
                            date_variable = match_date.group(1)
                            name_variable = re.sub(r"\[[^]]+\]", "", name_variable).strip()

                        files.append({
                            'name': name_variable,
                            'extension': extension,
                            'type': type_variable,
                            'date': date_variable,
                            'section': section_variable
                        })

                    except Exception as e:
                        print(f"Error extracting file details: {e}")
                        continue

            except Exception as e:
                print(f"Error extracting section details: {e}")
                continue

        return files

    def _get_course_details(self, course_info):
        files = {}
        notifications = {}
        reservation_links = {}

        try:
            for course_name, course_url in course_info.items():
                response = self.session.get(course_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                extracted_files = self._extract_files(soup)
                extracted_notifications = self._extract_notifications(soup)

                link_tags = soup.find_all('a', class_='nav-link mojtvzlink', onclick=True)
                for link_tag in link_tags:
                    if 'Rezervacija labosa' in link_tag.get_text():
                        onclick_content = link_tag['onclick']
                        start_idx = onclick_content.find("'") + 1
                        end_idx = onclick_content.find("',", start_idx)
                        reservation_link = onclick_content[start_idx:end_idx]
                        reservation_links[course_name] = reservation_link
                        break

                files[course_name] = extracted_files
                notifications[course_name] = extracted_notifications

        except Exception as e:
            print(f"Error fetching course details: {e}")

        return files, notifications, reservation_links



    def extract_filename_from_content_disposition(self, content_disposition: str) -> str:
        if content_disposition:
            match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
            if match:
                return match.group(1)
        return ''

    def determine_filename(self, response, filename: str) -> str:
        content_type = response.headers.get('Content-Type', '')
        suggested_extension = mimetypes.guess_extension(content_type)

        original_extension = os.path.splitext(filename)[1]

        if not original_extension and suggested_extension:
            filename += suggested_extension
        elif original_extension and suggested_extension and original_extension != suggested_extension:
            print(f"Warning: Original extension '{original_extension}' differs from suggested '{suggested_extension}'.")

        return filename

    def download_file(self, extension: str, filename: str) -> bool:
        try:
            # Construct the download URL
            url = f"https://moj.tvz.hr/index.php?TVZ={self.state}&link=skini/repoz{extension}"

            response = self.session.head(url, timeout=10)
            response.raise_for_status()

            final_filename = self.determine_filename(response, filename)
            print(f"Final determined filename: {final_filename}")

            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_dialog.setWindowTitle('Save File As')
            file_dialog.selectFile(final_filename)

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                save_path = file_dialog.selectedFiles()[0]
                print(f"Saving file to: {save_path}")

                with self.session.get(url, stream=True, timeout=30) as response:
                    response.raise_for_status()
                    total_downloaded = 0
                    expected_size = int(response.headers.get('Content-Length', 0))

                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                total_downloaded += len(chunk)
                                #print(f"Downloaded {total_downloaded} / {expected_size} bytes")

               # print(f"Download completed. Total bytes downloaded: {total_downloaded}")
                if total_downloaded != expected_size:
                    print(f"Warning: Downloaded size ({total_downloaded} bytes) does not match expected size ({expected_size} bytes).")
                    return False

                return True

        except requests.RequestException as e:
            print(f"Network error occurred: {e}")
            return False
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False


