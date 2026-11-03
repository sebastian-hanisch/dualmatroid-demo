"""Gemeinsame Fixtures: kleine Systeme, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dmo_algorithm import System  # noqa: E402
from dmo_scenario import Instance  # noqa: E402
from dmo_systems import fano_system  # noqa: E402


@pytest.fixture
def dreieck():
    """Graphisches Matroid eines Dreiecks, Kanten a, b, c = Elemente 0, 1, 2: zulässig sind alle Mengen mit höchstens 2 Kanten (U(2, 3)).
    Basen ab, ac, bc (Masken 3, 5, 6); einziger Kreis {a, b, c} (7). Dual: U(1, 3) mit Basen c, b, a; Kokreise {a, b}, {a, c}, {b, c} (3, 5, 6)."""
    return System("Dreieck", 3, [bin(mask).count("1") <= 2 for mask in range(8)])


@pytest.fixture
def parallel():
    """Zwei parallele Kanten a, b (0, 1) zwischen 1 und 2 und eine Brücke c (2): a und b schließen sich aus. Basen ac, bc (5, 6); Kreis {a, b} (3).
    Dual: Basen b, a (2, 1); Kokreise {c} (4, Schleife im Dual) und {a, b} (3)."""
    return System("parallel", 3, [not (mask & 1 and mask & 2) for mask in range(8)])


@pytest.fixture
def paarung3():
    """Paarung auf einem Pfad mit 3 Kanten e0, e1, e2 (kein Matroid): zulässig ∅, e0, e1, e2, e0e2; maximale Mengen {e1} (2) und {e0, e2} (5)."""
    return System("Paarung", 3, [not (mask & 1 and mask & 2) and not (mask & 2 and mask & 4) for mask in range(8)])


@pytest.fixture
def fano():
    """Fano-Ebene: die 7 von 0 verschiedenen Vektoren des GF(2)^3; 57 zulässige Mengen, 28 Basen, 14 Kreise, 7 Kokreise (Komplemente der Geraden), Dualrang 4."""
    return fano_system()


@pytest.fixture
def k4():
    """K4 planar gezeichnet: Dreieck 0, 1, 2 mit Mittelpunkt 3; Kanten (0,1), (0,2), (1,2), (0,3), (1,3), (2,3): 16 Spannbäume, 4 Flächen, 7 Bonds, selbstdual."""
    points = ((0.0, 0.0), (1.0, 0.0), (0.5, 1.0), (0.5, 0.35))
    return Instance(points, ((0, 1, 1.0), (0, 2, 1.0), (1, 2, 1.0), (0, 3, 1.0), (1, 3, 1.0), (2, 3, 1.0)))
