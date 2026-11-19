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
| Vocals / Wokal | **choir** / **chór** (see the note below / patrz uwaga niżej) |
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

**Vocals note / Uwaga o wokalu.** The screenshot was made with *music + choir shouts* (`backing calls`). That mode tells the
model "no lead vocal", so it mostly shouts the bracketed lines `( )` and skips the plain ones. To have the plain lines
sung too, choose **choir** (or a duet) in the Vocals field. Sections tagged `Instrumental` / `Solo` / `Break` should have
no text under them — the app warns about that before generating.
Zrzut powstał w trybie *tylko muzyka + okrzyki*. Ten tryb mówi modelowi „bez głównego wokalu”, więc głównie krzyczy wersy
w nawiasach `( )`, a zwykłe pomija. Żeby śpiewał też zwykłe wersy, wybierz **chór** (albo duet) w polu Wokal. Sekcje
oznaczone `Instrumental` / `Solo` / `Break` nie powinny mieć tekstu pod spodem — aplikacja ostrzega o tym przed generowaniem.

**Listen / Posłuchaj:** [`blask-nocy-5.mp3`](blask-nocy-5.mp3) — take no. 5, made from the lyrics in [`disco-claps.txt`](disco-claps.txt) (3 min, 4.1 MB). The result varies a lot from take to take (seed, steps, how the model reads the tags), so do not expect an identical track; the sample only shows what the model can produce. Generated with the help of AI (ACE-Step 1.5).
**Posłuchaj:** [`blask-nocy-5.mp3`](blask-nocy-5.mp3) — podejście nr 5, z tekstu [`disco-claps.txt`](disco-claps.txt) (3 min, 4,1 MB). Wynik bardzo się różni między podejściami (seed, kroki, sposób odczytania znaczników), więc nie licz na identyczny utwór; próbka pokazuje tylko, co model potrafi. Utwór wygenerowany z pomocą AI (ACE-Step 1.5).

How to use / Jak użyć: pick the settings above (Vocals: choir), paste `disco-chants.txt` into the lyrics field, click
**Generate music** / ustaw powyższe (Wokal: chór), wklej `disco-chants.txt` w pole tekstu, kliknij **Generuj muzykę**.
Note: in the "music + choir shouts" mode Gemma does not write lyrics — you enter them yourself
(see the in-app help) / w trybie „tylko muzyka + okrzyki” Gemma nie pisze tekstu — wpisujesz go sam.

## Disco with claps (experimental) / Disco z klaskaniem (eksperyment)

A longer variant of the same song: [`disco-claps.txt`](disco-claps.txt) (the lyrics of the sample track above) adds a bridge with a solo section and tries
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

## Same song in three rock genres / Ten sam utwór w trzech gatunkach rocka

The lyrics in [`rock-claps.txt`](rock-claps.txt) (guitar and bass solos, a male-vocal-and-male-choir duet answer after each
chorus, claps in the bridge) rendered in three genres. Only the **Genre** field changed; the text is the same.
Tekst [`rock-claps.txt`](rock-claps.txt) (solówki gitary i basu, „duet” męski głos + męski chór po każdym refrenie,
klaski w bridge'u) wygenerowany w trzech gatunkach. Zmieniało się tylko pole **Gatunek**; tekst jest ten sam.

| Genre / Gatunek | Sample / Próbka | Size / Rozmiar |
|---|---|---|
| Soft rock | [`blask-nocy-soft-rock.mp3`](blask-nocy-soft-rock.mp3) | 4.1 MB |
| Hard rock | [`blask-nocy-hard-rock.mp3`](blask-nocy-hard-rock.mp3) | 4.1 MB |
| Metal (style description: `metal lata 90`) | [`blask-nocy-metal.mp3`](blask-nocy-metal.mp3) | 4.1 MB |

The same caveat applies: every take comes out differently, and the model reads the tags loosely.
Obowiązuje ta sama uwaga: każde podejście wychodzi inaczej, a model czyta znaczniki swobodnie.

**The style description helps / Opis stylu pomaga.** Without a Style description the model tends to make a weaker, more generic
track, and in the first metal take the vocals did not come through. A retest with the field empty (same lyrics and settings)
did sing, only later in the track, so the description is **not** what decides whether vocals appear: the model decides that
loosely, and results vary from take to take. A few words of style are still worth adding because they steer the sound.
Bez opisu stylu model robi zwykle słabszy, bardziej ogólny utwór, a w pierwszym metalu wokal się nie pojawił. Powtórka z pustym
polem (ten sam tekst i ustawienia) jednak zaśpiewała, tylko później w utworze, więc opis **nie** decyduje o tym, czy będzie
wokal: model robi to swobodnie, a wyniki różnią się między podejściami. Kilka słów stylu warto dopisać, bo kierują brzmieniem.
