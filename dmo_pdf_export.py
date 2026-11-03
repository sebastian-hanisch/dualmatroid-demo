"""PDF-Export der Dualität des aktuellen Systems (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import dmo_constants as C
from dmo_evaluation import Analysis, Settings, cut_view, elemente, sizes_table, verdict_cut, verdict_no_dual, zahl

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x", "≈": "~", "∖": "\\", "∩": "n", "₁": "1", "₂": "2", "²": "2", "³": "3", "*": "*"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis, settings: Settings, cut_index: int = 0) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Dualität und Minoren"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    plan = "feste sieben Punkte" if settings.system == "fano" else f"{a.inst.n} Standorte, Plan-Seed {settings.seed}"
    pdf.multi_cell(0, 5, _s(f"{C.SYSTEM_NAMES[settings.system]}; {plan}; {'Matroid' if a.is_matroid else 'kein Matroid'}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    if not a.is_matroid:
        pdf.multi_cell(0, 5, _s(verdict_no_dual(a)[1]), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 8)
        heads = ("Größe", "M", "M* (Dual)")
        widths = (60, 40, 40)
        for h, w in zip(heads, widths):
            pdf.cell(w, 6, _s(h), border=1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        rows = (("Rang", a.rank, a.dual_rank), ("Basen", zahl(a.n_bases), zahl(a.n_bases)), ("Kreise", zahl(a.n_circuits), zahl(len(a.cocircuits))),
                ("Elemente", a.m, a.m))
        for row in rows:
            for val, w in zip(row, widths):
                pdf.cell(w, 5.5, _s(val), border=1)
            pdf.ln()
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        view = cut_view(settings, a, min(cut_index, len(a.cocircuits) - 1))
        pdf.multi_cell(0, 5, _s(verdict_cut(a, view)[1]), new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 5, _s("Durchschnitte der Kreise mit diesem Kokreis: " + ", ".join(f"{r['Zahl der Kreise']} Kreise mit {r['Elemente im Durchschnitt']}" for r in sizes_table(view, a.n_circuits)) + "."),
                       new_x="LMARGIN", new_y="NEXT")
        pdf.multi_cell(0, 5, _s(f"Binär: {'ja' if a.binary else 'nein'}; Kokreise insgesamt: {zahl(len(a.cocircuits))} ({elemente(a.m)} in der Grundmenge)."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: dualmatroid-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
