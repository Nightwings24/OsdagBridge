"""Headless OsdagBridge design + report generation.

Mirrors the desktop flow (Design -> Generate Report) without the GUI so the
report generator can be exercised reproducibly:

    python tools/generate_sample_report.py --out reports/ --stem Report_After

Material property keys normally primed by the input dock's material dialog
are filled from the same dialog class, run under an offscreen Qt platform.
"""
from __future__ import annotations

import argparse
import logging
import copy
import os
import pickle
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _bootstrap_databases() -> None:
    """Build the sqlite databases exactly like ``python -m osdagbridge.desktop`` does.

    Importing ``osdagbridge.desktop.__main__`` runs ``create_sqlite()`` and
    ``ensure_osdag_core_db()`` at module level (it does not start the GUI,
    which is guarded by ``if __name__ == '__main__'``).
    """
    import importlib
    importlib.import_module("osdagbridge.desktop.__main__")


def _prime_materials(input_dict: dict) -> None:
    """Replicates InputDock._prime_material_inputs() using the real dialog."""
    from PySide6.QtWidgets import QApplication
    from osdagbridge.core.utils.common import (
        KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC,
    )
    from osdagbridge.desktop.ui.dialogs.material_properties import MaterialPropertiesDialog

    _app = QApplication.instance() or QApplication(sys.argv[:1])
    for key in (KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC):
        selected = str(input_dict.get(key) or "").strip()
        if not selected:
            continue
        dlg = MaterialPropertiesDialog(read_only=True, selected_material=selected, member=key)
        input_dict.update(dlg.get_export_fields() or {})
        input_dict[key] = selected


def build_inputs(span: float, carriageway: float, footpath: str, skew: float,
                 state: str, district: str) -> dict:
    from osdagbridge.core.bridge_types.plate_girder.defaults import (
        BASIC_INPUT_DICT, solve_extend_basic_input_dict,
    )
    from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import get_weather
    from osdagbridge.core.utils.common import (
        KEY_PROJECT_LOCATION, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_FOOTPATH, KEY_SKEW_ANGLE,
    )

    inp = copy.deepcopy(BASIC_INPUT_DICT)
    inp[KEY_PROJECT_LOCATION] = {
        "method": "location_name",
        "data": {"state": state, "district": district},
        "weather_data": get_weather(state, district),
        "display_text": f"{district}, {state}",
        "show_display": True,
    }
    inp[KEY_SPAN] = span
    inp[KEY_CARRIAGEWAY_WIDTH] = carriageway
    inp[KEY_FOOTPATH] = footpath
    inp[KEY_SKEW_ANGLE] = skew
    _prime_materials(inp)
    solve_extend_basic_input_dict(inp)
    _sync_computed_values(inp)
    return inp


def _sync_computed_values(inp: dict) -> None:
    """Run the Additional-Inputs compute hooks (seismic / wind) like the GUI does."""
    try:
        from PySide6.QtWidgets import QApplication
        from osdagbridge.desktop.ui.dialogs.additional_input.additional_inputs import AdditionalInputs
        _app = QApplication.instance() or QApplication(sys.argv[:1])
        dlg = AdditionalInputs()
        for name in getattr(dlg, "_compute_functions", []):
            fn = getattr(dlg, name, None)
            if fn is None:
                continue
            res = fn(inp)
            if isinstance(res, dict):
                inp.update(res)
    except Exception as exc:  # pragma: no cover - best effort, GUI optional
        print(f"[generate_sample_report] compute sync skipped: {exc}")


def _capture_2d_figures(output_dict: dict) -> dict:
    """Offscreen equivalents of the 2D drawings OutputDock captures for the report.

    The 3D OCC views need the live desktop viewer and are therefore only
    available when the report is generated from the GUI.
    """
    figure_data = {}
    try:
        from PySide6.QtCore import QBuffer, QIODevice
        from PySide6.QtWidgets import QApplication
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.stiffener_cad_preview import StiffenerCadPreviewWidget
    except Exception as exc:  # pragma: no cover
        print(f"[generate_sample_report] 2D figure capture unavailable: {exc}")
        return figure_data
    _app = QApplication.instance() or QApplication(sys.argv[:1])

    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _grab(widget):
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        widget.grab().save(buf, "PNG")
        data = bytes(buf.data())
        buf.close()
        return data

    out = output_dict
    d = _f(out.get("steeldesign.details.total_depth")) or 0.0
    tfw = _f(out.get("steeldesign.details.top_flange_width")) or 0.0
    tft = _f(out.get("steeldesign.details.top_flange_thickness")) or 0.0
    bfw = _f(out.get("steeldesign.details.bottom_flange_width")) or tfw
    bft = _f(out.get("steeldesign.details.bottom_flange_thickness")) or tft
    wt = _f(out.get("steeldesign.details.web_thickness")) or 0.0
    st = str(out.get("steeldesign.details.section_type", "")).lower()
    if d and tfw and tft and wt:
        w = RolledSectionPreview()
        w.resize(700, 500)
        w.set_dimensions(depth_mm=d, flange_width_mm=tfw, bottom_flange_width_mm=bfw,
                         web_thickness_mm=wt, flange_thickness_mm=tft,
                         bottom_flange_thickness_mm=bft, show_welds=(st == "welded"))
        figure_data["section_preview"] = _grab(w)

    try:
        length_m = float(out.get("geometry.length") or 30.0)
    except (TypeError, ValueError):
        length_m = 30.0
    stiff = {
        "bearing_stiffeners_each_end": str(out.get("bearing_stiffeners_each_end", "2")),
        "bearing_spacing_mm": str(out.get("bearing_spacing_mm", "")),
        "intermediate_stiffener": str(out.get("intermediate_stiffener", "No")),
        "intermediate_spacing_mm": str(out.get("intermediate_spacing_mm", "NA")),
        "longitudinal_stiffener": str(out.get("longitudinal_stiffener", "No")),
    }
    dims = {"G1M1": {"depth_mm": d, "top_flange_thickness_mm": tft, "bottom_flange_thickness_mm": bft}}
    w = StiffenerCadPreviewWidget()
    w.resize(700, 300)
    w.set_data(segments=[{"id": "G1M1", "start": 0.0, "end": length_m, "length": length_m}],
               stiffener_by_member={"G1M1": stiff}, active_member_id="G1M1",
               section_dims_by_member=dims)
    figure_data["stiffener_preview"] = _grab(w)
    return figure_data


def _save_state(path: str, bridge) -> None:
    """Pickle everything generate_design_report() reads, so the report can be
    regenerated in seconds without re-running the analysis."""
    state = {
        "input_dict": dict(bridge.input_dict),
        "output_dict": dict(bridge.output_dict),
        "_lc_summary": getattr(bridge, "_lc_summary", None),
        "_reaction_summary": getattr(bridge, "_reaction_summary", None),
    }
    with open(path, "wb") as fh:
        pickle.dump(state, fh)


def _load_state(path: str):
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
    with open(path, "rb") as fh:
        state = pickle.load(fh)
    bridge = PlateGirderBridge()
    bridge.input_dict = state["input_dict"]
    bridge.output_dict = types.MappingProxyType(state["output_dict"])
    bridge._lc_summary = state["_lc_summary"]
    bridge._reaction_summary = state["_reaction_summary"]
    return bridge


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports")
    ap.add_argument("--stem", default="Report")
    ap.add_argument("--span", type=float, default=30.0)
    ap.add_argument("--carriageway", type=float, default=7.5)
    ap.add_argument("--footpath", default="Both Sides")
    ap.add_argument("--skew", type=float, default=0.0)
    ap.add_argument("--state", default="Maharashtra")
    ap.add_argument("--district", default="Mumbai")
    ap.add_argument("--save-state", default=None,
                    help="pickle design results here after the analysis")
    ap.add_argument("--from-state", default=None,
                    help="skip the analysis and build the report from a saved state")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    _bootstrap_databases()

    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
    from osdagbridge.core.reports.report_generator import (
        ReportMetadata, ReportOptions, ReportRequest,
    )

    if args.from_state:
        bridge = _load_state(args.from_state)
    else:
        inp = build_inputs(args.span, args.carriageway, args.footpath, args.skew,
                           args.state, args.district)
        bridge = PlateGirderBridge()
        bridge.set_input(inp)
        bridge.design()
        if args.save_state:
            _save_state(args.save_state, bridge)
            # Qt widget capture in the same process as the finished OpenSees /
            # OCC run can crash on teardown; build the report in a fresh process.
            import subprocess
            cmd = [sys.executable, os.path.abspath(__file__), "--out", args.out,
                   "--stem", args.stem, "--from-state", args.save_state]
            return subprocess.call(cmd)

    request = ReportRequest(
        metadata=ReportMetadata(
            project_name="Sample Plate Girder Bridge",
            project_location="",
            designer="OsdagBridge User",
            client="FOSSEE",
            company="IIT Bombay",
            job_number="OB-001",
            subtitle="Rev 0",
            reviewer="Reviewer",
        ),
        options=ReportOptions(
            sections=["loads", "analysis", "design_checks", "drawings", "quantities"],
            include_figures=True, include_toc=True, include_pdf=True,
        ),
        output_dir=os.path.abspath(args.out),
        file_stem=args.stem,
    )
    figures = _capture_2d_figures(dict(bridge.output_dict))
    result = bridge.generate_design_report(request, {"figure_data": figures})
    print("PDF:", result.pdf_path)
    print("TEX:", result.tex_path)
    return 0 if result.pdf_path else 1


if __name__ == "__main__":
    sys.exit(main())
