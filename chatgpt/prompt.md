Du hilfst mir, mein Projektradar zu füllen. Das ist eine Übersicht aller Projekte, die ich angefangen habe, mit Fortschritt in Prozent, Beleg und nächstem Schritt. Am Ende gibst du mir einen fertigen Daten-Block, den ich in die Seite einfüge.

Arbeite in dieser Reihenfolge. Geh nicht zum nächsten Schritt, bevor ich geantwortet habe.

SCHRITT 1: Ist das ein Update?
Steht unter dem Strich «MEINE BISHERIGEN PROJEKTDATEN» ein JSON-Block, ist das ein Update. Lies ihn, behalte alle Projekte und frag mich nur, was seit dem «stand» neu ist oder sich geändert hat. Springe dann zu Schritt 4. Steht dort nichts, ist es die erste Erfassung. Weiter mit Schritt 2.

SCHRITT 2: Meine Projektordner
Du kannst meine ChatGPT-Projektordner («Projekte» in der Seitenleiste) nicht selbst sehen. Sag mir das in einem Satz. Bitte mich dann, die Namen aller meiner Projektordner aufzuzählen, auch leere oder alte. Wenn ich sie einfüge, nimm jeden als eigenes Projekt auf.

SCHRITT 3: Projekte, die in keinem Ordner liegen
Viele Vorhaben stecken in einzelnen Chats. Erkläre mir den besten Weg: den Daten-Export.
1. ChatGPT öffnen, Profil, Einstellungen, Datenkontrolle, «Daten exportieren».
2. ChatGPT schickt per Mail einen Link zu einer ZIP-Datei. Das kann einige Minuten dauern.
3. ZIP entpacken und die Datei conversations.json hier in den Chat hochladen.
Warte auf die Datei. Wenn ich sie hochlade: Lies alle Chat-Titel und die Inhalte, soweit du kannst. Suche konkrete Vorhaben, die über mehrere Chats wiederkehren oder die ein Ziel haben, zum Beispiel eine App, einen Kurs, eine Webseite, ein Business, eine Anschaffung, einen Umzug, einen Lernplan, ein Buch, ein Hobby-Projekt. Einmalige Fragen («Wie lange kocht man Eier?») sind keine Projekte. Wenn die Datei zu gross ist, um sie ganz zu lesen, sag mir genau, welchen Teil du gelesen hast.
Habe ich keinen Export, frag, ob du es mit deiner Funktion «Chatverlauf referenzieren» versuchen sollst. Dann sag mir klar: Die Liste ist wahrscheinlich nicht vollständig, weil du nicht den ganzen Verlauf durchsuchen kannst.

SCHRITT 4: Liste prüfen und Rückfragen
Zeig mir die gefundenen Projekte als einfache Liste: Name, ein Satz was es ist, woher du es hast (Projektordner oder Chat-Titel mit Datum). Lass mich streichen, umbenennen und ergänzen. Dann stell mir höchstens 8 Rückfragen zum Stand und zum nächsten Schritt, gebündelt in einer Nachricht, nicht einzeln. Beispiele: Wird es schon genutzt? Wann hast du zuletzt daran gearbeitet? Was ist der nächste konkrete Schritt? Bei klar erkennbaren Dingen frag nicht nach.

SCHRITT 5: Ausgabe
Gib mir genau einen JSON-Block in einem Codeblock aus, nichts anderes im Codeblock. Danach nur dieser Satz: «Kopiere den Block, öffne dein Projektradar und klicke auf Daten einfügen.»

Das Format:
{
 "stand": "JJJJ-MM-TT",
 "aufmerksamkeit": [ {"t": "Projektname", "text": "Was drängt, ein Satz.", "crit": false} ],
 "projekte": [
  {"n": "Name", "c": "Kategorie", "s": "lauft", "p": 40,
   "d": "Was das Projekt ist, 1 bis 2 Sätze.",
   "w": "Wo es liegt, zum Beispiel ChatGPT-Projekt «Name» oder Chat «Titel»",
   "l": "JJJJ-MM-TT", "x": "Nächster Schritt, ein konkreter Satz.",
   "b": "Beleg: woran die Einschätzung hängt."}
 ]
}

Bedeutung der Felder:
- stand: heutiges Datum. Frag mich danach, wenn du es nicht sicher weisst.
- n: Name. Bei einem Update die bestehenden Namen nicht ändern.
- c: Kategorie. Wenige, breite Kategorien, zum Beispiel Arbeit, Familie, Lernen, Gesundheit, Finanzen, Hobby, Business.
- s: Status. «lauft» = wird im Alltag genutzt. «bau» = es wird daran gearbeitet. «pause» = angefangen, seit über 6 Wochen still. «idee» = nur ein Gedanke oder eine Notiz. «fertig» = abgeschlossen. «stop» = bewusst aufgegeben.
- p: Prozent, ganze Zahl von 0 bis 100. 100 = läuft im Alltag. 80 bis 99 = fast fertig. 60 bis 79 = Kern funktioniert. 30 bis 59 = im Aufbau. 10 bis 29 = Konzept oder Entwurf. 0 bis 9 = nur Idee. Hat ein Projekt Etappen oder eine Checkliste, rechne daraus.
- d: Was es ist.
- w: Fundort. Wo ich es wiederfinde: Ordnername, Chat-Titel, Datei.
- l: Datum der letzten Arbeit daran. Unbekannt: «–».
- x: Nächster Schritt. Ein Satz, mit dem ich morgen anfangen kann. «–» wenn nichts mehr nötig ist.
- b: Beleg. Woran du die Prozentzahl festmachst.
- aufmerksamkeit: höchstens 8 Punkte, nur was wirklich drängt, zum Beispiel eine verpasste Frist oder ein auslaufender Zugang. Gibt es nichts, lass die Liste leer: []. «crit»: true nur, wenn etwas kaputt ist oder etwas verloren gehen kann.

Regeln:
- Erfinde nichts. Was du nicht aus meinen Angaben oder Chats belegen kannst, schreibst du nicht hinein. Im Zweifel setze den Fortschritt tiefer und sag im Beleg, was fehlt.
- Schreibe keine Passwörter, Zugangsdaten, API-Schlüssel, Kundendaten, Gesundheits- oder Finanzdetails in den Block. Steht so etwas in einem Chat, umschreibe es («Zugang ist eingerichtet»).
- Der Block muss gültiges JSON sein: doppelte Anführungszeichen, keine Kommentare, kein Komma nach dem letzten Eintrag. Anführungszeichen im Text vermeiden, nimm «…».
- Schreibe Deutsch, in kurzen, klaren Sätzen.

---
MEINE BISHERIGEN PROJEKTDATEN (leer lassen bei der ersten Erfassung):
