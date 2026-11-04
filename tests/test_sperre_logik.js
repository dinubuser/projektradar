// Tests für die Sperre-Logik der Seite. Aufruf aus dem Repo-Ordner: node tests/test_sperre_logik.js
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const html = fs.readFileSync(path.join(__dirname, "..", "projektradar.html"), "utf8");
const m = html.match(/\/\/ SPERRE-LOGIK START\n([\s\S]*?)\/\/ SPERRE-LOGIK ENDE/);
assert.ok(m, "Marken SPERRE-LOGIK START und SPERRE-LOGIK ENDE nicht gefunden");
const { sperreStatus, pruefeSperre } = new Function(m[1] + "\nreturn { sperreStatus, pruefeSperre };")();

const gut = () => ({
  aktiv: true, bis: "2027-01-31", regel: "r",
  huerden: [{ name: "A", ziel: 5, stand: 0 }, { name: "B", ziel: 30, stand: 1 }],
  ausnahmen: []
});
let n = 0;
const test = (name, fn) => { fn(); n++; console.log("ok  " + name); };

test("gesperrt, 89 Tage", () => {
  assert.deepEqual(sperreStatus(gut(), "2026-11-03"), { zustand: "GESPERRT", tage: 89, erfuellt: 0, gesamt: 2 });
});
test("letzter Tag gilt noch, danach abgelaufen", () => {
  assert.deepEqual(sperreStatus(gut(), "2027-01-31"), { zustand: "GESPERRT", tage: 0, erfuellt: 0, gesamt: 2 });
  assert.equal(sperreStatus(gut(), "2027-02-01").zustand, "ABGELAUFEN");
});
test("alle Hürden erfüllt hebt auf", () => {
  const s = gut(); s.huerden[0].stand = 5; s.huerden[1].stand = 31;
  assert.equal(sperreStatus(s, "2026-11-03").zustand, "AUFGEHOBEN");
});
test("aktiv false ist ausgeschaltet, auch wenn alles erfüllt ist", () => {
  const s = gut(); s.aktiv = false; s.huerden[0].stand = 5; s.huerden[1].stand = 30;
  assert.equal(sperreStatus(s, "2026-11-03").zustand, "AUSGESCHALTEN");
});
test("gültige Sperre bleibt mit allen Feldern erhalten", () => {
  const r = pruefeSperre({ ...gut(), notiz: "bleibt" });
  assert.equal(r.fehler, undefined);
  assert.equal(r.sperre.notiz, "bleibt");
  assert.equal(r.sperre.huerden.length, 2);
});
test("fehlende Angaben bekommen Standardwerte", () => {
  const r = pruefeSperre({ bis: "2027-01-31", huerden: [{ name: "A", ziel: 1, stand: 0 }] });
  assert.equal(r.sperre.aktiv, true);
  assert.deepEqual(r.sperre.ausnahmen, []);
  assert.equal(r.sperre.regel, "");
});
test("ungültige Sperren werden abgelehnt", () => {
  const huerde = (o) => ({ ...gut(), huerden: [{ name: "A", ziel: 3, stand: 0, ...o }] });
  const faelle = {
    null: null,
    liste: [],
    datum_format: { ...gut(), bis: "31.01.2027" },
    datum_unmoeglich: { ...gut(), bis: "2027-02-30" },
    datum_fehlt: { ...gut(), bis: undefined },
    aktiv_text: { ...gut(), aktiv: "ja" },
    regel_zahl: { ...gut(), regel: 5 },
    keine_huerden: { ...gut(), huerden: [] },
    sieben_huerden: { ...gut(), huerden: Array.from({ length: 7 }, (_, i) => ({ name: "H" + i, ziel: 1, stand: 0 })) },
    ziel_null: huerde({ ziel: 0 }),
    ziel_text: huerde({ ziel: "3" }),
    ziel_komma: huerde({ ziel: 1.5 }),
    stand_negativ: huerde({ stand: -1 }),
    name_leer: huerde({ name: "  " }),
    name_doppelt: { ...gut(), huerden: [{ name: "A", ziel: 1, stand: 0 }, { name: " a ", ziel: 1, stand: 0 }] },
    ausnahmen_zahl: { ...gut(), ausnahmen: [1] }
  };
  for (const [name, obj] of Object.entries(faelle)) {
    const r = pruefeSperre(obj);
    assert.ok(r.fehler, "sollte abgelehnt werden: " + name);
    assert.match(r.fehler, /^Projektsperre:/);
  }
});

console.log(n + " Tests ok");
