"""Kennzahlen, Experimente und Verdikte. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

from dataclasses import dataclass
from functools import lru_cache

import dmo_constants as C
from dmo_algorithm import (
    System,
    binary_ways,
    cocircuits,
    crossing_free,
    dual,
    dual_drawing,
    dual_rank_formula_holds,
    dual_tree_check,
    elements,
    even_intersections,
    graph_system,
    graphic_search,
    intersection_sizes,
    minor,
    minor_identities,
    node_sides,
    odd_pair,
    planar_pos,
    popcount,
    small_binary_row,
    small_dual_row,
    u24_minor,
    uniform,
)
from dmo_scenario import Instance, make_instance
from dmo_systems import edge_colors, fano_system, get_system, ground_kind, labels


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def prozent(x: float, digits: int = 1) -> str:
    return de(100.0 * x, digits)


def zahl(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def elemente(k: int) -> str:
    return "1 Element" if k == 1 else f"{k} Elemente"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    system: str = "wald"


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: Instance
    kind: str               # "kanten", "knoten" oder "punkte"
    m: int                  # Zahl der Elemente der Grundmenge
    labels: tuple
    colors: tuple           # Kabelfarbe je Leitung (leer, wenn die Grundmenge keine Leitungen sind)
    is_matroid: bool
    rank: int
    n_bases: int            # Zahl der maximalen zulässigen Mengen
    base_sizes: tuple       # ((Größe, Zahl), ...)
    n_circuits: int
    dual_rank: int | None   # None bei einem Nicht-Matroid
    cocircuits: tuple       # Kokreise (Masken), nach Größe geordnet; leer bei einem Nicht-Matroid
    binary: bool | None     # Kreis-Kokreis-Parität; None bei einem Nicht-Matroid
    graphic_plan: bool      # das System ist der Wald auf dem Plan


@lru_cache(maxsize=32)
def get_dual(key: str, n: int, seed: int) -> System:
    return dual(get_system(key, n, seed))


def analyse(settings: Settings) -> Analysis:
    s = get_system(settings.system, settings.n, settings.seed)
    inst = make_instance(settings.n, settings.seed)
    kind = ground_kind(settings.system)
    base = dict(
        settings=settings, inst=inst, kind=kind, m=s.m, labels=tuple(labels(settings.system, inst)), colors=tuple(edge_colors(inst, settings.seed)) if kind == "kanten" else (),
        is_matroid=s.is_matroid, rank=s.rank, n_bases=len(s.bases), base_sizes=tuple(s.maximal_sizes().items()), n_circuits=len(s.circuits), graphic_plan=settings.system == "wald",
    )
    if not s.is_matroid:
        return Analysis(**base, dual_rank=None, cocircuits=(), binary=None)
    d = get_dual(settings.system, settings.n, settings.seed)
    return Analysis(**base, dual_rank=d.rank, cocircuits=tuple(cocircuits(d)), binary=even_intersections(s, d))


def names(a: Analysis, mask: int) -> str:
    return ", ".join(a.labels[e] for e in elements(mask, a.m)) or "keine"


def system_of(settings: Settings) -> System:
    return get_system(settings.system, settings.n, settings.seed)


# --- Hauptansicht: Kreis und Schnitt ---------------------------------------------------------------------------------------------------


def default_cut_index(a: Analysis) -> int:
    """Voreingestellter Kokreis: der erste mit mindestens 3 Elementen (ein Kokreis aus einer Brücke wäre ein langweiliger Anfang), sonst der erste."""
    return next((i for i, c in enumerate(a.cocircuits) if popcount(c) >= 3), 0)


def cut_view(settings: Settings, a: Analysis, index: int) -> dict:
    """Der Kokreis Nr. `index` (ab 0): Durchschnittsgrößen mit den Kreisen; beim Wald die zwei Seiten des Schnitts."""
    s = system_of(settings)
    cut = a.cocircuits[index]
    out = {"cut": cut, "sizes": intersection_sizes(s, cut), "sides": None}
    if a.graphic_plan:
        out["sides"] = node_sides(a.inst, cut)
    return out


def sizes_table(view: dict, total: int) -> list[dict]:
    return [{"Elemente im Durchschnitt": k, "Zahl der Kreise": c, "Anteil": f"{prozent(c / total)} %"} for k, c in view["sizes"].items()]


def verdict_cut(a: Analysis, view: dict) -> tuple[str, str]:
    cut = view["cut"]
    size = popcount(cut)
    sizes = view["sizes"]
    total = sum(sizes.values())
    if 1 in sizes:
        return "error", "Ein Kreis trifft einen Kokreis in genau einem Element. Das darf bei einem Matroid nicht sein: Rechenfehler."
    odd = {k: c for k, c in sizes.items() if k % 2}
    if a.graphic_plan:
        sides = view["sides"]
        left, right = sides.count(0), sides.count(1)
        head = (f"Der Kokreis {{{names(a, cut)}}} ({elemente(size)}) ist ein **Schnitt** des Leitungsnetzes: Ohne diese Leitungen zerfällt das Netz in zwei Teile mit {left} und {right} Standorten. ")
    else:
        head = f"Der Kokreis {{{names(a, cut)}}} ({elemente(size)}) ist eine kleinste Menge, die jede Basis trifft. "
    if not odd:
        tail = f"Keiner der {zahl(total)} Kreise trifft ihn in genau einem Element, und alle Durchschnitte haben eine **gerade** Größe."
        return "success", head + tail
    listing = ", ".join(f"{k} Elemente bei {zahl(c)} Kreisen" for k, c in odd.items())
    return "info", head + f"Keiner der {zahl(total)} Kreise trifft ihn in genau einem Element, aber ungerade Durchschnitte kommen vor ({listing}): Das System ist **nicht binär**."


def verdict_no_dual(a: Analysis) -> tuple[str, str]:
    sizes = ", ".join(f"{zahl(c)} mit {k}" for k, c in a.base_sizes)
    if len(a.base_sizes) > 1:
        reason = f"Die maximalen Mengen haben verschiedene Größen ({sizes}); Komplemente verschieden großer Mengen sind keine Basen eines Matroids."
    else:
        reason = f"Alle maximalen Mengen haben dieselbe Größe ({sizes}), aber der Basenaustausch ist verletzt."
    return "warning", f"Das System ist kein Matroid, und es gibt **kein Dual**: Die Komplemente der maximalen Mengen sind keine Basen eines Matroids. {reason}"


# --- Experiment 1: Dualgraph --------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=16)
def _drawing(n: int, seed: int):
    inst = make_instance(n, seed)
    pos = planar_pos(inst)
    if pos is None:
        return None
    drawing = dual_drawing(inst, pos)
    return drawing, dual_tree_check(inst, drawing)


def dual_view(settings: Settings, a: Analysis) -> dict:
    """Dualgraph des Plans (nur beim Wald): planare Zeichnung, Flächen, Test über alle Spannbäume."""
    if not a.graphic_plan:
        return {"available": False}
    inst = a.inst
    res = _drawing(settings.n, settings.seed)
    return {"available": True, "planar": res is not None, "crossing_free": crossing_free(inst), "drawing": res[0] if res else None, "check": res[1] if res else None,
            "bases": list(system_of(settings).bases)}


def verdict_dual_graph(a: Analysis, view: dict) -> tuple[str, str]:
    if not view["available"]:
        return "info", "Den Dualgraphen gibt es hier nur beim Wald: Die anderen Systeme sind keine Graphen auf dem Plan. Für sie bleibt das duale Matroid (Hauptansicht)."
    drawn = "" if view["crossing_free"] else "Auf dem Standortplan kreuzen sich Leitungen, deshalb ist der Plan hier **neu gezeichnet** (kreuzungsfrei). "
    if not view["planar"]:
        return "warning", (
            f"{drawn}Der Plan ist **nicht planar**: Es gibt keine kreuzungsfreie Zeichnung und also keinen Dualgraphen. Das duale Matroid des Waldes ist trotzdem ein Matroid (Hauptansicht), "
            f"aber **kein graphisches**: Das Dual eines graphischen Matroids ist genau bei planaren Graphen graphisch (Tutte; Experiment 4 zeigt es an K5 und K3,3)."
        )
    chk = view["check"]
    if not chk["equal"] or not chk["euler"]:
        return "error", "Die Komplemente der Spannbäume sind nicht die Spannbäume des Dualgraphen. Das darf nicht sein: Rechenfehler."
    m, n = a.m, a.inst.n
    return "success", (
        f"{drawn}Der Plan ist planar: {chk['faces']} Flächen (Euler: {m} − {n} + 2 = {m - n + 2}). Alle {zahl(chk['n_trees'])} Spannbäume des Plans haben als Komplement genau einen "
        f"Spannbaum des Dualgraphen (und umgekehrt): Das duale Matroid ist das graphische Matroid des Dualgraphen."
    )


# --- Experiment 2: Minoren ---------------------------------------------------------------------------------------------------------------


def minor_view(settings: Settings, e: int, op: str) -> dict:
    s = system_of(settings)
    d = get_dual(settings.system, settings.n, settings.seed)
    mi = minor(s, e, op)
    di = minor(d, e, "ziehen" if op == "loeschen" else "loeschen")
    ids = minor_identities(s, d, e)
    return {"e": e, "op": op, "minor": mi, "dual_minor": di, "ids": ids, "same": dual(mi).ok == di.ok, "dual_rank_ok": dual_rank_formula_holds(mi, dual(mi)) if mi.is_matroid else None}


def minor_rows(a: Analysis, view: dict) -> list[dict]:
    s, d = system_of(a.settings), get_dual(a.settings.system, a.settings.n, a.settings.seed)
    loeschen = view["op"] == "loeschen"
    rows = []
    for name, sys_ in (("M", s), ("M ∖ e" if loeschen else "M / e", view["minor"]), ("M*", d), ("M* / e" if loeschen else "M* ∖ e", view["dual_minor"])):
        rows.append({"Matroid": name, "Elemente": sys_.m, "Rang": sys_.rank, "Basen": zahl(len(sys_.bases)), "Kreise": zahl(len(sys_.circuits))})
    return rows


def verdict_minor(a: Analysis, view: dict) -> tuple[str, str]:
    ids = view["ids"]
    if not (ids["delete_matroid"] and ids["contract_matroid"]):
        return "error", "Ein Minor ist kein Matroid. Das darf nicht sein: Rechenfehler."
    if not (ids["delete_dual"] and ids["contract_dual"] and view["same"]):
        return "error", "Das Dual des Minors ist nicht der Minor des Duals. Das darf nicht sein: Rechenfehler."
    e = a.labels[view["e"]]
    if view["op"] == "loeschen":
        what = f"Löschen von {e} in M, Zusammenziehen von {e} in M*: (M ∖ e)* = M* / e"
        graph = " Beim Wald heißt Löschen: die Leitung entfernen." if a.graphic_plan else ""
    else:
        what = f"Zusammenziehen von {e} in M, Löschen von {e} in M*: (M / e)* = M* ∖ e"
        graph = " Beim Wald heißt Zusammenziehen: die Endpunkte der Leitung verschmelzen." if a.graphic_plan else ""
    di = view["dual_minor"]
    return "success", f"{what}. Beide Seiten haben dieselben zulässigen Mengen: Rang {di.rank}, {zahl(len(di.bases))} Basen.{graph}"


@lru_cache(maxsize=1)
def small_dual_rows() -> tuple:
    return tuple(small_dual_row(n) for n in range(1, C.ENUM_MAX_N + 1))


def small_dual_table(rows) -> list[dict]:
    return [
        {"Elemente n": r["n"], "Matroide": zahl(r["matroids"]), "Dual ist Matroid": zahl(r["dual_matroid"]), "Doppeldual gleich": zahl(r["involution"]), "Rangformel": zahl(r["rank_formula"]),
         "Minoren-Identitäten": zahl(r["minor_identities"]) if r["n"] >= 2 else "–", "Kreis-Kokreis ohne genau 1": zahl(r["orthogonal"]), "selbstdual": zahl(r["selfdual"]),
         "Nicht-Matroide mit Dual": f"{zahl(r['non_dual_matroid'])} von {zahl(r['non_matroids'])}"}
        for r in rows
    ]


def verdict_small_dual(rows) -> tuple[str, str]:
    mats = sum(r["matroids"] for r in rows)
    keys = ("dual_matroid", "involution", "rank_formula", "orthogonal")
    bad = sum(r["matroids"] - r[k] for r in rows for k in keys) + sum(r["matroids"] - r["minor_identities"] for r in rows if r["n"] >= 2) + sum(r["non_dual_matroid"] for r in rows)
    if bad:
        return "error", f"Bei {bad} Prüfungen gilt eine Aussage nicht. Das darf nicht sein: Rechenfehler."
    non = sum(r["non_matroids"] for r in rows)
    selfdual = ", ".join(f"{r['selfdual']} bei n = {r['n']}" for r in rows if r["selfdual"])
    return "success", (
        f"Bei allen {zahl(mats)} Matroiden mit höchstens {rows[-1]['n']} Elementen: Das Dual ist ein Matroid, das Doppeldual ist das Matroid selbst, die Rangformel gilt, Löschen und Zusammenziehen "
        f"vertauschen sich unter dem Dual, und kein Kreis trifft einen Kokreis in genau einem Element (**0 Abweichungen**). Beschriftet selbstdual sind {selfdual}. "
        f"Bei allen {zahl(non)} Nicht-Matroiden ist das System der Komplemente der maximalen Mengen **kein** Matroid."
    )


# --- Experiment 3: binär ----------------------------------------------------------------------------------------------------------------------


def binary_view(settings: Settings, a: Analysis) -> dict:
    s = system_of(settings)
    d = get_dual(settings.system, settings.n, settings.seed)
    with_minor = s.m <= C.U24_MAX_ELEMENTS
    ways = binary_ways(s, d, with_minor)
    witness = None if not with_minor else u24_minor(s)
    return {"ways": ways, "with_minor": with_minor, "u24": witness, "odd": odd_pair(s, d)}


def binary_rows(a: Analysis, view: dict) -> list[dict]:
    w = view["ways"]
    yn = lambda v: "–" if v is None else ("ja" if v else "nein")
    return [
        {"Weg": "Kreis-Kokreis-Parität: jeder Durchschnitt gerade", "binär?": yn(w["parity"])},
        {"Weg": "Darstellung über GF(2) zu einer festen Basis", "binär?": yn(w["rep"])},
        {"Weg": "kein U(2,4)-Minor", "binär?": yn(w["no_u24"]) if view["with_minor"] else f"nicht gerechnet (mehr als {C.U24_MAX_ELEMENTS} Elemente)"},
    ]


def verdict_binary(a: Analysis, view: dict) -> tuple[str, str]:
    w = view["ways"]
    vals = [v for v in (w["parity"], w["rep"], w["no_u24"]) if v is not None]
    if len(set(vals)) > 1:
        return "error", "Die Wege widersprechen sich. Das darf nicht sein: Rechenfehler."
    if w["parity"]:
        extra = "" if view["with_minor"] else f" (der U(2,4)-Minor wird nur bis {C.U24_MAX_ELEMENTS} Elemente gesucht)"
        return "success", f"Das System ist **binär**: Alle Kreis-Kokreis-Durchschnitte sind gerade, eine Darstellung über GF(2) stimmt auf allen Teilmengen, und es gibt keinen U(2,4)-Minor{extra}."
    c, k = view["odd"]
    text = f"Das System ist **nicht binär**: Der Kreis {{{names(a, c)}}} trifft den Kokreis {{{names(a, k)}}} in {popcount(c & k)} Elementen (ungerade), die Darstellung über GF(2) scheitert"
    if view["with_minor"] and view["u24"] is not None:
        x, cc = view["u24"]
        text += f", und nach dem Zusammenziehen von {{{names(a, cc)}}} bleibt auf {{{names(a, x)}}} das uniforme Matroid U(2,4): vier Elemente, je zwei unabhängig, je drei abhängig."
    else:
        text += "."
    return "info", text


@lru_cache(maxsize=1)
def small_binary_rows() -> tuple:
    return tuple(small_binary_row(n) for n in range(1, C.ENUM_MAX_N + 1))


def small_binary_table(rows) -> list[dict]:
    return [{"Elemente n": r["n"], "Matroide": zahl(r["matroids"]), "binär": zahl(r["binary"]), "nicht binär": zahl(r["matroids"] - r["binary"]), "drei Wege gleich": zahl(r["agree"])} for r in rows]


def verdict_small_binary(rows) -> tuple[str, str]:
    mats = sum(r["matroids"] for r in rows)
    agree = sum(r["agree"] for r in rows)
    if agree != mats:
        return "error", "Die drei Wege widersprechen sich bei einem kleinen Matroid. Das darf nicht sein: Rechenfehler."
    non = ", ".join(str(r["matroids"] - r["binary"]) for r in rows)
    return "success", (
        f"Bei allen {zahl(mats)} Matroiden mit höchstens {rows[-1]['n']} Elementen liefern Parität, Darstellung über GF(2) und „kein U(2,4)-Minor“ dasselbe. "
        f"Nicht binär sind {non} von " + ", ".join(zahl(r["matroids"]) for r in rows) + " (n = 1 bis 5): das erste ist U(2,4) bei n = 4."
    )


# --- Experiment 4: nicht graphisch ------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def nongraphic_rows() -> tuple:
    k33 = [(a, b) for a in range(3) for b in range(3, 6)]
    k5 = [(a, b) for a in range(5) for b in range(a + 1, 5)]
    fano = fano_system()
    targets = [
        ("Fano-Ebene F7", fano), ("Dual der Fano-Ebene F7*", dual(fano)), ("U(2,4)", uniform(2, 4)),
        ("Dual von K3,3: M*(K3,3)", dual(graph_system(6, k33))), ("Dual von K5: M*(K5)", dual(graph_system(5, k5))), ("Kontrolle: M(K3,3) selbst", graph_system(6, k33)),
    ]
    return tuple(graphic_search(t, label) for label, t in targets)


def nongraphic_table(rows) -> list[dict]:
    out = []
    for r in rows:
        out.append({
            "Matroid": r["label"], "Elemente": r["m"], "Rang": r["rank"], "Basen": zahl(r["bases"]), "Knotenpaare auf Rang + 1 Knoten": r["pairs"],
            "zusammenhängende einfache Graphen": zahl(r["candidates"]), "davon mit gleich vielen Spannbäumen": zahl(r["same_trees"]), "graphisch": "ja" if r["graphic"] else "nein",
        })
    return out


def verdict_nongraphic(rows) -> tuple[str, str]:
    control = rows[-1]
    targets = rows[:-1]
    if not control["graphic"] or any(r["graphic"] for r in targets):
        return "error", "Ein Matroid, das nicht graphisch sein soll, hat einen Graphen, oder die Kontrolle wird nicht gefunden. Das darf nicht sein: Rechenfehler."
    k5 = rows[4]
    return "success", (
        f"Bei keinem der fünf Matroide gibt es einen einfachen Graphen mit demselben Matroid: bei F7 und U(2,4) schon, weil es zu wenige Knotenpaare gibt, bei den anderen, weil "
        f"unter den Graphen (bei M\\*(K5): {zahl(k5['candidates'])} zusammenhängende) keiner **{k5['bases']}** Spannbäume hat. Die Kontrolle M(K3,3) wird dagegen als graphisch gefunden."
    )


# --- Spielwiese -----------------------------------------------------------------------------------------------------------------------------


def play_check(settings: Settings, mask: int) -> dict:
    s = system_of(settings)
    out = {"mask": mask, "empty": mask == 0, "independent": s.ok[mask], "circuit": mask in set(s.circuits), "cocircuit": False, "meets_all": None, "matroid": s.is_matroid}
    if s.is_matroid:
        d = get_dual(settings.system, settings.n, settings.seed)
        out["cocircuit"] = mask in set(d.circuits)
        out["meets_all"] = all(b & mask for b in s.bases) if mask else False
    return out


def verdict_play(a: Analysis, r: dict) -> tuple[str, str]:
    if r["empty"]:
        return "info", "Wählen Sie mindestens ein Element."
    parts = []
    if r["circuit"]:
        parts.append("ein **Kreis** (kleinste unzulässige Menge)")
    if r["cocircuit"]:
        parts.append("ein **Kokreis** (kleinste Menge, die jede Basis trifft; beim Wald ein minimaler Schnitt)")
    if parts:
        return "success", f"{{{names(a, r['mask'])}}} ist " + " und zugleich ".join(parts) + "."
    if r["independent"]:
        base = f"{{{names(a, r['mask'])}}} ist zulässig, also weder Kreis noch Kokreis."
    else:
        base = f"{{{names(a, r['mask'])}}} ist unzulässig, aber kein Kreis: Sie enthält einen kleineren Kreis."
    if r["matroid"] and r["meets_all"]:
        base += " Sie trifft jede Basis, ist aber nicht minimal: Sie enthält einen Kokreis."
    elif r["matroid"]:
        base += " Es gibt eine Basis, die sie nicht trifft."
    else:
        base += " Das System ist kein Matroid, ein Kokreis ist nicht definiert."
    return "info", base
