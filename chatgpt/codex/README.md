# Projektradar für Codex

Dieselbe Projektradar-Seite, gefüllt von der OpenAI Codex CLI statt von Claude Code. Codex durchsucht deinen Rechner nach angefangenen Projekten, schätzt den Stand mit Beleg und trägt alles in `projektradar.html` ein. Alles bleibt auf deinem Rechner.

## Voraussetzungen

- Terminal (macOS oder Linux).
- Die Codex CLI. Installation laut Doku: `curl -fsSL https://chatgpt.com/codex/install.sh | sh`, alternativ `npm install -g @openai/codex` oder `brew install --cask codex`.
- Ein ChatGPT-Konto. Beim ersten Start von `codex` wählst du «Sign in with ChatGPT». Laut Preisseite ist Codex in Free, Go, Plus, Pro, Business, Edu und Enterprise enthalten. Welche Limits dein Tarif hat, steht in der Doku von OpenAI.
- `python3` und `curl`.

## Installieren

```bash
curl -fsSL https://raw.githubusercontent.com/dinubuser/projektradar/main/chatgpt/codex/install-codex.sh | bash
```

Das Skript:

1. legt die Seite in `~/Projektradar/projektradar.html` ab (eine schon vorhandene Seite bleibt unverändert),
2. installiert den Skill `projekte-sammeln` nach `~/.agents/skills/` (dort liest Codex persönliche Skills),
3. öffnet die Seite im Browser und legt ihre Adresse in die Zwischenablage.

Läuft Codex schon, einmal neu starten, falls der Skill nicht auftaucht.

## Aufrufen

```bash
cd ~/Projektradar
codex
```

Dann im Codex-Fenster eingeben:

```
$projekte-sammeln alles
```

Später zum Aktualisieren:

```
$projekte-sammeln Aktualisiere ~/Projektradar/projektradar.html
```

Danach die Seite neu laden (Cmd+R).

Der Knopf «Projekte suchen» auf der Seite kopiert einen Auftrag, den du in Codex einfügst. Er beginnt mit «Nutze den Skill projekte-sammeln». Das funktioniert auch ohne `$`.

## Warum im Ordner ~/Projektradar starten

Codex darf nur im Startordner schreiben. Startest du in `~/Projektradar`, kann es die Radar-Datei und das Backup dort schreiben.

Ist `~/Projektradar` kein git-Ordner, startet Codex laut Doku unter Umständen im Modus `read-only`. Dann kann es die Seite nicht schreiben. Stelle in dem Fall im Codex-Fenster mit `/permissions` auf `workspace-write` um, oder markiere den Ordner beim Start als vertraut.

Um deinen Rechner zu lesen, kann Codex um Erlaubnis fragen. Antworte mit der engsten Option, die weiterhilft. Netzwerk ist in `workspace-write` standardmässig aus. Prüfungen öffentlicher Adressen mit `curl` scheitern dann oder brauchen eine Freigabe.

Nicht nötig und nicht empfohlen: `--yolo` oder `danger-full-access`.

## Was der Skill darf

- Nur lesen. Geschrieben wird nur die Radar-Datei und ihr Backup in `.projektradar-backups/`.
- Keine Passwörter, Tokens oder API-Keys im Radar. `.env`-Dateien bleiben zu.
- Bestehende Einträge werden nie ohne deine Aussage gelöscht.
- Vor jeder Änderung entsteht ein Backup (die letzten 20).
- Die Datei enthält Ordnerpfade und Projektnamen. Nicht teilen.

## Grenzen

- Die Prozentzahlen sind Schätzungen aus Belegen (Commits, Logs, Notizen). Prüfe sie. Sag Codex, was nicht stimmt, und es führt den Eintrag nach.
- Die Suche ist auf macOS ausgelegt (LaunchAgents). Auf Linux fehlt diese Quelle.
- Subagents laufen parallel nur, wenn Codex sie startet. Sonst sucht Codex die Quellen nacheinander ab. Das dauert länger.
- Subagents verbrauchen mehr Tokens als ein einzelner Lauf. Bei knappen Limits die erste Suche in einem Zug laufen lassen und später nur aktualisieren.
- Die Doku sagt nicht klar, ob die Sandbox das Lesen ausserhalb von `~/Projektradar` einschränkt. Wenn Codex nachfragt oder etwas nicht lesen kann, fehlt es im Radar. Der Bericht nennt solche Lücken.
- Codex-Funktionen ändern sich. Stand der Doku: https://learn.chatgpt.com/docs/build-skills
- Der Skill wurde nach der Doku geschrieben und nicht mit jeder Codex-Version getestet.

## Deinstallieren

Nur den Skill entfernen: den Ordner `~/.agents/skills/projekte-sammeln` löschen.

Alles entfernen: zusätzlich `~/Projektradar` löschen. Darin liegen deine Projektdaten und die Backups. Sichere vorher `projektradar.html`, wenn du die Projekte behalten willst.
