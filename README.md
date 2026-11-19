# Song Generator

*English: [README.en.md](README.en.md)*

Lokalny generator piosenek na Windows. Wpisujesz gatunek, nastrój i (opcjonalnie) tekst — aplikacja sama
napisze tekst i skomponuje utwór. Wszystko działa **na twoim komputerze**: bez chmury, bez kont, bez limitów.

- **Tekst:** Gemma 4 12B pisze słowa piosenki, wypełnia szablon (twoje wersy zostają) albo układa twój gotowy tekst
  w strukturę zwrotek i refrenów; proponuje też tytuł.
- **Muzyka:** ACE-Step 1.5 generuje utwór do 5 minut (MP3 lub WAV), z wokalem w języku polskim, angielskim,
  włoskim, niemieckim, hiszpańskim lub francuskim, albo sam podkład.
- **Silnik:** KoboldCpp (CUDA), uruchamiany i przełączany przez aplikację — nie trzeba go obsługiwać ręcznie.

Aplikacja wycięta z Little Mate: zostały tylko obsługa modeli i generator muzyki.

## Wymagania

- Windows 10/11, karta NVIDIA z CUDA. Sprawdzone na **RTX 4070 12 GB** (Gemma i ACE-Step nie mieszczą się
  razem w 12 GB, więc zawsze działa jeden zestaw modeli).
- Python 3.12 (tylko biblioteka standardowa) + opcjonalnie `pywebview` (`pip install pywebview`) dla natywnego okna.
  Bez `pywebview` strona otwiera się w przeglądarce.
- ok. 19 GB na modele (lista i rozmiary: `modele\README.md`) oraz `koboldcpp.exe` w `serwer\`
  (źródło i rozmiar: `serwer\README.md`). Jedno i drugie jest poza gitem.

## Uruchomienie

`start.cmd` (albo `python app\songgen.py`). Aplikacja startuje serwer modeli z profilem `gemma` i otwiera okno;
pasek w nagłówku pokazuje, co jest załadowane, a podczas ładowania — kółko i szacowany postęp.
Zamknięcie okna kończy aplikację i zwalnia kartę graficzną (`unload_on_exit` w `app\app.json`).
Drugie uruchomienie przy działającej aplikacji wynosi jej okno na wierzch.

## Jak z tego korzystać

1. Wybierz **gatunek**, ewentualnie **skład**, **wokal**, **język**, **długość** (30 s – 5 min).
2. Opcjonalnie wpisz tytuł i opis stylu; w polu tekstu użyj **Gemma: wypełnij tekst**, **Dopasuj mój tekst do
   szablonu** albo **Szablon ▾**.
3. **Generuj muzykę.** Aplikacja sama przełączy modele (Gemma → ACE-Step), jeśli trzeba; przełączenie trwa
   15–60 s. Jeśli model akurat generuje, przełączenie się nie uda — spróbuj za chwilę.
4. **Zapisz…** (jeden utwór) albo zaznacz kilka i **Zapisz wszystkie**. Utwory nie zapisują się same:
   historia znika po zamknięciu okna.

Dodatkowe pokrętła: **BPM** (puste = tempo gatunku), **Kroki** dyfuzji 4–50 (więcej = dokładniej, wolniej;
domyślnie 8), **Seed** (`-1` = losowo; ten sam seed i opis dają ten sam utwór), **Wyciszenie na końcu**.

### Panel Modele (⚙)

Załadowany profil, zajętość karty (VRAM), przyciski **Załaduj/Przeładuj** dla profili `gemma` i `muzyka`,
**Wyłącz model** (zwalnia kartę, Kobold czeka w tle) i lista plików modeli. Zwykle nic tu nie trzeba klikać —
„Generuj” ładuje potrzebny profil samo.

### Okienko podglądu (📊)

Małe okno zawsze na wierzchu z odczytami komputera, żeby nie zaglądać do Menedżera zadań: **GPU** (użycie,
temperatura, VRAM, pobór mocy, zegar, wentylatory), **CPU** (użycie, temperatura), **RAM**, **wentylatory**
z płyty (obr./min). Użycie CPU i RAM idą z WinAPI, GPU z `nvidia-smi`. Temperatura CPU i wentylatory płyty
wymagają **HWiNFO** z włączoną opcją „Obsługa pamięci współdzielonej” (Ustawienia → Ogólne; wersja darmowa
wyłącza ją po 12 godzinach — wtedy uruchom HWiNFO od nowa). Bez HWiNFO te pola pokazują „—”.

## Struktura katalogów

```
app\      songgen.py (serwer HTTP + okno), lyrics.py, music.py, ui\ (index.html, monitor.html, ikony)
serwer\   engine.py (KoboldCpp: start, przełączanie profilu, stan), models.py (katalog GGUF, VRAM, argumenty),
          sysmon.py (odczyty GPU/CPU/RAM), serwer.json (profile), koboldcpp.exe (poza gitem)
modele\   pliki .gguf (poza gitem)
```

Szczegóły silnika, profili i wskaźników: `serwer\README.md`. Plan i decyzje z początku projektu: `PLAN.md`.

## Autor i licencja

Autor: **Tomasz Masłowski** (toevi / tmfgroup). Kod na licencji **MIT** (`LICENSE`), otwarty dla wszystkich:
możesz go używać, zmieniać i rozpowszechniać. Składniki zewnętrzne (KoboldCpp — AGPL-3.0, pywebview, HWiNFO) nie
są częścią repo i mają własne licencje: `THIRD_PARTY_LICENSES.md`.

## Licencje modeli

Gemma 4 12B — Apache 2.0, ACE-Step 1.5 — MIT (użycie komercyjne dozwolone). Utwory powstają z pomocą AI; przy
publikacji (np. na YouTube) zaznacz, że treść została wygenerowana z pomocą AI, i nie proś o naśladowanie
konkretnego wykonawcy.

## Historia błędów i poprawek

Dokumentacja produkcyjna: co się psuło, jak naprawiono i co odrzucono.

| Data | Problem | Rozwiązanie |
|---|---|---|
| 2026-11-19 | Wskaźnik ładowania pokazywał tylko stan „załadowany”, bez postępu. | Pasek i kółko w nagłówku oraz pasek w panelu Modele. KoboldCpp nie podaje procentu, więc to **szacunek**: czas / zmierzony czas poprzedniego ładowania profilu (`serwer\czasy_ladowania.json`; domyślnie 40 s), do 90% liniowo, potem zwalnia do 99%. **Odrzucone:** parsowanie wyjścia Kobolda — startuje z `--quiet` i ukrytym oknem, a format logu nie jest stabilny między wersjami. |
| 2026-11-19 | Brak podglądu temperatur i obciążenia — trzeba było zaglądać do Menedżera zadań. | Okienko 📊 (`sysmon.py`, `monitor.html`). **Odrzucone:** `psutil` (zbędna zależność), LibreHardwareMonitor przez pythonnet (wymaga admina i własnego sterownika). Temperatury CPU Windows nie daje bez sterownika czujników (WMI puste na Ryzen 7 5700X), stąd HWiNFO. |
| 2026-11-19 | Odczyt HWiNFO: zły numer typu czujnika (TEMP=2 zamiast 1). | Poprawione: w strukturze HWiNFO `TEMP=1`, `FAN=3`. |
| 2026-11-19 | Okienko podglądu okazało się za małe — dolne odczyty ucięte. | Okno 320×520, treść z przewijaniem. |
| 2026-11-19 | Po zamknięciu głównego okna proces zostawał z samym oknem podglądu, trzymał port 8765, a następny start otwierał aplikację w przeglądarce. | Zamknięcie głównego okna zamyka resztę; watchdog kończy proces po 6 s, jeśli okna nie zamkną się same. |
| 2026-11-19 | Drugie uruchomienie przy działającej aplikacji otwierało zbędny drugi widok w przeglądarce. | Instancja zgłasza `native` w `/api/status`; drugi start wynosi istniejące okno na wierzch, a przeglądarkę otwiera tylko wtedy, gdy działająca instancja sama jest widokiem w przeglądarce. |
| 2026-11-19 | Okno zapisu pywebview (wybieracz folderu) otwierało się, ale nic nie zapisywało. | „Zapisz wszystkie” używa zwykłego okna zapisu dla pierwszego pliku, a jego folder dla reszty. |

## Otwarte

- Pierwsza wersja pomocy w aplikacji — na razie jedyną dokumentacją jest ten plik.
- Paczka (PyInstaller) — dopiero po stabilnym działaniu.
