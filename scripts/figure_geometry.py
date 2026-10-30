"""Small geometry helpers for paper-figure QA.

These are deliberately tiny: no data loading, no style policy. They encode the
recurring fixes found in the Cu-MAZ case (legend handles, dummy legend text,
parallel broken-axis marks, note alignment).
"""
from __future__ import annotations

from matplotlib.lines import Line2D


def line_handle(color, marker="o", label=None, lw=2.2, ms=6.3):
    """Legend handle with line + marker only (no errorbar caps)."""
    return Line2D([0], [0], color=color, marker=marker, lw=lw, ms=ms,
                  mfc=color, mec=color, label=label)


def dummy_handle(label):
    """Invisible handle for a text-only entry inside a legend."""
    return Line2D([0], [0], color="none", lw=0, label=label)


def break_marks(fig, ax_left, ax_right, dx=0.0065, lw=1.6, color="black"):
    """Draw parallel // marks at the top/bottom of a broken axis pair.

    Coordinates are in figure space, so the left/right slopes are identical
    regardless of the two axes' width/height ratios.
    """
    bL = ax_left.get_position()
    bR = ax_right.get_position()
    dy = dx * fig.get_figwidth() / fig.get_figheight()
    for x in (bL.x1, bR.x0):
        for y in (bL.y0, bL.y1):
            fig.add_artist(Line2D([x - dx, x + dx], [y - dy, y + dy],
                                  transform=fig.transFigure, color=color,
                                  lw=lw, clip_on=False))


def place_note_below_legend(fig, ax, legend, text, gap=0.055, **text_kwargs):
    """Place a note (GHSV, sample name) below a legend, left-aligned to its text.

    `text_kwargs` are passed to ax.text; do not repeat transform/ha/va.
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    # left edge of the first legend text (not the handle)
    x_px = legend.texts[0].get_window_extent(renderer).x0
    x_ax = ax.transAxes.inverted().transform((x_px, 0))[0]
    # bottom of the whole legend
    y_px = min(t.get_window_extent(renderer).y0 for t in legend.texts)
    y_ax = ax.transAxes.inverted().transform((0, y_px))[1]
    return ax.text(x_ax, y_ax - gap, text, transform=ax.transAxes,
                   ha="left", va="top", **text_kwargs)
