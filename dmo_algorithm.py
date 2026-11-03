"""Kern der Demo: Unabhängigkeitssysteme auf höchstens 16 Elementen (Bitmasken), das duale Matroid, Minoren, binär und der Dualgraph.

Ein Unabhängigkeitssystem ist eine nach unten abgeschlossene Familie von Teilmengen einer Grundmenge. Elemente sind Zahlen 0 .. m − 1, eine Menge ist die Bitmaske.
Rang r(F) = Größe der größten zulässigen Teilmenge von F. Basen = maximale zulässige Mengen. Kreise = minimale unzulässige Mengen. Kokreise = Kreise des Duals.
Dual M*: Basen sind die Komplemente der Basen von M; r*(F) = |F| − r(E) + r(E ∖ F). Löschen M ∖ e und Zusammenziehen M / e vertauschen sich unter dem Dual.
Binär: über GF(2) darstellbar; gleichwertig: jeder Kreis trifft jeden Kokreis in einer geraden Zahl von Elementen, und kein U(2,4)-Minor.
Dualgraph eines planaren Plans: je Fläche ein Knoten, je Leitung eine Dualleitung zwischen den beiden angrenzenden Flächen."""

import itertools
import math
from functools import cached_property

import networkx as nx
import numpy as np


def popcount(x: int) -> int:
    return bin(x).count("1")


def elements(mask: int, m: int) -> list[int]:
    return [e for e in range(m) if mask >> e & 1]


class System:
    """Unabhängigkeitssystem auf m Elementen; ok[mask] sagt, ob die Menge `mask` zulässig ist."""

    def __init__(self, name: str, m: int, ok):
        if not 1 <= m <= 16:
            raise ValueError(f"m = {m} außerhalb von 1 bis 16")
        if len(ok) != 1 << m or not ok[0]:
            raise ValueError("ok braucht 2**m Einträge, und die leere Menge muss zulässig sein")
        self.name, self.m, self.ok = name, m, list(ok)
        self.full = (1 << m) - 1
        self.ind = [mask for mask in range(1 << m) if self.ok[mask]]
        self.ind_array = np.array(self.ind, dtype=np.int64)
        self.sizes = np.array([popcount(i) for i in self.ind], dtype=np.int64)
        self._ranks()

    # --- Grundbegriffe ------------------------------------------------------------------------------------------------------------------

    def check_down_closed(self) -> bool:
        """Mit jeder zulässigen Menge sind alle Mengen ohne ein Element zulässig (genügt für alle Teilmengen)."""
        return all(self.ok[mask & ~(1 << e)] for mask in self.ind for e in range(self.m) if mask >> e & 1)

    def can_add(self, mask: int, e: int) -> bool:
        return not mask >> e & 1 and self.ok[mask | 1 << e]

    def addable(self, mask: int) -> int:
        """Maske aller Elemente, die zu `mask` passen."""
        out = 0
        for e in range(self.m):
            if self.can_add(mask, e):
                out |= 1 << e
        return out

    def is_maximal(self, mask: int) -> bool:
        return self.ok[mask] and self.addable(mask) == 0

    def _ranks(self):
        m, ok = self.m, self.ok
        ur = [0] * (1 << m)
        for mask in range(1, 1 << m):
            ur[mask] = popcount(mask) if ok[mask] else max(ur[mask & ~(1 << e)] for e in range(m) if mask >> e & 1)
        self.ur = ur
        lr = [0] * (1 << m)
        for i in sorted(self.ind, key=popcount):
            free = self.full & ~i & ~self.addable(i)
            s = free
            while True:
                f = i | s
                if f and lr[f] == 0:
                    lr[f] = popcount(i)
                if s == 0:
                    break
                s = (s - 1) & free
        self.lr = lr
        best = None
        for f in range(1, 1 << m):
            if ur[f] > 0:
                q = lr[f] / ur[f]
                if best is None or q < best[0] - 1e-15:
                    best = (q, f)
        self.q = best[0] if best else 1.0

    # --- Rang, Basen, Kreise, Abschluss, Flache -------------------------------------------------------------------------------------------

    @property
    def rank(self) -> int:
        """Rang der ganzen Grundmenge: Größe der größten zulässigen Menge."""
        return self.ur[self.full]

    def rank_of(self, f: int) -> int:
        return self.ur[f]

    @cached_property
    def bases(self) -> list[int]:
        """Maximale zulässige Mengen (bei einem Matroid alle gleich groß)."""
        return [i for i in self.ind if self.is_maximal(i)]

    @cached_property
    def circuits(self) -> list[int]:
        """Minimale unzulässige Mengen."""
        out = []
        for c in range(1, 1 << self.m):
            if not self.ok[c] and all(self.ok[c & ~(1 << e)] for e in range(self.m) if c >> e & 1):
                out.append(c)
        return out

    def closure(self, f: int) -> int:
        """cl(F) = F plus alle e, deren Hinzunahme den Rang nicht erhöht."""
        r = self.ur[f]
        out = f
        for e in range(self.m):
            if not f >> e & 1 and self.ur[f | 1 << e] == r:
                out |= 1 << e
        return out

    @cached_property
    def closures(self) -> list[int]:
        return [self.closure(f) for f in range(1 << self.m)]

    @cached_property
    def flats(self) -> list[int]:
        return [f for f in range(1 << self.m) if self.closures[f] == f]

    def flats_by_rank(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for f in self.flats:
            out[self.ur[f]] = out.get(self.ur[f], 0) + 1
        return dict(sorted(out.items()))

    def circuits_in(self, mask: int) -> list[int]:
        """Alle Kreise, die in `mask` enthalten sind."""
        return [c for c in self.circuits if c & ~mask == 0]

    def fundamental_circuit(self, base: int, e: int):
        """Der Kreis in B + e, wenn es genau einen gibt (bei einem Matroid immer), sonst None."""
        inside = self.circuits_in(base | 1 << e)
        return inside[0] if len(inside) == 1 else None

    def swap_is_basis(self, base: int, f: int, e: int) -> bool:
        """Ist B − f + e wieder eine Basis (maximale zulässige Menge)?"""
        new = (base & ~(1 << f)) | 1 << e
        return self.is_maximal(new)

    def maximal_sizes(self) -> dict[int, int]:
        sizes: dict[int, int] = {}
        for i in self.bases:
            sizes[popcount(i)] = sizes.get(popcount(i), 0) + 1
        return dict(sorted(sizes.items()))

    # --- Austauschprobe (Stück 3) -------------------------------------------------------------------------------------------------------

    def exchange_scan(self, weak: bool = False) -> tuple[int, int]:
        """(Zahl der Paare (I1, I2) mit |I1| < |I2|, Zahl der Paare ohne Austauschpartner); je I1 ein Maskenvergleich über alle I2."""
        pairs = viol = 0
        for i1, s1 in zip(self.ind, self.sizes):
            bigger = self.sizes == s1 + 1 if weak else self.sizes > s1
            count = int(bigger.sum())
            if not count:
                continue
            pairs += count
            viol += int(((self.ind_array[bigger] & ~i1 & self.addable(i1)) == 0).sum())
        return pairs, viol

    @cached_property
    def is_matroid(self) -> bool:
        return self.exchange_scan()[1] == 0


# --- Dual -----------------------------------------------------------------------------------------------------------------------------------


def independent_from_bases(m: int, bases) -> list[bool]:
    """Zulässig ist, was in einer Basis liegt: nach unten abgeschlossene Hülle der Basen."""
    ok = [False] * (1 << m)
    for b in bases:
        ok[b] = True
    for mask in sorted(range(1 << m), key=lambda x: -popcount(x)):
        if ok[mask]:
            for e in range(m):
                if mask >> e & 1:
                    ok[mask & ~(1 << e)] = True
    return ok


def sorted_sets(masks) -> list[int]:
    return sorted(masks, key=lambda x: (popcount(x), x))


def dual(s: System) -> System:
    """System der Komplemente der maximalen Mengen; bei einem Matroid ist das das duale Matroid M*, bei einem Nicht-Matroid kein Matroid."""
    return System("dual", s.m, independent_from_bases(s.m, [s.full ^ b for b in s.bases]))


def dual_rank_formula_holds(s: System, d: System) -> bool:
    """r*(F) = |F| − r(E) + r(E ∖ F) für alle Teilmengen F."""
    return all(d.ur[f] == popcount(f) - s.rank + s.ur[s.full ^ f] for f in range(1 << s.m))


def cocircuits(d: System) -> list[int]:
    """Kokreise von M = Kreise von M*, nach Größe und Maske geordnet (d ist das Dual)."""
    return sorted_sets(d.circuits)


# --- Minoren ----------------------------------------------------------------------------------------------------------------------------------


def _lift(mask: int, e: int) -> int:
    """Maske auf m − 1 Elementen -> Maske auf m Elementen mit Lücke bei e."""
    return (mask & ((1 << e) - 1)) | ((mask >> e) << (e + 1))


def delete(s: System, e: int) -> System:
    """M ∖ e: die Mengen ohne e, die in M zulässig sind (Elemente über e rücken um eins nach unten)."""
    return System("löschen", s.m - 1, [s.ok[_lift(mask, e)] for mask in range(1 << (s.m - 1))])


def contract(s: System, e: int) -> System:
    """M / e: Mengen I ohne e, für die I + e in M zulässig ist (bei einer Schleife e dasselbe wie Löschen)."""
    loop = not s.ok[1 << e]
    return System("ziehen", s.m - 1, [s.ok[_lift(mask, e)] if loop else s.ok[_lift(mask, e) | 1 << e] for mask in range(1 << (s.m - 1))])


def minor(s: System, e: int, op: str) -> System:
    return delete(s, e) if op == "loeschen" else contract(s, e)


def minor_identities(s: System, d: System, e: int) -> dict:
    """(M ∖ e)* = M*/e und (M / e)* = M* ∖ e als gleiche zulässige Mengen; dazu: sind die Minoren Matroide?"""
    md, mc = delete(s, e), contract(s, e)
    return {
        "delete_dual": dual(md).ok == contract(d, e).ok, "contract_dual": dual(mc).ok == delete(d, e).ok,
        "delete_matroid": md.is_matroid, "contract_matroid": mc.is_matroid,
    }


# --- Kreis und Kokreis -------------------------------------------------------------------------------------------------------------------


_PC = None


def _pc():
    """Tabelle der Elementzahl aller Masken bis 2^16."""
    global _PC
    if _PC is None:
        _PC = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.int16)
    return _PC


def _meets(circuits, cocircuits):
    """Matrix der Durchschnittsgrößen |C ∩ K| (Kreise mal Kokreise)."""
    c = np.array(circuits, dtype=np.int64)[:, None]
    k = np.array(cocircuits, dtype=np.int64)[None, :]
    return _pc()[c & k]


def intersection_sizes(s: System, cocircuit: int) -> dict[int, int]:
    """Wie oft trifft ein Kreis den Kokreis in 0, 1, 2, … Elementen?"""
    if not s.circuits:
        return {}
    counts = np.bincount(_pc()[np.array(s.circuits, dtype=np.int64) & cocircuit])
    return {k: int(c) for k, c in enumerate(counts) if c}


def orthogonal(s: System, d: System) -> bool:
    """Kein Kreis trifft einen Kokreis in genau einem Element (gilt für jedes Matroid)."""
    if not s.circuits or not d.circuits:
        return True
    return bool((_meets(s.circuits, d.circuits) != 1).all())


def even_intersections(s: System, d: System) -> bool:
    """Jeder Kreis trifft jeden Kokreis in einer geraden Zahl von Elementen (Eigenschaft der binären Matroide)."""
    if not s.circuits or not d.circuits:
        return True
    return bool((_meets(s.circuits, d.circuits) % 2 == 0).all())


def odd_pair(s: System, d: System):
    """Ein Kreis und ein Kokreis mit ungerader Durchschnittsgröße (das kleinste Paar nach Größe), oder None."""
    if not s.circuits or not d.circuits:
        return None
    circuits, cos = sorted_sets(s.circuits), sorted_sets(d.circuits)
    odd = _meets(circuits, cos) % 2 == 1
    idx = np.argwhere(odd)
    if not len(idx):
        return None
    i, j = idx[0]
    return circuits[i], cos[j]


# --- Binär -----------------------------------------------------------------------------------------------------------------------------------


def gf2_independent(vectors) -> bool:
    basis: list[int] = []
    for v in vectors:
        for b in basis:
            v = min(v, v ^ b)
        if not v:
            return False
        basis.append(v)
    return True


def gf2_vectors(s: System) -> list[int]:
    """Der einzige Kandidat für eine Darstellung über GF(2) zur Basis B = erste Basis: Elemente von B als Einheitsvektoren, e außerhalb als Summe der Einheitsvektoren
    der Elemente im Fundamentalkreis C(B, e) − e (Schleifen als Nullvektor). Nur bei einem Matroid."""
    base = s.bases[0]
    bl = elements(base, s.m)
    vec = [0] * s.m
    for i, b in enumerate(bl):
        vec[b] = 1 << i
    for e in range(s.m):
        if not base >> e & 1:
            c = s.fundamental_circuit(base, e)
            vec[e] = sum(1 << i for i, b in enumerate(bl) if c >> b & 1)
    return vec


def represents_over_gf2(s: System) -> bool:
    """Stimmt der Kandidat gf2_vectors auf allen Teilmengen mit der Unabhängigkeit überein? (Eine Darstellung ist durch die Basis bis auf Zeilenumformungen eindeutig.)"""
    vec = gf2_vectors(s)
    return all(gf2_independent([vec[e] for e in elements(mask, s.m)]) == s.ok[mask] for mask in range(1 << s.m))


def u24_minor(s: System):
    """(X, C) mit einer 4-elementigen Menge X und einer unabhängigen Menge C außerhalb, für die M / C auf X das uniforme Matroid U(2,4) ist (Rang von Y gleich min(|Y|, 2)
    für alle Teilmengen Y von X); dann ist M | (C ∪ X) / C = U(2,4) ein Minor. None, wenn es keinen gibt."""
    if s.m < 4:
        return None
    ur = s.ur
    for x_elems in itertools.combinations(range(s.m), 4):
        x = sum(1 << e for e in x_elems)
        subsets = [sum(1 << x_elems[i] for i in range(4) if k >> i & 1) for k in range(1, 16)]
        rest = s.full ^ x
        c = rest
        while True:
            if s.ok[c]:
                rc = popcount(c)
                if all(ur[c | y] - rc == min(popcount(y), 2) for y in subsets):
                    return x, c
            if c == 0:
                break
            c = (c - 1) & rest
    return None


def binary_ways(s: System, d: System, with_minor: bool = True) -> dict:
    """Die drei Wege am Matroid s (mit Dual d): Parität, Darstellung über GF(2), kein U(2,4)-Minor (None, wenn nicht gerechnet)."""
    parity = even_intersections(s, d)
    rep = represents_over_gf2(s)
    minor_free = None if not with_minor else u24_minor(s) is None
    return {"parity": parity, "rep": rep, "no_u24": minor_free}


# --- Graphen: graphisches Matroid und die Suche nach einem Graphen ---------------------------------------------------------------------


def graph_system(v: int, edges) -> System:
    """Graphisches Matroid der Kantenliste edges auf v Knoten (Schleifen sind nie zulässig)."""
    m = len(edges)
    ok = []
    for mask in range(1 << m):
        parent = list(range(v))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        good = True
        for e in range(m):
            if mask >> e & 1:
                a, b = find(edges[e][0]), find(edges[e][1])
                if a == b:
                    good = False
                    break
                parent[a] = b
        ok.append(good)
    return System("graph", m, ok)


def isomorphic(s1: System, s2: System) -> bool:
    """Gibt es eine Umnummerierung der Elemente mit gleichen Basen? Alle Permutationen, mit numpy; nur für m ≤ 9."""
    if s1.m != s2.m or len(s1.bases) != len(s2.bases) or s1.rank != s2.rank:
        return False
    if sorted(popcount(c) for c in s1.circuits) != sorted(popcount(c) for c in s2.circuits):
        return False
    m = s1.m
    perms = np.array(list(itertools.permutations(range(m))), dtype=np.int64)
    target = np.zeros(1 << m, dtype=bool)
    for b in s2.bases:
        target[b] = True
    good = np.ones(len(perms), dtype=bool)
    for b in s1.bases:
        new = np.zeros(len(perms), dtype=np.int64)
        for e in elements(b, m):
            new |= 1 << perms[:, e]
        good &= target[new]
        if not good.any():
            return False
    return bool(good.any())


def graphic_search(target: System, label: str, chunk: int = 40000) -> dict:
    """Gibt es einen einfachen Graphen auf rank + 1 Knoten mit m Kanten und demselben Matroid wie `target`? (Annahme: das Ziel ist zusammenhängend, ein graphisches Matroid
    kommt dann von einem 2-zusammenhängenden einfachen Graphen auf rank + 1 Knoten.) Filter: Zahl der Spannbäume (Kirchhoff) gleich der Zahl der Basen; danach Isomorphie."""
    v, m = target.rank + 1, target.m
    pairs = list(itertools.combinations(range(v), 2))
    out = {"label": label, "m": m, "rank": target.rank, "bases": len(target.bases), "pairs": len(pairs), "candidates": 0, "same_trees": 0, "graphic": False, "reason": "", "edges": None}
    if len(pairs) < m:
        out["reason"] = f"{m} Kanten, aber nur {len(pairs)} Knotenpaare auf {v} Knoten"
        return out
    pa = np.array([a for a, _ in pairs])
    pb = np.array([b for _, b in pairs])
    matches = []
    combos_iter = itertools.combinations(range(len(pairs)), m)
    while True:
        block = list(itertools.islice(combos_iter, chunk))
        if not block:
            break
        combos = np.array(block, dtype=np.int32)
        n = len(combos)
        lap = np.zeros((n, v, v))
        ar = np.arange(n)
        for j in range(m):
            idx = combos[:, j]
            a, b = pa[idx], pb[idx]
            lap[ar, a, a] += 1
            lap[ar, b, b] += 1
            lap[ar, a, b] -= 1
            lap[ar, b, a] -= 1
        trees = np.rint(np.linalg.det(lap[:, 1:, 1:])).astype(np.int64)
        out["candidates"] += int((trees > 0).sum())
        for i in np.nonzero(trees == len(target.bases))[0]:
            matches.append([pairs[k] for k in combos[i]])
    out["same_trees"] = len(matches)
    for edges in matches:
        if m > 9:
            out["reason"] = "Isomorphie nicht geprüft (mehr als 9 Elemente)"
            break
        if isomorphic(graph_system(v, edges), target):
            out.update(graphic=True, edges=edges)
            break
    return out


def uniform(k: int, n: int) -> System:
    return System(f"U({k},{n})", n, [popcount(mask) <= k for mask in range(1 << n)])


# --- Pläne: Schnitte und Dualgraph ---------------------------------------------------------------------------------------------------------


def bonds(inst) -> list[tuple[int, int]]:
    """Minimale Schnitte des Plans: (Kantenmaske, Knotenmenge der Seite mit dem Depot); beide Seiten zusammenhängend."""
    n = inst.n
    out = []
    for sub in range(0, 1 << (n - 1)):
        side = 1 | (sub << 1)
        other = ((1 << n) - 1) ^ side
        if not other:
            continue
        good = True
        for part in (side, other):
            nodes = elements(part, n)
            parent = {v: v for v in nodes}

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            for u, w, _ in inst.edges:
                if part >> u & 1 and part >> w & 1:
                    parent[find(u)] = find(w)
            if len({find(v) for v in nodes}) != 1:
                good = False
                break
        if good:
            out.append((sum(1 << e for e, (u, w, _) in enumerate(inst.edges) if (side >> u & 1) != (side >> w & 1)), side))
    return out


def crossing_free(inst) -> bool:
    """Ist die geradlinige Zeichnung des Plans mit den Standorten kreuzungsfrei?"""
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    for (a, b, _), (c, d, _) in itertools.combinations(inst.edges, 2):
        if len({a, b, c, d}) == 4:
            p1, p2, p3, p4 = inst.points[a], inst.points[b], inst.points[c], inst.points[d]
            if orient(p1, p2, p3) * orient(p1, p2, p4) < 0 and orient(p3, p4, p1) * orient(p3, p4, p2) < 0:
                return False
    return True


def planar_pos(inst):
    """Kreuzungsfreie geradlinige Zeichnung des Plans (nur Graph, nicht die Standorte): {Knoten: (x, y)} oder None, wenn der Plan nicht planar ist."""
    g = nx.Graph([(u, w) for u, w, _ in inst.edges])
    g.add_nodes_from(range(inst.n))
    ok, emb = nx.check_planarity(g)
    if not ok:
        return None
    pos = nx.combinatorial_embedding_to_pos(emb)
    return {v: (float(x), float(y)) for v, (x, y) in pos.items()}


def _faces(inst, pos):
    """Flächen der kreuzungsfreien Zeichnung über das Rotationssystem: (Fläche je Halbkante, Zahl der Flächen, Halbkantenfolge je Fläche)."""
    rot: dict[int, list] = {v: [] for v in range(inst.n)}
    for u, w, _ in inst.edges:
        for a, b in ((u, w), (w, u)):
            rot[a].append((math.atan2(pos[b][1] - pos[a][1], pos[b][0] - pos[a][0]), b))
    for v in rot:
        rot[v] = [b for _, b in sorted(rot[v])]
    face_of: dict[tuple[int, int], int] = {}
    walks: list[list[tuple[int, int]]] = []
    for u, w, _ in inst.edges:
        for a, b in ((u, w), (w, u)):
            if (a, b) in face_of:
                continue
            walk = []
            x, y = a, b
            while (x, y) not in face_of:
                face_of[(x, y)] = len(walks)
                walk.append((x, y))
                lst = rot[y]
                x, y = y, lst[(lst.index(x) - 1) % len(lst)]
            walks.append(walk)
    return face_of, len(walks), walks


def _area(walk, pos) -> float:
    return 0.5 * sum(pos[a][0] * pos[b][1] - pos[b][0] * pos[a][1] for a, b in walk)


def _inner_sign() -> float:
    """Vorzeichen der Fläche eines inneren Dreiecks bei dieser Umlaufrichtung (an einem Quadrat mit Diagonale geeicht)."""
    from dmo_scenario import Instance
    pts = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    inst = Instance(pts, ((0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0), (1, 2, 1.0), (2, 3, 1.0)))
    _, _, walks = _faces(inst, dict(enumerate(pts)))
    areas = sorted(_area(w, dict(enumerate(pts))) for w in walks)
    return 1.0 if areas[-1] > 0 and abs(areas[-1] - 0.5) < 1e-9 else -1.0


def dual_drawing(inst, pos) -> dict:
    """Dualgraph zur kreuzungsfreien Zeichnung pos: Flächen, Flächenknoten (Mittelpunkt, die Außenfläche links oben außerhalb), Dualleitung je Leitung."""
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    sx, sy = 0.9 / max(max(xs) - min(xs), 1e-9), 0.9 / max(max(ys) - min(ys), 1e-9)   # getrennte Streckung je Achse: erhält Geraden, Kreuzungsfreiheit und Umlaufrichtung
    norm = {v: (0.05 + (p[0] - min(xs)) * sx, 0.05 + (p[1] - min(ys)) * sy) for v, p in pos.items()}
    pos = norm
    face_of, nf, walks = _faces(inst, pos)
    sign = _inner_sign()
    areas = [_area(w, pos) * sign for w in walks]
    outer = min(range(nf), key=lambda f: areas[f])
    dual_pos = []
    for f, walk in enumerate(walks):
        vs = [a for a, _ in walk]
        dual_pos.append((sum(norm[v][0] for v in vs) / len(vs), sum(norm[v][1] for v in vs) / len(vs)))
    dual_pos[outer] = (min(p[0] for p in norm.values()) - 0.1, max(p[1] for p in norm.values()) + 0.1)
    dual_edges = [(face_of[(u, w)], face_of[(w, u)]) for u, w, _ in inst.edges]
    return {"pos": norm, "faces": nf, "outer": outer, "face_of": face_of, "walks": walks, "dual_pos": dual_pos, "dual_edges": dual_edges}


def spanning_trees(v: int, edges) -> set[int]:
    """Alle Spannbäume (v − 1 Kanten, kreisfrei) als Kantenmasken."""
    out = set()
    for combo in itertools.combinations(range(len(edges)), v - 1):
        parent = list(range(v))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        good = True
        for e in combo:
            a, b = find(edges[e][0]), find(edges[e][1])
            if a == b:
                good = False
                break
            parent[a] = b
        if good:
            out.add(sum(1 << e for e in combo))
    return out


def dual_tree_check(inst, drawing) -> dict:
    """Die Spannbäume des Plans und die Komplemente der Spannbäume des Dualgraphen sind dieselben Mengen (und die Flächenzahl folgt Euler: m − n + 2)."""
    g_trees = spanning_trees(inst.n, [(u, w) for u, w, _ in inst.edges])
    d_trees = spanning_trees(drawing["faces"], drawing["dual_edges"])
    full = (1 << inst.m) - 1
    return {"n_trees": len(g_trees), "dual_trees": len(d_trees), "equal": g_trees == {full ^ t for t in d_trees}, "faces": drawing["faces"], "euler": drawing["faces"] == inst.m - inst.n + 2}


def node_sides(inst, cut: int) -> list[int]:
    """Seite (0 oder 1) jedes Knotens, wenn die Leitungen des Schnitts `cut` entfernt sind: Seite 0 enthält das Depot; weitere Komponenten zählen als Seite 1."""
    parent = list(range(inst.n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e, (u, w, _) in enumerate(inst.edges):
        if not cut >> e & 1:
            parent[find(u)] = find(w)
    root0 = find(0)
    return [0 if find(v) == root0 else 1 for v in range(inst.n)]


# --- alle Matroide auf n Elementen --------------------------------------------------------------------------------------------------------


def all_systems(n: int) -> list[tuple[bool, ...]]:
    """Alle nach unten abgeschlossenen Familien auf n Elementen mit leerer Menge, jeweils als Tupel ok[mask]."""
    masks = sorted(range(1 << n), key=lambda x: (popcount(x), x))
    out: list[tuple[bool, ...]] = []
    family = [False] * (1 << n)

    def rec(i):
        if i == len(masks):
            if family[0]:
                out.append(tuple(family))
            return
        mask = masks[i]
        allowed = mask == 0 or all(family[mask & ~(1 << e)] for e in range(n) if mask >> e & 1)
        family[mask] = False
        rec(i + 1)
        if allowed:
            family[mask] = True
            rec(i + 1)
            family[mask] = False

    rec(0)
    return out


def small_dual_row(n: int) -> dict:
    """Alle Matroide auf n Elementen: Dual ist Matroid, Doppeldual, Rangformel, Minoren-Identitäten (n ≥ 2), Orthogonalität; dazu selbstduale."""
    row = {"n": n, "systems": 0, "matroids": 0, "dual_matroid": 0, "involution": 0, "rank_formula": 0, "minor_identities": 0, "orthogonal": 0, "selfdual": 0,
           "non_matroids": 0, "non_dual_matroid": 0}
    for ok in all_systems(n):
        s = System("x", n, list(ok))
        row["systems"] += 1
        if not s.is_matroid:
            row["non_matroids"] += 1
            row["non_dual_matroid"] += dual(s).is_matroid
            continue
        row["matroids"] += 1
        d = dual(s)
        row["dual_matroid"] += d.is_matroid
        row["involution"] += dual(d).ok == s.ok
        row["rank_formula"] += dual_rank_formula_holds(s, d)
        row["selfdual"] += d.ok == s.ok
        row["orthogonal"] += orthogonal(s, d)
        if n >= 2:
            good = True
            for e in range(n):
                r = minor_identities(s, d, e)
                good &= all(r.values())
            row["minor_identities"] += good
    return row


def small_binary_row(n: int) -> dict:
    """Alle Matroide auf n Elementen: binär auf drei Wegen (Parität, Darstellung, kein U(2,4)-Minor)."""
    row = {"n": n, "matroids": 0, "binary": 0, "agree": 0}
    for ok in all_systems(n):
        s = System("x", n, list(ok))
        if not s.is_matroid:
            continue
        w = binary_ways(s, dual(s))
        row["matroids"] += 1
        row["binary"] += w["parity"]
        row["agree"] += w["parity"] == w["rep"] == w["no_u24"]
    return row
