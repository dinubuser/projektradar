#!/usr/bin/env bash
# Projektradar installieren: lokale Startseite + Claude-Code-Skill.
# Aufruf: curl -fsSL https://raw.githubusercontent.com/dinubuser/projektradar/main/install.sh | bash
set -euo pipefail

REPO="${PROJEKTRADAR_REPO:-https://raw.githubusercontent.com/dinubuser/projektradar/main}"
ZIEL="${PROJEKTRADAR_DIR:-$HOME/Projektradar}"
SKILLS="$HOME/.claude/skills"
SEITE="$ZIEL/projektradar.html"

lade() { curl -fsSL "$REPO/$1" -o "$2"; }

echo "→ Projektradar nach $ZIEL"
mkdir -p "$ZIEL"

# Die Seite enthält später die eigenen Projekte. Nie überschreiben.
if [ -f "$SEITE" ]; then
  echo "  $SEITE gibt es schon, bleibt unverändert (deine Projekte sind darin)."
else
  lade projektradar.html "$SEITE"
  echo "  Seite angelegt."
fi

echo "→ Skill für Claude Code nach $SKILLS"
for datei in \
  projekte-sammeln/SKILL.md \
  projekte-sammeln/radar.py
do
  mkdir -p "$SKILLS/$(dirname "$datei")"
  lade "skills/$datei" "$SKILLS/$datei"
done
echo "  /projekte-sammeln installiert."
command -v claude >/dev/null 2>&1 || echo "  Hinweis: Claude Code ist nicht installiert. Ohne Claude Code bleibt die Seite leer: https://claude.com/claude-code"

URL="file://$SEITE"
if command -v pbcopy >/dev/null 2>&1; then printf '%s' "$URL" | pbcopy; KOPIERT=" (in der Zwischenablage)"; else KOPIERT=""; fi

if command -v open >/dev/null 2>&1; then open "$SEITE"
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$SEITE" >/dev/null 2>&1 || true
fi

cat <<EOF

✓ Fertig.

Adresse deines Projektradars$KOPIERT:
  $URL

Als Startseite im Browser eintragen:
  Chrome:  Einstellungen → Beim Start → «Bestimmte Seite öffnen» → Neue Seite hinzufügen → Adresse einfügen
  Safari:  Einstellungen → Allgemein → Homepage → Adresse einfügen
           (dazu «Neue Fenster/Tabs öffnen mit: Homepage»)
  Firefox: Einstellungen → Startseite → «Benutzerdefinierte Adressen» → Adresse einfügen
  Arc:     als Lesezeichen anpinnen

Projekte eintragen: Auf der Seite «↻ Projekte suchen» klicken,
den Auftrag in Claude Code einfügen. Claude sucht deine Projekte auf dem Rechner.
EOF
