#!/usr/bin/env python3
"""Prüfer für Store-Einträge zu replica-start. Nur Standardbibliothek.

Prüft einen Eintrag für App Store und Google Play gegen die Feldlimits der
Stores und gegen die Fehler, an denen ein Klon abgelehnt wird: der Name der
Original-App in deinen Metadaten, Ranking-Versprechen im Titel, verschwendete
Keyword-Zeichen.

    python3 listing.py replica/launch/listing.json
    python3 listing.py listing.json --avoid "Calendly,Acuity Scheduling"
    python3 listing.py listing.json --json

listing.json (siehe listing.example.json):

    {
      "avoid": ["Name der Original-App", "Seine Firma"],
      "app_store":   {"name", "subtitle", "promotional_text", "description",
                      "keywords", "whats_new"},
      "google_play": {"title", "short_description", "full_description"}
    }

Lass einen Store weg, in den du nicht gehst. Exit-Code 1 bei jedem Fehler, 0,
wenn es nur Warnungen gibt.
"""

import argparse
import json
import re
import sys
import unicodedata

LIMITS = {
    "app_store": {"name": 30, "subtitle": 30, "promotional_text": 170,
                  "description": 4000, "keywords": 100, "whats_new": 4000},
    "google_play": {"title": 30, "short_description": 80, "full_description": 4000},
}
SHORT_FIELDS = {"name", "subtitle", "title", "short_description"}
CLAIMS = re.compile(
    r"(#\s?1\b|\bnumber one\b|\bno\.? ?1\b|\bbest\b|\btop[- ]rated\b|\b(app|game) of the year\b"
    r"|\bfree\b|\bdiscount\b|\bsale\b|\b\d+% off\b|\bnew!?$"
    r"|\bnummer eins\b|\bnr\.? ?1\b|\bbeste[rnms]?\b|\btop[- ]bewertet\b"
    r"|\b(app|spiel) des jahres\b|\bkostenlos\b|\bgratis\b|\brabatt\b|\bangebot\b"
    r"|\b\d+ ?% rabatt\b|\bneu!?$)", re.I)
STOP = {"a", "an", "and", "app", "for", "the", "to", "of", "with", "your", "you", "in", "on", "&",
        "und", "für", "der", "die", "das", "mit", "dein", "deine", "ein", "eine", "zu", "im", "auf"}


def length(text):
    """Zeichen, wie ein Mensch sie zählt (ein aus Teilen gebautes Emoji ist eines)."""
    text = unicodedata.normalize("NFC", text or "")
    count = 0
    prev_joiner = False
    for ch in text:
        cat = unicodedata.category(ch)
        if ch == "‍":
            prev_joiner = True
            continue
        if cat in ("Mn", "Me") or ch in ("️", "︎") or 0x1F3FB <= ord(ch) <= 0x1F3FF:
            continue
        if prev_joiner:
            prev_joiner = False
            continue
        count += 1
    return count


def has_emoji(text):
    return any(unicodedata.category(ch) == "So" or ord(ch) >= 0x1F000 for ch in text or "")


def words(text):
    return [w for w in re.findall(r"[a-zäöüß0-9']+", (text or "").lower()) if w not in STOP]


def lint(listing, avoid=None):
    if not isinstance(listing, dict):
        raise ValueError("Eintrag muss ein JSON-Objekt sein")
    configured = listing.get("avoid", [])
    if not isinstance(configured, list) or not all(isinstance(a, str) for a in configured):
        raise ValueError("avoid muss eine Liste von Namen sein")
    issues = []
    avoid = [a.strip() for a in configured + (avoid or []) if a.strip()]

    def add(level, store, field, msg):
        issues.append({"level": level, "store": store, "field": field, "message": msg})

    found_store = False
    for store, limits in LIMITS.items():
        data = listing.get(store)
        if data is not None and (not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values())):
            raise ValueError("%s muss ein Objekt mit Textfeldern sein" % store)
        if not data:
            continue
        found_store = True
        for field, limit in limits.items():
            value = data.get(field, "")
            n = length(value)
            if not value.strip():
                level = "error" if field in ("name", "title", "description",
                                             "full_description") else "warn"
                add(level, store, field, "leer")
                continue
            if n > limit:
                add("error", store, field, "%d Zeichen, das Limit ist %d (%d zu viel)"
                    % (n, limit, n - limit))
            for name in avoid:
                if re.search(r"(?<!\w)%s(?!\w)" % re.escape(name), value, re.I):
                    add("error", store, field,
                        "nennt '%s'. Der Name oder die Marke einer anderen App in "
                        "deinen Metadaten führt zur Ablehnung des Eintrags und lädt "
                        "zu einer Abmahnung ein. Beschreibe stattdessen, was deine "
                        "App tut." % name)
            if field in SHORT_FIELDS:
                m = CLAIMS.search(value)
                if m:
                    add("warn", store, field,
                        "'%s' liest sich wie ein Ranking- oder Preisversprechen. "
                        "Google Play verbietet das in Titel und Kurzbeschreibung, "
                        "und Apple lehnt Versprechen ab, die du nicht belegen "
                        "kannst." % m.group(0).strip())
                if has_emoji(value):
                    add("warn", store, field, "Emoji in einem kurzen Feld. Play lehnt "
                        "sie in Titeln ab; auch App-Store-Prüfer tun das oft.")
                caps = re.findall(r"\b[A-Z]{4,}\b", value)
                if caps:
                    add("warn", store, field, "Wort(e) in Großbuchstaben: %s" % ", ".join(caps))
        if store == "app_store" and data.get("keywords"):
            kw_raw = data["keywords"]
            parts = [k.strip().lower() for k in kw_raw.split(",")]
            if re.search(r",\s", kw_raw):
                add("warn", store, "keywords", "Leerzeichen nach Kommas verschwenden Zeichen. "
                    "Schreibe wort1,wort2,wort3")
            dupes = sorted({k for k in parts if k and parts.count(k) > 1})
            if dupes:
                add("warn", store, "keywords", "doppelt: %s" % ", ".join(dupes))
            in_name = set(words(data.get("name", "")) + words(data.get("subtitle", "")))
            wasted = sorted({w for k in parts for w in words(k) if w in in_name})
            if wasted:
                add("warn", store, "keywords", "schon im Namen oder Untertitel enthalten, "
                    "diese Zeichen sind also verschwendet: %s" % ", ".join(wasted))
            if any(not k for k in parts):
                add("warn", store, "keywords", "leerer Eintrag (doppeltes oder abschließendes Komma)")
    if not found_store:
        add("error", "-", "-", "kein Abschnitt app_store oder google_play gefunden")
    return issues


def render(listing, issues):
    out = []
    for store, limits in LIMITS.items():
        data = listing.get(store)
        if not data:
            continue
        out.append(store.replace("_", " ").title())
        for field, limit in limits.items():
            n = length(data.get(field, ""))
            mark = "ZU LANG" if n > limit else ("ok" if n else "--")
            out.append("  %-18s %5d / %-5d %s" % (field, n, limit, mark))
        out.append("")
    if not issues:
        out.append("Keine Beanstandungen.")
    for i in issues:
        label = "FEHLER" if i["level"] == "error" else "WARNUNG"
        out.append("%-7s %s.%s: %s" % (label, i["store"], i["field"], i["message"]))
    errs = sum(1 for i in issues if i["level"] == "error")
    warns = len(issues) - errs
    out.append("")
    out.append("%d Fehler, %d Warnungen" % (errs, warns))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("listing", help="listing.json")
    ap.add_argument("--avoid", help="durch Komma getrennte Namen, die nicht vorkommen dürfen "
                                    "(die Original-App, ihre Firma)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        with open(args.listing, encoding="utf-8") as fh:
            listing = json.load(fh)
        avoid = args.avoid.split(",") if args.avoid else None
        issues = lint(listing, avoid)
    except (OSError, ValueError) as exc:
        print("listing: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(issues, indent=2))
    else:
        print(render(listing, issues))
    return 1 if any(i["level"] == "error" for i in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
