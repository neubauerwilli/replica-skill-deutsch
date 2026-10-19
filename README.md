# Der Replica-Skill

Elf Claude-Skills auf Deutsch, die jede App nachbauen. Kostenlos, MIT, ohne Anmeldung, ohne API-Schlüssel, nichts zu verbinden.

Das gilt für das Skill-Paket und seine sechs lokalen Python-Werkzeuge.
Claude Code sowie Hosting, Zahlungs- und E-Mail-Dienste haben eigene Voraussetzungen
und gegebenenfalls Kosten. Der Skill allein ist keine fertige App.

Einer nimmt die App auseinander, die du klonen willst. Einer baut sie neu. Einer testet sie auf Fehler. Und einer ist der Unternehmer: Er liest, was die Nutzer der App hassen, und behebt es in deiner, damit du eine App hast, die du verkaufen kannst.

Dazwischen planen die anderen Stack und Datenbank, bauen das Designsystem nach, verdrahten Login und Zahlungen, bewerten deinen Klon gegen das Original, geben ihm einen eigenen Namen und eine eigene Marke, schreiben die Landingpage und den Store-Eintrag und bringen ihn auf deine Domain.

**Er baut nach, was eine App tut, nie, was ihr gehört.** Funktionen und Abläufe, im Clean-Room-Stil. Nicht ihren Code, ihr Logo, ihre Texte oder ihre Inhalte. Das Kleingedruckte steht unten, und die Skills setzen es durch.

## Einrichten

Installiere die Skills als Plugin in [Claude Code](https://code.claude.com/docs/en/overview).
Sende dort diese zwei Befehle einzeln, prüfe die Quelle und bestätige den angezeigten Installationsstatus:

```
/plugin marketplace add neubauerwilli/replica-skill-deutsch
/plugin install replica-skill-deutsch@replica-skill-deutsch
```

Als Plugin bekommen die Skills einen Namensraum, sie heißen dann `/replica-skill-deutsch:replica-erkundung`
und so weiter. Wenn du einfach `/replica-erkundung` willst, kopiere die Ordner:

```bash
git clone https://github.com/neubauerwilli/replica-skill-deutsch.git
mkdir -p ~/.claude/skills
cp -r replica-skill-deutsch/replica-* ~/.claude/skills/
```

Nur für ein Projekt statt global: dieselben Ordner nach `.claude/skills/` in deinem Projekt kopieren.
Starte die Sitzung bei Bedarf neu. Unter `/` sollte zum Beispiel `/replica-erkundung` erscheinen.
Hilfe zur Plugininstallation: [offizielle Anleitung](https://code.claude.com/docs/en/discover-plugins).

Unter Windows PowerShell geht die manuelle Ablage so:

```powershell
git clone https://github.com/neubauerwilli/replica-skill-deutsch.git
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE/.claude/skills" | Out-Null
Copy-Item -Path 'replica-skill-deutsch/replica-*' -Destination "$env:USERPROFILE/.claude/skills" -Recurse
```

Ein GitHub-Link mit "install skill" im normalen Webchat ist kein Nachweis einer Installation.
Du kannst den Text einer einzelnen `SKILL.md` als Arbeitsanweisung einfügen.
Damit sind keine lokalen Skripte installiert oder ausgeführt. Für das vollständige Paket
verwende Claude Code und prüfe dort die angezeigten Befehle.

Die Werkzeuge brauchen Python 3.8 oder neuer. Nichts per pip installieren. Unter Windows heißt der
Aufruf oft `py` statt `python3`.

## Die elf

| Befehl | Was er macht |
| --- | --- |
| `/replica-erkundung` | Nimmt jede App auseinander: Bildschirme, Abläufe, Bausteine, Datenmodell. Aus öffentlichen Seiten, Screenshots, Store-Einträgen und deinem eigenen Konto. |
| `/replica-architekt` | Plant Stack, Datenbankschema und API für deinen Klon. |
| `/replica-design` | Baut das Designsystem nach: Farben, Schrift, Abstände, Bausteine. Als Tokens, mit deinen eigenen Assets. |
| `/replica-bau` | Baut die App Bildschirm für Bildschirm nach der Erkundungskarte nach. |
| `/replica-backend` | Auth, Datenbank, Zahlungen und Anbindungen. |
| `/replica-test` | Klickt jeden Ablauf durch und testet ihn auf Fehler. |
| `/replica-vergleich` | Vergleicht deinen Klon mit dem Original. Ein Paritätswert und was fehlt. |
| `/replica-unternehmer` | Liest in echten Bewertungen, was die Nutzer der App hassen, und macht daraus Korrekturen und einen Positionierungswinkel. |
| `/replica-marke` | Gibt deiner Version Namen und Marke, damit sie dir gehört. |
| `/replica-start` | Landingpage, Preise und App-Store-Eintrag. |
| `/replica-livegang` | Bringt sie auf deine eigene Domain. |

## So nutzt du es

Lass sie der Reihe nach laufen. Jeder liest, was der vorige geschrieben hat, in einem Ordner `replica/`
in deinem Projekt.

```
erkundung -> architekt -> design -> bau -> backend -> test -> vergleich -> unternehmer -> marke -> start -> livegang
```

Ein Beispiel: eine Terminbuchungs-App klonen, eine von der Sorte, bei der du einen Link teilst und Leute
eine Zeit mit dir buchen.

1. **`/replica-erkundung`** mit der URL der App. Er liest das Hilfecenter, die Preisseite, den
   Store-Eintrag und öffentliche Vorführungen, und du klickst mit ihm durch dein eigenes Konto. Heraus
   kommt `replica/recon.md`: 18 Bildschirme, 7 Abläufe (Gast bucht einen Termin, Gastgeber legt
   Verfügbarkeit fest, Gast verschiebt...), die Bausteine, ein abgeleitetes Datenmodell (Nutzer,
   Terminarten, Verfügbarkeit, Buchungen) und `features.csv`. Der Partner-Marktplatz ist als nicht
   im Umfang markiert: Das ist ihr Netzwerk, keine Funktion.
2. **`/replica-architekt`** wählt Next.js, Postgres, Stripe und Resend, schreibt das Schema (mit einer
   Bedingung, die verhindert, dass zwei Gäste denselben Termin buchen) und ordnet den Bau: zuerst der
   Buchungsablauf von Anfang bis Ende.
3. **`/replica-design`** misst die Screenshots in Tokens aus: Farbrollen, Schriftskala, 8-px-Abstände,
   die Spezifikationen der Datumsauswahl und der Termin-Buttons. Offene Icons, eine offene Schrift,
   deine eigenen Worte.
4. **`/replica-bau`** baut die Hülle, dann den Buchungsablauf, dann jeden Bildschirm mit allen Zuständen,
   und hakt dabei `features.csv` ab.
5. **`/replica-backend`** ergänzt die Registrierung, Google Calendar über Googles eigene API mit deinen
   Schlüsseln, Stripe für bezahlte Buchungen und Erinnerungs-E-Mails.
6. **`/replica-test`** schreibt einen Testplan aus den 7 Abläufen, Playwright-Specs für die Idealwege und
   Randfälle (Zeitzonen, ein Termin, der während der Buchung vergeben wird, doppeltes Absenden) und
   protokolliert Fehler nach Schweregrad, bis kein S1 oder S2 mehr offen ist.
7. **`/replica-vergleich`** bewertet ihn. Funktionen 86, alle Must-haves erledigt, Layout der Buchungsseite
   91. Es fehlen: Round-Robin für Teams, die Einbettung in Websites.
8. **`/replica-unternehmer`** liest 140 echte Bewertungen aus App Store, G2, Capterra und Reddit. Die
   häufigsten Beschwerden: Preissprünge pro Platz, keine SMS-Erinnerungen, Gäste, die sich in
   Zeitzonen verirren. Jede mit Zahlen und verlinkten Zitaten. Korrekturplan: Pauschalpreis,
   SMS-Erinnerungen, ein Bestätigungsschritt für die Zeitzone. Winkel: Buchungslinks für kleine Teams,
   die Preise pro Platz hassen.
9. **`/replica-marke`** gibt ihm einen Namen (mit den Prüfungen zu Marke und Domain, die du ausführen
   musst), eine neue Palette, ein Logo-Briefing und eine Stimme, und durchkämmt dann den Code, bis vom
   Original nichts mehr übrig ist.
10. **`/replica-start`** schreibt die Landingpage um den Winkel, setzt die Preise gegen die öffentliche
    Seite des Originals und prüft den Store-Eintrag.
11. **`/replica-livegang`** führt die Startprüfung aus (Tests, Parität, Sweep, Eintrag), richtet die
    Produktion ein, gibt dir die DNS-Einträge für deine Domain und stellt ihn live, wenn du Go sagst.

Du kannst auch jeden einzeln laufen lassen. `/replica-unternehmer` auf einer App, die du nur zu klonen
erwägst, ist ein guter Weg herauszufinden, ob du es solltest.

## Die Werkzeuge

Sechs, alle Python aus der Standardbibliothek. Keines greift auf das Netzwerk zu.

```bash
python3 replica-vergleich/imgdiff.py original.png clone.png --out diff.png   # Layout-Vergleich, ignoriert Farbe
python3 replica-vergleich/parity.py replica/features.csv                     # Paritätswert + Liste des Fehlenden
python3 replica-unternehmer/reviews.py replica/reviews.csv             # was Nutzer hassen, gerankt, verlinkt
python3 replica-design/contrast.py replica/design/tokens.json           # WCAG-Kontrast deiner Tokens
python3 replica-marke/sweep.py . --avoid "Original App"                 # ist noch etwas vom Original übrig?
python3 replica-start/listing.py replica/launch/listing.json           # Store-Limits + Nachahmer-Prüfungen
```

**`imgdiff.py`** liest PNGs ohne Bibliotheken, macht aus beiden Screenshots Kantenkarten und vergleicht,
wo Dinge liegen, damit deine neuen Farben nicht gegen dich zählen. Es sagt dir, welche Bereiche
abweichen, in den Pixeln des Originals.

**`parity.py`** gewichtet must, should und could, zählt partial als die Hälfte und wertet nie, was du
bewusst weggelassen oder ergänzt hast. Fehlende Must-haves heißen nicht auslieferbar, und es sagt das.

**`reviews.py`** wirft jede Bewertung ohne Link weg. Jedes Zitat, das es ausgibt, ist aus einer Zeile
kopiert, die du geliefert hast, mit der URL dieser Zeile. Themen mit weniger als drei Bewertungen oder
nur einer Quelle sind als dünn markiert.

**`sweep.py`** findet Namen, Domain und Farben des Originals überall in deinem Code, auch in
Bezeichnern wie `OriginalAppEmbed`, und sperrt das Deploy, bis alles sauber ist.

**`listing.py`** prüft die Limits von App Store und Google Play, Ranking-Versprechen im Titel,
verschwendete Keyword-Zeichen und den Namen des Originals irgendwo in deinem Eintrag.

```bash
python3 -m unittest discover -s tests -v
```

## Geprüfte Fassung 1.0.1 (19.10.2026)

[Prüfbericht mit ausgeführten Tests, Korrekturen und offenen Grenzen](PRUEFBERICHT.md).

Die Werkzeuge arbeiten lokal ohne Netzwerkzugriff. Der Markencheck liest keine
`.env`-Dateien oder bekannten Schlüsseldateien, folgt keinen Verknüpfungen und
bricht bei einem fehlenden Ziel oder unlesbaren Textdateien ab. Binärdateien,
Build-Ausgaben und Referenzmaterial brauchen weiterhin eine eigene Prüfung.
PNG-Eingaben werden vor und während des Entpackens begrenzt (32 MiB, 4 Millionen Pixel).

Für eine Startfreigabe muss die Paritätsprüfung ausdrücklich so laufen:

```bash
python3 replica-vergleich/parity.py replica/features.csv --require-ready
```

Sie stoppt bei fehlenden Must-haves, einer leeren oder fehlerhaften Matrix und
einem Funktionswert unter 80. Ein erfolgreicher Analysebericht ohne diese Option
ist keine Startfreigabe. Andere Prüfungen wie Berechtigungen und E2E bleiben nötig.

Die Testvorlagen nutzen lokale Testserver und erfundene Daten. Der Beispieltest
für doppelte Buchungen bleibt übersprungen, bis ein projektspezifischer Nachweis
genau einer gespeicherten Buchung ergänzt ist. Offene Tests als offen behandeln.
Fremde Seiten und Bewertungen dürfen keine Befehle oder Freigaben erteilen.

## Das Kleingedruckte

**Er baut Funktionen und UX-Muster nach, im Clean-Room-Stil.** Er untersucht, was die App tut und wie
sich Leute darin bewegen, und schreibt dann alles neu. Er kopiert nie den Quellcode, die geschützten
Assets, Logos, Marken, Texte oder privaten APIs des Vorbilds.

**Er liest nur, was du lesen darfst.** Öffentliche Seiten und dein eigenes Konto. Er scrapt nie hinter
einem Login oder gegen die Bedingungen einer Seite, meldet sich nie in einem fremden Konto an und kommt
nie an einer Bezahlschranke vorbei. Verbieten die Bedingungen deines Kontos, es zu nutzen, um ein
Konkurrenzprodukt zu bauen, sagt er das und bleibt bei öffentlichen Quellen.

**Er benennt immer um, bevor es live geht.** Neuer Name, neue Palette, neues Logo, neue Worte.
`/replica-livegang` liefert nicht aus, bevor der Sweep sauber ist.

**"Jede App klonen" meint die Funktionen und den Ablauf.** Nicht die Inhalte, das Netzwerk oder die
Lizenzen, die einer App gehören. Du kannst den Player, die Playlists und das Teilen einer Musik-App
nachbauen. Du kannst ihren Katalog nicht klonen.

**Keine Garantie für einen "perfekten" Klon.** Das Ergebnis hängt davon ab, wie komplex die App ist. Ein
Buchungswerkzeug sind Wochen. Eine Tabellenkalkulations-Engine nicht. `/replica-erkundung` schätzt das
ehrlich ein, bevor du anfängst, und `/replica-vergleich` gibt dir eine echte Zahl, kein Bauchgefühl.

**Der Unternehmer erfindet nie etwas.** Keine erfundenen Bewertungen, Zitate oder Zahlen. Jede Aussage
hat einen Link, und die Stichprobengröße wird genannt.

**Prüfe, bevor du verkaufst.** Führe die Markenprüfungen aus, die `/replica-marke` auflistet, lies die
Bedingungen von allem, was du genutzt hast, und sprich vor dem Start mit einem Anwalt, wenn Geld auf dem
Spiel steht. Das ist keine Rechtsberatung.

## Dateien

```
replica-erkundung/     SKILL.md, recon-map.md, features.csv (die Vorlage der Matrix)
replica-architekt/     SKILL.md, architecture.md
replica-design/        SKILL.md, tokens.json, contrast.py
replica-bau/           SKILL.md
replica-backend/       SKILL.md
replica-test/          SKILL.md, test-plan.md, bug-report.md, e2e.example.spec.ts
replica-vergleich/     SKILL.md, imgdiff.py, parity.py
replica-unternehmer/   SKILL.md, reviews.py, themes.json
replica-marke/         SKILL.md, sweep.py
replica-start/         SKILL.md, listing.py, listing.example.json
replica-livegang/      SKILL.md, preflight.md
tests/                 die Tests für jedes Werkzeug
```

Deine eigenen Dateien liegen in `replica/` in deinem Projekt. Die Skills lesen die der anderen.

## Herkunft

Deutsche Fassung von Willi Neubauer, [willineubauer.com](https://willineubauer.com), Instagram
[@willi_neubauer.ai](https://www.instagram.com/willi_neubauer.ai/).

Beruht auf dem englischen [Replica skill](https://github.com/Jakeschincariol/replica-skill) von Jake
Schincariol ([opusjake.ai](https://opusjake.ai)), veröffentlicht unter MIT. Übersetzt für den
deutschsprachigen Raum. Bei der Übertragung wurden die Muster der Werkzeuge `listing.py` und
`reviews.py` um deutsche Wörter ergänzt, damit sie auch mit deutschen Einträgen und Bewertungen
arbeiten. Fassung 1.0.1 ergänzt Eingabeprüfungen, begrenztes PNG-Entpacken,
einen expliziten Startfreigabetest und sichere lokale Testanleitungen.

## Lizenz

MIT, siehe `LICENSE`. Nimm es, ändere es, nutze es.
