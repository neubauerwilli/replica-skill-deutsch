#!/usr/bin/env python3
"""Screenshot-Vergleich für replica-vergleich. Nur Standardbibliothek.

Vergleicht einen Screenshot der Original-App mit demselben Bildschirm in deinem
Klon und sagt dir, wie nah das Layout ist und wo es abweicht.

    python3 imgdiff.py original.png clone.png
    python3 imgdiff.py original.png clone.png --out diff.png --json
    python3 imgdiff.py original.png clone.png --mode pixel --fail-under 95

Zwei Modi:

  layout (Standard) Vergleicht Struktur, nicht Farbe. Beide Bilder werden zu
                    Kantenkarten, in ein Raster zerlegt, und die Kantendichte
                    jeder Zelle wird verglichen. Deine Umbenennung ändert jede
                    Farbe mit Absicht, darum wird Farbe hier ignoriert. Nur
                    Zellen, in denen (in einem der beiden Bilder) etwas ist,
                    werden bewertet, damit leere Ränder die Zahl nicht
                    aufpolstern. Das ist der Paritätswert.
  pixel             Exakter Pixelvergleich mit Toleranz. Nutze ihn für deine
                    eigenen Regressionen (Klon heute gegen Klon gestern), nicht,
                    um den Pixeln des Originals nachzujagen.

Beide Bilder werden auf dieselbe Breite skaliert (--width, Standard 480) und
über die gemeinsame Höhe verglichen. Ein Höhenunterschied wird gemeldet, nicht
versteckt.

Liest PNGs mit 8 und 16 Bit (Grau, RGB, Palette, mit oder ohne Alpha).
Interlaced-PNGs werden mit einer Meldung abgelehnt: speichere den Screenshot
ohne Interlacing neu.
"""

import argparse
import json
import math
import struct
import sys
import zlib

SIG = b"\x89PNG\r\n\x1a\n"
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_PIXELS = 4_000_000


class PngError(Exception):
    pass


# ----------------------------------------------------------------- PNG lesen

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw, height, stride, bpp):
    rows = []
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        if pos + 1 + stride > len(raw):
            raise PngError("die Bilddaten sind abgeschnitten")
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        elif ftype != 0:
            raise PngError("unbekannter Filtertyp %d" % ftype)
        rows.append(line)
        prev = line
    return rows


def _samples(line, width, channels, depth):
    """Entpackt eine ungefilterte Bildzeile in eine flache Liste von 8-Bit-Werten."""
    n = width * channels
    if depth == 8:
        return list(line[:n])
    if depth == 16:
        return [line[2 * i] for i in range(n)]
    out = []
    per_byte = 8 // depth
    mask = (1 << depth) - 1
    for byte in line:
        for k in range(per_byte):
            shift = 8 - depth * (k + 1)
            out.append((byte >> shift) & mask)
            if len(out) == n:
                return out
    return out


def read_png(path):
    """Gibt (Breite, Höhe, Zeilen) zurück. rows[y][x] ist ein (r, g, b)-Tupel.

    Alpha wird über Weiß gelegt, so wie ein Screenshot einer Seite sie zeigt.
    """
    with open(path, "rb") as fh:
        data = fh.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise PngError("PNG ist größer als 32 MiB; Screenshot verkleinern oder zuschneiden")
    if data[:8] != SIG:
        raise PngError("%s ist keine PNG-Datei" % path)
    pos = 8
    ihdr = None
    plte = None
    trns = None
    idat = []
    ended = False
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        if pos + 12 + length > len(data):
            raise PngError("abgeschnittener PNG-Block")
        chunk = data[pos + 8:pos + 8 + length]
        crc = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])[0]
        if zlib.crc32(ctype + chunk) & 0xffffffff != crc:
            raise PngError("PNG-Prüfsumme stimmt nicht")
        pos += 12 + length
        if ctype == b"IHDR":
            if ihdr is not None or len(chunk) != 13 or pos != 33:
                raise PngError("ungültiger IHDR-Block")
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            if not chunk or len(chunk) % 3 or len(chunk) > 768:
                raise PngError("ungültige PNG-Palette")
            plte = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif ctype == b"tRNS":
            trns = chunk
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            ended = True
            break
    if ihdr is None or not ended:
        raise PngError("%s hat keinen IHDR-Block" % path)
    width, height, depth, color, _comp, _filt, interlace = ihdr
    if width < 1 or height < 1 or width * height > MAX_PIXELS:
        raise PngError("PNG braucht positive Maße und höchstens 4 Millionen Pixel; Screenshot zuschneiden")
    if _comp != 0 or _filt != 0:
        raise PngError("nicht unterstützte PNG-Kompression oder Filtermethode")
    if interlace:
        raise PngError("%s ist interlaced gespeichert. Speichere es ohne Interlacing "
                       "neu (auf dem Mac: sips -s format png in.png --out out.png)" % path)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if channels is None:
        raise PngError("nicht unterstützter PNG-Farbtyp %d" % color)
    allowed_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
    if depth not in allowed_depths[color]:
        raise PngError("nicht unterstützte Bittiefe %d" % depth)
    if color == 3 and plte is None:
        raise PngError("Paletten-PNG ohne Palette")
    bits = depth * channels
    bpp = max(1, bits // 8)
    stride = (width * bits + 7) // 8
    expected = height * (stride + 1)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(b"".join(idat), expected + 1)
    if len(raw) != expected or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:
        raise PngError("PNG-Bilddaten haben eine ungültige oder zu große entpackte Länge")
    lines = _unfilter(raw, height, stride, bpp)

    scale = 255 // ((1 << depth) - 1) if depth < 8 else 1
    alpha_pal = list(trns) if (color == 3 and trns) else []
    rows = []
    for line in lines:
        s = _samples(line, width, channels, depth)
        row = []
        if color == 0:
            for v in s:
                g = v * scale
                row.append((g, g, g))
        elif color == 2:
            for i in range(0, len(s), 3):
                row.append((s[i], s[i + 1], s[i + 2]))
        elif color == 3:
            for idx in s:
                if idx >= len(plte):
                    raise PngError("PNG-Palettenindex liegt außerhalb der Palette")
                r, g, b = plte[idx]
                a = alpha_pal[idx] if idx < len(alpha_pal) else 255
                row.append(_over_white(r, g, b, a))
        elif color == 4:
            for i in range(0, len(s), 2):
                g = s[i]
                row.append(_over_white(g, g, g, s[i + 1]))
        else:
            for i in range(0, len(s), 4):
                row.append(_over_white(s[i], s[i + 1], s[i + 2], s[i + 3]))
        rows.append(row)
    return width, height, rows


def _over_white(r, g, b, a):
    if a == 255:
        return (r, g, b)
    inv = 255 - a
    return ((r * a + 255 * inv) // 255, (g * a + 255 * inv) // 255,
            (b * a + 255 * inv) // 255)


# ----------------------------------------------------------------- PNG schreiben

def write_png(path, width, height, rows):
    """Schreibt 8-Bit-RGB. rows[y][x] ist ein (r, g, b)-Tupel."""
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))

    def chunk(kind, body):
        crc = zlib.crc32(kind + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as fh:
        fh.write(SIG + chunk(b"IHDR", ihdr) +
                 chunk(b"IDAT", zlib.compress(bytes(raw), 6)) +
                 chunk(b"IEND", b""))


# ------------------------------------------------------------------- Vergleichen

def resize(rows, width, height, new_w, new_h):
    """Skalierung zum nächsten Nachbarn. Gut genug für Struktur, und schnell."""
    xs = [min(width - 1, int(x * width / new_w)) for x in range(new_w)]
    ys = [min(height - 1, int(y * height / new_h)) for y in range(new_h)]
    return [[rows[y][x] for x in xs] for y in ys]


def to_width(img, target):
    w, h, rows = img
    if w == target:
        return w, h, rows
    new_h = max(1, int(round(h * target / float(w))))
    return target, new_h, resize(rows, w, h, target, new_h)


def gray(rows):
    return [[(299 * r + 587 * g + 114 * b) // 1000 for r, g, b in row] for row in rows]


def edges(g, threshold):
    h = len(g)
    w = len(g[0]) if h else 0
    out = []
    for y in range(h):
        row = g[y]
        below = g[y + 1] if y + 1 < h else row
        e = []
        for x in range(w):
            right = row[x + 1] if x + 1 < w else row[x]
            e.append(1 if abs(right - row[x]) + abs(below[x] - row[x]) > threshold else 0)
        out.append(e)
    return out


def _regions(flags, n_rows, n_cols):
    """Fasst markierte Rasterzellen zu Rechtecken zusammen (4er-Nachbarschaft)."""
    seen = set()
    regions = []
    for r in range(n_rows):
        for c in range(n_cols):
            if not flags[r][c] or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr + 1, cc), (cr - 1, cc), (cr, cc + 1), (cr, cc - 1)):
                    if 0 <= nr < n_rows and 0 <= nc < n_cols and flags[nr][nc] \
                            and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [x[0] for x in cells]
            cs = [x[1] for x in cells]
            regions.append((min(rs), min(cs), max(rs), max(cs), len(cells)))
    regions.sort(key=lambda t: -t[4])
    return regions


def compare(img_a, img_b, mode="layout", width=480, cols=12, tolerance=24,
            edge_threshold=40):
    """Vergleicht zwei dekodierte Bilder. Gibt (Bericht als dict, Diff-Zeilen) zurück."""
    if width <= 0 or not 1 <= cols <= 512 or not 0 <= tolerance <= 255:
        raise ValueError("width muss positiv sein, cols 1 bis 512, tolerance 0 bis 255")
    wa, ha, _ = img_a
    wb, hb, _ = img_b
    target = min(width, wa, wb)
    a = to_width(img_a, target)
    b = to_width(img_b, target)
    w = target
    h = min(a[1], b[1])
    ra = a[2][:h]
    rb = b[2][:h]
    height_delta = (b[1] - a[1]) / float(a[1]) * 100.0 if a[1] else 0.0
    to_orig = wa / float(w)

    ga = gray(ra)
    dim = [[(200 + v // 5,) * 3 for v in row] for row in ga]
    report = {
        "mode": mode,
        "original": {"width": wa, "height": ha},
        "clone": {"width": wb, "height": hb},
        "compared_at": {"width": w, "height": h},
        "height_delta_pct": round(height_delta, 1),
    }

    if mode == "pixel":
        changed = 0
        flags_px = []
        for y in range(h):
            fr = []
            for x in range(w):
                pa, pb = ra[y][x], rb[y][x]
                d = max(abs(pa[0] - pb[0]), abs(pa[1] - pb[1]), abs(pa[2] - pb[2]))
                hit = d > tolerance
                fr.append(hit)
                if hit:
                    changed += 1
                    dim[y][x] = (220, 30, 30)
            flags_px.append(fr)
        total = w * h or 1
        score = 100.0 * (1 - changed / float(total))
        report["changed_pixels"] = changed
        # Pixeltreffer als Rasterbereiche zusammenfassen, damit der Bericht lesbar bleibt.
        cell = max(1, int(math.ceil(w / float(cols))))
        n_rows = int(math.ceil(h / float(cell)))
        flags = [[False] * cols for _ in range(n_rows)]
        for r in range(n_rows):
            for c in range(cols):
                hits = 0
                area = 0
                for y in range(r * cell, min(h, (r + 1) * cell)):
                    row = flags_px[y]
                    for x in range(c * cell, min(w, (c + 1) * cell)):
                        area += 1
                        hits += row[x]
                flags[r][c] = area > 0 and hits / float(area) > 0.02
    else:
        ea = edges(ga, edge_threshold)
        eb = edges(gray(rb), edge_threshold)
        cell = max(1, int(math.ceil(w / float(cols))))
        n_rows = int(math.ceil(h / float(cell)))
        flags = [[False] * cols for _ in range(n_rows)]
        sims = []
        for r in range(n_rows):
            for c in range(cols):
                y0, y1 = r * cell, min(h, (r + 1) * cell)
                x0, x1 = c * cell, min(w, (c + 1) * cell)
                area = (y1 - y0) * (x1 - x0)
                if area <= 0:
                    continue
                da = sum(sum(ea[y][x0:x1]) for y in range(y0, y1)) / float(area)
                db = sum(sum(eb[y][x0:x1]) for y in range(y0, y1)) / float(area)
                top = max(da, db)
                if top < 0.01:
                    continue  # in beiden leer: sagt nichts über das Layout
                sim = 1.0 - abs(da - db) / top
                sims.append(sim)
                if sim < 0.6:
                    flags[r][c] = True
                    for y in range(y0, y1):
                        for x in range(x0, x1):
                            g0 = dim[y][x][0]
                            dim[y][x] = (min(255, g0 + 30), g0 // 3, g0 // 3)
        score = 100.0 * sum(sims) / len(sims) if sims else 100.0

    regions = []
    for r0, c0, r1, c1, n in _regions(flags, len(flags), cols):
        x = int(c0 * cell * to_orig)
        y = int(r0 * cell * to_orig)
        regions.append({
            "x": x, "y": y,
            "w": min(wa - x, int((c1 - c0 + 1) * cell * to_orig)),
            "h": min(ha - y, int((r1 - r0 + 1) * cell * to_orig)),
            "cells": n,
            "where": _where(r0, c0, r1, c1, len(flags), cols),
        })
    report["score"] = round(score, 1)
    report["verdict"] = verdict(score)
    report["regions"] = regions
    return report, dim


def _where(r0, c0, r1, c1, n_rows, n_cols):
    mid_r = (r0 + r1) / 2.0 / max(1, n_rows - 1) if n_rows > 1 else 0.5
    mid_c = (c0 + c1) / 2.0 / max(1, n_cols - 1) if n_cols > 1 else 0.5
    v = "oben" if mid_r < 0.34 else ("unten" if mid_r > 0.66 else "Mitte")
    hz = "links" if mid_c < 0.34 else ("rechts" if mid_c > 0.66 else "mittig")
    return "%s %s" % (v, hz)


def verdict(score):
    if score >= 90:
        return "stimmt"
    if score >= 75:
        return "nah"
    if score >= 50:
        return "teilweise"
    return "anders"


def render_text(report, a_name, b_name):
    lines = []
    bar = int(round(report["score"] / 100.0 * 24))
    lines.append("  %s gegen %s" % (a_name, b_name))
    lines.append("  %-6s %s%s  %5.1f  %s" % (
        report["mode"].upper(), "#" * bar, "." * (24 - bar), report["score"],
        report["verdict"].upper()))
    hd = report["height_delta_pct"]
    if abs(hd) >= 5:
        lines.append("  Höhe: der Klon ist %.0f%% %s als das Original"
                     % (abs(hd), "höher" if hd > 0 else "niedriger"))
    if report["regions"]:
        lines.append("  wo sie abweichen (Pixel des Originals, größte zuerst):")
        for reg in report["regions"][:8]:
            lines.append("    %-14s x=%d y=%d w=%d h=%d" % (
                reg["where"], reg["x"], reg["y"], reg["w"], reg["h"]))
    else:
        lines.append("  keine abweichenden Bereiche")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("original", help="Screenshot der Original-App (PNG)")
    ap.add_argument("clone", help="derselbe Bildschirm in deinem Klon (PNG)")
    ap.add_argument("--mode", choices=("layout", "pixel"), default="layout")
    ap.add_argument("--width", type=int, default=480,
                    help="in dieser Breite vergleichen (Standard 480)")
    ap.add_argument("--cols", type=int, default=12, help="Rasterspalten (Standard 12)")
    ap.add_argument("--tolerance", type=int, default=24,
                    help="Pixelmodus: ignorierter Unterschied pro Kanal (Standard 24)")
    ap.add_argument("--out", help="hierhin ein Diff-Bild schreiben (PNG)")
    ap.add_argument("--json", action="store_true", help="JSON statt Text ausgeben")
    ap.add_argument("--fail-under", type=float,
                    help="Exit 1, wenn der Wert darunter liegt")
    args = ap.parse_args(argv)
    try:
        if args.fail_under is not None and (not math.isfinite(args.fail_under) or not 0 <= args.fail_under <= 100):
            raise ValueError("--fail-under muss zwischen 0 und 100 liegen")
        a = read_png(args.original)
        b = read_png(args.clone)
        report, diff = compare(a, b, mode=args.mode, width=args.width, cols=args.cols,
                               tolerance=args.tolerance)
        if args.out:
            import os
            if os.path.realpath(args.out) in (os.path.realpath(args.original), os.path.realpath(args.clone)):
                raise ValueError("Diff-Ausgabe darf keine Eingabedatei überschreiben")
            write_png(args.out, report["compared_at"]["width"], report["compared_at"]["height"], diff)
    except (PngError, OSError, ValueError, zlib.error) as exc:
        print("imgdiff: %s" % exc, file=sys.stderr)
        return 2
    report["files"] = {"original": args.original, "clone": args.clone}
    if args.out:
        report["diff_image"] = args.out
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report, args.original, args.clone))
        if args.out:
            print("  Diff-Bild: %s" % args.out)
    if args.fail_under is not None and report["score"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
