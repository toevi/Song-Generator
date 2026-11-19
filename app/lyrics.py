"""Teksty piosenek: Gemma pisze wersy do szablonu, dopasowuje tekst użytkownika do szablonu.

Przeniesione z Little Mate (write_lyrics, fit_lyrics, fill_skeleton) bez zmian w logice.
Model tekstowy to profil `gemma` w serwerze; ta warstwa tylko woła /v1/chat/completions.
"""
import json
import re
import urllib.error
import urllib.request

import engine as E


class LLMError(Exception):
    pass


def complete(messages, max_tokens=1200):
    """Jedno wywołanie bez strumieniowania; zwraca wiadomość asystenta (dict)."""
    cfg = E.config()
    body = {"model": "local", "messages": messages, "temperature": 0.1, "max_tokens": max_tokens}
    req = urllib.request.Request(E.url() + "/v1/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with E.LOCK:
        try:
            with urllib.request.urlopen(req, timeout=cfg.get("timeout_s", 600)) as resp:
                return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]
        except (urllib.error.URLError, OSError) as e:
            raise LLMError(f"Brak połączenia z modelem ({E.url()}): {e}") from e


VOCAL_LANGS = {"pl": "polski", "en": "angielski", "it": "włoski", "de": "niemiecki", "es": "hiszpański",
               "fr": "francuski"}


def _sections(text):
    """[(tag line, [lines])] - the text before the first tag goes under ''."""
    out = [["", []]]
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            out.append([s, []])
        elif s:
            out[-1][1].append(s)
    return out


def fill_skeleton(skeleton, written):
    """Put the model's lines into the '...' places of the skeleton; tags, calls and the user's lines stay.

    Lines are matched section by section; when the model changed the sections, its sung lines go in order.
    """
    sk, wr = _sections(skeleton), _sections(written)
    same = [t for t, _ in sk] == [t for t, _ in wr]
    given = {l for _, ls in sk for l in ls}  # the user's own lines and calls: never taken from the model again
    pool = [l for _, ls in wr for l in ls
            if not l.startswith("(") and l != "..." and l not in given and not l.endswith(":")]
    out = []
    for k, (tag, lines) in enumerate(sk):
        mine = [l for l in wr[k][1] if not l.startswith("(")] if same else []
        new, m = [], 0
        for line in lines:
            if line == "...":
                got = mine[m] if m < len(mine) else (pool.pop(0) if not same and pool else "...")
                m += 1
                new.append(got)
            else:
                if same and not line.startswith("("):
                    m += 1  # the model's copy of a line the user wrote: skip it
                new.append(line)
        if tag or new:
            out.append("\n".join(([tag] if tag else []) + new))
    return "\n\n".join(out) + "\n"


def write_lyrics(theme, language, seconds, skeleton=""):
    """Song lyrics for ACE-Step, written by the text model (the music profile has no text model of its own).

    With a skeleton (section tags + '...' lines) the model writes only the '...' lines; tags, backing calls
    and lines the user already wrote stay exactly as they are.
    """
    theme = (theme or "").strip()[:1000]
    lang = VOCAL_LANGS.get(language, "angielski")
    st = E.status()
    if st["online"] and not st.get("llm", True):
        raise ValueError("Załadowany profil nie ma modelu tekstowego - załaduj np. profil gemma.")
    skeleton = (skeleton or "").strip()[:6000]
    if "..." not in skeleton:
        raise ValueError("Brak szablonu do wypełnienia.")
    msgs = [{"role": "system", "content":
             "Piszesz teksty piosenek do śpiewania przez syntezator muzyki. Dostajesz szablon: znaczniki części "
             "w nawiasach kwadratowych i linie „...”. Każdą linię „...” zastępujesz jednym śpiewnym wersem "
             "(4–8 słów), z rymami; refreny mają ten sam tekst za każdym razem. Znaczniki, wstawki w nawiasach "
             "okrągłych i gotowe wersy przepisujesz bez zmian. W pierwszej linii, przed szablonem, piszesz "
             "„Tytuł: …” — krótki tytuł piosenki. Poza tym zwracasz WYŁĄCZNIE cały tekst, bez komentarzy."},
            {"role": "user", "content": f"Język wersów: {lang}.\nTemat i nastrój: {theme or 'dowolny, pogodny'}\n\n"
                                        f"Szablon:\n{skeleton}"}]
    out = (complete(msgs, max_tokens=2000).get("content") or "").strip()
    if not out:
        raise ValueError("Model nie napisał tekstu piosenki - spróbuj jeszcze raz.")
    m = re.search(r"^\W*(?:tytuł|title)\W*:\s*(.+)$", out, re.I | re.M)
    title = m.group(1).strip(" *\"„”'") if m else ""
    if m:
        out = out[:m.start()] + out[m.end():]
    return fill_skeleton(skeleton, out), title[:80]


def _words(text):
    return re.findall(r"[^\W\d_]+", text.lower())


def _unused_lines(raw, text):
    """The user's lines that did not make it into the song (most of their words missing from it)."""
    have = {}
    for w in _words(text):
        have[w] = have.get(w, 0) + 1
    left = []
    for line in raw.splitlines():
        s = line.strip()
        ws = _words(s)
        if not ws or (s.startswith("[") and s.endswith("]")) or (s.endswith(":") and len(ws) <= 3):
            continue  # tags and labels such as "Refren:" are not sung lines
        if sum(1 for w in ws if have.get(w)) / len(ws) < 0.6:
            left.append(s)
        else:
            for w in ws:
                if have.get(w):
                    have[w] -= 1
    return left


def _sung_lines(line):
    """A long sentence as short sung lines: a leading label ("Druga zwrotka:") goes, then commas and stops
    split it, and pieces over 8 words are halved."""
    s = re.sub(r"^\s*[^\W\d_]+(?:\s+[^\W\d_]+){0,2}\s*:\s*", "", line.strip())
    out = []
    for part in re.split(r"(?<=[,.;!?])\s+", s):
        part = part.strip().rstrip(",;")
        words = part.split()
        while len(words) > 8:
            half = (len(words) + 1) // 2
            out.append(" ".join(words[:half]))
            words = words[half:]
        if words:
            out.append(" ".join(words))
    return out


def _add_verse(text, lines):
    """Lines that did not fit go into one more verse, before the final chorus / outro / end."""
    rows = text.rstrip("\n").split("\n")
    verses = [r.strip() for r in rows if r.strip().lower().startswith("[verse")]
    who = verses[-1][1:-1].split(" - ", 1)[1] if verses and " - " in verses[-1] else ""
    tag = f"[Verse {len(verses) + 1}{' - ' + who if who else ''}]"
    at = next((i for i, r in enumerate(rows)
               if re.match(r"\[(final chorus|outro|end)", r.strip().lower())), len(rows))
    block = [tag, *[piece for line in lines for piece in _sung_lines(line)], ""]
    return "\n".join(rows[:at] + block + rows[at:]).rstrip("\n") + "\n"


def fit_lyrics(skeleton, raw, language):
    """The user's own text laid into the '...' places of a template, words kept (only split into lines).

    Returns (lyrics, lines that did not fit and went into an extra verse, share of words not from the user).
    Too little text: the rest of the places stay '...'.
    """
    raw = (raw or "").strip()[:8000]
    skeleton = (skeleton or "").strip()[:6000]
    if not raw:
        raise ValueError("Wklej najpierw swój tekst.")
    if "..." not in skeleton:
        raise ValueError("Szablon nie ma pustych miejsc (linii „...”).")
    st = E.status()
    if st["online"] and not st.get("llm", True):
        raise ValueError("Załadowany profil nie ma modelu tekstowego - załaduj np. profil gemma.")
    lang = VOCAL_LANGS.get(language, "polski")
    msgs = [{"role": "system", "content":
             "Układasz gotowy tekst piosenki użytkownika w szablon dla syntezatora muzyki. Szablon ma znaczniki "
             "części w nawiasach kwadratowych i linie „...”. Każdą linię „...” zastępujesz jednym wersem Z TEKSTU "
             "UŻYTKOWNIKA. Zasady: używasz wyłącznie słów użytkownika i nie dopisujesz własnych; długie zdania "
             "dzielisz na krótsze, śpiewne wersy w naturalnych miejscach; zwrotki idą w kolejności tekstu; "
             "na refren bierzesz fragment, który użytkownik oznaczył jako refren, a jeśli nie oznaczył — "
             "najbardziej chwytliwy, i każdy refren ma te same wersy; gdy tekstu zabraknie, zostawiasz „...”. "
             "Znaczniki, wstawki w nawiasach okrągłych i gotowe wersy szablonu przepisujesz bez zmian. "
             "Zwracasz WYŁĄCZNIE cały szablon, bez komentarzy."},
            {"role": "user", "content": f"Język tekstu: {lang}.\n\nSzablon:\n{skeleton}\n\nTekst użytkownika:\n{raw}"}]
    out = (complete(msgs, max_tokens=2500).get("content") or "").strip()
    if not out:
        raise ValueError("Model nie dopasował tekstu - spróbuj jeszcze raz.")
    text = fill_skeleton(skeleton, out)
    left = _unused_lines(raw, text)
    if left:
        text = _add_verse(text, left)
    mine = set(_words(raw)) | set(_words(skeleton))
    sung = [w for line in text.splitlines()
            if line.strip() and not line.strip().startswith(("[", "(")) for w in _words(line)]
    foreign = sum(1 for w in sung if w not in mine) / len(sung) if sung else 0.0
    return text, len(left), round(foreign, 2)


def translate(text, language):
    """Opis stylu (polski) na język modelu muzyki; zachowuje podziały linii, nic nie dopisuje."""
    text, language = text.strip(), (language or "").strip() or "angielski"
    if not text:
        raise ValueError("Pusty tekst do tłumaczenia.")
    if len(text) > 20000:
        raise ValueError("Tekst za długi do tłumaczenia (limit 20 000 znaków).")
    st = E.status()
    if st["online"] and not st.get("llm", True):
        raise ValueError("Załadowany profil nie ma modelu tekstowego - załaduj np. profil gemma.")
    msgs = [{"role": "system", "content":
             "Jesteś tłumaczem korespondencji. Tłumaczysz wiernie, zachowujesz ton, formę grzecznościową, "
             "podział na akapity i fragmenty w nawiasach kwadratowych. Zwracasz WYŁĄCZNIE tłumaczenie."},
            {"role": "user", "content": f"Przetłumacz na język: {language}.\n\n{text}"}]
    reply = complete(msgs, max_tokens=min(4000, len(text) // 2 + 600))
    out = (reply.get("content") or "").strip()
    if not out:
        raise ValueError("Model nie zwrócił tłumaczenia.")
    return out
