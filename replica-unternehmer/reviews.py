#!/usr/bin/env python3
"""Feedback-Ranking für replica-unternehmer. Nur Standardbibliothek.

Nimmt die echten Bewertungen, die du zur nachgebauten App gesammelt hast, und
ordnet, was ihre Nutzer hassen und wonach sie immer wieder fragen, mit den
genauen Worten und einem Link zu jeder Aussage.

    python3 reviews.py replica/reviews.csv
    python3 reviews.py replica/reviews.csv --out replica/feedback.md
    python3 reviews.py replica/reviews.csv --json
    python3 reviews.py replica/reviews.csv --themes meine-themen.json

Die CSV braucht diese Spalten (weitere Spalten werden ignoriert):

    source   woher es kam: app-store, google-play, g2, capterra,
             trustpilot, reddit, hacker-news, product-hunt, ...
    url      der Link zur Bewertung oder zum Thread. Pflicht.
    date     JJJJ-MM-TT, wenn du es hast (JJJJ-MM reicht)
    rating   1 bis 5 Sterne, wenn die Quelle Sterne hat, sonst leer
    text     die Bewertung, exakt kopiert. Pflicht.

Eine Zeile ohne url oder ohne text wird verworfen und mitgezählt, nie erraten.
Das Werkzeug ordnet nur neu, was du ihm gibst. Es schreibt keine Bewertungen,
es umschreibt sie nicht, und jedes Zitat, das es ausgibt, ist ein Teilstück
einer Zeile, die du geliefert hast, mit dem Link dieser Zeile.

So wird ein Thema gerankt: Jede passende Bewertung fügt ein Gewicht hinzu. Eine
Bewertung mit 1 Stern fügt 1,0 hinzu, eine mit 5 Sternen 0,2, eine ohne Sterne
0,6. Bewertungen, die älter als --months (Standard 18) sind, zählen halb.
Themen mit weniger als 3 Bewertungen oder nur aus einer Quelle gelten als dünn.
"""

import argparse
import csv
import datetime as _dt
import html
import json
import os
import re
import sys
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_THEMES = os.path.join(HERE, "themes.json")
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


class FeedbackError(Exception):
    pass


def load_themes(path=DEFAULT_THEMES):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("themes"), list):
        raise FeedbackError("Themen-Datei braucht ein Objekt mit einer themes-Liste")
    themes = []
    ids = set()
    for t in data.get("themes", []):
        if not isinstance(t, dict) or not isinstance(t.get("id"), str) or not t["id"].strip():
            raise FeedbackError("jedes Thema braucht eine id als Text")
        if t["id"] in ids:
            raise FeedbackError("doppelte Themen-id: %s" % t["id"])
        ids.add(t["id"])
        for key in ("label", "kind"):
            if key in t and not isinstance(t[key], str):
                raise FeedbackError("%s muss Text sein" % key)
        patterns = t.get("patterns", [])
        if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
            raise FeedbackError("patterns muss eine Liste von regulären Ausdrücken sein")
        themes.append({
            "id": t["id"], "label": t.get("label", t["id"]),
            "kind": t.get("kind", "complaint"),
            "patterns": [re.compile(p, re.I) for p in t.get("patterns", [])],
        })
    request_patterns = data.get("request_patterns", [])
    if not isinstance(request_patterns, list) or not all(isinstance(p, str) for p in request_patterns):
        raise FeedbackError("request_patterns muss eine Liste von regulären Ausdrücken sein")
    requests = [re.compile(p, re.I) for p in request_patterns]
    return themes, requests


def parse_date(text):
    text = (text or "").strip()
    for fmt, n in (("%Y-%m-%d", 10), ("%Y-%m", 7)):
        try:
            return _dt.datetime.strptime(text[:n], fmt).date()
        except ValueError:
            continue
    return None


def parse_rating(text):
    text = (text or "").strip()
    if not text:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    value = float(m.group(1))
    if value < 1 or value > 5:
        return None
    return value


def load_reviews(path):
    """Gibt (behaltene Zeilen, Zahl verworfener, Zahl doppelter) zurück."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise FeedbackError("%s ist leer" % path)
        cols = [c.strip().lower() for c in reader.fieldnames]
        for need in ("url", "text"):
            if need not in cols:
                raise FeedbackError(
                    "%s hat keine Spalte '%s'. Jede Bewertung braucht den Link, von "
                    "dem sie stammt, und ihren genauen Text: source,url,date,rating,text"
                    % (path, need))
        kept, dropped, dupes = [], 0, 0
        seen = set()
        for i, raw in enumerate(reader, start=2):
            if None in raw:
                raise FeedbackError("Zeile %d: zu viele CSV-Felder; Bewertungstext mit Kommas in Anführungszeichen setzen" % i)
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            url, text = row.get("url", ""), row.get("text", "")
            try:
                parsed = urlsplit(url)
                valid_url = (parsed.scheme in ("http", "https") and parsed.hostname and
                             not parsed.username and not parsed.password and
                             not any(ch.isspace() or ch in '<>"' for ch in url))
            except ValueError:
                valid_url = False
            if not valid_url or not text:
                dropped += 1
                continue
            key = re.sub(r"\W+", " ", text.lower()).strip()
            if key in seen:
                dupes += 1
                continue
            seen.add(key)
            kept.append({
                "line": i,
                "source": row.get("source", "") or _host(url),
                "url": url,
                "date": parse_date(row.get("date", "")),
                "rating": parse_rating(row.get("rating", "")),
                "text": text,
            })
    return kept, dropped, dupes


def _host(url):
    m = re.match(r"^https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else "unbekannt"


def weight(review, today, months):
    r = review["rating"]
    w = 0.6 if r is None else (6.0 - r) / 5.0
    if review["date"] is not None and today is not None:
        age_days = (today - review["date"]).days
        if age_days > months * 30.4:
            w *= 0.5
    return w


def snippet(text, pattern, limit=220):
    """Der erste Satz des Textes, der auf das Muster passt, wörtlich."""
    for sent in SENTENCE.split(text):
        if pattern.search(sent):
            s = sent.strip()
            if len(s) > limit:
                m = pattern.search(s)
                start = max(0, m.start() - limit // 2)
                s = s[start:start + limit].strip()
                s = ("..." if start > 0 else "") + s + "..."
            return s
    s = text.strip()
    return s if len(s) <= limit else s[:limit].rstrip() + "..."


def analyse(reviews, themes, request_patterns, today=None, months=18):
    if today is None:
        today = _dt.date.today()
    results = {t["id"]: {"id": t["id"], "label": t["label"], "kind": t["kind"],
                         "reviews": [], "score": 0.0} for t in themes}
    requests = []
    unthemed_negative = []
    for rv in reviews:
        w = weight(rv, today, months)
        matched = False
        for t in themes:
            hit = next((p for p in t["patterns"] if p.search(rv["text"])), None)
            if hit is None:
                continue
            matched = True
            res = results[t["id"]]
            res["score"] += w
            res["reviews"].append({"rv": rv, "quote": snippet(rv["text"], hit)})
        req = next((p for p in request_patterns if p.search(rv["text"])), None)
        if req is not None:
            requests.append({"quote": snippet(rv["text"], req), "url": rv["url"],
                             "source": rv["source"], "rating": rv["rating"]})
        if not matched and rv["rating"] is not None and rv["rating"] <= 2:
            unthemed_negative.append(rv)

    total = len(reviews) or 1
    ranked = []
    for res in results.values():
        items = res["reviews"]
        if not items:
            continue
        rated = [x["rv"]["rating"] for x in items if x["rv"]["rating"] is not None]
        sources = sorted({x["rv"]["source"] for x in items})
        # Zuerst die schlechteste Bewertung, dann die kürzeste, damit die gezeigten Zitate am schärfsten sind.
        items.sort(key=lambda x: (x["rv"]["rating"] if x["rv"]["rating"] is not None else 3,
                                  len(x["quote"])))
        ranked.append({
            "id": res["id"], "label": res["label"], "kind": res["kind"],
            "score": round(res["score"], 2),
            "count": len(items),
            "share_pct": round(100.0 * len(items) / total, 1),
            "avg_rating": round(sum(rated) / len(rated), 2) if rated else None,
            "sources": sources,
            "thin": len(items) < 3 or len(sources) < 2,
            "quotes": [{"quote": x["quote"], "url": x["rv"]["url"],
                        "source": x["rv"]["source"], "rating": x["rv"]["rating"]}
                       for x in items[:3]],
        })
    ranked.sort(key=lambda d: (-d["score"], -d["count"], d["id"]))
    return {
        "reviews": len(reviews),
        "sources": sorted({r["source"] for r in reviews}),
        "rated": sum(1 for r in reviews if r["rating"] is not None),
        "themes": ranked,
        "requests": requests,
        "unthemed_negative": [{"url": r["url"], "source": r["source"],
                               "rating": r["rating"], "text": r["text"][:220]}
                              for r in unthemed_negative],
    }


def _stars(r):
    return "-" if r is None else ("%g*" % r)


def safe_text(text):
    """Fremdtext bleibt im Markdown sichtbar, erzeugt aber keine HTML-/Bild-Elemente."""
    text = html.escape(" ".join(str(text).split()), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#!|>])", r"\\\1", text)


def render(result, dropped=0, dupes=0):
    out = ["# Was die Nutzer des Originals hassen und wollen", ""]
    out.append("%d Bewertungen aus %d Quellen (%s). %d hatten Sternebewertungen." % (
        result["reviews"], len(result["sources"]), safe_text(", ".join(result["sources"])) or "keine",
        result["rated"]))
    if dropped:
        out.append("%d Zeilen verworfen: kein Link oder kein Text. Nichts wird ohne "
                   "seine Quelle gezählt." % dropped)
    if dupes:
        out.append("%d doppelte Bewertungen entfernt." % dupes)
    if result["reviews"] < 30:
        out.append("")
        out.append("Kleine Stichprobe. Unter 30 Bewertungen stützen eine Richtung, "
                   "kein Ranking. Sammle mehr, bevor du die Roadmap darauf setzt.")
    for kind, title in (("complaint", "Was sie hassen"), ("request", "Wonach sie fragen")):
        rows = [t for t in result["themes"] if t["kind"] == kind]
        out.append("")
        out.append("## %s" % title)
        out.append("")
        if not rows:
            out.append("Nichts passte. Lies die Bewertungen von Hand.")
            continue
        out.append("| Rang | Thema | Wert | Bewertungen | Anteil | Ø Sterne | Quellen |")
        out.append("| --- | --- | --- | --- | --- | --- | --- |")
        for i, t in enumerate(rows, 1):
            out.append("| %d | %s%s | %.1f | %d | %.0f%% | %s | %d |" % (
                i, safe_text(t["label"]), " (dünn)" if t["thin"] else "", t["score"], t["count"],
                t["share_pct"], "-" if t["avg_rating"] is None else "%.1f" % t["avg_rating"],
                len(t["sources"])))
        for t in rows[:6]:
            out.append("")
            out.append("**%s**" % safe_text(t["label"]))
            for q in t["quotes"]:
                out.append('- "%s" (%s, %s) <%s>' % (safe_text(q["quote"]), safe_text(q["source"]),
                                                   _stars(q["rating"]), q["url"]))
    if result["requests"]:
        out.append("")
        out.append("## Gewünscht in ihren eigenen Worten")
        out.append("")
        for q in result["requests"][:25]:
            out.append('- "%s" (%s, %s) <%s>' % (safe_text(q["quote"]), safe_text(q["source"]),
                                               _stars(q["rating"]), q["url"]))
    if result["unthemed_negative"]:
        out.append("")
        out.append("## Lies diese von Hand")
        out.append("")
        out.append("Niedrige Bewertungen, die zu keinem Thema passten. Entweder Rauschen "
                   "oder ein Thema, das themes.json noch nicht hat. Oft der nützlichste Teil.")
        out.append("")
        for r in result["unthemed_negative"][:15]:
            out.append('- (%s, %s) <%s>: "%s"' % (safe_text(r["source"]), _stars(r["rating"]),
                                               r["url"], safe_text(r["text"])))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("reviews", help="CSV mit source,url,date,rating,text")
    ap.add_argument("--themes", default=DEFAULT_THEMES)
    ap.add_argument("--months", type=int, default=18,
                    help="ältere Bewertungen zählen halb (Standard 18)")
    ap.add_argument("--today", help="JJJJ-MM-TT, für reproduzierbare Läufe")
    ap.add_argument("--out", help="den Markdown-Bericht hierhin schreiben")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        if args.months <= 0:
            raise FeedbackError("--months muss positiv sein")
        if args.today and (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.today) or parse_date(args.today) is None):
            raise FeedbackError("--today braucht ein gültiges Datum JJJJ-MM-TT")
        themes, req = load_themes(args.themes)
        reviews, dropped, dupes = load_reviews(args.reviews)
    except (FeedbackError, OSError, ValueError, KeyError, re.error) as exc:
        print("reviews: %s" % exc, file=sys.stderr)
        return 2
    if not reviews:
        print("reviews: keine brauchbaren Zeilen. Jede Zeile braucht eine url (http...) "
              "und den Bewertungstext.", file=sys.stderr)
        return 2
    today = parse_date(args.today) if args.today else None
    result = analyse(reviews, themes, req, today=today, months=args.months)
    result["dropped"] = dropped
    result["duplicates"] = dupes
    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0
    text = render(result, dropped, dupes)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            print("reviews: %s" % exc, file=sys.stderr)
            return 2
        print("geschrieben: %s" % args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
