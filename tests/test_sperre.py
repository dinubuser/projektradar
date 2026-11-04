"""Tests für die Projektsperre in radar.py. Nur Standardbibliothek.
Aufruf aus dem Repo-Ordner: python3 -m unittest discover -s tests -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RADAR = os.path.join(WURZEL, "skills", "projekte-sammeln", "radar.py")
VORLAGE = os.path.join(WURZEL, "projektradar.html")

GUT = {
    "aktiv": True,
    "bis": "2027-01-31",
    "regel": "Keine neuen Projekte, bis die Hürden erreicht sind.",
    "huerden": [
        {"name": "Erste Hürde", "ziel": 5, "stand": 0},
        {"name": "Zweite Hürde", "ziel": 30, "stand": 1},
    ],
    "ausnahmen": [],
}

PROJEKT = {"n": "Testprojekt", "c": "Test", "s": "bau", "p": 40, "d": "d", "w": "w", "l": "2026-11-01", "x": "x", "b": "b"}


class SperreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.html = os.path.join(self.tmp, "projektradar.html")
        shutil.copy(VORLAGE, self.html)

    def lauf(self, *args):
        p = subprocess.run([sys.executable, "-I", RADAR, *args], capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def json_datei(self, obj, name="neu.json"):
        pfad = os.path.join(self.tmp, name)
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        return pfad

    def setze(self, obj):
        return self.lauf("sperre-setze", "--html", self.html, "--neu", self.json_datei(obj))

    def lies_alles(self):
        code, out, err = self.lauf("info", "--html", self.html, "--json")
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def inhalt(self):
        with open(self.html, encoding="utf-8") as f:
            return f.read()

    def test_ohne_sperre_info_und_datei_unveraendert(self):
        vorher = self.inhalt()
        code, out, err = self.lauf("sperre-info", "--html", self.html)
        self.assertEqual(code, 0, err)
        self.assertIn("Keine Projektsperre", out)
        self.assertEqual(self.inhalt(), vorher)

    def test_setze_und_info(self):
        code, out, err = self.setze(GUT)
        self.assertEqual(code, 0, err)
        code, out, err = self.lauf("sperre-info", "--html", self.html, "--heute", "2026-11-03")
        self.assertEqual(code, 0, err)
        self.assertIn("GESPERRT", out)
        self.assertIn("noch 89 Tage", out)
        self.assertIn("0 von 2", out)
        self.assertIn("Erste Hürde", out)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".projektradar-backups")))

    def test_setze_lehnt_ungueltiges_ab(self):
        faelle = {
            "kein_objekt": [1, 2],
            "datum": {**GUT, "bis": "31.01.2027"},
            "datum_unmoeglich": {**GUT, "bis": "2027-02-30"},
            "ziel_null": {**GUT, "huerden": [{"name": "A", "ziel": 0, "stand": 0}]},
            "stand_negativ": {**GUT, "huerden": [{"name": "A", "ziel": 3, "stand": -1}]},
            "ziel_text": {**GUT, "huerden": [{"name": "A", "ziel": "3", "stand": 0}]},
            "keine_huerden": {**GUT, "huerden": []},
            "sieben_huerden": {**GUT, "huerden": [{"name": f"H{i}", "ziel": 1, "stand": 0} for i in range(7)]},
            "name_leer": {**GUT, "huerden": [{"name": " ", "ziel": 3, "stand": 0}]},
            "name_doppelt": {**GUT, "huerden": [{"name": "A", "ziel": 3, "stand": 0}, {"name": "a ", "ziel": 3, "stand": 0}]},
            "ausnahmen_kein_text": {**GUT, "ausnahmen": [1]},
            "aktiv_kein_bool": {**GUT, "aktiv": "ja"},
            "geheimnis": {**GUT, "regel": "token: abcdefghijklmnop1234"},
        }
        vorher = self.inhalt()
        for name, obj in faelle.items():
            with self.subTest(name):
                code, _, err = self.setze(obj)
                self.assertEqual(code, 2, err)
                self.assertIn("FEHLER", err)
                self.assertEqual(self.inhalt(), vorher)


if __name__ == "__main__":
    unittest.main()
