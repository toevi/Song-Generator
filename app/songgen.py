#!/usr/bin/env python3
"""Song Generator — okno aplikacji i lokalne API dla interfejsu.

Uruchomienie: `python app\\songgen.py` (albo start.cmd w katalogu głównym).
Okno natywne (pywebview) pokazuje stronę z app\\ui, którą serwuje ten proces na 127.0.0.1.
Modelami zarządza serwer\\engine.py; tu tylko HTTP, zapis plików i okno. Tylko biblioteka standardowa
(+ pywebview dla okna; bez niego strona otwiera się w przeglądarce).
"""
import base64
import json
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent            # ...\Song Generator\app
ROOT = BASE.parent
sys.path.insert(0, str(ROOT / "serwer"))
sys.path.insert(0, str(BASE))
import engine as E  # noqa: E402
import lyrics as L  # noqa: E402
import music as MU  # noqa: E402

UI_DIR = BASE / "ui"
WEBVIEW_DIR = BASE / ".okno"  # profil okna: trzyma localStorage (lista utworów, ustawienia) między uruchomieniami
CONFIG_PATH = BASE / "app.json"
MAX_BODY = 32 * 2**20
UI = {"last_poll": 0.0, "bye": 0.0}
BYE_GRACE_S = 15


def app_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _err(e, what):
    return {"ok": False, "error": f"Błąd {what}: {e}"}


class Handler(BaseHTTPRequestHandler):
    server_version = "SongGenerator/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _trusted(self, post):
        """Tylko nasza strona może z nami rozmawiać. Każda witryna otwarta w przeglądarce może słać
        żądania na 127.0.0.1: obcy Host = DNS rebinding, obcy Origin = żądanie między witrynami,
        a typ inny niż JSON = „proste” żądanie bez preflightu CORS."""
        port = self.server.server_address[1]
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "") not in hosts:
            return False
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://{h}" for h in hosts}:
            return False
        if post and not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return False
        return True

    def do_GET(self):
        if not self._trusted(post=False):
            return self._json(403, {"error": "forbidden"})
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, (UI_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path in ("/icon.png", "/favicon.ico"):
            name, kind = ("icon.png", "image/png") if path == "/icon.png" else ("icon.ico", "image/x-icon")
            self._send(200, (UI_DIR / name).read_bytes(), kind)
        elif path == "/api/status":
            UI["last_poll"] = time.monotonic()
            st = E.status()
            st["apply"] = {k: E.APPLY[k] for k in ("running", "name", "code")}
            if st["online"]:
                st["profile"] = E.running_profile(st)
                st.update(E.capabilities())
            self._json(200, st)
        elif path == "/api/models":
            self._json(200, E.overview())
        elif path == "/api/apply":
            self._json(200, dict(E.APPLY))
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if not self._trusted(post=True):
            return self._json(403, {"error": "forbidden"})
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                raise ValueError("too large")
            req = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "zły JSON albo plik za duży"})

        if path == "/api/profile":
            return self._json(200, E.save_profile(str(req.get("name", "")), req.get("profile") or {},
                                                  str(req.get("old_name") or "")))
        if path == "/api/estimate":
            import models as M
            try:
                p = M.validate("podglad", req.get("profile") or {}, [E.models_dir()])
            except ValueError as e:
                return self._json(200, {"ok": False, "error": str(e)})
            vram, notes = M.estimate_vram(p)
            return self._json(200, {"ok": True, "vram": vram, "notes": notes, "gpu": M.gpu()})
        if path == "/api/profile/delete":
            return self._json(200, E.delete_profile(str(req.get("name", ""))))
        if path == "/api/default":
            return self._json(200, E.set_default(str(req.get("name", ""))))
        if path == "/api/apply":
            return self._json(200, E.start_apply(str(req.get("name", ""))))
        if path == "/api/prepare":
            return self._json(200, E.prepare_for(str(req.get("need", ""))))
        if path == "/api/unload":
            return self._json(200, E.unload_model())
        if path == "/api/abort":
            E.abort_generation()
            return self._json(200, {"ok": True})
        if path == "/api/bye":
            UI["bye"] = time.monotonic()
            return self._json(200, {"ok": True})
        if path == "/api/music":
            try:
                audio, ctype, info = MU.generate_music(req)
            except ValueError as e:
                return self._json(200, {"ok": False, "error": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._json(200, _err(e, "generowania muzyki"))
            # Surowy dźwięk (3-minutowy WAV to ~35 MB - bez base64 w JSON); plan jedzie w nagłówku.
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(audio)))
            self.send_header("X-Music-Plan", urllib.parse.quote(json.dumps(info, ensure_ascii=False)))
            self.end_headers()
            self.wfile.write(audio)
            return None
        if path == "/api/lyrics/fit":
            try:
                text, left, foreign = L.fit_lyrics(str(req.get("skeleton", "")), str(req.get("text", "")),
                                                   str(req.get("lang", "")))
                return self._json(200, {"ok": True, "text": text, "extra_lines": left, "foreign": foreign})
            except (ValueError, L.LLMError) as e:
                return self._json(200, {"ok": False, "error": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._json(200, _err(e, "dopasowania tekstu"))
        if path == "/api/lyrics":
            try:
                text, title = L.write_lyrics(str(req.get("theme", "")), str(req.get("lang", "")),
                                             req.get("duration"), str(req.get("skeleton", "")))
                return self._json(200, {"ok": True, "text": text, "title": title})
            except (ValueError, L.LLMError) as e:
                return self._json(200, {"ok": False, "error": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._json(200, _err(e, "pisania tekstu"))
        if path == "/api/translate":
            try:
                return self._json(200, {"ok": True, "text": L.translate(str(req.get("text", "")),
                                                                        str(req.get("jezyk", "")))})
            except (ValueError, L.LLMError) as e:
                return self._json(200, {"ok": False, "error": str(e)})
            except Exception as e:  # noqa: BLE001
                return self._json(200, _err(e, "tłumaczenia"))
        self._json(404, {"error": "not found"})


class Server(ThreadingHTTPServer):
    # Windows: SO_REUSEADDR pozwala drugiemu procesowi po cichu zająć ten sam port; odmawiamy.
    allow_reuse_address = sys.platform != "win32"
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], ConnectionError):  # okno zamknięte w trakcie żądania
            return
        super().handle_error(request, client_address)


SAVE_KINDS = {"mp3": "MP3", "wav": "WAV"}


def _unique(path):
    """nazwa.ext -> nazwa-2.ext, nazwa-3.ext ... aż wolne (zapis nigdy po cichu nie nadpisuje)."""
    path, n = Path(path), 2
    stem = path.stem
    while path.exists():
        path, n = path.with_name(f"{stem}-{n}{path.suffix}"), n + 1
    return path


class SaveApi:
    """Natywne okna zapisu. Każdy zapis idzie za wyborem użytkownika w oknie dialogowym."""

    def __init__(self):
        self._window = None  # z podkreśleniem: pywebview nie może wchodzić w obiekt Window (nieskończona rekurencja)
        self.folder = None   # folder wybrany dla „zapisz wszystkie” w tym oknie

    @staticmethod
    def _data(data):
        return base64.b64decode(data.split(",", 1)[-1])

    def _ask(self, name, kind):
        import webview
        return self._window.create_file_dialog(webview.FileDialog.SAVE, save_filename=Path(str(name)).name,
                                               file_types=(f"{SAVE_KINDS[kind]} (*.{kind})",))

    def save(self, name, kind, data=""):
        if kind not in SAVE_KINDS:
            return {"ok": False, "error": "Nieznany typ pliku."}
        got = self._ask(name or f"utwor.{kind}", kind)
        if not got:
            return {"ok": False, "cancel": True}
        target = Path(got if isinstance(got, str) else got[0])
        if target.suffix.lower() != "." + kind:
            target = target.with_name(target.name + "." + kind)
        try:
            target.write_bytes(self._data(data))
        except (OSError, ValueError) as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "path": str(target)}

    def pick_folder(self, name="", kind=""):
        """Gdzie pisze „zapisz wszystkie”: zwykłe okno zapisu dla pierwszego pliku, jego folder dla reszty.
        (Wybieracz folderu pywebview otwierał się, ale nic nie zapisywał w oknie aplikacji — 19.11.)"""
        try:
            if kind not in SAVE_KINDS:
                return {"ok": False, "error": "Nieznany typ pliku."}
            got = self._ask(name, kind)
            if not got:
                return {"ok": False, "cancel": True}
            first = Path(got if isinstance(got, str) else got[0])
            if first.suffix.lower() != "." + kind:
                first = first.with_name(first.name + "." + kind)
            self.folder = first.parent
            return {"ok": True, "path": str(self.folder), "name": first.name}
        except Exception as e:  # pokazane w aplikacji zamiast cichego zatrzymania
            traceback.print_exc()
            return {"ok": False, "error": f"Okno zapisu: {e}"}

    def save_in_folder(self, name, kind, data):
        """Zapis do folderu wybranego chwilę wcześniej (pick_folder), nigdy na istniejący plik."""
        if not self.folder or kind not in SAVE_KINDS:
            return {"ok": False, "error": "Najpierw wybierz folder."}
        name = Path(str(name)).name
        if not name.lower().endswith("." + kind):
            name += "." + kind
        try:
            target = _unique(self.folder / name)
            target.write_bytes(self._data(data))
        except Exception as e:
            traceback.print_exc()
            return {"ok": False, "error": str(e)}
        return {"ok": True, "path": str(target)}


def run_webview(url):
    """Blokuje do zamknięcia okna."""
    import webview
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
    if sys.platform == "win32":
        import ctypes
        # Własna grupa na pasku zadań, żeby Windows pokazał naszą ikonę zamiast python.exe.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SongGenerator.App")
    api = SaveApi()
    api._window = webview.create_window("Song Generator", url, width=1400, height=900, min_size=(900, 600),
                                        js_api=api)
    webview.start(private_mode=False, storage_path=str(WEBVIEW_DIR), icon=str(UI_DIR / "icon.ico"))


def _on_console_close(action):
    """Uruchamia `action` przy zamknięciu okna konsoli krzyżykiem (Windows); Ctrl+C obsługuje serve."""
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)
    def handler(event):
        if event in (2, 5, 6):  # CLOSE, LOGOFF, SHUTDOWN
            action()
        return False
    _on_console_close.keep = handler  # callback musi przeżyć tę funkcję
    ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)


def serve():
    cfg = app_config()
    url = f"http://{cfg['host']}:{cfg['port']}"
    try:
        httpd = Server((cfg["host"], cfg["port"]), Handler)
    except OSError:
        print(f"Port {cfg['port']} jest zajęty - Song Generator już działa w innym oknie.")
        webbrowser.open(url)
        return
    print(f"Song Generator: {url}")
    unload = cfg.get("unload_on_exit", True)
    _on_console_close(lambda: unload and E.release_gpu(wait=False))
    # Serwer modeli rusza od razu z profilem domyślnym (gemma); okno pokazuje „ładuję…”.
    E.start_apply(E.config().get("default_profile"))
    try:
        import webview  # noqa: F401
        have_window = True
    except ImportError:
        print("Brak pywebview (pip install pywebview) - otwieram w przeglądarce.")
        have_window = False
    if have_window:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        run_webview(url)
        print("\nOkno Song Generator zamknięte.")
        if unload:
            E.release_gpu(wait=True)
        httpd.shutdown()
        return
    webbrowser.open(url)
    threading.Thread(target=_close_watch, args=(httpd, unload), daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        if unload:
            E.release_gpu(wait=True)


def _close_watch(httpd, unload):
    """Tryb przeglądarki: strona zgłasza zamknięcie (/api/bye); cisza po pożegnaniu = koniec."""
    while True:
        time.sleep(2)
        bye = UI["bye"]
        if bye and UI["last_poll"] < bye and time.monotonic() - bye > BYE_GRACE_S:
            if unload:
                E.release_gpu(wait=True)
            httpd.shutdown()
            return


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    serve()
