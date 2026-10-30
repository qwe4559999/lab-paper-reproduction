# 可复用代码片段（都来自已验证的出图脚本）

> 这些不是"最佳实践"，是**踩过坑之后能用的写法**。复制时改颜色/字体/数据，不要改坐标逻辑。
> 来源：Cu-MAZ Fig5 v2（`rebuild_fig5_v2.py`）、Fig1 v2、Fig6。

## 1. 竖版"向白渐变"填充（替代平涂 alpha）

问题：平涂 alpha 在重叠区会叠出发褐的脏色，和 Origin 的渐变填充差很远。

做法：用 imshow 铺一层 RGBA，alpha 按"该列曲线高度"归一化后衰减，再用轴范围天然裁切。

```python
import numpy as np
from matplotlib.colors import to_rgb

def gradient_fill(ax, x, y, color, amax=0.72, power=1.15, nx=720, ny=340):
    x = np.asarray(x, float)
    y = np.clip(np.asarray(y, float), 0, None)
    if y.max() <= 0:
        return
    xg = np.linspace(x.min(), x.max(), nx)
    yg = np.linspace(0, y.max() * 1.001, ny)
    cur = np.interp(xg, x, y)[None, :]              # 每列的曲线高度
    Y = yg[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        t = np.where(cur > 1e-12, Y / cur, np.inf)  # 该列没有曲线 -> 不填
    a = amax * np.clip(t, 0.0, 1.0) ** power        # 基线 0 -> 曲线处 amax
    a[~np.isfinite(t) | (t > 1.0)] = 0.0            # 曲线以上不填
    rgba = np.zeros((ny, nx, 4))
    rgba[..., :3] = to_rgb(color)
    rgba[..., 3] = a
    ax.imshow(rgba, extent=[xg[0], xg[-1], 0.0, yg[-1]], origin="lower",
              aspect="auto", interpolation="bilinear", zorder=1)
```

**两个必须检查的坑（都实际踩过）：**

1. **方向**：alpha 要随 t = y/curve **增大**（基线 0 → 曲线 amax）。
   写成 (1−t) 会得到"上淡下浓"的倒渐变——远看像阴影，近看就是假。
2. **空列**：曲线≈0 的那些列，如果 fallback 成 t=1，会画出**整块色块**（2026-10-28 实际出现）。
   必须用 np.inf 或显式 mask 掉。

**amax 的标定**：Cu-MAZ 原图在填充 35% 高度处 α≈0.64、60% 处 α≈0.33；
amax=0.72、power=1.15 能对上。换论文时按同样方法从原图取样标定，不要直接抄 0.72。

配套：轮廓线用**不透明** ax.plot(..., lw=1.5)，不要 alpha=0.8；总拟合线 1.8–1.9 pt，叠在填充之上。

## 2. 标注引线：x 用数据坐标，y 用轴比例

问题：引线长度会随轴范围变化；用纯数据坐标改一次轴限就全歪。

做法：`blended_transform_factory(ax.transData, ax.transAxes)`。

```python
from matplotlib.transforms import blended_transform_factory

TR = blended_transform_factory(ax.transData, ax.transAxes)

for x, (y_bottom, y_top) in zip(peak_centers, leader_spans):
    ax.plot([x, x], [y_bottom, y_top], transform=TR,
            color="black", lw=1.3, zorder=6, solid_capstyle="butt")
    ax.text(x, y_top + 0.012, "S1", transform=TR,
            ha="center", va="bottom", fontsize=12.5, zorder=7)
```

- x 用作者报告峰位；
- `leader_spans` 用"该峰峰顶 → 总拟合线 +3% 面板高"算出来；
- 顶端贴边的那个峰（S1）把标签放到引线**下方**。

## 3. 轴标题：用 fig.text 定位，别用 labelpad 堆

问题：字号一大，matplotlib 的 bbox 堆叠会把轴标题顶出画布（Fig5 v2 第一版就是这么被裁的）。

```python
# 位置从原图量（图高/图宽的比例），或用 style-profile 的边距默认值
fig.text(0.265, 0.017, "Field (G)", ha="center", va="baseline",
         fontsize=17.5, fontweight="bold")
fig.text(0.0225, 0.5675, "Signal Intensity (a.u.)", rotation=90,
         ha="center", va="center", fontsize=17.5, fontweight="bold")
```

注意 `va="baseline"`：给文字留出下伸空间，否则括号底会被裁。

## 4. 图例：顺序重排 + line+marker

```python
from matplotlib.lines import Line2D

# 4.1 想按"视觉行优先"排，就得重排 handles（legend 是按列填的）
h, lb = ax.get_legend_handles_labels()
order = [2, 1, 0]                     # 例如原图是 3.56 / 2.69 / 1.26
ax.legend([h[i] for i in order], [lb[i] for i in order],
          loc="upper left", bbox_to_anchor=(0.108, 0.317), frameon=False,
          fontsize=14, handlelength=1.2, handletextpad=0.32,
          labelspacing=0.40, borderaxespad=0.0, borderpad=0.0)

# 4.2 有 error bar 的图，图例 handle 换成 line+marker，否则会带上下帽
handles = [Line2D([0], [0], color=c, marker=m, lw=1.8, ms=5,
                  mfc=c, mec=c) for c, m in zip(colors, markers)]

# 4.3 图例里要放纯文字（如 "NH3 · 60 min"），用不可见 handle 占位
dummy = Line2D([0], [0], color="none", lw=0)
```

## 5. 用 add_axes 精确摆面板

问题：`gridspec` 的 wspace/hspace 是相对值，很难和原图的像素位置对上。

```python
# 直接用原图量出来的矩形（figure 分数坐标），一步到位
axA = fig.add_axes([94/2400, 1-926/1074, 1084/2400, (926-3)/1074])
for i in range(3):                    # 三个等高子图，hspace = 0
    fig.add_axes([1319/2400,
                  1-926/1074 + (2-i)*((926-3)/1074)/3,
                  1077/2400,
                  ((926-3)/1074)/3])
```

**注意**：边框线宽会向外溢出一半，顶边贴到 1.0 时会被画布裁掉——
把高度减 0.0035（或把顶边压到 0.997）再出图。

## 6. 独立子轴：只改 ylim，不动数据

```python
# 每个子图各自的可读性轴限；数据本身 scale=1、offset=0
TPR_YLIM = {s: (bottom_k * fmax[s], top_k * fmax[s]) for s in samples}
ax.set_ylim(*TPR_YLIM[sample])
```

在 QA 里必须写一句"子图轴限不同，不可跨子图比较视觉峰高"。

## 7. 断轴 // 与图例文字对齐

见 `scripts/figure_geometry.py`：`break_marks()`（figure 坐标同斜率）、`place_note_below_legend()`（按图例文字 bbox 对齐，不硬编码 x）。

## 8. 下标符号（g//、A//、g⊥ 这类）

问题：直接写 `g//=2.38` 时斜杠会与等号同高、贴着基线，和 Origin 里"斜杠落在下三分之一"的样子不一样。
做法：把斜杠放进 mathtext 下标。

```python
ax.text(0.211, 0.905, r"g$_{//}$=2.38   A$_{//}$=149G",
        transform=ax.transAxes, ha="left", va="baseline", fontsize=12.5)
ax.text(3342, 0.1475, r"g$_{\bot}$=2.08",
        transform=blended_transform_factory(ax.transData, ax.transAxes),
        ha="left", va="center", fontsize=13)
```

- 下标里的 `//` 会按 0.7 倍缩小并下移；`\!`（负 thin space）会把两根斜杠挤在一起，一般不要加。
- 文字里夹 mathtext 时，整串仍然用 plain string 的 r"…" 包起来，只有 `$…$` 部分是公式。
- 竖线连接符（把标注连到括号的那根）要落在两段文字之间的空隙里；文字宽度会随字号变，位置要按出图后量到的空隙中心放，不要写死。
