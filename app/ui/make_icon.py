"""Draws the Song Generator icon (ui/icon.png + ui/icon.ico) with the standard library only.

Violet-to-blue rounded square with two white beamed eighth notes. Shapes are tested per pixel with
4x4 supersampling, so edges stay smooth at every size.
Run: python make_icon.py
"""
import math
import struct
import zlib
from pathlib import Path

TOP = (124, 58, 237)     # violet
BOTTOM = (14, 165, 233)  # sky blue
WHITE = (255, 255, 255)
SS = 4  # supersampling per axis


def rounded_rect(x, y, x0, y0, x1, y1, r):
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r and x0 <= x <= x1 and y0 <= y <= y1


def in_ellipse(x, y, cx, cy, rx, ry, tilt):
    """Point inside an ellipse tilted by `tilt` radians (note heads lean up to the right)."""
    dx, dy = x - cx, y - cy
    c, s = math.cos(tilt), math.sin(tilt)
    u, v = dx * c + dy * s, -dx * s + dy * c
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1


def in_poly(x, y, pts):
    inside = False
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def colour_at(x, y):
    """Colour of a point in a 256x256 design space, or None for transparent."""
    if not rounded_rect(x, y, 8, 8, 248, 248, 56):
        return None
    note = (in_ellipse(x, y, 92, 178, 30, 22, -0.4) or in_ellipse(x, y, 176, 160, 30, 22, -0.4)
            or 108 <= x <= 122 and 72 <= y <= 176        # left stem
            or 192 <= x <= 206 and 54 <= y <= 158         # right stem
            or in_poly(x, y, [(108, 72), (206, 54), (206, 90), (108, 108)]))  # beam
    if note:
        return WHITE
    t = (y - 8) / 240
    return tuple(round(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))


def render(size):
    k = 256 / size
    rows = []
    for py in range(size):
        row = bytearray([0])  # PNG filter: none
        for px in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(SS):
                for sx in range(SS):
                    c = colour_at((px + (sx + 0.5) / SS) * k, (py + (sy + 0.5) / SS) * k)
                    if c:
                        acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; acc[3] += 1
            n = acc[3]
            row += bytes((acc[0] // n, acc[1] // n, acc[2] // n, 255 * n // (SS * SS))) if n else b"\0\0\0\0"
        rows.append(bytes(row))
    return png(size, b"".join(rows))


def png(size, raw):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def ico(images):
    """ICO with PNG-compressed entries (Windows Vista and newer)."""
    head = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries, data = b"", b""
    for size, blob in images:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset + len(data))
        data += blob
    return head + entries + data


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    images = [(s, render(s)) for s in (16, 24, 32, 48, 64, 256)]
    (here / "icon.png").write_bytes(images[-1][1])
    (here / "icon.ico").write_bytes(ico(images))
    print("icon.png, icon.ico:", ", ".join(str(s) for s, _ in images))
