# =============================================================================
# OsdagBridge Report — Centralised Style System (single source of truth)
# =============================================================================
# Every visual / layout decision used by the report generator lives here:
#
#   * PAGE      – paper, margins, header/footer box sizes
#   * FONTS     – base size, font packages, table / caption / note sizes
#   * PALETTE   – brand + semantic colours (also exported to LaTeX \definecolor)
#   * TABLE     – padding, row height, rule widths, header shading, page-bottom
#                 threshold, "continued" texts
#   * HEADER_FOOTER – running header / footer theme
#   * FIGURE    – default figure widths and float placement
#   * CHART     – matplotlib look (sizes, colours, threshold line)
#   * SPACING   – vertical rhythm between blocks
#
# Chapter modules never hard-code any of these values: they import the
# constants / helpers below (directly or through latex_builders.py).  Changing
# a value here restyles the entire report.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Page geometry
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class PageGeometry:
    paper: str = "a4paper"
    top: str = "24mm"
    bottom: str = "26mm"
    left: str = "22mm"
    right: str = "22mm"
    headheight: str = "16pt"
    headsep: str = "7mm"
    # Distance from the last text baseline to the footer baseline.  Large
    # enough to hold the optional "* Software default value" note *and* the
    # footer rule without either overlapping body text.
    footskip: str = "15mm"

    def geometry_options(self) -> str:
        return (f"{self.paper}, top={self.top}, bottom={self.bottom}, "
                f"left={self.left}, right={self.right}, headheight={self.headheight}, "
                f"headsep={self.headsep}, footskip={self.footskip}")


# ─────────────────────────────────────────────────────────────────────────────
# Fonts
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Fonts:
    base_size: str = "11pt"
    document_class: str = "report"
    # T1 + Latin Modern give proper hyphenation/kerning; microtype reduces
    # overfull boxes in narrow table columns.
    packages: Tuple[str, ...] = ("lmodern", "microtype")
    line_stretch: float = 1.12
    table_size: str = r"\small"            # body text of every table
    table_header_style: str = r"\bfseries"
    caption_size: str = r"\normalsize"
    note_size: str = r"\footnotesize"
    footer_size: str = r"\footnotesize"
    header_size: str = r"\footnotesize"


# ─────────────────────────────────────────────────────────────────────────────
# Colour palette (HTML hex, no '#').  Names become LaTeX colours "osdag<Name>".
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Palette:
    Green: str = "91B014"          # Osdag brand green
    GreenDark: str = "5E7A0B"
    HeaderFill: str = "EEF4DC"     # table header row background
    SectionFill: str = "F6F8EF"    # full-width sub-heading rows inside tables
    Rule: str = "5A5A5A"           # table rules
    Text: str = "1E1E1E"
    Muted: str = "6B6B6B"
    Pass: str = "2E7D32"
    Fail: str = "C62828"
    Warn: str = "B26A00"
    Info: str = "1F5FA8"

    def as_dict(self) -> Dict[str, str]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    def hex(self, name: str) -> str:
        return "#" + getattr(self, name)


# ─────────────────────────────────────────────────────────────────────────────
# Tables
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class TableStyle:
    tabcolsep: str = "5pt"           # horizontal cell padding
    arraystretch: float = 1.30       # row height multiplier
    extrarowheight: str = "1.5pt"    # extra top padding in every row
    rule_width: str = "0.4pt"
    header_fill: str = "osdagHeaderFill"
    section_fill: str = "osdagSectionFill"
    rule_color: str = "osdagRule"
    lt_pre: str = "2pt"              # space above a longtable
    lt_post: str = "4pt"             # space below a longtable
    # Page-bottom threshold: if fewer than this many lines remain on the page
    # the table (caption + header + first rows) starts on the next page.
    min_lines_before_table: int = 13
    continued_caption: str = "(continued)"
    caption_skip: str = "2pt"        # gap between caption row and table
    continued_footer: str = "Continued on next page"
    # Keep multi-row groups (e.g. all rows of one girder) on one page.
    keep_groups_together: bool = True
    # Largest group (in rows) that is kept together; longer groups may break.
    max_rows_kept_together: int = 16


# ─────────────────────────────────────────────────────────────────────────────
# Running header / footer
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class HeaderFooterTheme:
    rule_color: str = "osdagGreen"
    rule_width: str = "0.8pt"
    text_color: str = "osdagMuted"
    footer_left: str = r"Osdag \textbar{} FOSSEE \textbar{} Indian Institute of Technology Bombay"
    footer_right: str = r"Page \thepage\ of \pageref{LastPage}"
    sd_note: str = r"* Software default value"


# ─────────────────────────────────────────────────────────────────────────────
# Figures & charts
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class FigureStyle:
    placement: str = "H"
    default_width: str = r"0.85\textwidth"
    chart_width: str = r"0.95\textwidth"
    medium_chart_width: str = r"0.62\textwidth"
    half_chart_width: str = r"0.48\textwidth"
    analysis_width: str = r"0.75\textwidth"
    cell_width: str = r"0.31\textwidth"


@dataclass(frozen=True)
class ChartStyle:
    dpi: int = 220
    figsize: Tuple[float, float] = (7.6, 4.4)        # full-width charts
    figsize_medium: Tuple[float, float] = (5.0, 3.5) # ~0.6 text width
    figsize_small: Tuple[float, float] = (3.9, 3.1)  # half text width
    font_family: str = "DejaVu Sans"
    font_size: float = 8.5
    title_size: float = 10.0
    grid_alpha: float = 0.35
    bar_edge: str = "#3A3A3A"
    # One colour per primary element (consistent across all charts).
    element_colors: Dict[str, str] = field(default_factory=lambda: {
        "Steel Plate Girders": "#5E7A0B",
        "Concrete Deck Slab": "#7E8C9A",
        "Cross Bracing": "#2F6DA3",
        "End Diaphragms": "#C07A1C",
    })
    material_colors: Dict[str, str] = field(default_factory=lambda: {
        "Girders": "#5E7A0B",
        "Cross Bracing": "#2F6DA3",
        "End Diaphragms": "#C07A1C",
        "Concrete": "#8C959E",
        "Reinforcement": "#9B3D2E",
    })
    threshold_value: float = 1.0
    threshold_color: str = "#D62728"
    threshold_style: str = "--"
    threshold_width: float = 1.6
    fail_hatch: str = "////"
    fail_edge: str = "#C62828"


# ─────────────────────────────────────────────────────────────────────────────
# Vertical spacing
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Spacing:
    before_table: str = "0.6em"
    after_note: str = "0.8em"
    before_figure: str = "0.4em"
    chapter_before: str = "0pt"
    chapter_after: str = "12pt"


PAGE = PageGeometry()
FONTS = Fonts()
PALETTE = Palette()
TABLE = TableStyle()
HEADER_FOOTER = HeaderFooterTheme()
FIGURE = FigureStyle()
CHART = ChartStyle()
SPACING = Spacing()


# ─────────────────────────────────────────────────────────────────────────────
# Semantic LaTeX snippets (defined as macros in the preamble below)
# ─────────────────────────────────────────────────────────────────────────────
PASS = r"\statusPass{}"
FAIL = r"\statusFail{}"
WARN = r"\statusWarn{}"
NA = r"\textcolor{osdagMuted}{N/A}"
DASH = r"---"


def status(ok) -> str:
    """PASS/FAIL macro for a boolean; DASH when undetermined (None)."""
    if ok is None:
        return DASH
    return PASS if ok else FAIL


def status_from_text(text) -> str:
    """Map a backend status string ('PASS', 'FAIL', 'WARN', ...) to a macro."""
    s = str(text or "").strip()
    u = s.upper()
    if not s:
        return DASH
    if "FAIL" in u:
        return FAIL
    if "WARN" in u:
        return WARN
    if "PASS" in u or u == "OK":
        return PASS
    return s


def ur_text(value, nd: int = 2) -> str:
    """Utilisation ratio formatted and coloured red when > threshold."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    s = f"{f:.{nd}f}"
    return (r"\textcolor{osdagFail}{\textbf{" + s + "}}") if f > CHART.threshold_value else s


def note(text: str) -> str:
    """A table / figure footnote in the house style (kept with the table)."""
    return (r"\par\nopagebreak\vspace{1pt}\noindent\parbox{\linewidth}{" + FONTS.note_size
            + r"\itshape\color{osdagMuted}\raggedright " + text
            + r"}\par\vspace{" + SPACING.after_note + "}\n")


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX preamble block generated from the settings above
# ─────────────────────────────────────────────────────────────────────────────
def latex_packages() -> str:
    pkgs = [
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        *[r"\usepackage{" + p + "}" for p in FONTS.packages],
        r"\usepackage[" + PAGE.geometry_options() + "]{geometry}",
    ]
    return "\n".join(pkgs)


def latex_style_block(project: str, job: str, date: str, version: str) -> str:
    """Colours, table metrics, captions, header/footer — all from this module."""
    colors = "\n".join(
        r"\definecolor{osdag" + name + "}{HTML}{" + hexv + "}"
        for name, hexv in PALETTE.as_dict().items()
    )
    hf = HEADER_FOOTER
    head_l = project + r" \textbar{} " + job
    head_r = date + r" \textbar{} " + version

    def _style(name: str, with_head: bool) -> str:
        head = (r"  \fancyhead[L]{\color{" + hf.text_color + "}" + FONTS.header_size + " " + head_l + "}\n"
                r"  \fancyhead[R]{\color{" + hf.text_color + "}" + FONTS.header_size + " " + head_r + "}\n"
                r"  \renewcommand{\headrule}{{\color{" + hf.rule_color + r"}\hrule width\headwidth height "
                + hf.rule_width + "}}\n") if with_head else r"  \renewcommand{\headrule}{}" + "\n"
        return (r"\fancypagestyle{" + name + "}{\n"
                r"  \fancyhf{}" + "\n" + head +
                r"  \fancyfoot[L]{\color{" + hf.text_color + "}" + FONTS.footer_size + " " + hf.footer_left + "}\n"
                r"  \fancyfoot[R]{\color{" + hf.text_color + "}" + FONTS.footer_size + " " + hf.footer_right + "}\n"
                r"  \renewcommand{\footrule}{\osdagFootRule}" + "\n"
                "}\n")

    return r"""
% ---------------------------------------------------------------------------
% Generated from osdagbridge/core/reports/styles.py — edit there, not here.
% ---------------------------------------------------------------------------
""" + colors + r"""

% Status macros used by every chapter
\newcommand{\statusPass}{\textcolor{osdagPass}{\textbf{PASS}}}
\newcommand{\statusFail}{\textcolor{osdagFail}{\textbf{FAIL}}}
\newcommand{\statusWarn}{\textcolor{osdagWarn}{\textbf{WARN}}}

% Table metrics
\setlength{\tabcolsep}{""" + TABLE.tabcolsep + r"""}
\renewcommand{\arraystretch}{""" + f"{TABLE.arraystretch:.2f}" + r"""}
\setlength{\extrarowheight}{""" + TABLE.extrarowheight + r"""}
\setlength{\arrayrulewidth}{""" + TABLE.rule_width + r"""}
\arrayrulecolor{""" + TABLE.rule_color + r"""}
\setlength{\LTpre}{""" + TABLE.lt_pre + r"""}
\setlength{\LTpost}{""" + TABLE.lt_post + r"""}
\setlength{\LTleft}{0pt}
\setlength{\LTright}{0pt}
\newlength{\osdagTW}   % usable width of the current table (set per table)

% \clineNB: \cline that forbids a page break below it.  The standard \cline
% ends with \noalign{\vskip-\arrayrulewidth}; that glue follows a box and is a
% legal page break, which split multi-row groups (and their \multirow label)
% across pages.  Placing \nobreak before the glue removes the breakpoint.
\makeatletter
\let\osdag@cline\@cline
\patchcmd{\osdag@cline}{\noalign{\vskip-\arrayrulewidth}}{\noalign{\nobreak\vskip-\arrayrulewidth\nobreak}}{}{\typeout{OsdagBridge: clineNB patch failed}}
\newcommand{\clineNB}[1]{\osdag@cline#1\@nil}
\makeatother

% Page-bottom threshold for floats / tables that are not longtables
\BeforeBeginEnvironment{table}{\Needspace{""" + str(TABLE.min_lines_before_table) + r"""\baselineskip}}

% Captions
\captionsetup{font=""" + {r"\normalsize": "normalsize", r"\small": "small"}.get(FONTS.caption_size, "normalsize") + r""",
  labelfont={bf,color=osdagGreenDark}, textfont=bf, justification=raggedright,
  singlelinecheck=false, format=plain, skip=4pt}

% Table captions are typeset as a full-width first row of the longtable (see
% latex_builders.ReportTable) and repeated as "(continued)".  longtable itself
% steps the table counter (\LTcaptype), so the caption only prints it.
\newcommand{\osdagCapLabel}[1]{{\color{osdagGreenDark}\bfseries #1:}}
\newcommand{\osdagTableCaption}[1]{\osdagCapLabel{Table~\thetable}~{\bfseries #1}}
\newcommand{\osdagTableCaptionCont}[1]{\osdagCapLabel{Table~\thetable}~{\bfseries #1}}
\newcommand{\osdagTableCaptionStar}[1]{{\bfseries #1}}

% Running header / footer.  The software-default note sits *inside* the footer
% box (above the rule) so it can never collide with body text.
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\newcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/after}{\global\boolfalse{hasSDonPage}}
\newcommand{\osdagFootRule}{%
  \ifbool{hasSDonPage}{%
    \vbox to 0pt{\vss\hbox to \headwidth{""" + FONTS.footer_size + r"""\itshape\color{osdagMuted}""" + hf.sd_note + r"""\hfil}\vspace{3pt}}%
  }{}%
  {\color{""" + hf.rule_color + r"""}\hrule width\headwidth height """ + hf.rule_width + r"""}\vspace{4pt}}
""" + _style("main", True) + _style("plain", True) + _style("firstpage", False) + r"""
\pagestyle{main}
\setstretch{""" + f"{FONTS.line_stretch:.2f}" + r"""}
"""


def latex_heading_block() -> str:
    """Chapter / section heading and table-of-contents styling."""
    sp = SPACING
    return r"""
% Headings
\titleformat{\chapter}[hang]
  {\normalfont\LARGE\bfseries\color{osdagGreenDark}}{\thechapter}{0.7em}{}
  [\vspace{2pt}{\color{osdagGreen}\titlerule[1.2pt]}]
\titlespacing*{\chapter}{0pt}{""" + sp.chapter_before + r"""}{""" + sp.chapter_after + r"""}
\titleformat{\section}
  {\normalfont\Large\bfseries\color{osdagText}}{\thesection}{0.8em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries\color{osdagText}}{\thesubsection}{0.8em}{}
\titlespacing*{\section}{0pt}{14pt plus 4pt minus 2pt}{6pt plus 2pt}
% Keep-with-next: a heading is never left at the foot of a page without at
% least the opening of the table / text that follows it.
\pretocmd{\section}{\Needspace{""" + str(TABLE.min_lines_before_table + 4) + r"""\baselineskip}}{}{}
\pretocmd{\subsection}{\Needspace{""" + str(TABLE.min_lines_before_table + 3) + r"""\baselineskip}}{}{}
\titlespacing*{\subsection}{0pt}{10pt plus 3pt minus 2pt}{4pt plus 2pt}

% Table of contents
\setcounter{tocdepth}{2}
\titlecontents{chapter}[1.8em]
  {\addvspace{6pt}\bfseries}
  {\contentslabel{1.8em}}
  {\hspace*{-1.8em}}
  {\hfill\contentspage}
\titlecontents{section}[4.2em]
  {}
  {\contentslabel{2.4em}}
  {\hspace*{-2.4em}}
  {\titlerule*[0.6pc]{.}\contentspage}
\titlecontents{subsection}[7.4em]
  {}
  {\contentslabel{3.2em}}
  {\hspace*{-3.2em}}
  {\titlerule*[0.6pc]{.}\contentspage}
\renewcommand{\contentsname}{Table of Contents}
"""


def apply_matplotlib_style():
    """Apply CHART settings to matplotlib (call before creating figures)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": CHART.font_family,
        "font.size": CHART.font_size,
        "axes.titlesize": CHART.title_size,
        "axes.titleweight": "bold",
        "axes.labelsize": CHART.font_size + 0.5,
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.alpha": CHART.grid_alpha,
        "grid.linestyle": ":",
        "legend.fontsize": CHART.font_size - 0.5,
        "legend.frameon": False,
        "savefig.dpi": CHART.dpi,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    })
    return plt
