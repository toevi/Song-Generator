# Song Generator — plan

Wycinek z Little Mate (`E:\HARNESS\Harness App`): zostaje **obsługa modeli** i **generator muzyki**. Reszta (rozmowa, narzędzia, poczta, grafika, wideo, zadania) odpada.
Stan wyjściowy: Little Mate, commit `4f589e8` (2026-11-19).

## Decyzje

| Pytanie | Decyzja | Powód |
|---|---|---|
| Język | **Python 3, tylko biblioteka standardowa** (+ opcjonalnie `pywebview`) | Backend to cienka warstwa: HTTP do KoboldCpp, zarządzanie procesem, nagłówki GGUF. Kod już działa i jest przetestowany; przepisanie na C# nic nie daje. |
| Silnik | **koboldcpp.exe** (CUDA) bez zmian | ACE-Step 1.5 i `--musiclowvram` działają tylko tam; endpointy `/api/extra/music/prepare` + `/generate`. |
| UI | **HTML/JS w oknie pywebview** (jak teraz), serwer lokalny 127.0.0.1 | Zero zależności frontendowych, ten sam wygląd i zachowanie; okno natywne + zapis plików przez dialog systemowy już jest. |
| Modele | **Bez zmian schematu**: `config.json → llm_autostart.models`, dwa profile `gemma` i `muzyka` | Sprawdzone na RTX 4070 12 GB. Nie ruszamy flag ani plików. |
| Pliki modeli | Zostają w `E:\HARNESS` (≈ 20 GB potrzebne: Gemma 8,6 + mmproj 0,17 + ACE-Step 4 pliki ≈ 11,9), ścieżki w configu | Za duże do kopiowania; `models.py` waliduje, że plik leży w folderze modeli. |

## Model: dwa profile, przełączane

Gemma 12B (Q5) i ACE-Step razem nie mieszczą się w 12 GB VRAM → **zawsze jeden naraz**. KoboldCpp ładuje jeden profil; zmiana = zatrzymanie i start z innym zestawem argumentów (~20 s z podmiany).

Przepływ „Generuj wszystko”:
1. profil `gemma` → tekst piosenki / dopasowanie własnego tekstu do szablonu / tytuł,
2. przełączenie na `muzyka` (`--musiclowvram`: 4 modele ACE kolejno na karcie),
3. `prepare` (LM planuje utwór) → `generate` (render, mp3/wav, do 5 min),
4. dla kolejnych tekstów wracamy na `gemma`.

Przełączanie ma być widoczne w górnym pasku (który profil działa, „ładuję…”, szacunek VRAM) i automatyczne, gdy akcja wymaga drugiego profilu (jak `ensure` w Little Mate, `littlemate.py` ~1412–1439).

## Co przenosimy

| Z Little Mate | Do Song Generator |
|---|---|
| `models.py` | całość bez zmian w logice (skan GGUF, VRAM, `args_of`, `validate`); można wyciąć gałęzie `sd*`/wideo |
| `generate_music`, `VOICES`, `MUSIC_MAX_S`, `_llm_call`, `_llm_raw` | serwer muzyki |
| tekst: Gemma pisze / dopasowuje tekst do szablonu, tytuł, szablony części i znaczniki | moduł `lyrics` |
| start/stop/zamiana KoboldCpp (`start_llm`, `choose_profile`, `current_model`, kolejka zajętości) | moduł `engine` |
| zakładka Muzyka, lista utworów, odtwarzacz, zapis przez dialog | UI |
| panel Modele (⚙) | UI, uproszczony do dwóch profili |
| `i18n.js` (PL/EN/IT) | zostaje, tylko używane klucze |

## Co odrzucamy

Rozmowa i narzędzia plików, poczta (`mail.py`), `tools.py`, `tasks.json`, grafika (FLUX), wideo (`video.py`, Wan), Whisper/mowa, profil `coder`, tryb CLI-menu, zakładki inne niż muzyka. Gemma bez zdjęć → `mmproj` do rozważenia po pierwszym działającym buildzie (oszczędza 0,17 GB, ale na razie zostaje, bo zestaw jest sprawdzony).

## UI: układ

Dziś: trzy kolumny (ustawienia | tekst na całą wysokość | odtwarzacz + utwory), a w górnym menu wolne miejsce.
Propozycja: **ustawienia idą do paska u góry**, żeby nie chować ich między oknami edycji.

```
[Song Generator] [profil: gemma ● / muzyka ○  VRAM 9,4/12 GB] [⚙]
[Gatunek ▾] [Głos ▾] [Język ▾] [Długość] [BPM] [Kroki] [Format] [Seed]   [Generuj wszystko]
+-------------------------------+--------------------------------------+
| Opis stylu                    | Odtwarzacz                           |
| Tekst piosenki (szablon,      | Lista utworów (zapis, usuń, nazwa)   |
| znaczniki, Gemma / dopasuj)   |                                      |
+-------------------------------+--------------------------------------+
```

Wąski ekran: pasek zawija się w dwa rzędy, kolumny w jedną.

## Struktura katalogu

```
C:\APLIKACJE\Song Generator\
  songgen.py        # serwer HTTP + start okna
  engine.py         # KoboldCpp: start/stop/przełączenie profilu, stan
  music.py          # prepare + generate, VOICES
  lyrics.py         # prompty do Gemmy
  models.py         # z Little Mate
  config.json       # llm_autostart.models: gemma, muzyka (ścieżki do E:\HARNESS)
  ui\               # index.html, i18n.js, icon
  start.cmd
  README.md         # dokumentacja produkcyjna: błędy, poprawki, odrzucone podejścia
```

## Kroki

1. Git init, skopiować `models.py`, `ui/`, `config.json` (tylko profile `gemma` i `muzyka`), `start.cmd`.
2. Wyciąć z `littlemate.py` ścieżkę muzyki + silnik + szablony tekstu do `songgen.py/engine.py/music.py/lyrics.py`; usunąć nieużywane importy.
3. Uruchomić: start `gemma` → tekst → przełączenie na `muzyka` → utwór 60 s. Zmierzyć czasy przełączenia.
4. Przebudować UI na pasek ustawień u góry; zostawić panel Modele.
5. Test pełny: utwór 5 min, powrót na Gemmę, awaria Kobolda w trakcie, zajęty serwer.
6. README + opcjonalnie paczka (PyInstaller) — dopiero po stabilnym działaniu.

## Otwarte (do decyzji później, nie blokują startu)

- Czy przenosić trzy języki UI (PL/EN/IT), czy zacząć od PL.
- Czy wyciąć `mmproj` i Whisper z profilu Gemmy.
- Czy aplikacja ma sama pilnować pobierania brakujących modeli (`MODELE.md` ma linki i rozmiary).
