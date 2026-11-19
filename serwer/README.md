# serwer

Silnik modeli. `engine.py` uruchamia `koboldcpp.exe` (CUDA, 1.124.2, poza gitem), przełącza profile
`gemma` <-> `muzyka` przez admin API i wyładowuje model z karty. Profile i ustawienia: `serwer.json`.
`models.py` — katalog plików GGUF, szacunek VRAM, argumenty Kobolda. `admin\` — kcpps eksportowane przy
przełączaniu (odtwarzane za każdym razem).
Źródło silnika: https://github.com/LostRuins/koboldcpp/releases/download/v1.124.2/koboldcpp.exe
(622 841 516 B). Gemma i ACE-Step nie mieszczą się razem w 12 GB — zawsze działa jeden profil.

## Wskaźnik ładowania profilu

KoboldCpp nie podaje procentu wczytywania modelu, więc pasek w UI (nagłówek i panel Modele) to **szacunek**:
upłynięty czas / czas poprzedniego ładowania tego profilu (`czasy_ladowania.json`, mierzy i zapisuje
`engine.start_apply` po udanym ładowaniu; poza gitem). Bez pomiaru: 40 s. Do 90% rośnie liniowo, dalej
zwalnia do maks. 99%, więc długie ładowanie nie wygląda na zawieszone (status dopisuje „dłużej niż zwykle”).
`engine.apply_state()` dodaje `elapsed` do `APPLY` dla `/api/status` i `/api/apply`.
Podejście odrzucone: parsowanie wyjścia Kobolda — startuje z `--quiet` i ukrytym oknem, a format logu
nie jest stabilny między wersjami.

## Okienko podglądu (📊 w nagłówku)

`sysmon.py` + `app/ui/monitor.html` (trasy `/monitor`, `/api/sys`): małe okno „zawsze na wierzchu” z GPU
(użycie, temperatura, VRAM, pobór, zegar — `nvidia-smi`), CPU (użycie — `GetSystemTimes`), RAM
(`GlobalMemoryStatusEx`); odświeżanie co 1,5 s, odczyt cache'owany 1 s. Bez zależności (psutil nie jest
zainstalowany). **Temperatura CPU:** Windows nie daje jej bez sterownika czujników (WMI/`Thermal Zone`
puste na Ryzen 7 5700X), więc jest czytana z pamięci współdzielonej HWiNFO (`Global\HWiNFO_SENS_SM2`) —
wymaga uruchomionego HWiNFO z włączonym „Shared Memory Support”; bez tego pole pokazuje „—” i podpowiedź.
Okienko zamyka się razem z głównym oknem (inaczej `webview.start` nie wróciłoby). Podejście odrzucone:
LibreHardwareMonitor przez pythonnet — wymaga admina i własnego sterownika, za ciężkie.

**Wentylatory:** GPU — `fan.speed` z `nvidia-smi` (% obrotów; 0% na jałowym to normalne, RTX 4070 zatrzymuje wentylatory
poniżej progu temperatury). CPU/obudowa — odczyty typu FAN (obroty/min) z HWiNFO, lista budowana dynamicznie.
Uwaga z pisania: w strukturze HWiNFO typ czujnika to TEMP=1, FAN=3 (pierwsza wersja miała błędnie TEMP=2).
