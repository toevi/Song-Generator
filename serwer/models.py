"""Katalog plików modeli i profile ładowania dla Song Generator. Tylko biblioteka standardowa.

Profil = jedno załadowanie KoboldCpp: albo model tekstowy (Gemma — teksty piosenek), albo zestaw
muzyczny ACE-Step 1.5 (cztery pliki). Oba naraz nie mieszczą się w 12 GB, więc zawsze działa jeden profil.
Tu: nagłówki GGUF, szacunek VRAM, argumenty Kobolda i walidacja profili.
"""
import re
import shutil
import struct
import subprocess
from pathlib import Path

MODEL_EXTS = (".gguf",)
KV_TYPES = {"f16": 2.0, "q8_0": 1.0625, "q4_0": 0.5625}
REASONING = ("default", "none", "low", "medium", "high")
SAMPLER_KEYS = {"temperature": (0.0, 2.0), "top_p": (0.0, 1.0), "min_p": (0.0, 1.0),
                "top_k": (0, 200), "rep_pen": (1.0, 2.0)}
NAME_RE = re.compile(r"^[a-z0-9_]{1,32}$")
# Typy plików llama.cpp, dla plików, których nazwa nie mówi o kwantyzacji.
FTYPES = {0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_0", 8: "Q5_0", 9: "Q5_1", 10: "Q2_K",
          11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L", 14: "Q4_K_S", 15: "Q4_K_M", 16: "Q5_K_S",
          17: "Q5_K_M", 18: "Q6_K", 19: "IQ2_XXS", 20: "IQ2_XS", 21: "Q2_K_S", 22: "IQ3_XS",
          23: "IQ3_XXS", 24: "IQ1_S", 25: "IQ4_NL", 26: "IQ3_S", 27: "IQ3_M", 28: "IQ2_S",
          29: "IQ2_M", 30: "IQ4_XS", 31: "IQ1_M", 32: "BF16"}
QUANT_RE = re.compile(r"(?:UD-)?(?:I?Q\d_[A-Z0-9_]+|Q\d_\d|BF16|F16|F32)", re.I)
_INFO_CACHE = {}


# ---------------------------------------------------------------- nagłówek GGUF

_SCALAR = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i", 6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
_WANTED = ("general.architecture", "general.name", "general.file_type", "general.size_label", "general.type",
           ".context_length", ".block_count", ".embedding_length", ".attention.head_count",
           ".attention.head_count_kv", ".attention.key_length", ".attention.value_length",
           ".attention.sliding_window", ".attention.sliding_window_pattern", ".attention.key_length_swa",
           ".attention.value_length_swa", ".full_attention_interval")


def _read_gguf(path):
    """Wybrane klucze metadanych pliku GGUF (tylko nagłówek; wielkie tablice, np. słownik, pomijane)."""
    meta = {}
    with open(path, "rb") as f:
        if f.read(4) != b"GGUF":
            return None
        version, = struct.unpack("<I", f.read(4))
        if version < 2:
            return None
        _tensors, kv_count = struct.unpack("<QQ", f.read(16))

        def string():
            n, = struct.unpack("<Q", f.read(8))
            return f.read(n).decode("utf-8", "replace")

        def value(vtype, keep):
            if vtype == 8:
                return string()
            if vtype == 9:
                etype, count = struct.unpack("<IQ", f.read(12))
                if etype == 8 or etype == 9:
                    for _ in range(count):  # pomijamy bez dekodowania (słowniki mają 100k+ wpisów)
                        if etype == 8:
                            n, = struct.unpack("<Q", f.read(8))
                            f.seek(n, 1)
                        else:
                            value(9, False)
                    return None
                size = struct.calcsize(_SCALAR[etype])
                if keep and count <= 4096:
                    return list(struct.unpack("<" + _SCALAR[etype][1] * count, f.read(size * count)))
                f.seek(size * count, 1)
                return None
            fmt = _SCALAR[vtype]
            return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]

        for _ in range(kv_count):
            key = string()
            vtype, = struct.unpack("<I", f.read(4))
            keep = key in _WANTED or any(key.endswith(w) for w in _WANTED if w.startswith("."))
            v = value(vtype, keep)
            if keep:
                meta[key] = v
    return meta


FILE_KEYS = ("model", "musicllm", "musicemb", "musicdit", "musicvae")  # muzyka: ACE-Step 1.5 (KoboldCpp 1.109+)
MUSIC_FLAGS = {"musicllm": "--musicllm", "musicemb": "--musicembeddings", "musicdit": "--musicdiffusion",
               "musicvae": "--musicvae"}


def file_info(path):
    """Rodzaj, rozmiar, architektura i liczby do szacunku VRAM. Pamięć podręczna per (ścieżka, rozmiar, mtime)."""
    p = Path(path)
    st = p.stat()
    key = (str(p), st.st_size, st.st_mtime)
    if key in _INFO_CACHE:
        return _INFO_CACHE[key]
    name = p.name.lower()
    info = {"path": str(p), "name": p.name, "size": st.st_size, "kind": "inne", "arch": "", "quant": ""}
    meta = None
    try:
        meta = _read_gguf(p)
    except (OSError, struct.error, KeyError, UnicodeDecodeError):
        meta = None
    m = QUANT_RE.search(p.stem)
    info["quant"] = m.group(0).upper() if m else ""
    if meta:
        arch = meta.get("general.architecture", "")
        info["arch"] = arch
        if not info["quant"] and meta.get("general.file_type") in FTYPES:
            info["quant"] = FTYPES[meta["general.file_type"]]
        g = lambda k, d=None: meta.get(f"{arch}.{k}", d)  # noqa: E731
        info.update(train_ctx=g("context_length"), layers=g("block_count"), n_embd=g("embedding_length"),
                    heads=g("attention.head_count"), kv_heads=g("attention.head_count_kv"),
                    key_len=g("attention.key_length"), val_len=g("attention.value_length"),
                    swa=g("attention.sliding_window"), swa_pattern=g("attention.sliding_window_pattern"),
                    key_len_swa=g("attention.key_length_swa"), val_len_swa=g("attention.value_length_swa"),
                    full_every=g("full_attention_interval"))
        if "vae" in name:
            info["kind"] = "muzyka: VAE"
        elif "embed" in name:
            info["kind"] = "muzyka: embeddings"
        elif "acestep-v15" in name or "dit" in name:
            info["kind"] = "muzyka: DiT"
        elif "acestep" in name and "lm" in name:
            info["kind"] = "muzyka: LM"
        else:
            info["kind"] = "llm"
    _INFO_CACHE[key] = info
    return info


def scan(dirs):
    """Wszystkie pliki modeli w podanych folderach (i ich bezpośrednich podfolderach)."""
    found = []
    for d in dirs:
        base = Path(d).expanduser()
        if not base.is_dir():
            continue
        candidates = list(base.iterdir())
        for sub in candidates[:]:
            if sub.is_dir() and not sub.name.startswith("."):
                try:
                    candidates += list(sub.iterdir())
                except OSError:
                    pass
        for p in candidates:
            if p.is_file() and p.suffix.lower() in MODEL_EXTS and p.stat().st_size > 1_000_000:
                try:
                    found.append(file_info(p))
                except OSError:
                    pass
    found.sort(key=lambda i: (i["kind"], i["name"].lower()))
    return found


OVERHEAD = 1536 * 2**20  # bufory obliczeniowe; skalibrowane na Gemmie 4 12B przy 32k (~10,8 GB zmierzone)


def estimate_vram(profile):
    """Przybliżone zapotrzebowanie na VRAM w bajtach: wagi + cache KV + bufory. Zwraca (bajty, uwagi)."""
    total, notes = OVERHEAD, []
    for key in FILE_KEYS:
        if key in MUSIC_FLAGS and profile.get("musiclowvram", True):
            continue  # liczone niżej: z --musiclowvram na karcie siedzi tylko największy model muzyczny
        if profile.get(key) and Path(profile[key]).is_file():
            total += Path(profile[key]).stat().st_size
    music = [Path(profile[k]).stat().st_size for k in MUSIC_FLAGS
             if profile.get(k) and Path(profile[k]).is_file()]
    if music and profile.get("musiclowvram", True):
        total += max(music)
        notes.append("muzyka: modele ładowane po kolei (--musiclowvram)")
    if profile.get("model") and Path(profile["model"]).is_file():
        info = file_info(profile["model"])
        ctx = int(profile.get("context") or 4096)
        layers = info.get("layers") or 0
        kv = info.get("kv_heads")
        heads = info.get("heads") if isinstance(info.get("heads"), int) else 0
        key_len = info.get("key_len") or ((info.get("n_embd") or 0) // heads if heads else 128)
        val_len = info.get("val_len") or key_len
        pattern = info.get("swa_pattern") if isinstance(info.get("swa_pattern"), list) else None
        kv_list = kv if isinstance(kv, list) else [kv or 0] * layers
        elems = 0  # elementy KV zsumowane po warstwach i zapamiętanych tokenach
        for i, h in enumerate(kv_list):
            if not h:
                continue
            if info.get("full_every") and (i + 1) % info["full_every"]:
                continue  # modele hybrydowe: warstwy liniowe nie trzymają cache na token
            sliding = info.get("swa") and (pattern[i] if pattern and i < len(pattern) else False)
            if sliding:
                k, v = info.get("key_len_swa") or key_len, info.get("val_len_swa") or val_len
                elems += h * (k + v) * min(ctx, info["swa"])
            else:
                elems += h * (key_len + val_len) * ctx
        total += int(elems * KV_TYPES.get(profile.get("quantkv") or "f16", 2.0))
        if info.get("swa") and not pattern:
            notes.append("okno przesuwne bez wzoru warstw - szacunek z górką")
        if info.get("full_every"):
            notes.append("atencja hybrydowa - mała pamięć kontekstu")
        if info.get("train_ctx") and ctx > info["train_ctx"]:
            notes.append(f"kontekst większy niż model obsługuje ({info['train_ctx']})")
    return total, notes


def gpu():
    """{'name','total','used'} w bajtach z nvidia-smi albo None."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        name, total, used = [x.strip() for x in out.splitlines()[0].split(",")]
        return {"name": name, "total": int(total) * 2**20, "used": int(used) * 2**20}
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------- profile

def profile_of(entry):
    """Profil jako słownik (kopia)."""
    return dict(entry)


def args_of(entry):
    """Argumenty KoboldCpp dla profilu (ścieżki muszą być już bezwzględne)."""
    a = []
    if entry.get("model"):  # profil muzyczny nie ma modelu tekstowego
        a += ["--model", entry["model"], "--contextsize", str(int(entry.get("context") or 4096))]
    if entry.get("gpulayers") not in (None, -1, "-1", ""):
        a += ["--gpulayers", str(int(entry["gpulayers"]))]
    if entry.get("quantkv") and entry["quantkv"] != "f16":
        a += ["--quantkv", entry["quantkv"]]
    if entry.get("jinja"):
        a += ["--jinja"]
    if entry.get("reasoning") and entry["reasoning"] != "default":
        a += ["--reasoningeffort", entry["reasoning"]]
    if entry.get("musicdit"):
        for key, flag in MUSIC_FLAGS.items():
            if entry.get(key):
                a += [flag, entry[key]]
        if entry.get("musiclowvram", True):
            a += ["--musiclowvram"]  # cztery modele muzyki biorą turę na karcie zamiast wszystkie naraz
    return a


def sampler_of(entry):
    return dict(entry.get("sampler") or {})


def validate(name, p, dirs):
    """Czysty słownik profilu z danych z UI albo ValueError z polskim komunikatem.

    Tylko dozwolone pola; każdy plik musi leżeć w folderze modeli, więc panel nigdy nie wskaże Kobolda
    na dowolną ścieżkę. Sam plik wykonywalny nie jest edytowalny z UI.
    """
    if not NAME_RE.match(name or ""):
        raise ValueError("Nazwa profilu: małe litery, cyfry i _, do 32 znaków.")
    roots = [Path(d).expanduser().resolve() for d in dirs]

    def model_file(key):
        v = str(p.get(key) or "").strip()
        if not v:
            return ""
        f = Path(v).expanduser().resolve()
        if not f.is_file() or not any(f.is_relative_to(r) for r in roots):
            raise ValueError(f"Plik spoza folderu modeli albo nie istnieje: {v}")
        return str(f)

    def num(key, lo, hi, cast, default):
        v = p.get(key, default)
        try:
            v = cast(v)
        except (TypeError, ValueError):
            raise ValueError(f"Zła wartość: {key}") from None
        if not lo <= v <= hi:
            raise ValueError(f"{key} poza zakresem {lo}-{hi}")
        return v

    clean = {"model": model_file("model"),
             **{k: model_file(k) for k in MUSIC_FLAGS}, "musiclowvram": bool(p.get("musiclowvram", True)),
             "context": num("context", 512, 262144, int, 8192),
             "gpulayers": num("gpulayers", -1, 999, int, -1),
             "quantkv": p.get("quantkv") if p.get("quantkv") in KV_TYPES else "f16",
             "jinja": bool(p.get("jinja")),
             "reasoning": p.get("reasoning") if p.get("reasoning") in REASONING else "default",
             "note": str(p.get("note") or "")[:200]}
    sampler = {}
    for k, (lo, hi) in SAMPLER_KEYS.items():
        v = (p.get("sampler") or {}).get(k)
        if v in (None, ""):
            continue
        cast = int if k == "top_k" else float
        try:
            v = cast(v)
        except (TypeError, ValueError):
            raise ValueError(f"Zła wartość: {k}") from None
        if not lo <= v <= hi:
            raise ValueError(f"{k} poza zakresem {lo}-{hi}")
        sampler[k] = v
    clean["sampler"] = sampler
    if not (clean["model"] or clean["musicdit"]):
        raise ValueError("Wybierz model tekstowy albo zestaw muzyki.")
    if clean["model"] and clean["musicdit"]:
        raise ValueError("Tekst i muzyka nie mieszczą się razem w pamięci karty — to dwa osobne profile.")
    if any(clean[k] for k in MUSIC_FLAGS) and not all(clean[k] for k in MUSIC_FLAGS):
        raise ValueError("Muzyka (ACE-Step) potrzebuje czterech plików: LM, embeddings, DiT i VAE.")
    # Zostaje tylko to, co działa na wybrane modele, żeby plik profili nie miał martwych ustawień.
    if not clean["model"]:
        for k in ("context", "gpulayers", "quantkv", "jinja", "reasoning", "sampler"):
            clean.pop(k)
    if not clean["musicdit"]:
        for k in (*MUSIC_FLAGS, "musiclowvram"):
            clean.pop(k)
    return clean
