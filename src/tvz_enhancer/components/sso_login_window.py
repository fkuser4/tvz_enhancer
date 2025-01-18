import requests
from PyQt6.QtCore import QUrl, pyqtSignal, Qt
from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMainWindow, QMessageBox
from bs4 import BeautifulSoup
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineCookieStore
from PyQt6.QtCore import QDateTime

from src.tvz_enhancer.utils.cookie_manager import CookieManager


class SSOLoginWindow(QMainWindow):
    login_completed = pyqtSignal(bool)
    login_canceled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prijava u TVZ Enhancer")
        self.setGeometry(200, 200, 400, 550)
        self.setFixedSize(400, 550)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowMinimizeButtonHint & ~Qt.WindowType.WindowMaximizeButtonHint & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        # Create a transparent icon
        transparent_icon = QIcon(self.create_transparent_pixmap(16, 16))
        self.setWindowIcon(transparent_icon)
        QApplication.setWindowIcon(transparent_icon)

        self.url = "https://moj.tvz.hr/"
        self.cookie_manager = CookieManager()
        self.cookie_store = QWebEngineProfile.defaultProfile().cookieStore()
        self.cookie_manager.set_cookie_store(self.cookie_store)

        self.redirect_url = self.getSOOLoginUrl()

        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)

        if self.redirect_url:
            self.web_view.setUrl(QUrl(self.redirect_url))
            self.web_view.urlChanged.connect(self.check_for_redirect)
        else:
            self.web_view.setUrl(QUrl(self.url))
            QMessageBox.critical(self, "Login Error",
                                 "Failed to connect to the login page. Please try again later.")

        layout.addWidget(self.web_view)
        self.setCentralWidget(central_widget)
        self.check_timer = None

    def getSOOLoginUrl(self):
        try:
            session = requests.Session()
            response = session.get(self.url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form', {'name': 'microsoft_form'})
            if not form:
                raise ValueError("Form not found on the page.")

            form_action = form.get('action') or self.url
            hidden_inputs = form.find_all('input', {'type': 'hidden'})
            payload = {inp.get('name'): inp.get('value') for inp in hidden_inputs}
            payload['microsoft_login'] = ''

            post_response = session.post(form_action, data=payload, allow_redirects=True, timeout=10)
            post_response.raise_for_status()

            for cookie in session.cookies:
                qt_cookie = QNetworkCookie(cookie.name.encode(), cookie.value.encode())
                qt_cookie.setDomain(cookie.domain)
                qt_cookie.setPath(cookie.path)
                qt_cookie.setSecure(cookie.secure)
                qt_cookie.setHttpOnly(cookie.has_nonstandard_attr('HttpOnly'))

                if cookie.expires:
                    qt_cookie.setExpirationDate(QDateTime.fromSecsSinceEpoch(cookie.expires))

                self.cookie_store.setCookie(qt_cookie, QUrl(f"https://{cookie.domain}"))

            return post_response.url
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except ValueError as e:
            print(f"Parsing error: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def create_transparent_pixmap(self, width, height):
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(0, 0, 0, 0))
        return pixmap

    def check_for_redirect(self, new_url):
        if new_url.toString().startswith(
                "https://moj.tvz.hr/index.php?state="):
            self.login_completed.emit(True)
            self.close()

    def closeEvent(self, event):
        self.login_canceled.emit(True)
        event.accept()




