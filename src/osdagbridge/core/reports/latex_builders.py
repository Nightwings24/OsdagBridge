# =============================================================================
# OsdagBridge Report — PyLaTeX building blocks
# =============================================================================
# All tables and figures of the report are produced through this module so
# that layout rules are applied uniformly:
#
#   ReportTable  – PyLaTeX ``LongTable`` wrapper.  Every table
#                  * repeats its caption + column-header rows on every page
#                    (\endfirsthead / \endhead),
#                  * prints "Continued on next page" at a page break (\endfoot),
#                  * fills the text width exactly (column widths are given as
#                    relative weights and resolved against \linewidth),
#                  * keeps multi-row groups (e.g. all rows of one girder)
#                    together with ``\\*`` so ``\multirow`` cells are never
#                    split across a page break,
#                  * reserves a page-bottom threshold with \needspace so a
#                    caption/header is never stranded at the foot of a page.
#   figure()      – PyLaTeX ``Figure`` (float [H]) with image or placeholder.
#
# Visual parameters come exclusively from styles.py.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Union

from pylatex import Command, Figure, LongTable, MultiColumn, MultiRow, NoEscape
from pylatex.base_classes import LatexObject

from osdagbridge.core.reports import styles as S

Cell = Union[str, LatexObject, None]

_ALIGN = {
    "L": r">{\raggedright\arraybackslash}",
    "C": r">{\centering\arraybackslash}",
    "R": r">{\raggedleft\arraybackslash}",
}


@dataclass(frozen=True)
class Col:
    """A table column: alignment ('L', 'C', 'R') and relative width weight."""
    align: str = "L"
    weight: float = 1.0
    valign: str = "m"   # 'm' = vertically centred, 'p' = top aligned


def _dumps(cell: Cell) -> str:
    if cell is None:
        return ""
    if isinstance(cell, LatexObject):
        return cell.dumps()
    return str(cell)


class _OsdagLongTable(LongTable):
    """LongTable with the missing ``\\endfirsthead`` marker."""

    _latex_name = "longtable"

    def end_table_first_header(self):
        self.append(Command("endfirsthead"))


class ReportTable:
    """Builder for a multi-page report table (PyLaTeX ``LongTable``).

    Parameters
    ----------
    caption : str
        Caption text (LaTeX).  Repeated as "<caption> (continued)" on
        subsequent pages.
    columns : sequence of Col
        Column definitions; widths are normalised to the full text width.
    header : sequence of cells, optional
        A single header row.  Use ``header_rows`` for multi-line headers.
    header_rows : list of raw LaTeX rows (without trailing ``\\\\``), optional
        An item may be ``(row, rule)`` to use e.g. ``\\cline{4-6}`` instead
        of ``\\hline`` below that row.
    numbered : bool
        ``False`` produces ``\\caption*`` (no table number).
    label : str, optional
    font : str, optional
        Override the table font size (defaults to ``styles.FONTS.table_size``).
    """

    def __init__(self, caption: str, columns: Sequence[Col],
                 header: Optional[Sequence[Cell]] = None,
                 header_rows: Optional[List[str]] = None,
                 numbered: bool = True, label: Optional[str] = None,
                 font: Optional[str] = None):
        self.caption = caption
        self.columns = list(columns)
        self.n = len(self.columns)
        self.numbered = numbered
        self.label = label
        self.font = font or S.FONTS.table_size
        if header_rows is None:
            header_rows = []
            if header is not None:
                header_rows.append(" & ".join(self._hdr(c) for c in header))
        self.header_rows = header_rows
        self._body: List[str] = []
        self._note: Optional[str] = None

    # ── column spec ──────────────────────────────────────────────────────
    def _spec(self) -> str:
        total = sum(c.weight for c in self.columns) or 1.0
        parts = []
        for c in self.columns:
            frac = c.weight / total
            parts.append(_ALIGN.get(c.align, _ALIGN["L"]) + c.valign + "{" + f"{frac:.4f}" + r"\osdagTW}")
        return "|" + "|".join(parts) + "|"

    @staticmethod
    def _hdr(cell: Cell) -> str:
        s = _dumps(cell)
        return (S.FONTS.table_header_style + " " + s) if s else ""

    # ── body rows ────────────────────────────────────────────────────────
    def add_row(self, cells: Sequence[Cell], rule: str = "hline", nobreak: bool = False):
        """Append one row. ``rule`` is 'hline', 'cline' (cline 2-n) or ''."""
        cells = list(cells)
        if len(cells) < self.n and not any(isinstance(c, MultiColumn) for c in cells):
            cells += [""] * (self.n - len(cells))
        end = r"\\*" if nobreak else r"\\"
        line = " & ".join(_dumps(c) for c in cells) + " " + end
        if rule == "hline":
            # \hline carries longtable's own breakpoint; a kept row uses a
            # full-width \cline instead so no break can occur below it.
            line += (r" \clineNB{1-" + str(self.n) + "}") if nobreak else r" \hline"
        elif rule == "cline":
            # \clineNB (styles.py) = \cline without the trailing breakpoint.
            line += (r" \clineNB{2-" if nobreak else r" \cline{2-") + str(self.n) + "}"
        self._body.append(line)
        return self

    def add_rows(self, rows: Iterable[Sequence[Cell]]):
        for r in rows:
            self.add_row(r)
        return self

    def add_group(self, label: Cell, rows: Sequence[Sequence[Cell]]):
        """Rows sharing a first-column label (rendered with \\multirow).

        The group is kept on one page (``\\\\*`` between its rows) when it is
        not longer than ``styles.TABLE.max_rows_kept_together``.
        """
        rows = [list(r) for r in rows]
        if not rows:
            return self
        keep = S.TABLE.keep_groups_together and len(rows) <= S.TABLE.max_rows_kept_together
        if len(rows) == 1:
            return self.add_row([label] + rows[0])
        first = MultiRow(len(rows), width="=", data=NoEscape(_dumps(label)))
        for i, r in enumerate(rows):
            last = i == len(rows) - 1
            self.add_row([first if i == 0 else ""] + r,
                         rule="hline" if last else "cline",
                         nobreak=keep and not last)
        return self

    def add_section(self, text: str):
        """Full-width shaded sub-heading row inside the table."""
        mc = MultiColumn(self.n, align="|l|", data=NoEscape(
            r"\cellcolor{" + S.TABLE.section_fill + "}" + S.FONTS.table_header_style + " " + text))
        # Keep the sub-heading with the row that follows it.
        self._body.append(mc.dumps() + r" \\* \clineNB{1-" + str(self.n) + "}")
        return self

    def add_message(self, label: Cell, text: str):
        """A label cell followed by one message spanning the remaining columns."""
        mc = MultiColumn(self.n - 1, align="c|", data=NoEscape(text))
        self._body.append(_dumps(label) + " & " + mc.dumps() + r" \\ \hline")
        return self

    def is_empty(self) -> bool:
        return not self._body

    # ── assembly ─────────────────────────────────────────────────────────
    def _header_block(self) -> List[str]:
        out = [NoEscape(r"\hline")]
        for row in self.header_rows:
            row, rule = (row if isinstance(row, tuple) else (row, r"\hline"))
            out.append(NoEscape(r"\rowcolor{" + S.TABLE.header_fill + "}" + row + r" \\ " + rule))
        return out

    def _cap(self, continued: bool) -> str:
        """Caption as a full-width first row of the table.

        longtable's own \\caption (through the caption package) is set in a
        fixed-width box that produced overfull boxes and narrow, indented
        captions; a spanning row always matches the table width exactly.
        """
        cap = self.caption
        if continued:
            cmd = r"\osdagTableCaptionCont" if self.numbered else r"\osdagTableCaptionStar"
            cap = cap + " " + S.TABLE.continued_caption
        else:
            cmd = r"\osdagTableCaption" if self.numbered else r"\osdagTableCaptionStar"
        lab = (r"\label{" + self.label + "}") if (self.label and not continued and self.numbered) else ""
        body = r"\raggedright " + cmd + "{" + cap + "}" + lab
        return (MultiColumn(self.n, align=NoEscape(r"@{}p{\linewidth}@{}"), data=NoEscape(body)).dumps()
                + r"\\[" + S.TABLE.caption_skip + "]")

    def build(self) -> LongTable:
        t = _OsdagLongTable(NoEscape(self._spec()))
        # First page head: caption + header
        t.append(NoEscape(self._cap(False)))
        for x in self._header_block():
            t.append(x)
        t.end_table_first_header()
        # Continuation head
        t.append(NoEscape(self._cap(True)))
        for x in self._header_block():
            t.append(x)
        t.end_table_header()
        # Foot on pages that continue
        t.append(MultiColumn(self.n, align="r", data=NoEscape(
            S.FONTS.note_size + r"\itshape\color{osdagMuted} " + S.TABLE.continued_footer)))
        t.append(NoEscape(r"\\"))
        t.end_table_footer()
        # An empty \endlastfoot is void and longtable would fall back to the
        # "continued" foot on the last page; a zero-height row keeps it non-void.
        # Row height in an array = \arraystretch*\baselineskip + \extrarowheight.
        t.append(NoEscape(r"\multicolumn{" + str(self.n)
                          + r"}{c}{}\\[-\dimexpr\arraystretch\baselineskip+\extrarowheight\relax]"))
        t.end_table_last_footer()
        body = list(self._body)
        if body and body[-1].endswith(r"\\ \hline"):
            # Never leave the table end alone on a new page: the last row is
            # glued to the table end (avoids an empty "continued" page).
            body[-1] = body[-1][:-len(r"\\ \hline")] + r"\\* \clineNB{1-" + str(self.n) + "}"
        for line in body:
            t.append(NoEscape(line))
        if self._note:
            # Note as a borderless, full-width last row glued to the table so
            # it can never be separated from the rows it explains.
            t.append(NoEscape(MultiColumn(self.n, align=NoEscape(r"@{}p{\linewidth}@{}"), data=NoEscape(
                r"\rule{0pt}{1.1em}" + S.FONTS.note_size + r"\itshape\color{osdagMuted}\raggedright "
                + self._note)).dumps() + r"\\"))
        return t

    def dumps(self, note: Optional[str] = None) -> str:
        """LaTeX for the table; ``note`` is printed directly below it."""
        if note:
            self._note = note
        avail = (r"\setlength{\osdagTW}{\dimexpr\linewidth-" + str(2 * self.n) + r"\tabcolsep-"
                 + str(self.n + 1) + r"\arrayrulewidth\relax}")
        # Unnumbered tables must not advance longtable's table counter.
        nonum = "" if self.numbered else r"\def\LTcaptype{}"
        return ("\n" + r"\Needspace{" + str(S.TABLE.min_lines_before_table) + r"\baselineskip}"
                + "\n" + r"\begingroup" + self.font + nonum + "\n" + avail + "\n"
                + self.build().dumps() + "\n" + r"\endgroup" + "\n")

    __str__ = dumps


# ─────────────────────────────────────────────────────────────────────────────
# Convenience builders
# ─────────────────────────────────────────────────────────────────────────────

def kv_table(caption: str, rows: Sequence[Sequence[Cell]], header=("Parameter", "Value"),
             weights=(0.42, 0.58), numbered: bool = True, label: Optional[str] = None,
             note: Optional[str] = None) -> str:
    """Two-column parameter/value table."""
    t = ReportTable(caption, [Col("L", weights[0]), Col("L", weights[1])],
                    header=header, numbered=numbered, label=label)
    t.add_rows(rows)
    return t.dumps(note=note)


def table_note(text: str) -> str:
    return S.note(text)


def _placeholder_box(caption: str, width: str) -> str:
    return (r"\fcolorbox{osdagMuted}{white}{\parbox[c][3.2cm][c]{" + width + r"}{\centering"
            r"\color{osdagMuted}\itshape [ Figure not available: " + caption + r" ]}}")


def figure(path: Optional[str], caption: str, width: Optional[str] = None,
           numbered: bool = True, label: Optional[str] = None,
           placeholder: bool = True) -> str:
    """PyLaTeX ``Figure`` with the image, or a framed placeholder box."""
    width = width or S.FIGURE.default_width
    if not path and not placeholder:
        return ""
    fig = Figure(position=S.FIGURE.placement)
    fig.append(NoEscape(r"\centering"))
    if path:
        fig.add_image(path.replace("\\", "/"), width=NoEscape(width))
    else:
        fig.append(NoEscape(_placeholder_box(caption, r"0.9\linewidth")))
    if numbered:
        fig.add_caption(NoEscape(caption))
    else:
        fig.append(NoEscape(r"\caption*{" + caption + "}"))
    if label:
        fig.append(Command("label", NoEscape(label)))
    return "\n" + fig.dumps() + "\n"


def figure_cell(path: Optional[str], caption: str, label: Optional[str] = None,
                width: Optional[str] = None) -> str:
    """One minipage of a side-by-side figure row."""
    width = width or S.FIGURE.cell_width
    if path:
        body = r"\includegraphics[width=\linewidth]{" + path.replace("\\", "/") + "}"
    else:
        body = _placeholder_box(caption, r"0.92\linewidth")
    lab = (r"\label{" + label + "}") if label else ""
    return (r"\begin{minipage}[t]{" + width + "}\n\\centering\n" + body + "\n"
            r"\captionof{figure}{" + caption + "}" + lab + "\n" + r"\end{minipage}")


def figure_row(cells: Sequence[str]) -> str:
    return ("\n" + r"\Needspace{12\baselineskip}" + "\n" + r"\noindent" + "\n"
            + "\n\\hfill\n".join(cells) + "\n" + r"\par\vspace{" + S.SPACING.after_note + "}\n")
