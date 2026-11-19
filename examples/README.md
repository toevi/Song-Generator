# Examples / Przykłady

## Disco with group chants / Disco z okrzykami chóru

An instrumental disco track whose only "vocals" are chanted shouts and a choir — the lyrics field holds just
the structure tags and the chants. The ready-to-paste text is in [`disco-chants.txt`](disco-chants.txt).
Instrumentalny utwór disco, w którym śpiewają tylko okrzyki i chór — w polu tekstu są same znaczniki struktury
i okrzyki. Gotowy tekst do wklejenia: [`disco-chants.txt`](disco-chants.txt).

![Disco example / Przykład disco](../docs/example-disco.png)

| Setting / Ustawienie | Value / Wartość |
|---|---|
| Genre / Gatunek | Disco |
| Vocals / Wokal | music + choir shouts (`backing calls`) / tylko muzyka + okrzyki chórku |
| Singing language / Język śpiewu | Polish / polski |
| Length / Długość | 3 min |
| Tempo (BPM) | 250 |
| Steps / Kroki | 16 |
| Format | MP3 |
| Seed | -1 (random / losowo) |
| Fade out at the end / Wyciszenie na końcu | on / włączone |
| Title / Tytuł | Blask Nocy |
| Style description / Opis stylu | `wypełnij tylko chorki tekst piosenki disco disco` |

Result / Wynik: 2:58, 4.1 MB; the model reported about 220 BPM, G minor / model podał ok. 220 BPM, tonacja g-moll.

How to use / Jak użyć: pick the settings above, paste `disco-chants.txt` into the lyrics field, click
**Generate music** / ustaw powyższe, wklej `disco-chants.txt` w pole tekstu, kliknij **Generuj muzykę**.
Note: in the "music + choir shouts" mode Gemma does not write lyrics — you enter the shouts yourself
(see the in-app help) / w trybie „tylko muzyka + okrzyki” Gemma nie pisze tekstu — okrzyki wpisujesz sam.

## Disco with claps (experimental) / Disco z klaskaniem (eksperyment)

A longer variant of the same song: [`disco-claps.txt`](disco-claps.txt) adds a bridge with a solo section and tries
to get real hand claps with the sections `[Instrumental - Hand Claps]` and `[Percussion Break - Claps]`.
Dłuższy wariant tego samego utworu: [`disco-claps.txt`](disco-claps.txt) dodaje bridge z częścią solową i próbuje
uzyskać prawdziwe klaskanie sekcjami `[Instrumental - Hand Claps]` i `[Percussion Break - Claps]`.

**Claps are not guaranteed / Klaskanie nie jest gwarantowane.** ACE-Step has no documented tag for sound effects.
The official songwriting guide ([ACE-Step-1.5, `acestep-songwriting`](https://github.com/ace-step/ACE-Step-1.5/blob/main/.claude/skills/acestep-songwriting/SKILL.md))
lists structure tags (`[Intro]`, `[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]`, `[Build]`, `[Drop]`, `[Breakdown]`,
`[Instrumental]`, `[Guitar Solo]`, `[Piano Interlude]`, `[Fade Out]`, `[Silence]`) and says to keep the instruments
in the style description consistent with the instrumental sections in the lyrics. It does not mention claps, so the
two clap sections above are an experiment: add `hand claps, rhythmic clapping` to the **style description** and try
a few seeds. A bracketed `(Clap your hands!)` is a choir shout, not clapping.
Oficjalny przewodnik nie wymienia klaskania, więc obie sekcje to eksperyment: dopisz `hand claps, rhythmic clapping`
do **opisu stylu** i wypróbuj kilka seedów. `(Clap your hands!)` w nawiasie to okrzyk chóru, nie klaskanie.
