import sys
from PyQt6.QtWidgets import QApplication

from app.core.token_store import get_access_token
from app.views.login_view import LoginView
from app.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    def ac_ana_pencere():
        pencere.hide()
        main_win = MainWindow()
        main_win.show()
        app._main_win = main_win   # GC'den korunmak için referans tut

    pencere = LoginView()

    # Kayıtlı token varsa login atla
    if get_access_token():
        main_win = MainWindow()
        main_win.show()
    else:
        pencere.giris_yapildi.connect(ac_ana_pencere)
        pencere.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
