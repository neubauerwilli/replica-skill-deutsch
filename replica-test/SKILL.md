---
name: replica-test
description: >-
  Klickt jeden Ablauf eines App-Klons durch und prüft ihn auf Fehler: ein aus
  den Abläufen der Erkundung erzeugter Testplan mit Idealwegen und Randfällen,
  Playwright-End-to-End-Tests, wo es geht, ein Durchklicken im Browser, wo
  nicht, und Fehlerberichte in festem Format mit Schweregrad, Schritten und
  Beleg. Nutze den Skill, wenn der Nutzer sagt: "teste meinen Klon", "finde
  Fehler", "mach QA", "klick alles durch", "schreib E2E-Tests", "funktioniert
  es", oder nachdem /replica-bau oder /replica-backend fertig ist.
---

# replica-test

Liest die Abläufe in `replica/recon.md`. Schreibt `replica/test-plan.md`,
`replica/bugs.md` und End-to-End-Tests im Projekt (`e2e/`). Vorlagen in diesem
Ordner: `test-plan.md`, `bug-report.md`, `e2e.example.spec.ts`.

## Die Regel

**Teste deinen Klon, nicht das Original.** Mach nie Lasttests, Fuzzing,
Skripte oder Dauerfeuer gegen die Server der Original-App. Das Original von
Hand zu benutzen, wie ein normaler Nutzer, um sein Verhalten zu sehen, ist in
Ordnung.

## Schritt 1: der Plan

Schreib für jeden Ablauf F01, F02... der Erkundungskarte:

- **Idealweg**: die Schritte und was der Nutzer am Ende sehen soll.
- **Randfälle**, die passen. Geh diese Liste für jeden Ablauf durch:
  leere Eingabe, sehr lange Eingabe, Emoji und Akzente, zwei Tabs gleichzeitig,
  Doppelklick auf Absenden, Zurück-Taste mitten im Ablauf, Neuladen mitten im
  Ablauf, langsames Netz, offline, abgelaufene Sitzung, Daten eines zweiten
  Nutzers (müssen unsichtbar sein), Zeitzonen und Sommerzeit, mobile Breite,
  nur Tastatur, Labels für Screenreader.
- **Negativfälle**: falsches Passwort, Karte abgelehnt (Stripe-Testkarte
  `4000 0000 0000 0002`), Berechtigung verweigert, gelöschter Datensatz.

Nummeriere jeden Fall: F01-H1, F01-E3, F01-N2.

## Schritt 2: automatisieren, was geht

Playwright, eine Spec pro Ablauf, gegen den lokalen Dev-Server mit Startdaten.
Nimm für Selektoren Rollen und Labels (`getByRole('button', { name: 'Buchen' })`),
nie CSS-Klassen. Siehe `e2e.example.spec.ts`.

```bash
npm i -D @playwright/test && npx playwright install chromium
npx playwright test
```

Füge jeder Spec hinzu: bei Konsolenfehlern fehlschlagen, bei jeder
5xx-Antwort fehlschlagen und ein axe-Barrierefreiheitsscan
(`@axe-core/playwright`) auf jedem Bildschirm.

## Schritt 3: den Rest durchklicken

Was sich nicht automatisieren lässt (ankommende E-Mails, OAuth mit echten
Anbietern, Zahlungen von Anfang bis Ende, optische Fehler), bekommt einen
manuellen Durchgang. Ist ein Browser-Werkzeug verfügbar, steuere den lokalen
Klon damit und mach von jedem Schritt einen Screenshot. Sonst gib dem Nutzer
die Checkliste und warte auf Antworten.

## Schritt 4: Fehler melden

Jeder Fehler kommt in `replica/bugs.md` im Format von `bug-report.md`: eine ID,
ein Schweregrad, genaue Schritte, erwartet, tatsächlich, Beleg. Schweregrad:

| | bedeutet |
| --- | --- |
| S1 | Datenverlust, Sicherheitslücke, falsche Zahlungen, Kernablauf blockiert |
| S2 | eine Funktion kaputt, keine Umgehung |
| S3 | kaputt mit Umgehung, oder sichtbar falsch |
| S4 | kosmetisch |

Melde nur, was du reproduziert hast. "Könnte ein Problem sein" kommt auf eine
eigene Liste "zu prüfen".

## Schritt 5: Korrekturschleife

Behebe zuerst S1 und S2. Bei jeder Korrektur: erst den fehlschlagenden Test
schreiben, dann beheben, zusehen, wie er besteht, und den Test behalten. Lass
nach jeder Gruppe die ganze Suite neu laufen. Trag in `bugs.md` den Commit
ein, der jeden Fehler behoben hat.

## Ergebnis

`test-plan.md`, die Specs, `bugs.md` und eine Zusammenfassung: durchgeführte
Fälle, bestanden, fehlgeschlagen, Fehler nach Schweregrad, bisher behoben.
Liefere nichts mit einem offenen S1 aus. Weiter mit: `/replica-vergleich`.
