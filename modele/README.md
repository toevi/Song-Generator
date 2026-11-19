# modele

Pliki modeli (`.gguf`), poza gitem. Potrzebne (≈ 19 GB, sprawdzone na RTX 4070 12 GB):

| Profil | Plik | Rozmiar (B) | Licencja |
|---|---|---|---|
| gemma | `gemma-4-12b-it-UD-Q5_K_XL.gguf` | 8 606 021 440 | Apache 2.0 |
| muzyka | `acestep-5Hz-lm-4B-Q8_0.gguf` | 4 457 323 648 | MIT |
| muzyka | `Ace-Qwen3-Embedding-0.6B-BF16.gguf` | 1 196 890 592 | MIT |
| muzyka | `acestep-v15-sftturbo50-BF16.gguf` | 4 791 642 016 | MIT |
| muzyka | `ace-vae-BF16.gguf` | 337 420 928 | MIT |

Gdzie szukać: strona modelu Gemma — https://ai.google.dev/gemma, projekt ACE-Step — https://github.com/ace-step/ACE-Step
(pliki w formacie GGUF, np. na Hugging Face). Plik o innym rozmiarze niż w tabeli to inna wersja niż testowana.
Ścieżki w `serwer\serwer.json` są względne do katalogu głównego projektu.
