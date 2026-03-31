import sys
import csv
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QHBoxLayout, QWidget, QFileDialog, QLabel, QGroupBox)

from audio_io import wczytaj_plik_wav
from math_engine import (przygotuj_sygnal, podziel_na_ramki, oblicz_ste,
                         oblicz_glosnosc, oblicz_zcr, detekcja_ciszy,
                         estymuj_f0, estymuj_f0_amdf, oblicz_vstd, oblicz_vdr,
                         oblicz_vu, oblicz_lster, oblicz_energy_entropy,
                         oblicz_zstd, oblicz_hzcrr, generuj_spektrogram, klasyfikuj_mowa_muzyka,
                         oblicz_czas_ataku)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza Dźwięku (czas)")
        self.setGeometry(100, 100, 1200, 900)
        self.regiony_ciszy = []
        self.aktualne_wyniki = {}
        self.regiony_dzwiezne = []
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # ================= PANEL LEWY (WYKRESY) =================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.lbl_plik = QLabel("Brak wczytanego pliku")
        self.lbl_plik.setStyleSheet("font-size: 13px; font-weight: bold; color: #aaaaff;")
        left_layout.addWidget(self.lbl_plik)
        self.btn_wczytaj = QPushButton("Wczytaj plik WAV")
        self.btn_wczytaj.setFixedHeight(40)
        self.btn_wczytaj.clicked.connect(self.wczytaj_i_analizuj)
        left_layout.addWidget(self.btn_wczytaj)

        self.plot_sygnal = pg.PlotWidget(title="1. Przebieg czasowy (Amplituda)")
        self.plot_glosnosc = pg.PlotWidget(title="2. Głośność (Volume)")
        self.plot_zcr = pg.PlotWidget(title="3. Zero Crossing Rate (ZCR)")
        self.plot_f0 = pg.PlotWidget(title="4. Ton podstawowy (F0)")
        self.plot_spec = pg.PlotWidget(title="5. Spektrogram (Widmo)")

        self.img_spec = pg.ImageItem()
        self.plot_spec.addItem(self.img_spec)
        self.img_spec.setLookupTable(pg.colormap.get('inferno').getLookupTable())

        plots = [self.plot_sygnal, self.plot_glosnosc, self.plot_zcr, self.plot_f0, self.plot_spec]
        for p in plots:
            p.showGrid(x=True, y=True)
            left_layout.addWidget(p)
            if p != self.plot_sygnal:
                p.setXLink(self.plot_sygnal)

        self.krzywa_sygnalu = self.plot_sygnal.plot(pen='y')
        self.krzywa_glosnosci = self.plot_glosnosc.plot(pen='c')
        self.krzywa_zcr = self.plot_zcr.plot(pen='m')
        self.plot_f0.addLegend()
        self.krzywa_f0 = self.plot_f0.plot(pen='g', symbol='o', symbolSize=4, name="F0 Auto")
        self.krzywa_f0_amdf = self.plot_f0.plot(pen='c', symbol='t', symbolSize=4, name="F0 AMDF")

        self.plot_sygnal.setLabel('left', 'Amplituda')
        self.plot_sygnal.setLabel('bottom', 'Czas [s]')
        self.plot_glosnosc.setLabel('left', 'Głośność (Volume)')
        self.plot_glosnosc.setLabel('bottom', 'Czas [s]')
        self.plot_zcr.setLabel('left', 'ZCR')
        self.plot_zcr.setLabel('bottom', 'Czas [s]')
        self.plot_f0.setLabel('left', 'F0 [Hz]')
        self.plot_f0.setLabel('bottom', 'Czas [s]')
        self.plot_spec.setLabel('left', 'Częstotliwość [Hz]')
        self.plot_spec.setLabel('bottom', 'Czas [s]')

        main_layout.addWidget(left_panel, stretch=3)

        # ================= PANEL PRAWY (STATYSTYKI) =================
        right_group = QGroupBox("Parametry klipu (Clip-Level)")
        right_layout = QVBoxLayout(right_group)

        self.lbl_klasyfikacja = QLabel("KLASYFIKACJA: -")
        self.lbl_klasyfikacja.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffaa00;")
        right_layout.addWidget(self.lbl_klasyfikacja)

        self.stats_labels = {}
        for key in ["Info", "VSTD", "VDR", "VU", "LSTER", "Entropy", "ZSTD", "HZCRR", "Czas Ataku"]:
            lbl = QLabel(f"{key}: -")
            lbl.setStyleSheet("font-family: 'Consolas';")
            right_layout.addWidget(lbl)
            self.stats_labels[key] = lbl

        self.btn_eksport = QPushButton("Eksportuj wyniki do CSV")
        self.btn_eksport.setFixedHeight(40)
        self.btn_eksport.setEnabled(False)
        self.btn_eksport.clicked.connect(self.eksportuj_do_csv)
        right_layout.addWidget(self.btn_eksport)

        right_layout.addStretch()
        main_layout.addWidget(right_group, stretch=1)

    def wczytaj_i_analizuj(self):
        sciezka, _ = QFileDialog.getOpenFileName(self, "Wybierz plik WAV", "", "Pliki WAV (*.wav)")
        if not sciezka: return

        fs, amplitudy = wczytaj_plik_wav(sciezka)
        if amplitudy is None: return

        self.lbl_plik.setText(f"{sciezka.split('/')[-1]}")

        sygnal_np = przygotuj_sygnal(amplitudy)
        ramki = podziel_na_ramki(sygnal_np, fs)
        ste = oblicz_ste(ramki)
        glosnosc = oblicz_glosnosc(ramki)
        zcr = oblicz_zcr(ramki)
        f0_auto = estymuj_f0(ramki, fs)
        f0_amdf = estymuj_f0_amdf(ramki, fs)

        cisza = detekcja_ciszy(glosnosc, zcr)
        rozmiar_ramki = int(0.02 * fs)

        vstd = oblicz_vstd(glosnosc)
        vdr = oblicz_vdr(glosnosc)
        vu = oblicz_vu(glosnosc)
        lster = oblicz_lster(ste)
        entropy = oblicz_energy_entropy(ramki)
        zstd = oblicz_zstd(zcr)
        hzcrr = oblicz_hzcrr(zcr)
        czas_ataku = oblicz_czas_ataku(amplitudy, fs)

        # Zaznacz fragmenty dźwięczne na wykresie F0
        if hasattr(self, 'regiony_dzwiezne'):
            for r in self.regiony_dzwiezne:
                self.plot_f0.removeItem(r)
        self.regiony_dzwiezne = []

        for i, f in enumerate(f0_auto):
            if f > 0:  # dźwięczna ramka
                t_start = i * 0.02
                t_end = (i + 1) * 0.02
                region = pg.LinearRegionItem(
                    values=[t_start, t_end],
                    brush=pg.mkBrush(0, 255, 100, 40),
                    movable=False
                )
                self.plot_f0.addItem(region)
                self.regiony_dzwiezne.append(region)

        typ = klasyfikuj_mowa_muzyka(lster, entropy)

        self.aktualne_wyniki = {
            "Plik": sciezka.split('/')[-1],
            "FS": fs,
            "VSTD": f"{vstd:.4f}",
            "VDR": f"{vdr:.4f}",
            "VU": f"{vu:.2f}",
            "LSTER": f"{lster:.4f}",
            "Entropy": f"{entropy:.2f}",
            "ZSTD": f"{zstd:.4f}",
            "HZCRR": f"{hzcrr:.4f}",
            "Czas Ataku": f"{czas_ataku:.4f} s",
            "Klasyfikacja": typ
        }
        self.btn_eksport.setEnabled(True)

        # ---- WYKRESY ----
        os_x_sygnal = np.arange(len(amplitudy)) / fs       # sekundy
        os_x_ramki = np.arange(len(ramki)) * 0.02          # sekundy

        self.krzywa_sygnalu.setData(x=os_x_sygnal, y=np.array(amplitudy, dtype=np.float64))
        self.krzywa_glosnosci.setData(x=os_x_ramki, y=glosnosc)
        self.krzywa_zcr.setData(x=os_x_ramki, y=zcr)
        self.krzywa_f0.setData(x=os_x_ramki, y=f0_auto)
        self.krzywa_f0_amdf.setData(x=os_x_ramki, y=f0_amdf)

        # ---- SPEKTROGRAM ----
        spec_data = generuj_spektrogram(ramki)              # (n_ramek, n_freq_bins)
        img = spec_data                                   # (n_freq_bins, n_ramek) — pyqtgraph: kolumny=X, wiersze=Y
        self.img_spec.setImage(img, autoLevels=True)
        # setTransform: skaluje piksele obrazu → jednostki wykresu
        # X: 1 kolumna = 0.02s,  Y: 1 wiersz = fs/2/n_freq_bins Hz
        n_freq_bins = img.shape[1]
        tr = pg.QtGui.QTransform()
        tr.scale(0.02, (fs / 2) / n_freq_bins)
        self.img_spec.setTransform(tr)
        self.plot_spec.getViewBox().invertY(False)

        self.lbl_klasyfikacja.setText(f"KLASYFIKACJA: {typ}")
        for k, v in self.aktualne_wyniki.items():
            if k in self.stats_labels:
                self.stats_labels[k].setText(f"{k}: {v}")

        self.plot_sygnal.autoRange()

        #print(f"Min głośność: {np.min(glosnosc):.1f}")
        #print(f"Max głośność: {np.max(glosnosc):.1f}")
        #print(f"10% max: {0.1 * np.max(glosnosc):.1f}")
        #print(f"Ramki poniżej 10% max: {np.sum(glosnosc < 0.1 * np.max(glosnosc))}")

    def eksportuj_do_csv(self):
        if not self.aktualne_wyniki: return
        sciezka_zapisu, _ = QFileDialog.getSaveFileName(self, "Zapisz wyniki", "wyniki_analizy.csv",
                                                        "Pliki CSV (*.csv)")
        if sciezka_zapisu:
            with open(sciezka_zapisu, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.aktualne_wyniki.keys())
                writer.writeheader()
                writer.writerow(self.aktualne_wyniki)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
