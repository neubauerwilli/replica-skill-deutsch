# Deploy-Checkliste: {{deine App}}

Datum: {{JJJJ-MM-TT}}  Commit: {{sha}}  Go vom Nutzer: {{ja / noch nicht}}

## Startprüfung (alles muss bestehen)

- [ ] E2E-Suite grün: {{n bestanden / n}}
- [ ] keine offenen S1- oder S2-Fehler
- [ ] Parität: `parity.py replica/features.csv --require-ready` Ende mit 0; alle Must-haves erledigt ({{n/n}}), Funktionswert {{n}}
- [ ] Umbenennungs-Sweep sauber (`sweep.py` Ende mit 0)
- [ ] Store-Eintrag besteht (`listing.py` Ende mit 0), wenn du in die Stores gehst
- [ ] Produktions-Build besteht
- [ ] Datenschutzerklärung und Nutzungsbedingungen online, jeder Auftragsverarbeiter genannt
- [ ] Kontolöschung funktioniert
- [ ] Favicon, Titel, OG-Bild, E-Mails und App-Icon sind deine

## Produktion

- [ ] eigene Produktionsdatenbank, Backups an, Migrationen im Deploy
- [ ] Umgebungsvariablen gesetzt (Namen passen zu .env.example)
- [ ] Stripe live: Produkte, Preise, Webhook-Endpunkt + Geheimnis; echten Kauf und Erstattung nur vom Nutzer durchführen lassen, falls benötigt
- [ ] OAuth-Weiterleitungs-URIs und Ursprünge enthalten die Produktionsdomain
- [ ] Google-OAuth-Verifizierung genehmigt (bei sensiblen Scopes)
- [ ] E-Mail-Versanddomain verifiziert

## Domain

- [ ] A @ -> {{Wert}}
- [ ] CNAME www -> {{Wert}}
- [ ] SPF, DKIM, DMARC gesetzt
- [ ] kanonischer Host gewählt, der andere leitet um
- [ ] HTTPS gültig

## Beobachten

- [ ] Fehlerverfolgung
- [ ] Erreichbarkeitsprüfungen
- [ ] Analytics
- [ ] Kernablauf auf der Live-Seite erledigt, Desktop und Handy
