# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex
from osdagbridge.core.reports.latex_builders import Col, ReportTable, kv_table


def _kv(caption, rows, label=None, note=None):
    return kv_table(caption, rows, header=("Parameter", "Value"), weights=(0.42, 0.58), label=label, note=note)


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)

    location = _kv("Project Location", [
        ("Project Location", _tex(m.project_location)),
        ("Latitude / Longitude", _render_value(input_dict, 'latitude') + ', ' + _render_value(input_dict, 'longitude')),
        ("Seismic Zone (IRC 6)", _render_value(input_dict, 'seismic_zone')),
        ("Basic Wind Speed (IRC 6)", _render_value(input_dict, 'wind_speed', ' m/s')),
        ("Shade Temp. Max / Min (IRC 6)", _render_value(input_dict, 'shade_temp_max', '') + r" $^\circ$C / "
         + _render_value(input_dict, 'shade_temp_min', '') + r" $^\circ$C"),
    ], label="subsec:project-location")

    geometry = _kv("Bridge Geometry", [
        ("Type of Structure", _render_value(input_dict, KEY_STRUCTURE_TYPE)),
        ("Span", _render_value(input_dict, KEY_SPAN, ' m')),
        ("Carriageway Width", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')),
        ("Include Median", _render_value(input_dict, KEY_INCLUDE_MEDIAN)),
        ("Footpath", _render_value(input_dict, KEY_FOOTPATH)),
        ("Skew Angle", _render_value(input_dict, KEY_SKEW_ANGLE, r'$^\circ$')
         + r" (IRC 24 Cl. 504.8 limit: $\pm$15$^\circ$)"),
    ], label="subsec:bridge-geometry")

    material = _kv("Material Selection", [
        ("Girder Steel Grade (IS 2062)", _render_value(input_dict, KEY_GIRDER)),
        ("Cross Bracing Steel Grade", _render_value(input_dict, KEY_CROSS_BRACING)),
        ("End Diaphragm Steel Grade", _render_value(input_dict, KEY_END_DIAPHRAGM)),
        ("Concrete Deck Grade (IRC 22)", _render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)),
    ], label="subsec:material")

    typical = _kv("Typical Section Details", [
        ("Overall Bridge Width", _render_value(input_dict, KEY_TS_OVERALL_WIDTH, ' m')),
        ("No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)),
        ("Girder Spacing", _render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')),
        ("Deck Overhang Width", _render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')),
        ("Deck Thickness", _render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')),
        ("Footpath Width", _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m') + " (IRC 5 Cl. 104.3.6 min: 1.5 m)"),
        ("No. of Traffic Lanes", _render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT) + " (per IRC 5 Cl. 104.3.1)"),
    ])

    comp_rows = [
        ("Crash Barrier Type", _render_value(input_dict, KEY_CB_TYPE)),
        ("Crash Barrier Load", _render_value(input_dict, KEY_CB_LOAD, ' kN/m')),
    ]
    # Median row only shown when the user included a median
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        comp_rows.append(("Median Type", _render_value(input_dict, KEY_MD_TYPE)))
    comp_rows += [
        ("Railing Type", _render_value(input_dict, KEY_RL_TYPE)),
        ("Railing Load", _render_value(input_dict, KEY_RL_LOAD_VALUE, ' kN/m')),
        ("Wearing Course Material", _render_value(input_dict, KEY_WC_MATERIAL)),
        ("Wearing Course Thickness", _render_value(input_dict, KEY_WC_THICKNESS, ' mm')),
    ]
    components = _kv("Components Details", comp_rows)

    return r"""
\chapter{Input Parameters}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}
""" + location + geometry + material + r"""
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.
""" + typical + components + _girder_tables(input_dict, n_girders) + _bracing_tables(input_dict, n_girders) \
        + _shear_connector_table(input_dict, output_dict) + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]
    entries = [(lbl, mid, i) for i, (lbl, mid) in enumerate(girder_entries, start=1)]

    def v(key, i, unit=""):
        return _render_value(input_dict, f"{key}.G{i}.M1", unit)

    def mm(key, i):
        """Girder plate dimension in mm.

        design() converts these per-girder keys from mm to SI metres in place
        (PlateGirderBridge._convert_girder_dims_mm_to_m), and the report is
        always generated after design, so numeric values are metres here.
        """
        raw = input_dict.get(f"{key}.G{i}.M1")
        try:
            return f"{float(raw) * 1000.0:.0f} mm"
        except (TypeError, ValueError):
            return _tex(raw) if raw not in (None, "") else ""

    gen = ReportTable("Girder General Information",
                      [Col("C", 0.8), Col("C", 0.9), Col("L", 1.3), Col("L", 1.3), Col("L", 1.3)],
                      header=["Girder", "Member ID", "Design Mode", "Girder Type", "Girder Symmetry"])
    for lbl, mid, i in entries:
        gen.add_row([lbl, mid, _render_value(input_dict, KEY_DESIGN_MODE),
                     v(KEY_MP_GIRDER_TYPE, i), v(KEY_MP_GIRDER_SYMMETRY, i)])

    dims = ReportTable("Girder Section Dimensions",
                       [Col("C", 0.8), Col("C", 1.1), Col("C", 1.0), Col("C", 1.5), Col("C", 1.5)],
                       header=["Girder", "Total Depth, $D$", "Web, $t_w$",
                               r"Top Flange ($b_{tf}$, $t_{tf}$)", r"Bottom Flange ($b_{bf}$, $t_{bf}$)"])
    for lbl, _, i in entries:
        dims.add_row([lbl, mm(KEY_MP_GIRDER_DEPTH, i), mm(KEY_MP_GIRDER_WEB_THICKNESS, i),
                      mm(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, i) + ', ' + mm(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, i),
                      mm(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, i) + ', ' + mm(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, i)])

    rst = ReportTable("Girder Restraint and Stiffener Details",
                      [Col("C", 0.7), Col("L", 1.2), Col("L", 1.0), Col("L", 1.5), Col("L", 1.1), Col("L", 1.5)],
                      header=["Girder", "Torsional / Warping Restraint", "Web Philosophy",
                              "Intermediate Stiffeners", "Longitudinal Stiffeners", "Bearing Stiffener"])
    for lbl, _, i in entries:
        rst.add_row([
            lbl,
            v(KEY_MP_GIRDER_TORSIONAL_RESTRAINT, i) + ', ' + v(KEY_MP_GIRDER_WARPING_RESTRAINT, i),
            v(KEY_MP_GIRDER_WEB_TYPE, i),
            v(KEY_MP_STIFFENER_INTERMEDIATE, i) + r'; Spacing: ' + v(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, i, ' mm')
            + r'; Thickness: ' + v(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, i, ' mm'),
            v(KEY_MP_STIFFENER_LONGITUDINAL, i),
            r'No.: ' + v(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, i) + r'; Spacing: '
            + v(KEY_MP_STIFFENER_SPACING, i, ' mm') + r'; Thickness: '
            + v(KEY_MP_STIFFENER_BEARING_THICKNESS, i, ' mm'),
        ])
    return gen.dumps() + dims.dumps() + rst.dumps()


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    cb = ReportTable("Member Properties: Cross Bracing Details",
                     [Col("C", 1.0), Col("C", 1.1), Col("L", 1.1), Col("L", 1.3), Col("C", 0.8)],
                     header=["Location", "Member IDs", "Type of Bracing", "Bracing Section", "Spacing"])
    ed = ReportTable("Member Properties: End Diaphragm Details",
                     [Col("C", 1.0), Col("C", 1.1), Col("L", 1.1), Col("L", 1.3)],
                     header=["Location", "Member IDs", "Type", "Section"])
    for i in range(1, n):
        cbk = f"G{i}G{i+1}.B{i}M1"
        edk = f"G{i}G{i+1}.E{i}M1"
        cb.add_row([_render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.{cbk}"),
                    _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.{cbk}"),
                    _render_value(input_dict, f"{KEY_MP_CB_TYPE}.{cbk}"),
                    _render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.{cbk}"),
                    _render_value(input_dict, f"{KEY_MP_CB_SPACING}.{cbk}", ' m')])
        ed.add_row([_render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.{edk}"),
                    _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.{edk}"),
                    _render_value(input_dict, f"{KEY_MP_ED_TYPE}.{edk}"),
                    _render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.{edk}")])
    return cb.dumps() + ed.dumps()


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"\label{subsec:shear-connectors}" + _kv("Shear Connector Details", [
        ("Stud Diameter", _render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')),
        ("Stud Height", _render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')),
        ("Stud $f_y$", _render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')),
        ("Stud $f_u$", _render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')),
        ("No. of Studs per Section", _render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)),
    ])


def _safety_factors_table(input_dict):
    return r"\label{subsec:safety-factors}" + _kv("Partial Safety Factors", [
        (r"$\gamma_{M0}$ (Yielding / Buckling)", _render_value(input_dict, KEY_DO_GAMMA_M0)),
        (r"$\gamma_{M1}$ (Ultimate Stress)", _render_value(input_dict, KEY_DO_GAMMA_M1)),
        (r"$\gamma_C$ (Concrete, Basic)", _render_value(input_dict, KEY_DO_GAMMA_C_BASIC)),
        (r"$\gamma_s$ (Reinforcement)", _render_value(input_dict, KEY_DO_GAMMA_S)),
        (r"$\gamma_v$ (Shear Connectors)", _render_value(input_dict, KEY_DO_GAMMA_V)),
        (r"$\gamma_{fft}$ (Fatigue Load)", _render_value(input_dict, KEY_DO_GAMMA_FLT)),
        (r"$\gamma_{Mft}$ (Fatigue Strength)", _render_value(input_dict, KEY_DO_GAMMA_MF)),
    ], note="All values are per IRC 22 Table 1 unless user-modified.")
