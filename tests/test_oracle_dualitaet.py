"""Orakel (ORACLE-PLAYBOOK §5): anderer Rechenweg als der der Demo.

1. Dual: Kokreise direkt aus der Definition (kleinste Mengen, die jede Basis treffen), Dualrang über „E ∖ I enthält eine Basis“, beides auf Zufallsmatroiden.
2. Wald: Kokreise gegen die Bonds mit networkx (beide Seiten zusammenhängend); Minoren gegen die Graphoperationen mit networkx (Multigraph, Schleifen).
3. Dualgraph: Flächen gegen die Einbettung von networkx (Halbkantenfolgen), Spannbaumzahlen gegen Kirchhoff (numpy) in beiden Graphen.
4. Binär: Darstellung durch Aufzählung aller Matrizen zu einer festen Basis und der U(2,4)-Minor durch die Rekursion über alle Löschungen und Zusammenziehungen,
   gegen die Parität, auf allen Matroiden mit höchstens 5 Elementen.
5. Literatur: Matroide 2, 5, 16, 68, 406; Spannbäume von K5 = 5^3 = 125 (Cayley), K3,3 = 81; Fano hat 28 Basen und 7 Kokreise."""

import itertools
import random

import numpy as np
import pytest

import dmo_algorithm as A
import dmo_systems as S
from dmo_algorithm import System
from dmo_scenario import make_instance

nx = pytest.importorskip("networkx")


def _random_matroid(rng, n):
    """Zufallsmatroid: graphisch, uniform, Partition oder Vektoren über GF(2) auf n Elementen."""
    kind = rng.choice(["uniform", "gf2", "partition"])
    if kind == "uniform":
        return A.uniform(rng.randint(0, n), n)
    if kind == "gf2":
        vec = [rng.getrandbits(3) for _ in range(n)]
        return System("gf2", n, [A.gf2_independent([vec[e] for e in range(n) if mask >> e & 1]) for mask in range(1 << n)])
    cls = [rng.randint(0, 2) for _ in range(n)]
    return System("partition", n, [len({cls[e] for e in range(n) if mask >> e & 1}) == bin(mask).count("1") for mask in range(1 << n)])


def _maximal_independent(s):
    return [i for i in range(1 << s.m) if s.ok[i] and not any(s.ok[i | 1 << e] for e in range(s.m) if not i >> e & 1)]


def test_cocircuits_equal_the_minimal_sets_that_meet_every_basis():
    rng = random.Random(1)
    for _ in range(25):
        s = _random_matroid(rng, rng.randint(2, 6))
        bases = _maximal_independent(s)
        meets = [f for f in range(1, 1 << s.m) if all(b & f for b in bases)]
        minimal = [f for f in meets if not any(g != f and g & ~f == 0 for g in meets)]
        assert sorted(A.cocircuits(A.dual(s))) == sorted(minimal), (s.name, s.m)


def test_dual_independence_is_the_complement_containing_a_basis():
    rng = random.Random(2)
    for _ in range(25):
        s = _random_matroid(rng, rng.randint(2, 6))
        d = A.dual(s)
        r = s.rank
        for mask in range(1 << s.m):
            rest = s.full ^ mask
            spans = max(bin(i).count("1") for i in range(1 << s.m) if s.ok[i] and i & ~rest == 0) == r         # E ∖ I enthält eine Basis
            assert d.ok[mask] == spans


def test_wald_cocircuits_equal_the_bonds_computed_with_networkx():
    for n, seed in ((6, 0), (6, 1), (7, 8), (7, 3)):
        inst = make_instance(n, seed)
        s = S.get_system("wald", n, seed)
        found = set()
        for sub in range(0, 1 << (n - 1)):
            side = {0} | {v + 1 for v in range(n - 1) if sub >> v & 1}
            other = set(range(n)) - side
            if not other:
                continue
            ok = True
            for part in (side, other):
                g = nx.Graph()
                g.add_nodes_from(part)
                g.add_edges_from((u, w) for u, w, _ in inst.edges if u in part and w in part)
                ok &= nx.is_connected(g)
            if ok:
                found.add(sum(1 << e for e, (u, w, _) in enumerate(inst.edges) if (u in side) != (w in side)))
        assert set(A.cocircuits(A.dual(s))) == found == {c for c, _ in A.bonds(inst)}, (n, seed)


def test_wald_minors_equal_the_graph_operations_of_networkx():
    inst = make_instance(6, 3)
    s = S.get_system("wald", 6, 3)

    def forest(edges, mask):
        g = nx.MultiGraph()
        g.add_nodes_from(range(inst.n))
        g.add_edges_from(edges[e] for e in range(len(edges)) if mask >> e & 1)
        return nx.is_forest(g)

    edges = [(u, w) for u, w, _ in inst.edges]
    for e in range(len(edges)):
        rest = [x for i, x in enumerate(edges) if i != e]
        u, w = edges[e]
        merged = [(u if a == w else a, u if b == w else b) for a, b in rest]
        assert A.delete(s, e).ok == [forest(rest, mask) for mask in range(1 << len(rest))]
        assert A.contract(s, e).ok == [forest(merged, mask) for mask in range(1 << len(rest))]


def _faces_of_networkx(inst):
    g = nx.Graph([(u, w) for u, w, _ in inst.edges])
    ok, emb = nx.check_planarity(g)
    assert ok
    seen, faces = set(), []
    for u, w in emb.edges():
        if (u, w) in seen:
            continue
        nodes = emb.traverse_face(u, w, mark_half_edges=seen)
        faces.append(nodes)
    return emb, faces


def _kirchhoff(n, edges):
    lap = np.zeros((n, n))
    for a, b in edges:
        if a != b:
            lap[a, a] += 1
            lap[b, b] += 1
            lap[a, b] -= 1
            lap[b, a] -= 1
    return round(np.linalg.det(lap[1:, 1:]))


def test_dual_graph_faces_equal_the_networkx_embedding_and_spanning_tree_counts_agree():
    plans = [(n, seed) for n in (6, 7) for seed in range(12) if nx.check_planarity(nx.Graph([(u, w) for u, w, _ in make_instance(n, seed).edges]))[0]][:8] + [(7, 8)]
    assert len(plans) == 9
    for n, seed in plans:
        inst = make_instance(n, seed)
        pos = A.planar_pos(inst)
        assert pos is not None
        d = A.dual_drawing(inst, pos)
        _, faces = _faces_of_networkx(inst)
        mine = {frozenset(frozenset(h) for h in w) for w in d["walks"]}
        theirs = {frozenset(frozenset(h) for h in zip(f, f[1:] + f[:1])) for f in faces}
        assert len(faces) == d["faces"] == inst.m - inst.n + 2 and mine == theirs
        assert _kirchhoff(inst.n, [(u, w) for u, w, _ in inst.edges]) == _kirchhoff(d["faces"], d["dual_edges"]) == A.dual_tree_check(inst, d)["n_trees"]


def test_non_planar_plans_have_no_planar_drawing_according_to_networkx():
    count = 0
    for seed in range(200):
        inst = make_instance(7, seed)
        planar = nx.check_planarity(nx.Graph([(u, w) for u, w, _ in inst.edges]))[0]
        assert (A.planar_pos(inst) is not None) == planar
        count += not planar
    assert count == 21


def _brute_binary(s):
    """Binär, wenn es zu einer festen Basis eine Matrix A über GF(2) gibt, die dieselben unabhängigen Mengen liefert (alle Matrizen durchprobiert)."""
    base = _maximal_independent(s)[0]
    bl = [e for e in range(s.m) if base >> e & 1]
    other = [e for e in range(s.m) if not base >> e & 1]
    r = len(bl)
    for a in range(1 << (r * len(other))):
        vec = [0] * s.m
        for i, e in enumerate(bl):
            vec[e] = 1 << i
        for j, e in enumerate(other):
            vec[e] = (a >> (j * r)) & ((1 << r) - 1)
        if all(A.gf2_independent([vec[e] for e in range(s.m) if mask >> e & 1]) == s.ok[mask] for mask in range(1 << s.m)):
            return True
    return False


def _has_u24_by_recursion(s, memo):
    key = (s.m, tuple(s.ok))
    if key not in memo:
        if s.m < 4:
            memo[key] = False
        elif s.m == 4:
            memo[key] = tuple(s.ok) == tuple(bin(mask).count("1") <= 2 for mask in range(16))
        else:
            memo[key] = any(_has_u24_by_recursion(f(s, e), memo) for e in range(s.m) for f in (A.delete, A.contract))
    return memo[key]


def test_binary_by_three_independent_routes_on_all_matroids_up_to_five_elements():
    memo = {}
    nonbinary = []
    for n in range(1, 6):
        count = 0
        for ok in A.all_systems(n):
            s = System("x", n, list(ok))
            if not s.is_matroid:
                continue
            brute, rec = _brute_binary(s), not _has_u24_by_recursion(s, memo)
            assert brute == rec == A.even_intersections(s, A.dual(s)) == A.represents_over_gf2(s) == (A.u24_minor(s) is None), (n, ok)
            count += not brute
        nonbinary.append(count)
    assert nonbinary == [0, 0, 0, 1, 32]


def test_matroid_counts_and_spanning_tree_literature_values():
    counts = [sum(1 for ok in A.all_systems(n) if System("x", n, list(ok)).is_matroid) for n in range(1, 6)]
    assert counts == [2, 5, 16, 68, 406]                                                         # OEIS A058673
    k5 = A.graph_system(5, list(itertools.combinations(range(5), 2)))
    k33 = A.graph_system(6, [(a, b) for a in range(3) for b in range(3, 6)])
    assert len(k5.bases) == 5 ** 3 == 125 and len(k33.bases) == 81                              # Cayley; 3^2 * 3^2
    assert len(A.dual(k5).bases) == 125 and A.dual(k5).rank == 6 and A.dual(k33).rank == 4


def test_fano_literature_numbers(fano):
    d = A.dual(fano)
    assert (len(fano.bases), len(fano.circuits), len(d.circuits), fano.rank, d.rank) == (28, 14, 7, 3, 4)
