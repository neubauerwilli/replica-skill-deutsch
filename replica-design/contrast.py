#!/usr/bin/env python3
"""Kontrastprüfung für die Tokens von replica-design. Nur Standardbibliothek.

Jede Textfarbe in deiner Token-Datei, geprüft gegen die Hintergründe, auf denen
sie steht, mit dem WCAG-2-Kontrastverhältnis. Lass es nach jeder Änderung der
Palette laufen, auch bei der Umbenennung der Marke, denn bei einer neuen Palette
bricht der Kontrast.

    python3 contrast.py replica/design/tokens.json
    python3 contrast.py tokens.json --json
    python3 contrast.py "#6b7280" "#ffffff"        # ein einzelnes Paar

Die Paare kommen aus der Liste "pairs" der Token-Datei: [["text", "bg"], ...],
oder [["text-muted", "surface", "large"], ...] für Text ab 24px (oder 18,66px
fett), der nur 3:1 braucht. Ohne pairs-Liste wird jede Farbe, in deren Namen
text, fg oder on- vorkommt, gegen jede Farbe geprüft, in deren Namen bg,
background oder surface vorkommt.

Schwellen (WCAG 2.2): normaler Text AA 4,5, AAA 7. Großer Text AA 3, AAA 4,5.
UI-Teile und Fokusringe ("ui" als dritter Eintrag) brauchen 3.
Exit-Code 1, wenn ein Paar AA nicht erreicht, damit das Skript einen Build
sperren kann.
"""

import argparse
import json
import re
import sys

HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
NEEDS = {"normal": (4.5, 7.0), "large": (3.0, 4.5), "ui": (3.0, 3.0)}


def parse_hex(value):
    m = HEX.match(value.strip())
    if not m:
        raise ValueError("keine Hex-Farbe: %r" % value)
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    la, lb = luminance(parse_hex(fg)), luminance(parse_hex(bg))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def flatten(obj, prefix=""):
    """{"color": {"text": {"muted": "#..."}}} -> {"text-muted": "#..."}."""
    out = {}
    if isinstance(obj, dict):
        if "value" in obj and isinstance(obj["value"], str):
            out[prefix] = obj["value"]
            return out
        if "$value" in obj and isinstance(obj["$value"], str):
            out[prefix] = obj["$value"]
            return out
        for k, v in obj.items():
            if k.startswith("$") or k.startswith("_"):
                continue
            key = "%s-%s" % (prefix, k) if prefix else k
            out.update(flatten(v, key))
    elif isinstance(obj, str) and HEX.match(obj.strip()):
        out[prefix] = obj.strip()
    return out


def colours(tokens):
    src = tokens.get("color", tokens.get("colors", tokens.get("colour", {})))
    return {k: v for k, v in flatten(src).items() if HEX.match(v)}


def default_pairs(cols):
    fg = [k for k in cols if re.search(r"(^|-)(text|fg|on)(-|$)", k)]
    bg = [k for k in cols if re.search(r"(^|-)(bg|background|surface)(-|$)", k)]
    return [[f, b] for f in fg for b in bg]


def check(cols, pairs):
    if not isinstance(pairs, list):
        raise ValueError("pairs muss eine Liste von Paaren sein")
    rows = []
    for p in pairs:
        if not isinstance(p, list) or len(p) not in (2, 3) or not all(isinstance(v, str) for v in p):
            raise ValueError("jedes Paar braucht zwei Tokennamen und optional normal/large/ui")
        fg, bg = p[0], p[1]
        size = p[2] if len(p) > 2 else "normal"
        if size not in NEEDS:
            raise ValueError("unbekannte Textgröße: %s" % size)
        if fg not in cols or bg not in cols:
            rows.append({"fg": fg, "bg": bg, "size": size, "error": "unbekanntes Token"})
            continue
        r = ratio(cols[fg], cols[bg])
        aa, aaa = NEEDS[size]
        rows.append({"fg": fg, "bg": bg, "size": size, "ratio": round(r, 2),
                     "aa": r >= aa, "aaa": r >= aaa,
                     "fg_hex": cols[fg], "bg_hex": cols[bg]})
    return rows


def render(rows):
    out = []
    for r in rows:
        if "error" in r:
            out.append("  ??    %-24s auf %-20s %s" % (r["fg"], r["bg"], r["error"]))
            continue
        if r["size"] == "ui":
            grade = "PASS" if r["aa"] else "FAIL"
        else:
            grade = "AAA" if r["aaa"] else ("AA" if r["aa"] else "FAIL")
        out.append("  %-5s %5.2f:1  %-24s auf %-20s %s" % (
            grade, r["ratio"], r["fg"], r["bg"], "" if r["size"] == "normal" else r["size"]))
    fails = sum(1 for r in rows if "error" in r or not r["aa"])
    out.append("")
    out.append("  %d Paare, %d erreichen AA nicht" % (len(rows), fails))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("args", nargs="+", help="tokens.json oder zwei Hex-Farben")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if len(a.args) not in (1, 2):
            raise ValueError("eine Token-Datei oder genau zwei Hex-Farben angeben")
        if len(a.args) == 2 and all(HEX.match(x) for x in a.args):
            cols = {"fg": a.args[0], "bg": a.args[1]}
            pairs = [["fg", "bg"]]
        else:
            if len(a.args) != 1:
                raise ValueError("ungültiges Hex-Farbpaar")
            with open(a.args[0], encoding="utf-8") as fh:
                tokens = json.load(fh)
            if not isinstance(tokens, dict):
                raise ValueError("Token-Datei muss ein JSON-Objekt sein")
            cols = colours(tokens)
            pairs = tokens.get("pairs", default_pairs(cols))
        rows = check(cols, pairs)
    except (OSError, ValueError) as exc:
        print("contrast: %s" % exc, file=sys.stderr)
        return 2
    if not pairs:
        print("contrast: keine Paare zu prüfen. Füge der Token-Datei eine \"pairs\"-Liste hinzu.",
              file=sys.stderr)
        return 2
    print(json.dumps(rows, indent=2) if a.json else render(rows))
    return 1 if any("error" in r or not r["aa"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
