# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries
from osdagbridge.core.reports.latex_builders import Col, ReportTable, figure, kv_table
from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports import charts

if TYPE_CHECKING:
    pass

PASS, FAIL, DASH = S.PASS, S.FAIL, S.DASH

# Column layouts shared by the per-girder check tables (relative widths).
_CHECK_COLS = [Col("C", 0.75), Col("L", 1.9), Col("C", 1.55), Col("C", 1.35), Col("C", 0.8)]

# Element grouping of the overall summary (used for the UR charts, Sec. 5.5).
EL_GIRDER = "Steel Plate Girders"
EL_DECK = "Concrete Deck Slab"
EL_CB = "Cross Bracing"
EL_ED = "End Diaphragms"


def _girder_group(table, girder_entries, rows):
    """Add the same per-girder row block for every girder (multirow label)."""
    for lbl, _ in girder_entries:
        table.add_group(lbl, rows)
    return table


def ch5_design_checks(checks_data, bridge, asset_dir=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    asset_dir : str, optional
        Directory (inside the LaTeX build folder) where the utilisation-ratio
        charts of Section 5.5 are written.  Charts are skipped when None.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    od = bridge.output_dict

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = od.get("deck_report_values", {}) or {}

    def rv(key, unit=""):
        return _render_value(od, key, unit)

    # ── Girder section properties ────────────────────────────────────────
    t51 = ReportTable("Girder Section Properties (Final Optimized / User-selected)",
                      [Col("C", 0.7), Col("L", 2.6), Col("C", 1.3)],
                      header=["Girder", "Property", "Value"])
    _girder_group(t51, girder_entries, [
        (r"Depth, $D$ (mm)", rv(KEY_SD_TOTAL_DEPTH)),
        (r"Top Flange Width, $b_f$ (mm)", rv(KEY_SD_TOP_FLANGE_WIDTH)),
        (r"Bottom Flange Width, $b_f$ (mm)", rv(KEY_SD_BOTTOM_FLANGE_WIDTH)),
        (r"Top Flange Thickness, $t_f$ (mm)", rv(KEY_SD_TOP_FLANGE_THICKNESS)),
        (r"Bottom Flange Thickness, $t_f$ (mm)", rv(KEY_SD_BOTTOM_FLANGE_THICKNESS)),
        (r"Web Thickness, $t_w$ (mm)", rv(KEY_SD_WEB_THICKNESS)),
        (r"Gross Area, $A$ (cm$^2$)", rv(KEY_SD_SECTION_PROP_AREA)),
        (r"Moment of Inertia, $I_z$ (cm$^4$)", rv(KEY_SD_SECTION_PROP_IZ)),
        (r"Elastic Section Modulus, $Z_{ez}$ (cm$^3$)", rv(KEY_SD_SECTION_PROP_ZZ)),
        (r"Plastic Section Modulus, $Z_{pz}$ (cm$^3$)", rv(KEY_SD_SECTION_PROP_ZUZ)),
        (r"Effective Slab Width, $b_{eff}$ (mm)", rv(KEY_SD_EFFECTIVE_SLAB_WIDTH)),
        (r"Transformed Composite $I_z$ (cm$^4$)", rv(KEY_SD_COMPOSITE_IZ)),
        (r"Depth to Plastic Neutral Axis (mm)", rv(KEY_SD_PNA_DEPTH)),
    ])

    # ── Section classification ───────────────────────────────────────────
    t52 = ReportTable("Girder Section Classification",
                      [Col("C", 0.75), Col("L", 1.4), Col("C", 1.3), Col("C", 1.1), Col("C", 1.4)],
                      header=["Girder", "Element", "Slenderness Ratio", "Class Limit", "Classification"])
    _girder_group(t52, girder_entries, [
        ("Top Flange", rv(KEY_SD_FLANGE_SLENDERNESS), rv(KEY_SD_FLANGE_CLASS_LIMIT), rv(KEY_SD_CLASS_FLANGE)),
        ("Web", rv(KEY_SD_WEB_SLENDERNESS), rv(KEY_SD_WEB_CLASS_LIMIT), rv(KEY_SD_CLASS_WEB)),
        ("Overall Section", DASH, DASH, rv(KEY_SD_SECTION_CLASS)),
    ])

    # ── Moment capacity ──────────────────────────────────────────────────
    # Flexure UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _flex_ur = float(od.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = S.status(_flex_ur <= 1.0)
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = DASH
    t53 = ReportTable("Moment Capacity Check", _CHECK_COLS,
                      header=["Girder", "Parameter", "Formula", "Value", "Status"])
    _girder_group(t53, girder_entries, [
        (r"Applied Moment, $M_u$", "Governing LC (ULS)", rv(KEY_SD_MU_APPLIED, " kN-m"), DASH),
        (r"Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", rv(KEY_SD_MD_CAPACITY, " kN-m"), DASH),
        (r"Utilization Ratio, $M_u / M_d$", r"$M_u / M_d$", _flex_ur_str, _flex_status),
    ])

    # ── Shear capacity ───────────────────────────────────────────────────
    try:
        _shear_ur = float(od.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = S.status(_shear_ur <= 1.0)
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = DASH
    t54 = ReportTable("Shear Capacity Check", _CHECK_COLS,
                      header=["Girder", "Parameter", "Formula", "Value", "Status"])
    _girder_group(t54, girder_entries, [
        (r"Applied Shear, $V_u$", "Governing LC (ULS)", rv(KEY_SD_SHEAR_VU, " kN"), DASH),
        (r"Shear Area, $A_v$", r"$d_w \times t_w$", rv(KEY_SD_SHEAR_AV, " mm$^2$"), DASH),
        (r"Panel Aspect Ratio, $c/d$", DASH, rv(KEY_SD_PANEL_CD), DASH),
        (r"Shear Buckling Coefficient, $k_v$", "IS 800 Cl. 8.4.2.2", rv(KEY_SD_SHEAR_KV), DASH),
        (r"Web Slenderness, $\lambda_w$", r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$", rv(KEY_SD_SHEAR_LAMBDA_W), DASH),
        (r"Design Shear Stress, $\tau_b$", "IRC 22 Cl. 603.3.3.2", rv(KEY_SD_SHEAR_TAU_B, " MPa"), DASH),
        (r"Shear Buckling Resistance, $V_{cr}$", r"$A_v \times \tau_b$", rv(KEY_SD_SHEAR_VCR, " kN"), DASH),
        (r"Utilization Ratio, $V_u / V_d$", r"$V_u / V_d$", _shear_ur_str, _shear_status),
    ])

    # ── Interaction ──────────────────────────────────────────────────────
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return PASS
        elif ratio < 1.00:
            return S.WARN
        return FAIL
    try:
        _mv_ur = float(od.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = DASH
    # M-N interaction: None → no axial load → N/A.
    _mn_r  = od.get(KEY_SD_MN_RATIO)
    _mn_ax = od.get(KEY_SD_MN_AXIAL)
    _mn_mo = od.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55 = ReportTable("Interaction Checks (M-V and M-N)", _CHECK_COLS,
                      header=["Girder", "Check", "Condition", "Value", "Status"])
    _girder_group(t55, girder_entries, [
        ("High Shear Condition?", r"$V_u > 0.6\,V_d$", rv(KEY_SD_HIGH_SHEAR), DASH),
        (r"Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", rv(KEY_SD_MDV, " kN-m"), DASH),
        (r"Interaction Check: $M_u \leq M_{dv}$", DASH, _mv_ur_str, _mv_status),
        (r"Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$", _mn_cond, _mn_val, _mn_status),
    ])

    # ── LTB ──────────────────────────────────────────────────────────────
    try:
        _ltb_ur = float(od.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = DASH
    t56 = ReportTable("Lateral Torsional Buckling Check -- Construction Stage", _CHECK_COLS,
                      header=["Girder", "Parameter", "Formula", "Value", "Status"])
    _girder_group(t56, girder_entries, [
        (r"Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", rv(KEY_SD_LTB_MCR, " kN-m"), DASH),
        (r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$", r"$\sqrt{M_p / M_{cr}}$", rv(KEY_SD_LTB_LAMBDA), DASH),
        (r"LTB Reduction Factor, $\chi_{LT}$", "IS 800 Cl. 8.2.2", rv(KEY_SD_LTB_CHI), DASH),
        (r"LTB Resistance, $M_b$", r"$\chi_{LT}\,M_p / \gamma_{m0}$", rv(KEY_SD_LTB_MB, " kN-m"), DASH),
        (r"$M_u \leq M_b$", r"$M_u / M_b$", _ltb_ur_str, _ltb_status),
    ])

    # ── Stiffener design summary ─────────────────────────────────────────
    t57 = ReportTable("Stiffener Design Summary", [Col("C", 0.7), Col("L", 2.4), Col("L", 1.5)],
                      header=["Girder", "Parameter", "Value"])
    _girder_group(t57, girder_entries, [
        ("Shear Buckling Design Method", rv(KEY_SD_STIFF_METHOD)),
        ("Intermediate Stiffener Thickness (mm)", rv(KEY_SD_STIFF_INT_THICK)),
        ("Intermediate Stiffener Spacing (mm)", rv(KEY_SD_STIFF_INT_SPACING)),
        ("End Panel Stiffener Thickness (mm)", rv(KEY_SD_STIFF_END_THICK)),
        ("No. of End Panel Stiffeners", rv(KEY_SD_STIFF_END_COUNT)),
        ("Longitudinal Stiffeners", rv(KEY_SD_STIFF_LONG)),
    ])

    # ── Intermediate stiffener checks (IS 800 Cl. 8.7.1.2) ───────────────
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return S.status(float(provided) >= float(required))
        except (TypeError, ValueError):
            return DASH
    _iys_status = _ge_status(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))

    # Verification table — only has data when the user supplied stiffener sizes
    # (Design Type = Custom). In Optimized mode the stiffeners are auto-sized
    # (nothing to verify), so the whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    t58_block = ""
    if _is_custom:
        t58 = ReportTable("Intermediate Stiffener Checks", _CHECK_COLS,
                          header=["Girder", "Check", "Required", "Provided", "Status"])
        _girder_group(t58, girder_entries, [
            (r"Min. Moment of Inertia, $I_s$", rv(KEY_SD_IS_IYS_MIN, " mm$^4$"), rv(KEY_SD_IS_IYS_PROV, " mm$^4$"), _iys_status),
            (r"Buckling Resistance, $F_{qd} \geq F_q$", rv(KEY_SD_IS_FQ, " kN"), rv(KEY_SD_IS_FQD, " kN"), _fqd_status),
        ])
        t58_block = t58.dumps(note="IS 800 Cl. 8.7.1.2")

    # ── End panel (bearing) stiffener checks (IS 800 Cl. 8.7.3) ──────────
    # End panel == bearing stiffener for this bridge. Each resistance vs reaction R.
    # Resistances are 0 in guidance-only mode (optimized w/o outstand) → N/A.
    _bs_r = od.get(KEY_SD_BS_R)

    def _bs_check(resist_key):
        prov = od.get(resist_key)
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        return (f"{_bs_r} kN", f"{prov} kN", S.status(float(prov) >= float(_bs_r)))
    t59 = ReportTable("End Panel Stiffener Checks", _CHECK_COLS,
                      header=["Girder", "Check", "Required", "Provided", "Status"])
    _girder_group(t59, girder_entries, [
        ("Web Buckling Resistance", *_bs_check(KEY_SD_BS_FCDW_WB)),
        ("Local Crushing Resistance", *_bs_check(KEY_SD_BS_FCDW_LC)),
        ("Bearing Capacity", *_bs_check(KEY_SD_BS_FPSD)),
        ("Column Buckling Resistance", *_bs_check(KEY_SD_BS_FCD)),
    ])

    # ── Serviceability — deflection (IRC 22 Cl. 604.3.2) ─────────────────
    def _defl_status(actual, allowable):
        """PASS / FAIL for 'actual ≤ allowable'; DASH when values are missing."""
        try:
            return S.status(float(actual) <= float(allowable))
        except (TypeError, ValueError):
            return DASH

    def _dfmt(v, nd=2):
        """Format a numeric value to nd decimal places; empty string when None."""
        try:
            return f"{float(v):.{nd}f}"
        except (TypeError, ValueError):
            return ""

    # Mirror generate_results_values_builder.resolve_deflection_live/total_load
    # exactly so the report shows the same numbers as the Generate Results dialog:
    # allowable from span (L/800, L/600), actual from the per-girder values that
    # design() persists into output_dict under the canonical "G1".."Gn" suffix.
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm  = _span_m * 1000.0 / 800.0
        _allow_total_mm = _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str  = (f"L/800 = {_allow_live_mm:.1f} mm")  if _allow_live_mm  is not None else ""
    _allow_total_str = (f"L/600 = {_allow_total_mm:.1f} mm") if _allow_total_mm is not None else ""

    t510 = ReportTable("Serviceability -- Deflection Checks", _CHECK_COLS,
                       header=["Girder", "Check", "Allowable", "Actual (mm)", "Status"])
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _live_mm  = od.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _total_mm = od.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        t510.add_group(lbl, [
            (r"Live Load Deflection, $\delta_{LL}$", _allow_live_str, _dfmt(_live_mm, nd=3),
             _defl_status(_live_mm, _allow_live_mm)),
            (r"Total Load Deflection, $\delta_{total}$", _allow_total_str, _dfmt(_total_mm, nd=3),
             _defl_status(_total_mm, _allow_total_mm)),
        ])

    # ── SLS steel stress limitation (IRC 22 Cl. 604.3.1) ────────────────
    # Steel stress is a single envelope-SLS value (same for every girder);
    # allowable = 0.9·fy. Both live in output_dict["design_results"].
    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    _dr = od.get("design_results", {}) or {}
    _steel_sigma = _dr.get(KEY_SD_STRESS_STEEL)
    _steel_allow = _dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    t511 = ReportTable("Serviceability -- Maximum Stress Limitation", _CHECK_COLS,
                       header=["Girder", "Element", "Allowable Stress", "Actual Stress", "Status"])
    for lbl, _ in girder_entries:
        t511.add_row([lbl, r"Structural Steel ($0.9\,f_y$)", _mpa(_steel_allow), _mpa(_steel_sigma),
                      _defl_status(_steel_sigma, _steel_allow)])

    # ── Fatigue (IRC 22 Cl. 605) ─────────────────────────────────────────
    # One row per girder showing the GOVERNING fatigue check (worst of
    # normal/shear by DCR), from design_results["steeldesign.uls_per_girder"].
    _fat_cat = (_dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}
    t512 = ReportTable("Serviceability -- Fatigue Assessment",
                       [Col("C", 0.75), Col("C", 1.4), Col("C", 1.4), Col("C", 1.1), Col("C", 0.9)],
                       header=["Girder", r"Stress Range, $\Delta\sigma$", r"Fatigue Limit, $f_{fd}$",
                               "Utilization Ratio", "Status"])
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512.add_row([lbl, _mpa(_g.get("demand")), _mpa(_g.get("capacity")),
                      S.ur_text(_g.get("ur")), S.status_from_text(_g.get("status"))])

    # ── Per-girder design summary (controlling check) ───────────────────
    _pg_summary = _dr.get("per_girder", {}) or {}

    def _with_unit(value, unit):
        s = _dfmt(value, nd=2)
        if not s:
            return ""
        return (s + " " + _tex(unit)) if unit and str(unit) not in ("-", "–") else s

    t513 = ReportTable("Girder Design Summary (DCR / Utilization Ratio)",
                       [Col("C", 0.6), Col("L", 2.0), Col("L", 1.3), Col("C", 1.0), Col("C", 1.0),
                        Col("C", 0.6), Col("C", 0.75)],
                       header=["Girder", "Controlling LC / Combination", "Controlling Check",
                               "Demand", "Capacity", "UR", "Status"], font=r"\footnotesize")
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = _pg_summary.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            t513.add_row([lbl])
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        # Worst real load case for the controlling check id (skip Envelope pseudo-LCs)
        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""
        t513.add_row([lbl, _tex(str(ctrl_lc)), _tex(str(ctrl.get("name", ""))),
                      _with_unit(ctrl.get("demand"), ctrl.get("demand_unit")),
                      _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit")),
                      S.ur_text(ctrl.get("dcr"), nd=3), S.status_from_text(ctrl.get("status"))])

    # ── Shear connectors (bridge-level values in design_results) ────────
    def _kn(v):
        s = _dfmt(v, nd=2)
        return (s + " kN") if s else ""

    def _mm(v):
        s = _dfmt(v, nd=1)
        return (s + " mm") if s else ""

    t514 = ReportTable("Shear Connector Capacity",
                       [Col("L", 1.5), Col("C", 2.4), Col("C", 0.9), Col("L", 1.3)],
                       header=["Parameter", "Formula", "Value", "Reference"])
    t514.add_row([r"Design Resistance, $Q_u$",
                  r"\footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]"
                  r"$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[3pt]"
                  r"$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$}",
                  _kn(_dr.get(KEY_SD_SC_Qu_kN)), "IRC 22 Cl. 606.3.1 (Eq. 6.1)"])
    t514.add_row([r"Fatigue Shear Resistance, $Q_r$", r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
                  _kn(_dr.get(KEY_SD_SC_Qr_kN)), "IRC 22 Cl. 606.3.2 (Table 8)"])

    # Each spacing criterion passes when the provided spacing is no larger
    # than that criterion's required spacing (denser = safe).
    _sc_prov = _dr.get("stud_spacing_provided_mm")
    t515 = ReportTable("Shear Connector Spacing",
                       [Col("L", 1.6), Col("C", 1.3), Col("C", 1.3), Col("C", 0.8)],
                       header=["Criterion", "Governing Spacing", "Actual Spacing Provided", "Status"])
    for crit, req in (("ULS Shear (SL1)", _dr.get(KEY_SD_SC_SL1)),
                      ("Full Composite (SL2)", _dr.get(KEY_SD_SC_SL2)),
                      ("SLS Fatigue (SR)", _dr.get(KEY_SD_SC_SR)),
                      ("Max Spacing Limit (IRC 22)", _dr.get("stud_spacing_max_mm"))):
        t515.add_row([crit, _mm(req), _mm(_sc_prov), _defl_status(_sc_prov, req)])

    # Transverse shear (Cl.606.10) and detailing (Cl.606.6).
    def _cm2m(v):
        s = _dfmt(v, nd=2)
        return (s + r" cm$^2$/m") if s else ""

    def _knm(v):
        s = _dfmt(v, nd=2)
        return (s + " kN/m") if s else ""

    _ts_vl  = _dr.get(KEY_SD_TS_VL)
    _ts_vrd = _dr.get(KEY_SD_TS_VRD)
    _ts_ur_str = DASH
    try:
        if _ts_vl is not None and _ts_vrd is not None and float(_ts_vrd) > 0.0:
            _ts_ur_str = f"{float(_ts_vl) / float(_ts_vrd):.2f}"
    except (TypeError, ValueError):
        pass
    _ts_ok = _dr.get("transverse_shear_ok")
    _ts_status = S.status(_ts_ok) if _ts_ok is not None else DASH

    _ast_req = _dr.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which run
    # transversely between girders and cross the shear plane (see deck design).
    _dd = od.get("deck_design_results", {}) or {}
    try:
        _ast_prov = (float(_dd.get("rebar_bottom_area") or 0)
                     + float(_dd.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        _ast_prov = None
    _stud_d   = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    _d_lim    = _dr.get(KEY_SD_SC_D_LIMIT)
    _edge     = _dr.get(KEY_SD_SC_EDGE_DIST)
    _edge_req = _dr.get(KEY_SD_SC_REQ_EDGE_DIST)

    t516 = ReportTable("Transverse Shear and Detailing Checks",
                       [Col("L", 2.1), Col("L", 2.6), Col("C", 0.8)],
                       header=["Check", "Value", "Status"])
    t516.add_rows([
        (r"Longitudinal Shear per unit length, $V_L$", _knm(_ts_vl), DASH),
        (r"Transverse Shear Capacity of Slab, $V_{Rd}$", _knm(_ts_vrd), DASH),
        ("Transverse Shear Check", r"$V_L/V_{Rd}$ = " + _ts_ur_str, _ts_status),
        (r"Min. Transverse Reinforcement, $A_{st,min}$",
         "Required " + _cm2m(_ast_req) + ", Provided " + _cm2m(_ast_prov), _defl_status(_ast_req, _ast_prov)),
        (r"Stud Diameter $\leq 2\,t_f$", r"$d$ = " + _mm(_stud_d) + r" $\leq 2t_f$ = " + _mm(_d_lim),
         _defl_status(_stud_d, _d_lim)),
        ("Stud Edge Distance", "Provided " + _mm(_edge) + r" (req. $\geq$ " + _mm(_edge_req) + ")",
         _defl_status(_edge_req, _edge)),
    ])

    # ── Cross bracing tables ─────────────────────────────────────────────
    pairs = bridge.get_cb_pairs()
    t_cb_props = ReportTable("{el} --- Connection and Section Properties",
                             [Col("C", 0.8), Col("L", 1.0), Col("C", 0.9), Col("C", 1.1), Col("C", 0.9), Col("C", 0.9)],
                             header=["Panel", "Member", "Connection", "Section", r"$A_g$ (mm$^2$)", r"$r_{min}$ (mm)"])
    if not pairs:
        t_cb_props.add_row(["Between Girders", "Diagonal"])
    for pair in pairs:
        pair_id = pair.replace("-", "")
        rows = []
        for member, label in [("diagonal", "Diagonal"), ("chord", "Top / Bottom chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            if member == "diagonal":
                pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
            else:
                pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                if od.get(f"{pfx}.A") is None:
                    pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"
            area_cm2 = od.get(f"{pfx}.A")
            rv_cm = od.get(f"{pfx}.rv")
            rows.append((label, bridge.get_cb_connection(pair, member, ftype),
                         bridge.get_cb_section(pair, member, ftype),
                         f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else "",   # cm² → mm²
                         f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""))          # cm → mm
        t_cb_props.add_group(_tex(pair), rows)

    def _slender_status(slnd_str, limit):
        try:
            return S.status(float(slnd_str) <= limit)
        except (ValueError, TypeError):
            return ""
    t_cb_slend = ReportTable(r"{el} --- Slenderness Ratio Check (IS~800 Cl.~3.8)",
                             [Col("C", 0.8), Col("L", 1.0), Col("C", 0.6), Col("C", 1.1), Col("C", 0.8), Col("C", 1.2)],
                             header=["Panel", "Member", "Nature", r"Eff. Length $KL$ (mm)", r"$KL/r$", "Limit / Status"])
    if not pairs:
        t_cb_slend.add_row(["Between Girders", "Diagonal", "C", "", "", DASH])
    top_chord_enabled = od.get("member_properties.cross_bracing_details.top_chord", True)
    bottom_chord_enabled = od.get("member_properties.cross_bracing_details.bottom_chord", True)
    for pair in pairs:
        kl_diag = bridge.get_cb_effective_length("diagonal")
        kl_ch = bridge.get_cb_effective_length("chord")
        slnd_diag = bridge.get_cb_slenderness(pair, "diagonal")
        slnd_ch = bridge.get_cb_slenderness(pair, "chord")
        rows = [("Diagonal", "C", kl_diag, slnd_diag, "250 --- " + _slender_status(slnd_diag, 250))]
        if top_chord_enabled:
            rows.append(("Top chord", "C", kl_ch, slnd_ch, "250 --- " + _slender_status(slnd_ch, 250)))
        if bottom_chord_enabled:
            rows.append(("Bottom chord", "T", kl_ch, slnd_ch, "400 --- " + _slender_status(slnd_ch, 400)))
        t_cb_slend.add_group(_tex(pair), rows)

    t_cb_cap = ReportTable("{el} Design --- Capacity Summary",
                           [Col("C", 0.75), Col("L", 0.85), Col("C", 0.95), Col("C", 1.15), Col("C", 0.85),
                            Col("C", 0.85), Col("C", 0.55), Col("C", 0.75)],
                           header=["Panel", "Member", "Section", "Governing LC", "Demand (kN)",
                                   "Capacity (kN)", "UR", "Status"], font=r"\footnotesize")
    for pair in pairs:
        rows = []
        for member, label in [("diagonal", "Diagonal"), ("chord", "Chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            ur = bridge.get_cb_efficiency(pair, member, ftype)
            st = bridge.get_cb_status(pair, member, ftype)
            rows.append((label, bridge.get_cb_section(pair, member, ftype),
                         bridge.get_cb_gov_lc(pair, member, ftype), force_str,
                         bridge.get_cb_capacity(pair, member, ftype), S.ur_text(ur),
                         S.status_from_text(st) if st else ""))
        t_cb_cap.add_group(_tex(pair), rows)

    def _el(table, element, note=None):
        """The cross-bracing tables are re-used for the end diaphragm."""
        return table.dumps(note=note).replace("{el}", element)

    # ── Deck slab design value helpers (Tables 5.17 a/b/c/e/g) ────────────
    # Read from deck_rpt = output_dict["deck_report_values"] (common.KEY_DD_*).
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    def _dkv(key, default=0.0):
        """Raw float for status comparisons (0.0 if missing/non-numeric)."""
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        """Formatted display string; placeholder when deck design not run."""
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return _tex(v)

    def _dks(ok):
        """PASS/FAIL status; DASH when deck design not run."""
        return S.status(ok) if _dk_has else DASH

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        """Overhang value; 'N/A' when there is no overhang."""
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    # Governing crack width = max(bottom, top[, overhang]) vs the limit.
    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)]
    if _dk_oh:
        _dk_wks.append(_dkv(KEY_DD_WK_OH))
    _dk_gov_wk = max(_dk_wks)
    _dk_gov_wk_str = (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH)
    _dk_crack_ok = _dk_has and _dk_gov_wk <= _dkv(KEY_DD_WK_LIMIT)

    gdl, gll = _dkf(KEY_DD_GAMMA_DL, nd=2), _dkf(KEY_DD_GAMMA_LL, nd=2)
    deck_geo = kv_table("Deck Slab --- Loading and Geometry", [
        (r"Effective Span of Deck Slab, $l_{eff}$", _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + " mm (girder spacing, c/c)"),
        (r"Deck Thickness, $t_s$", _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + " mm"),
        ("Clear Cover (IRC 112 Cl. 15.2)", "Top " + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER)
         + " / Bottom " + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + " mm"),
        ("Concrete Grade (IRC 112 Cl. 6.4)", _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)
         + r" ($f_{ck}$ = " + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r" MPa, $f_{ctm}$ = "
         + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + " MPa)"),
        ("Reinforcement Grade (IRC 112 Cl. 6.2)", _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL)
         + r" ($f_y$ = " + _dkf(KEY_DD_FY, nd=0) + " MPa)"),
        (r"Dead Load per Unit Area, $w_{DL}$", _dkf(KEY_DD_WDL, nd=2) + r" kN/m$^2$ (slab self-weight)"),
        ("IRC 6 Wheel Load (Class A / 70R)", _dkf(KEY_DD_WHEEL_LOAD, nd=1) + " kN"),
        ("Tyre Contact Width (IRC 6 Annex~A)", _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + " mm (transverse)"),
        ("Impact Factor (IRC 6 Cl. 208.2)", _dkf(KEY_DD_IMPACT_FACTOR, nd=3)),
        ("Governing Live Load Case", _dkf(KEY_DD_VEHICLE)),
    ])

    deck_flex = ReportTable("Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)",
                            [Col("C", 0.85), Col("L", 1.6), Col("C", 1.4), Col("C", 1.15), Col("C", 0.7)],
                            header=["Location", "Parameter", "Formula / Reference", "Value", "Status"])
    deck_flex.add_group(r"\makecell{At Midspan\\(Sagging)}", [
        (r"Transverse BM (DL), $M_{T,DL}$", r"$w_{DL}\,l_{eff}^2/10$", _dkf(KEY_DD_M_DL) + " kN-m/m", DASH),
        (r"Transverse BM (LL), $M_{T,LL}$", "Effective width (IRC 112 B3.1)", _dkf(KEY_DD_M_LL) + " kN-m/m", DASH),
        (r"Total Design BM, $M_{u,sag}$", gdl + " DL + " + gll + " LL", _dkf(KEY_DD_M_ULS_SAG) + " kN-m/m", DASH),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", _dkf(KEY_DD_D_BOT, nd=1) + " mm", DASH),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", _dkf(KEY_DD_MU_BOT) + " kN-m/m",
         _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG))),
    ])
    deck_flex.add_group(r"\makecell{At Support\\(Hogging)}", [
        (r"Total Design BM, $M_{u,hog}$", gdl + " DL + " + gll + " LL (at support)", _dkf(KEY_DD_M_ULS_HOG) + " kN-m/m", DASH),
        (r"Required Top Steel, $A_{st,top}$", r"$M_u / (0.87\,f_y\,d)$", _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r" mm$^2$/m", DASH),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", _dkf(KEY_DD_MU_TOP) + " kN-m/m",
         _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG))),
    ])

    _four = [Col("L", 2.0), Col("C", 1.45), Col("C", 1.4), Col("C", 0.7)]
    deck_oh = ReportTable("Deck Slab --- Cantilever Overhang Flexure Check", _four,
                          header=["Parameter", "Formula", "Value", "Status"])
    deck_oh.add_rows([
        (r"Overhang Length, $l_{oh}$", DASH, _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m"), DASH),
        ("Crash Barrier Load Moment", "IRC 6 Cl. 206.4", _dkoh(KEY_DD_M_BARRIER, unit=" kN-m/m"), DASH),
        ("Dead Load Moment", r"$w_{DL}\,l_{oh}^2/2$ + railing", _dkoh(KEY_DD_M_DL_OH, unit=" kN-m/m"), DASH),
        ("Live Load Moment (eccentric wheel)", r"Wheel load $\times$ arm", _dkoh(KEY_DD_M_LL_OH, unit=" kN-m/m"), DASH),
        (r"Total Hogging Moment, $M_{u,oh}$", gdl + " DL + " + gll + " (LL + CB)", _dkoh(KEY_DD_M_ULS_OH, unit=" kN-m/m"), DASH),
        (r"Moment Capacity (top steel), $M_{Rd,oh}$", "IRC 112 Cl. 12.2", _dkoh(KEY_DD_MU_OH, unit=" kN-m/m"),
         _dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else DASH)),
    ])

    deck_punch = ReportTable(r"Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)", _four,
                             header=["Parameter", "Formula / Reference", "Value", "Status"])
    deck_punch.add_rows([
        (r"Design Wheel Load (ULS), $V_{Ed}$", r"$\gamma_Q\,(1+IF)\,P_w$", _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + " kN", DASH),
        ("Tyre Contact Area", r"$a \times b$ (IRC 6 Annex~A)",
         _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r" $\times$ " + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + " mm", DASH),
        (r"Loaded Area at mid-depth, $b_0$", r"$c_1 \times c_2$ (incl.\ WC dispersion)",
         _dkf(KEY_DD_PUNCH_C1, nd=0) + r" $\times$ " + _dkf(KEY_DD_PUNCH_C2, nd=0) + " mm", DASH),
        (r"Control Perimeter, $u_1$", r"$2(c_1+c_2) + 4\pi d$", _dkf(KEY_DD_PUNCH_U1, nd=0) + " mm", DASH),
        (r"Punching Shear Stress, $v_{Ed}$", r"$V_{Ed} / (u_1\,d)$", _dkf(KEY_DD_PUNCH_VED, nd=3) + " MPa", DASH),
        (r"Punching Resistance, $v_{Rd,c}$", r"IRC 112 Eq.\ 10.1", _dkf(KEY_DD_VRD_C_MPA, nd=3) + " MPa", DASH),
        ("Punching Shear Check", r"$v_{Ed} \leq v_{Rd,c}$",
         (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH),
         _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK)))),
    ])

    deck_crack = kv_table("Crack Width Check (Deck Slab)", [
        (r"Min. Reinforcement for Crack Control, $A_{s,min}$", _dkf(KEY_DD_AS_MIN, nd=0) + r" mm$^2$/m [IRC 112 Cl. 16.5.1]"),
        ("Provided Reinforcement (bottom)", r"$\phi$" + _dkf(KEY_DD_DIA_BOT, nd=0) + " @ " + _dkf(KEY_DD_SPC_BOT, nd=0)
         + " mm c/c (" + _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m)"),
        ("Max. Permissible Crack Width", _dkf(KEY_DD_WK_LIMIT, nd=2) + " mm"),
        (r"Calculated Crack Width, $w_k$ (governing)", _dk_gov_wk_str + " mm"),
        ("Crack Width Check", _dks(_dk_crack_ok)),
    ], header=("Parameter", "Value / Reference"), weights=(0.48, 0.52))

    deck_shear = ReportTable("One-Way (Beam) Shear Check (Deck Slab)", _four,
                             header=["Parameter", "Formula / Reference", "Value", "Status"])
    deck_shear.add_rows([
        (r"Design Shear per unit width, $V_{Ed}$", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$",
         _dkf(KEY_DD_SHEAR_VED) + " kN/m", DASH),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", _dkf(KEY_DD_D_BOT, nd=1) + " mm", DASH),
        (r"Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$",
         (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH), DASH),
        (r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$",
         (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH), DASH),
        (r"Shear resistance (no stirrups), $V_{Rd,c}$", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)", _dkf(KEY_DD_SHEAR_VRDC) + " kN/m", DASH),
        ("One-Way Shear Check", r"$V_{Ed} \leq V_{Rd,c}$",
         (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH),
         _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK)))),
    ])

    deck_rebar = ReportTable("Reinforcement Detailing Summary (Deck Slab)", _four,
                             header=["Parameter", "Required / Limit", "Provided", "Status"])
    deck_rebar.add_section(r"Main Reinforcement --- Bottom (Transverse)")
    deck_rebar.add_rows([
        (r"Required Area, $A_{st,req}$", _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r" mm$^2$/m", _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m",
         _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT))),
        (r"Bar Diameter $\times$ Spacing", r"$\phi \geq 10$ mm (IRC 112)",
         r"$\phi$" + _dkf(KEY_DD_DIA_BOT, nd=0) + " @ " + _dkf(KEY_DD_SPC_BOT, nd=0) + " mm c/c", DASH),
        (r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)", _dkf(KEY_DD_AS_MIN, nd=0) + r" mm$^2$/m",
         _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m", _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN))),
        (r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)", _dkf(KEY_DD_SPACING_MAX, nd=0) + " mm", _dkf(KEY_DD_SPC_BOT, nd=0) + " mm",
         _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX))),
    ])
    deck_rebar.add_section(r"Distribution Reinforcement --- Longitudinal")
    deck_rebar.add_row([r"Required Area, $A_{st,dist}$", r"$\geq 20\%$ of main steel", _dkf(KEY_DD_AS_LONG, nd=0) + r" mm$^2$/m",
                        _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN)))])
    deck_rebar.add_section(r"Top Reinforcement (Support / Cantilever Overhang)")
    deck_rebar.add_row([r"Required Area, $A_{st,top}$", _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r" mm$^2$/m",
                        _dkf(KEY_DD_AS_TOP, nd=0) + r" mm$^2$/m", _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP))])
    deck_rebar.add_section(r"Cover and Detailing")
    deck_rebar.add_row(["Clear Cover (IRC 112 Cl. 15.2)", r"$\geq$ " + _dkf(KEY_DD_MIN_COVER, nd=0) + " mm (Table 14.2)",
                        "Top " + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + " / Bottom "
                        + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + " mm",
                        _dks(bool(deck_rpt.get(KEY_DD_COVER_OK)))])

    # ── Overall Design Check Summary (Table 5.22) ────────────────────────
    # Three row families:
    #  (1) Girder DCR-engine checks: design_results["per_girder"] gives Demand,
    #      Capacity, UR and the governing LC; worst girder = highest DCR.
    #      SLS-conditional checks (e.g. deflection) fall back to per_lc.
    #  (2) Deck slab: Demand/Capacity from deck_report_values.
    #  (3) Cross bracing / end diaphragm: get_cb_* helpers (worst pair/member).
    _pg_522 = _pg_summary

    def _vu_522(v, unit):
        s = _dfmt(v, nd=2)
        if not s:
            return ""
        u = _tex((unit or "").strip())
        return (s + " " + u) if u else s

    def _lc_short(lc):
        # Full combination expression as-is (the per_lc key).
        return _tex(str(lc).strip())

    def _gov_lc_in_522(g, check_ids):
        gd = _pg_522.get(g) or {}
        best = None
        for _lc, _ld in (gd.get("per_lc") or {}).items():
            if str(_lc).lower().startswith("envelope"):
                continue
            for _chk in (_ld.get("checks") or []):
                if _chk.get("id") in check_ids:
                    _d = _chk.get("dcr") or 0.0
                    if best is None or _d > best[0]:
                        best = (_d, _lc)
        return _lc_short(best[1]) if best else DASH

    # Each summary-row builder returns (gov_lc, demand, capacity, ur_float).
    def _dcr_row(check_ids, fallback_unit=""):
        best = None  # (dcr, demand, capacity, dunit, cunit, g)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (_gov_lc_in_522(g, check_ids), _vu_522(dem, du) or DASH, _vu_522(cap, cu) or DASH, d)
        best = None  # (dcr, demand, capacity, lc)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), _lc)
        if best is None:
            return (DASH, DASH, DASH, None)
        d, dem, cap, _lc = best
        return (_lc_short(_lc), _vu_522(dem, fallback_unit) or DASH, _vu_522(cap, fallback_unit) or DASH, d)

    _cb_pairs_522 = pairs

    def _cb_row(force_type):
        best = None  # (ur, pair, member, capacity_str)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                cap = bridge.get_cb_capacity(pair, member, force_type)
                try:
                    ur = float(bridge.get_cb_efficiency(pair, member, force_type))
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return (DASH, DASH, DASH, None)
        ur, pair, member, cap = best
        gov = bridge.get_cb_gov_lc(pair, member, force_type) or DASH
        dem = f"{float(cap) * ur:.2f} kN" if cap else DASH
        return (gov, dem, (cap + " kN") if cap else DASH, ur)

    def _cb_slender_row():
        best = None  # (ratio, slend, limit)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                try:
                    sf = float(bridge.get_cb_slenderness(pair, member))
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                if best is None or sf / lim > best[0]:
                    best = (sf / lim, sf, lim)
        if best is None:
            return (DASH, DASH, DASH, None)
        ratio, sf, lim = best
        return (DASH, f"{sf:.1f}", f"{lim:.0f}", ratio)

    # Deck rows: designed for the IRC:6 Basic ULS combination.
    _deck_combo = (r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")) if _dk_has else DASH

    def _deck_row(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return (DASH, DASH, DASH, None)
        if is_oh and not _dk_oh:
            return (_deck_combo, "N/A", "N/A", None)
        dem, cap = _dkv(dem_key), _dkv(cap_key)
        return (_deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", (dem / cap) if cap > 0 else None)

    def _gov_sls_frequent():
        best = None  # (dcr, lc)
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"):
                continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower():
                    continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    _wk_lim = _dkv(KEY_DD_WK_LIMIT)
    _crack_cells = ((_gov_sls_frequent(), f"{_dk_gov_wk:.3f} mm", f"{_wk_lim:.3f} mm",
                     (_dk_gov_wk / _wk_lim) if _wk_lim > 0 else None)
                    if _dk_has else (DASH, DASH, DASH, None))

    # End diaphragm: when configured as Cross Bracing it is designed as bracing
    # members → mirror the cross-bracing axial rows. Rolled / welded beam end
    # diaphragms have no moment/shear design yet → message row.
    _ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            _ed_type = str(_v)
            break
    _ed_is_cb = "brac" in _ed_type.strip().lower()
    _ed_msg = r"Rolled / Welded section --- design to be added"

    def _trans_shear_row():
        """DCR engine check 16; falls back to the composite transverse-shear
        values (V_L vs V_Rd, Table 5.16) when the engine has no entry."""
        row = _dcr_row({16})
        if row[3] is not None:
            return row
        try:
            ur = float(_ts_vl) / float(_ts_vrd)
        except (TypeError, ValueError, ZeroDivisionError):
            ur = _dd.get("ur_composite_trans_shear")
        if ur is None:
            return row
        return ("Envelope ULS", _knm(_ts_vl) or DASH, _knm(_ts_vrd) or DASH, ur)

    # (element, label, cells-or-message)
    summary = [
        (EL_GIRDER, r"Girder --- Moment",             _dcr_row({1})),
        (EL_GIRDER, r"Girder --- Shear",              _dcr_row({2})),
        (EL_GIRDER, r"Girder --- LTB (constr.)",      _dcr_row({5})),
        (EL_GIRDER, r"Girder --- Deflection",         _dcr_row({13, 14}, fallback_unit="mm")),
        (EL_GIRDER, r"Girder --- Stress",             _dcr_row({11}, fallback_unit="MPa")),
        (EL_GIRDER, r"Girder --- Fatigue",            _dcr_row({8, 9}, fallback_unit="MPa")),
        (EL_DECK,   r"Transverse Shear (slab)",       _trans_shear_row()),
        (EL_DECK,   r"Crack Width (slab)",            _crack_cells),
        (EL_DECK,   r"Deck --- Flexure (sagging)",    _deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
        (EL_DECK,   r"Deck --- Flexure (hogging)",    _deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
        (EL_DECK,   r"Deck --- Cantilever Overhang",  _deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)),
        (EL_DECK,   r"Deck --- Punching Shear",       _deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
        (EL_DECK,   r"Deck --- One-Way Shear",        _deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")),
        (EL_CB,     r"Cross Bracing --- Compression", _cb_row("compression")),
        (EL_CB,     r"Cross Bracing --- Tension",     _cb_row("tension")),
        (EL_CB,     r"Cross Bracing --- Slenderness", _cb_slender_row()),
        (EL_ED,     r"End Diaphragm --- Moment",      _cb_row("compression") if _ed_is_cb else _ed_msg),
        (EL_ED,     r"End Diaphragm --- Shear",       _cb_row("tension") if _ed_is_cb else _ed_msg),
    ]

    t522 = ReportTable("Overall Design Check Summary --- All Members",
                       [Col("L", 1.55), Col("L", 2.1), Col("C", 0.95), Col("C", 0.95), Col("C", 0.55)],
                       header=["Member / Check", "Governing Load Combo", "Demand", "Capacity", "UR"])
    chart_rows = []
    current = None
    for element, label, cells in summary:
        if element != current:
            t522.add_section(element)
            current = element
        if isinstance(cells, str):
            t522.add_message(label, cells)
            chart_rows.append((element, label, None))
            continue
        gov, dem, cap, ur = cells
        t522.add_row([label, gov or DASH, dem or DASH, cap or DASH, S.ur_text(ur) or DASH])
        chart_rows.append((element, label, ur))

    ur_figs = ""
    if asset_dir:
        widths = [S.FIGURE.chart_width, S.FIGURE.medium_chart_width]
        for k, (path, caption) in enumerate(charts.utilization_charts(chart_rows, asset_dir)):
            ur_figs += figure(path, caption, width=widths[min(k, 1)], label=f"fig:ur-chart-{k + 1}")

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}
""" + t51.dumps() + t52.dumps(note="IS 800:2007 Table 2") \
        + t53.dumps(note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1") \
        + t54.dumps(note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2") \
        + t55.dumps(note="IRC 22 Cl. 603.3.3.3") \
        + t56.dumps(note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2") \
        + t57.dumps() + t58_block \
        + t59.dumps(note="IS 800 Cl. 8.4.2.2") \
        + t510.dumps(note="IRC 22 Cl. 604.3.2") \
        + t511.dumps() \
        + t512.dumps(note=r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). "
                                    r"Capacity reduction factor $\mu_r$ applied where plate thickness $>$ 25 mm.") \
        + t513.dumps(note=r"UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The "
                                    r"controlling check is the criterion with the highest UR for each girder, with "
                                    r"the real load case/combination that drives it.") \
        + t514.dumps() + t515.dumps(note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.") \
        + t516.dumps(note="IRC 22 Cl. 606.6, 606.10.") + r"""
\section{Deck Slab Design}
\label{sec:deck-design}

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.
""" + deck_geo + deck_flex.dumps(note="IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\\% of main "
                     "steel moment (IRC 21 Cl. 305.18).") \
        + deck_oh.dumps(note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.") \
        + deck_punch.dumps(note=r"Punching shear reinforcement not typically required for deck slabs "
                                          r"with $d \geq 200$ mm and adequate longitudinal reinforcement.") \
        + deck_crack + deck_shear.dumps(note="IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on "
                     "concrete and main reinforcement.") \
        + deck_rebar.dumps(note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy "
                                          "strength and detailing requirements.") + r"""
\section{Cross Bracing Design}
\label{sec:cross-bracing}

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination (DL + LL + WL).
""" + _el(t_cb_props, "Cross Bracing", note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.") \
        + _el(t_cb_slend, "Cross Bracing", note=r"Limit = 250 for compression members, 400 for tension "
                                                         r"members. $K = 1.0$ for members with both ends pinned.") \
        + _el(t_cb_cap, "Cross Bracing", note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). "
                                                      "OsdagBridge cross-bracing module used.") + r"""
\section{End Diaphragm Design}
\label{sec:end-diaphragm}

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.
""" + _el(t_cb_props, "End Diaphragm", note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.") \
        + _el(t_cb_slend, "End Diaphragm", note=r"Limit = 250 for compression members, 400 for tension "
                                                         r"members. $K = 1.0$ for members with both ends pinned.") \
        + _el(t_cb_cap, "End Diaphragm", note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). "
                                                      "OsdagBridge cross-bracing module used.") + r"""
\section{Overall Design Check Summary}
\label{sec:overall-summary}
""" + t522.dumps(note=
        r"UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks; values $> 1.0$ are shown in red. "
        r"The governing check for each component is highlighted in the individual design check sections above.") \
        + ur_figs
