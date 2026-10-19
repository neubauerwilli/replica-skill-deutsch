---
name: replica-architekt
description: >-
  Plant Stack, Datenbankschema und API für den Klon einer App, ausgehend von
  der Erkundungskarte, die replica-erkundung geschrieben hat. Wählt langweilige,
  verwaltete Technik, macht aus dem abgeleiteten Datenmodell echtes SQL mit
  Indizes und Zugriffsregeln, listet jede Route nach Ablauf auf und ordnet den
  Bau so, dass zuerst ein dünner vertikaler Schnitt steht. Nutze den Skill,
  wenn der Nutzer sagt: "plane den Klon", "welchen Stack soll ich nehmen",
  "entwirf die Datenbank", "schreib das Schema", "plane die API", "Architektur
  für meine Version von X", oder nachdem /replica-erkundung fertig ist.
---

# replica-architekt

Liest `replica/recon.md` und `replica/features.csv`. Schreibt
`replica/architecture.md` (Vorlage: architecture.md in diesem Ordner).

Gibt es keine Erkundungskarte, halte an und lass zuerst `/replica-erkundung`
laufen. Einen Klon aus der Erinnerung daran zu planen, was eine App tut, ist
der sichere Weg, die Hälfte zu übersehen.

## Schritt 1: der Stack

Nimm, was der Nutzer schon kennt, falls er einen Stack hat. Sonst gilt der
Standard, weil jeder Teil verwaltet, dokumentiert und bei null Nutzern billig
ist:

| Schicht | Standard | Alternative |
| --- | --- | --- |
| Web-App | Next.js (App Router) + TypeScript | Remix, SvelteKit, Rails |
| Styling | Tailwind, Tokens aus replica-design | CSS-Module |
| Mobil | Expo (React Native) | SwiftUI, Kotlin |
| Datenbank | Postgres auf Supabase oder Neon | PlanetScale, SQLite (Turso) |
| ORM | Drizzle oder Prisma | rohes SQL |
| Auth | Supabase Auth oder Auth.js | Clerk |
| Zahlungen | Stripe Checkout + Billing | Lemon Squeezy, Paddle |
| E-Mail | Resend oder Postmark | SES |
| Jobs | Vercel Cron, Inngest oder Trigger.dev | ein Worker auf Fly |
| Dateien | Supabase Storage oder Cloudflare R2 | S3 |
| Hosting | Vercel | Netlify, Fly, Render |

Schreib zu jeder Wahl eine Zeile, warum. Eine Datenbank. Keine Microservices.
Der Klon braucht nicht die Architektur des Originals, er braucht die
Funktionen des Originals.

## Schritt 2: das Schema

Mach aus dem abgeleiteten Datenmodell SQL. Für jede Tabelle gilt:

- `id uuid primary key default gen_random_uuid()`, `created_at`, `updated_at`
- eine Eigentümerspalte (`user_id` oder `org_id`) bei allem, was einem Nutzer gehört
- Fremdschlüssel mit einer festgelegten `on delete`-Regel, nicht der Standardregel
- Indizes auf jedem Fremdschlüssel und jeder Spalte, nach der du filterst oder sortierst
- Enums oder Check-Constraints für Statusfelder
- Zeiten immer als `timestamptz`, in UTC gespeichert
- Geld als ganze Cent plus eine Währungsspalte
- Zugriffsregeln: Row Level Security in Postgres auf Supabase, oder eine
  Berechtigungsprüfung pro Abfrage in der Datenschicht. Schreib auf, welche.

Beispiel für eine Buchungs-App:

```sql
create table bookings (
  id uuid primary key default gen_random_uuid(),
  event_type_id uuid not null references event_types(id) on delete cascade,
  host_id uuid not null references users(id) on delete cascade,
  start_at timestamptz not null,
  end_at timestamptz not null,
  guest_name text not null,
  guest_email text not null,
  guest_timezone text not null,
  status text not null default 'confirmed'
    check (status in ('confirmed','cancelled','rescheduled')),
  answers jsonb not null default '{}',
  created_at timestamptz not null default now(),
  constraint no_zero_length check (end_at > start_at)
);
create index on bookings (host_id, start_at);
```

Dann die harten Bedingungen, die die Erkundung gefunden hat. Dass zwei Gäste
denselben Termin buchen, ist ein Datenbankproblem (eine Exclusion-Constraint
oder ein Unique-Index), kein Problem der Oberfläche.

## Schritt 3: die API

Eine Tabelle pro Ablauf aus der Erkundungskarte. Für jede Route oder Server
Action:

`Methode Pfad | was sie tut | wer sie aufrufen darf | Eingabe | Ausgabe | Ablauf`

Dazu Webhooks eingehend (Stripe, Kalenderanbieter) und ausgehend, und
Hintergrundjobs (Erinnerungen, Synchronisierung, Aufräumen) mit ihrem
Zeitplan.

Nur offizielle, öffentliche APIs mit den eigenen Schlüsseln des Nutzers. Nie
die privaten Endpunkte der Original-App, auch wenn sie in einem Browser
sichtbar sind.

## Schritt 4: die Stellen, an denen es beißt

Schreib zu jedem, der zutrifft, eine Zeile: Zeitzonen und Sommerzeit,
Idempotenz (Webhooks kommen doppelt an), Wettlaufsituationen, Ratenlimits,
Dateigrößenlimits, Suche, Echtzeit, Offline, Zustellbarkeit von E-Mails,
Mandantenfähigkeit, DSGVO-Löschung.

## Schritt 5: Reihenfolge des Baus

1. **Vertikaler Schnitt.** Der Kernablauf von Anfang bis Ende, hässlich:
   registrieren, die eine Sache tun, das Ergebnis sehen. Beweist den Stack.
2. **Must-haves** aus `features.csv`, nach Bereich.
3. **Should-haves**, dann Could-haves.
4. **Die Korrekturen**, die replica-unternehmer findet, sobald er gelaufen ist.

Jeder Meilenstein listet seine Bildschirme (S-IDs), Tabellen und Routen.

## Ergebnis

`replica/architecture.md`, das SQL in `replica/schema.sql` oder als erste
Migration, und eine Zusammenfassung: der Stack in einer Zeile, Zahl der
Tabellen, Zahl der Routen, die drei riskantesten Teile und der nächste
Schritt: `/replica-design`.
