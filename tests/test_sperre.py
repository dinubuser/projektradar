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

    def stand_von(self, i):
        return self.lies_alles()["sperre"]["huerden"][i]["stand"]

    def test_stand_relativ_und_absolut(self):
        self.setze(GUT)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "zweite hürde", "--wert", "+2")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.stand_von(1), 3)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "Zweite Hürde", "--wert", "10")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.stand_von(1), 10)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "Zweite Hürde", "--wert=-20")
        self.assertEqual(code, 2, err)
        self.assertEqual(self.stand_von(1), 10)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "Zweite Hürde", "--wert=-4")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.stand_von(1), 6)

    def test_stand_unbekannte_huerde_nennt_die_vorhandenen(self):
        self.setze(GUT)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "Gibt es nicht", "--wert", "1")
        self.assertEqual(code, 2)
        self.assertIn("Erste Hürde", err)
        self.assertIn("Zweite Hürde", err)

    def test_stand_ohne_sperre(self):
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "A", "--wert", "1")
        self.assertEqual(code, 2)
        self.assertIn("keine Projektsperre", err)

    def test_stand_keine_zahl(self):
        self.setze(GUT)
        code, _, err = self.lauf("sperre-stand", "--html", self.html, "--huerde", "Erste Hürde", "--wert", "viel")
        self.assertEqual(code, 2)

    def test_alle_erfuellt_hebt_auf(self):
        self.setze(GUT)
        self.lauf("sperre-stand", "--html", self.html, "--huerde", "Erste Hürde", "--wert", "5")
        self.lauf("sperre-stand", "--html", self.html, "--huerde", "Zweite Hürde", "--wert", "30")
        code, out, err = self.lauf("sperre-info", "--html", self.html, "--heute", "2026-11-03")
        self.assertEqual(code, 0, err)
        self.assertIn("AUFGEHOBEN", out)

    def test_letzter_tag_gilt_noch_danach_abgelaufen(self):
        self.setze(GUT)
        _, out, _ = self.lauf("sperre-info", "--html", self.html, "--heute", "2027-01-31")
        self.assertIn("GESPERRT", out)
        self.assertIn("noch 0 Tage", out)
        _, out, _ = self.lauf("sperre-info", "--html", self.html, "--heute", "2027-02-01")
        self.assertIn("ABGELAUFEN", out)

    def test_ausgeschaltet(self):
        self.setze({**GUT, "aktiv": False})
        _, out, _ = self.lauf("sperre-info", "--html", self.html, "--heute", "2026-11-03")
        self.assertIn("AUSGESCHALTEN", out)

    def test_ausnahme_nur_einmal(self):
        self.setze(GUT)
        code, _, err = self.lauf("sperre-ausnahme", "--html", self.html, "--projekt", "Neues Ding")
        self.assertEqual(code, 0, err)
        code, out, err = self.lauf("sperre-ausnahme", "--html", self.html, "--projekt", " neues ding ")
        self.assertEqual(code, 0, err)
        self.assertIn("schon als Ausnahme", out)
        self.assertEqual(self.lies_alles()["sperre"]["ausnahmen"], ["Neues Ding"])

    def test_ausnahme_ohne_name_oder_ohne_sperre(self):
        code, _, err = self.lauf("sperre-ausnahme", "--html", self.html, "--projekt", "X")
        self.assertEqual(code, 2)
        self.setze(GUT)
        code, _, err = self.lauf("sperre-ausnahme", "--html", self.html, "--projekt", "  ")
        self.assertEqual(code, 2)

    def test_projekte_und_unbekannte_felder_bleiben(self):
        code, _, err = self.lauf("schreibe", "--html", self.html, "--neu", self.json_datei([PROJEKT], "projekte.json"))
        self.assertEqual(code, 0, err)
        self.setze({**GUT, "notiz": "bleibt"})
        self.lauf("sperre-stand", "--html", self.html, "--huerde", "Erste Hürde", "--wert", "+1")
        alles = self.lies_alles()
        self.assertEqual([p["n"] for p in alles["projekte"]], ["Testprojekt"])
        self.assertEqual(alles["sperre"]["notiz"], "bleibt")
        self.assertEqual(alles["sperre"]["huerden"][0]["stand"], 1)

    def test_schreibe_laesst_die_sperre_unveraendert(self):
        self.setze(GUT)
        vorher = self.lies_alles()["sperre"]
        code, _, err = self.lauf("schreibe", "--html", self.html, "--neu", self.json_datei([PROJEKT], "projekte.json"))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.lies_alles()["sperre"], vorher)

    def test_info_json_hat_status(self):
        self.setze(GUT)
        code, out, err = self.lauf("sperre-info", "--html", self.html, "--json", "--heute", "2026-11-03")
        self.assertEqual(code, 0, err)
        daten = json.loads(out)
        self.assertEqual(daten["status"], {"zustand": "GESPERRT", "tage": 89, "erfuellt": 0, "gesamt": 2})

    def test_info_json_ohne_sperre(self):
        code, out, err = self.lauf("sperre-info", "--html", self.html, "--json")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"sperre": None, "status": None})

    def test_setze_nicht_utf8_datei(self):
        pfad = os.path.join(self.tmp, "kaputt.json")
        with open(pfad, "wb") as f:
            f.write(b"\xff\xfe")
        code, _, err = self.lauf("sperre-setze", "--html", self.html, "--neu", pfad)
        self.assertEqual(code, 2)
        self.assertIn("FEHLER", err)


if __name__ == "__main__":
    unittest.main()
