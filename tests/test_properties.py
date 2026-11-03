"""Eigenschaftstests (Schicht „Eigenschaften“, siehe Eigenschaftstests-Pilot): Invarianten auf Zufallsmatroiden mit festem Seed."""

import random

import dmo_algorithm as A
from dmo_algorithm import System

SEED = 20261108


def _random_matroid(rng, n):
    kind = rng.choice(["uniform", "gf2", "partition", "graphic"])
    if kind == "uniform":
        return A.uniform(rng.randint(0, n), n)
    if kind == "gf2":
        vec = [rng.getrandbits(3) for _ in range(n)]
        return System("gf2", n, [A.gf2_independent([vec[e] for e in range(n) if mask >> e & 1]) for mask in range(1 << n)])
    if kind == "partition":
        cls = [rng.randint(0, 2) for _ in range(n)]
        return System("partition", n, [len({cls[e] for e in range(n) if mask >> e & 1}) == bin(mask).count("1") for mask in range(1 << n)])
    v = rng.randint(2, 5)
    return A.graph_system(v, [(rng.randrange(v), rng.randrange(v)) for _ in range(n)])


def _matroids(count=60):
    rng = random.Random(SEED)
    return [_random_matroid(rng, rng.randint(2, 6)) for _ in range(count)]


def test_the_dual_of_the_dual_is_the_matroid_and_the_dual_rank_is_size_minus_rank():
    for s in _matroids():
        assert s.is_matroid
        d = A.dual(s)
        assert d.is_matroid and A.dual(d).ok == s.ok and d.rank == s.m - s.rank and len(d.bases) == len(s.bases)
        assert A.dual_rank_formula_holds(s, d)


def test_loops_become_coloops_and_back():
    for s in _matroids():
        d = A.dual(s)
        loops = {e for e in range(s.m) if not s.ok[1 << e]}
        coloops = {e for e in range(s.m) if all(b >> e & 1 for b in s.bases)}
        dual_loops = {e for e in range(s.m) if not d.ok[1 << e]}
        assert dual_loops == coloops and {e for e in range(s.m) if all(b >> e & 1 for b in d.bases)} == loops


def test_circuits_and_cocircuits_are_orthogonal_and_binary_matroids_meet_evenly():
    for s in _matroids():
        d = A.dual(s)
        assert A.orthogonal(s, d)
        ways = A.binary_ways(s, d)
        assert ways["parity"] == ways["rep"] == ways["no_u24"]


def test_graphic_and_gf2_matroids_are_binary_and_non_graphic_examples_are_not():
    rng = random.Random(SEED + 1)
    for _ in range(25):
        v = rng.randint(2, 5)
        g = A.graph_system(v, [(rng.randrange(v), rng.randrange(v)) for _ in range(rng.randint(2, 6))])
        assert A.binary_ways(g, A.dual(g))["parity"]
    assert not A.binary_ways(A.uniform(2, 5), A.dual(A.uniform(2, 5)))["parity"]


def test_deletion_and_contraction_commute_for_different_elements_and_stay_matroids():
    for s in _matroids(30):
        if s.m < 3:
            continue
        for e, f in ((0, 1), (1, 0)):
            g = f - 1 if f > e else f                                                    # Nummer von f nach dem Entfernen von e
            h = e - 1 if e > f else e
            a = A.delete(A.contract(s, e), g)
            b = A.contract(A.delete(s, f), h)
            assert a.is_matroid and b.is_matroid
        assert A.delete(A.contract(s, 0), 0).ok == A.contract(A.delete(s, 1), 0).ok       # {0, 1}: erst 0 ziehen, dann (alte) 1 löschen; erst 1 löschen, dann 0 ziehen


def test_relabeling_commutes_with_the_dual_and_keeps_the_cocircuit_sizes():
    rng = random.Random(SEED + 2)
    for s in _matroids(25):
        perm = list(range(s.m))
        rng.shuffle(perm)
        ok = [False] * (1 << s.m)
        for i in s.ind:
            ok[sum(1 << perm[e] for e in range(s.m) if i >> e & 1)] = True
        t = System("neu", s.m, ok)
        assert sorted(A.popcount(c) for c in A.cocircuits(A.dual(t))) == sorted(A.popcount(c) for c in A.cocircuits(A.dual(s)))
        assert A.dual(t).ok == [A.dual(s).ok[sum(1 << perm.index(e) for e in range(s.m) if mask >> e & 1)] for mask in range(1 << s.m)]


def test_cocircuit_hits_every_basis_and_removing_an_element_misses_one():
    for s in _matroids(30):
        d = A.dual(s)
        for k in A.cocircuits(d):
            assert all(b & k for b in s.bases)
            for e in range(s.m):
                if k >> e & 1 and k != 1 << e:
                    assert not all(b & (k & ~(1 << e)) for b in s.bases)


def test_planar_plans_have_a_dual_graph_whose_trees_are_the_complements():
    from dmo_scenario import make_instance
    checked = 0
    for seed in range(40):
        inst = make_instance(6, seed)
        pos = A.planar_pos(inst)
        if pos is None:
            continue
        d = A.dual_drawing(inst, pos)
        chk = A.dual_tree_check(inst, d)
        assert chk["equal"] and chk["euler"] and chk["faces"] == inst.n
        checked += 1
    assert checked == 40                                               # alle Pläne mit 6 Standorten und Seeds 0 bis 39 sind planar


def test_wald_cocircuits_are_exactly_the_bonds_of_random_plans():
    from dmo_scenario import make_instance
    import dmo_systems as S
    for n, seed in ((6, 4), (6, 9), (7, 2)):
        inst = make_instance(n, seed)
        d = A.dual(S.get_system("wald", n, seed))
        assert {c for c, _ in A.bonds(inst)} == set(d.circuits)
        for c, side in A.bonds(inst):
            sides = A.node_sides(inst, c)
            assert set(sides) == {0, 1} and sum(1 for s in sides if s == 0) == bin(side).count("1")
