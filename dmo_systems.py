"""Die Unabhängigkeitssysteme der Demo, gebaut aus einem Leitungsnetz (Plan) mit farbigen Kabeln, dazu die Fano-Ebene."""

import random
from fractions import Fraction
from functools import lru_cache

import dmo_constants as C
from dmo_algorithm import System, popcount
from dmo_scenario import Instance, make_instance


def edge_colors(inst: Instance, seed: int) -> list[str]:
    """Kabelfarbe je Leitung, deterministisch aus dem Seed."""
    rng = random.Random(seed * 31 + 7)
    return [C.CABLE_COLORS[rng.randrange(len(C.CABLE_COLORS))] for _ in range(inst.m)]


def _components(inst: Instance, mask: int):
    """Komponentenetikett je Standort für die Leitungen in mask."""
    label = list(range(inst.n))
    for e in range(inst.m):
        if mask >> e & 1:
            u, v, _ = inst.edges[e]
            old, new = label[v], label[u]
            label = [new if x == old else x for x in label]
    return label


def _forest_ok(inst: Instance, maxdeg: int = 0, colors=None) -> list[bool]:
    """Wald: kein Kreis; mit maxdeg höchstens so viele Leitungen je Standort; mit colors höchstens eine Leitung je Farbe."""
    n, m = inst.n, inst.m
    ok = [False] * (1 << m)
    for mask in range(1 << m):
        label = list(range(n))
        deg = [0] * n
        seen = set()
        good = True
        for e in range(m):
            if mask >> e & 1:
                u, v, _ = inst.edges[e]
                deg[u] += 1
                deg[v] += 1
                if (maxdeg and (deg[u] > maxdeg or deg[v] > maxdeg)) or label[u] == label[v] or (colors and colors[e] in seen):
                    good = False
                    break
                if colors:
                    seen.add(colors[e])
                old, new = label[v], label[u]
                label = [new if x == old else x for x in label]
        ok[mask] = good
    return ok


def _anschluss_ok(inst: Instance) -> list[bool]:
    """Jede Leitung bekommt einen ihrer beiden Standorte als Anschluss, kein Standort doppelt: jede Komponente hat höchstens so viele Leitungen wie Standorte."""
    m = inst.m
    ok = []
    for mask in range(1 << m):
        label = _components(inst, mask)
        good = True
        for comp in set(label[inst.edges[e][0]] for e in range(m) if mask >> e & 1):
            edges_in = sum(1 for e in range(m) if mask >> e & 1 and label[inst.edges[e][0]] == comp)
            nodes_in = len({v for e in range(m) if mask >> e & 1 and label[inst.edges[e][0]] == comp for v in inst.edges[e][:2]})
            if edges_in > nodes_in:
                good = False
                break
        ok.append(good)
    return ok


def rank_over_q(vectors) -> int:
    """Rang einer Liste ganzzahliger Vektoren über den rationalen Zahlen (Gauß in exakten Brüchen)."""
    rows = [[Fraction(x) for x in v] for v in vectors]
    rank = 0
    cols = len(rows[0]) if rows else 0
    for c in range(cols):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][c] != 0), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for r in range(len(rows)):
            if r != rank and rows[r][c] != 0:
                f = rows[r][c] / rows[rank][c]
                rows[r] = [x - f * y for x, y in zip(rows[r], rows[rank])]
        rank += 1
    return rank


def standort_vectors(inst: Instance) -> list[tuple[int, int, int]]:
    """Standort v als Vektor (x, y, 1) auf einem Raster von 0 bis GRID: Mengen sind unabhängig, wenn die Punkte nicht auf einer Geraden liegen (höchstens drei)."""
    return [(int(p[0] * C.GRID + 0.5), int(p[1] * C.GRID + 0.5), 1) for p in inst.points]


def gf2_rank(vectors) -> int:
    basis: list[int] = []
    for v in vectors:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


FANO_VECTORS = (1, 2, 3, 4, 5, 6, 7)   # alle von 0 verschiedenen Vektoren des GF(2)^3 als Bitmuster


def fano_system() -> System:
    ok = [gf2_rank([FANO_VECTORS[e] for e in range(7) if mask >> e & 1]) == popcount(mask) for mask in range(1 << 7)]
    return System("Fano-Ebene", 7, ok)


def build_system(key: str, inst: Instance, seed: int = 0) -> System:
    """System `key` (aus C.SYSTEMS) auf dem Plan. Grundmenge: die Leitungen; bei "standorte" und "vektoren" die Standorte; bei "fano" die 7 Punkte."""
    if key not in C.SYSTEMS:
        raise ValueError(f"unbekanntes System: {key}")
    name = C.SYSTEM_NAMES[key]
    m, n = inst.m, inst.n
    if key == "fano":
        return fano_system()
    if key == "wald":
        return System(name, m, _forest_ok(inst))
    if key == "wald2":
        return System(name, m, _forest_ok(inst, 2))
    if key == "paarung":
        return System(name, m, _forest_ok(inst, 1))
    if key == "wald_farben":
        return System(name, m, _forest_ok(inst, colors=edge_colors(inst, seed)))
    if key == "farben":
        colors = edge_colors(inst, seed)
        return System(name, m, [len({colors[e] for e in range(m) if mask >> e & 1}) == popcount(mask) for mask in range(1 << m)])
    if key == "anschluss":
        return System(name, m, _anschluss_ok(inst))
    if key == "uniform":
        return System(name, m, [popcount(mask) <= C.UNIFORM_K for mask in range(1 << m)])
    if key == "vektoren":
        vecs = standort_vectors(inst)
        return System(name, n, [rank_over_q([vecs[v] for v in range(n) if mask >> v & 1]) == popcount(mask) if mask else True for mask in range(1 << n)])
    if key == "budget":
        cap = budget_cap(inst)
        return System(name, m, [sum(inst.edges[e][2] for e in range(m) if mask >> e & 1) <= cap for mask in range(1 << m)])
    return System(name, n, [all(not (mask >> u & 1 and mask >> v & 1) for u, v, _ in inst.edges) for mask in range(1 << n)])


@lru_cache(maxsize=32)
def get_system(key: str, n: int, seed: int) -> System:
    """Gleiches System für gleiche (key, n, seed): der Aufbau kostet bei 16 Leitungen etwa eine Sekunde."""
    return build_system(key, make_instance(n, seed), seed)


def budget_cap(inst: Instance) -> int:
    return int(C.BUDGET_SHARE * sum(c for _, _, c in inst.edges))


def ground_kind(key: str) -> str:
    """"kanten" (Elemente sind Leitungen), "knoten" (Standorte) oder "punkte" (die sieben Fano-Punkte, ohne Plan)."""
    return {"standorte": "knoten", "vektoren": "knoten", "fano": "punkte"}.get(key, "kanten")


def labels(key: str, inst: Instance) -> list[str]:
    kind = ground_kind(key)
    if kind == "knoten":
        return [inst.name(v) for v in range(inst.n)]
    if kind == "punkte":
        return [f"P{e + 1}" for e in range(7)]
    return [inst.label(e) for e in range(inst.m)]
