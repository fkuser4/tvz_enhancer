import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCalendarWidget, QListWidget, QListWidgetItem, QDialog, QTextEdit, QHBoxLayout,
    QSpacerItem, QSizePolicy, QPushButton, QMessageBox, QFormLayout, QLineEdit, QComboBox, QTimeEdit, QFileDialog,
    QDateEdit
)
from PyQt6.QtGui import QTextCharFormat, QBrush, QColor, QFont, QIcon
from PyQt6.QtCore import Qt, QDate, QTime, QSize
from collections import defaultdict
from ics import Calendar
from pytz import timezone
from src.tvz_enhancer.utils.local_storage import save_local_events, load_local_events



def print_widget_hierarchy(widget, indent=0):
    print("  " * indent + f"{widget.metaObject().className()} (ObjectName: {widget.objectName()})")
    for child in widget.children():
        print_widget_hierarchy(child, indent + 1)


# Putanja do JSON datoteke za lokalno spremanje događaja
local_data_path = os.path.join(os.path.dirname(__file__), "../resources/data/kalendar_events.json")

# Globalno indeksirani događaji po datumu
indexed_events = defaultdict(list)

def parse_ics():
    """Parsira ICS datoteku i pohranjuje događaje u indeksirani format."""
    if not os.path.exists(ics_file_path):
        print(f"[WARN] Nema ICS datoteke: {ics_file_path}")
        return

    with open(ics_file_path, 'r', encoding='utf-8') as file:
        calendar = Calendar(file.read())

        local_tz = timezone("Europe/Zagreb")
        for event in calendar.events:
            adjusted_start = event.begin.astimezone(local_tz)
            adjusted_end = event.end.astimezone(local_tz)

            datum = adjusted_start.strftime("%Y-%m-%d")
            naziv = event.name

            # Automatski dodijeli tip na temelju naziva
            if "predavanja" in naziv.lower():
                tip = "Predavanja"
            elif "laboratorijske vježbe" in naziv.lower():
                tip = "Laboratorijske vježbe"
            else:
                tip = "Ostalo"

            event_data = {
                "Naziv": naziv,
                "Vrijeme početka": adjusted_start.strftime("%Y-%m-%d %H:%M"),
                "Vrijeme kraja": adjusted_end.strftime("%Y-%m-%d %H:%M"),
                "Lokacija": event.location,
                "Opis": event.description if event.description else "",
                "Tip": tip,
            }

            # Dodaj samo ako već nije u popisu za taj datum(nemoj dodavati duplikate)
            if event_data not in indexed_events[datum]:
                indexed_events[datum].append(event_data)


class CalendarModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        local_events = load_local_events()
        for datum, events in local_events.items():
            for event in events:
                if event not in indexed_events[datum]:
                    indexed_events[datum].append(event)
        #parse_ics()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Top Layout for Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        button_layout.addStretch()

        # "Import ics" gumb
        import_ics_button = QPushButton("Import ics")
        import_ics_svg_path = os.path.join(os.path.dirname(__file__), "../resources/document.svg")  # Putanja do SVG-a
        if os.path.exists(import_ics_svg_path):
            import_ics_icon = QIcon(import_ics_svg_path)
            import_ics_button.setIcon(import_ics_icon)
            import_ics_button.setIconSize(QSize(16, 16))  # Postavite veličinu ikone

        import_ics_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px;
                text-align: left; /* Ikona s lijeve strane */
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """)
        import_ics_button.clicked.connect(self.import_ics_action)
        button_layout.addWidget(import_ics_button)

        # "Dodaj događaj" gumb
        add_event_button = QPushButton("Dodaj događaj")
        add_event_svg_path = os.path.join(os.path.dirname(__file__), "../resources/plus.svg")  # Putanja do SVG-a
        if os.path.exists(add_event_svg_path):
            add_event_icon = QIcon(add_event_svg_path)
            add_event_button.setIcon(add_event_icon)
            add_event_button.setIconSize(QSize(16, 16))  # Postavite veličinu ikone

        add_event_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b; 
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px;
                text-align: left; /* Ikona s lijeve strane */
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """)
        add_event_button.clicked.connect(self.add_event_action)  # Placeholder method
        button_layout.addWidget(add_event_button)

        # Za centriranje kalendara
        centered_layout = QHBoxLayout()
        main_layout.addLayout(centered_layout)

        spacer_left = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        centered_layout.addItem(spacer_left)

        # Vertikalni layout za kalendar
        calendar_layout = QVBoxLayout()
        centered_layout.addLayout(calendar_layout)

        centered_layout.addItem(spacer_right)


        # Kalendar
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar_widget.selectionChanged.connect(self.update_day_events)
        self.calendar_widget.currentPageChanged.connect(self.update_calendar_highlights)



        # Maksimalna širina kalendara
        self.calendar_widget.setMaximumWidth(300)

        # kalendar Stylesheet
        self.calendar_widget.setStyleSheet("""
            QCalendarWidget QAbstractItemView {
                background-color: #1e1e1e; /* Pozadinska boja kalendara */
                color: #616060; /* Boja datuma */
            }
            QCalendarWidget QAbstractItemView::item:selected {
                color: #d3d3d3; /* Boja svih datuma, uključujući vikende */
                background-color: #030eb0; /* Pozadniska boja odabranog dana */
                color: white; /* Boja teksta za odabrani dan */
            }
            /* Header */
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background-color: #1e1e1e; 
                font-size: 18px;
            }
            
            
        """)


        calendar_layout.addWidget(self.calendar_widget)

        # Uređivanje gumbi za mijenjanje mjeseci
        nav_bar = self.calendar_widget.findChild(QWidget, "qt_calendar_navigationbar")
        if nav_bar:
            left_button = nav_bar.findChild(QWidget, "qt_calendar_prevmonth")
            right_button = nav_bar.findChild(QWidget, "qt_calendar_nextmonth")

            # Debugging
            print("Left Button:", left_button)
            print("Right Button:", right_button)

            # Put do ikona za gumbe
            left_arrow_path = os.path.join(os.path.dirname(__file__), "../resources/square-chevron-left.svg")
            right_arrow_path = os.path.join(os.path.dirname(__file__), "../resources/square-chevron-right.svg")

            # Ažuriraj ikone
            if left_button and os.path.exists(left_arrow_path):
                left_button.setIcon(QIcon(left_arrow_path))
                left_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2b2b2b;
                        border-radius: 5px;
                        padding: 5px;
                    }
                """)

            if right_button and os.path.exists(right_arrow_path):
                right_button.setIcon(QIcon(right_arrow_path))
                right_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2b2b2b;
                        border-radius: 5px;
                        padding: 5px;
                    }
                """)

        # Lista događaja ispod kalendara
        self.events_list = QListWidget()
        self.events_list.setStyleSheet("""
            background-color: black; /* Pozadniska i hover boja za evente */
            border: 1px solid black;
            border-radius: 4px;
            padding: 5px;
        """)
        main_layout.addWidget(self.events_list)

        # Update kalendar
        self.update_calendar_highlights()
        self.update_day_events()

    def import_ics_action(self):
        """Pokreće odabir ICS datoteke i parsira je."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Odaberite ICS datoteku",
            "",  # Početni direktorij
            "ICS datoteke (*.ics);;Sve datoteke (*)"  # Filtriranje datoteka
        )

        if file_path:  # Ako je putanja odabrana
            global ics_file_path
            ics_file_path = file_path
            indexed_events.clear()  # Očisti prethodno učitane događaje
            parse_ics()  # Parsiraj novu datoteku
            self.update_calendar_highlights()  # Ažuriraj kalendar s novim događajima
            self.update_day_events()  # Ažuriraj prikaz događaja za odabrani datum
        else:
            print("Nije odabrana datoteka.")

    def add_event_action(self):
        """Akcija za 'Dodaj događaj' gumb."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Dodaj novi događaj")
        dialog.setMinimumWidth(500)

        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main container
        container = QWidget(dialog)
        container.setObjectName("containerWidget")
        container.setFixedWidth(450)
        container.setStyleSheet("""
            QWidget#containerWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(20)

        # Title
        title_label = QLabel("Novi događaj")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #000000;
            }
        """)
        container_layout.addWidget(title_label)

        # Form fields
        field_style = """
            QLineEdit, QTimeEdit, QComboBox, QDateEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 16px;
                color: #000000;
                min-height: 30px;
            }
            QTimeEdit::up-button, QTimeEdit::down-button,
            QDateEdit::up-button, QDateEdit::down-button {
                width: 0px;
                height: 0px;
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
        """
        dialog.setStyleSheet(field_style)

        # Input fields
        def create_label(text):
            label = QLabel(text)
            label.setStyleSheet("font-size: 16px; font-weight: 500; color: #000000;")
            return label

        # Naziv
        container_layout.addWidget(create_label("Naziv"))
        naziv_input = QLineEdit()
        naziv_input.setPlaceholderText("Unesite naziv događaja")
        container_layout.addWidget(naziv_input)

        # Vrijeme početka
        container_layout.addWidget(create_label("Vrijeme početka"))
        vrijeme_pocetka_input = QTimeEdit()
        vrijeme_pocetka_input.setDisplayFormat("HH:mm")
        container_layout.addWidget(vrijeme_pocetka_input)

        # Vrijeme kraja
        container_layout.addWidget(create_label("Vrijeme kraja"))
        vrijeme_kraja_input = QTimeEdit()
        vrijeme_kraja_input.setDisplayFormat("HH:mm")
        vrijeme_kraja_input.setTime(vrijeme_pocetka_input.time().addSecs(3600))
        container_layout.addWidget(vrijeme_kraja_input)

        # Lokacija
        container_layout.addWidget(create_label("Lokacija"))
        lokacija_input = QLineEdit()
        lokacija_input.setPlaceholderText("Unesite lokaciju")
        container_layout.addWidget(lokacija_input)

        # Vrsta događaja
        container_layout.addWidget(create_label("Vrsta događaja"))
        vrsta_dogadaja = QComboBox()
        vrsta_dogadaja.addItems(["Predavanja", "Laboratorijske vježbe", "Ispit", "Drugo"])
        container_layout.addWidget(vrsta_dogadaja)

        # Ponavljanje checkbox
        ponavljanje_checkbox = QPushButton("Dodaj za više dana")
        ponavljanje_checkbox.setCheckable(True)
        ponavljanje_checkbox.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #000000;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:checked {
                background-color: #f3f4f6;
                border-color: #000000;
            }
        """)
        container_layout.addWidget(ponavljanje_checkbox)

        # Krajnji datum
        krajnji_datum_widget = QWidget()
        krajnji_datum_layout = QVBoxLayout(krajnji_datum_widget)
        krajnji_datum_layout.setContentsMargins(0, 0, 0, 0)
        krajnji_datum_layout.setSpacing(8)

        krajnji_datum_label = QLabel("Krajnji datum ponavljanja")
        krajnji_datum_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #000000;")
        krajnji_datum_label.setEnabled(False)

        krajnji_datum_input = QDateEdit()
        krajnji_datum_input.setCalendarPopup(True)
        krajnji_datum_input.setDate(self.calendar_widget.selectedDate())
        krajnji_datum_input.setEnabled(False)

        krajnji_datum_layout.addWidget(krajnji_datum_label)
        krajnji_datum_layout.addWidget(krajnji_datum_input)
        container_layout.addWidget(krajnji_datum_widget)

        def toggle_repeat_options():
            krajnji_datum_label.setEnabled(ponavljanje_checkbox.isChecked())
            krajnji_datum_input.setEnabled(ponavljanje_checkbox.isChecked())

        ponavljanje_checkbox.clicked.connect(toggle_repeat_options)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        odustani_button = QPushButton("Odustani")
        odustani_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #000000;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)

        dodaj_button = QPushButton("Dodaj događaj")
        dodaj_button.setStyleSheet("""
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

        button_layout.addWidget(odustani_button)
        button_layout.addWidget(dodaj_button)
        container_layout.addLayout(button_layout)

        # Center the container
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Functionality
        def dodaj_dogadaj():
            naziv = naziv_input.text()
            vrijeme_pocetka = vrijeme_pocetka_input.time().toString("HH:mm")
            vrijeme_kraja = vrijeme_kraja_input.time().toString("HH:mm")
            lokacija = lokacija_input.text()
            tip = vrsta_dogadaja.currentText()
            datum = self.calendar_widget.selectedDate()
            krajnji_datum = krajnji_datum_input.date()

            if not naziv or not vrijeme_pocetka or not vrijeme_kraja:
                QMessageBox.warning(dialog, "Greška", "Sva polja moraju biti ispunjena!")
                return

            current_date = datum
            while current_date <= krajnji_datum:
                if not ponavljanje_checkbox.isChecked() or current_date.dayOfWeek() == datum.dayOfWeek():
                    novi_event = {
                        "Naziv": naziv,
                        "Vrijeme početka": f"{current_date.toString('yyyy-MM-dd')} {vrijeme_pocetka}",
                        "Vrijeme kraja": f"{current_date.toString('yyyy-MM-dd')} {vrijeme_kraja}",
                        "Lokacija": lokacija,
                        "Tip": tip,
                        "Opis": ""
                    }
                    indexed_events[current_date.toString('yyyy-MM-dd')].append(novi_event)
                current_date = current_date.addDays(1)

            save_local_events(indexed_events)
            self.update_day_events()
            dialog.accept()

        dodaj_button.clicked.connect(dodaj_dogadaj)
        odustani_button.clicked.connect(dialog.reject)

        # Add input validation
        def validate_inputs():
            naziv = naziv_input.text().strip()
            lokacija = lokacija_input.text().strip()
            dodaj_button.setEnabled(bool(naziv and lokacija))

        naziv_input.textChanged.connect(validate_inputs)
        lokacija_input.textChanged.connect(validate_inputs)
        validate_inputs()  # Initial validation

        dialog.exec()

    def update_calendar_highlights(self):
        """Ističe datume koji imaju događanja u kalendaru."""
        for datum, events in indexed_events.items():
            qdate = QDate.fromString(datum, "yyyy-MM-dd")
            if not qdate.isValid():
                continue

            format = QTextCharFormat()
            format.setBackground(QBrush(QColor("#2e2e2e")))  # boja pozadine za datume s događajima
            format.setForeground(QBrush(QColor("white")))  # boja teksta za datume s događajima
            format.setFontWeight(QFont.Weight.Bold)

            self.calendar_widget.setDateTextFormat(qdate, format)

    def update_day_events(self):
        """Ažurira prikaz događaja za odabrani dan."""
        self.events_list.clear()

        # Prikaz odabranog datuma iznad liste događaja
        selected_date = self.calendar_widget.selectedDate()
        selected_date_str = selected_date.toString("dddd, dd. MMMM yyyy").replace('January', 'siječnja').replace(
            'February', 'veljače').replace('March', 'ožujka').replace('April', 'travnja').replace('May',
                                                                                                  'svibnja').replace(
            'June', 'lipnja').replace('July', 'srpnja').replace('August', 'kolovoza').replace('September',
                                                                                              'rujna').replace(
            'October', 'listopada').replace('November', 'studenoga').replace('December', 'prosinca').replace('Monday',
                                                                                                             'ponedjeljak').replace(
            'Tuesday', 'utorak').replace('Wednesday', 'srijeda').replace('Thursday', 'četvrtak').replace('Friday',
                                                                                                         'petak').replace(
            'Saturday', 'subota').replace('Sunday', 'nedjelja')  # Formatted date
        date_label = QListWidgetItem()  # placeholder
        date_label_widget = QLabel(selected_date_str)  # QLabel za prikaz datuma
        date_label_widget.setStyleSheet(
            "color: #d3d3d3; font-size: 14px; font-weight: bold; padding: 0px;")
        self.events_list.addItem(date_label)  # placeholder
        self.events_list.setItemWidget(date_label, date_label_widget)  # QLabel kao widget za item

        # Dohvati događaje za odabrani datum
        selected_date_iso = selected_date.toString("yyyy-MM-dd")
        events = indexed_events.get(selected_date_iso, [])
        events.sort(key=lambda e: e["Vrijeme početka"])

        # Dodavanje događaja u listu
        for event in events:
            self.add_event_to_list(event)

    def add_event_to_list(self, event):
        """Dodaje događaj u listu događaja sa stilom, gumbima za brisanje i izmjenu."""
        # Extract event details
        naziv = event["Naziv"]
        vrijeme_pocetka = event["Vrijeme početka"].split()[1]
        vrijeme_kraja = event["Vrijeme kraja"].split()[1]
        lokacija = event["Lokacija"] or "N/A"
        tip = event.get("Tip", "")  # Dohvati tip događaja

        # Odredi boju indikatora na temelju tipa događaja
        if tip.lower() == "predavanja":
            indicator_color = "#3BA55D"
            oznaka_tipa = "[Predavanja]"
        elif tip.lower() == "laboratorijske vježbe":
            indicator_color = "#5555FF"
            oznaka_tipa = "[Lab]"
        elif tip.lower() == "ispit":
            indicator_color = "red"
            oznaka_tipa = "[Ispit]"
        else:
            indicator_color = "#FFA500"
            oznaka_tipa = "[Ostalo]"

        # Dodaj oznaku tipa uz naziv
        naziv_s_oznakom = f"{naziv} {oznaka_tipa}"

        # custom widget za događaj
        event_widget = QWidget()
        event_layout = QVBoxLayout(event_widget)
        event_layout.setContentsMargins(6, 2, 6, 2)
        event_layout.setSpacing(1)

        # Naslov događaja
        title_label = QLabel(naziv_s_oznakom)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FFFFFF; border:none;")
        event_layout.addWidget(title_label)

        # Vrijeme događaja
        time_label = QLabel(f"{vrijeme_pocetka} - {vrijeme_kraja}")
        time_label.setStyleSheet("font-size: 10px; color: #AAAAAA; border:none;")
        event_layout.addWidget(time_label)

        # Lokacija događaja
        if lokacija:
            location_label = QLabel(f"Lokacija: {lokacija}")
            location_label.setStyleSheet("font-size: 10px; color: #CCCCCC; border:none;")
            event_layout.addWidget(location_label)

        # Gubmi uredi i briši
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)

        delete_button = QPushButton("Obriši")
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                font-size: 8px;
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #3c3c3c; 
            }
        """)
        delete_button.clicked.connect(lambda: self.delete_event(event)) #spoji na funkciju briši
        button_layout.addStretch()  # stavlja gumbe na desno
        button_layout.addWidget(delete_button)

        edit_button = QPushButton("Uredi")
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b; 
                color: white;
                font-size: 8px; 
                border-radius: 3px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """)
        edit_button.clicked.connect(lambda: self.edit_event(event))  # spoji na funkcij uredi
        button_layout.addWidget(edit_button)

        event_layout.addLayout(button_layout)

        # Indikator boja sastrane
        indicator = QWidget()
        indicator.setFixedWidth(5)  # Širina indikatora
        indicator.setStyleSheet(f"background-color: {indicator_color}; border-radius: 2px; border:none;")
        indicator_layout = QHBoxLayout()
        indicator_layout.addWidget(indicator)
        indicator_layout.addWidget(event_widget)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.setSpacing(7)

        # Kombiniramo indikator i glavni widget
        container_widget = QWidget()
        container_widget.setLayout(indicator_layout)
        container_widget.setStyleSheet(
            "background-color: #222222; border-radius: 6px; padding: 2px;")

        # Dodaj widget u listu
        item = QListWidgetItem(self.events_list)
        item.setSizeHint(container_widget.sizeHint())
        self.events_list.addItem(item)
        self.events_list.setItemWidget(item, container_widget)

    def delete_event(self, event):
        """Briše događaj iz popisa događaja uz opciju brisanja ponavljajućih događaja."""
        # Otvori dijalog za potvrdu brisanja
        reply = QMessageBox.question(
            self,
            "Potvrda brisanja",
            "Želite li izbrisati sve ponavljajuće događaje?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return  # Prekid ako korisnik otkaže

        selected_date = self.calendar_widget.selectedDate().toString("yyyy-MM-dd")
        selected_day_of_week = QDate.fromString(selected_date, "yyyy-MM-dd").dayOfWeek()

        if reply == QMessageBox.StandardButton.No:  # Brisanje samo trenutnog događaja
            if selected_date in indexed_events:
                if event in indexed_events[selected_date]:
                    indexed_events[selected_date].remove(event)

                    # Ako više nema događaja za taj datum, ukloni ključ
                    if not indexed_events[selected_date]:
                        del indexed_events[selected_date]

        elif reply == QMessageBox.StandardButton.Yes:  # Brisanje svih ponavljajućih događaja
            for date, events in list(indexed_events.items()):
                # Dohvati dan u tjednu za trenutni datum
                current_day_of_week = QDate.fromString(date, "yyyy-MM-dd").dayOfWeek()

                # Filtriraj događaje koji imaju isti naziv, vrijeme, lokaciju, tip i dan u tjednu
                indexed_events[date] = [
                    e for e in events
                    if not (
                            e["Naziv"] == event["Naziv"]
                            and e["Vrijeme početka"].split()[1] == event["Vrijeme početka"].split()[1]
                            and e["Vrijeme kraja"].split()[1] == event["Vrijeme kraja"].split()[1]
                            and e["Lokacija"] == event["Lokacija"]
                            and e.get("Tip", "").lower() == event.get("Tip", "").lower()
                            and current_day_of_week == selected_day_of_week
                    )
                ]
                # Ako je popis događaja za datum prazan, ukloni ključ
                if not indexed_events[date]:
                    del indexed_events[date]

        # Spremi promjene u lokalnu datoteku
        save_local_events(indexed_events)

        # Osvježi prikaz događaja
        self.update_day_events()

    def edit_event(self, event):
        """Otvara dijalog za uređivanje događaja."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Uredi događaj")
        layout = QVBoxLayout(dlg)

        # Naziv događaja
        naziv_label = QLabel("Naziv:")
        layout.addWidget(naziv_label)
        naziv_edit = QTextEdit(event["Naziv"])
        naziv_edit.setMaximumHeight(30)
        layout.addWidget(naziv_edit)

        # Vrijeme početka
        vrijeme_pocetka_label = QLabel("Vrijeme početka (HH:MM):")
        layout.addWidget(vrijeme_pocetka_label)
        vrijeme_pocetka_edit = QTextEdit(event["Vrijeme početka"].split()[1])
        vrijeme_pocetka_edit.setMaximumHeight(30)
        layout.addWidget(vrijeme_pocetka_edit)

        # Vrijeme kraja
        vrijeme_kraja_label = QLabel("Vrijeme kraja (HH:MM):")
        layout.addWidget(vrijeme_kraja_label)
        vrijeme_kraja_edit = QTextEdit(event["Vrijeme kraja"].split()[1])
        vrijeme_kraja_edit.setMaximumHeight(30)
        layout.addWidget(vrijeme_kraja_edit)

        # Lokacija
        lokacija_label = QLabel("Lokacija:")
        layout.addWidget(lokacija_label)
        lokacija_edit = QTextEdit(event["Lokacija"])
        lokacija_edit.setMaximumHeight(30)
        layout.addWidget(lokacija_edit)

        # Gumbi za potvrdu i odustajanje
        button_layout = QHBoxLayout()
        save_button = QPushButton("Spremi")
        save_button.clicked.connect(
            lambda: self.save_event_changes(
                dlg,
                event,
                naziv_edit.toPlainText(),
                vrijeme_pocetka_edit.toPlainText(),
                vrijeme_kraja_edit.toPlainText(),
                lokacija_edit.toPlainText(),
            )
        )
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Odustani")
        cancel_button.clicked.connect(dlg.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dlg.exec()

    def save_event_changes(self, dlg, original_event, naziv, vrijeme_pocetka, vrijeme_kraja, lokacija):
        """Spremi promjene događaja."""
        # Provjera unosa
        if not naziv or not vrijeme_pocetka or not vrijeme_kraja:
            QMessageBox.warning(self, "Greška", "Sva polja moraju biti ispunjena!")
            return

        # Dohvati datum događaja
        datum = original_event["Vrijeme početka"].split()[0]

        # Kreiraj ažurirani događaj
        updated_event = {
            "Naziv": naziv,
            "Vrijeme početka": f"{datum} {vrijeme_pocetka}",
            "Vrijeme kraja": f"{datum} {vrijeme_kraja}",
            "Lokacija": lokacija,
            "Tip": original_event.get("Tip", "Predavanja"),  # Ako nema tipa, pretpostavi 'Predavanja'
            "Opis": original_event.get("Opis", ""),
        }

        # Ažuriraj događaj u indeksu
        if datum in indexed_events:
            for i, ev in enumerate(indexed_events[datum]):
                if ev == original_event:
                    indexed_events[datum][i] = updated_event
                    break

        # Spremi promjene u lokalnu datoteku
        try:
            save_local_events(indexed_events)
        except Exception as e:
            print(f"Greška pri spremanju događaja: {e}")
            QMessageBox.critical(self, "Greška", "Došlo je do pogreške prilikom spremanja promjena.")
            return

        # Osvježi prikaz
        self.update_day_events()

        # Zatvori dijalog
        dlg.accept()

    def show_event_details(self, event):
        """Prikazuje detalje događaja u dijalogu."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Detalji događaja")
        layout = QVBoxLayout(dlg)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(f"Naziv: {event['Naziv']}\n" +
                          f"Vrijeme: {event['Vrijeme početka']} - {event['Vrijeme kraja']}\n" +
                          f"Lokacija: {event['Lokacija']}\n" +
                          f"Opis: {event['Opis']}")
        text_edit.setStyleSheet("""
            background-color: #1e1e1e;
            color: #dcdcdc;
            border: 1px solid #444444;
            border-radius: 4px;
            padding: 10px;
        """)
        layout.addWidget(text_edit)

        dlg.setStyleSheet("background-color: #2d2d2d;")
        dlg.exec()