# Testplan: {{deine App}}

Build: {{Commit}}  Datum: {{JJJJ-MM-TT}}  Umgebung: lokal, Startdaten

| Fall | Ablauf | Art | Schritte | erwartet | auto | Ergebnis |
| --- | --- | --- | --- | --- | --- | --- |
| F01-H1 | Gast bucht einen Termin | Idealweg | /u/demo/30min öffnen, morgen 10:00 wählen, Formular ausfüllen, absenden | Bestätigungsbildschirm, Buchung im Dashboard des Gastgebers, E-Mail an beide | e2e | |
| F01-E1 | | Randfall: Zeit während des Ausfüllens vergeben | | klare Meldung, andere Zeit wählbar, keine Doppelbuchung | e2e | |
| F01-E2 | | Randfall: Gast in anderer Zeitzone | | Zeiten in der Zone des Gastes angezeigt, in UTC gespeichert | e2e | |
| F01-N1 | | Negativfall: Karte abgelehnt | | Fehler angezeigt, keine Buchung angelegt | manuell | |
