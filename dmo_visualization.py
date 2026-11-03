"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import dmo_constants as C

# Fano-Ebene als Zeichnung: Mittelpunkt P1, Ecken P2, P4, P7, Seitenmitten P3 (gegenüber P2), P5 (gegenüber P4), P6 (gegenüber P7); sieben Geraden.
FANO_POINTS = {0: (0.5, 0.383), 1: (0.5, 0.95), 2: (0.5, 0.1), 3: (0.05, 0.1), 4: (0.725, 0.525), 5: (0.275, 0.525), 6: (0.95, 0.1)}
FANO_LINES = ((0, 1, 2), (0, 3, 4), (0, 5, 6), (1, 3, 5), (1, 4, 6), (2, 3, 6), (2, 4, 5))   # Punkte als Index 0 bis 6, P1 bis P7


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _lines(inst, edge_ids):
    xs, ys = [], []
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        xs += [inst.points[u][0], inst.points[v][0], None]
        ys += [inst.points[u][1], inst.points[v][1], None]
    return xs, ys


def build_plan(inst, kind, groups, colors=(), height=430, node_colors=None):
    """Plan der Standorte oder die Fano-Zeichnung. kind: "kanten" (Elemente sind Leitungen), "knoten" (Standorte), "punkte" (Fano).
    groups: Liste (Name, Elemente, Farbe) in Zeichenreihenfolge, hervorgehoben (Leitungen dick, Standorte groß). colors: Kabelfarbe je Leitung (dünn gezeichnet).
    node_colors: {Standort: Farbe} für die Standorte bei Elementen, die Leitungen sind (zum Beispiel die zwei Seiten eines Schnitts)."""
    fig = go.Figure()
    marked = {e for _, ids, _ in groups for e in ids}
    if kind == "punkte":
        return _fano_figure(groups, height)
    if kind == "kanten":
        for color in sorted(set(colors)) or [None]:
            ids = [e for e in range(inst.m) if e not in marked and (color is None or colors[e] == color)]
            if ids:
                xs, ys = _lines(inst, ids)
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.CABLE_RGB[color] if color else C.COLOR_OTHER, width=2), name=f"Kabel {color}" if color else "mögliche Leitung", hoverinfo="skip"))
        for name, ids, color in groups:
            if ids:
                xs, ys = _lines(inst, ids)
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=6), name=name, hoverinfo="skip"))
    colors_of_nodes, sizes = [], []
    for v in range(inst.n):
        colors_of_nodes.append((node_colors or {}).get(v, C.COLOR_DEPOT if v == 0 else C.COLOR_NODE))
        sizes.append(16)
    if kind == "knoten":
        for name, ids, color in groups:
            for v in ids:
                colors_of_nodes[v] = color
                sizes[v] = 26
    fig.add_trace(go.Scatter(
        x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text",
        text=[inst.name(v) for v in range(inst.n)],
        textposition="top center", textfont=dict(size=14), marker=dict(size=sizes, color=colors_of_nodes, line=dict(color="white", width=1.5)),
        name="Standort", hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))
    if kind == "knoten":
        for name, ids, color in groups:
            if ids:
                fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=14, color=color), name=name))
    fig.add_trace(go.Scatter(x=[-0.05, 1.05], y=[-0.05, 1.05], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def _fano_figure(groups, height):
    fig = go.Figure()
    for tri in FANO_LINES[:6]:
        a, b, c = tri
        ends = sorted(tri, key=lambda i: (FANO_POINTS[i][0], FANO_POINTS[i][1]))
        xs = [FANO_POINTS[ends[0]][0], FANO_POINTS[ends[-1]][0]]
        ys = [FANO_POINTS[ends[0]][1], FANO_POINTS[ends[-1]][1]]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=1.5), hoverinfo="skip", showlegend=False))
    (ax, ay), (bx, by), (qx, qy) = FANO_POINTS[2], FANO_POINTS[4], FANO_POINTS[5]          # die Gerade P3, P5, P6 ist der Kreis durch diese drei Punkte
    d = 2 * (ax * (by - qy) + bx * (qy - ay) + qx * (ay - by))
    cx = ((ax ** 2 + ay ** 2) * (by - qy) + (bx ** 2 + by ** 2) * (qy - ay) + (qx ** 2 + qy ** 2) * (ay - by)) / d
    cy = ((ax ** 2 + ay ** 2) * (qx - bx) + (bx ** 2 + by ** 2) * (ax - qx) + (qx ** 2 + qy ** 2) * (bx - ax)) / d
    r = math.dist((cx, cy), (ax, ay))
    circle =[(cx + r * math.cos(t / 50 * 2 * math.pi), cy + r * math.sin(t / 50 * 2 * math.pi)) for t in range(51)]
    fig.add_trace(go.Scatter(x=[p[0] for p in circle], y=[p[1] for p in circle], mode="lines", line=dict(color=C.COLOR_OTHER, width=1.5), hoverinfo="skip", showlegend=False))
    marked = {}
    for name, ids, color in groups:
        for e in ids:
            marked[e] = color
    fig.add_trace(go.Scatter(
        x=[FANO_POINTS[e][0] for e in range(7)], y=[FANO_POINTS[e][1] for e in range(7)], mode="markers+text", text=[f"P{e + 1}" for e in range(7)],
        textposition="top center", textfont=dict(size=14),
        marker=dict(size=[26 if e in marked else 16 for e in range(7)], color=[marked.get(e, C.COLOR_NODE) for e in range(7)], line=dict(color="white", width=1.5)),
        hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))
    for name, ids, color in groups:
        if ids:
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=14, color=color), name=name))
    fig.add_trace(go.Scatter(x=[-0.05, 1.05], y=[-0.05, 1.05], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_bar_chart(categories, values, colors, x_title, y_title, hover, height=300):
    """Balken; hover ist eine Formatzeichenfolge mit %{x} und %{y}."""
    fig = go.Figure(go.Bar(x=list(categories), y=list(values), marker_color=list(colors), hovertemplate=hover + "<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)


def build_dual_plan(inst, drawing, tree_mask, height=470):
    """Plan als kreuzungsfreie Zeichnung mit seinem Dualgraphen. tree_mask: gewählter Spannbaum (Basis): seine Leitungen blaugrün; die übrigen Leitungen sind genau
    die Spannbaum-Leitungen des Dualgraphen (orange gestrichelt)."""
    pos, dpos = drawing["pos"], drawing["dual_pos"]
    fig = go.Figure()
    xs, ys = [], []
    for e, (u, w, _) in enumerate(inst.edges):
        if not tree_mask >> e & 1:
            xs += [pos[u][0], pos[w][0], None]
            ys += [pos[u][1], pos[w][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=2), name="Leitung nicht im Baum", hoverinfo="skip"))
    xs, ys = [], []
    for e, (u, w, _) in enumerate(inst.edges):
        if tree_mask >> e & 1:
            xs += [pos[u][0], pos[w][0], None]
            ys += [pos[u][1], pos[w][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_TREE, width=6), name="Spannbaum (Basis)", hoverinfo="skip"))
    xs, ys, lx, ly = [], [], [], []
    for e, (u, w, _) in enumerate(inst.edges):
        f1, f2 = drawing["dual_edges"][e]
        mid = ((pos[u][0] + pos[w][0]) / 2, (pos[u][1] + pos[w][1]) / 2)
        pts = [dpos[f1], mid] if f1 == f2 else [dpos[f1], mid, dpos[f2]]
        if not tree_mask >> e & 1:
            xs += [p[0] for p in pts] + [None]
            ys += [p[1] for p in pts] + [None]
        else:
            lx += [p[0] for p in pts] + [None]
            ly += [p[1] for p in pts] + [None]
    fig.add_trace(go.Scatter(x=lx, y=ly, mode="lines", line=dict(color="rgba(217,95,2,0.35)", width=1.5, dash="dot"), name="Dualleitung (nicht im Dualbaum)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_CUT, width=4, dash="dash"), name="Spannbaum des Dualgraphen", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[pos[v][0] for v in range(inst.n)], y=[pos[v][1] for v in range(inst.n)], mode="markers+text", text=[inst.name(v) for v in range(inst.n)], textposition="top center",
        textfont=dict(size=14), marker=dict(size=16, color=[C.COLOR_DEPOT if v == 0 else C.COLOR_NODE for v in range(inst.n)], line=dict(color="white", width=1.5)),
        hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in dpos], y=[p[1] for p in dpos], mode="markers+text", text=[("F∞" if f == drawing["outer"] else f"F{f + 1}") for f in range(len(dpos))],
        textposition="bottom center", textfont=dict(size=13, color=C.COLOR_DUAL_NODE), marker=dict(size=14, symbol="square", color=C.COLOR_DUAL_NODE, line=dict(color="white", width=1.5)),
        hovertemplate="Fläche %{text}<extra></extra>", showlegend=False))
    allx = [p[0] for p in pos.values()] + [p[0] for p in dpos]
    ally = [p[1] for p in pos.values()] + [p[1] for p in dpos]
    fig.add_trace(go.Scatter(x=[min(allx) - 0.05, max(allx) + 0.05], y=[min(ally) - 0.08, max(ally) + 0.08], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_minor_plan(inst, e, op, height=360):
    """Der Graph nach dem Löschen (Leitung e entfernt) oder Zusammenziehen (die Endpunkte von e zu einem Standort in der Mitte der Leitung verschmolzen).
    Rückgabe: (Abbildung, Zahl der Schleifen, die beim Zusammenziehen entstehen und nicht gezeichnet werden)."""
    u, w, _ = inst.edges[e]
    pts = {v: inst.points[v] for v in range(inst.n)}
    new_of = {v: v for v in range(inst.n)}
    if op == "ziehen":
        pts[u] = ((pts[u][0] + pts[w][0]) / 2, (pts[u][1] + pts[w][1]) / 2)
        new_of[w] = u
        del pts[w]
    fig = go.Figure()
    seen: dict[tuple[int, int], int] = {}
    loops = 0
    for i, (a, b, _) in enumerate(inst.edges):
        if i == e:
            continue
        a2, b2 = new_of[a], new_of[b]
        if a2 == b2:
            loops += 1
            continue
        key = (min(a2, b2), max(a2, b2))
        k = seen.get(key, 0)
        seen[key] = k + 1
        dx, dy = pts[b2][0] - pts[a2][0], pts[b2][1] - pts[a2][1]
        norm = math.hypot(dx, dy) or 1.0
        off = 0.015 * k
        ox, oy = -dy / norm * off, dx / norm * off
        fig.add_trace(go.Scatter(x=[pts[a2][0] + ox, pts[b2][0] + ox], y=[pts[a2][1] + oy, pts[b2][1] + oy], mode="lines", line=dict(color=C.COLOR_TREE, width=3), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pts.values()], y=[p[1] for p in pts.values()], mode="markers+text",
        text=[inst.name(v) + ("=" + inst.name(w) if op == "ziehen" and v == u else "") for v in pts], textposition="top center", textfont=dict(size=14),
        marker=dict(size=16, color=[C.COLOR_REMOVED if (op == "ziehen" and v == u) else (C.COLOR_DEPOT if v == 0 else C.COLOR_NODE) for v in pts], line=dict(color="white", width=1.5)),
        hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.add_trace(go.Scatter(x=[-0.05, 1.05], y=[-0.05, 1.05], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    return _base(fig, height), loops
