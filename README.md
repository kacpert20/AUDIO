# AiPD - Analiza Dźwięku w Dziedzinie Czasu 🎙️🎸

Aplikacja okienkowa (GUI) służąca do zaawansowanej ekstrakcji, wizualizacji i analizy cech sygnału audio w dziedzinie czasu. Projekt zrealizowany w ramach przedmiotu Analiza i Przetwarzanie Dźwięku na ocenę 5.0. 

Aplikacja nie tylko obrazuje podstawowe właściwości sygnału (Frame-Level), ale też dokonuje długookresowej analizy statystycznej (Clip-Level) pozwalającej na zautomatyzowaną klasyfikację nagrań za pomocą nieliniowej heurystyki.

## Główne funkcjonalności

* **Rozbudowane GUI (PyQt6 & PyQtGraph):** Pięć zsynchronizowanych w czasie wykresów pozwalających na płynne przybliżanie i badanie sygnału.
* **Analiza Frame-Level:** Obliczanie energii (STE), Głośności oraz Zero Crossing Rate (ZCR).
* **Estymacja Tonu Podstawowego (F0):** Jednoczesna analiza metodami **Autokorelacji** oraz **AMDF** wraz z wykrywaniem fragmentów dźwięcznych.
* **Analiza Clip-Level & Statystyki:** Automatyczne wyliczanie VSTD, VDR, VU, LSTER, Entropii Energii, ZSTD, HZCRR oraz autorskiego **Czasu Ataku**.
* **Klasyfikacja (Mowa / Instrument):** Zastosowanie autorskiego, nieliniowego klasyfikatora opartego na paraboli decyzyjnej względem LSTER i Entropii Energii.
* **Eksport Danych:** Możliwość zapisu zebranych statystyk do pliku `.csv` jednym kliknięciem.
* **Spektrogram:** Podgląd dystrybucji częstotliwości (formantów i alikwotów).

## 🛠️ Wymagania i Architektura

Projekt opiera się wyłącznie na podstawowych operacjach matematycznych (`numpy`), celowo unikając wysokopoziomowych bibliotek analizy dźwięku (np. `librosa`), aby zaprezentować matematyczne podstawy DSP (Digital Signal Processing).

* **Python 3.x**
* **Numpy / Scipy** (matematyka i I/O)
* **PyQt6** (interfejs okienkowy)
* **PyQtGraph** (wydajne renderowanie wykresów)
* **Pandas** (opcjonalnie do pracy z bazami `.csv`)

## 🚀 Jak uruchomić?

1. Sklonuj to repozytorium na swój dysk:
   ```bash
   git clone [https://github.com/kacpert20/AUDIO.git](https://github.com/kacpert20/AUDIO.git)
   cd AUDIO
   python gui_main.py
   ```
2. Zainstaluj wymagane pakiety:
   ```bash
   pip install numpy scipy pyqtgraph PyQt6 pandas
   ```

3. Uruchom główny plik aplikacji:
   ```bash
   python gui_main.py
   ```

4. W aplikacji kliknij "Wczytaj plik WAV" i wybierz dowolną próbkę z folderu znormalizowane/.
## Ograniczenia znane w projekcie
Analiza w domenie czasu jest bardzo czuła na poziom szumów i jakość wejściową sygnału. Klasyfikatory czy detektory ciszy mogą działać mniej optymalnie dla mocno zaszumionych lub specyficznych plików (np. zawierających głośne spółgłoski wybuchowe). Dobór progów został zbalansowany pod kątem udostępnionego zbioru w repozytorium.
