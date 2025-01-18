import sys
import requests
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTime, QDateTime
from PyQt6.QtWidgets import QApplication
from bs4 import BeautifulSoup


class ReservationThread(QThread):
    resultReady = pyqtSignal(object)
    statusChanged = pyqtSignal(str)

    def __init__(self, session, target_time_str, keywords, link, parent=None):
        super().__init__(parent)
        self.session = session
        self.target_time = QTime.fromString(target_time_str, "HH:mm")
        self.keywords = keywords
        self.link = link
        self._status = "unactive"
        self._running = True
        self.statusChanged.emit(self._status)

    def set_status(self, new_status):
        self._status = new_status
        self.statusChanged.emit(new_status)

    def stop(self):
        self._running = False
        self.quit()
        self.wait(100)  # Čekamo maksimalno 100ms
        if self.isRunning():
            print("Force terminating thread...")
            self.terminate()

    def run(self):
        try:
            current_time = QTime.currentTime()

            if self.target_time <= current_time:
                seconds_in_day = 24 * 60 * 60
                seconds_to_wait = current_time.secsTo(self.target_time) + seconds_in_day
                print(
                    f"Waiting until tomorrow at {self.target_time.toString('HH:mm')}. Waiting {seconds_to_wait} seconds.")
                time.sleep(seconds_to_wait)
            else:
                while current_time < self.target_time and self._running:
                    remaining_seconds = current_time.secsTo(self.target_time)
                    time.sleep(min(remaining_seconds, 1))
                    current_time = QTime.currentTime()

            if not self._running:
                self.set_status("unactive")
                return

            self.set_status("active")

            try:
                form_data = {"supporttype": "labo"}
                response = self.session.post(self.link, data=form_data)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all("div", class_="card card-default")

                if not cards:
                    self.set_status("failed")
                    self.resultReady.emit("No cards found.")
                    return

                best_card, best_score = self.find_best_matching_card(cards)

                if best_card is None:
                    self.set_status("failed")
                    self.resultReady.emit("No matching cards found.")
                    return

                form = best_card.find("form")
                if not form:
                    self.set_status("failed")
                    self.resultReady.emit("No form found in the best matching card.")
                    return

                action_url = "https://moj.tvz.hr/" + form["action"]
                hidden_inputs = {
                    input_tag["name"]: input_tag["value"]
                    for input_tag in form.find_all("input", type="hidden")
                }

                second_response = self.session.post(action_url, data=hidden_inputs)
                second_response.raise_for_status()

                second_soup = BeautifulSoup(second_response.text, "html.parser")
                time_slot_cards = second_soup.find_all("div", class_="card card-default")

                if not time_slot_cards:
                    self.set_status("failed")
                    self.resultReady.emit("No time slots found.")
                    return

                best_time_slot, best_score = self.find_best_matching_card(time_slot_cards)

                if best_time_slot is None:
                    self.set_status("failed")
                    self.resultReady.emit("No matching time slots found.")
                    return

                time_slot_form = best_time_slot.find("form")
                if not time_slot_form:
                    self.set_status("failed")
                    self.resultReady.emit("No form found in the best matching time slot.")
                    return

                time_slot_action_url = "https://moj.tvz.hr/" + time_slot_form["action"]
                time_slot_hidden_inputs = {
                    input_tag["name"]: input_tag["value"]
                    for input_tag in time_slot_form.find_all("input", type="hidden")
                }

                final_response = self.session.post(time_slot_action_url, data=time_slot_hidden_inputs)
                final_response.raise_for_status()

                if "obriši me iz grupe" in final_response.text.lower():
                    self.set_status("fulfilled")
                    self.resultReady.emit(True)
                else:
                    self.set_status("failed")
                    self.resultReady.emit("Failed to join the group. Please try again.")

            except requests.RequestException as e:
                self.set_status("failed")
                self.resultReady.emit(f"Request failed: {e}")
            except Exception as e:
                self.set_status("failed")
                self.resultReady.emit(f"Error: {str(e)}")

        except Exception as e:
            self.set_status("failed")
            self.resultReady.emit(f"Thread error: {str(e)}")

    def find_best_matching_card(self, cards):
        best_card = None
        best_score = float("-inf")

        for card in cards:
            title = card.find("div", class_="col-5").get_text().lower()
            score = 0

            for keyword in self.keywords:
                if keyword.startswith("+"):
                    if keyword[1:].lower() in title:
                        score += 1
                elif keyword.startswith("-"):
                    if keyword[1:].lower() in title:
                        score -= 1

            if score > best_score:
                best_card = card
                best_score = score

        return best_card, best_score