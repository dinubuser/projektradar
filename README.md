# Projektradar

Alle angefangenen Projekte auf einer lokalen Startseite, sortiert nach Fortschritt. Jedes Projekt hat einen Prozentwert mit Beleg, den Fundort und einen konkreten nächsten Schritt. Oben steht, was jetzt Aufmerksamkeit braucht: ausgefallene Automationen, Code ohne Backup, verpasste Fristen.

Die Seite ist am Anfang leer. Eine KI findet deine Projekte, schätzt den Stand und trägt alles ein: entweder ChatGPT (über deinen Chatverlauf) oder [Claude Code](https://claude.com/claude-code) und Codex (über deinen Rechner). Alles bleibt auf deinem Gerät.

Gut für alle, die viele Ideen anfangen und den Überblick verlieren.

## Zwei Wege

| | Mit ChatGPT | Mit Claude Code oder Codex |
|---|---|---|
| Braucht | normales ChatGPT, einen Browser | ein Terminal, Claude Code oder Codex |
| Wie die Projekte gefunden werden | Du nennst ChatGPT deine Projektordner, es wertet deinen exportierten Chatverlauf aus und fragt nach | Die KI liest deinen Rechner selbst (Code-Ordner, Notizen, Automationen) |
| Wo die Daten liegen | im Browser (localStorage), mit Sicherung als Datei | in der Seite auf deinem Rechner |
| Gut für | alle, die ihre Vorhaben vor allem in Chats haben | alle, die Code und Ordner voller Projekte haben |

## Mit ChatGPT

Kein Download, keine Installation.

1. Öffne das Projektradar: <https://dinubuser.github.io/projektradar/> (oder lade `projektradar.html` herunter und öffne die Datei im Browser).
2. Klicke auf **ChatGPT-Prompt kopieren**.
3. Wechsle in ChatGPT oben auf **Work** und öffne dort einen neuen Chat. Füge den Prompt ein und sende ihn. ChatGPT holt sich die Vorlage selbst und baut keine eigene Seite. Es bittet dich um einen Screenshot der Seitenleiste mit deinen Projektordnern. Das ist der schnellste Weg. Danach sucht es selbst nach weiteren Projekten in deinem Chatverlauf. Kann es die Vorlage nicht holen, sagt es dir, wie du sie über **Vorlage herunterladen** anhängst.
4. Am Ende fragt ChatGPT, wie du das Ergebnis möchtest:
   - **Fertige Seite als Datei (empfohlen):** ChatGPT trägt deine Projekte in die angehängte Vorlage ein und gibt dir die fertige Datei zurück. Speichere sie und öffne sie mit einem Doppelklick im Browser. Das ist dieselbe Seite wie bei Claude Code, mit deinen Projekten darin. Diesen Weg gibt es nur, wenn dein ChatGPT Dateien erzeugen kann (im Test ging das im Modus Work). Sieht die Seite anders aus als die Vorlage, hat ChatGPT sie nicht benutzt. Dann war die Vorlage nicht angehängt.
   - **Nur der Daten-Block:** ChatGPT gibt den Block aus. Kopiere ihn, klicke im Projektradar auf **Daten einfügen** und füge ihn ein.

Was ChatGPT kann und was nicht:

- Deine Projektordner («Projekte» in der Seitenleiste) kann ChatGPT nicht selbst auflisten. Du schickst ihm einen Screenshot der Seitenleiste oder nennst die Namen.
- Den ganzen Verlauf durchsucht ChatGPT nur zuverlässig über den **Daten-Export** (Einstellungen → Datenkontrolle → Daten exportieren, die ZIP-Datei kommt per Mail, `conversations.json` im Chat hochladen). Ohne Export hängt es davon ab, was ChatGPT über «Chatverlauf referenzieren» abrufen kann. Die Liste ist dann wahrscheinlich unvollständig ([OpenAI: Memory in ChatGPT](https://help.openai.com/en/articles/8590148-memory-in-chatgpt)).
- Die Prozentzahlen sind Schätzungen. Prüfe sie, bevor du dich darauf verlässt.
- Starte direkt in Work und hänge die Vorlage gleich an. Wechselst du mitten im Gespräch von Chat zu Work, bekommt Work nur eine kurze Zusammenfassung und baut leicht seine eigene Seite mit anderem Aussehen und anderen Feldern.

Deine Daten werden nie an einen Server geschickt. Beim Weg mit dem Daten-Block liegen sie im Browser. Der Browser kann sie löschen (zum Beispiel beim Leeren der Website-Daten). Darum gibt es **Sichern als Datei** und **Aus Datei laden**. Sichere nach jeder Änderung. Bei der fertigen Datei stecken die Daten in der Datei selbst, die Datei ist deine Sicherung.

Aktualisieren: Klicke auf **Mit ChatGPT aktualisieren**. Der Prompt enthält dann deine bisherigen Daten, und ChatGPT fragt nur nach dem, was neu ist. Hast du eine fertige Datei, lade sie beim Aktualisieren wieder hoch.

## Mit Codex

Codex ist der Terminal-Agent von OpenAI und liest wie Claude Code deinen Rechner. Anleitung und Installation: [chatgpt/codex/README.md](chatgpt/codex/README.md).

## Installieren (Claude Code)

Terminal öffnen und einfügen:

```bash
curl -fsSL https://raw.githubusercontent.com/dinubuser/projektradar/main/install.sh | bash
```

Das Skript:

1. legt die Seite in `~/Projektradar/projektradar.html` ab (eine schon vorhandene Seite bleibt unverändert),
2. installiert den Claude-Code-Skill `/projekte-sammeln` nach `~/.claude/skills/`,
3. öffnet die Seite im Browser und legt ihre Adresse in die Zwischenablage.

Läuft auf macOS. Linux geht auch, dort fehlen die macOS-Automationen (LaunchAgents) als Quelle.

Erst anschauen? Die leere Seite hat einen Link «So sieht es mit Beispieldaten aus».

## Als Startseite eintragen

Adresse: `file:///Users/<dein-name>/Projektradar/projektradar.html` (das Skript zeigt sie dir an).

- **Chrome:** Einstellungen → Beim Start → «Bestimmte Seite oder Seiten öffnen» → Neue Seite hinzufügen → Adresse einfügen
- **Safari:** Einstellungen → Allgemein → Homepage → Adresse einfügen. Dazu «Neue Fenster/Tabs öffnen mit: Homepage» wählen.
- **Firefox:** Einstellungen → Startseite → «Startseite und neue Fenster: Benutzerdefinierte Adressen» → Adresse einfügen
- **Arc / andere:** als Lesezeichen anpinnen

## Projekte eintragen

1. Auf der Seite auf **↻ Projekte suchen** klicken. Der Auftrag liegt dann in der Zwischenablage.
2. Claude Code starten (`claude` im Terminal) und den Auftrag einfügen.
3. Claude sucht in deinen Code-Ordnern und git-Repos, in Obsidian-Notizen, in deinen Automationen (LaunchAgents, cron) und in deinen eigenen Claude-Skills. Die erste Suche dauert etwa 10 bis 20 Minuten.
4. Seite neu laden (Cmd+R).

Danach Claude sagen, was nicht stimmt («X ist schon live», «Y streichen»). Claude führt es nach.

Später findet derselbe Knopf neuen Fortschritt und neue Projekte seit der letzten Suche.

## Mit dem nächsten Schritt arbeiten

Ein Klick auf **Nächster Schritt** einer Karte kopiert einen fertigen Auftrag mit Projektname, Schritt und Ordner. In Claude Code einfügen, und Claude legt im richtigen Projekt los. Am Ende führt Claude den Eintrag im Radar nach (Prozent, nächster Schritt, Datum).

Tipp: Claude Code im Projektordner starten (`cd <ordner> && claude`), dann stimmt der Arbeitsordner gleich.

## Sicherheit

- Claude liest nur. Ausser der Radar-Datei ändert, verschiebt oder löscht der Skill nichts und startet keine Dienste.
- Keine Passwörter, Tokens oder API-Keys im Radar. Das Hilfsskript bricht ab, wenn ein Text danach aussieht. `.env`-Dateien und der Schlüsselbund bleiben zu.
- Vor jeder Änderung legt der Skill ein Backup an (`~/Projektradar/.projektradar-backups/`, die letzten 20).
- Die Datei enthält Ordnerpfade und Projektnamen. Teile sie nicht und lege sie nicht in einen öffentlichen Ordner.

## Aktualisieren

Den Installationsbefehl nochmals ausführen. Der Skill wird ersetzt, deine Seite mit den Projekten bleibt.

## Deinstallieren

Den Ordner `~/Projektradar` und den Ordner `~/.claude/skills/projekte-sammeln` löschen.
