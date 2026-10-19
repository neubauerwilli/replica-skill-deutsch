# Architektur: {{deine App}} (ein Nachbau der Kernfunktionen von {{app}})

## Stack

| Schicht | Wahl | Warum |
| --- | --- | --- |
| Web | | |
| Datenbank | | |
| Auth | | |
| Zahlungen | | |
| E-Mail | | |
| Jobs | | |
| Hosting | | |

## Schema

Tabellen: {{n}}. Zugriffsregeln: {{RLS | Prüfungen in der Datenschicht}}.

```sql
-- oder siehe replica/schema.sql
```

## API

| Methode Pfad | tut | wer | Eingabe | Ausgabe | Ablauf |
| --- | --- | --- | --- | --- | --- |

Webhooks eingehend: {{...}}  Webhooks ausgehend: {{...}}
Jobs: {{Name, Zeitplan, was er tut}}

## Die Stellen, an denen es beißt

- Zeitzonen:
- Idempotenz:
- Wettlaufsituationen:

## Reihenfolge des Baus

1. Vertikaler Schnitt: {{Bildschirme, Tabellen, Routen}}
2. Must-haves:
3. Should-haves:
4. Korrekturen aus replica-unternehmer:
