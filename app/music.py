"""Generator muzyki: ACE-Step 1.5 przez KoboldCpp (profil `muzyka`).

Dwa wywołania, jak własny interfejs muzyczny Kobolda: /prepare (LM planuje utwór) i /generate (render).
"""
import uuid

import engine as E
from lyrics import VOCAL_LANGS

MUSIC_MAX_S = 300  # YouTube backing tracks: 3 min at first, user 17.11 asked for 4 and 5 min too

KEYS = {f"{n} {k}" for n in "ABCDEFG" for k in ("Major", "Minor")}
METERS = {"4/4", "3/4", "6/8"}


# Voice choice -> (words at the start of the caption, what the planner must avoid). Tested 19.11: with
# rewrite_caption the planner shortened the caption and turned "male vocals" into "female lead vocal".
VOICES = {
    "female vocals": ("female vocals, sung by a woman, female lead singer", "male vocals, male singer"),
    "male vocals": ("male vocals, sung by a man, male lead singer", "female vocals, female singer"),
    "child vocals, young voice": ("child vocals, sung by a child, young high voice", "adult male vocals, deep voice"),
    "male and female duet vocals": ("male and female duet vocals, a man and a woman sing together", "solo vocalist"),
    "choir vocals": ("choir vocals, many voices singing together", "solo vocalist"),
    # Owner 19.11: "only music and backing calls" - a structure template with shouts like (Hey!) / (Let's go!).
    "backing calls": ("instrumental music with group chants and shouted backing vocals only, no lead vocal",
                      "lead vocal, lead singer, sung verses"),
}


def generate_music(req):
    """Instrumental backing track through ACE-Step 1.5 in KoboldCpp. Returns (audio bytes, content type, plan).

    Two calls, as KoboldCpp's own Music UI does: /prepare lets the music LM plan the piece (rewrites the
    description into its caption, fills BPM/key/metre, writes the audio codes), /generate renders it.
    """
    if not E.capabilities()["music"]:
        raise ValueError("Załadowany profil nie ma modelu muzyki - załaduj profil z ACE-Step.")
    caption = str(req.get("prompt") or "").strip()[:1000]
    if not caption:
        raise ValueError("Opisz nastrój i gatunek podkładu.")

    def num(key, lo, hi, default, cast=int):
        try:
            return min(hi, max(lo, cast(req.get(key, default))))
        except (TypeError, ValueError):
            return default
    lyrics = str(req.get("lyrics") or "").strip()[:4000]
    lang = str(req.get("vocal_language") or "")
    vocal = bool(lyrics) and lang in VOCAL_LANGS
    lyrics = lyrics if vocal else "[Instrumental]"
    body = {"caption": caption, "lyrics": lyrics, "vocal_language": lang if vocal else "unknown",
            "duration": num("duration", 10, MUSIC_MAX_S, 120), "seed": num("seed", -1, 2**31 - 1, -1),
            "inference_steps": num("steps", 4, 50, 8), "guidance_scale": 1.0, "musicfamily": "acestep",
            "stereo": True, "use_mp3": req.get("format") != "wav", "rewrite_caption": True, "gen_codes": True}
    if body["seed"] < 0:
        body["seed"] = int.from_bytes(uuid.uuid4().bytes[:4], "big") >> 1
    voice = VOICES.get(str(req.get("voice") or "")) if vocal else None
    if voice:  # keep our caption word for word, voice first, the other voice as the planner's negative
        body.update(caption=f"{voice[0]}, {caption}", rewrite_caption=False, lm_negative_prompt=voice[1])
    if req.get("bpm"):
        body["bpm"] = num("bpm", 40, 220, 100)
    key, meter = str(req.get("keyscale") or "").strip(), str(req.get("timesignature") or "").strip()
    if key in KEYS:
        body["keyscale"] = key
    if meter in METERS:
        body["timesignature"] = meter
    # Advanced ACE-Step knobs (empty = the model's default): the user's value is sent as typed, within sane limits.
    for k, lo, hi in (("guidance_scale", 0, 15), ("shift", 1, 5), ("lm_temperature", 0, 2), ("lm_cfg_scale", 1, 5)):
        if str(req.get(k) or "").strip():
            body[k] = num(k, lo, hi, 0, float)
    timeout = E.config().get("timeout_s", 600)
    plan = E.call("/api/extra/music/prepare", body, timeout=timeout)
    if not isinstance(plan, dict) or plan.get("error") or not str(plan.get("audio_codes") or "").strip():
        raise ValueError("Model muzyki nie ułożył planu utworu: " + str((plan or {}).get("error") or "pusty wynik"))
    # The planner may rewrite the caption and pick tempo/key; length, lyrics and language stay ours.
    final = {**body, **plan, "lyrics": lyrics, "vocal_language": body["vocal_language"], "duration": body["duration"],
             **({"caption": body["caption"]} if voice else {}),
             "gen_codes": False, "rewrite_caption": False}
    if "bpm" in body:  # tempo of the chosen style or typed by the user wins over the planner's pick
        final["bpm"] = body["bpm"]
    for k in ("keyscale", "timesignature", "guidance_scale", "shift"):  # the user's choice wins over the planner's pick
        if k in body:
            final[k] = body[k]
    audio, ctype = E.raw("/api/extra/music/generate", final, timeout)
    if len(audio) < 1000:  # KoboldCpp answers with an empty body when rendering failed inside
        raise ValueError("Kobold nie zwrócił dźwięku (błąd w trakcie generowania - spróbuj krótszego utworu).")
    info = {k: final.get(k) for k in ("caption", "bpm", "keyscale", "timesignature", "duration", "seed")}
    return audio, ctype, info
