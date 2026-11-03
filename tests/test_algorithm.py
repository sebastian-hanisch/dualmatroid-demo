"""Einheiten des Kerns an Mini-Instanzen von Hand (DEMO-PLAYBOOK §1b, §4)."""

import pytest

import dmo_algorithm as A
from dmo_algorithm import System


def test_dual_of_the_triangle_is_u13_with_the_three_cuts_as_cocircuits(dreieck):
    d = A.dual(dreieck)
    assert d.is_matroid and d.rank == 1 and sorted(d.bases) == [1, 2, 4]                      # c, b, a
    assert A.cocircuits(d) == [3, 5, 6]                                                          # {a, b}, {a, c}, {b, c}
    assert A.dual_rank_formula_holds(dreieck, d) and A.dual(d).ok == dreieck.ok


def test_dual_of_parallel_edges_with_a_bridge(parallel):
    d = A.dual(parallel)
    assert sorted(d.bases) == [1, 2] and d.rank == 1                                           # a und b sind im Dual parallel, c ist dort eine Schleife
    assert A.cocircuits(d) == [4, 3]                                                             # {c} (Brücke), {a, b}
    assert not d.ok[4] and d.ok[1] and d.ok[2]


def test_fano_dual_has_rank_four_and_seven_cocircuits_of_size_four(fano):
    d = A.dual(fano)
    assert d.rank == 4 and len(d.bases) == 28 and len(A.cocircuits(d)) == 7 and {A.popcount(c) for c in d.circuits} == {4}
    lines = [c for c in fano.circuits if A.popcount(c) == 3]
    assert sorted(A.cocircuits(d)) == sorted(fano.full ^ line for line in lines)                  # die Komplemente der 7 Geraden


def test_minors_of_the_triangle_by_hand(dreieck):
    de = A.delete(dreieck, 0)                       # Elemente b, c: alle Mengen mit höchstens 2 Elementen
    co = A.contract(dreieck, 0)                     # I zulässig, wenn I + a höchstens 2 Elemente hat: ∅, b, c
    assert de.ok == [True, True, True, True] and co.ok == [True, True, True, False]
    d = A.dual(dreieck)
    assert all(A.minor_identities(dreieck, d, e).values() for e in range(3))
    assert A.minor(dreieck, 1, "loeschen").ok == A.delete(dreieck, 1).ok and A.minor(dreieck, 1, "ziehen").ok == A.contract(dreieck, 1).ok


def test_contracting_a_loop_equals_deleting_it():
    s = System("Schleife", 2, [True, False, True, False])       # Element 0 ist eine Schleife, Element 1 frei
    assert A.contract(s, 0).ok == A.delete(s, 0).ok == [True, True]


def test_intersection_sizes_and_the_orthogonality_checks(dreieck, fano):
    d = A.dual(dreieck)
    assert A.intersection_sizes(dreieck, 3) == {2: 1}                # der Kreis {a, b, c} trifft {a, b} in 2 Elementen
    assert A.orthogonal(dreieck, d) and A.even_intersections(dreieck, d) and A.odd_pair(dreieck, d) is None          # ein graphisches Matroid ist binär
    u24 = A.uniform(2, 4)
    assert A.orthogonal(u24, A.dual(u24)) and not A.even_intersections(u24, A.dual(u24)) and A.odd_pair(u24, A.dual(u24)) == (7, 7)
    df = A.dual(fano)
    assert A.orthogonal(fano, df) and A.even_intersections(fano, df) and A.odd_pair(fano, df) is None


def test_u24_is_the_only_non_binary_matroid_on_four_elements():
    u24 = A.uniform(2, 4)
    w = A.binary_ways(u24, A.dual(u24))
    assert w == {"parity": False, "rep": False, "no_u24": False} and A.u24_minor(u24) == (15, 0)
    assert A.u24_minor(A.uniform(2, 3)) is None


def test_fano_is_binary_on_all_three_ways(fano):
    assert A.binary_ways(fano, A.dual(fano)) == {"parity": True, "rep": True, "no_u24": True}
    assert A.gf2_vectors(fano)[fano.bases[0].bit_length() - 1] != 0


def test_graph_system_of_the_triangle_is_the_triangle_matroid(dreieck):
    assert A.graph_system(3, [(0, 1), (0, 2), (1, 2)]).ok == dreieck.ok
    assert A.graph_system(2, [(0, 0), (0, 1)]).ok == [True, False, True, False]                 # eine Schleife ist nie zulässig


def test_k4_is_isomorphic_to_its_dual_but_not_equal_as_labeled():
    k4 = A.graph_system(4, [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3)])
    d = A.dual(k4)
    assert len(k4.bases) == 16 and A.isomorphic(k4, d) and d.ok != k4.ok


def test_graphic_search_hand_cases(fano):
    r = A.graphic_search(fano, "F7")
    assert not r["graphic"] and r["candidates"] == 0 and "7 Kanten" in r["reason"]
    tri = A.graphic_search(A.graph_system(3, [(0, 1), (0, 2), (1, 2)]), "Dreieck")
    assert tri["graphic"] and sorted(tri["edges"]) == [(0, 1), (0, 2), (1, 2)] and tri["candidates"] == 1 and tri["same_trees"] == 1
    assert not A.graphic_search(A.uniform(2, 4), "U24")["graphic"]


def test_k4_drawing_has_four_faces_and_a_dual_isomorphic_to_k4(k4):
    pos = dict(enumerate(k4.points))
    d = A.dual_drawing(k4, pos)
    assert d["faces"] == 4 and len({frozenset(e) for e in d["dual_edges"]}) == 6 and all(a != b for a, b in d["dual_edges"])        # Dual von K4 ist K4
    chk = A.dual_tree_check(k4, d)
    assert chk == {"n_trees": 16, "dual_trees": 16, "equal": True, "faces": 4, "euler": True}
    assert d["outer"] in range(4) and sum(1 for f in range(4) if f != d["outer"]) == 3


def test_bonds_of_k4(k4):
    b = A.bonds(k4)
    assert len(b) == 7 and sorted(A.popcount(c) for c, _ in b) == [3, 3, 3, 3, 4, 4, 4]
    assert {c for c, _ in b} == set(A.dual(A.graph_system(4, [(u, w) for u, w, _ in k4.edges])).circuits)


def test_node_sides_split_the_plan_into_two_parts(k4):
    cut, side = next((c, s) for c, s in A.bonds(k4) if A.popcount(c) == 3 and s == 1)           # Knoten 0 allein
    assert A.node_sides(k4, cut) == [0, 1, 1, 1]


def test_spanning_trees_of_k4(k4):
    assert len(A.spanning_trees(4, [(u, w) for u, w, _ in k4.edges])) == 16


def test_crossing_free_detects_a_crossing():
    from dmo_scenario import Instance
    crossed = Instance(((0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)), ((0, 1, 1.0), (2, 3, 1.0)))
    assert not A.crossing_free(crossed)
    assert A.crossing_free(Instance(((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)), ((0, 1, 1.0), (2, 3, 1.0))))


def test_small_rows_for_three_and_four_elements():
    r3 = A.small_dual_row(3)
    assert (r3["systems"], r3["matroids"], r3["non_matroids"], r3["dual_matroid"], r3["minor_identities"], r3["selfdual"], r3["non_dual_matroid"]) == (19, 16, 3, 16, 16, 0, 0)
    r4 = A.small_dual_row(4)
    assert (r4["matroids"], r4["selfdual"], r4["orthogonal"], r4["rank_formula"], r4["non_dual_matroid"]) == (68, 4, 68, 68, 0)
    b4 = A.small_binary_row(4)
    assert b4 == {"n": 4, "matroids": 68, "binary": 67, "agree": 68}


def test_all_systems_counts():
    assert [len(A.all_systems(n)) for n in range(1, 5)] == [2, 5, 19, 167]


def test_independent_from_bases_roundtrip(dreieck):
    assert A.independent_from_bases(3, dreieck.bases) == dreieck.ok
