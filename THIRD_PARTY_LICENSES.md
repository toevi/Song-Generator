# Third-party components / Składniki zewnętrzne

Song Generator's own code is MIT-licensed (see `LICENSE`). It does **not** ship the components below; it uses
them after you download them yourself (`serwer\README.md`, `modele\README.md`). Each keeps its own licence.
Kod Song Generator jest na licencji MIT (`LICENSE`). Poniższych składników repo **nie zawiera** — pobierasz je sam
i każdy zachowuje własną licencję.

| Component | Used for | Licence | Source |
|---|---|---|---|
| KoboldCpp (`koboldcpp.exe`, v1.124.2) | model server, CUDA | AGPL-3.0 | https://github.com/LostRuins/koboldcpp |
| Gemma 4 12B (GGUF) | lyrics | Apache 2.0 (check the terms of the file you download) | https://ai.google.dev/gemma |
| ACE-Step 1.5 (GGUF) | music | MIT | https://github.com/ace-step/ACE-Step |
| pywebview (optional) | native window | BSD-3-Clause | https://github.com/r0x0r/pywebview |
| HWiNFO (optional, not bundled) | CPU temperature and motherboard fans in the 📊 window | free for personal use; shared-memory interface per its own terms | https://www.hwinfo.com |

KoboldCpp is run as a separate process and talked to over HTTP; it is not linked into or distributed with this code.
