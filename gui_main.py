import sys
from PyQt6.QtWidgets import QApplication, QMainWindow


def main():
    # Inicjalizacja aplikacji
    app = QApplication(sys.argv)

    # Tworzenie głównego okna
    window = QMainWindow()
    window.setWindowTitle("AiPD - Analiza Dźwięku 5.0")
    window.setGeometry(100, 100, 800, 600)  # x, y, szerokość, wysokość

    # Wyświetlenie okna
    window.show()

    # Uruchomienie pętli zdarzeń
    sys.exit(app.exec())


if __name__ == '__main__':
    main()