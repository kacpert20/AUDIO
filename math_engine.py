import numpy as np


def przygotuj_sygnal(amplitudy):
    """
    Zmienia zwykłą listę na tablicę numpy (typu float).
    To zabezpiecza nas przed przepełnieniem (A^2).
    """
    return np.array(amplitudy, dtype=np.float64)


def podziel_na_ramki(sygnal_np, czestotliwosc_probkowania, dlugosc_ramki_ms=20):
    """
    Dzieli sygnał na ramki o zadanej długości.
    """
    rozmiar_ramki = int((dlugosc_ramki_ms / 1000.0) * czestotliwosc_probkowania)


    ile_ramek = len(sygnal_np) // rozmiar_ramki
    sygnal_przyciety = sygnal_np[:ile_ramek * rozmiar_ramki]


    ramki = sygnal_przyciety.reshape((ile_ramek, rozmiar_ramki))
    return ramki


def oblicz_ste(ramki):
    """
    Oblicza Short Time Energy (STE) dla wszystkich ramek naraz.
    Zgodnie ze wzorem: STE(n) = (1/N) * sum(s_n(i)^2).
    """

    ste = np.mean(ramki ** 2, axis=1)
    return ste


def oblicz_glosnosc(ramki):
    """
    Oblicza Głośność (Volume) aproksymowaną jako pierwiastek średniej energii.
    Wzór: p(n) = sqrt(STE(n)).
    """

    glosnosc = np.sqrt(oblicz_ste(ramki))
    return glosnosc


def oblicz_zcr(ramki):
    """
    Oblicza Zero Crossing Rate (ZCR) - liczbę przejść przez zero.
    """
    N = ramki.shape[1]


    znak = np.sign(ramki)


    zmiany_znaku = np.abs(znak[:, 1:] - znak[:, :-1])


    zcr = np.sum(zmiany_znaku, axis=1) / (2 * N)
    return zcr

def detekcja_ciszy(glosnosc, zcr, prog_glosnosci=0.02, prog_zcr=0.1):
    """
    Na podstawie wyliczonej głośności i ZCR określa, czy dana ramka to cisza.
    Zwraca tablicę wartości logicznych (True - cisza, False - dźwięk).
    """
    # Zwraca True, jeśli OBA warunki są spełnione naraz
    cisza = (glosnosc < prog_glosnosci) & (zcr < prog_zcr)
    return cisza


def oblicz_autokorelacje(ramka):
    """
    Funkcja autokorelacji R_n(l). Szuka podobieństw przesuwając sygnał.
    """
    N = len(ramka)
    R = np.zeros(N)

    # Przesuwamy sygnał o 'l' próbek i mnożymy
    for l in range(N):
        # Mnożymy nieprzesunięty fragment przez przesunięty i sumujemy
        R[l] = np.sum(ramka[:N - l] * ramka[l:])

    return R


def oblicz_amdf(ramka):
    """
    Funkcja AMDF A_n(l). Szuka różnic między przesuniętymi sygnałami.
    POPRAWKA: Dzielimy przez (N-l), żeby uzyskać ŚREDNIĄ różnicę.
    """
    N = len(ramka)
    A = np.zeros(N)

    for l in range(N):
        ile_probek = N - l
        if ile_probek > 0:
            # Teraz dzielimy sumę przez liczbę próbek, które faktycznie porównaliśmy!
            A[l] = np.sum(np.abs(ramka[l:] - ramka[:N - l])) / ile_probek

    return A


def estymuj_f0(ramki, fs):
    """
    Wylicza F0 (w Hz) dla każdej ramki.
    Określa też fragmenty dźwięczne (wartość > 0) i bezdźwięczne (wartość = 0).
    """
    f0_tab = np.zeros(len(ramki))
    min_lag = int(fs / 500)
    max_lag = int(fs / 50)

    for i, ramka in enumerate(ramki):
        # SPRZĄTANIE 1: Ignorujemy ciche szmery. Zwiększamy próg z 50 na 200.
        if np.max(np.abs(ramka)) < 200:
            continue

        R = oblicz_autokorelacje(ramka)
        prawdziwy_max_lag = min(max_lag, len(R) - 1)

        if min_lag < prawdziwy_max_lag:
            fragment = R[min_lag:prawdziwy_max_lag]
            if len(fragment) > 0:
                idx_piku = np.argmax(fragment)
                wartosc_piku = fragment[idx_piku]

                # NOWY WARUNEK: Jeśli pik uderza w sufit (500Hz), to zrzucamy do zera
                if idx_piku == 0:
                    f0_tab[i] = 0
                elif wartosc_piku > 0.25 * R[0]:  # Tutaj Twój próg energii
                    pik = idx_piku + min_lag
                    f0_tab[i] = fs / pik
                else:
                    f0_tab[i] = 0

    return f0_tab


def estymuj_f0_amdf(ramki, fs):
    """
    Wylicza F0 (w Hz) dla każdej ramki używając funkcji AMDF.
    AMDF szuka MINIMUM różnicy, w przeciwieństwie do autokorelacji.
    """
    f0_tab = np.zeros(len(ramki))
    min_lag = int(fs / 500)
    max_lag = int(fs / 50)

    for i, ramka in enumerate(ramki):
        # Sprzątanie cichych szmerów (ten sam próg co wcześniej)
        if np.max(np.abs(ramka)) < 200:
            continue

        A = oblicz_amdf(ramka)
        prawdziwy_max_lag = min(max_lag, len(A) - 1)

        if min_lag < prawdziwy_max_lag:
            fragment = A[min_lag:prawdziwy_max_lag]
            if len(fragment) > 0:
                if len(fragment) > 0:
                    idx_dolka = np.argmin(fragment)
                    wartosc_dolka = fragment[idx_dolka]


                    if idx_dolka == 0:
                        f0_tab[i] = 0
                    elif wartosc_dolka < 0.8 * np.max(fragment):
                        pik = idx_dolka + min_lag
                        f0_tab[i] = fs / pik
                    else:
                        f0_tab[i] = 0

    return f0_tab


# =========================================================================
# 2. PARAMETRY NA POZIOMIE KLIPU (CLIP-LEVEL)
# =========================================================================

# --- 2.1. BAZUJĄCE NA GŁOŚNOŚCI ---

def oblicz_vstd(glosnosc):
    """2.1.1. Odchylenie standardowe głośności normalizowane przez Max głośność."""
    max_v = np.max(glosnosc)
    if max_v == 0: return 0
    return np.std(glosnosc) / max_v


def oblicz_vdr(glosnosc):
    """2.1.2. Volume Dynamic Range - Zakres dynamiki głośności."""
    max_v = np.max(glosnosc)
    if max_v == 0: return 0
    return (max_v - np.min(glosnosc)) / max_v


def oblicz_vu(glosnosc):
    """2.1.3. Volume Undulation - Falistość głośności (różnice szczytów i dolin)."""
    # Znajdujemy różnice między sąsiednimi próbkami głośności
    diffs = np.diff(glosnosc)
    # Sumujemy wartości bezwzględne zmian kierunku (uproszczona falistość)
    return np.sum(np.abs(diffs))


# --- 2.2. BAZUJĄCE NA ENERGII ---

def oblicz_lster(ste):
    """
    2.2.1. Low Short Time Energy Ratio.
    Odsetek ramek, gdzie STE < 50% średniej STE.
    """
    avSTE = np.mean(ste)  # Średnia dla całego klipu (uproszczone okno 1s)
    N = len(ste)
    if N == 0 or avSTE == 0: return 0

    # Implementacja wzoru ze sgn: (sgn(0.5*avSTE - STE) + 1) / 2
    count = np.sum((np.sign(0.5 * avSTE - ste) + 1) / 2)
    return count / N


def oblicz_energy_entropy(ramki):
    """
    2.2.2. Energy Entropy.
    Dzieli klip na segmenty, liczy znormalizowaną energię i entropię.
    """
    # Obliczamy energię dla każdej ramki (segmentu)
    energetyka_ramek = np.sum(ramki ** 2, axis=1)
    calkowita_energia = np.sum(energetyka_ramek)

    if calkowita_energia == 0: return 0

    # Normalizacja energii: sigma_i^2
    sigma_sq = energetyka_ramek / calkowita_energia

    # Wzór na entropię: -sum(sigma^2 * log2(sigma^2))
    # Dodajemy małą wartość 1e-10, żeby nie liczyć log(0)
    entropy = -np.sum(sigma_sq * np.log2(sigma_sq + 1e-10))
    return entropy


# --- 2.3. BAZUJĄCE NA ZCR ---

def oblicz_zstd(zcr):
    """2.3.1. Standardowe odchylenie ZCR."""
    return np.std(zcr)


def oblicz_hzcrr(zcr):
    """
    2.3.2. High Zero Crossing Rate Ratio.
    Odsetek ramek, gdzie ZCR > 1.5 * średnia ZCR.
    """
    avZCR = np.mean(zcr)
    N = len(zcr)
    if N == 0 or avZCR == 0: return 0

    # Wzór: (sgn(ZCR - 1.5*avZCR) + 1) / 2
    count = np.sum((np.sign(zcr - 1.5 * avZCR) + 1) / 2)
    return count / N


# --- DODATKOWE: SPEKTROGRAM I KLASYFIKACJA ---

def generuj_spektrogram(ramki):
    """Wylicza FFT dla ramek i zwraca dane w skali dB."""
    widmo = np.abs(np.fft.rfft(ramki, axis=1))
    return 20 * np.log10(widmo + 1e-6)


def klasyfikuj_mowa_muzyka(vstd, vdr, hzcrr):
    """
    Klasyfikacja eksperymentalna oparta na progach z bazy statystyk.
    """
    # 1. Twardy filtr na stabilne, podtrzymywane dźwięki (np. flet, skrzypce)
    # Jeśli dźwięk nie ma głębokich spadków głośności (VDR < 0.95), to na 100% instrument.
    if vdr < 0.95 and vstd < 0.15:
        return "MUZYKA / INSTRUMENT"

    # 2. Główny klasyfikator (szukanie szumiących spółgłosek)
    # Jeśli HZCRR przebija próg 0.025, mamy do czynienia z mową ludzką.
    if hzcrr > 0.025:
        return "MOWA"
    else:
        return "MUZYKA / INSTRUMENT"