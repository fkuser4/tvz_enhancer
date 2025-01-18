import json
import os
from PyQt6.QtWebEngineCore import QWebEngineCookieStore
from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtCore import QDateTime, QUrl


class CookieManager:
    def __init__(self, cookie_file="cookies.json"):
        self.cookie_file = cookie_file
        self.cookies = []
        self.cookie_store = None
        self._clear_cookie_file()

    def set_cookie_store(self, cookie_store: QWebEngineCookieStore):
        self.cookie_store = cookie_store
        self.cookie_store.cookieAdded.connect(self._on_cookie_added)
        self.cookie_store.cookieRemoved.connect(self._on_cookie_removed)

        self.cookie_store.setCookieFilter(lambda _: True)

    def _on_cookie_added(self, cookie):
        try:
            name = cookie.name().data().decode('utf-8')
            value = cookie.value().data().decode('utf-8')

            cookie_data = {
                'name': name,
                'value': value,
                'domain': cookie.domain(),
                'path': cookie.path(),
                'secure': cookie.isSecure(),
                'httpOnly': cookie.isHttpOnly(),
                'expiry': cookie.expirationDate().toSecsSinceEpoch() if cookie.expirationDate().isValid() else None
            }

            self.cookies = [c for c in self.cookies if not (c['name'] == name and c['domain'] == cookie.domain())]
            self.cookies.append(cookie_data)
            self._save_cookies_to_file()

        except Exception as e:
            print(f"Error processing cookie: {e}")

    def _on_cookie_removed(self, cookie):
        try:
            name = cookie.name().data().decode('utf-8')
            self.cookies = [c for c in self.cookies if not (c['name'] == name and c['domain'] == cookie.domain())]
            self._save_cookies_to_file()
        except Exception as e:
            print(f"Error removing cookie: {e}")

    def load_cookies(self):
        try:
            if os.path.exists(self.cookie_file):
                with open(self.cookie_file, "r") as file:
                    self.cookies = json.load(file)

                if self.cookie_store:
                    for cookie_data in self.cookies:
                        qt_cookie = QNetworkCookie(
                            cookie_data['name'].encode(),
                            cookie_data['value'].encode()
                        )
                        qt_cookie.setDomain(cookie_data['domain'])
                        qt_cookie.setPath(cookie_data['path'])
                        qt_cookie.setSecure(cookie_data['secure'])
                        qt_cookie.setHttpOnly(cookie_data['httpOnly'])

                        if cookie_data['expiry']:
                            qt_cookie.setExpirationDate(
                                QDateTime.fromSecsSinceEpoch(cookie_data['expiry'])
                            )

                        self.cookie_store.setCookie(
                            qt_cookie,
                            QUrl(f"https://{cookie_data['domain']}")
                        )
        except Exception as e:
            print(f"Error loading cookies: {e}")

    def _save_cookies_to_file(self):
        try:
            with open(self.cookie_file, "w") as file:
                json.dump(self.cookies, file, indent=4)
        except Exception as e:
            print(f"Error saving cookies: {e}")

    def _clear_cookie_file(self):
        try:
            with open(self.cookie_file, "w") as file:
                json.dump([], file, indent=4)
        except Exception as e:
            print(f"Error clearing cookie file: {e}")

