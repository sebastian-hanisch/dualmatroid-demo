# Dualität und Minoren – Kreis und Schnitt – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-dualmatroid-demo.streamlit.app/)** -->

Sechstes Stück der Reihe **Matroide und Submodularität** (Bereich Kombinatorik) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo zeigt das **Gegenstück zum Kreis**: das duale Matroid M*, dessen Basen die Komplemente der Basen von M sind, dessen Kreise die **Kokreise** von M sind (beim Wald die minimalen **Schnitte**), und bei dem sich **Löschen und Zusammenziehen** vertauschen. Dazu: das Dual eines planaren Plans ist der **Dualgraph**, nicht jedes Matroid ist **graphisch**, und **binär** heißt „kein U(2,4)-Minor“.

**Einordnung in die Reihe:** Nachfolger von [greedy-optimalitaet-demo](../greedy-optimalitaet-demo) (Stück 5), [rang-basen-kreise-demo](../rang-basen-kreise-demo) (Stück 4: Kreise, Basen, Fundamentalkreis), [matroid-demo](../matroid-demo) (Stück 3), [unabhaengigkeitssystem-demo](../unabhaengigkeitssystem-demo) (Stück 2) und [greedy-austausch-demo](../greedy-austausch-demo) (Stück 1). Das Beispiel ist dasselbe **Leitungsnetz mit farbigen Kabeln** mit denselben elf Systemen. Abgrenzung: [planar-dual-demo](../planar-dual-demo) (Planaritäts-Linie) zeigt den Dualgraphen für Fluss und kürzeste Wege, hier geht es um das Matroid dahinter.

## Warum dieses Problem

In Stück 4 war der Kreis eine kleinste Menge, die nicht zulässig ist. Im Graphen gibt es dazu ein Gegenstück, den **Schnitt**; im Matroid heißt es **Kokreis**. Offen ist, ob das ein Zufall der Graphen ist. Es ist keiner: Jedes Matroid hat ein Dual, dessen Kreise die Kokreise sind, und das gilt für alle 497 Matroide mit höchstens 5 Elementen ohne Ausnahme. Daraus folgt, was ein Graph nicht sieht: Das Dual eines Graphen ist nur bei planaren Graphen wieder ein Graph, und es gibt Matroide wie die Fano-Ebene, die zu keinem Graphen gehören.

## Befunde und Korrekturen gegenüber dem Plan

- **Dualgraph auf einer eigenen Zeichnung:** Die Standortpläne sind in der geradlinigen Zeichnung selten kreuzungsfrei (8 % bei 6, 4 % bei 7 Standorten), obwohl die meisten abstrakt planar sind. Die App zeichnet den Plan deshalb mit `networkx` neu (kreuzungsfrei, getrennte Streckung der Achsen) und leitet die Flächen aus dem Rotationssystem dieser Zeichnung ab. **`networkx` ist darum jetzt eine Laufzeit-Abhängigkeit** (in den Stücken davor nur für die Tests).
- **Darstellung über GF(2) aus den Fundamentalkreisen:** Statt alle Matrizen aufzuzählen (Plan, Messung) baut die App den einzigen Kandidaten (zur Basis B: Einheitsvektoren, e außerhalb als Summe der Elemente im Fundamentalkreis) und prüft ihn auf allen Teilmengen; die Aufzählung aller Matrizen bleibt als Orakel im Test.
- **U(2,4)-Minor über eine unabhängige Menge:** Statt aller Löschungen und Zusammenziehungen sucht die App eine 4-Element-Menge X und eine unabhängige Menge C außerhalb, bei der M / C auf X das U(2,4) ist (die Rangbedingung für alle 15 Teilmengen); nur bis 12 Elemente. Die Rekursion über alle Minoren ist das Orakel im Test (n ≤ 5).
- **Kandidatenzahlen in „nicht graphisch“:** Gezählt werden die **zusammenhängenden** einfachen Graphen (Spannbaumzahl über null): für M\*(K5) 331 506 von 352 716 Graphen mit 7 Knoten und 10 Kanten (in der Messung vor dem Bau stand die Zahl aller Graphen, 352 716).
- **Voreingestellter Kokreis:** der erste mit mindestens 3 Elementen (beim Wald eine Brücke als erster Kokreis wäre ein langweiliger Anfang).
- **Bild des Graphminors einfach:** Beim Zusammenziehen werden die Endpunkte zu einem Standort verschmolzen, parallele Leitungen sind leicht versetzt, Schleifen werden gezählt und nicht gezeichnet.
- **Port 9346;** Repo `dualmatroid-demo`, Präfix `dmo_`.

## Modell

Dieselben elf Systeme wie in Stück 3 bis 5 auf einem **Leitungsnetz mit farbigen Kabeln** (n Standorte, Depot A in der Mitte, min(n(n − 1)/2, 2n − 2) mögliche Leitungen, drei Kabelfarben), davon sechs Matroide (Wald, Kabelfarben, Anschluss-Standort, höchstens 4 Leitungen, Standorte als Vektoren, Fano-Ebene) und fünf, die keine sind (Paarung, Wald mit höchstens 2 Leitungen je Standort, Budget-Auswahl, Standorte ohne Nachbarn, Wald und Farbregel); diese fünf haben **kein Dual**. Formeln und Beweisskizzen: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Dual:** System der Komplemente der maximalen Mengen (`dual`); bei einem Matroid ist das M*. Gegenprobe: die Rangformel r*(F) = |F| − r(E) + r(E ∖ F) für alle F (`dual_rank_formula_holds`).
- **Kokreise:** die Kreise des Duals (`cocircuits`); beim Wald gegen die Bonds über alle Knotenmengen (`bonds`).
- **Minoren:** Löschen und Zusammenziehen auf Bitmasken (`delete`, `contract`), die Identitäten (M ∖ e)* = M*/e und (M/e)* = M* ∖ e als gleiche zulässige Mengen (`minor_identities`).
- **Dualgraph:** kreuzungsfreie Zeichnung (`planar_pos`), Flächen über das Rotationssystem (`dual_drawing`); Test: Spannbäume des Plans gegen die Komplemente der Spannbäume des Dualgraphen über alle (n − 1)-Teilmengen (`dual_tree_check`).
- **Binär:** drei Wege: Kreis-Kokreis-Parität (`even_intersections`), Darstellung über GF(2) (`represents_over_gf2`), kein U(2,4)-Minor (`u24_minor`).
- **Nicht graphisch:** einfache Graphen auf Rang + 1 Knoten mit gleich vielen Spannbäumen (Kirchhoff, `numpy.linalg.det`), bei Gleichstand Isomorphie über alle Permutationen (`graphic_search`).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet. Plan: 7 Standorte, 12 mögliche Leitungen, Seed 8 (die Fano-Ebene ist vom Plan unabhängig, die zwei Standorte-Systeme haben 7 Elemente).

| System | Rang | Dualrang | Basen | Kreise | Kokreise | binär |
|---|---|---|---|---|---|---|
| Wald (graphisches Matroid) | 6 | 6 | 180 | 32 | 24 | ja |
| höchstens eine Leitung je Kabelfarbe (Partitionsmatroid) | 3 | 9 | 42 | 25 | 3 | ja |
| jede Leitung mit eigenem Anschluss-Standort (bizirkulares Matroid) | 7 | 5 | 311 | 93 | 200 | nein |
| höchstens 4 Leitungen (uniformes Matroid) | 4 | 8 | 495 | 792 | 220 | nein |
| Standorte als Vektoren über R (lineares Matroid) | 3 | 4 | 28 | 20 | 11 | nein |
| Fano-Ebene (lineares Matroid über GF(2)) | 3 | 4 | 28 | 14 | 7 | ja |
| Paarung, Wald mit Grad ≤ 2, Budget-Auswahl, Standorte ohne Nachbarn, Wald und Farbregel | kein Matroid | kein Dual | – | – | – | – |

| Frage | Befund |
|---|---|
| **Alle Matroide auf 1 bis 5 Elementen** (2, 5, 16, 68, **406** Matroide) | Das Dual ist ein Matroid, das Doppeldual ist das Matroid selbst, die Rangformel gilt, (M ∖ e)* = M*/e und (M/e)* = M* ∖ e gelten für alle e, und kein Kreis trifft einen Kokreis in genau einem Element: bei **allen 497**, **0 Abweichungen**. Beschriftet selbstdual: 1 (n = 2) und 4 (n = 4), sonst keines. |
| **Nicht-Matroide ohne Dual** (alle Systeme auf 3 bis 5 Elementen: 3, 99, 7 174) | Das System der Komplemente der maximalen Mengen ist bei **0 von 7 276** ein Matroid. |
| **Binär auf drei Wegen** (alle 497 Matroide) | Kreis-Kokreis-Parität, Darstellung über GF(2) und „kein U(2,4)-Minor“ liefern bei **allen 497** dasselbe; nicht binär sind **0, 0, 0, 1 und 32** von 2, 5, 16, 68, 406 (n = 1 bis 5); das erste ist U(2,4). |
| **Wald: Kokreise gleich Schnitte** (Plan 7/8) | Die **24 Kokreise** sind genau die **24 minimalen Schnitte**; Größen (Größe: Zahl) 1: 1, 2: 1, 3: 2, 4: 1, 5: 6, 6: 9, 7: 4. |
| **Dualgraph auf Plänen** (200 Pläne je Größe, Seeds 0 bis 199) | Standort-Zeichnung kreuzungsfrei: 16, 8, 3, 2 von 200 (n = 6, 7, 8, 9). Abstrakt planar: **200, 179, 158, 141** von 200. Bei allen planaren Plänen mit 6 bis 8 Standorten (200, 179, 158) und den 41 planaren der ersten 60 Pläne mit 9 Standorten sind die Komplemente der Spannbäume **genau** die Spannbäume des Dualgraphen; die Flächenzahl ist jedes Mal m − n + 2 = n. Plan 7/8: planar, 7 Flächen, 180 Spannbäume. |
| **Minoren im Wald** (Plan 7/8) | Löschen gleich Leitung entfernen: **12 von 12**; Zusammenziehen gleich Endpunkte verschmelzen: **12 von 12**. |
| **Nicht graphisch** (Aufzählung einfacher Graphen auf Rang + 1 Knoten) | **Fano F7:** 7 Kanten bei 4 Knoten, aber nur 6 Knotenpaare. **U(2,4):** 4 Kanten, 3 Paare. **F7\*:** von 120 zusammenhängenden Graphen hat **keiner** 28 Spannbäume. **M\*(K3,3):** von 10 **keiner** 81. **M\*(K5):** von 331 506 zusammenhängenden einfachen Graphen auf 7 Knoten mit 10 Kanten **keiner** 125. **Kontrolle** M(K3,3): von 4 945 hat **10** Graphen 81 Spannbäume, und M(K3,3) wird gefunden. |

## Ehrliche Grenzen

- **Kleine Grundmengen.** Höchstens 16 Elemente; Basen, Kreise und Dual werden aus allen Teilmengen berechnet. Die Aufzählung aller Matroide geht nur bis 5 Elemente, die Suche nach einem U(2,4)-Minor nur bis 12 Elemente.
- **Rechenzeit bei 9 Standorten.** Der erste Aufruf eines Systems mit 16 Leitungen braucht einige Sekunden (am längsten das Anschluss-System); danach liegt das Ergebnis im Zwischenspeicher.
- **Der Dualgraph gilt nur beim Wald auf planaren Plänen,** auf einer neu gezeichneten Zeichnung, nicht auf den Standorten. Bei nichtplanaren Plänen (21 von 200 bei 7 Standorten) ist das Dual ein Matroid, aber **nicht graphisch**; das ist ein Satz von Tutte (Quelle: Vorlesungsskript, nicht die Originalarbeit) und hier nur an K5 und K3,3 durch Aufzählung nachgerechnet, nicht an den nichtplanaren Plänen.
- **„Nicht graphisch“ nur für fünf Matroide** und unter der Annahme, dass ein zusammenhängendes graphisches Matroid von einem einfachen Graphen auf Rang + 1 Knoten kommt; eine allgemeine Prüfung „ist dieses Matroid graphisch?“ gibt es nicht.
- **Binär, nicht regulär.** Dass regulär „weder F7 noch F7* als Minor“ heißt, wird nicht gezeigt.
- **Der Satz „binär genau ohne U(2,4)-Minor“ ist von Tutte** (nach Websuche, Zusammenfassungen, nicht die Originalarbeit); hier an allen 497 kleinen Matroiden nachgerechnet, nicht bewiesen.
- **Die Zeichnung der Fano-Ebene** ist eine Skizze (6 Strecken und ein Kreis für die 7 Geraden), keine Darstellung über einem Körper.

## Verifikation

- **Kern:** Dual, Kokreise, Minoren, Orthogonalität, GF(2)-Darstellung, U(2,4), graphisches Matroid, K4-Dualgraph und Bonds gegen Handrechnung auf Dreieck, parallelen Kanten mit Brücke, Fano und K4 (`tests/conftest.py`, `tests/test_algorithm.py`); Randfälle: ein Element (frei, Schleife), das freie und das Nullmatroid, Schleifen und parallele Elemente, die Grenze der U(2,4)-Suche, Nicht-Matroide mit gleich großen maximalen Mengen, nichtplanare Pläne (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_dualitaet.py`): Kokreise direkt aus der Definition (kleinste Mengen, die jede Basis treffen) und Dualrang über „E ∖ I enthält eine Basis“ auf 25 Zufallsmatroiden; Wald-Kokreise gegen die Bonds mit `networkx`; Minoren des Waldes gegen die Graphoperationen mit `networkx` (Multigraph, Schleifen); Flächen gegen die Einbettung von `networkx`, Spannbaumzahlen gegen Kirchhoff in beiden Graphen; Planarität gegen `networkx` für 200 Pläne; binär durch Aufzählung aller Matrizen und die Rekursion über alle Minoren gegen die App auf allen 497 kleinen Matroiden; Literaturwerte (Matroide 2, 5, 16, 68, 406; Spannbäume von K5 = 125 nach Cayley, K3,3 = 81; Fano).
- **Eigenschaften** (`tests/test_properties.py`): Dual des Duals, Dualrang, Basenzahl; Schleifen gegen Koschleifen; Kreis-Kokreis-Orthogonalität; graphische und GF(2)-Matroide sind binär; Löschen und Zusammenziehen vertauschen sich; Umbenennen der Elemente verträgt sich mit dem Dual; jeder Kokreis trifft jede Basis und ist minimal; Dualgraph und Bonds auf Zufallsplänen.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte an handgesetzten Werten; jedes Preset zeigt den versprochenen Effekt.
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Hauptansicht, Experimente, Spielwiese, Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** siehe `pytest --collect-only -q tests`.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Kreis und Schnitt, Kernfrage, vier Experimente, Spielwiese, Grenzen, Formeln |
| `dmo_constants.py` | Reglergrenzen, Systeme und ihre Namen, Prüfgrenzen, Farben, Presets |
| `dmo_scenario.py` | Plan: Standorte, mögliche Leitungen, Kosten (wie in den Stücken 1 bis 5) |
| `dmo_algorithm.py` | Kern: Unabhängigkeitssystem auf Bitmasken, Dual, Kokreise, Minoren, binär, graphisches Matroid, Suche nach einem Graphen, Dualgraph, Aufzählen aller Matroide |
| `dmo_systems.py` | die elf Systeme auf dem Plan mit Kabelfarben, die Fano-Ebene |
| `dmo_evaluation.py` | Kennzahlen, Ansichten der Experimente, Verdikte |
| `dmo_visualization.py` | Plan mit Schnitt, Dualgraph, Graphminor, Fano-Zeichnung, Balkendiagramm |
| `dmo_presets.py` | Permalink, Presets, Zufalls-Seed |
| `dmo_layout.py` | fester Kopf |
| `dmo_pdf_export.py` | PDF des aktuellen Systems |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Matroid-Schnitt (Stück 7) und -Vereinigung (Stück 9); Tutte-Polynom und Dualität (Stück 16).
- Regularität und die ausgeschlossenen Minoren F7, F7\* im Einzelnen; Darstellbarkeit über andere Körper als GF(2); die Theorie der Matroid-Minoren allgemein.
- Eine allgemeine Prüfung „ist dieses Matroid graphisch?“ (Aufzählung nur für fünf feste Matroide); der Dualgraph für andere Systeme als den Wald.
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly, numpy, networkx und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
