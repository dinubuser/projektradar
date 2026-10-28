---
name: projekte-sammeln
description: "Sucht auf dem Rechner nach angefangenen Projekten (Code-Ordner, git-Repos, Notizen, Automationen, eigene Skills), schätzt pro Projekt den Fortschritt in Prozent mit Beleg und nächstem Schritt und trägt alles ins Projektradar (projektradar.html) ein. Führt auch einzelne Projekte nach. Nutzen bei: 'Projekte suchen', 'Projektradar aktualisieren', 'was habe ich alles angefangen', 'Stand meiner Projekte', 'trag das Projekt ins Radar ein', 'Projekt X ist jetzt fertig'."
---

# Projekte sammeln

Dieser Skill füllt das Projektradar. Er findet angefangene Projekte, schätzt ehrlich, wie weit sie sind, und schreibt sie in die HTML-Datei. Jede Einschätzung braucht einen Beleg, den der Besitzer nachprüfen kann.

## Dateien

- Projektradar: der Pfad aus dem Auftrag. Sonst `~/Projektradar/projektradar.html`. Fehlt sie dort, suchen: `find ~ -maxdepth 4 -name projektradar.html -not -path '*/node_modules/*' -not -path '*/.projektradar-backups/*' 2>/dev/null`. Gibt es keine, das sagen und auf die Installation hinweisen: https://github.com/dinubuser/projektradar
- Die Daten stehen als JSON im Block `<script type="application/json" id="radar">`. Diesen Block nie von Hand bearbeiten, immer über `radar.py`.
- `radar.py` liegt im Ordner dieses Skills, normalerweise `~/.agents/skills/projekte-sammeln`. Unten heisst dieser Ordner `SKILL_DIR`.
- Arbeitsordner für Zwischenergebnisse: `mktemp -d`. Unten heisst er `TMP`. Darf Codex dort nicht schreiben, `TMP="$PWD/.projektradar-tmp"` nehmen und den Ordner am Ende wieder entfernen.

## Harte Regeln

1. Nur lesen. Ausser der Radar-Datei (und ihrem Backup-Ordner `.projektradar-backups/`) und dem Arbeitsordner `TMP` nichts ändern, verschieben, löschen, committen oder starten. Keine Dienste neu starten, keine Pakete installieren.
2. Keine Geheimnisse ins Radar: keine Passwörter, Tokens, API-Keys, Kundendaten, Gesundheits- oder Finanzdetails. `.env`-Dateien, Schlüsselbund und Passwort-Apps nicht öffnen. Steht in einem Beleg etwas Heikles, umschreiben («Zugang ist eingerichtet»).
3. Bestehende Einträge nie löschen. Entfernen (`--entferne`) nur, wenn der Besitzer es ausdrücklich sagt. Nachführen ist erlaubt.
4. Fortschritt nie schönrechnen. Was nicht belegt ist, zählt nicht. Im Zweifel tiefer schätzen und im Beleg sagen, was fehlt.
5. Python nur mit `python3 -I` starten.
6. Wird eine Genehmigung verweigert oder ist ein Ordner nicht lesbar: nicht umgehen (kein Wechsel auf vollen Zugriff, keine Umwege). Die Lücke im Bericht nennen.

## Datenformat

```json
{
 "stand": "JJJJ-MM-TT",
 "aufmerksamkeit": [ {"t": "Projektname", "text": "Was ist los, ein Satz.", "crit": true} ],
 "projekte": [
  {"n": "Name", "c": "Kategorie", "s": "lauft|bau|pause|idee|fertig|stop", "p": 0,
   "d": "Was das Projekt ist, 1 bis 2 Sätze.",
   "w": "~/pfad/zum/projekt · weitere Fundorte, getrennt mit ·",
   "l": "JJJJ-MM-TT", "x": "Nächster Schritt, ein konkreter Satz. «–» wenn nichts nötig.",
   "b": "Beleg: woran die Einschätzung hängt.", "cwd": "~/ordner (optional)"}
 ]
}
```

- `n` ist der Schlüssel. Gleicher Name (ohne Gross/Klein) heisst gleiches Projekt. Namen nicht umbenennen, sonst entsteht ein Duplikat.
- `c` Kategorie: wenige, breite Kategorien. Vorhandene aus `radar.py info` wiederverwenden. Für den Anfang zum Beispiel: Business, Content & Social, Automation, Infrastruktur & Tools, Persönlich, Lernen.
- `s` Status: `lauft` = wird im Alltag genutzt. `bau` = es wird daran gearbeitet. `pause` = angefangen, seit über 6 Wochen still. `idee` = nichts Lauffähiges. `fertig` = abgeschlossen, braucht nichts mehr. `stop` = bewusst aufgegeben oder ersetzt.
- `p` Prozent: ganze Zahl von 0 bis 100, siehe Skala unten.
- `l` Zuletzt: Datum der letzten echten Änderung (letzter Commit, Änderungsdatum der neuesten Datei). Unbekannt: `–`.
- `w` Fundort: zuerst der Projektordner mit `~/`. Der Knopf «Nächster Schritt» nimmt den ersten Pfad als Arbeitsordner für den Agenten. Passt der nicht, `cwd` setzen.
- `aufmerksamkeit`: höchstens 8 Punkte. Nur was wirklich drängt: ausgefallene Automationen, auslaufende Zugänge, Code ohne git oder Backup, verpasste Fristen. `crit: true` nur, wenn etwas kaputt ist oder Daten verloren gehen können.

### Prozent-Skala

| Prozent | Bedeutung | Typischer Beleg |
|---|---|---|
| 100 | läuft im Alltag | Dienst oder Job läuft, Logs aktuell, wird genutzt |
| 80–99 | fast fertig | funktioniert, letzte Punkte offen (Feinschliff, Veröffentlichen) |
| 60–79 | Kern funktioniert | Hauptfunktion läuft, wichtige Teile fehlen |
| 30–59 | im Aufbau | Teile gebaut, noch nicht nutzbar |
| 10–29 | Konzept | Plan, Entwurf, Prototyp |
| 0–9 | nur Idee | Notiz, Chat, Stichwort |

Hat ein Projekt einen eigenen Plan mit Etappen oder Checkliste, daraus rechnen (zum Beispiel 3 von 6 Etappen = 50 %).

## Ablauf

### 1. Bestand lesen

```bash
python3 -I "$SKILL_DIR/radar.py" info --html "<pfad>/projektradar.html"
```

Merken: Stand, Kategorien, vorhandene Projekte.

Art des Auftrags:
- **Einzelnes Projekt** («führe den Eintrag X nach», «X ist jetzt fertig»): nur dieses Projekt prüfen (Fundort lesen, letzter Commit, was im Gespräch erledigt wurde), dann direkt zu Schritt 4. Keine Vollsuche.
- **Aktualisieren** (Radar hat schon Projekte): alle vorhandenen Projekte auf neuen Stand prüfen und nur nach Neuem seit dem Stand suchen.
- **Erste Suche** («alles» oder leeres Radar): Vollsuche.

### 2. Quellen absuchen

Jede Quelle liefert ein JSON-Array mit Projekten im Format oben nach `TMP/<quelle>.json`.

**Parallel mit Subagents, wenn möglich.** Codex startet Subagents nur auf ausdrückliche Anweisung. Dieser Skill ist so eine Anweisung: Starte pro Quelle (unten) einen Subagent, warte auf alle, und nimm ihre Ergebnisse zusammen. Subagents erben Sandbox und Genehmigungen der Hauptsitzung. Geben sie nichts zurück oder gibt es keine Subagents: die Quellen nacheinander selbst absuchen, gleiches Ergebnis, nur langsamer.

Jedem Subagent mitgeben: die harten Regeln, das Datenformat, die Prozent-Skala, die Liste der vorhandenen Projektnamen, das heutige Datum und den Satz «Nur lesen, nichts ändern, nur die Datei TMP/<quelle>.json schreiben.»

Quellen (nur was es auf diesem Rechner gibt, vorher kurz prüfen):

1. **Code und git-Repos:** `find ~ -maxdepth 4 -name .git -type d -not -path '*/Library/*' -not -path '*/node_modules/*' -not -path '*/.Trash/*' 2>/dev/null`. Pro Repo: README, `git log -1 --format=%cs`, Anzahl Commits, offene Branches, Plan- oder TODO-Dateien. Dazu Projektordner ohne git in `~/Projekte`, `~/Projects`, `~/Developer`, `~/Code`, `~/Documents`, `~/Desktop`, `~/Downloads` (Ordner mit `package.json`, `pyproject.toml`, `requirements.txt`, `index.html`, `*.py`). Code ohne git als Aufmerksamkeit melden.
2. **Notizen:** Obsidian-Vaults (`find ~ -maxdepth 4 -name .obsidian -type d -not -path '*/Library/*' 2>/dev/null`, dazu `~/Library/Mobile Documents/iCloud~md~obsidian/Documents`). Projektordner, Notizen mit «Projekt», «Plan», «Roadmap», «TODO», «Idee» im Namen oder Frontmatter. Nur Projekte aufnehmen, keine Tagebuch- oder Gesundheitsinhalte.
3. **Automationen:** `ls ~/Library/LaunchAgents` (nur eigene, keine von Apple, Google, Adobe, Microsoft und ähnlichen Herstellern), `crontab -l`. Pro Job: läuft er (`launchctl list | grep <label>`), letztes Log-Datum, Fehler im Log. Ein Job, der seit über einer Woche nicht mehr gelaufen ist oder Fehler wirft, kommt in die Aufmerksamkeit. Lässt sich `launchctl` oder ein Log nicht lesen, keinen Ausfall melden, sondern die Lücke im Bericht nennen.
4. **Codex:** eigene Skills in `~/.agents/skills` (Skills aus Plugins und die mitgelieferten System-Skills auslassen), eigene Subagents in `~/.codex/agents`, Projektanweisungen in `AGENTS.md`-Dateien der gefundenen Projekte. Nur lesen. `~/.codex/config.toml` und alles andere in `~/.codex` bleibt zu, ausser den genannten Ordnern.

Nennt der Besitzer Server oder Webseiten: nur öffentliche Adressen mit `curl -sI` prüfen. Kein Login, kein SSH ohne ausdrückliches OK. Ist das Netzwerk in der Sandbox gesperrt und `curl` scheitert, nicht umgehen: die Adresse als ungeprüft im Bericht nennen.

### 3. Zusammenführen

1. JSON-Dateien aus `TMP` lesen.
2. Doppelte Treffer zusammenlegen. Derselbe Ordner oder ein sehr ähnlicher Name ist dasselbe Projekt. Fundorte mit `·` zusammenhängen. Der stärkste Beleg zählt: ein laufender Dienst oder ein frischer Commit schlägt eine alte README.
3. Gegen den Bestand prüfen. Vorhandene Projekte unter dem alten Namen nachführen, nicht neu anlegen.
4. Kleinkram weglassen: leere Ordner, reine Tutorials, geklonte fremde Repos ohne eigene Commits, Testordner. Im Zweifel als `idee` aufnehmen und im Bericht nennen.
5. Für jedes Projekt einen konkreten nächsten Schritt schreiben: ein Satz, mit dem man morgen anfangen kann. Bei `pause` oft: «Entscheiden: weitermachen oder archivieren.»
6. Aufmerksamkeit neu zusammenstellen (ersetzt die alte Liste).
7. Alles nach `TMP/aenderungen.json` schreiben: `{"projekte": [...], "aufmerksamkeit": [...]}`. Bei einem einzelnen Projekt nur dieses Projekt, `aufmerksamkeit` weglassen, dann bleibt die Liste.

### 4. Einsetzen

Erst trocken:

```bash
python3 -I "$SKILL_DIR/radar.py" schreibe --html "<pfad>/projektradar.html" --neu "$TMP/aenderungen.json" --dry-run
```

Dann echt, ohne `--dry-run`. Das Skript prüft Felder und Status, sperrt Texte, die nach Passwort oder Token aussehen, macht ein Backup nach `.projektradar-backups/` neben der Datei, schreibt, prüft nach und setzt bei einem Fehler das Backup zurück. `stand` wird heute.

Ist die Datei kaputt (die Seite zeigt «Die Projektdaten sind beschädigt»):

```bash
python3 -I "$SKILL_DIR/radar.py" repariere --html "<pfad>/projektradar.html"
```

### 5. Bericht

Kurz, auf Deutsch, ohne Fachjargon:

- Welche Quellen liefen (zum Beispiel «12 git-Repos, 1 Obsidian-Vault, 4 eigene Automationen, 9 Skills»). Quellen, die nicht lesbar waren, mit Grund.
- Neu im Radar und nachgeführt: je eine Zeile mit Name, Prozent, nächstem Schritt.
- Braucht Aufmerksamkeit: die Punkte aus der Liste.
- Bitte prüfen: unsichere Einschätzungen und Duplikat-Verdacht, je eine Zeile mit Grund. Der Besitzer kennt seine Projekte besser als jeder Beleg. Korrekturen («X ist schon live», «Y streichen») sofort mit Schritt 4 einarbeiten.
- Schluss: «Das Projektradar im Browser neu laden (Cmd+R).»
