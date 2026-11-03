"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 9, 7           # Standorte inklusive Depot (Knoten A); bis 9 (16 mögliche Leitungen)
SEED_MAX, DEFAULT_SEED = 999999, 8
HUB_FACTOR = 0.4                            # nur vom Plan-Erzeuger gebraucht (keine Nabe in dieser Demo)
COST_SCALE = 100                            # Kosten einer Leitung = Entfernung auf dem Plan mal 100 (für das Budget-System)
BUDGET_SHARE = 0.4                          # Budget-System: zulässig ist, was zusammen höchstens 40 % der Kosten aller Leitungen kostet
UNIFORM_K = 4                               # uniformes Matroid: höchstens 4 Leitungen
GRID = 4                                    # Standorte als Vektoren: Koordinaten mal 4, gerundet, Vektor (x, y, 1)
CABLE_COLORS = ("rot", "grün", "blau")      # Kabelfarben der Leitungen
ENUM_MAX_N = 5                              # alle Matroide bis zu so vielen Elementen aufzählen
U24_MAX_ELEMENTS = 12                       # die Suche nach einem U(2,4)-Minor am gewählten System nur bis zu so vielen Elementen (sonst zu langsam)
REP_MAX_ELEMENTS = 16                       # die Darstellung über GF(2) am gewählten System bis zu so vielen Elementen
SMALL_FACES_CHECK_MAX_N = 9                 # den Dualgraph-Test über alle Spannbäume bis zu so vielen Standorten (n = 9: 12 870 Teilmengen)

SYSTEMS = ("wald", "farben", "anschluss", "uniform", "vektoren", "fano", "paarung", "wald2", "budget", "standorte", "wald_farben")
MATROID_SYSTEMS = ("wald", "farben", "anschluss", "uniform", "vektoren", "fano")
SYSTEM_NAMES = {
    "wald": "Wald (graphisches Matroid)",
    "farben": "höchstens eine Leitung je Kabelfarbe (Partitionsmatroid)",
    "anschluss": "jede Leitung mit eigenem Anschluss-Standort (bizirkulares Matroid)",
    "uniform": "höchstens 4 Leitungen (uniformes Matroid)",
    "vektoren": "Standorte als Vektoren über R (lineares Matroid)",
    "fano": "Fano-Ebene (lineares Matroid über GF(2))",
    "paarung": "Paarung (höchstens 1 Leitung je Standort)",
    "wald2": "Wald, höchstens 2 Leitungen je Standort",
    "budget": "Budget-Auswahl (Rucksack auf den Leitungen)",
    "standorte": "Standorte ohne Nachbarn (unabhängige Menge)",
    "wald_farben": "Wald und höchstens eine Leitung je Kabelfarbe (Schnitt zweier Matroide)",
}

COLOR_CUT = "#d95f02"                       # Schnitt (Kokreis) und Dualkanten
COLOR_TREE = "#2F6B65"                      # Spannbaum, Basis
COLOR_SIDE_A = "#4c78a8"                    # eine Seite des Schnitts
COLOR_SIDE_B = "#1b9e77"                    # die andere Seite
COLOR_REMOVED = "#c0392b"                   # gelöschtes oder zusammengezogenes Element
COLOR_DUAL_NODE = "#d95f02"
COLOR_SET = "#4c78a8"                       # frei gewählte Menge der Spielwiese
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_NODE = "#4c78a8"
COLOR_DEPOT = "#f0a30a"
CABLE_RGB = {"rot": "rgba(200,60,60,0.55)", "grün": "rgba(60,150,80,0.55)", "blau": "rgba(70,110,200,0.55)"}

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "system": "wald"},
    "Kabelfarben": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "system": "farben"},
    "Fano-Ebene": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "system": "fano"},
    "Höchstens 4 Leitungen": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "system": "uniform"},
    "Paarung (kein Matroid)": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "system": "paarung"},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Wald auf dem Leitungsnetz: die Kokreise sind die minimalen Schnitte, und der Plan ist planar, das Dual ist der Dualgraph.",
    "Kabelfarben": "Höchstens eine Leitung je Kabelfarbe: ein Partitionsmatroid, dual dazu ist das Matroid mit drei Kokreisen (die Farbklassen).",
    "Fano-Ebene": "Sieben Punkte, Rang 3, Dualrang 4, 7 Kokreise; binär, aber nicht graphisch.",
    "Höchstens 4 Leitungen": "Ein uniformes Matroid: nicht binär (U(2,4)-Minor), dual dazu ist U(8,12).",
    "Paarung (kein Matroid)": "Kein Matroid: Die Komplemente der maximalen Mengen sind keine Basen eines Matroids, es gibt kein Dual.",
}
