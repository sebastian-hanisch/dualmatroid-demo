"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import dmo_constants as C
import dmo_evaluation as ev
import dmo_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX and preset["system"] in C.SYSTEMS


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    assert P.SETTING_SPECS["system_select"].default == ev.Settings().system == "wald"


def test_setting_specs_cover_every_preset_key_and_have_valid_defaults():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for spec in P.SETTING_SPECS.values():
        assert spec.choices is None or (spec.default in spec.choices and spec.lo in spec.choices and spec.hi in spec.choices)
    assert P.SETTING_SPECS["system_select"].hi not in {p["system"] for p in C.PRESETS.values()}      # sonst fällt die Hervorhebung mit einem Preset zusammen


def test_standardfall_help_numbers_hold():
    a = ev.analyse(_settings("Standardfall (Voreinstellung)"))
    assert a.is_matroid and a.graphic_plan and len(a.cocircuits) == 24
    assert ev.dual_view(a.settings, a)["planar"]


def test_kabelfarben_help_says_three_cocircuits_and_dual_rank_nine():
    a = ev.analyse(_settings("Kabelfarben"))
    assert len(a.cocircuits) == 3 and (a.rank, a.dual_rank) == (3, 9) and a.binary


def test_fano_help_numbers_hold():
    a = ev.analyse(_settings("Fano-Ebene"))
    assert (a.rank, a.dual_rank, len(a.cocircuits), a.binary) == (3, 4, 7, True)


def test_uniform_help_says_not_binary_and_dual_u812():
    a = ev.analyse(_settings("Höchstens 4 Leitungen"))
    assert a.binary is False and (a.rank, a.dual_rank) == (4, 8) and a.n_bases == 495


def test_paarung_has_no_dual():
    a = ev.analyse(_settings("Paarung (kein Matroid)"))
    assert not a.is_matroid and a.dual_rank is None and a.cocircuits == ()
