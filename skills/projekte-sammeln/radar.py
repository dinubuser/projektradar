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

  python3 -I radar.py sperre-info --html <projektradar.html> [--json] [--heute JJJJ-MM-TT]
      Zeigt die Projektsperre: Zustand (GESPERRT, AUFGEHOBEN, ABGELAUFEN, AUSGESCHALTEN), Resttage, Hürden.

  python3 -I radar.py sperre-setze --html <projektradar.html> --neu <sperre.json>
      Legt die Projektsperre an oder ersetzt sie. sperre.json ist das Objekt aus dem Feld "sperre"
      (aktiv, bis, regel, huerden [name, ziel, stand], ausnahmen). Backup, atomares Schreiben und Prüfung wie bei schreibe.

  python3 -I radar.py sperre-stand --html <projektradar.html> --huerde NAME --wert <Zahl|+Zahl|-Zahl>
      Setzt den Stand einer Hürde (ohne Vorzeichen) oder ändert ihn (mit + oder -). Mit Minus: --wert=-1

  python3 -I radar.py sperre-ausnahme --html <projektradar.html> --projekt NAME
      Trägt ein Projekt als Ausnahme von der Sperre ein.

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


def pruefe_sperre(s):
    """Prüft das optionale Feld sperre. Unbekannte Felder bleiben erlaubt."""
    if not isinstance(s, dict):
        raise Abbruch("sperre: muss ein Objekt sein")
    if "aktiv" in s and not isinstance(s["aktiv"], bool):
        raise Abbruch("sperre.aktiv muss true oder false sein")
    bis = s.get("bis")
    if not isinstance(bis, str) or not DATUM_RE.match(bis):
        raise Abbruch(f"sperre.bis muss JJJJ-MM-TT sein, ist {bis!r}")
    try:
        dt.date.fromisoformat(bis)
    except ValueError:
        raise Abbruch(f"sperre.bis ist kein gültiges Datum: {bis!r}")
    if "regel" in s and not isinstance(s["regel"], str):
        raise Abbruch("sperre.regel muss Text sein")
    h = s.get("huerden")
    if not isinstance(h, list) or not 1 <= len(h) <= 6:
        raise Abbruch("sperre.huerden: es braucht 1 bis 6 Hürden")
    namen = set()
    for i, x in enumerate(h, 1):
        if not isinstance(x, dict):
            raise Abbruch(f"Hürde {i}: kein Objekt")
        name = x.get("name")
        if not isinstance(name, str) or not name.strip():
            raise Abbruch(f"Hürde {i}: name fehlt")
        if schluessel(name) in namen:
            raise Abbruch(f"Hürde «{name}»: Name doppelt")
        namen.add(schluessel(name))
        for feld, minimum in (("ziel", 1), ("stand", 0)):
            w = x.get(feld)
            if not isinstance(w, int) or isinstance(w, bool) or w < minimum:
                raise Abbruch(f"Hürde «{name}»: {feld} muss eine ganze Zahl ab {minimum} sein, ist {w!r}")
    ausnahmen = s.get("ausnahmen", [])
    if not isinstance(ausnahmen, list) or not all(isinstance(a, str) for a in ausnahmen):
        raise Abbruch("sperre.ausnahmen muss eine Liste von Namen sein")
    texte = [s.get("regel", "")] + [x["name"] for x in h] + ausnahmen
    if any(GEHEIM_RE.search(t) for t in texte):
        raise Abbruch("sperre: ein Text sieht nach Passwort, Token oder Schlüssel aus. Nicht ins Radar schreiben.")


def sperre_status(s, heute):
    """Zustand der Sperre. Sie gilt bis einschliesslich s['bis']."""
    gesamt = len(s["huerden"])
    erfuellt = sum(1 for h in s["huerden"] if h["stand"] >= h["ziel"])
    tage = (dt.date.fromisoformat(s["bis"]) - heute).days
    if s.get("aktiv", True) is False:
        zustand = "AUSGESCHALTEN"
    elif erfuellt == gesamt:
        zustand = "AUFGEHOBEN"
    elif tage < 0:
        zustand = "ABGELAUFEN"
    else:
        zustand = "GESPERRT"
    return {"zustand": zustand, "tage": tage, "erfuellt": erfuellt, "gesamt": gesamt}


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
    if "sperre" in daten:
        pruefe_sperre(daten["sperre"])


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


def speichere_daten(html_pfad, html, m, d):
    """Prüft, sichert, schreibt atomar und kontrolliert. Bei Fehler kommt das Backup zurück."""
    pruefe_alles(d)
    neues_html = html[: m.start(2)] + als_block(d) + html[m.end(2):]
    backup = mache_backup(html_pfad)
    schreibe_atomar(html_pfad, neues_html)
    try:
        html2, m2, d2 = lies(html_pfad)
        if d2 != d:
            raise Abbruch("Daten nach dem Schreiben anders als geplant", 1)
        if html2[: m2.start(2)] != html[: m.start(2)] or html2[m2.end(2):] != html[m.end(2):]:
            raise Abbruch("Rest der HTML verändert", 1)
        if "</" in m2.group(2):
            raise Abbruch("</ im JSON nicht escaped", 1)
    except Abbruch as e:
        shutil.copy2(backup, html_pfad)
        raise Abbruch(f"Prüfung fehlgeschlagen ({e}). Backup wieder eingesetzt: {backup}", 1)
    return backup


def lies_json(pfad):
    try:
        with open(os.path.expanduser(pfad), encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        raise Abbruch(f"{pfad} lässt sich nicht lesen ({e})")
    except json.JSONDecodeError as e:
        raise Abbruch(f"{pfad} ist kein gültiges JSON ({e})")
    except UnicodeDecodeError as e:
        raise Abbruch(f"{pfad} ist nicht UTF-8-kodiert ({e})")


def heute_von(a):
    if not getattr(a, "heute", None):
        return dt.date.today()
    try:
        return dt.date.fromisoformat(a.heute)
    except ValueError:
        raise Abbruch(f"--heute muss JJJJ-MM-TT sein, ist {a.heute!r}")


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


def cmd_sperre_info(a):
    _, _, d = lies(a.html)
    s = d.get("sperre")
    if s is None:
        if a.json:
            print(json.dumps({"sperre": None, "status": None}))
        else:
            print("Keine Projektsperre eingerichtet.")
        return
    pruefe_sperre(s)
    st = sperre_status(s, heute_von(a))
    if a.json:
        print(json.dumps({"sperre": s, "status": st}, ensure_ascii=False, indent=1))
        return
    if st["zustand"] == "GESPERRT":
        wort = "Tag" if st["tage"] == 1 else "Tage"
        zusatz = f" bis {s['bis']} (noch {st['tage']} {wort})"
    else:
        zusatz = f" (bis {s['bis']})"
    print(f"Projektsperre: {st['zustand']}{zusatz}")
    if s.get("regel"):
        print(f"Regel: {s['regel']}")
    print(f"Hürden: {st['erfuellt']} von {st['gesamt']} erfüllt")
    for h in s["huerden"]:
        haken = "x" if h["stand"] >= h["ziel"] else " "
        print(f"  [{haken}] {h['name']}: {h['stand']} von {h['ziel']}")
    ausnahmen = s.get("ausnahmen", [])
    print("Ausnahmen: " + (", ".join(ausnahmen) if ausnahmen else "(keine)"))


def cmd_sperre_setze(a):
    html, m, d = lies(a.html)
    neu = lies_json(a.neu)
    pruefe_sperre(neu)
    d["sperre"] = neu
    backup = speichere_daten(a.html, html, m, d)
    print(f"OK Projektsperre gesetzt. Backup: {backup}")


def _sperre_oder_abbruch(d):
    s = d.get("sperre")
    if s is None:
        raise Abbruch("Es gibt keine Projektsperre. Zuerst sperre-setze ausführen.")
    return s


def cmd_sperre_stand(a):
    html, m, d = lies(a.html)
    s = _sperre_oder_abbruch(d)
    gesucht = schluessel(a.huerde)
    treffer = [h for h in s["huerden"] if schluessel(h["name"]) == gesucht]
    if not treffer:
        raise Abbruch(f"Keine Hürde «{a.huerde}». Vorhanden: " + ", ".join(h["name"] for h in s["huerden"]))
    h = treffer[0]
    wert = a.wert.strip()
    if not re.fullmatch(r"[+-]?\d+", wert):
        raise Abbruch(f"--wert muss eine ganze Zahl sein, optional mit + oder -, ist {a.wert!r}")
    neu = h["stand"] + int(wert) if wert[0] in "+-" else int(wert)
    if neu < 0:
        raise Abbruch(f"Der Stand würde {neu}. Er darf nicht unter 0 liegen.")
    h["stand"] = neu
    backup = speichere_daten(a.html, html, m, d)
    print(f"OK «{h['name']}»: {neu} von {h['ziel']}. Backup: {backup}")


def cmd_sperre_ausnahme(a):
    html, m, d = lies(a.html)
    s = _sperre_oder_abbruch(d)
    name = a.projekt.strip()
    if not name:
        raise Abbruch("--projekt darf nicht leer sein")
    liste = s.setdefault("ausnahmen", [])
    if schluessel(name) in {schluessel(x) for x in liste}:
        print(f"«{name}» ist schon als Ausnahme eingetragen. Nichts geändert.")
        return
    liste.append(name)
    backup = speichere_daten(a.html, html, m, d)
    print(f"OK «{name}» ist Ausnahme von der Sperre. Backup: {backup}")


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
    si = sub.add_parser("sperre-info")
    si.add_argument("--html", required=True)
    si.add_argument("--json", action="store_true")
    si.add_argument("--heute")
    se = sub.add_parser("sperre-setze")
    se.add_argument("--html", required=True)
    se.add_argument("--neu", required=True)
    sst = sub.add_parser("sperre-stand")
    sst.add_argument("--html", required=True)
    sst.add_argument("--huerde", required=True)
    sst.add_argument("--wert", required=True)
    sau = sub.add_parser("sperre-ausnahme")
    sau.add_argument("--html", required=True)
    sau.add_argument("--projekt", required=True)
    a = ap.parse_args()
    a.html = os.path.expanduser(a.html)
    try:
        if not os.path.isfile(a.html):
            raise Abbruch(f"{a.html} gibt es nicht")
        {
            "info": cmd_info,
            "schreibe": cmd_schreibe,
            "repariere": cmd_repariere,
            "sperre-info": cmd_sperre_info,
            "sperre-setze": cmd_sperre_setze,
            "sperre-stand": cmd_sperre_stand,
            "sperre-ausnahme": cmd_sperre_ausnahme,
        }[a.cmd](a)
    except Abbruch as e:
        print("FEHLER: " + str(e), file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
