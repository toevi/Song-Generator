"""Silnik Song Generator: zarządzanie serwerem modeli (KoboldCpp) i jego profilami.

To jedyne miejsce, które zna proces `koboldcpp.exe`: start, przełączanie profilu gemma <-> muzyka
przez admin API, wyładowanie z karty, stan. Aplikacja (`app\\`) tylko woła funkcje stąd.
Układ katalogów: serwer\\ (ten kod + koboldcpp.exe + serwer.json), modele\\ (pliki .gguf), app\\ (okno i UI).
Logika przełączania przeniesiona z Little Mate (ensure_llm / swap_llm), bez zmian w zachowaniu.
"""
import json
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import models as M  # noqa: E402

HERE = Path(__file__).resolve().parent          # ...\Song Generator\serwer
ROOT = HERE.parent                               # ...\Song Generator
CONFIG_PATH = HERE / "serwer.json"
ADMIN_DIR = HERE / "admin"                       # kcpps eksportowane przy przełączaniu (odtwarzane za każdym razem)
CONFIG_LOCK = threading.Lock()

# KoboldCpp obsługuje jedną generację naraz; nasze wywołania ustawiamy w kolejce zamiast kolizji.
LOCK = threading.Lock()

ENSURE_OK, ENSURE_FAIL, ENSURE_BUSY = 0, 1, 2
# Ładowanie profilu z panelu w tle: jedno naraz, log dla UI.
APPLY = {"running": False, "name": "", "code": None, "log": []}


# ---------------------------------------------------------------- konfiguracja

def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def write_config(cfg):
    with CONFIG_LOCK:
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(CONFIG_PATH)


def _abs(p):
    """Ścieżka z configu (względna do katalogu głównego projektu) -> bezwzględna."""
    if not p:
        return ""
    q = Path(p)
    return str(q if q.is_absolute() else (ROOT / q).resolve())


def _rel(p):
    """Bezwzględna -> względna do katalogu głównego (jeśli leży w projekcie), żeby config był przenośny."""
    if not p:
        return ""
    try:
        return Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)


def models_dir():
    return Path(_abs(config().get("models_dir") or "modele"))


def profiles():
    """Nazwa -> profil ze ścieżkami bezwzględnymi."""
    out = {}
    for name, entry in (config().get("profiles") or {}).items():
        p = M.profile_of(entry)
        for k in M.FILE_KEYS:
            if p.get(k):
                p[k] = _abs(p[k])
        out[name] = p
    return out


def profile_args(name):
    return M.args_of(profiles()[name])


def url():
    return config()["url"].rstrip("/")


# ---------------------------------------------------------------- klient KoboldCpp

def call(path, payload=None, timeout=10):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url() + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def raw(path, payload, timeout):
    """POST JSON, zwraca (bajty, content-type) — dla odpowiedzi dźwiękowych."""
    req = urllib.request.Request(url() + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type") or "application/octet-stream"


def context_size():
    try:
        return call("/api/extra/true_max_context_length")["value"]
    except Exception:  # noqa: BLE001
        return None


def _media_model():
    """'koboldcpp/music', gdy Kobold działa bez modelu tekstowego, a z muzyką; inaczej ''."""
    try:
        v = call("/api/extra/version")
        return "koboldcpp/music" if not v.get("llm") and v.get("music") else ""
    except Exception:  # noqa: BLE001
        return ""


def status():
    try:
        model = call("/v1/models")["data"][0]["id"]
    except urllib.error.HTTPError as e:
        # Na porcie odpowiada inny program (nie KoboldCpp).
        return {"online": False, "foreign": True,
                "error": f"Port {url()} zajmuje inny program (to nie KoboldCpp, HTTP {e.code}). "
                         "Zmień port w serwer/serwer.json."}
    except Exception as e:  # noqa: BLE001
        return {"online": False, "error": str(e)}
    llm = True
    if model == "inactive":
        # Kobold zgłasza "inactive" po wyładowaniu i dla profilu bez modelu tekstowego (muzyka).
        media = _media_model()
        if not media:
            return {"online": False, "error": "model wyłączony (Kobold czeka na profil)", "unloaded": True}
        model, llm = media, False
    try:
        perf = call("/api/extra/perf")
        kobold_busy = perf.get("idle") == 0 or bool(perf.get("queue"))
    except Exception:  # noqa: BLE001
        kobold_busy = False
    return {"online": True, "llm": llm, "model": model, "context": context_size() if llm else None,
            "busy": LOCK.locked() or kobold_busy}


def capabilities():
    """Co umie załadowany profil (wszystko False, gdy serwer nie działa)."""
    try:
        v = call("/api/extra/version")
    except Exception:  # noqa: BLE001
        v = {}
    return {"music": bool(v.get("music"))}


def abort_generation():
    try:
        call("/api/extra/abort", {})
    except Exception:  # noqa: BLE001
        pass


def kobold_idle():
    """True, gdy KoboldCpp nic nie generuje i nie ma kolejki (także dla innych klientów)."""
    try:
        perf = call("/api/extra/perf")
        return perf.get("idle") == 1 and not perf.get("queue")
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------- który profil działa

def _model_tag(p):
    if p.get("model"):
        return Path(p["model"]).stem.lower()
    if p.get("musicdit"):
        return "koboldcpp/music"  # Kobold nie podaje nazwy pliku muzyki; _media_model mówi "music"
    return ""


def running_profile(st):
    """Nazwa profilu odpowiadającego temu, co zgłasza serwer, albo None."""
    rid = (st.get("model") or "").lower()
    same = [n for n, p in profiles().items() if _model_tag(p) and _model_tag(p) in rid]
    return same[0] if same else None


# ---------------------------------------------------------------- log ładowania (dla panelu)

class _Log:
    open_line = False  # ostatnia linia jeszcze pisana (kropki postępu, potem " gotowe.")

    def write(self, s):
        log = list(APPLY["log"])
        parts = s.split("\n")
        for i, part in enumerate(parts):
            if part.strip():
                if self.open_line and log:
                    log[-1] += part
                else:
                    log.append(part.strip())
                self.open_line = True
            if i < len(parts) - 1:
                self.open_line = False
        APPLY["log"] = log[-40:]
        sys.__stdout__.write(s)
        sys.__stdout__.flush()


_log = _Log()


def say(text, end="\n"):
    _log.write(text + end)


# ---------------------------------------------------------------- start / przełączanie

def launch_command(name):
    cfg = config()
    exe = _abs(cfg.get("kobold") or "serwer/koboldcpp.exe")
    cmd = [exe, "--usecuda", "--gpulayers", "-1", "--host", cfg.get("host", "127.0.0.1"),
           "--port", str(cfg["port"]), "--skiplauncher", "--quiet"]
    # Tryb admin pozwala przełączać profil przez API Kobolda zamiast zabijać proces; Kobold przyjmuje
    # konfigi tylko z tego folderu i wywala się na starcie, gdy go brak.
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)
    cmd += ["--admin", "--admindir", str(ADMIN_DIR)]
    return cmd + profile_args(name)


def _idle_for_swap(patience_s):
    """Dwa odczyty 'bezczynny' w odstępie sekundy w ciągu `patience_s` s."""
    deadline = time.monotonic() + patience_s
    while True:
        if kobold_idle():
            time.sleep(1)
            if kobold_idle():
                return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(1)


def _wait_ready(name, deadline, proc=None):
    say("Czekam na wczytanie modelu", end="")
    while time.monotonic() < deadline:
        if proc is not None and proc.poll() is not None:
            say(f"\nProces modelu zakończył się (kod {proc.returncode}) - sprawdź parametry profilu.")
            return False
        st = status()
        # Po przełączeniu stary model jeszcze chwilę odpowiada, więc liczy się tylko nowy;
        # zimny start akceptuje też model, którego nie umiemy dopasować po nazwie.
        accepted = (name,) if proc is None else (name, None)
        if st["online"] and running_profile(st) in accepted:
            say(" gotowe.")
            return True
        say(".", end="")
        time.sleep(2)
    say("\nModel nie wstał w zadanym czasie (wait_s w serwer.json).")
    return False


def swap(name):
    """Podmiana profilu w działającym KoboldCpp przez admin API. Zwraca kod ENSURE_*."""
    try:
        admin = call("/api/extra/version").get("admin", 0)
    except Exception:  # noqa: BLE001
        admin = 0
    if not admin:
        say("Kobold działa bez trybu admin (uruchomiony ręcznie) - nie da się podmienić modelu bez "
            "zamykania. Zamknij okno Kobolda i uruchom ponownie.")
        return ENSURE_FAIL
    # Nigdy nie przerywamy cudzej generacji. Do 10 s cierpliwości: tuż po zadaniu Kobold chwilę
    # zgłasza zajętość (widziane 17.11 po muzyce).
    if not _idle_for_swap(10):
        say("Model jest zajęty (trwa generowanie albo kolejka) - nic nie podmieniam. Spróbuj później.")
        return ENSURE_BUSY
    cfg_name = f"{name}.kcpps"
    # Kobold sam zapisuje swój format konfiguracji z tych samych argumentów, co zimny start.
    export = launch_command(name) + ["--exportconfig", str(ADMIN_DIR / cfg_name)]
    try:
        subprocess.run(export, capture_output=True, timeout=180,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as e:
        say(f"Nie udało się przygotować konfiguracji modelu: {e}")
        return ENSURE_FAIL
    if not (ADMIN_DIR / cfg_name).exists():
        say(f"KoboldCpp nie zapisał {ADMIN_DIR / cfg_name} - sprawdź parametry profilu w serwer.json.")
        return ENSURE_FAIL
    if not kobold_idle():  # ostatnie sprawdzenie tuż przed podmianą
        say("Model zajął się generowaniem - nic nie podmieniam. Spróbuj później.")
        return ENSURE_BUSY
    say(f"Podmieniam model na '{name}' (admin API KoboldCpp).")
    try:
        ok = call("/api/admin/reload_config", {"filename": cfg_name}).get("success")
    except Exception as e:  # noqa: BLE001
        say(f"KoboldCpp odrzucił podmianę: {e}")
        return ENSURE_FAIL
    if not ok:
        say("KoboldCpp odrzucił podmianę (plik spoza admin_dir?).")
        return ENSURE_FAIL
    # Stara instancja chwilę odpowiada po żądaniu; czekamy aż zniknie, żeby ponowne załadowanie tego
    # samego profilu (zmienione ustawienia) nie wyglądało na "już załadowany".
    gone = time.monotonic() + 30
    while time.monotonic() < gone and status()["online"]:
        time.sleep(0.5)
    deadline = time.monotonic() + config().get("wait_s", 300)
    return ENSURE_OK if _wait_ready(name, deadline) else ENSURE_FAIL


def ensure(name=None, hidden=True, replace=False, force=False):
    """Upewnia się, że profil działa; zwraca kod ENSURE_*.

    name=None przyjmuje to, co działa (zimny start = profil domyślny). Inny profil niż działający
    jest podmieniany tylko z replace=True i tylko gdy Kobold jest bezczynny; force=True przeładowuje
    nawet ten sam profil (po edycji ustawień w panelu).
    """
    cfg = config()
    allp = profiles()
    name = name or cfg.get("default_profile")
    if name not in allp:
        say(f"Nie znam profilu '{name}'. Dostępne: {', '.join(allp) or '-'}.")
        return ENSURE_FAIL
    for k in M.FILE_KEYS:
        if allp[name].get(k) and not Path(allp[name][k]).is_file():
            say(f"Brak pliku modelu '{name}': {allp[name][k]}")
            return ENSURE_FAIL
    st = status()
    if st["online"]:
        current = running_profile(st)
        if current == name and not (force and replace):
            say(f"Model już działa: {st['model']}")
            return ENSURE_OK
        if not replace:
            say(f"Działa już inny profil ({current or st['model']}). Użyj przełączenia, żeby podmienić na '{name}'.")
            return ENSURE_FAIL
        return swap(name)
    if st.get("unloaded"):
        # Kobold pracuje pusty po "Wyłącz model": ładujemy przez admin API, nigdy drugi proces na tym porcie.
        return swap(name)
    if st.get("foreign"):  # start tam tylko nie zbinduje portu i będzie czekał minuty
        say(st["error"])
        return ENSURE_FAIL
    command = launch_command(name)
    say(f"Uruchamiam profil '{name}'...")
    flags = getattr(subprocess, "CREATE_NO_WINDOW" if hidden else "CREATE_NEW_CONSOLE", 0)
    try:
        proc = subprocess.Popen(command, creationflags=flags, cwd=str(HERE))
    except OSError as e:
        say(f"Nie udało się uruchomić serwera modeli: {e}")
        return ENSURE_FAIL
    deadline = time.monotonic() + config().get("wait_s", 300)
    return ENSURE_OK if _wait_ready(name, deadline, proc) else ENSURE_FAIL


def start_apply(name):
    """Ładowanie profilu w tle (przycisk w panelu albo automatyczne przełączenie)."""
    if APPLY["running"]:
        return {"ok": False, "error": f"Trwa już ładowanie '{APPLY['name']}'."}
    if name not in profiles():
        return {"ok": False, "error": "Nie ma takiego profilu."}
    APPLY.update(running=True, name=name, code=None, log=[])

    def work():
        try:
            APPLY["code"] = ensure(name, hidden=True, replace=True, force=True)
        except Exception as e:  # noqa: BLE001 - raportujemy zamiast umierać po cichu w wątku
            APPLY["log"].append(f"Błąd: {e}")
            APPLY["code"] = ENSURE_FAIL
        finally:
            APPLY["running"] = False

    threading.Thread(target=work, daemon=True).start()
    return {"ok": True}


NEEDS = {"text": ("model", lambda st, cap: st.get("llm", True)),
         "music": ("musicdit", lambda st, cap: cap["music"])}


def prepare_for(need):
    """Dopasowuje załadowany profil do zadania, żeby nie wybierać modeli ręcznie.

    Gotowe, gdy działający profil już to umie; inaczej przełącza na pierwszy, który umie.
    Zwraca {ok, ready} albo {ok, switching: nazwa}.
    """
    if need not in NEEDS:
        return {"ok": False, "error": "Nieznane zadanie."}
    if APPLY["running"]:
        return {"ok": True, "switching": APPLY["name"]}
    key, can = NEEDS[need]
    st = status()
    if st["online"] and can(st, capabilities()):
        return {"ok": True, "ready": True}
    able = [n for n, p in profiles().items() if p.get(key)]
    if not able:
        what = {"text": "modelu językowego", "music": "modelu muzyki (ACE-Step)"}[need]
        return {"ok": False, "error": f"Żaden profil nie ma {what} - dodaj go w panelu Modele."}
    r = start_apply(able[0])
    return {"ok": True, "switching": able[0]} if r["ok"] else r


def unload_model():
    """Zwalnia kartę bez zamykania KoboldCpp (tryb admin); późniejsze ładowanie przywraca model."""
    try:
        admin = call("/api/extra/version").get("admin", 0)
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": "Kobold nie działa."}
    if not admin:
        return {"ok": False, "error": "Kobold bez trybu admin - zamknij jego okno ręcznie."}
    if not _idle_for_swap(10):  # tuż po zadaniu Kobold chwilę zgłasza zajętość
        return {"ok": False, "error": "Model właśnie generuje - spróbuj za chwilę."}
    if not call("/api/admin/reload_config", {"filename": "unload_model"}).get("success"):
        return {"ok": False, "error": "Kobold odrzucił polecenie."}
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if status().get("unloaded"):
            return {"ok": True, "error": ""}
        time.sleep(1)
    return {"ok": False, "error": "Kobold nie potwierdził wyłączenia w 60 s - sprawdź stan za chwilę."}


def release_gpu(wait=True):
    """Wyładowuje model przy wyjściu, jeśli nikt inny nie generuje; nigdy nie rzuca wyjątku."""
    try:
        if not status()["online"]:
            return
        if wait:
            r = unload_model()
            print("Model wyładowany - karta wolna." if r["ok"] else f"Model zostaje: {r['error']}")
        elif kobold_idle():
            call("/api/admin/reload_config", {"filename": "unload_model"})  # zamykanie konsoli: bez czekania
    except Exception as e:  # noqa: BLE001
        print(f"Nie udało się wyładować modelu: {e}")


# ---------------------------------------------------------------- panel Modele

def overview():
    cfg = config()
    files = M.scan([models_dir()])
    st = status()
    active = running_profile(st) if st["online"] else None
    out = {}
    for name, p in profiles().items():
        vram, notes = M.estimate_vram(p)
        missing = [k for k in M.FILE_KEYS if p.get(k) and not Path(p[k]).is_file()]
        out[name] = {"profile": p, "vram": vram, "notes": notes, "missing": missing,
                     "args": " ".join(M.args_of(p))}
    keep = ("name", "path", "size", "kind", "arch", "quant", "train_ctx", "layers")
    return {"dirs": [str(models_dir())], "files": [{k: f.get(k) for k in keep} for f in files],
            "profiles": out, "default": cfg.get("default_profile"), "active": active,
            "online": st["online"], "unloaded": bool(st.get("unloaded")), "running_model": st.get("model"),
            "context": st.get("context"), "gpu": M.gpu(), "kv_types": list(M.KV_TYPES),
            "reasoning": list(M.REASONING), "overhead": M.OVERHEAD}


def save_profile(name, profile, old_name=""):
    cfg = config()
    store = cfg.setdefault("profiles", {})
    if not old_name and name in store:
        return {"ok": False, "error": f"Profil '{name}' już istnieje - wybierz inną nazwę."}
    if old_name and old_name != name:
        return {"ok": False, "error": "Nazwy istniejącego profilu nie zmieniamy."}
    try:
        clean = M.validate(name, profile, [models_dir()])
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    vram, notes = M.estimate_vram(clean)
    store[name] = {k: (_rel(v) if k in M.FILE_KEYS else v) for k, v in clean.items()}
    write_config(cfg)
    return {"ok": True, "vram": vram, "notes": notes}


def delete_profile(name):
    cfg = config()
    if name not in (cfg.get("profiles") or {}):
        return {"ok": False, "error": "Nie ma takiego profilu."}
    if name == cfg.get("default_profile"):
        return {"ok": False, "error": "To profil domyślny - najpierw ustaw inny jako domyślny."}
    st = status()
    if st["online"] and running_profile(st) == name:
        return {"ok": False, "error": "Ten profil jest teraz załadowany - najpierw załaduj inny."}
    del cfg["profiles"][name]
    write_config(cfg)
    (ADMIN_DIR / f"{name}.kcpps").unlink(missing_ok=True)
    return {"ok": True}


def set_default(name):
    cfg = config()
    if name not in (cfg.get("profiles") or {}):
        return {"ok": False, "error": "Nie ma takiego profilu."}
    cfg["default_profile"] = name
    write_config(cfg)
    return {"ok": True}


def active_sampler():
    """Domyślne próbkowanie załadowanego profilu ({} gdy nieznane)."""
    st = status()
    name = running_profile(st) if st["online"] else None
    return M.sampler_of(profiles()[name]) if name else {}
