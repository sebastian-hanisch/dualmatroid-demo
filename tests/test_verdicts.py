"""Verdikte (reine Funktionen in dmo_evaluation.py) an handgesetzten Werten: jeder Zweig, jede Zahl im Text (DEMO-PLAYBOOK §4)."""

import dmo_algorithm as A
import dmo_evaluation as ev


def _a(system, n=7, seed=8):
    return ev.analyse(ev.Settings(n, seed, system))


# --- Hauptansicht ------------------------------------------------------------------------------------------------------------------------


def test_cut_verdict_for_the_wald_names_the_two_sides_and_the_even_intersections():
    a = _a("wald")
    view = {"cut": a.cocircuits[2], "sizes": {0: 20, 2: 12}, "sides": [0, 1, 1, 1, 1, 1, 0]}
    kind, text = ev.verdict_cut(a, view)
    assert kind == "success" and "ist ein **Schnitt**" in text and "zwei Teile mit 2 und 5 Standorten" in text and "Keiner der 32 Kreise" in text and "**gerade**" in text
    assert "(3 Elemente)" in text


def test_cut_verdict_for_other_systems_and_for_odd_intersections():
    a = _a("uniform")
    view = {"cut": a.cocircuits[0], "sizes": {2: 36, 3: 252, 4: 378, 5: 126}, "sides": None}
    kind, text = ev.verdict_cut(a, view)
    assert kind == "info" and "eine kleinste Menge, die jede Basis trifft" in text and "ungerade Durchschnitte kommen vor (3 Elemente bei 252 Kreisen, 5 Elemente bei 126 Kreisen)" in text and "nicht binär" in text
    kind, text = ev.verdict_cut(_a("fano"), {"cut": _a("fano").cocircuits[0], "sizes": {0: 2, 2: 12}, "sides": None})
    assert kind == "success" and "Keiner der 14 Kreise" in text and "(4 Elemente)" in text


def test_cut_verdict_errors_when_an_intersection_has_exactly_one_element():
    a = _a("wald")
    assert ev.verdict_cut(a, {"cut": a.cocircuits[2], "sizes": {1: 1, 2: 3}, "sides": [0] * 7})[0] == "error"


def test_sizes_table_has_shares():
    rows = ev.sizes_table({"sizes": {0: 20, 2: 12}}, 32)
    assert rows == [{"Elemente im Durchschnitt": 0, "Zahl der Kreise": 20, "Anteil": "62,5 %"}, {"Elemente im Durchschnitt": 2, "Zahl der Kreise": 12, "Anteil": "37,5 %"}]


def test_no_dual_verdict_branches():
    kind, text = ev.verdict_no_dual(_a("budget"))
    assert kind == "warning" and "verschiedene Größen (196 mit 4" not in text and "15 mit 4, 128 mit 5, 53 mit 6" in text and "kein **Dual**" not in text and "**kein Dual**" in text
    assert "dieselbe Größe" in ev.verdict_no_dual(_a("wald_farben"))[1]


# --- Experiment 1 ----------------------------------------------------------------------------------------------------------------------


def test_dual_graph_verdict_branches():
    a = _a("wald")
    ok = {"available": True, "planar": True, "crossing_free": False, "check": {"equal": True, "euler": True, "faces": 7, "n_trees": 180}}
    kind, text = ev.verdict_dual_graph(a, ok)
    assert kind == "success" and "neu gezeichnet" in text and "7 Flächen (Euler: 12 − 7 + 2 = 7)" in text and "Alle 180 Spannbäume" in text
    assert "neu gezeichnet" not in ev.verdict_dual_graph(a, {**ok, "crossing_free": True})[1]
    assert ev.verdict_dual_graph(a, {**ok, "check": {**ok["check"], "equal": False}})[0] == "error"
    assert ev.verdict_dual_graph(a, {**ok, "check": {**ok["check"], "euler": False}})[0] == "error"
    kind, text = ev.verdict_dual_graph(a, {"available": True, "planar": False, "crossing_free": False})
    assert kind == "warning" and "nicht planar" in text and "Whitney" in text
    assert ev.verdict_dual_graph(a, {"available": False})[0] == "info"


# --- Experiment 2 ----------------------------------------------------------------------------------------------------------------------


def test_minor_verdicts_for_both_operations_and_the_error_branches():
    a = _a("wald")
    s = ev.Settings(system="wald")
    for op, needle in (("loeschen", "Löschen von A–B in M, Zusammenziehen von A–B in M*: (M ∖ e)* = M* / e"), ("ziehen", "Zusammenziehen von A–B in M, Löschen von A–B in M*: (M / e)* = M* ∖ e")):
        view = ev.minor_view(s, 0, op)
        kind, text = ev.verdict_minor(a, view)
        assert kind == "success" and needle in text and "Beim Wald heißt" in text
        assert ev.minor_rows(a, view)[0] == {"Matroid": "M", "Elemente": 12, "Rang": 6, "Basen": "180", "Kreise": "32"}
    bad = {**view, "ids": {**view["ids"], "delete_dual": False}}
    assert ev.verdict_minor(a, bad)[0] == "error"
    assert ev.verdict_minor(a, {**view, "ids": {**view["ids"], "delete_matroid": False}})[0] == "error"
    kind, text = ev.verdict_minor(_a("fano"), ev.minor_view(ev.Settings(system="fano"), 0, "ziehen"))
    assert kind == "success" and "Beim Wald" not in text and "Rang 4, 12 Basen" in text


def test_small_dual_verdict_and_table():
    rows = tuple(A.small_dual_row(n) for n in range(1, 4))
    kind, text = ev.verdict_small_dual(rows)
    assert kind == "success" and "Bei allen 23 Matroiden mit höchstens 3 Elementen" in text and "**0 Abweichungen**" in text and "Bei allen 3 Nicht-Matroiden" in text and "Beschriftet selbstdual sind 1 bei n = 2" in text
    table = ev.small_dual_table(rows)
    assert table[0]["Minoren-Identitäten"] == "–" and table[2]["Nicht-Matroide mit Dual"] == "0 von 3" and table[1]["selbstdual"] == "1"
    broken = tuple({**r, "involution": r["involution"] - 1} if r["n"] == 3 else r for r in rows)
    assert ev.verdict_small_dual(broken)[0] == "error"


# --- Experiment 3 ----------------------------------------------------------------------------------------------------------------------


def test_binary_verdicts():
    a = _a("fano")
    view = {"ways": {"parity": True, "rep": True, "no_u24": True}, "with_minor": True, "u24": None, "odd": None}
    kind, text = ev.verdict_binary(a, view)
    assert kind == "success" and "**binär**" in text and "keinen U(2,4)-Minor" in text and "nur bis" not in text
    assert "nur bis 12 Elemente" in ev.verdict_binary(a, {**view, "with_minor": False, "ways": {**view["ways"], "no_u24": None}})[1]
    u = _a("uniform")
    nonbin = {"ways": {"parity": False, "rep": False, "no_u24": False}, "with_minor": True, "u24": (15, 0), "odd": (7, 7)}
    kind, text = ev.verdict_binary(u, nonbin)
    assert kind == "info" and "**nicht binär**" in text and "in 3 Elementen (ungerade)" in text and "U(2,4)" in text
    assert "U(2,4)" not in ev.verdict_binary(u, {**nonbin, "with_minor": False, "u24": None, "ways": {**nonbin["ways"], "no_u24": None}})[1]
    assert ev.verdict_binary(u, {**nonbin, "ways": {"parity": False, "rep": True, "no_u24": False}})[0] == "error"
    assert [r["binär?"] for r in ev.binary_rows(u, nonbin)] == ["nein", "nein", "nein"]


def test_small_binary_verdict_and_table():
    rows = tuple(A.small_binary_row(n) for n in range(1, 5))
    kind, text = ev.verdict_small_binary(rows)
    assert kind == "success" and "Bei allen 91 Matroiden mit höchstens 4 Elementen" in text and "0, 0, 0, 1 von 2, 5, 16, 68" in text
    assert ev.small_binary_table(rows)[3] == {"Elemente n": 4, "Matroide": "68", "binär": "67", "nicht binär": "1", "drei Wege gleich": "68"}
    assert ev.verdict_small_binary(tuple({**r, "agree": r["agree"] - 1} if r["n"] == 4 else r for r in rows))[0] == "error"


# --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------


def test_nongraphic_verdict_and_error_branch():
    rows = ev.nongraphic_rows()
    kind, text = ev.verdict_nongraphic(rows)
    assert kind == "success" and "331 506 zusammenhängende" in text and "**125** Spannbäume" in text and "M(K3,3) wird dagegen als graphisch gefunden" in text
    table = ev.nongraphic_table(rows)
    assert [r["graphisch"] for r in table] == ["nein"] * 5 + ["ja"] and table[1]["zusammenhängende einfache Graphen"] == "120" and table[0]["Knotenpaare auf Rang + 1 Knoten"] == 6
    bad = tuple({**r, "graphic": True} if i == 1 else r for i, r in enumerate(rows))
    assert ev.verdict_nongraphic(bad)[0] == "error"
    assert ev.verdict_nongraphic(tuple({**r, "graphic": False} if i == 5 else r for i, r in enumerate(rows)))[0] == "error"


# --- Spielwiese ------------------------------------------------------------------------------------------------------------------------


def test_play_verdicts():
    s = ev.Settings(system="wald")
    a = ev.analyse(s)
    co = ev.verdict_play(a, ev.play_check(s, a.cocircuits[2]))
    assert co[0] == "success" and "ist ein **Kokreis**" in co[1] and "minimaler Schnitt" in co[1]
    sys_ = ev.system_of(s)
    ci = ev.verdict_play(a, ev.play_check(s, sys_.circuits[0]))
    assert ci[0] == "success" and "ist ein **Kreis**" in ci[1]
    both = ev.verdict_play(a, {"empty": False, "mask": 3, "circuit": True, "cocircuit": True, "independent": False, "matroid": True, "meets_all": True})
    assert "ein **Kreis** (kleinste unzulässige Menge) und zugleich ein **Kokreis**" in both[1]
    dependent = ev.verdict_play(a, {"empty": False, "mask": 3, "circuit": False, "cocircuit": False, "independent": False, "matroid": True, "meets_all": True})
    assert dependent[0] == "info" and "unzulässig, aber kein Kreis" in dependent[1] and "enthält einen Kokreis" in dependent[1]
    miss = ev.verdict_play(a, {"empty": False, "mask": 1, "circuit": False, "cocircuit": False, "independent": True, "matroid": True, "meets_all": False})
    assert "ist zulässig, also weder Kreis noch Kokreis" in miss[1] and "Es gibt eine Basis, die sie nicht trifft" in miss[1]


def test_number_helpers():
    assert ev.de(1.5, 1) == "1,5" and ev.prozent(0.625) == "62,5" and ev.zahl(1234567) == "1 234 567" and ev.elemente(1) == "1 Element" and ev.elemente(3) == "3 Elemente"
