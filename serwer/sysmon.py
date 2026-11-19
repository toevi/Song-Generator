"""Odczyt parametrów komputera dla okienka podglądu: GPU, CPU, RAM. Tylko biblioteka standardowa.

GPU: nvidia-smi. CPU (użycie) i RAM: WinAPI przez ctypes. Temperatury CPU Windows nie udostępnia
bez sterownika czujników, więc bierzemy ją z pamięci współdzielonej HWiNFO (jeśli działa z włączonym
"Shared Memory Support"); bez niej pole zostaje puste.
"""
import ctypes
import shutil
import struct
import subprocess
import threading
import time
from ctypes import wintypes

_LOCK = threading.Lock()
_CACHE = {"t": 0.0, "data": None}
_CPU_PREV = None
_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ---------------------------------------------------------------- GPU

def _gpu():
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,clocks.sm",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, creationflags=_NOWIN).stdout
        name, temp, util, used, total, power, clock = [x.strip() for x in out.splitlines()[0].split(",")]

        def num(x):
            try:
                return float(x)
            except ValueError:  # "[N/A]"
                return None
        return {"name": name, "temp": num(temp), "util": num(util), "vram_used": num(used) * 2**20,
                "vram_total": num(total) * 2**20, "power": num(power), "clock": num(clock)}
    except (OSError, ValueError, IndexError, TypeError, subprocess.TimeoutExpired):
        return None


# ---------------------------------------------------------------- CPU użycie + RAM

class _MemStatus(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def _ram():
    m = _MemStatus()
    m.dwLength = ctypes.sizeof(m)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        return None
    return {"total": m.ullTotalPhys, "used": m.ullTotalPhys - m.ullAvailPhys}


def _cpu_util():
    """Użycie CPU w % od poprzedniego odczytu (pierwszy odczyt: None)."""
    global _CPU_PREV
    idle, kern, user = (wintypes.FILETIME() for _ in range(3))
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
        return None
    ft = lambda f: (f.dwHighDateTime << 32) | f.dwLowDateTime  # noqa: E731
    cur = (ft(idle), ft(kern), ft(user))  # kern zawiera czas bezczynności
    prev, _CPU_PREV = _CPU_PREV, cur
    if not prev:
        return None
    didle, dkern, duser = (c - p for c, p in zip(cur, prev))
    total = dkern + duser
    return round(100 * (total - didle) / total, 1) if total > 0 else None


# ---------------------------------------------------------------- CPU temperatura (HWiNFO)

HWINFO_MAP = "Global\\HWiNFO_SENS_SM2"
SENSOR_TYPE_TEMP = 2
_TEMP_PREFER = ("tctl", "tdie", "cpu package", "cpu (")


def _hwinfo_cpu_temp():
    k32 = ctypes.windll.kernel32
    k32.OpenFileMappingW.restype = wintypes.HANDLE
    k32.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    k32.MapViewOfFile.restype = ctypes.c_void_p
    k32.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
    k32.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
    h = k32.OpenFileMappingW(4, False, HWINFO_MAP)  # FILE_MAP_READ
    if not h:
        return None
    try:
        view = k32.MapViewOfFile(h, 4, 0, 0, 0)
        if not view:
            return None
        try:
            # Nagłówek (pack 1): sygnatura, wersja, rewizja, czas(8), offset/rozmiar/liczba sekcji czujników i odczytów.
            sig, _ver, _rev, _poll, _so, _ss, _sn, ro, rs, rn = struct.unpack("<IIIqIIIIII", ctypes.string_at(view, 44))
            if sig == 0 or not rn or not rs:
                return None  # HWiNFO zamknięty albo 'zamrożony' (sygnatura 0xDEAD)
            found = []
            for i in range(min(rn, 2000)):
                raw = ctypes.string_at(view + ro + i * rs, rs)
                typ = struct.unpack_from("<I", raw, 0)[0]
                if typ != SENSOR_TYPE_TEMP:
                    continue
                label = raw[12:12 + 128].split(b"\0")[0].decode("latin-1").lower()
                value = struct.unpack_from("<d", raw, 12 + 128 + 128 + 16)[0]
                found.append((label, value))
            for pref in _TEMP_PREFER:
                for label, value in found:
                    if pref in label:
                        return round(value, 1)
            return None
        finally:
            k32.UnmapViewOfFile(view)
    finally:
        k32.CloseHandle(h)


# ---------------------------------------------------------------- całość

def sample():
    """Jeden odczyt (cache 1 s, bo okienko i panel mogą pytać równolegle)."""
    with _LOCK:
        now = time.monotonic()
        if _CACHE["data"] is not None and now - _CACHE["t"] < 1.0:
            return _CACHE["data"]
        try:
            temp = _hwinfo_cpu_temp()
        except Exception:  # noqa: BLE001 - brak czujnika nie może psuć reszty odczytu
            temp = None
        data = {"gpu": _gpu(), "cpu": {"util": _cpu_util(), "temp": temp}, "ram": _ram()}
        _CACHE.update(t=now, data=data)
        return data
