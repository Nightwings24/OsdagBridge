# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Quantities come from boq.calculate_material_quantities() (already merged into
# input_dict by generate_report).  End diaphragm steel is not part of the BOQ
# module yet, so it is derived here from the end-diaphragm member properties.
# =============================================================================

import math

from osdagbridge.core.utils.common import KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS
from osdagbridge.core.reports.latex_builders import Col, ReportTable, figure_cell, figure_row
from osdagbridge.core.reports import charts
from osdagbridge.core.reports import styles as S

_ED = "member_properties.end_diaphragm_details"
_N_SUPPORTS = 2          # an end diaphragm line at each support


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _q(d, key):
    v = d.get(key, "N.A.")
    return S.DASH if v in (None, "", "N.A.") else str(v)


def end_diaphragm_quantity(input_dict, output_dict):
    """Steel in the end diaphragms (both supports).

    Returns dict(qty, length_m, wt_single, wt_total) or None when the members
    are not defined.  Mass per metre comes from the section database values
    stored on the member (kg/m); double-angle sections count twice.
    """
    try:
        n = int(_f(input_dict.get(KEY_TS_NO_OF_GIRDERS)) or 0)
    except (TypeError, ValueError):
        return None
    spacing = _f(input_dict.get(KEY_TS_GIRDER_SPACING))
    if n < 2 or not spacing:
        return None
    geom = ((output_dict or {}).get("crossbracing_forces_dict") or {}).get("geometry") or {}
    diag_len = _f(geom.get("diagonal_length_m"))

    members, length, weight = 0, 0.0, 0.0
    for i in range(1, n):
        sfx = f"G{i}G{i + 1}.E{i}M1"
        mass = _f(input_dict.get(f"{_ED}.section_properties.mass.{sfx}"))
        if not mass:
            continue
        etype = str(input_dict.get(f"{_ED}.type.{sfx}", "") or "")
        if "brac" in etype.lower():
            if "double" in str(input_dict.get(f"{_ED}.bracing_section.{sfx}", "")).lower():
                mass *= 2.0
            pieces = [diag_len or math.hypot(spacing, spacing * 0.5)] * 2       # two diagonals
            for chord in ("top_chord", "bottom_chord"):
                if str(input_dict.get(f"{_ED}.{chord}.{sfx}", "Yes")).strip().lower() == "yes":
                    pieces.append(spacing)
        else:                                                                   # rolled / welded beam
            pieces = [spacing]
        members += len(pieces) * _N_SUPPORTS
        length += sum(pieces) * _N_SUPPORTS
        weight += sum(pieces) * mass * _N_SUPPORTS / 1000.0                     # kg → t
    if not members:
        return None
    return {"qty": members, "length_m": length, "wt_total": weight,
            "wt_single": weight / members}


def ch7_quantities(input_dict, output_dict=None, asset_dir=None):
    q = input_dict
    t = ReportTable("Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
                    [Col("C", 0.45), Col("L", 1.6), Col("C", 2.2), Col("C", 0.75), Col("C", 0.8),
                     Col("C", 0.8), Col("C", 0.8)],
                    header=["S.N.", "Item Description", "Volume", "Qty.", r"Total Volume (m$^3$)",
                            "Weight (MT)", "Total Weight (MT)"],
                    font=r"\footnotesize", label="tab:bom")

    def row(sn, desc, pfx):
        t.add_row([sn, desc, _q(q, f"{pfx}_vol_formula"), _q(q, f"{pfx}_qty"), _q(q, f"{pfx}_vol_total"),
                   _q(q, f"{pfx}_wt_single"), _q(q, f"{pfx}_wt_total")])

    row("1", "Structural Steel (IS 2062) for Girders", "steel_girders")
    row("2(a)", "Cross Bracing - Top Chord", "bracing_top")
    row("2(b)", "Cross Bracing - Bottom Chord", "bracing_bot")
    row("2(c)", "Cross Bracing - Diagonal Chord", "bracing_diag")
    ed = end_diaphragm_quantity(input_dict, output_dict or {})
    if ed:
        t.add_row(["2(d)", "End Diaphragms (both supports)",
                   f"$\\Sigma L = {ed['length_m']:.2f}$ m", str(ed["qty"]),
                   f"{ed['wt_total'] / 7.85:.2f}", f"{ed['wt_single']:.4f}", f"{ed['wt_total']:.2f}"])
    else:
        t.add_row(["2(d)", "End Diaphragms (both supports)", S.DASH, S.DASH, S.DASH, S.DASH, S.DASH])
    row("3", "Concrete (M40) for Deck Slab", "concrete_deck")
    row("4", "Reinforcement Steel (Fe 500)", "rebar_deck")
    row("5", "Shear Stud Connectors", "shear_studs")
    row("6", "Crash Barrier", "crash_barrier")

    # ── Summary + charts ───────────────────────────────────────────────
    girders_t = _f(q.get("steel_girders_wt_total"))
    cb_parts = [_f(q.get(k)) for k in ("bracing_top_wt_total", "bracing_bot_wt_total", "bracing_diag_wt_total")]
    cb_t = sum(v for v in cb_parts if v is not None) if any(v is not None for v in cb_parts) else None
    ed_t = ed["wt_total"] if ed else None
    concrete = _f(q.get("concrete_deck_vol_total"))
    rebar = _f(q.get("rebar_deck_wt_total"))

    def fmt(v, nd=2):
        return f"{v:.{nd}f}" if v is not None else S.DASH

    steel_total = sum(v for v in (girders_t, cb_t, ed_t) if v is not None)
    summary = ReportTable("Material Quantity Summary", [Col("L", 2.4), Col("C", 1.0), Col("C", 0.7)],
                          header=["Material", "Quantity", "Unit"])
    summary.add_section("Structural steel (IS 2062)")
    summary.add_rows([
        ("Plate girders", fmt(girders_t), "MT"),
        ("Cross bracing (top + bottom chords + diagonals)", fmt(cb_t), "MT"),
        ("End diaphragms", fmt(ed_t), "MT"),
        (r"\textbf{Total structural steel}", r"\textbf{" + fmt(steel_total) + "}", "MT"),
    ])
    summary.add_section("Deck slab")
    summary.add_rows([
        ("Concrete volume", fmt(concrete), r"m$^3$"),
        ("Reinforcement steel", fmt(rebar), "MT"),
    ])

    figs = ""
    if asset_dir:
        cells = [figure_cell(path, caption, label="fig:material-" + str(k + 1), width=S.FIGURE.half_chart_width)
                 for k, (path, caption) in enumerate(charts.material_charts(
                     [("Girders", girders_t), ("Cross Bracing", cb_t), ("End Diaphragms", ed_t)],
                     concrete, rebar, asset_dir))]
        if cells:
            figs = r"\section*{Material Quantity Charts}" + "\n" + figure_row(cells)

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

The bill of materials below is derived from the final member sizes. Steel weights use a density of 7.85 t/m$^3$; end diaphragm weights use the section mass per metre of the selected members at both supports.
""" + t.dumps() + summary.dumps() + figs
