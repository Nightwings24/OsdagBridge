# OsdagBridge Report Generator: Technical Changes

This document covers the refactoring of the PDF design report generator
(`src/osdagbridge/core/reports/`). Two reports from the same design are in this
folder:

| File | Produced by |
|------|-------------|
| `Report_Before.pdf` | Original `dev` code (commit `d74f56d`) |
| `Report_After.pdf`  | Refactored code on branch `feature/report-generator-refactor` |

Both use the same design: a 30 m span, 7.5 m carriageway, footpaths on both
sides, Mumbai, with the software default additional inputs. The reports were
generated headlessly with `tools/generate_sample_report.py`, which follows the
desktop *Design → Generate Report* path (see "Reproducing the reports" below).
The 3D OCC views need the live desktop viewer, so they show as placeholders in
both PDFs. The GUI fills them as before.

---

## 1. Summary of results

| Metric (same design) | Before | After |
|---|---|---|
| LaTeX errors during compilation | 139 (hidden by `nonstopmode`) | **0** |
| Overfull boxes (content running past margins) | many tables wider than the text block | **1** |
| Column headers repeated after a page break | no | **every table** (`\endfirsthead` / `\endhead`) |
| Multi-row girder groups split across pages (e.g. "G4" running into the footer) | yes | **no** (groups are kept together) |
| Live loads | one merged parameter/value table | **3 tables**: vehicle live loads, live-load parameters, footpath live load |
| UR charts in Section 5.5 | none | **2** (all checks, governing per element) |
| Material quantity charts in Chapter 7 | none | **2** (steel tonnage, concrete vs. reinforcement) |
| Hard-coded style values in chapter files | many (`\\[6pt]`, `\textcolor{red}`, `\setlength{\tabcolsep}`) | **none**; all come from `styles.py` |

---

## 2. Files changed

### New modules (`src/osdagbridge/core/reports/`)

| File | Purpose |
|---|---|
| `styles.py` | **Centralized style system (single source of truth).** Holds page geometry, fonts, color palette, table metrics, header/footer theme, figure widths, chart look and vertical spacing. It also generates the LaTeX preamble block from these settings. |
| `latex_builders.py` | **PyLaTeX layer.** `ReportTable` (a `pylatex.LongTable` subclass and builder), `kv_table`, `figure` (`pylatex.Figure`), `figure_cell` and `figure_row`. Every table and figure in the report goes through this module. |
| `charts.py` | matplotlib charts: `utilization_charts()` (Section 5.5) and `material_charts()` (Chapter 7). PNGs are written to the temporary LaTeX build folder. |

### Modified modules

| File | Change |
|---|---|
| `report_generator.py` | The preamble is built from `styles.py`. The title page and TOC are restyled. A `charts/` asset folder is created in the temporary build directory and passed to Chapters 5 and 7. Unicode symbols that come from backend strings (≤, ≥, λ, φ, …) are declared. The page counter continues after the title page, so the page number in the footer matches the PDF page. The LaTeX log is parsed (errors and overfull boxes are logged) and is kept next to the `.tex` file if no PDF is produced. |
| `executive_summary.py` | Tables and figures use the builders. "Key Design Outcomes" used to be hard-coded text ("Girder design pass…"). It is now a table driven by data (max UR and PASS/FAIL per component). |
| `chap1.py`, `chap2.py`, `chap4.py`, `chap6.py`, `chap8.py` | All raw `tabular`/`longtable`/`table[H]` strings are replaced by `ReportTable` / `kv_table` / `figure`. In Chapter 2, the cross bracing and end diaphragm tables had 6-column specs for 5 or 4 headers; this is fixed. The girder plate dimensions are converted back to mm, because `design()` stores them in metres and the old report printed "1.67 mm". Table 4.2 *Reactions at Supports* had three empty placeholder rows; it is now filled from the analysis results. |
| `chap3.py` | **Load tables rewritten (scope item 3).** See §5. |
| `chap5.py` | All 29 tables are rebuilt with `ReportTable` and per-girder groups. The overall summary (Table 5.29) is grouped by element and also feeds the UR charts. The *Transverse Shear (slab)* summary row was empty; it now falls back to the computed V<sub>L</sub>/V<sub>Rd</sub>. |
| `chap7.py` | Uses the builders and adds an **end diaphragm steel row** (the BOQ module has none; the weight comes from the end diaphragm member section mass at both supports). Adds a material summary table and the charts. |
| `report_utils.py` | `_render_value` limits floats to 3 decimals, so `12.149999999999999 m` is now shown as `12.15 m`. The unused figure helpers were removed (replaced by `latex_builders.figure`). |

### Outside the report directory (small, required fixes)

| File | Change |
|---|---|
| `core/utils/codes/irc6_2017.py` | `cl_211_2_braking_force()` raised `UnboundLocalError` for bridges with 2 lanes or fewer (`braking_force_2` was never set). Because of this, the old report always printed "Braking Load: N/A". The additional-lane term also overwrote itself instead of adding 5 % per lane. Both are fixed, and the docstring now states the real unit (N). |
| `environment.yml`, `pyproject.toml`, `requirements.txt`, `conda-recipe/meta.yaml` | Add the `pylatex` dependency. |
| `tests/unit/test_report_layout.py` | 11 new tests: repeated headers, group keeping, full-width columns, the page-bottom threshold, notes kept inside tables, the style block, no hard-coded styles in chapters, vehicle filtering, the braking fix, and chart output. |
| `tools/generate_sample_report.py` | Headless *Design → Generate Report* driver, used to produce the before/after PDFs (`--save-state` / `--from-state` regenerate the report in seconds). |

---

## 3. Key LaTeX / PyLaTeX changes

### 3.1 Repeated table headers (scope item 1)

`ReportTable.build()` builds a `pylatex.LongTable` in this order:

```
<caption row>  <header rows>  \endfirsthead
<caption row "(continued)">  <header rows>  \endhead
\multicolumn{n}{r}{Continued on next page}  \endfoot
<zero-height row>  \endlastfoot
<body rows>
```

* PyLaTeX's `LongTable` has `end_table_header()`, `end_table_footer()` and
  `end_table_last_footer()`, but nothing for `\endfirsthead`. The subclass
  `_OsdagLongTable` adds `end_table_first_header()`.
* An **empty** `\endlastfoot` is a void box, and longtable then reuses the
  "Continued on next page" foot on the last page. A zero-height row
  (`\\[-\dimexpr\arraystretch\baselineskip+\extrarowheight]`) keeps it non-void.
* The caption is a full-width spanning row instead of longtable's
  `\caption`. Through the caption package, `\caption` produced a 472 pt
  overfull box per table, and the captions were narrow and indented. The
  current longtable already steps the `table` counter (`\LTcaptype`), so the
  row only prints `\thetable`. Unnumbered tables set `\LTcaptype{}` locally.

### 3.2 Footer overlap and vertical spacing (scope item 2)

The "G4 runs into the footer" problem had three causes. Each one is fixed:

1. **Groups split across pages.** Each girder is a `\multirow` block whose rows
   were separated by `\cline`. `\cline` ends with
   `\noalign{\vskip-\arrayrulewidth}`. That glue follows a box, so it is a legal
   page break: the group broke at the page bottom, and the `\multirow` label
   was printed below the table or near the footer. `styles.py` now defines
   `\clineNB`, a patched copy of colortbl's `\@cline` with `\nobreak` before and
   after the glue. `ReportTable.add_group()` ends the rows with `\\*` +
   `\clineNB`, so a group (up to `TABLE.max_rows_kept_together` rows) always
   stays on one page. Sub-heading rows and the last row of a table are kept with
   the next row in the same way, so no empty "continued" page is produced.
2. **`\needspace` confused longtable.** The original preamble used
   `\BeforeBeginEnvironment{longtable}{\needspace{...}}`. `\needspace` leaves
   `\vskip+X \penalty \vskip-X` on the page. That makes `\pagetotal` too large,
   so longtable's start-of-table check decided the table did not fit and
   started with an empty page that had only a foot. The new code uses
   `\Needspace` (an exact `\pagegoal - \pagetotal` check) with a page-bottom
   threshold of `TABLE.min_lines_before_table` lines. `\section` and
   `\subsection` get the same reserve with `\pretocmd`, so headings stay with the
   content that follows them.
3. **Footer geometry.** The old footer drew the "* Software default value" note
   with `\vspace{-20pt}` above the footer rule, which put it in the text area,
   and `geometry` set only `margin=1in`. `PAGE` now sets `top`, `bottom`,
   `headheight`, `headsep` and `footskip` explicitly. The note is in a
   zero-height `\vbox` inside the footer box (`\osdagFootRule`), so it cannot
   collide with body text.

Other changes:

* Row heights come from `\arraystretch` and `\extrarowheight` instead of the
  `\\[6pt]` that was on almost every row.
* Table notes are a borderless last row of the table, so they never land alone
  on the next page.
* Column widths are given as relative weights. `ReportTable` sets
  `\osdagTW = \linewidth − 2n·\tabcolsep − (n+1)·\arrayrulewidth` for each
  table, and every column is `m{w·\osdagTW}`. Every table therefore fills the
  text width exactly and cannot overflow into the margin.

### 3.3 Charts (scope items 4 and 5)

* `charts.utilization_charts(rows, asset_dir)` reads the same rows that build
  Table 5.29. It produces:
  1. A bar chart of every check, colored by primary element (steel plate
     girders, concrete deck slab, cross bracing, end diaphragms). It has a red
     dashed line at UR = 1.0, failing bars (UR > 1.0) are hatched red, and
     checks that are not designed are marked `n/d`.
  2. The governing (maximum) UR for each element, with the governing check
     named on each bar.
* `charts.material_charts()` produces the structural steel tonnage chart
  (girders, cross bracing, end diaphragms) and a dual-axis chart of concrete
  volume (m³) and reinforcement weight (MT).
* PNGs are written to `<tempdir>/charts/` during generation. They are embedded
  with `pylatex.Figure` (Section 5.5) or as side-by-side `figure_cell`s
  (Chapter 7), and they are removed with the temporary directory.

---

## 4. Structure of the centralized style module (`styles.py`)

```
styles.py
├── PageGeometry   PAGE           paper, margins, headheight, headsep, footskip
├── Fonts          FONTS          base size, font packages (lmodern, microtype),
│                                 table / caption / note / header / footer sizes
├── Palette        PALETTE        Green, GreenDark, HeaderFill, SectionFill, Rule,
│                                 Text, Muted, Pass, Fail, Warn, Info  -> \definecolor{osdag*}
├── TableStyle     TABLE          tabcolsep, arraystretch, extrarowheight, rule width/color,
│                                 header & section fill, LTpre/LTpost, page-bottom threshold,
│                                 "continued" texts, group keeping
├── HeaderFooterTheme HEADER_FOOTER  rule color/width, text color, footer texts, SD note
├── FigureStyle    FIGURE         float placement, default / chart / half widths
├── ChartStyle     CHART          matplotlib sizes, fonts, element & material colors,
│                                 UR threshold value/color/style, fail hatch
├── Spacing        SPACING        vertical rhythm between blocks and headings
│
├── PASS / FAIL / WARN / NA / DASH, status(), status_from_text(), ur_text(), note()
├── latex_packages()        fontenc, inputenc, fonts, geometry   (from PAGE / FONTS)
├── latex_style_block()     colors, status macros, table metrics, \clineNB, captions,
│                           fancyhdr page styles                 (from all of the above)
├── latex_heading_block()   chapter/section formats, keep-with-next, TOC style
└── apply_matplotlib_style() rcParams                            (from CHART)
```

Chapter modules import only `styles` and `latex_builders`. Status cells use
`S.PASS`/`S.FAIL`, which become the `\statusPass`/`\statusFail` macros colored
from `PALETTE`. A unit test fails if a chapter file uses `\textcolor{red}`,
`\\[6pt]` or a local `\tabcolsep` again. Changing one value in `styles.py`
(for example `PALETTE.Green` or `TABLE.arraystretch`) restyles the whole
report and its charts.

---

## 5. Load table refactoring (Chapter 3)

The old merged "Live Loads (LL)" table had four rows: vehicles as one
comma-separated string; the impact factor as text; braking "N/A", caused by the
backend bug above; and the footpath load, which was empty with the IRC 6
default. It is replaced by:

**Table 3.3 Vehicle Live Loads (IRC 6 Cl. 204, 208, 211).** Columns follow the
example in the task: *Vehicle · Total Load (kN) · Impact Factor (1+IM) · Braking
Load {Considered? · Value (kN) · Eccentricity (m)}*.

* Only the vehicles **checked in Additional Inputs → Loading → Live Load** are
  listed (`KEY_LL_IRC_*`). Custom vehicles are appended.
* Total load comes from the `IRC6_2017` vehicle definitions (Class A, 70R
  wheeled/tracked, SV, fatigue). For Class AA and the 70R bogie there is no
  geometry function, so the nominal IRC 6 loads are used.
* Impact factor: Cl. 208.2 for Class A and fatigue, and Cl. 208.3 for wheeled or
  tracked 70R/AA. The backend `cl_208_3_impact_factor` chooses the
  tracked/wheeled branch from module constants, so it always returned the
  tracked value. The report now applies the right branch for each vehicle.
* Braking: considered for every vehicle except fatigue; for Class SV only when
  the *Braking Load → Class SV* option (`KEY_BL_IRC_CLASS_SV`) is checked.
  Value = 20 % of the vehicle load (Cl. 211.2). Eccentricity is
  `KEY_LL_ECCENTRICITY` (Cl. 211.3).

**Table 3.4 Live Load Parameters:** *Parameter · Value · Unit · Reference*. It
lists the number of design lanes (IRC 6 Table 6), the impact factors by vehicle
group, the total braking force for the lane count, the braking eccentricity,
and the centrifugal force. The centrifugal force is 0 kN for a straight
alignment (Cl. 212, R = ∞).

**Table 3.5 Footpath Live Load (IRC 6 Cl. 206):** footpath provision, number
of footpaths, width, pressure mode, design pressure (kN/m²) and equivalent line
load (kN/m). If no footpath is provided, a single row says the load is not
applicable.

All other Chapter 3 tables now use *Parameter · Value · Unit* columns. They also
use the computed fallbacks (V<sub>z</sub>, P<sub>z</sub>, Z, S<sub>a</sub>/g,
A<sub>h</sub>, A<sub>v</sub>, bridge temperatures) that the old code calculated
but never printed. Load combinations are grouped under ULS and SLS sub-headings.

---

## 6. Rationale for the main decisions

* **A PyLaTeX builder rather than a large PyLaTeX document tree.** The chapters
  mix a lot of math and conditional data logic. Wrapping only the structural
  parts (`LongTable`, `MultiRow`, `MultiColumn`, `Figure`) in PyLaTeX and
  passing cell contents as `NoEscape` keeps the engineering logic in each
  chapter unchanged and reviewable. The fragile layout code is now in one
  tested place.
* **Relative column weights.** Hard-coded `p{10cm}` columns were what made
  tables wider than the text block. Weights resolved against `\linewidth`
  adapt when `PAGE` margins change.
* **Fixing page breaks at the TeX level** (`\clineNB`, `\Needspace`, a
  non-void last foot), instead of adding manual `\newpage`/`\clearpage` calls:
  the report length changes with the number of girders and load cases, so
  manual breaks would go stale.
* **Charts as files in the temporary build directory.** The original design
  already compiles in a `TemporaryDirectory` and leaves nothing next to the
  PDF. The charts follow the same rule.
* **No engineering values were recomputed or changed** in the report layer.
  The exceptions are presentation of values that were already available (the
  end diaphragm steel weight from member masses, the transverse shear UR, and
  the girder dimension units). The only backend change is the braking-force
  crash.

---

## 7. Visual enhancements and polish

* Brand-colored chapter headings with a rule, section styles, and a TOC with
  dotted leaders.
* Shaded header rows, shaded full-width sub-heading rows (for example
  *Main Reinforcement*, *ULS / SLS*, element groups in Table 5.29), and thinner
  gray rules.
* Colored bold PASS / FAIL / WARN status macros, with UR > 1.0 highlighted in
  red in every table.
* Data-driven *Key Design Outcomes* table in the Executive Summary.
* *Material Quantity Summary* table with total structural steel.
* `lmodern` + `microtype` for better justification in narrow table columns.
* Framed "Figure not available" placeholders instead of bracketed text.
* Footer page numbers match the PDF page index ("Page n of N").
* Number formatting cleaned up (no `12.149999999999999`), and correct units on
  girder dimensions.
* LaTeX diagnostics are logged, and the `.log` file is kept when compilation
  fails.

---

## 8. Reproducing the reports

```bash
conda activate osdagbridge-env
# full analysis + report (about 3 min); also saves a state file for quick re-runs
python tools/generate_sample_report.py --out out --stem Report_After --save-state out/state.pkl
# report only, from the saved design state (a few seconds)
python tools/generate_sample_report.py --out out --stem Report_After --from-state out/state.pkl
# tests
python -m pytest tests/unit/test_report_layout.py -q
```

In the GUI: `python -m osdagbridge.desktop` → **Design** → **Generate Report**.
The public entry points (`build_report_payload`, `generate_report`) and the
dataclasses are unchanged.
