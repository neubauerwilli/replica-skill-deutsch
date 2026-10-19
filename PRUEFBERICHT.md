# Sicherheits- und Funktionsprüfung (19.10.2026)

Geprüft wurde die deutsche Fassung ab Commit `d840022` und die daraus
überarbeitete Version 1.0.1. Umfang: alle elf Anleitungen, sechs
Python-Werkzeuge, Plugin- und Marketplace-Manifest, Installationstexte und
Playwright-Vorlagen. Die Prüfung ersetzt keinen Sicherheitstest einer
später mit den Skills erzeugten App.

## Reproduzierte Fehler und Korrekturen

| Befund | Korrektur und Nachweis |
| --- | --- |
| Der Deploy-Aufruf der Paritätsanalyse gab auch bei fehlenden Must-haves Exit 0 zurück. | Neue Option `--require-ready`; Livegang-Anleitung und Checkliste nutzen sie. Leere/fehlerhafte Matrizen und ein Funktionswert unter 80 blockieren ebenfalls. |
| Ein nicht vorhandener Sweep-Ordner wurde als sauber gemeldet; Lesefehler und große Textdateien wurden übergangen. | Fehlendes Ziel, unvollständige Prüfung und Verknüpfungen liefern einen Fehler statt einer Freigabe. |
| Sweep-Treffer aus `.env.local` enthielten den vollständigen Wert einer fiktiven Geheimniszeile. | `.env` und bekannte Schlüsseldateien werden nicht gelesen. Ausnahmen vom Prüfbereich werden benannt. |
| PNG-Daten wurden unbegrenzt entpackt; Prüfsummen und Blocklängen waren ungeprüft. | Größen-/Pixellimit, begrenztes Entpacken, Prüfung von CRC, Blocklängen, Format und Datenmenge. Beschädigte Bilder werden abgelehnt. |
| Der Layoutvergleich übersah bei bestimmten Breiten den rechten Bildrand. | Raster deckt die gesamte Breite ab; Regression mit einem 13 Pixel breiten Bild. |
| Eine Diff-Ausgabe konnte das Eingabebild überschreiben. | Gleiche aufgelöste Eingabe-/Ausgabepfade werden abgelehnt. |
| Falsche JSON-Typen und CSV-Zeilen mit zusätzlichen Feldern führten zu Tracebacks. | Eingabeschemata und verständliche Fehlermeldungen mit Exit 2. |
| Ungültige Kontrastpaare konnten zu null Prüfungen und Exit 0 führen. | Form, Tokennamen und Größenangaben werden geprüft. |
| `--avoid` ersetzte im Store-Prüfer die bereits konfigurierte Ausschlussliste. | Listen werden zusammengeführt; Pflichtfelder nur aus Leerraum zählen als leer. |
| Bewertungslinks ohne Host wurden akzeptiert; fremdes HTML und Bild-Markdown erschienen unverändert im Bericht. | URL-Validierung, keine Zugangsdaten in Links, sichere Markdown-Ausgabe; Rohtext im JSON bleibt erhalten. |
| Installierte Skripte wurden über unzuverlässige relative Pfade aufgerufen. | Quotierte Pfade über den jeweiligen Skillordner; Projektdaten bleiben im Projekt. |
| Der E2E-Beispieltest behauptete genau eine Buchung, ohne die Zahl gespeicherter Buchungen zu prüfen. | Als offen übersprungen, bis der projektspezifische API-/Datenbanknachweis ergänzt ist. |
| Der E2E-Installationsbefehl ließ das importierte axe-Paket aus. | Beide benötigten Pakete werden genannt; lokale Playwright-Konfiguration ergänzt. |

Die elf Anleitungen behandeln Fremdinhalte ausdrücklich als Daten. Prüfaufträge
erlauben keine echten Käufe, Erstattungen, Versandaktionen oder Änderungen an
Produktionsdaten. Bestehende konkrete Veröffentlichungsaufträge bleiben gültig.

## Tatsächlich ausgeführt

- Ursprüngliche Suite: 58 Tests bestanden.
- Erweiterte Suite: 79 Tests bestanden unter Windows mit Python 3.12.
  Die neuen Regressionen wurden vor den Korrekturen mit Fehlern beobachtet.
- `claude plugin validate` für beide Manifeste: bestanden, Claude Code 2.1.296.
- Laden über `--plugin-dir`: alle elf Skills im tatsächlichen
  Claude-Code-Register mit dem Namensraum `replica-skill-deutsch` erkannt.
- Verhaltenstest mit einem erfundenen Produktionsszenario: `replica-test`
  verlangte eine lokale Umgebung mit Testdaten und führte keine Aktion aus.
  Dies ist ein KI-Verhaltenstest, kein echter Nutzer- oder Produktionstest.
- Playwright-Vorlage gegen eine isolierte, fiktive lokale Buchungsseite:
  Idealweg bestanden, axe-Prüfung der angezeigten Zustände bestanden.
  Der noch anzupassende Idempotenztest blieb ausdrücklich übersprungen.
- Zwei absichtlich fehlerhafte Varianten dieser Demo: Konsolenfehler und
  HTTP 503 wurden beide vom Test erkannt.
- Quellprüfung der sechs Python-Werkzeuge: keine Netzwerk- oder
  Shell-Ausführung gefunden. Suche nach typischen eingebetteten
  Zugangsschlüssel-Signaturen: keine Treffer. Dies ist kein vollständiger
  Geheimnisscanner.

Die Suite läuft zusätzlich per GitHub Actions auf Windows und Linux mit
Python 3.10 und 3.13. Ein konfigurierter Workflow ist erst durch seine
tatsächlichen GitHub-Ergebnisse bestätigt.

## Noch offen und Grenzen

- Kein vollständiger App-Neubau und kein Test fremder Original-Apps.
- Keine dauerhafte Marketplace-Installation im Nutzerprofil vorgenommen;
  Manifeste und Laden als lokales Plugin wurden tatsächlich geprüft.
- Keine echten Konten, Zahlungen, E-Mails, OAuth-Verbindungen oder
  Produktionsdatenbanken getestet.
- Der Sweep prüft Textdateien innerhalb seines benannten Bereichs. Bilder,
  ausgelieferte Build-Dateien, Geheimnisdateien und Referenzmaterial brauchen
  eigene Kontrollen. Er ist kein vollständiger Marken- oder Geheimnisscanner.
- Der Layoutwert ist ein Rastervergleich; funktionale Gleichheit und
  unterschiedliche Bildhöhen müssen zusätzlich beurteilt werden.
- Eigene `--themes`-Dateien enthalten reguläre Ausdrücke. Nur geprüfte lokale
  Konfigurationen verwenden; fremde Muster nicht ungeprüft übernehmen.
- Schutzregeln in Anleitungen verringern Fehlverhalten, bilden aber keine
  technische Isolation. Der spätere Agent und die App benötigen eigene Rechte
  und Prüfungen. Eine Garantie vollständiger Fehlerfreiheit wird nicht behauptet.

Grundlagen zur Pluginstruktur und Pfadauflösung:
[Claude-Code-Manifestreferenz](https://code.claude.com/docs/en/plugins-reference),
[Claude-Code-Skills](https://code.claude.com/docs/en/skills).
