from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.reports.latex_builders import Col, ReportTable, figure, kv_table
from osdagbridge.core.reports import styles as S

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    demands = ReportTable(
        "Summary of Maximum Demands",
        [Col("L", 2.6)] + [Col("C", 1.25), Col("C", 0.9), Col("C", 0.9)] * 2 + [Col("C", 1.15)] * 2,
        header_rows=[
            (r"\textbf{Load Case /} & \multicolumn{3}{c|}{\textbf{Bending Moment}} & "
             r"\multicolumn{3}{c|}{\textbf{Shear Force}} & \multicolumn{2}{c|}{\textbf{Support Reaction}}",
             r"\cline{2-9}"),
            (r"\textbf{Combination} & \textbf{Max (kNm)} & \textbf{Girder} & \textbf{Loc. (m)} & "
             r"\textbf{Max (kN)} & \textbf{Girder} & \textbf{Loc. (m)} & \textbf{Left (kN)} & \textbf{Right (kN)}"),
        ],
        font=r"\footnotesize")
    reactions = ReportTable("Reactions at Supports", [Col("L", 2.4), Col("C", 1.0), Col("C", 1.0)],
                            header=["Load Case / Combination", "Left Support (kN)", "Right Support (kN)"])
    for lc in all_lcs:
        bm_d = lc_summary.get(lc) or {}
        rxn_d = rxn_summary.get(lc) or {}
        demands.add_row([
            _tex(lc), _fmt(bm_d.get('max_bm')), _tex(bm_d.get('bm_girder', '---')), _fmt(bm_d.get('bm_location')),
            _fmt(bm_d.get('max_sf')), _tex(bm_d.get('sf_girder', '---')), _fmt(bm_d.get('sf_location')),
            _fmt(rxn_d.get('left_kN')), _fmt(rxn_d.get('right_kN'))])
        if rxn_d:
            reactions.add_row([_tex(lc), _fmt(rxn_d.get('left_kN')), _fmt(rxn_d.get('right_kN'))])
    if demands.is_empty():
        demands.add_row(["---"] * 9)
    if reactions.is_empty():
        reactions.add_message("---", "No support reactions available")

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = S.status(_live_mm <= _allow_live_mm) if _live_mm is not None else S.DASH
    _total_status    = S.status(_total_mm <= _allow_total_mm) if _total_mm is not None else S.DASH

    defl = kv_table("Deflection Summary (Live Load \\& Total Load)", [
        (r"Deflection due to Live Load, $\delta_{LL}$", _live_str),
        (r"Allowable Live Load Deflection ($\Delta_{allow}$)", _allow_live_str),
        ("Live Load Deflection Check Status", _live_status),
        (r"Deflection due to Total Load, $\delta_{total}$", _total_str),
        (r"Allowable Total Deflection ($\Delta_{allow}$)", _allow_total_str),
        ("Total Load Deflection Check Status", _total_status),
    ])

    w = S.FIGURE.analysis_width
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.
""" + demands.dumps() + reactions.dumps() + defl \
        + figure(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=w) \
        + figure(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=w) \
        + figure(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=w)
