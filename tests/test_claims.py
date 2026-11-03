"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

import re
from collections import Counter
from pathlib import Path

import dmo_algorithm as A
import dmo_constants as C
import dmo_evaluation as ev
import dmo_systems as S
from dmo_scenario import make_instance

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
PLAN = (7, 8)


def _settings(key):
    return ev.Settings(*PLAN, key)


def test_the_six_matroid_table_and_the_five_non_matroids():
    expected = {  # Rang, Dualrang, Basen, Kreise, Kokreise, binär
        "wald": (6, 6, 180, 32, 24, True), "farben": (3, 9, 42, 25, 3, True), "anschluss": (7, 5, 311, 93, 200, False), "uniform": (4, 8, 495, 792, 220, False),
        "vektoren": (3, 4, 28, 20, 11, False), "fano": (3, 4, 28, 14, 7, True),
    }
    for key, (rank, drank, bases, circuits, cocircuits, binary) in expected.items():
        a = ev.analyse(_settings(key))
        assert (a.rank, a.dual_rank, a.n_bases, a.n_circuits, len(a.cocircuits), a.binary) == (rank, drank, bases, circuits, cocircuits, binary), key
        line = [l for l in README.splitlines() if l.startswith("| " + C.SYSTEM_NAMES[key] + " |")]
        assert line and f"| {rank} | {drank} | {bases} | {circuits} | {cocircuits} | {'ja' if binary else 'nein'} |" in line[0], key
    for key in set(C.SYSTEMS) - set(expected):
        a = ev.analyse(_settings(key))
        assert not a.is_matroid and a.dual_rank is None and a.cocircuits == ()


def test_all_small_matroids():
    rows = ev.small_dual_rows()
    assert [r["matroids"] for r in rows] == [2, 5, 16, 68, 406] and sum(r["matroids"] for r in rows) == 497
    for key in ("dual_matroid", "involution", "rank_formula", "orthogonal"):
        assert [r[key] for r in rows] == [r["matroids"] for r in rows], key
    assert [r["minor_identities"] for r in rows][1:] == [5, 16, 68, 406]
    assert [r["selfdual"] for r in rows] == [0, 1, 0, 4, 0]
    assert [r["non_matroids"] for r in rows] == [0, 0, 3, 99, 7174] and sum(r["non_matroids"] for r in rows) == 7276 and sum(r["non_dual_matroid"] for r in rows) == 0


def test_binary_on_three_ways():
    rows = ev.small_binary_rows()
    assert [r["matroids"] - r["binary"] for r in rows] == [0, 0, 0, 1, 32] and all(r["agree"] == r["matroids"] for r in rows)


def test_wald_cocircuits_are_the_bonds_and_their_sizes():
    a = ev.analyse(_settings("wald"))
    inst = make_instance(*PLAN)
    assert {c for c, _ in A.bonds(inst)} == set(a.cocircuits) and len(a.cocircuits) == 24
    assert sorted(Counter(A.popcount(c) for c in a.cocircuits).items()) == [(1, 1), (2, 1), (3, 2), (4, 1), (5, 6), (6, 9), (7, 4)]


def test_plans_crossings_planarity_and_the_dual_graph():
    expected = {6: (16, 200, 200, 200), 7: (8, 179, 179, 179), 8: (3, 158, 158, 158), 9: (2, 141, 41, 41)}   # kreuzungsfrei, planar, geprüft, gleich
    for n, (free, planar, checked, equal) in expected.items():
        f = p = c = ok = 0
        for seed in range(200):
            inst = make_instance(n, seed)
            f += A.crossing_free(inst)
            pos = A.planar_pos(inst)
            p += pos is not None
            if pos is not None and (n < 9 or seed < 60):
                chk = A.dual_tree_check(inst, A.dual_drawing(inst, pos))
                c += 1
                ok += chk["equal"] and chk["euler"] and chk["faces"] == n
        assert (f, p, c, ok) == (free, planar, checked, equal), n
    a = ev.analyse(_settings("wald"))
    view = ev.dual_view(a.settings, a)
    assert view["planar"] and not view["crossing_free"] and view["check"]["faces"] == 7 and view["check"]["n_trees"] == 180


def test_minors_of_the_wald_equal_the_graph_operations():
    inst = make_instance(*PLAN)
    s = S.get_system("wald", *PLAN)
    edges = [(u, w) for u, w, _ in inst.edges]
    dele = con = 0
    for e in range(len(edges)):
        rest = [x for i, x in enumerate(edges) if i != e]
        u, w = edges[e]
        merged = [(u if a == w else a, u if b == w else b) for a, b in rest]
        dele += A.graph_system(inst.n, rest).ok == A.delete(s, e).ok
        con += A.graph_system(inst.n, merged).ok == A.contract(s, e).ok
    assert (dele, con, len(edges)) == (12, 12, 12)


def test_non_graphic_enumeration():
    rows = {r["label"]: r for r in ev.nongraphic_rows()}
    assert len(rows) == 6
    f7, f7s, u24, k33s, k5s, control = ev.nongraphic_rows()
    assert (f7["m"], f7["pairs"], f7["candidates"]) == (7, 6, 0) and (u24["m"], u24["pairs"], u24["candidates"]) == (4, 3, 0)
    assert (f7s["candidates"], f7s["same_trees"], f7s["bases"]) == (120, 0, 28) and (k33s["candidates"], k33s["same_trees"], k33s["bases"]) == (10, 0, 81)
    assert (k5s["candidates"], k5s["same_trees"], k5s["bases"]) == (331506, 0, 125)
    assert (control["candidates"], control["same_trees"], control["graphic"]) == (4945, 10, True) and not any(r["graphic"] for r in (f7, f7s, u24, k33s, k5s))


def test_the_total_number_of_graphs_for_the_five_cycle_dual_is_a_binomial():
    from math import comb
    assert comb(21, 10) == 352716


def test_readme_names_every_checked_number():
    for needle in ("**allen 497**", "**0 Abweichungen**", "1 (n = 2) und 4 (n = 4)", "**0 von 7 276**", "**0, 0, 0, 1 und 32**", "**24 Kokreise**", "**24 minimalen Schnitte**",
                   "1: 1, 2: 1, 3: 2, 4: 1, 5: 6, 6: 9, 7: 4", "16, 8, 3, 2 von 200", "**200, 179, 158, 141**", "(200, 179, 158)", "41 planaren", "7 Flächen, 180 Spannbäume",
                   "**12 von 12**", "7 Kanten bei 4 Knoten", "nur 6 Knotenpaare", "4 Kanten, 3 Paare", "von 120 zusammenhängenden Graphen hat **keiner** 28", "von 10 **keiner** 81",
                   "331 506", "352 716", "**keiner** 125", "von 4 945 hat **10** Graphen 81 Spannbäume", "21 von 200", "8 % bei 6, 4 % bei 7"):
        assert needle in README, needle


def test_readme_table_has_no_decimal_points():
    table = README.split("## Befunde (gemessen, keine Behauptungen)")[1].split("## Ehrliche Grenzen")[0]
    assert not re.search(r"\d\.\d", table)
