#!/usr/bin/env python3
"""Funktionsparität für replica-vergleich. Nur Standardbibliothek.

Liest die Funktionsmatrix, die replica-erkundung geschrieben hat und die du beim
Bauen ausfüllst, und sagt dir, wie viel vom Original dein Klon kann, was fehlt
und in welcher Reihenfolge du es bauen solltest.

    python3 parity.py replica/features.csv
    python3 parity.py replica/features.csv --visual diffs/*.json
    python3 parity.py replica/features.csv --markdown > replica/parity.md
    python3 parity.py replica/features.csv --fail-under 80

Die CSV hat diese Spalten (weitere Spalten werden ignoriert):

    feature    was es tut, in einfachen Worten ("einen Termin verschieben")
    area       der Bildschirm oder Ablauf, zu dem es gehört ("Buchungsseite")
    priority   must | should | could   (P0 | P1 | P2 gehen auch)
    original   yes | no     hat die Original-App es
    clone      yes | partial | no | skip
    notes      beliebig. Bei skip den Grund nennen ("lizenzierter Inhalt, nicht im Umfang")

Gewichte: must 3, should 2, could 1. yes zählt 1, partial 0,5, no 0.
skip und Zeilen, in denen original "no" ist (Funktionen, die du ergänzt hast),
bleiben außerhalb des Werts und werden getrennt aufgelistet, damit die Zahl
immer nur Parität misst.

Mit --visual werden die Layout-Werte aus imgdiff.py --json gemittelt und neben
dem Funktionswert ausgegeben, und der Gesamtwert ist 80 % Funktionen + 20 %
Layout. Wofür Nutzer bezahlen, sind Funktionen.
"""

import argparse
import csv
import json
import sys

WEIGHT = {"must": 3, "should": 2, "could": 1, "p0": 3, "p1": 2, "p2": 1}
CREDIT = {"yes": 1.0, "done": 1.0, "partial": 0.5, "no": 0.0, "": 0.0, "todo": 0.0}
PRIORITY_NAME = {3: "must", 2: "should", 1: "could"}


class MatrixError(Exception):
    pass


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise MatrixError("%s ist leer" % path)
        fields = [f.strip().lower() for f in reader.fieldnames]
        for need in ("feature", "priority", "clone"):
            if need not in fields:
                raise MatrixError("%s hat keine Spalte '%s'. Nötige Spalten: "
                                  "feature, area, priority, original, clone, notes"
                                  % (path, need))
        rows = []
        for i, raw in enumerate(reader, start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            if not row.get("feature"):
                continue
            row["line"] = i
            rows.append(row)
    return rows


def score(rows):
    counted = []
    skipped = []
    extras = []
    problems = []
    for row in rows:
        original = row.get("original", "yes").lower() or "yes"
        clone = row.get("clone", "").lower()
        prio = row.get("priority", "").lower()
        if original in ("no", "n", "false"):
            extras.append(row)
            continue
        if clone == "skip":
            skipped.append(row)
            continue
        if prio not in WEIGHT:
            problems.append("Zeile %d: priority '%s' ist nicht must/should/could, "
                            "wird als could gezählt" % (row["line"], row.get("priority", "")))
        if clone not in CREDIT:
            problems.append("Zeile %d: clone '%s' ist nicht yes/partial/no/skip, "
                            "wird als no gezählt" % (row["line"], row.get("clone", "")))
        w = WEIGHT.get(prio, 1)
        c = CREDIT.get(clone, 0.0)
        counted.append(dict(row, weight=w, credit=c))

    total = sum(r["weight"] for r in counted)
    got = sum(r["weight"] * r["credit"] for r in counted)
    feature_score = 100.0 * got / total if total else 0.0

    areas = {}
    for r in counted:
        a = r.get("area") or "(kein Bereich)"
        t = areas.setdefault(a, [0.0, 0.0, 0])
        t[0] += r["weight"] * r["credit"]
        t[1] += r["weight"]
        t[2] += 1
    by_area = sorted(
        ({"area": a, "score": round(100.0 * g / t, 1) if t else 0.0, "features": n}
         for a, (g, t, n) in areas.items()),
        key=lambda d: d["score"])

    missing = [r for r in counted if r["credit"] < 1.0]
    missing.sort(key=lambda r: (-r["weight"], r["credit"], r.get("area", ""), r["feature"]))

    def brief(r):
        return {"feature": r["feature"], "area": r.get("area", ""),
                "priority": PRIORITY_NAME.get(r.get("weight", WEIGHT.get(
                    r.get("priority", "").lower(), 1)), "could"),
                "clone": r.get("clone", "") or "no", "notes": r.get("notes", "")}

    musts = [r for r in counted if r["weight"] == 3]
    return {
        "feature_score": round(feature_score, 1),
        "counted": len(counted),
        "must_have_done": sum(1 for r in musts if r["credit"] == 1.0),
        "must_have_total": len(musts),
        "by_area": by_area,
        "missing": [brief(r) for r in missing],
        "skipped": [brief(r) for r in skipped],
        "extras": [brief(r) for r in extras],
        "problems": problems,
    }


def visual_scores(paths):
    scores = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        if "score" not in data:
            raise MatrixError("%s ist keine Ausgabe von imgdiff.py --json" % p)
        name = data.get("files", {}).get("clone", p)
        scores.append({"file": name, "score": float(data["score"]),
                       "mode": data.get("mode", "layout")})
    return scores


def combine(result, visuals):
    if visuals:
        layout = sum(v["score"] for v in visuals) / len(visuals)
        result["visual"] = visuals
        result["layout_score"] = round(layout, 1)
        result["overall"] = round(0.8 * result["feature_score"] + 0.2 * layout, 1)
    else:
        result["overall"] = result["feature_score"]
    return result


def render(result, markdown=False):
    out = []
    h = "## " if markdown else ""
    out.append("%sParität: %.1f / 100" % (h, result["overall"]))
    out.append("")
    out.append("Funktionen %.1f  (%d gezählt, Must-haves %d von %d erledigt)" % (
        result["feature_score"], result["counted"], result["must_have_done"],
        result["must_have_total"]))
    if "layout_score" in result:
        out.append("Layout     %.1f  (%d Bildschirme verglichen)" % (
            result["layout_score"], len(result["visual"])))
    if result["must_have_done"] < result["must_have_total"]:
        out.append("")
        out.append("Noch nicht auslieferbar: %d Must-have-Funktionen sind nicht erledigt."
                   % (result["must_have_total"] - result["must_have_done"]))
    out.append("")
    out.append("%sNach Bereich, der schwächste zuerst" % h)
    for a in result["by_area"]:
        out.append("- %-28s %5.1f  (%d Funktionen)" % (a["area"], a["score"], a["features"]))
    out.append("")
    out.append("%sFehlt, in Baureihenfolge" % h)
    if not result["missing"]:
        out.append("- nichts. Jede gezählte Funktion ist erledigt.")
    for m in result["missing"]:
        note = ("  (%s)" % m["notes"]) if m["notes"] else ""
        out.append("- [%s] %s: %s, %s%s" % (m["priority"], m["area"] or "-",
                                             m["feature"], m["clone"], note))
    if result["skipped"]:
        out.append("")
        out.append("%sBewusst weggelassen (nicht gewertet)" % h)
        for m in result["skipped"]:
            out.append("- %s: %s" % (m["feature"], m["notes"] or "kein Grund genannt, ergänze einen"))
    if result["extras"]:
        out.append("")
        out.append("%sDeine, nicht im Original (nicht gewertet)" % h)
        for m in result["extras"]:
            out.append("- %s" % m["feature"])
    if result.get("visual"):
        out.append("")
        out.append("%sBildschirme" % h)
        for v in sorted(result["visual"], key=lambda d: d["score"]):
            out.append("- %-40s %5.1f" % (v["file"], v["score"]))
    if result["problems"]:
        out.append("")
        out.append("%sIn der Matrix beheben" % h)
        for p in result["problems"]:
            out.append("- %s" % p)
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("matrix", help="die CSV der Funktionsmatrix")
    ap.add_argument("--visual", nargs="*", default=[],
                    help="Ausgaben von imgdiff.py --json, die eingerechnet werden")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--fail-under", type=float)
    args = ap.parse_args(argv)
    try:
        result = combine(score(load(args.matrix)), visual_scores(args.visual))
    except (MatrixError, OSError, ValueError) as exc:
        print("parity: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result, markdown=args.markdown))
    if args.fail_under is not None and result["overall"] < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
