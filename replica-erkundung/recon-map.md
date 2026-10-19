# Erkundungskarte: {{app}} ({{platform}})

Umfang: {{der nachgebaute Ausschnitt}}
Für: {{für wen der Klon ist}}
Datum: {{JJJJ-MM-TT}}

## Quellen

| # | Quelle | URL | Notizen |
| --- | --- | --- | --- |
| 1 | Hilfecenter | | |

## Kernablauf

{{ein Satz: das, wofür Nutzer bezahlen}}

## Bildschirme

| ID | Bildschirm | Route / Weg dorthin | Zweck | wichtige Bausteine | gesehene Zustände |
| --- | --- | --- | --- | --- | --- |
| S01 | | | | | leer, gefüllt, Fehler |

## Abläufe

```
F01 {{Ziel}}
    S01 -> S02 -> S03
    Klicks auf dem Idealweg: {{n}}
    Randfall: {{Fälle}}
```

## Bausteine

| Baustein | Varianten | Zustände | genutzt auf |
| --- | --- | --- | --- |
| Button | primary, secondary, ghost, danger | default, hover, focus, disabled, loading | alle |

## Abgeleitetes Datenmodell

```
{{Entität}}  {{Felder}}
             Beleg: {{Bildschirm-IDs, Hilfeartikel}}
             Sicherheit: hoch | mittel | Vermutung
```

Beziehungen: {{User 1-n EventType, EventType 1-n Booking, ...}}

## Funktionsmatrix

Siehe `features.csv`. Must: {{n}}, should: {{n}}, could: {{n}}, skip: {{n}}.

## Nicht im Umfang (lässt sich nicht oder sollte man nicht nachbauen)

- {{lizenzierte Inhalte, das Netzwerk, Partnerverträge, ...}}

## Größe

Bildschirme {{n}}, Abläufe {{n}}, Entitäten {{n}}. Schwere Teile: {{Liste}}. Größe: {{S|M|L|XL}}.
