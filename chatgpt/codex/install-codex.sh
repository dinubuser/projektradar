#!/usr/bin/env bash
# Projektradar installieren: lokale Startseite + Skill für die Codex CLI.
# Aufruf: curl -fsSL https://raw.githubusercontent.com/dinubuser/projektradar/main/chatgpt/codex/install-codex.sh | bash
set -euo pipefail

REPO="${PROJEKTRADAR_REPO:-https://raw.githubusercontent.com/dinubuser/projektradar/main}"
ZIEL="${PROJEKTRADAR_DIR:-$HOME/Projektradar}"
SKILLS="$HOME/.agents/skills"
SEITE="$ZIEL/projektradar.html"

lade() { curl -fsSL "$REPO/$1" -o "$2"; }

command -v curl >/dev/null 2>&1 || { echo "curl fehlt. Bitte curl installieren und noch einmal starten."; exit 1; }
command -v python3 >/dev/null 2>&1 || echo "Hinweis: python3 fehlt. Der Skill braucht es zum Schreiben der Radar-Datei."

echo "→ Projektradar nach $ZIEL"
mkdir -p "$ZIEL"

# Die Seite enthält später die eigenen Projekte. Nie überschreiben.
if [ -f "$SEITE" ]; then
  echo "  $SEITE gibt es schon, bleibt unverändert (deine Projekte sind darin)."
else
  lade projektradar.html "$SEITE"
  echo "  Seite angelegt."
fi

echo "→ Skill für Codex nach $SKILLS"
mkdir -p "$SKILLS/projekte-sammeln"
# SKILL.md ist die Codex-Fassung, radar.py ist dieselbe Datei wie beim Claude-Code-Skill.
lade chatgpt/codex/SKILL.md "$SKILLS/projekte-sammeln/SKILL.md"
lade skills/projekte-sammeln/radar.py "$SKILLS/projekte-sammeln/radar.py"
echo "  \$projekte-sammeln installiert."
command -v codex >/dev/null 2>&1 || echo "  Hinweis: Codex CLI ist nicht installiert. Ohne Codex bleibt die Seite leer: https://learn.chatgpt.com/docs/codex/cli"

URL="file://$SEITE"
if command -v pbcopy >/dev/null 2>&1; then printf '%s' "$URL" | pbcopy; KOPIERT=" (in der Zwischenablage)"; else KOPIERT=""; fi

if command -v open >/dev/null 2>&1; then open "$SEITE"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$SEITE" >/dev/null 2>&1 || true
fi

cat <<EOT

✓ Fertig.

Adresse deines Projektradars$KOPIERT:
  $URL

Projekte eintragen:
  cd "$ZIEL"
  codex
  Dann eingeben:  \$projekte-sammeln alles
  Codex fragt eventuell um Erlaubnis, Ordner ausserhalb von $ZIEL zu lesen.
  Startet Codex im Modus read-only: im Codex-Fenster /permissions und workspace-write wählen.
  Danach die Seite im Browser neu laden (Cmd+R).

Falls Codex den Skill nicht anzeigt: Codex neu starten.
EOT
