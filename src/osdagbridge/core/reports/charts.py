# =============================================================================
# OsdagBridge Report — data-visualisation charts (matplotlib → PNG)
# =============================================================================
# Charts are written into the LaTeX build folder (a TemporaryDirectory created
# by generate_report) and embedded with PyLaTeX ``Figure`` objects, so nothing
# is left on disk after the PDF is produced.  Look & feel: styles.CHART.
# =============================================================================

from __future__ import annotations

import os
import re
from typing import List, Optional, Sequence, Tuple

from osdagbridge.core.reports import styles as S

ChartRow = Tuple[str, str, Optional[float]]   # (element, check label, UR or None)

_PREFIXES = ("Girder --- ", "Deck --- ", "Cross Bracing --- ", "End Diaphragm --- ")


def _plain(label: str) -> str:
    """LaTeX label → plain chart text."""
    s = label
    for p in _PREFIXES:
        if s.startswith(p):
            s = s[len(p):]
    s = s.replace("---", "–").replace("--", "–").replace("~", " ")
    s = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", s)
    return s.replace("\\", "").strip()


def _save(fig, asset_dir: str, name: str) -> str:
    os.makedirs(asset_dir, exist_ok=True)
    path = os.path.join(asset_dir, name)
    fig.savefig(path)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path.replace("\\", "/")


def _threshold(ax, xmax):
    c = S.CHART
    ax.axhline(c.threshold_value, color=c.threshold_color, linestyle=c.threshold_style,
               linewidth=c.threshold_width, zorder=4, label=f"UR = {c.threshold_value:.1f} (limit)")


def _bar_style(ur):
    c = S.CHART
    if ur is not None and ur > c.threshold_value:
        return dict(hatch=c.fail_hatch, edgecolor=c.fail_edge, linewidth=1.2)
    return dict(edgecolor=c.bar_edge, linewidth=0.6)


def utilization_charts(rows: Sequence[ChartRow], asset_dir: str) -> List[Tuple[str, str]]:
    """UR bar charts for Section 5.5.  Returns [(png_path, caption), ...]."""
    rows = list(rows)
    if not rows or not any(r[2] is not None for r in rows):
        return []
    plt = S.apply_matplotlib_style()
    c = S.CHART
    out = []

    # ── 1) every check, grouped and coloured by primary element ─────────
    fig, ax = plt.subplots(figsize=c.figsize)
    xs, heights, colors, labels, styles_ = [], [], [], [], []
    x = 0.0
    group_spans = []
    prev = None
    start = 0.0
    for element, label, ur in rows:
        if prev is not None and element != prev:
            group_spans.append((prev, start, x - 1.0))
            x += 0.6                                   # gap between elements
            start = x
        elif prev is None:
            start = x
        prev = element
        xs.append(x)
        heights.append(ur if ur is not None else 0.0)
        colors.append(c.element_colors.get(element, "#888888"))
        labels.append(_plain(label))
        styles_.append(ur)
        x += 1.0
    group_spans.append((prev, start, x - 1.0))

    ymax = max([h for h in heights] + [c.threshold_value]) * 1.18
    for xi, h, col, ur in zip(xs, heights, colors, styles_):
        if ur is None:
            ax.bar(xi, ymax * 0.04, color="white", edgecolor="#9A9A9A", hatch="..", linewidth=0.6, zorder=3)
            ax.text(xi, ymax * 0.05, "n/d", ha="center", va="bottom", fontsize=c.font_size - 1.5, color="#6B6B6B")
            continue
        ax.bar(xi, h, color=col, zorder=3, width=0.78, **_bar_style(ur))
        ax.text(xi, h + ymax * 0.01, f"{h:.2f}", ha="center", va="bottom",
                fontsize=c.font_size - 1.5, color=(c.fail_edge if h > c.threshold_value else "#222222"))
    _threshold(ax, x)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=c.font_size - 1)
    ax.set_ylabel("Utilization Ratio, UR = Demand / Capacity")
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.7, x - 0.3)
    ax.grid(axis="y")
    for element, a, b in group_spans:
        if a > 0:
            ax.axvline(a - 0.8, color="#BBBBBB", linewidth=0.6, zorder=1)
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=c.element_colors.get(e, "#888888"), edgecolor=c.bar_edge, label=e)
               for e, _, _ in group_spans]
    handles += ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(handles),
              fontsize=c.font_size - 1, handlelength=1.4, columnspacing=1.0)
    out.append((_save(fig, asset_dir, "ur_all_checks.png"),
                r"Utilization ratio (UR = Demand / Capacity) of every design check, grouped by primary "
                r"element. The red dashed line marks the limit UR = 1.0; hatched red bars ($UR > 1.0$) "
                r"fail, n/d = check not designed in this version."))

    # ── 2) governing (maximum) UR per primary element ───────────────────
    gov = {}
    for element, label, ur in rows:
        if ur is None:
            gov.setdefault(element, (None, ""))
            continue
        if gov.get(element, (None,))[0] is None or ur > gov[element][0]:
            gov[element] = (ur, _plain(label))
    elements = [e for e in c.element_colors if e in gov] + [e for e in gov if e not in c.element_colors]
    fig, ax = plt.subplots(figsize=c.figsize_medium)
    vals = [gov[e][0] for e in elements]
    ymax = max([v for v in vals if v is not None] + [c.threshold_value]) * 1.25
    for i, e in enumerate(elements):
        v, chk = gov[e]
        if v is None:
            ax.bar(i, ymax * 0.04, color="white", edgecolor="#9A9A9A", hatch="..", linewidth=0.6, zorder=3)
            ax.text(i, ymax * 0.06, "not designed", ha="center", va="bottom", fontsize=c.font_size - 1, color="#6B6B6B")
            continue
        ax.bar(i, v, color=c.element_colors.get(e, "#888888"), width=0.6, zorder=3, **_bar_style(v))
        ax.text(i, v + ymax * 0.015, f"{v:.2f}\n({chk})", ha="center", va="bottom",
                fontsize=c.font_size - 1.5, color=(c.fail_edge if v > c.threshold_value else "#222222"),
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85),
                zorder=5)
    _threshold(ax, len(elements))
    ax.set_xticks(range(len(elements)))
    ax.set_xticklabels([e.replace(" ", "\n", 1) for e in elements])
    ax.set_ylabel("Governing Utilization Ratio")
    ax.set_ylim(0, ymax)
    ax.grid(axis="y")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0))
    out.append((_save(fig, asset_dir, "ur_by_element.png"),
                r"Governing (maximum) utilization ratio of each primary element: steel plate girders, "
                r"concrete deck slab, cross bracing and end diaphragms. Red dashed line: UR = 1.0."))
    return out


def _num(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def material_charts(steel: Sequence[Tuple[str, Optional[float]]],
                    concrete_m3: Optional[float], rebar_t: Optional[float],
                    asset_dir: str) -> List[Tuple[str, str]]:
    """Bar charts for Chapter 7.  ``steel`` = [(component, tonnes), ...]."""
    plt = S.apply_matplotlib_style()
    c = S.CHART
    out = []

    data = [(k, _num(v)) for k, v in steel]
    if any(v for _, v in data):
        fig, ax = plt.subplots(figsize=c.figsize_small)
        names = [k for k, _ in data]
        vals = [v or 0.0 for _, v in data]
        cols = [c.material_colors.get(k, "#888888") for k in names]
        bars = ax.bar(range(len(names)), vals, color=cols, edgecolor=c.bar_edge, linewidth=0.6, width=0.6, zorder=3)
        top = max(vals) if vals else 1.0
        for b, v, (_, raw) in zip(bars, vals, data):
            txt = f"{v:.2f} t" if raw is not None else "n/a"
            ax.text(b.get_x() + b.get_width() / 2, v + top * 0.02, txt, ha="center", va="bottom",
                    fontsize=c.font_size - 0.5)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([n.replace(" ", "\n") for n in names])
        ax.set_ylabel("Structural steel (MT)")
        ax.set_ylim(0, top * 1.2 if top > 0 else 1)
        ax.grid(axis="y")
        ax.set_title(f"Total structural steel: {sum(vals):.2f} MT", fontsize=c.font_size + 0.5)
        out.append((_save(fig, asset_dir, "steel_tonnage.png"),
                    "Structural steel tonnage by component (girders, cross bracing and end diaphragms)."))

    cv, rw = _num(concrete_m3), _num(rebar_t)
    if cv is not None or rw is not None:
        fig, ax1 = plt.subplots(figsize=c.figsize_small)
        ax2 = ax1.twinx()
        ax2.spines["right"].set_visible(True)
        col_c = c.material_colors["Concrete"]
        col_r = c.material_colors["Reinforcement"]
        ax1.bar(0, cv or 0.0, color=col_c, edgecolor=c.bar_edge, linewidth=0.6, width=0.55, zorder=3)
        ax2.bar(1, rw or 0.0, color=col_r, edgecolor=c.bar_edge, linewidth=0.6, width=0.55, zorder=3)
        ax1.set_ylim(0, (cv or 1.0) * 1.22)
        ax2.set_ylim(0, (rw or 1.0) * 1.22)
        if cv is not None:
            ax1.text(0, cv * 1.02, f"{cv:.2f} m³", ha="center", va="bottom", fontsize=c.font_size - 0.5)
        if rw is not None:
            ax2.text(1, rw * 1.02, f"{rw:.2f} MT", ha="center", va="bottom", fontsize=c.font_size - 0.5)
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(["Concrete\n(deck slab)", "Reinforcement\nsteel"])
        ax1.set_ylabel("Concrete volume (m³)", color=col_c)
        ax2.set_ylabel("Reinforcement weight (MT)", color=col_r)
        ax1.tick_params(axis="y", colors=col_c)
        ax2.tick_params(axis="y", colors=col_r)
        ax1.grid(axis="y")
        ax1.set_xlim(-0.6, 1.6)
        out.append((_save(fig, asset_dir, "concrete_vs_rebar.png"),
                    r"Deck concrete volume (m$^3$, left axis) and reinforcement steel weight (MT, right axis)."))
    return out
