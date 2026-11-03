"""AppTest: Hauptansicht, Experimente, Spielwiese, Permalink und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import dmo_algorithm as A
import dmo_constants as C
import dmo_evaluation as ev
from dmo_pdf_export import build_pdf
from dmo_scenario import make_instance

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
PLAY = "wald_7_8"


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_default_shows_the_wald_cut_and_the_four_numbers():
    at = _app()
    assert any("ist ein **Schnitt** des Leitungsnetzes" in t and "Keiner der 32 Kreise" in t for t in _texts(at))
    assert [m.value for m in at.metric][:4] == ["6", "6", "32", "24"]


def test_main_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "ist ein **Schnitt** des Leitungsnetzes",
        "Kabelfarben": "Keiner der 25 Kreise",
        "Fano-Ebene": "Keiner der 14 Kreise",
        "Höchstens 4 Leitungen": "**nicht binär**",
        "Paarung (kein Matroid)": "es gibt **kein Dual**",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_cocircuit_slider_changes_the_cut():
    at = _app()
    at.slider(key=f"cut_{PLAY}").set_value(1).run()
    assert not at.exception and any("(1 Element) ist ein **Schnitt**" in t for t in _texts(at))
    at.slider(key=f"cut_{PLAY}").set_value(24).run()
    assert not at.exception and any("(7 Elemente) ist ein **Schnitt**" in t for t in _texts(at))


def test_experiment_one_dual_graph_and_its_variants():
    at = _app()
    assert any("Alle 180 Spannbäume des Plans" in t and "7 Flächen" in t for t in _texts(at))
    at.slider(key=f"dual_base_{PLAY}").set_value(5).run()
    assert not at.exception
    _click_preset(at, "Fano-Ebene")
    assert any("Den Dualgraphen gibt es hier nur beim Wald" in t for t in _texts(at))
    nonplanar = next(seed for seed in range(200) if A.planar_pos(make_instance(7, seed)) is None)
    bad = _app(dict(system="wald", n="7", seed=str(nonplanar)))
    assert any("nicht planar" in t for t in _texts(bad))


def test_experiment_two_minors_and_the_small_matroid_check():
    at = _app()
    assert any("(M ∖ e)* = M* / e" in t for t in _texts(at))
    at.radio(key="min_op").set_value("ziehen").run()
    assert not at.exception and any("(M / e)* = M* ∖ e" in t for t in _texts(at))
    at.selectbox(key=f"min_e_{PLAY}").set_value(5).run()
    assert not at.exception
    assert not any("497" in t for t in _texts(at))
    at.button(key="small_dual_run").click().run()
    assert not at.exception and any("Bei allen 497 Matroiden mit höchstens 5 Elementen" in t and "**0 Abweichungen**" in t for t in _texts(at))
    _click_preset(at, "Paarung (kein Matroid)")
    assert any("Minoren und Dualität werden nur bei Matroiden gezeigt" in t for t in _texts(at)) and any("497" in t for t in _texts(at))


def test_experiment_three_binary_and_the_small_matroid_check():
    at = _app()
    assert any("Das System ist **binär**" in t for t in _texts(at))
    _click_preset(at, "Höchstens 4 Leitungen")
    assert any("Das System ist **nicht binär**" in t and "U(2,4)" in t for t in _texts(at))
    at.button(key="small_bin_run").click().run()
    assert not at.exception and any("Nicht binär sind 0, 0, 0, 1, 32 von 2, 5, 16, 68, 406" in t for t in _texts(at))


def test_experiment_four_nongraphic_runs_on_demand():
    at = _app()
    assert not any("Bei keinem der fünf Matroide" in t for t in _texts(at))
    at.button(key="nongraphic_run").click().run()
    assert not at.exception and any("Bei keinem der fünf Matroide" in t and "331 506" in t for t in _texts(at))


def test_every_system_runs_without_exception_and_has_the_matching_verdict():
    at = _app()
    for system in C.SYSTEMS:
        at.sidebar.selectbox(key="system_select").set_value(system).run()
        assert not at.exception, (system, [str(e) for e in at.exception])
        texts = _texts(at)
        if system in C.MATROID_SYSTEMS:
            assert any("Keiner der" in t and "Kreise trifft ihn in genau einem Element" in t for t in texts), system
        else:
            assert any("**kein Dual**" in t for t in texts), system


def test_playground_branches():
    at = _app()
    assert any("ist ein **Kokreis**" in t for t in _texts(at))
    at.multiselect(key=f"play_f_{PLAY}").set_value([]).run()
    assert not at.exception and any(t == "Wählen Sie mindestens ein Element." for t in _texts(at))
    at.multiselect(key=f"play_f_{PLAY}").set_value([0]).run()
    assert not at.exception and any("weder Kreis noch Kokreis" in t for t in _texts(at))
    at.multiselect(key=f"play_f_{PLAY}").set_value(list(range(12))).run()
    assert not at.exception and any("enthält einen" in t for t in _texts(at))


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(n="8", seed="3", system="paarung"))
    assert at.sidebar.slider(key="n_slider").value == 8 and at.sidebar.number_input(key="seed_input").value == 3 and at.sidebar.selectbox(key="system_select").value == "paarung"
    bad = _app(dict(n="99", seed="-4", system="gibtsnicht"))
    assert bad.sidebar.slider(key="n_slider").value == C.N_MAX and bad.sidebar.number_input(key="seed_input").value == 0 and bad.sidebar.selectbox(key="system_select").value == "wald"


def test_address_line_mirrors_the_settings():
    at = _app(dict(system="budget"))
    assert str(at.query_params["system"]) in ("budget", "['budget']")


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception and "pdf_made" in at.session_state and at.session_state["pdf_made"][2][:4] == b"%PDF"


def test_pdf_builds_for_every_system():
    for key in C.SYSTEMS:
        s = ev.Settings(n=6, seed=2, system=key)
        assert build_pdf(ev.analyse(s), s)[:4] == b"%PDF", key


def test_extreme_plan_sizes_do_not_raise():
    for n in (C.N_MIN, C.N_MAX):
        for system in ("wald", "uniform", "fano", "paarung"):
            at = _app(dict(n=str(n), system=system))
            assert not at.exception, (n, system)
