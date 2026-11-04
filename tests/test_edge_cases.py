"""Randfälle (DEMO-PLAYBOOK §4): kleinste Systeme, Schleifen, Brücken, Reglergrenzen, Nicht-Matroide."""

import pytest

import dmo_algorithm as A
import dmo_constants as C
import dmo_evaluation as ev
import dmo_systems as S
from dmo_algorithm import System


def test_a_single_free_element_has_a_loop_as_its_dual():
    s = System("frei", 1, [True, True])
    d = A.dual(s)
    assert d.ok == [True, False] and A.cocircuits(d) == [1] and A.dual(d).ok == s.ok          # Koschleife im Matroid, Schleife im Dual


def test_a_single_loop_has_a_free_element_as_its_dual():
    s = System("schleife", 1, [True, False])
    assert A.dual(s).ok == [True, True] and A.cocircuits(A.dual(s)) == []


def test_the_free_matroid_has_no_circuits_and_all_singletons_as_cocircuits():
    free = System("frei", 3, [True] * 8)
    assert free.circuits == [] and A.cocircuits(A.dual(free)) == [1, 2, 4]
    assert A.orthogonal(free, A.dual(free)) and A.even_intersections(free, A.dual(free)) and A.intersection_sizes(free, 1) == {}


def test_the_zero_matroid_dualizes_to_the_free_matroid():
    zero = System("null", 3, [mask == 0 for mask in range(8)])
    assert zero.rank == 0 and A.dual(zero).ok == [True] * 8


def test_binary_ways_on_a_system_with_loops_and_parallel_elements():
    s = System("gemischt", 3, [not (mask & 1) and not (mask & 2 and mask & 4) for mask in range(8)])      # Element 0 ist Schleife, 1 und 2 sind parallel
    assert s.is_matroid
    w = A.binary_ways(s, A.dual(s))
    assert w == {"parity": True, "rep": True, "no_u24": True}


def test_u24_minor_needs_four_elements_and_ignores_a_matroid_without_it():
    assert A.u24_minor(System("klein", 3, [True] * 8)) is None
    assert A.u24_minor(A.uniform(1, 5)) is None and A.u24_minor(A.uniform(2, 5)) is not None and A.u24_minor(A.uniform(3, 5)) is not None


def test_non_matroids_have_no_dual_matroid(paarung3):
    assert not A.dual(paarung3).is_matroid
    a = ev.analyse(ev.Settings(system="paarung"))
    assert not a.is_matroid and a.dual_rank is None and a.cocircuits == () and a.binary is None
    kind, text = ev.verdict_no_dual(a)
    assert kind == "warning" and "kein Dual" in text and "2 mit 2, 16 mit 3" in text


def test_a_non_matroid_with_equal_sized_maximal_sets_has_a_different_reason():
    a = ev.analyse(ev.Settings(system="wald_farben"))
    kind, text = ev.verdict_no_dual(a)
    assert kind == "warning" and "dieselbe Größe" in text and "40 mit 3" in text and "Basenaustausch" in text


def test_slider_limits_build_and_analyse_for_every_matroid_system():
    for n in (C.N_MIN, C.N_MAX):
        for key in C.MATROID_SYSTEMS:
            if key == "anschluss" and n == C.N_MAX:
                continue
            a = ev.analyse(ev.Settings(n, C.DEFAULT_SEED, key))
            assert a.is_matroid and a.dual_rank == a.m - a.rank and a.cocircuits


def test_u24_search_is_skipped_above_the_limit():
    s = ev.Settings(9, 8, "uniform")
    a = ev.analyse(s)
    assert a.m == 16 > C.U24_MAX_ELEMENTS
    view = ev.binary_view(s, a)
    assert not view["with_minor"] and view["ways"]["no_u24"] is None and view["ways"]["parity"] is False
    assert "nicht gerechnet" in ev.binary_rows(a, view)[2]["binär?"]


def test_default_cut_index_skips_bridges_and_falls_back_to_the_first():
    wald = ev.analyse(ev.Settings(system="wald"))
    assert A.popcount(wald.cocircuits[0]) == 1 and A.popcount(wald.cocircuits[ev.default_cut_index(wald)]) >= 3 and ev.default_cut_index(wald) == 2
    farben = ev.analyse(ev.Settings(system="farben"))
    assert ev.default_cut_index(farben) == 0 or A.popcount(farben.cocircuits[ev.default_cut_index(farben)]) >= 3
    non = ev.analyse(ev.Settings(system="paarung"))
    assert ev.default_cut_index(non) == 0


def test_dual_view_is_unavailable_for_other_systems_and_for_non_planar_plans():
    a = ev.analyse(ev.Settings(system="fano"))
    assert not ev.dual_view(a.settings, a)["available"] and ev.verdict_dual_graph(a, ev.dual_view(a.settings, a))[0] == "info"
    nonplanar = next(seed for seed in range(200) if A.planar_pos(S.make_instance(7, seed)) is None)
    s = ev.Settings(7, nonplanar, "wald")
    wa = ev.analyse(s)
    view = ev.dual_view(s, wa)
    kind, text = ev.verdict_dual_graph(wa, view)
    assert view["available"] and not view["planar"] and kind == "warning" and "nicht planar" in text and "Whitney" in text


def test_minor_of_the_smallest_system_and_of_a_two_element_system():
    s = System("zwei", 2, [True, True, True, True])
    d = A.dual(s)
    assert all(A.minor_identities(s, d, e).values() for e in range(2))
    assert A.delete(s, 0).ok == [True, True] == A.contract(s, 0).ok


def test_play_check_covers_empty_independent_circuit_cocircuit_and_non_matroid():
    s = ev.Settings(system="wald")
    a = ev.analyse(s)
    assert ev.verdict_play(a, ev.play_check(s, 0))[1] == "Wählen Sie mindestens ein Element."
    co = a.cocircuits[2]
    assert ev.verdict_play(a, ev.play_check(s, co))[0] == "success" and "Kokreis" in ev.verdict_play(a, ev.play_check(s, co))[1]
    assert ev.verdict_play(a, ev.play_check(s, 1))[0] == "info"
    sys_ = ev.system_of(s)
    circuit = sys_.circuits[0]
    assert "Kreis" in ev.verdict_play(a, ev.play_check(s, circuit))[1]
    n = ev.Settings(system="paarung")
    na = ev.analyse(n)
    assert "kein Matroid" in ev.verdict_play(na, ev.play_check(n, 7))[1]


def test_check_for_an_unknown_system_name_fails_early():
    with pytest.raises(ValueError):
        S.build_system("gibtsnicht", S.make_instance(6, 1))
