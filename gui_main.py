import sys
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QGroupBox)

from audio_io import wczytaj_plik_wav
from math_engine import (przygotuj_sygnal, podziel_na_ramki,
                         oblicz_glosnosc, oblicz_zcr, detekcja_ciszy, estymuj_f0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AiPD - Analiza Dźwięku 5.0")
        self.setGeometry(100, 100, 1000, 700)

        # GŁÓWNY UKŁAD OKNA (Poziomy: Lewo Wykresy, Prawo Parametry)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ================= PANEL LEWY (WYKRESY) =================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.btn_wczytaj = QPushButton("Wczytaj plik WAV")
        self.btn_wczytaj.clicked.connect(self.wczytaj_i_analizuj)
        left_layout.addWidget(self.btn_wczytaj)

        # Wykres 1: Przebieg czasowy (Sygnał)
        self.plot_sygnal = pg.PlotWidget(title="Przebieg czasowy (Amplituda)")
        self.plot_sygnal.showGrid(x=True, y=True)
        self.krzywa_sygnalu = self.plot_sygnal.plot(pen='y')
        left_layout.addWidget(self.plot_sygnal)

        # Wykres 2: Głośność (Volume)
        self.plot_glosnosc = pg.PlotWidget(title="Głośność w ramkach (Volume)")
        self.plot_glosnosc.showGrid(x=True, y=True)
        self.krzywa_glosnosci = self.plot_glosnosc.plot(pen='c')  # 'c' - cyan
        left_layout.addWidget(self.plot_glosnosc)

        # Wykres 3: ZCR
        self.plot_zcr = pg.PlotWidget(title="Zero Crossing Rate (ZCR)")
        self.plot_zcr.showGrid(x=True, y=True)
        self.krzywa_zcr = self.plot_zcr.plot(pen='m')  # 'm' - magenta
        left_layout.addWidget(self.plot_zcr)

        # Wykres 4: Ton podstawowy (F0)
        self.plot_f0 = pg.PlotWidget(title="Ton podstawowy (F0) - Autokorelacja")
        self.plot_f0.showGrid(x=True, y=True)
        self.krzywa_f0 = self.plot_f0.plot(pen='g', symbol='o', symbolSize=4)  # 'g' - zielony z kropkami
        left_layout.addWidget(self.plot_f0)

        # Pamiętaj o synchronizacji osi X!
        self.plot_f0.setXLink(self.plot_sygnal)

        # SYNCHRONIZACJA OSI X (Zoomowanie jednego przybliża wszystkie)
        self.plot_glosnosc.setXLink(self.plot_sygnal)
        self.plot_zcr.setXLink(self.plot_sygnal)

        main_layout.addWidget(left_panel, stretch=3)  # Wykresy zajmą 3/4 szerokości

        # ================= PANEL PRAWY (STATYSTYKI) =================
        right_panel = QGroupBox("Parametry nagrania (Clip-Level)")
        right_layout = QVBoxLayout(right_panel)

        self.lbl_info = QLabel("Brak wczytanego pliku.")
        self.lbl_glosnosc_max = QLabel("Max Głośność: -")
        self.lbl_zcr_srednie = QLabel("Średnie ZCR: -")

        right_layout.addWidget(self.lbl_info)
        right_layout.addWidget(self.lbl_glosnosc_max)
        right_layout.addWidget(self.lbl_zcr_srednie)
        right_layout.addStretch()  # Wypycha tekst do góry

        main_layout.addWidget(right_panel, stretch=1)  # Panel zajmie 1/4 szerokości

    def wczytaj_i_analizuj(self):
        sciezka, _ = QFileDialog.getOpenFileName(self, "Wybierz plik WAV", "", "Pliki WAV (*.wav)")

        if sciezka:
            czestotliwosc, amplitudy = wczytaj_plik_wav(sciezka)
            if amplitudy is None: return

            # 1. Rysowanie sygnału i blokada osi
            self.krzywa_sygnalu.setData(amplitudy)
            self.plot_f0.setLimits(xMin=0, xMax=len(amplitudy), yMin=0, yMax=600)
            self.plot_f0.autoRange()
            # ZABEZPIECZENIE: Ustawiamy granice (limits), żeby wykres nie uciekł
            self.plot_sygnal.setLimits(xMin=0, xMax=len(amplitudy), yMin=-35000, yMax=35000)
            # Automatycznie dopasowujemy widok po wczytaniu
            self.plot_sygnal.autoRange()

            # 2. Matematyka - Analiza Ramek
            sygnal_np = przygotuj_sygnal(amplitudy)
            ramki = podziel_na_ramki(sygnal_np, czestotliwosc, dlugosc_ramki_ms=20)

            glosnosc = oblicz_glosnosc(ramki)
            zcr = oblicz_zcr(ramki)




            # 3. Rysowanie parametrów
            # Tworzymy oś X dla ramek, żeby odpowiadała czasowi z głównego wykresu
            rozmiar_ramki = int((20 / 1000.0) * czestotliwosc)
            os_x_ramki = np.arange(len(ramki)) * rozmiar_ramki

            self.krzywa_glosnosci.setData(x=os_x_ramki, y=glosnosc)
            self.krzywa_zcr.setData(x=os_x_ramki, y=zcr)



            f0_wartosci = estymuj_f0(ramki, czestotliwosc)
            self.krzywa_f0.setData(x=os_x_ramki, y=f0_wartosci)

            # 4. Aktualizacja prawego panelu ze statystykami
            nazwa = sciezka.split('/')[-1]
            self.lbl_info.setText(f"Plik: {nazwa}\nPróbkowanie: {czestotliwosc} Hz\nLiczba ramek: {len(ramki)}")
            self.lbl_glosnosc_max.setText(f"Max Głośność: {np.max(glosnosc):.2f}")
            self.lbl_zcr_srednie.setText(f"Średnie ZCR: {np.mean(zcr):.4f}")






            # --- DETEKCJA I ZAZNACZANIE CISZY ---

            # 1. Czyszczenie starych zaznaczeń (POPRAWIONE)
            # Używamy nawiasów (), bo items() to metoda
            for item in self.plot_sygnal.items():
                if isinstance(item, pg.LinearRegionItem):
                    self.plot_sygnal.removeItem(item)

            # 2. Wywołanie funkcji matematycznej (SR)
            prog_vol = np.max(glosnosc) * 0.03
            cisza_tablica = detekcja_ciszy(glosnosc, zcr, prog_glosnosci=prog_vol, prog_zcr=0.1)

            # 3. Malowanie czerwonych bloków ciszy
            for i, czy_cisza in enumerate(cisza_tablica):
                if czy_cisza:
                    start_probka = i * rozmiar_ramki
                    koniec_probka = start_probka + rozmiar_ramki

                    region = pg.LinearRegionItem(values=[start_probka, koniec_probka],
                                                 brush=(255, 0, 0, 50),
                                                 movable=False)
                    region.lines[0].setPen(pg.mkPen(None))
                    region.lines[1].setPen(pg.mkPen(None))
                    self.plot_sygnal.addItem(region)

            # --- BLOKADY OSI (LIMITS) DLA POZOSTAŁYCH WYKRESÓW ---

            # Blokada dla Głośności
            self.plot_glosnosc.setLimits(xMin=0, xMax=len(amplitudy),
                                         yMin=0, yMax=np.max(glosnosc) * 1.1)
            self.plot_glosnosc.autoRange()

            # Blokada dla ZCR
            self.plot_zcr.setLimits(xMin=0, xMax=len(amplitudy),
                                    yMin=0, yMax=np.max(zcr) * 1.1)
            self.plot_zcr.autoRange()
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()