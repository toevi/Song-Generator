# Song Generator — założenia projektu

Decyzje projektowe i przepływ pracy. Opis użytkowy: `README.md`; silnik: `serwer\README.md`.

## Decyzje

| Pytanie | Decyzja | Powód |
|---|---|---|
| Język | **Python 3, tylko biblioteka standardowa** (+ opcjonalnie `pywebview`) | Backend to cienka warstwa: HTTP do KoboldCpp, zarządzanie procesem, nagłówki GGUF. Zero zależności do instalowania. |
| Silnik | **koboldcpp.exe** (CUDA) bez zmian | ACE-Step 1.5 i `--musiclowvram` działają tylko tam; endpointy `/api/extra/music/prepare` i `/generate`. |
| UI | **HTML/JS w oknie pywebview**, serwer lokalny 127.0.0.1 | Zero zależności frontendowych; okno natywne i zapis plików przez dialog systemowy. |
| Modele | Dwa profile: `gemma` (tekst) i `muzyka` (ACE-Step), w `serwer\serwer.json` | Sprawdzone na RTX 4070 12 GB. |
| Pliki modeli | W `modele\`, poza gitem (≈ 19 GB) | Za duże do repo; `models.py` waliduje ścieżki i rozmiary. |

## Model: dwa profile, przełączane

Gemma 12B (Q5) i ACE-Step razem nie mieszczą się w 12 GB VRAM, więc **zawsze działa jeden profil**. Zmiana profilu
to podmiana konfiguracji w działającym KoboldCpp przez admin API (15–60 s).

Przepływ „Generuj muzykę”:
1. profil `gemma`: tekst piosenki, dopasowanie własnego tekstu do szablonu, tytuł;
2. przełączenie na `muzyka` (`--musiclowvram`: cztery modele ACE kolejno na karcie);
3. `prepare` (LM planuje utwór), potem `generate` (render MP3/WAV, do 5 minut);
4. dla kolejnych tekstów powrót na `gemma`.

Przełączanie jest widoczne w nagłówku (który profil działa, postęp ładowania, szacunek VRAM) i automatyczne, gdy
akcja wymaga drugiego profilu.

## Układ interfejsu

Ustawienia (gatunek, skład, wokal, język, długość, BPM, kroki, format, seed) w pasku u góry, pod nim dwie kolumny:
po lewej tytuł, opis stylu i tekst piosenki, po prawej odtwarzacz i lista utworów. Widoki: muzyka (domyślny),
modele (⚙), pomoc (?). Wąski ekran zawija pasek, a kolumny układają się jedna pod drugą.

## Otwarte

- Pobieranie brakujących modeli z poziomu aplikacji.
- Pakiet instalacyjny (PyInstaller) — po ustabilizowaniu.
