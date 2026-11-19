# serwer

Silnik modeli. `engine.py` uruchamia `koboldcpp.exe` (CUDA, 1.124.2, poza gitem), przełącza profile
`gemma` <-> `muzyka` przez admin API i wyładowuje model z karty. Profile i ustawienia: `serwer.json`.
`models.py` — katalog plików GGUF, szacunek VRAM, argumenty Kobolda. `admin\` — kcpps eksportowane przy
przełączaniu (odtwarzane za każdym razem).
Źródło silnika: https://github.com/LostRuins/koboldcpp/releases/download/v1.124.2/koboldcpp.exe
(622 841 516 B). Gemma i ACE-Step nie mieszczą się razem w 12 GB — zawsze działa jeden profil.
