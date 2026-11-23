"""Tests for the report generator layout layer (PyLaTeX builders, styles, charts)."""

import os
import re

import pytest

pytest.importorskip("pylatex")

from osdagbridge.core.reports import styles as S
from osdagbridge.core.reports.latex_builders import Col, ReportTable, figure, kv_table
from osdagbridge.core.utils import common as C


# ── ReportTable ───────────────────────────────────────────────────────────────

def _table():
    t = ReportTable("Caption", [Col("C", 1), Col("L", 2), Col("C", 1)], header=["G", "Property", "Value"])
    t.add_group("G1", [("a", "1"), ("b", "2"), ("c", "3")])
    t.add_row(["G2", "d", "4"])
    return t.dumps()


def test_longtable_repeats_header_on_every_page():
    tex = _table()
    assert r"\begin{longtable}" in tex
    first, rest = tex.split(r"\endfirsthead", 1)
    head, _ = rest.split(r"\endhead", 1)
    # caption + header both in the first head and in the continuation head
    assert r"\osdagTableCaption{Caption}" in first and r"\bfseries Property" in first
    assert r"\osdagTableCaptionCont{Caption (continued)}" in head and r"\bfseries Property" in head
    assert r"\endfoot" in tex and r"\endlastfoot" in tex
    assert S.TABLE.continued_footer in tex


def test_groups_are_kept_on_one_page():
    tex = _table()
    # every row of the group except the last ends with \\* and a non-breaking cline
    assert tex.count(r"\\* \clineNB{2-3}") == 2
    assert r"\multirow{3}{=}{G1}" in tex


def test_columns_fill_text_width():
    tex = _table()
    fracs = [float(x) for x in re.findall(r"\{([0-9.]+)\\osdagTW\}", tex)]
    assert abs(sum(fracs) - 1.0) < 1e-3
    assert r"\setlength{\osdagTW}{\dimexpr\linewidth-6\tabcolsep-4\arrayrulewidth\relax}" in tex


def test_page_bottom_threshold_and_unnumbered_tables():
    tex = kv_table("X", [("a", "b")], numbered=False)
    assert r"\Needspace{%d\baselineskip}" % S.TABLE.min_lines_before_table in tex
    assert r"\def\LTcaptype{}" in tex            # does not consume a table number


def test_note_is_part_of_table():
    t = ReportTable("C", [Col(), Col()], header=["a", "b"])
    t.add_row(["1", "2"])
    tex = t.dumps(note="Some note")
    assert tex.index("Some note") < tex.index(r"\end{longtable}")


def test_figure_placeholder_and_image():
    assert r"\includegraphics" in figure("x.png", "Cap")
    ph = figure(None, "Missing")
    assert "Figure not available" in ph and r"\includegraphics" not in ph


# ── styles: single source of truth ───────────────────────────────────────────

def test_style_block_generated_from_settings():
    block = S.latex_style_block("P", "J", "D", "R")
    assert r"\definecolor{osdagGreen}{HTML}{%s}" % S.PALETTE.Green in block
    assert r"\setlength{\tabcolsep}{%s}" % S.TABLE.tabcolsep in block
    assert r"\clineNB" in block
    assert S.PAGE.footskip in S.latex_packages()


def test_chapters_do_not_hardcode_status_colours_or_row_padding():
    here = os.path.dirname(S.__file__)
    for name in ("chap1.py", "chap2.py", "chap3.py", "chap4.py", "chap5.py", "chap7.py", "executive_summary.py"):
        src = open(os.path.join(here, name), encoding="utf-8").read()
        assert r"\textcolor{red}" not in src, name
        assert r"\\[6pt]" not in src, name
        assert r"\setlength{\tabcolsep}" not in src, name


# ── chapter 3: live-load tables follow the Loading tab selection ─────────────

def _loads_input(**selected):
    d = {C.KEY_SPAN: 30.0, C.KEY_CARRIAGEWAY_WIDTH: 7.5, C.KEY_FOOTPATH: "None"}
    for key in (C.KEY_LL_IRC_CLASS_A, C.KEY_LL_IRC_70R_WHEELED, C.KEY_LL_IRC_CLASS_SV):
        d[key] = False
    d.update(selected)
    return d


def test_vehicle_table_lists_only_selected_vehicles():
    from osdagbridge.core.reports.chap3 import ch3_loads
    tex = ch3_loads(_loads_input(**{C.KEY_LL_IRC_CLASS_A: True, C.KEY_LL_IRC_CLASS_SV: True,
                                    C.KEY_BL_IRC_CLASS_SV: False}))
    vehicle_table = tex.split("Vehicle Live Loads", 1)[1].split(r"\end{longtable}", 1)[0]
    assert "Class A &" in vehicle_table
    assert "Class SV &" in vehicle_table
    assert "70R (Wheeled)" not in vehicle_table
    # SV braking not opted in -> "No"
    sv_row = [l for l in vehicle_table.splitlines() if l.startswith("Class SV")][0]
    assert "& No &" in sv_row
    assert "Footpath Live Load" in tex and "No footpath provided" in tex
    assert "Live Load Parameters" in tex and "Centrifugal force" in tex


def test_braking_force_two_lanes_no_longer_crashes():
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    assert IRC6_2017.cl_211_2_braking_force(2) > 0
    assert IRC6_2017.cl_211_2_braking_force(4) > IRC6_2017.cl_211_2_braking_force(3)


# ── charts ────────────────────────────────────────────────────────────────────

def test_utilization_and_material_charts_are_written(tmp_path):
    pytest.importorskip("matplotlib")
    from osdagbridge.core.reports import charts
    rows = [("Steel Plate Girders", "Girder --- Moment", 0.6),
            ("Steel Plate Girders", "Girder --- Fatigue", 1.2),
            ("Concrete Deck Slab", "Deck --- Flexure (sagging)", 0.9),
            ("Cross Bracing", "Cross Bracing --- Tension", 0.2),
            ("End Diaphragms", "End Diaphragm --- Moment", None)]
    out = charts.utilization_charts(rows, str(tmp_path))
    assert len(out) == 2 and all(os.path.getsize(p) > 0 for p, _ in out)
    out = charts.material_charts([("Girders", 40.0), ("Cross Bracing", 1.0), ("End Diaphragms", None)],
                                 90.0, 10.0, str(tmp_path))
    assert len(out) == 2 and all(os.path.exists(p) for p, _ in out)
