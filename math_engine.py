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
    """
    N = len(ramka)
    A = np.zeros(N)

    for l in range(N):
        # Odejmujemy przesunięty sygnał od nieprzesuniętego i sumujemy wartości bezwzględne
        A[l] = np.sum(np.abs(ramka[l:] - ramka[:N - l]))

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
        if np.max(np.abs(ramka)) < 50:
            continue

        R = oblicz_autokorelacje(ramka)
        prawdziwy_max_lag = min(max_lag, len(R) - 1)

        if min_lag < prawdziwy_max_lag:
            fragment = R[min_lag:prawdziwy_max_lag]
            if len(fragment) > 0:
                idx_piku = np.argmax(fragment)
                wartosc_piku = fragment[idx_piku]

                # Zabezpieczenie przed szumem/bezdźwięcznością:
                if wartosc_piku > 0.3 * R[0]:
                    pik = idx_piku + min_lag
                    f0_tab[i] = fs / pik
                else:
                    f0_tab[i] = 0  # Fragment bezdźwięczny / szum

    return f0_tab