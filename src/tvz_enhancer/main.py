from PyQt6.QtWidgets import QApplication
from src.tvz_enhancer.common.app_manager import AppManager
from src.tvz_enhancer.scenes.login_scene import LoginScene
from src.tvz_enhancer.scenes.loading_scene import LoadingScene
import sys



def main():
    app = QApplication(sys.argv)
    manager = AppManager()

    login_scene = LoginScene(manager)
    manager.add_scene("login", login_scene)

    loading_scene = LoadingScene(manager)

    manager.add_scene("loading", loading_scene)

    manager.switch_to("loading")
    manager.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

#+kolokvij,+G1,+G2,+10:00,+11:00
#+Kolokvij,+12:00,+12:45








