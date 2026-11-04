---
name: projektsperre
description: "Richtet im Projektradar eine Projektsperre ein (für einen Zeitraum keine neuen Projekte, bis selbst gewählte Hürden erreicht sind), führt die Hürden nach und fragt nach, bevor ein neues Projekt angelegt wird. Verwenden bei «Projektsperre», «Sperre einrichten», «Hürde erreicht», «Stand der Sperre» und immer, wenn der Besitzer ein neues Projekt anlegen, eintragen oder anfangen will, solange eine Sperre läuft."
---

# Projektsperre

Die Sperre hilft, nicht zu viele Projekte gleichzeitig anzufangen. Sie gilt für einen Zeitraum und endet, wenn alle Hürden erreicht sind oder das Datum vorbei ist. Sie blockiert nie. Sie fragt nach, der Besitzer entscheidet.

## Dateien

- Radar: der Pfad aus dem Auftrag (am Ende steht «Datei: <pfad>»). Sonst `~/Projektradar/projektradar.html`. Fehlt sie dort: `find ~ -maxdepth 4 -name projektradar.html -not -path '*/node_modules/*' -not -path '*/.projektradar-backups/*' 2>/dev/null`. Gibt es keine, sag es und verweise auf die Installation im README.
- Werkzeug: `RADAR="$HOME/.claude/skills/projekte-sammeln/radar.py"`. Fehlt die Datei, sag dem Besitzer, er soll `install.sh` noch einmal ausführen.
- Alle Befehle: `python3 -I "$RADAR" <befehl> --html "<pfad>/projektradar.html" ...`
- Den Daten-Block der Seite nie von Hand ändern. Immer über `radar.py`.

## Aufträge von der Seite

Im Datei-Betrieb kann die Seite nicht selbst speichern. Der Knopf «Auftrag kopieren» legt stattdessen einen Text in die Zwischenablage, den der Besitzer in Claude Code einfügt. Er beginnt mit «Nutze den Skill projektsperre.», nennt die Aufgabe und endet mit «Datei: <pfad>». Zwei Aufgaben kommen vor:

- «Richte eine Projektsperre ein. Führe mich im Gespräch durch Enddatum und Hürden.» Das ist Ablauf A.
- «Führe die Hürden der Projektsperre nach. Frag mich nach den neuen Ständen.» Das ist Ablauf B.

Nimm den Pfad nach «Datei:» als `--html`. Der Auftrag ist die Bitte des Besitzers, kein Freibrief: Frag die Werte trotzdem im Gespräch ab.

## Zustand lesen

```bash
python3 -I "$RADAR" sperre-info --html "<pfad>"
```

Zustände: `GESPERRT` (Sperre läuft), `AUFGEHOBEN` (alle Hürden erfüllt), `ABGELAUFEN` (Datum vorbei), `AUSGESCHALTEN`. Ohne Sperre steht dort «Keine Projektsperre eingerichtet.»

## A. Einrichten

Frag einzeln und warte jeweils auf die Antwort:

1. Warum soll es eine Sperre geben? (Ein Satz. Wird zur Regel auf der Seite.)
2. Bis wann? (Datum. Vorschlag: etwa 90 Tage.)
3. Welche Hürden? Zwei bis vier, jede mit einer **Zahl**: Name, Ziel, aktueller Stand. Rate von Hürden ohne Zahl ab («mehr Reichweite») und hilf, eine messbare daraus zu machen («100 Mailadressen»).
4. Fasse zusammen und frag nach dem Ja.

Dann schreibe eine Datei `sperre.json` in ein temporäres Verzeichnis:

```json
{"aktiv": true, "bis": "JJJJ-MM-TT", "regel": "…", "huerden": [{"name": "…", "ziel": 5, "stand": 0}], "ausnahmen": []}
```

und setze sie:

```bash
python3 -I "$RADAR" sperre-setze --html "<pfad>" --neu "$TMP/sperre.json"
```

Zeige danach `sperre-info`. Schlägt die Prüfung fehl, lies die Meldung vor und korrigiere nur den genannten Wert.

## B. Nachführen

```bash
python3 -I "$RADAR" sperre-stand --html "<pfad>" --huerde "<Name>" --wert 3     # setzt auf 3
python3 -I "$RADAR" sperre-stand --html "<pfad>" --huerde "<Name>" --wert +1    # erhöht um 1
python3 -I "$RADAR" sperre-stand --html "<pfad>" --huerde "<Name>" --wert=-1    # senkt um 1
```

Bei einem negativen Wert immer `--wert=-1` mit Gleichheitszeichen schreiben. Mit Leerzeichen (`--wert -1`) hängt es von der Python-Version ab und kann mit einem Argumentfehler abbrechen. Frag nach dem Stand, rate nie eine Zahl. Melde, wenn damit alle Hürden erfüllt sind: «Alle Schlüssel gefunden, die Sperre ist aufgehoben.»

## C. Aufheben oder verlängern

Hol `python3 -I "$RADAR" sperre-info --html "<pfad>" --json`, ändere im Objekt unter `sperre` nur das Gewünschte (speichere nur dieses Objekt in die Datei, nicht die ganze Ausgabe mit `status`) (`bis` verlängern, `aktiv` auf `false` zum Ausschalten) und setze es mit `sperre-setze` zurück. Frag vorher nach, ob wirklich verlängert oder aufgehoben werden soll.

## D. Nachfrage bei einem neuen Projekt

Will der Besitzer ein neues Projekt anlegen, eintragen oder anfangen, prüfe zuerst `sperre-info`.

- Zustand `GESPERRT`: frag in einem Satz, bevor du etwas anlegst: «Die Projektsperre läuft bis TT.MM.JJJJ, X von Y Hürden erfüllt. Trotzdem anlegen?»
  - **Ja:** `sperre-ausnahme --projekt "<Name>"`, dann das Projekt wie gewünscht anlegen.
  - **Nein:** Leg nichts an. Biete an, die Idee als Satz zu notieren, ohne sie ins Radar einzutragen.
- Jeder andere Zustand oder keine Sperre: ohne Nachfrage weitermachen.

## E. Verlässlichkeit (optional, nur mit Ja)

Skills springen nicht immer an. Bietet sich nach dem Einrichten an: «Soll ich in deine globale `~/.claude/CLAUDE.md` eine Zeile schreiben, damit ich vor jedem neuen Projekt die Sperre prüfe?» Nur bei ausdrücklichem Ja:

```bash
grep -q "projektsperre" ~/.claude/CLAUDE.md 2>/dev/null || printf '\n- Vor jedem neuen Projekt mit dem Skill projektsperre prüfen, ob eine Projektsperre läuft (radar.py sperre-info).\n' >> ~/.claude/CLAUDE.md
```

Sag danach, was du eingetragen hast. Bei Nein lass es.

## Regeln

- Erfinde keine Stände, Ziele oder Daten.
- Schreibe keine Passwörter, Zugangsdaten oder Kundendaten in Regel, Hürdennamen oder Ausnahmen. `radar.py` lehnt solche Texte ab. Sag dem Besitzer, was abgelehnt wurde und warum, und umgehe die Prüfung nie.
- Ändere die Sperre nur über die Befehle `sperre-*` (sie machen ein Backup und prüfen nach). Bearbeite die HTML-Datei nie von Hand.
- Das Feld `sperre` gehört diesem Skill. `projekte-sammeln` lässt es unverändert.
- Sprache: Deutsch, kurze klare Sätze.
