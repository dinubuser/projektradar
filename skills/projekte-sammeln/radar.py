#!/usr/bin/env python3
"""Teil des Skills projekte-sammeln. Liest und ergaenzt das Projektradar (HTML mit JSON-Block #radar).

Nur Standardbibliothek, laeuft mit `python3 -I`.

Befehle:
  python3 -I radar.py info --html <projektradar.html> [--json]
      Zeigt Stand, Anzahl, Aufmerksamkeits-Punkte und alle Projekte
      (name | status | prozent | zuletzt | fundort). Mit --json alles als JSON.

  python3 -I radar.py schreibe --html <projektradar.html> --neu <aenderungen.json>
                               [--stand JJJJ-MM-TT] [--entferne NAME ...] [--dry-run]
      aenderungen.json: {"projekte": [...], "aufmerksamkeit": [...]} oder nur eine Liste von Projekten.
      Projekte mit gleichem Namen (ohne Gross/Klein) werden ergaenzt: Felder aus der Datei
      ersetzen die alten, fehlende Felder bleiben. Neue Namen kommen dazu.
      "aufmerksamkeit" ersetzt die ganze Liste, wenn vorhanden.
      Geloescht wird nur, was mit --entferne genannt ist.
      Vorher Backup nach <ordner der html>/.projektradar-backups/ (die letzten 20 bleiben),
      atomar schreiben, danach pruefen, bei Fehler Backup zurueck.

  python3 -I radar.py repariere --html <projektradar.html>
      Setzt das neueste Backup mit gueltigem JSON wieder ein.

Exit-Codes: 0 ok, 1 Pruefung fehlgeschlagen, 2 Aufruf oder Daten falsch.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import tempfile

BLOCK_RE = re.compile(r'(<script type="application/json" id="radar">)(.*?)(</script>)', re.S)
STATUS = {"lauft", "bau", "pause", "idee", "fertig", "stop"}
FELDER = ("n", "c", "s", "p", "d", "w", "l", "x", "b")
OPTIONAL = ("cwd",)
DATUM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Grobe Sperre gegen Geheimnisse in den Feldern. Lieber einmal zu viel abbrechen.
GEHEIM_RE = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9_-]{20,}|xox[abp]-|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY|passwor[dt]\s*[:=]\s*\S|api[_-]?key\s*[:=]\s*\S|token\s*[:=]\s*\S{12,})",
    re.I,
)
BACKUPS_BEHALTEN = 20


class Abbruch(Exception):
    def __init__(self, text, code=2):
        super().__init__(text)
        self.code = code


def lies(pfad):
    with open(pfad, encoding="utf-8") as f:
        html = f.read()
    m = BLOCK_RE.search(html)
    if not m:
        raise Abbruch(f'{pfad}: kein Block <script type="application/json" id="radar"> gefunden')
    try:
        daten = json.loads(m.group(2).replace("<\\/", "</"))
    except json.JSONDecodeError as e:
        raise Abbruch(f"JSON im Block #radar ist kaputt ({e}). Mit 'repariere' das letzte Backup einsetzen.", 1)
    daten.setdefault("stand", "")
    daten.setdefault("aufmerksamkeit", [])
    daten.setdefault("projekte", [])
    return html, m, daten


def schluessel(name):
    return re.sub(r"\s+", " ", str(name)).strip().casefold()


def pruefe_projekt(p, i):
    if not isinstance(p, dict):
        raise Abbruch(f"Projekt {i}: kein Objekt")
    if not str(p.get("n", "")).strip():
        raise Abbruch(f"Projekt {i}: Feld n (Name) fehlt")
    name = p["n"]
    if p.get("s") not in STATUS:
        raise Abbruch(f"«{name}»: s muss eines von {sorted(STATUS)} sein, ist {p.get('s')!r}")
    if not isinstance(p.get("p"), int) or isinstance(p.get("p"), bool) or not 0 <= p["p"] <= 100:
        raise Abbruch(f"«{name}»: p muss eine ganze Zahl von 0 bis 100 sein, ist {p.get('p')!r}")
    l = p.get("l", "–")
    if l not in ("", "–") and not DATUM_RE.match(str(l)):
        raise Abbruch(f"«{name}»: l (zuletzt) muss JJJJ-MM-TT oder «–» sein, ist {l!r}")
    for k, v in p.items():
        if k not in FELDER + OPTIONAL:
            raise Abbruch(f"«{name}»: unbekanntes Feld {k!r}. Erlaubt: {', '.join(FELDER + OPTIONAL)}")
        if k != "p" and not isinstance(v, str):
            raise Abbruch(f"«{name}»: Feld {k} muss Text sein")
        if isinstance(v, str) and GEHEIM_RE.search(v):
            raise Abbruch(f"«{name}»: Feld {k} sieht nach Passwort, Token oder Schlüssel aus. Nicht ins Radar schreiben.")


def pruefe_alles(daten):
    if daten.get("stand") and not DATUM_RE.match(daten["stand"]):
        raise Abbruch(f"stand muss JJJJ-MM-TT sein, ist {daten['stand']!r}")
    namen = set()
    for i, p in enumerate(daten["projekte"]):
        pruefe_projekt(p, i)
        k = schluessel(p["n"])
        if k in namen:
            raise Abbruch(f"Name doppelt: «{p['n']}»")
        namen.add(k)
    for a in daten["aufmerksamkeit"]:
        if not isinstance(a, dict) or not str(a.get("t", "")).strip():
            raise Abbruch("aufmerksamkeit: jeder Punkt braucht t (Titel) und text")
        for k in a:
            if k not in ("t", "text", "crit"):
                raise Abbruch(f"aufmerksamkeit «{a.get('t')}»: unbekanntes Feld {k!r}")
        if GEHEIM_RE.search(str(a.get("t", "")) + " " + str(a.get("text", ""))):
            raise Abbruch(f"aufmerksamkeit «{a['t']}» sieht nach Passwort oder Token aus")


def als_block(daten):
    return json.dumps(daten, ensure_ascii=False, indent=1).replace("</", "<\\/")


def backup_ordner(html_pfad):
    return os.path.join(os.path.dirname(os.path.abspath(html_pfad)), ".projektradar-backups")


def mache_backup(html_pfad):
    ordner = backup_ordner(html_pfad)
    os.makedirs(ordner, exist_ok=True)
    ziel = os.path.join(ordner, "projektradar-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".html")
    shutil.copy2(html_pfad, ziel)
    alte = sorted(f for f in os.listdir(ordner) if f.startswith("projektradar-") and f.endswith(".html"))
    for f in alte[:-BACKUPS_BEHALTEN]:
        os.remove(os.path.join(ordner, f))
    return ziel


def schreibe_atomar(pfad, inhalt):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(pfad)), prefix=".radar-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(inhalt)
    shutil.copymode(pfad, tmp)
    os.replace(tmp, pfad)


def cmd_info(a):
    _, _, d = lies(a.html)
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return
    print(f"Stand: {d['stand'] or '(noch nie gesucht)'}")
    print(f"Projekte: {len(d['projekte'])}")
    kategorien = sorted({p.get("c", "") for p in d["projekte"] if p.get("c")})
    print("Kategorien: " + (", ".join(kategorien) or "(keine)"))
    print(f"Aufmerksamkeit: {len(d['aufmerksamkeit'])}")
    for x in d["aufmerksamkeit"]:
        print(f"  {'!' if x.get('crit') else '-'} {x['t']}: {x.get('text', '')}")
    for p in sorted(d["projekte"], key=lambda p: -p.get("p", 0)):
        print(f"{p['n']} | {p.get('s')} | {p.get('p')} % | {p.get('l', '–')} | {p.get('w', '')}")


def cmd_schreibe(a):
    html, m, d = lies(a.html)
    alte_namen = {schluessel(p["n"]) for p in d["projekte"]}
    with open(os.path.expanduser(a.neu), encoding="utf-8") as f:
        neu = json.load(f)
    if isinstance(neu, list):
        neu = {"projekte": neu}
    if not isinstance(neu, dict):
        raise Abbruch("aenderungen.json muss ein Objekt oder eine Liste sein")

    index = {schluessel(p["n"]): i for i, p in enumerate(d["projekte"])}
    neu_n, geaendert = [], []
    for p in neu.get("projekte", []):
        if not isinstance(p, dict) or not str(p.get("n", "")).strip():
            raise Abbruch("Jedes Projekt in aenderungen.json braucht ein Feld n")
        k = schluessel(p["n"])
        if k in index:
            # Der bestehende Name bleibt, auch wenn die Schreibweise abweicht.
            d["projekte"][index[k]].update({f: v for f, v in p.items() if f != "n"})
            geaendert.append(p["n"])
        else:
            eintrag = {"c": "", "d": "", "w": "", "l": "–", "x": "–", "b": ""}
            eintrag.update(p)
            d["projekte"].append(eintrag)
            index[k] = len(d["projekte"]) - 1
            neu_n.append(p["n"])

    entfernt = []
    for name in a.entferne or []:
        k = schluessel(name)
        vorher = len(d["projekte"])
        d["projekte"] = [p for p in d["projekte"] if schluessel(p["n"]) != k]
        if len(d["projekte"]) == vorher:
            raise Abbruch(f"--entferne «{name}»: kein Projekt mit diesem Namen")
        entfernt.append(name)

    if "aufmerksamkeit" in neu:
        d["aufmerksamkeit"] = neu["aufmerksamkeit"]
    d["stand"] = a.stand or dt.date.today().isoformat()
    pruefe_alles(d)

    print(f"Neu: {len(neu_n)}" + (" · " + ", ".join(neu_n) if neu_n else ""))
    print(f"Nachgeführt: {len(geaendert)}" + (" · " + ", ".join(geaendert) if geaendert else ""))
    print(f"Entfernt: {len(entfernt)}" + (" · " + ", ".join(entfernt) if entfernt else ""))
    print(f"Aufmerksamkeit: {len(d['aufmerksamkeit'])} · Stand: {d['stand']} · Total: {len(d['projekte'])}")
    for p in d["projekte"]:
        if p["s"] == "lauft" and p["p"] < 60:
            print(f"Hinweis: «{p['n']}» steht auf «lauft» mit nur {p['p']} %. Gewollt?")
    if a.dry_run:
        print("(dry-run, nichts geschrieben)")
        return

    neues_html = html[: m.start(2)] + als_block(d) + html[m.end(2):]
    backup = mache_backup(a.html)
    schreibe_atomar(a.html, neues_html)

    # Nachpruefen: JSON lesbar, Anzahl stimmt, alte Projekte da (ausser entfernte), Rest der Datei gleich.
    try:
        html2, m2, d2 = lies(a.html)
        weg = {schluessel(n) for n in entfernt}
        neue_namen = {schluessel(p["n"]) for p in d2["projekte"]}
        if len(d2["projekte"]) != len(d["projekte"]):
            raise Abbruch("Anzahl stimmt nicht", 1)
        if not (alte_namen - weg) <= neue_namen:
            raise Abbruch("alte Projekte fehlen", 1)
        if html2[: m2.start(2)] != html[: m.start(2)] or html2[m2.end(2):] != html[m.end(2):]:
            raise Abbruch("Rest der HTML verändert", 1)
        if "</" in m2.group(2):
            raise Abbruch("</ im JSON nicht escaped", 1)
    except Abbruch as e:
        shutil.copy2(backup, a.html)
        raise Abbruch(f"Prüfung fehlgeschlagen ({e}). Backup wieder eingesetzt: {backup}", 1)
    print(f"OK geschrieben. Backup: {backup}")


def cmd_repariere(a):
    ordner = backup_ordner(a.html)
    if not os.path.isdir(ordner):
        raise Abbruch(f"Keine Backups in {ordner}", 1)
    for f in sorted(os.listdir(ordner), reverse=True):
        pfad = os.path.join(ordner, f)
        with open(pfad, encoding="utf-8") as fh:
            m = BLOCK_RE.search(fh.read())
        if not m:
            continue
        try:
            json.loads(m.group(2).replace("<\\/", "</"))
        except json.JSONDecodeError:
            continue
        shutil.copy2(a.html, a.html + ".kaputt")
        shutil.copy2(pfad, a.html)
        print(f"OK: {f} eingesetzt. Die kaputte Fassung liegt als {a.html}.kaputt daneben.")
        return
    raise Abbruch("Kein Backup mit gültigem JSON gefunden", 1)


def main():
    ap = argparse.ArgumentParser(description="Projektradar lesen und ergänzen")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("info")
    i.add_argument("--html", required=True)
    i.add_argument("--json", action="store_true")
    s = sub.add_parser("schreibe")
    s.add_argument("--html", required=True)
    s.add_argument("--neu", required=True)
    s.add_argument("--stand")
    s.add_argument("--entferne", nargs="*")
    s.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("repariere")
    r.add_argument("--html", required=True)
    a = ap.parse_args()
    a.html = os.path.expanduser(a.html)
    try:
        if not os.path.isfile(a.html):
            raise Abbruch(f"{a.html} gibt es nicht")
        {"info": cmd_info, "schreibe": cmd_schreibe, "repariere": cmd_repariere}[a.cmd](a)
    except Abbruch as e:
        print("FEHLER: " + str(e), file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
