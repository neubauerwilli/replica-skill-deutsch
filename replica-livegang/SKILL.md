---
name: replica-livegang
description: >-
  Bringt einen App-Klon auf der eigenen Domain des Nutzers live: eine
  Startprüfung als Tor (Tests grün, Must-haves der Parität erledigt,
  Umbenennungs-Sweep sauber, Eintrag geprüft, Rechtsseiten online),
  Produktionsdatenbank und Umgebungsvariablen, der Host, DNS-Einträge für die
  Domain und für E-Mail, Stripe im Live-Modus, OAuth-Weiterleitungen,
  Überwachung und mobile Builds für TestFlight und Play. Nutze den Skill, wenn
  der Nutzer sagt: "deploye es", "bring es raus", "stell es live", "verbinde
  meine Domain", "geh in Produktion", "veröffentliche die App", oder nachdem
  /replica-start fertig ist.
---

# replica-livegang

Liest alles in `replica/`. Schreibt `replica/deploy.md` (die ausgefüllte
Checkliste aus `preflight.md` in diesem Ordner). Der Begriff Deploy bedeutet:
den Stand deiner App auf den Server stellen, auf dem sie für alle erreichbar
ist.

## Die Regeln

- **Nichts geht ohne das Go des Nutzers live.** Zeig die Ergebnisse der
  Startprüfung und frag.
- **Der Nutzer kauft und meldet sich an.** Claude kauft nie eine Domain,
  gibt nie eine Karte ein, tippt nie ein Passwort und fügt nie einen
  Live-Schlüssel ein. Claude schreibt die genauen DNS-Einträge, die Namen der
  Umgebungsvariablen und die Befehle; die Schritte in den Konten macht der
  Nutzer.
- **Nicht, bevor umbenannt ist.** Der Sweep muss sauber sein. Keine Ausnahmen.

## Schritt 1: Startprüfung

Führe jede Prüfung aus und füge die Ergebnisse in `deploy.md` ein:

```bash
npx playwright test                                                  # replica-test
python3 ../replica-vergleich/parity.py replica/features.csv               # Must-haves erledigt
python3 ../replica-marke/sweep.py . --config replica/brand.json      # Ende mit 0: sauber
python3 ../replica-start/listing.py replica/launch/listing.json     # wenn du in die Stores gehst
npm run build                                                        # der Produktions-Build besteht
```

(Die Pfade gelten relativ dazu, wo das Paket installiert ist. Unter
`~/.claude/skills/` ist das `~/.claude/skills/replica-vergleich/parity.py` und
so weiter.)

Dazu von Hand: keine offenen S1- oder S2-Fehler, Seiten für Datenschutz und
Nutzungsbedingungen online (mit jedem Auftragsverarbeiter), Cookie-Banner, wenn
du in der EU oder im Vereinigten Königreich nicht notwendige Cookies nutzt,
Kontolöschung funktioniert, Favicon, Titel und OG-Bild sind deine.

Jeder Fehlschlag stoppt das Deploy. Sag, welcher, und warum.

## Schritt 2: Produktionsdienste

- Ein **eigenes Produktionsprojekt** für die Datenbank (nie das der
  Entwicklung), Backups an, Migrationen vom Deploy ausgeführt, nicht von Hand.
- Umgebungsvariablen im Host für die Produktion gesetzt, passend zu
  `.env.example`. Live-Schlüssel nur hier.
- **Stripe**: auf den Live-Modus umstellen, Produkte und Preise neu anlegen,
  den Produktions-Webhook-Endpunkt und sein Signaturgeheimnis hinzufügen, einen
  echten Kauf testen und erstatten.
- **OAuth**: die Produktionsdomain bei jedem Anbieter in die
  Weiterleitungs-URIs und zugelassenen Ursprünge eintragen. Google-Scopes, die
  eine Verifizierung brauchen, müssen genehmigt sein, sonst können sich nur
  Testnutzer anmelden.
- **E-Mail**: die Versanddomain beim Anbieter verifiziert.

## Schritt 3: Host und Domain

Standard: Vercel für Next.js (sonst Netlify, Cloudflare Pages, Fly oder
Render). Verbinde das Repo, damit `main` deployt und Pull Requests
Vorschau-URLs bekommen.

Die Domain, nachdem der Nutzer sie bei einem beliebigen Registrar gekauft hat:

| Eintrag | Name | Wert |
| --- | --- | --- |
| A | @ | die Apex-IP des Hosts (Vercel: in den Domain-Einstellungen angezeigt) |
| CNAME | www | das Ziel des Hosts (Vercel: `cname.vercel-dns.com`) |
| TXT | @ oder eine Subdomain | der Verifizierungswert des Hosts, falls verlangt |

E-Mail-DNS vom E-Mail-Anbieter: SPF (TXT), DKIM (CNAME oder TXT) und ein
DMARC-Eintrag, der mit `v=DMARC1; p=none; rua=mailto:du@deinedomain` beginnt
und auf `quarantine` verschärft wird, sobald die Berichte sauber sind. Ohne
diese landen deine Bestätigungsmails im Spam.

Wähle einen kanonischen Host (Apex oder www) und leite den anderen um. HTTPS
ist bei den genannten Hosts automatisch; prüf es.

## Schritt 4: im Blick behalten

Fehlerverfolgung (Sentry oder die des Hosts), Erreichbarkeitsprüfungen auf der
Startseite und der API des Kernablaufs, aufbewahrte Logs, Analytics (eine
datenschutzfreundliche erspart das Cookie-Banner) und ein Alarm an die E-Mail
oder das Handy des Nutzers. Mach dann selbst den Kernablauf auf der Live-Seite
und bitte den Nutzer, ihn auf seinem Handy zu machen.

## Schritt 5: mobil, wenn es eine App gibt

Expo: `eas build`, dann `eas submit` an TestFlight und die interne
Play-Testphase. Nativ: in Xcode archivieren, in App Store Connect hochladen;
Gradle-Bundle in die Play Console. Die Entwicklerkonten gehören dem Nutzer (99
$ im Jahr bei Apple, 25 $ einmalig bei Google). Erst Beta, dann die Prüfung
mit dem Eintrag aus replica-start.

## Ergebnis

`replica/deploy.md` mit jeder Prüfung und ihrem Ergebnis, der Live-URL, den
gesetzten DNS-Einträgen und dem, was in der ersten Woche zu beobachten ist. Der
Klon ist jetzt eine App mit deinem Namen darauf.
