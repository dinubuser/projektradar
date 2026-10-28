#!/usr/bin/env python3
"""Setzt chatgpt/prompt.md in projektradar.html ein (Block #chatgpt-prompt).

Aufruf aus dem Repo-Ordner:
  python3 -I chatgpt/sync-prompt.py          # einsetzen
  python3 -I chatgpt/sync-prompt.py --pruefe # nur prüfen, Exit 1 bei Abweichung
"""
import pathlib
import re
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
HTML = WURZEL / "projektradar.html"
PROMPT = WURZEL / "chatgpt" / "prompt.md"
MUSTER = re.compile(r'(<script type="text/plain" id="chatgpt-prompt">)(.*?)(</script>)', re.S)


def main():
    text = PROMPT.read_text(encoding="utf-8").strip()
    # Diese Texte würden die Seite zerbrechen oder den Daten-Block der Seite doppeln (radar.py sucht ihn per Regex).
    for verboten in ("<script", "</script", 'id="radar"'):
        if verboten in text.lower():
            sys.exit("prompt.md enthält %s. Bitte umformulieren." % verboten)
    seite = HTML.read_text(encoding="utf-8")
    treffer = MUSTER.search(seite)
    if not treffer:
        sys.exit("Block #chatgpt-prompt in projektradar.html nicht gefunden.")
    if "--pruefe" in sys.argv:
        if treffer.group(2).strip() != text:
            sys.exit("projektradar.html ist nicht auf dem Stand von prompt.md. Ausführen: python3 -I chatgpt/sync-prompt.py")
        print("ok: Prompt in der Seite ist aktuell.")
        return
    neu = MUSTER.sub(lambda m: m.group(1) + text + m.group(3), seite, count=1)
    HTML.write_text(neu, encoding="utf-8")
    print("Prompt eingesetzt (%d Zeichen)." % len(text))


main()
