# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.latex_builders import Col, ReportTable
from osdagbridge.core.reports import styles as S
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


# ─────────────────────────────────────────────────────────────────────────────
# Live-load data (presentation helpers — values come from IRC6_2017)
# ─────────────────────────────────────────────────────────────────────────────

# Vehicles offered in the UI (Additional Inputs → Loading → Live Load), in UI
# order.  'kind' selects the impact-factor rule of IRC 6 Cl. 208.
_IRC_VEHICLES = [
    (KEY_LL_IRC_CLASS_A,       "Class A",              "class_a"),
    (KEY_LL_IRC_AA_WHEELED,    "Class AA (Wheeled)",   "wheeled"),
    (KEY_LL_IRC_AA_TRACKED,    "Class AA (Tracked)",   "tracked"),
    (KEY_LL_IRC_70R_WHEELED,   "Class 70R (Wheeled)",  "wheeled"),
    (KEY_LL_IRC_70R_TRACKED,   "Class 70R (Tracked)",  "tracked"),
    (KEY_LL_IRC_70R_BOGIE,     "Class 70R (Bogie)",    "wheeled"),
    (KEY_LL_IRC_CLASS_SV,      "Class SV",             "sv"),
    (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue",        "fatigue"),
]

_N_PER_KN = 1000.0


def _vehicle_total_kN(key):
    """Gross vehicle load (kN) from the IRC6_2017 vehicle definitions.

    Class AA (Tracked / Wheeled) and the 70R bogie have no geometry function in
    IRC6_2017, so their nominal IRC 6 Cl. 204.1 loads (70 t, 40 t, 40 t) are used.
    """
    try:
        if key == KEY_LL_IRC_CLASS_A:
            return sum(IRC6_2017.cl_204_1_ClassA_vehicle()['wheel_loads']) / _N_PER_KN
        if key == KEY_LL_IRC_70R_WHEELED:
            return sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()['wheel_loads']) / _N_PER_KN
        if key == KEY_LL_IRC_70R_TRACKED:
            d = IRC6_2017.cl_204_1_Class70R_vehicle_track()
            length = max(d['x']) - min(d['x'])
            return d['wheel_loads_udl'] * length * len(d['z']) / _N_PER_KN
        if key == KEY_LL_IRC_CLASS_SV:
            return float(IRC6_2017.cl_204_5_1_special_vehicle()['total_load_kN'])
        if key == KEY_LL_IRC_CLASS_FATIGUE:
            return sum(IRC6_2017.cl_204_6_fatigue_load()['wheel_loads']) / _N_PER_KN
        return {KEY_LL_IRC_AA_TRACKED: 70.0, KEY_LL_IRC_AA_WHEELED: 40.0,
                KEY_LL_IRC_70R_BOGIE: 40.0}[key] * 9.81
    except Exception:
        return None


def _impact_factor(kind, span_m):
    """(1 + IM) per IRC 6 Cl. 208.2 / 208.3.

    Cl. 208.3 distinguishes tracked and wheeled vehicles; IRC6_2017's
    cl_208_3_impact_factor() selects that branch from module constants, so the
    tracked / wheeled rule is applied here explicitly (same expressions).
    """
    if span_m is None:
        return None
    if kind in ("class_a", "fatigue"):
        return 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)
    if kind == "sv":
        return None            # Class SV moves at crawl speed — no impact
    L = span_m
    if kind == "tracked":
        im = (0.25 if L < 5.0 else 0.10) if L <= 45.0 else 9.0 / (13.5 + 45.0)
    else:  # wheeled
        if L < 9.0:
            im = 0.25
        elif L <= 45.0:
            im = 0.25 if L < 23.0 else 9.0 / (13.5 + L)
        else:
            im = 9.0 / (13.5 + 45.0)
    return 1.0 + round(im, 3)


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _num(v, nd=2):
    f = _f(v)
    return f"{f:.{nd}f}" if f is not None else S.DASH


def _design_lanes(input_dict):
    lanes = _f(input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT))
    if lanes:
        return int(lanes)
    cw = _f(input_dict.get(KEY_CARRIAGEWAY_WIDTH))
    try:
        return IRC6_2017.table_6(cw) if cw else None
    except Exception:
        return None


def _vehicle_live_load_table(input_dict, span_m):
    ecc = _f(input_dict.get(KEY_LL_ECCENTRICITY))
    if ecc is None:
        ecc = IRC6_2017.cl_211_3_braking_force_location()['height_m']
    t = ReportTable(
        r"Vehicle Live Loads (IRC 6 Cl. 204, 208, 211)",
        [Col("L", 1.5), Col("C", 1.0), Col("C", 1.0), Col("C", 0.95), Col("C", 0.9), Col("C", 0.95)],
        header_rows=[
            (r"\textbf{Vehicle} & \textbf{Total Load} & \textbf{Impact Factor} & "
             r"\multicolumn{3}{c|}{\textbf{Braking Load (Cl. 211)}}", r"\cline{4-6}"),
            (r"& \textbf{(kN)} & \textbf{($1+IM$)} & \textbf{Considered?} & \textbf{Value (kN)} "
             r"& \textbf{Eccentricity (m)}"),
        ], label="tab:vehicle-ll")
    n = 0
    for key, name, kind in _IRC_VEHICLES:
        if not input_dict.get(key):
            continue
        n += 1
        total = _vehicle_total_kN(key)
        im = _impact_factor(kind, span_m)
        if kind == "sv":
            considered = bool(input_dict.get(KEY_BL_IRC_CLASS_SV))
        else:
            considered = kind != "fatigue"
        brake = (0.20 * total) if (considered and total) else None
        t.add_row([name,
                   _num(total, 1),
                   _num(im, 3) if im is not None else S.DASH,
                   "Yes" if considered else "No",
                   _num(brake, 1) if brake is not None else S.DASH,
                   _num(ecc, 2) if considered else S.DASH])
    for c in (input_dict.get(KEY_LL_CUSTOM_VEHICLES) or []):
        name = c.get('name') if isinstance(c, dict) else c
        if name:
            n += 1
            t.add_row([_tex(name) + " (custom)", S.DASH, S.DASH, "---", S.DASH, S.DASH])
    if n == 0:
        t.add_message("---", "No vehicle selected in the Loading tab")
    return t.dumps(note=
        r"Vehicles as selected in Additional Inputs $\rightarrow$ Loading $\rightarrow$ Live Load. "
        r"Braking value = 20\% of the vehicle load for the first train (IRC 6 Cl. 211.2), applied "
        r"at the eccentricity above the deck (Cl. 211.3). Class SV braking is considered only when "
        r"selected; the fatigue vehicle is used for fatigue checks only. Impact factor is not "
        r"applied to Class SV (crawl speed).")


def _live_load_parameter_table(input_dict, span_m):
    lanes = _design_lanes(input_dict)
    brake_total = None
    if lanes:
        try:
            brake_total = IRC6_2017.cl_211_2_braking_force(int(lanes)) / _N_PER_KN
        except Exception:
            brake_total = None
    ecc = _f(input_dict.get(KEY_LL_ECCENTRICITY))
    if ecc is None:
        ecc = IRC6_2017.cl_211_3_braking_force_location()['height_m']
    t = ReportTable("Live Load Parameters", label="tab:ll-params", columns=
                    [Col("L", 2.1), Col("C", 0.8), Col("C", 0.6), Col("L", 1.5)],
                    header=["Parameter", "Value", "Unit", "Reference"])
    t.add_row(["Number of design lanes", str(lanes) if lanes else S.DASH, "---", "IRC 6 Table 6"])
    t.add_row(["Impact factor, Class A / Fatigue ($1+IM$)",
               _num(_impact_factor("class_a", span_m), 3), "---", "IRC 6 Cl. 208.2"])
    t.add_row(["Impact factor, wheeled 70R / AA ($1+IM$)",
               _num(_impact_factor("wheeled", span_m), 3), "---", "IRC 6 Cl. 208.3"])
    t.add_row(["Impact factor, tracked 70R / AA ($1+IM$)",
               _num(_impact_factor("tracked", span_m), 3), "---", "IRC 6 Cl. 208.3"])
    t.add_row(["Total longitudinal braking force", _num(brake_total, 2), "kN", "IRC 6 Cl. 211.2"])
    t.add_row(["Braking force eccentricity above deck", _num(ecc, 2), "m", "IRC 6 Cl. 211.3"])
    t.add_row(["Centrifugal force", "0.00", "kN",
               r"IRC 6 Cl. 212 --- not applicable, straight alignment ($R = \infty$)"])
    return t.dumps()


def _footpath_live_load_table(input_dict, span_m):
    t = ReportTable("Footpath Live Load (IRC 6 Cl. 206)", label="tab:footpath-ll", columns=
                    [Col("L", 2.1), Col("C", 0.8), Col("C", 0.6), Col("L", 1.5)],
                    header=["Parameter", "Value", "Unit", "Reference"])
    fp = str(input_dict.get(KEY_FOOTPATH, "None") or "None").strip()
    n_fp = _f(input_dict.get(KEY_TS_NO_OF_FOOTPATHS))
    if n_fp is None:
        n_fp = 0 if fp in ("None", "") else (2 if "Both" in fp else 1)
    if fp in ("None", "") or not n_fp:
        t.add_message("Footpath", "No footpath provided --- footway live load not applicable")
        return t.dumps()

    width = _f(input_dict.get(KEY_TS_FOOTPATH_WIDTH))
    mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "") or "")
    custom = _f(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE))
    if mode.strip().lower() in ("as per irc 6", "as per irc6", "automatic", "") or custom is None:
        try:
            pressure = IRC6_2017.cl_206_1_footway_load()
        except Exception:
            pressure = None
        src = "IRC 6 Cl. 206.1"
    else:
        pressure = custom
        src = "User defined"
    line = pressure * width if (pressure is not None and width) else None
    t.add_row(["Footpath provision", _tex(fp), "---", "Basic inputs"])
    t.add_row(["Number of footpaths", str(int(n_fp)), "---", "Typical section"])
    t.add_row(["Footpath width", _num(width, 2), "m", "IRC 5 Cl. 104.3.6"])
    t.add_row(["Pressure definition", _tex(mode or "As per IRC 6"), "---", "Loading tab"])
    t.add_row(["Design footway pressure", _num(pressure, 3), r"kN/m$^2$", src])
    t.add_row(["Equivalent line load per footpath", _num(line, 2), "kN/m", "pressure $\\times$ width"])
    return t.dumps()


def _pvu(caption, rows):
    """Parameter / Value / Unit table."""
    t = ReportTable(caption, [Col("L", 2.2), Col("L", 1.8), Col("C", 0.7)],
                    header=["Parameter", "Value", "Unit"])
    t.add_rows(rows)
    return t.dumps()


def ch3_loads(input_dict):
    span = input_dict.get(KEY_SPAN)
    span_m = _f(span)

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass

    # Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, nd=4):
        return _num(v, nd) if v not in (None, "") else "N/A"

    # Temperature: computed effective bridge temperature range
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = None
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            tl_temp_min = _res.get('T_min', 0)
            tl_temp_max = _res.get('T_max', 0)
            _mean   = (tl_temp_max + tl_temp_min) / 2.0
            tl_rise     = tl_temp_max - _mean
            tl_fall     = _mean - tl_temp_min
    except Exception:
        pass

    def _rv(key, alt=None, nd=2):
        v = input_dict.get(key)
        if v in (None, ""):
            v = alt
        if v in (None, ""):
            return "N/A"
        f = _f(v)
        return f"{f:.{nd}f}" if f is not None else _tex(v)

    # --- Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    lc = ReportTable("Load Combinations", [Col("C", 0.9), Col("L", 4.0)],
                     header=["Combination ID", "Load Cases (partial safety factors)"])
    lc.add_section("Ultimate Limit State (IRC 6 Annex B, Table B.2)")
    for i, combo in enumerate(IRC6_2017.uls_load_combinations(), start=1):
        lc.add_row([f"ULS-{i:02d}", _fmt_factors(combo['factors'])])
    lc.add_section("Serviceability Limit State (IRC 6 Annex B, Table B.3)")
    for i, combo in enumerate(IRC6_2017.sls_load_combinations(), start=1):
        lc.add_row([f"SLS-{i:02d}", _fmt_factors(combo['factors'])])

    rl = _render_value(input_dict, KEY_RL_LOAD_VALUE)
    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\section{Permanent Loads}
""" + _pvu("Dead Load -- Self Weight", [
        ("Steel self-weight applied", _rv(KEY_MATERIAL_GIRDER_DENSITY), r"kN/m$^3$"),
        ("Concrete deck weight", _rv(KEY_MATERIAL_DECK_DENSITY), r"kN/m$^3$"),
        ("Self-weight factor", _rv(KEY_PL_SELF_WEIGHT_FACTOR), "---"),
    ]) + _pvu("Dead Load for Surfacing (DW)", [
        ("Wearing course", _render_value(input_dict, KEY_WC_MATERIAL) + r", "
         + _render_value(input_dict, KEY_WC_THICKNESS) + " mm thick", "---"),
        ("Additional SIDL (crash barrier, per barrier)", _rv(KEY_CB_LOAD), "kN/m"),
        ("Railing load", (rl + r"\sdstar{}") if rl else "N/A", "kN/m"),
    ]) + r"""
\section{Live Loads}
\label{sec:live-loads}

Vehicular and pedestrian live loads are reported separately: Table~\ref{tab:vehicle-ll} lists the IRC vehicles selected in the Loading tab of Additional Inputs, Table~\ref{tab:ll-params} the associated live-load parameters and Table~\ref{tab:footpath-ll} the footway loading.
""" + _vehicle_live_load_table(input_dict, span_m) + _live_load_parameter_table(input_dict, span_m) \
        + _footpath_live_load_table(input_dict, span_m) + r"""
\section{Environmental Loads}
""" + _pvu(r"Wind Load (WL) --- per IRC 6", [
        (r"Basic wind speed, $V_b$ (from project location)", _rv('wind_speed', input_dict.get(KEY_WL_BASIC_WIND_SPEED)), "m/s"),
        ("Terrain type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE) or "N/A", "---"),
        ("Average exposed height, $H$", _rv(KEY_WL_AVG_EXPOSED_HEIGHT), "m"),
        (r"Hourly mean wind speed, $V_z$", _rv(KEY_WL_HOURLY_MEAN_WIND, vz_val), "m/s"),
        (r"Hourly wind pressure, $P_z$", _rv(KEY_WL_HOURLY_WIND_PRESSURE, pz_val), r"N/m$^2$"),
        ("Transverse wind force", _rv(KEY_WL_TRANSVERSE_WIND_FORCE), "kN"),
        ("Longitudinal wind force", _rv(KEY_WL_LONGITUDINAL_WIND_FORCE), "kN"),
        ("Vertical wind force", _rv(KEY_WL_VERTICAL_WIND_FORCE), "kN"),
    ]) + _pvu(r"Earthquake Load (EL) --- per IRC 6", [
        ("Seismic zone (from project location)", _render_value(input_dict, 'seismic_zone') or "N/A", "---"),
        ("Zone factor, $Z$", _sl(sl_zone_factor, 2), "---"),
        ("Importance factor, $I$", _rv(KEY_SL_IMPORTANCE_FACTOR), "---"),
        ("Type of soil", _render_value(input_dict, KEY_SL_SOIL_TYPE) or "N/A", "---"),
        ("Spectral acceleration coefficient, $S_a/g$", _sl(sl_spectral, 3), "---"),
        ("Horizontal seismic coefficient, $A_h$", _sl(sl_ah), "---"),
        ("Vertical seismic coefficient, $A_v$", _sl(sl_av), "---"),
    ]) + _pvu(r"Temperature Load (TL) --- per IRC 6", [
        ("Maximum shade temperature", _rv('shade_temp_max'), r"$^\circ$C"),
        ("Minimum shade temperature", _rv('shade_temp_min'), r"$^\circ$C"),
        ("Effective bridge temperature range",
         _rv(KEY_TL_BRIDGE_TEMP_MIN, tl_temp_min) + " to " + _rv(KEY_TL_BRIDGE_TEMP_MAX, tl_temp_max), r"$^\circ$C"),
        ("Temperature rise / fall for design",
         "+" + _rv(KEY_TL_TEMP_RISE, tl_rise) + r" / \textminus{}" + _rv(KEY_TL_TEMP_FALL, tl_fall), r"$^\circ$C"),
    ]) + r"""
\section{Load Combinations}
""" + lc.dumps(note=
        "All IRC 6 load combinations are auto-generated by OsdagBridge. "
        "User-defined custom combinations, if any, are appended.")
