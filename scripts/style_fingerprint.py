"""Measure the layout / type-scale fingerprint of a figure raster.

Usage
-----
    python style_fingerprint.py FIGURE.png                # self-check against the house style
    python style_fingerprint.py FIGURE.png --ref ORIG.png # compare a redraw with its reference

Why
---
The most common failure in "data are right but the figure looks wrong" is *proportion*:
a canvas that is too large makes every label look small. This prints the ratios that
matter (all normalised to figure width/height, so dpi does not matter) and flags the
ones outside the house-style band in references/style-profile-template.md.

Notes
-----
* Reads pixels only. Never touches the data.
* Assumes the figure is a grid of rectangular panels with visible spines.
* If the axes are frameless or the background is not white, expect detection to fail;
  that is a signal to check the figure by hand, not a bug to work around.
"""
from __future__ import annotations
import argparse
import numpy as np
from PIL import Image

# house style bands, see references/style-profile-template.md
TARGET = {
    "tick_label_pct_h": (3.0, 3.5),
    "axis_title_pct_h": (5.7, 6.2),
    "panel_left_pct_w": (3.0, 5.0),
    "panel_right_pct_w": (0.0, 1.0),
    "panel_top_pct_h": (0.4, 1.2),
    "panel_bottom_pct_h": (13.0, 15.0),
    "spine_pct_w": (0.28, 0.40),
}


def bands(mask, gap=3, minlen=1):
    idx = np.flatnonzero(mask)
    out = []
    if not len(idx):
        return out
    s = p = idx[0]
    for x in idx[1:]:
        if x - p > gap:
            if p - s + 1 >= minlen:
                out.append((int(s), int(p)))
            s = x
        p = x
    if p - s + 1 >= minlen:
        out.append((int(s), int(p)))
    return out


def measure(path):
    img = np.array(Image.open(path).convert("RGB")).astype(int)
    g = img.mean(axis=2)
    H, W = g.shape
    dark = g < 100
    rows = [y for y in range(H) if max([b - a + 1 for a, b in bands(dark[y])] or [0]) > .35 * W]
    cols = [x for x in range(W) if max([b - a + 1 for a, b in bands(dark[:, x])] or [0]) > .35 * H]
    rb = bands(np.isin(np.arange(H), rows), gap=3)
    cb = bands(np.isin(np.arange(W), cols), gap=3)
    if len(rb) < 2 or len(cb) < 2:
        raise SystemExit(f"{path}: cannot find panel frames (frameless axes? try a crop of one panel)")

    r = {"path": path, "W": W, "H": H,
         "panels_x": max(1, len(cb) // 2), "panels_y": len(rb) - 1}

    # outer plot box and margins
    top, bot = rb[0][1], rb[-1][0]
    left, right = cb[0][1], cb[-1][0]
    ys, xs = np.where(dark)
    r["left_margin_pct_w"] = xs.min() / W * 100
    r["right_margin_pct_w"] = (W - 1 - xs.max()) / W * 100
    r["top_margin_pct_h"] = ys.min() / H * 100
    r["bottom_margin_pct_h"] = (H - 1 - ys.max()) / H * 100
    r["spine_pct_w"] = (cb[0][1] - cb[0][0] + 1) / W * 100

    # plot box (whole area covered by panels) and its distance to the canvas edge
    r["panel_left_pct_w"] = left / W * 100
    r["panel_right_pct_w"] = (W - 1 - right) / W * 100
    r["panel_top_pct_h"] = top / H * 100
    r["panel_bottom_pct_h"] = (H - 1 - rb[-1][1]) / H * 100
    r["plot_box_aspect"] = (right - left) / (bot - top) if bot > top else float("nan")

    # bottom strip: [tick marks] [tick labels] [axis title]
    # measured under the FIRST panel only: mixing panels with different tick
    # lengths merges two label rows into one band and inflates the number
    x_hi = cb[1][0] if len(cb) >= 2 else right
    strip = (g[rb[-1][1] + 1: H, left:x_hi] < 140).any(axis=1)
    sb = bands(strip, gap=5, minlen=2)
    r["bottom_bands_pct_h"] = [round((b - a + 1) / H * 100, 2) for a, b in sb]
    if len(sb) >= 2:
        r["tick_label_pct_h"] = (sb[1][1] - sb[1][0] + 1) / H * 100
    if len(sb) >= 3:
        r["axis_title_pct_h"] = (sb[2][1] - sb[2][0] + 1) / H * 100
    if sb:
        r["tick_len_pct_h"] = (sb[0][1] - sb[0][0] + 1) / H * 100

    # left strip: rotated y-axis title
    lstrip = g[top:bot, 0:max(1, cb[0][0] - 2)] < 140
    ys2 = np.flatnonzero(lstrip.any(axis=1))
    if len(ys2):
        r["ylabel_len_pct_h"] = (ys2.max() - ys2.min() + 1) / H * 100
        xs2 = np.flatnonzero(lstrip.any(axis=0))
        r["ylabel_gap_pct_w"] = (cb[0][1] - (xs2.max() + 1)) / W * 100
    return r


def show(r, ref=None):
    def cell(key, fmt="{:.2f}"):
        v = r.get(key)
        v = "  -  " if v is None else fmt.format(v)
        if ref is None:
            lo, hi = TARGET.get(key, (None, None))
            if lo is None or r.get(key) is None:
                return v + "        "
            ok = lo <= r[key] <= hi
            return f"{v}  {'ok ' if ok else 'FIX'} [{lo}-{hi}]"
        rv = ref.get(key)
        rv = "  -  " if rv is None else fmt.format(rv)
        d = "" if (r.get(key) is None or ref.get(key) is None) else f"  Δ{r[key]-ref[key]:+.2f}"
        return f"{v}  ref {rv}{d}"

    print(f"\n{r['path']}")
    print(f"  canvas {r['W']}x{r['H']}   {r['panels_x']} cols x {r['panels_y']} rows of frames"
          f"   plot box w/h {r.get('plot_box_aspect', float('nan')):.3f}")
    print(f"  plot box left {cell('panel_left_pct_w')}   right {cell('panel_right_pct_w')}")
    print(f"           top  {cell('panel_top_pct_h')}   bottom {cell('panel_bottom_pct_h')}")
    print(f"  ink edge l {r['left_margin_pct_w']:.2f}  r {r['right_margin_pct_w']:.2f}"
          f"  t {r['top_margin_pct_h']:.2f}  b {r['bottom_margin_pct_h']:.2f}")
    print(f"  spine    {cell('spine_pct_w')}   tick len {r.get('tick_len_pct_h', float('nan')):.2f}")
    print(f"  tick labels {cell('tick_label_pct_h')}")
    print(f"  axis title  {cell('axis_title_pct_h')}")
    if "ylabel_len_pct_h" in r:
        print(f"  y title  len {r['ylabel_len_pct_h']:.1f}%H  gap {r.get('ylabel_gap_pct_w', float('nan')):.2f}%W")
    print(f"  bottom bands %H {r['bottom_bands_pct_h']}")
    if r.get("axis_title_pct_h", 0) > 12 or r.get("tick_label_pct_h", 0) > 8:
        print("  [!] 这组数不可信：图不是规则网格，或断轴/多行谱打断了边框检测。"
              " 请按 references/figure-qa-checklist.md 手工量。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("figure")
    ap.add_argument("--ref", help="reference figure to compare against")
    a = ap.parse_args()
    ref = measure(a.ref) if a.ref else None
    show(measure(a.figure), ref)
    if ref:
        print("\n(columns: rebuild | reference | delta; deltas are percentage points)")
