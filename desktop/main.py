import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from app.core.token_store import clear_tokens
from app.views.login_view import LoginView
from app.views.main_window import MainWindow
from app.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    # Inter yoksa Segoe UI'ya düş
    font = QFont("Inter", 13)
    if not font.exactMatch():
        font = QFont("Segoe UI", 13)
    app.setFont(font)

    # Her açılışta önceki oturumu sil — PIN her seferinde sorulsun
    clear_tokens()

    def ac_ana_pencere():
        pencere.hide()
        main_win = MainWindow()
        main_win.show()
        app._main_win = main_win

    pencere = LoginView()
    pencere.giris_yapildi.connect(ac_ana_pencere)
    pencere.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
