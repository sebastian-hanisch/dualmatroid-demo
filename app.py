"""Dualität und Minoren - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 6 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import dmo_constants as C
from dmo_algorithm import elements
from dmo_evaluation import (
    Settings,
    analyse,
    binary_rows,
    binary_view,
    cut_view,
    default_cut_index,
    dual_view,
    elemente,
    minor_rows,
    minor_view,
    nongraphic_rows,
    nongraphic_table,
    play_check,
    small_binary_rows,
    small_binary_table,
    small_dual_rows,
    small_dual_table,
    sizes_table,
    verdict_binary,
    verdict_cut,
    verdict_dual_graph,
    verdict_minor,
    verdict_no_dual,
    verdict_nongraphic,
    verdict_play,
    verdict_small_binary,
    verdict_small_dual,
    zahl,
)
from dmo_layout import dunkles_design, kopf_css
from dmo_pdf_export import build_pdf
from dmo_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from dmo_visualization import build_bar_chart, build_dual_plan, build_minor_plan, build_plan

st.set_page_config(page_title="Dualität und Minoren – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Dual, Basen und Kreise bestimmen …")
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _cut(settings, index):
    return cut_view(settings, analyse(settings), index)


@st.cache_data(show_spinner="Dualgraph zeichnen und alle Spannbäume prüfen …")
def _dual_view(settings):
    return dual_view(settings, analyse(settings))


@st.cache_data(show_spinner="Minor und sein Dual bestimmen …")
def _minor(settings, e, op):
    return minor_view(settings, e, op)


@st.cache_data(show_spinner="Binär auf drei Wegen prüfen …")
def _binary(settings):
    return binary_view(settings, analyse(settings))


@st.cache_data(show_spinner="Alle Matroide bis 5 Elemente aufzählen (einige Sekunden) …")
def _small_dual():
    return small_dual_rows()


@st.cache_data(show_spinner="Alle Matroide bis 5 Elemente binär prüfen (einige Sekunden) …")
def _small_binary():
    return small_binary_rows()


@st.cache_data(show_spinner="Einfache Graphen aufzählen (einige Sekunden) …")
def _nongraphic():
    return nongraphic_rows()


@st.cache_data(show_spinner=False)
def _play(settings, mask):
    return play_check(settings, mask)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in dmo_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔀 Dualität und Minoren")
st.markdown(
    """
Stück 4 hat den **Kreis** eingeführt, die kleinsten Mengen, die nicht zulässig sind. Hier kommt das **Gegenstück**: das **duale Matroid** M*, dessen Basen die **Komplemente der Basen** von M sind. Seine Kreise sind die **Kokreise** von M, die kleinsten Mengen, die jede Basis treffen; beim Wald sind das genau die **minimalen Schnitte** des Leitungsnetzes. Kreis und Schnitt sind also derselbe Begriff in M und in M*. Dazu vertauschen sich Löschen und Zusammenziehen unter dem Dual, bei planaren Graphen ist das Dual der **Dualgraph**, und nicht jedes Matroid ist **graphisch** (die Fano-Ebene nicht); ob ein Matroid **binär** ist, zeigt ein Minor namens U(2,4).

Dies ist das **sechste Stück** der Reihe „Matroide und Submodularität“. Weiter unten: vier Experimente (🔬), eine **Spielwiese**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So hängt es zusammen", expanded=True):
    st.markdown(
        """
1. **Dual:** Die Basen von M* sind die Komplemente der Basen von M. Der Rang ist r*(F) = |F| − r(E) + r(E ∖ F). Das Dual des Duals ist M. Nur bei einem **Matroid** ist das System der Komplemente wieder ein Matroid.
2. **Kokreis:** ein Kreis des Duals, also eine kleinste Menge, die jede Basis trifft. Beim Wald: ein **minimaler Schnitt** (beide Seiten hängen zusammen). Kein Kreis trifft einen Kokreis in genau einem Element.
3. **Minoren:** Löschen M ∖ e (Elemente ohne e) und Zusammenziehen M / e (Mengen, die mit e zulässig sind). Beim Graphen: Leitung entfernen, Endpunkte verschmelzen. Unter dem Dual vertauschen sie sich: (M ∖ e)* = M* / e.
4. **Planar:** Jede Fläche wird ein Knoten, jede Leitung eine Dualleitung zwischen den zwei Flächen daneben. Die Komplemente der Spannbäume sind genau die Spannbäume des Dualgraphen. Bei **nichtplanaren** Graphen ist das Dual nicht mehr graphisch.
5. **Binär** (über GF(2) darstellbar): jeder Kreis trifft jeden Kokreis gerade oft, gleichwertig: **kein U(2,4)-Minor**. Graphische Matroide sind binär; die Fano-Ebene ist binär, aber nicht graphisch.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Plan**")
    n = st.slider("Standorte (mit Depot A)", *bounds("n_slider"), key="n_slider", help="Wie viele Standorte der Plan hat. Bis 9 (16 mögliche Leitungen).")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**System**")
    system = st.selectbox("Zulässige Mengen", C.SYSTEMS, key="system_select", format_func=lambda k: C.SYSTEM_NAMES[k] + ("" if k in C.MATROID_SYSTEMS else (" (auf dem Standardplan kein Matroid)" if k == "wald_farben" else " (kein Matroid)")),
                          help="Sechs Matroide und fünf Systeme, die auf dem Standardplan keine sind (ohne Dual; Wald und Farbregel ist auf manchen Plänen doch ein Matroid). Die Fano-Ebene hat feste sieben Punkte und hängt nicht vom Plan ab.")

sync_query_params({"n_slider": int(n), "seed_input": int(seed), "system_select": system})

settings = Settings(int(n), int(seed), system)
a = _analysis(settings)
inst = a.inst
play_id = f"{system}_{settings.n}_{settings.seed}"
ground = {"kanten": "Leitungen", "knoten": "Standorte", "punkte": "Punkte der Fano-Ebene"}[a.kind]

# --- Kreis und Schnitt -----------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Kreis und Schnitt")
st.caption(f"{C.SYSTEM_NAMES[system]}: Grundmenge sind die {ground} ({a.m} Elemente); {'ein Matroid' if a.is_matroid else 'kein Matroid'}.")
cut_index = 0
if a.is_matroid:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rang r", a.rank)
    m2.metric("Dualrang r*", a.dual_rank, help=f"Dualrang = Elemente − Rang = {a.m} − {a.rank}")
    m3.metric("Kreise von M", zahl(a.n_circuits))
    m4.metric("Kokreise von M", zahl(len(a.cocircuits)), help="Die Kokreise von M sind die Kreise des Duals M*.")
    if len(a.cocircuits) > 1:
        cut_index = st.slider("Kokreis Nr.", 1, len(a.cocircuits), default_cut_index(a) + 1, key=f"cut_{play_id}", help="Welcher Kokreis betrachtet wird (nach Größe und Maske geordnet).") - 1
    view = _cut(settings, cut_index)
    col_a, col_b = st.columns(2)
    with col_a:
        node_colors = {v: (C.COLOR_SIDE_A if side == 0 else C.COLOR_SIDE_B) for v, side in enumerate(view["sides"])} if view["sides"] else None
        st.plotly_chart(build_plan(inst, a.kind, [("Kokreis" + (" (Schnitt)" if a.graphic_plan else ""), elements(view["cut"], a.m), C.COLOR_CUT)], a.colors, node_colors=node_colors),
                        width="stretch", key="map_cut")
    with col_b:
        st.markdown("**Wie viele Elemente jeder Kreis mit dem Kokreis gemeinsam hat**")
        st.dataframe(sizes_table(view, a.n_circuits), hide_index=True, width="stretch")
        st.caption("Orange: der Kokreis" + (", blau und grün: die zwei Seiten des Schnitts." if a.graphic_plan else "."))
else:
    st.metric("Maximale Mengen", zahl(a.n_bases), delta=f"{len(a.base_sizes)} verschiedene Größen" if len(a.base_sizes) > 1 else "alle gleich groß", delta_color="off")

if st.button("📄 PDF des aktuellen Systems erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, cut_index, build_pdf(a, settings, cut_index))
made = st.session_state.get("pdf_made")
if made and made[:2] == (settings, cut_index):
    st.download_button("⬇️ PDF herunterladen", data=made[2], file_name="dualitaet-und-minoren.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was ist das Gegenstück zum Kreis?")
if a.is_matroid:
    kind_v, text_v = verdict_cut(a, view)
else:
    kind_v, text_v = verdict_no_dual(a)
getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Der Dualgraph")
st.caption("Beim Wald auf einem planaren Plan ist das Dual der Dualgraph: Flächen werden Knoten, Leitungen kreuzen sich mit ihrer Dualleitung. Wählen Sie eine Basis (einen Spannbaum): Seine Komplement-Leitungen bilden einen Spannbaum des Dualgraphen.")
dv = _dual_view(settings)
if dv["available"] and dv["planar"]:
    bases = dv["bases"]
    idx = st.slider("Spannbaum Nr.", 1, len(bases), 1, key=f"dual_base_{play_id}", help="Welche Basis betrachtet wird (in der Reihenfolge der Bitmasken).") if len(bases) > 1 else 1
    st.plotly_chart(build_dual_plan(inst, dv["drawing"], bases[idx - 1]), width="stretch", key="map_dual")
    st.caption("Blaugrün: der Spannbaum (Basis) im Plan. Orange gestrichelt: die Dualleitungen der übrigen Leitungen, sie bilden einen Spannbaum des Dualgraphen. Quadrate: die Flächen (F∞ ist die Außenfläche).")
kind_v, text_v = verdict_dual_graph(a, dv)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 2: Minoren und Dualität")
st.caption("Wählen Sie ein Element e und eine Operation. Das Dual des Minors ist der Minor des Duals mit vertauschter Operation.")
if a.is_matroid and a.m >= 2:
    c1, c2 = st.columns(2)
    with c1:
        e_min = st.selectbox("Element e", list(range(a.m)), key=f"min_e_{play_id}", format_func=lambda x: a.labels[x])
    with c2:
        op = st.radio("Operation", ("loeschen", "ziehen"), horizontal=True, key="min_op", format_func={"loeschen": "Löschen M ∖ e", "ziehen": "Zusammenziehen M / e"}.get)
    mv = _minor(settings, e_min, op)
    st.dataframe(minor_rows(a, mv), hide_index=True, width="stretch")
    if a.graphic_plan:
        fig, loops = build_minor_plan(inst, e_min, op)
        st.plotly_chart(fig, width="stretch", key="map_minor")
        st.caption("Der Graph nach der Operation" + (f" (beim Zusammenziehen werden {loops} Leitungen zu Schleifen und nicht gezeichnet; parallele Leitungen sind leicht versetzt)." if op == "ziehen" else "."))
    kind_v, text_v = verdict_minor(a, mv)
    getattr(st, kind_v)(text_v)
elif not a.is_matroid:
    st.info("Das System ist kein Matroid und hat kein Dual; Minoren und Dualität werden nur bei Matroiden gezeigt. Die Prüfung unten gilt für alle kleinen Matroide.")
if st.button("📊 Alle Matroide bis 5 Elemente prüfen", key="small_dual_run"):
    st.session_state["small_dual_done"] = True
if st.session_state.get("small_dual_done"):
    rows = _small_dual()
    st.dataframe(small_dual_table(rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_small_dual(rows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 3: Binär auf drei Wegen")
st.caption("Ein Matroid ist binär, wenn es über GF(2) darstellbar ist. Drei Prüfungen, die dasselbe sagen sollen: Kreis-Kokreis-Parität, eine Darstellung über GF(2), und kein U(2,4)-Minor.")
if a.is_matroid:
    bv = _binary(settings)
    st.dataframe(binary_rows(a, bv), hide_index=True, width="stretch")
    kind_v, text_v = verdict_binary(a, bv)
    getattr(st, kind_v)(text_v)
else:
    st.info("Das System ist kein Matroid; binär ist nur bei Matroiden erklärt. Die Prüfung unten gilt für alle kleinen Matroide.")
if st.button("📊 Alle Matroide bis 5 Elemente binär prüfen", key="small_bin_run"):
    st.session_state["small_bin_done"] = True
if st.session_state.get("small_bin_done"):
    rows = _small_binary()
    st.dataframe(small_binary_table(rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_small_binary(rows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 4: Nicht jedes Matroid ist graphisch")
st.caption("Gibt es einen einfachen Graphen, dessen Kreise genau die Kreise des Matroids sind? Ein zusammenhängendes graphisches Matroid vom Rang r kommt von einem einfachen Graphen auf r + 1 Knoten; man zählt dessen Spannbäume (Kirchhoff) und vergleicht mit der Zahl der Basen.")
if st.button("🧮 Fünf Matroide prüfen (einige Sekunden)", key="nongraphic_run"):
    st.session_state["nongraphic_done"] = True
if st.session_state.get("nongraphic_done"):
    rows = _nongraphic()
    st.dataframe(nongraphic_table(rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_nongraphic(rows)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: Kreis, Kokreis oder keines von beiden?")
st.caption("Wählen Sie eine Menge F von Elementen. Die App sagt, ob F ein Kreis, ein Kokreis (beim Wald ein minimaler Schnitt) oder keines von beiden ist.")
default_f = elements(a.cocircuits[default_cut_index(a)], a.m) if a.cocircuits else []
sel_f = st.multiselect("Menge F", list(range(a.m)), default=default_f, key=f"play_f_{play_id}", format_func=lambda x: a.labels[x])
pr = _play(settings, sum(1 << x for x in sel_f))
kind_v, text_v = verdict_play(a, pr)
getattr(st, kind_v)(text_v)
if sel_f:
    st.plotly_chart(build_plan(inst, a.kind, [("gewählte Menge F", sel_f, C.COLOR_SET)], a.colors), width="stretch", key="map_play")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist (wer setzt an) |
|---|---|
| **Die Grundmenge ist klein (höchstens 16 Elemente)** | Basen, Kreise und Dual werden aus allen Teilmengen berechnet. Die Aufzählung aller Matroide geht nur bis 5 Elemente, die Suche nach einem U(2,4)-Minor nur bis 12 Elemente. **(Stück 17)** |
| **Das System ist ein Matroid** | Bei den fünf Systemen, die auf dem Standardplan keine Matroide sind, gibt es kein Dual: Die Komplemente der maximalen Mengen sind keine Basen eines Matroids. **(Stück 3)** |
| **Der Plan ist planar** | Den Dualgraphen gibt es nur bei planaren Plänen (und hier nur beim Wald); die Standort-Zeichnung ist selten kreuzungsfrei, deshalb wird der Plan neu gezeichnet. Bei nichtplanaren Plänen ist das Dual ein Matroid, aber nicht graphisch; gezeigt wird das nur an K5 und K3,3, im Allgemeinen ist es ein Satz von Whitney (Planaritätskriterium). **(Stück 6)** |
| **„Nicht graphisch“ nur für fünf Matroide** | Die Aufzählung gilt für F7, F7*, U(2,4), M*(K3,3) und M*(K5) unter der Annahme, dass ein zusammenhängendes graphisches Matroid von einem einfachen Graphen auf Rang + 1 Knoten kommt; eine allgemeine Prüfung „ist dieses Matroid graphisch?“ gibt es hier nicht. **(Stück 6)** |
| **Binär, nicht regulär** | Regulär (über jedem Körper darstellbar) heißt zusätzlich: weder F7 noch F7* als Minor; das wird hier nicht gezeigt. **(nicht in dieser Reihe)** |
| **Ein Matroid, nicht zwei** | Der Schnitt zweier Matroide ist im Allgemeinen kein Matroid und hat dann kein Dual; man braucht den Matroid-Schnitt-Algorithmus. **(Stück 7)** |
| **Das Tutte-Polynom** | Es verträgt sich mit Dualität (Vertauschen der beiden Variablen), wird hier aber nicht gezeigt. **(Stück 16)** |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein Matroid $M = (E, \mathcal{I})$ mit Basen $\mathcal{B}$ und Rang $r$.

| Symbol | Bedeutung |
|---|---|
| $M^*$ | duales Matroid: Basen $\{E \setminus B : B \in \mathcal{B}\}$ |
| $r^*(F)$ | Rang im Dual: $\lvert F \rvert - r(E) + r(E \setminus F)$ |
| $C^*$ | Kokreis: Kreis von $M^*$, kleinste Menge, die jede Basis trifft |
| $M \setminus e$ | Löschen: $\{I \subseteq E - e : I \in \mathcal{I}\}$ |
| $M / e$ | Zusammenziehen (für $e$ keine Schleife): $\{I \subseteq E - e : I \cup e \in \mathcal{I}\}$ |

**Dualität.** $M^*$ ist ein Matroid, $(M^*)^* = M$, und $r(M^*) = \lvert E \rvert - r(M)$. Es gilt $(M \setminus e)^* = M^* / e$ und $(M / e)^* = M^* \setminus e$. Für jeden Kreis $C$ und jeden Kokreis $C^*$ gilt $\lvert C \cap C^* \rvert \neq 1$.

**Graphen.** Für einen zusammenhängenden Graphen $G$ sind die Kokreise von $M(G)$ genau die **Bonds** (minimale Kantenschnitte). Ist $G$ planar mit Dualgraph $G^*$, so ist $M(G)^* = M(G^*)$: Die Komplemente der Spannbäume von $G$ sind genau die Spannbäume von $G^*$. Allgemein ist $M(G)^*$ genau dann graphisch, wenn $G$ planar ist (Whitney).

**Binär.** Ein Matroid ist binär (über $\mathrm{GF}(2)$ darstellbar) genau dann, wenn jeder Kreis jeden Kokreis in einer geraden Zahl von Elementen schneidet, genau dann, wenn es keinen Minor $U_{2,4}$ hat (Tutte). Zu einer Basis $B$ ist die Darstellung eindeutig: $e \notin B$ ist die Summe der Einheitsvektoren der Elemente von $B$ im Fundamentalkreis $C(B, e)$.

**Nicht graphisch.** Ein graphisches Matroid vom Rang $r$ ohne parallele Elemente und Schleifen hat höchstens $\binom{r+1}{2}$ Elemente (einfacher Graph auf $r + 1$ Knoten); die Fano-Ebene hat 7 Elemente bei Rang 3 und $\binom{4}{2} = 6$. Sonst zählt man die Spannbäume eines Kandidaten (Kirchhoff, Determinante des gekürzten Laplace-Matrix) und vergleicht mit $\lvert \mathcal{B} \rvert$.

**Literatur.** Dass $M(G)^*$ genau bei planaren $G$ graphisch ist, ist das Planaritätskriterium von Whitney; die Kennzeichnung der binären Matroide über $U_{2,4}$ stammt von Tutte; die Quellen (Vorlesungsskripte, Übersichtsarbeiten, per Websuche) wurden nur über Auszüge eingesehen, nicht die Originalarbeiten; Standardwerk: Oxley, *Matroid Theory*, nicht eingesehen. Die Konstruktion des Dualgraphen über das Rotationssystem und die Aufzählung der Graphen sind hier hergeleitet und nachgerechnet.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
