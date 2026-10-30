# 示例 profile（已脱敏）

> 这是一份**填完的** case profile，用来说明"做到什么颗粒度算填好了"。
> 样品名、图号、峰位、路径都已替换成占位符；处理新论文时复制 `case-profile-template.md` 重写，**不要照搬这里的任何数值**。

## 1. 基本信息

| 项 | 内容 |
|---|---|
| 来源 | 某课题组未发表稿（示例） |
| 目标图 | Fig.4（峰拟合）、Fig.5（谱学叠加） |
| 数据目录 | 只读；仓库里只留相对路径与 SHA，不留绝对路径 |
| 交付 | 600 dpi PNG + SVG/PDF + provenance + QA 记录 |

## 2. 图—数据—列对应表（节选）

| 图 | 面板 | 源文件 | sheet/列 | 样品 | 单位 | 变换 | 来源层级 |
|---|---|---|---|---|---|---|---|
| Fig4 | B | peaks.xlsx | Sheet1, Xobs/Yobs/Xgen/Ygen/Peak1-4 | 样品 A | °C / a.u. | 无 | fit |
| Fig4 | A | tpd.csv | time, T, signal | 样品 A/B/C | °C / a.u. | 无 | fit |
| Fig5 | A | epr.txt | B(mT), intensity | 样品 A/B/C | mT / a.u. | 无 | processed |
| Fig5 | B | tpr.txt | T, H2-uptake | 样品 A/B/C | °C / a.u. | 无 | processed |

**结论**：Fig4/5 的观察谱与作者拟合都可读，本项目**不重拟合**，只复画；残差照原样呈现。

## 3. 这个案例证明必须保留的行为

- 固定 Arial 8 pt、去掉上/右框，和"对齐原稿"是冲突的目标；风格必须从原图量，不能套默认。
- PeakFit 导出的 8 列是 `Xobs, Yobs, Xgen, Ygen, Peak1-4`；**峰列顺序与报告里的分量编号不一定一致**，必须先核对映射。
- 观察与 generated 的温度网格不能逐行相减；残差要在同一 x 网格上算。
- 有作者拟合时不要重新拟合；为"看起来更像"去改参数不算复现。
- XRD 工作表里的 y 已经含作者尺度/偏移，**不要再逐谱除最大值**。
- 同一块数据里出现重复点/缺失点（例如某个温度重复、某个温度缺失）→ 标出来等作者确认，**不猜改**。
- 平滑不是拟合；偏移不是基线校正；逐谱归一化会抹掉样品间强度关系。
- 分峰必须用渐变填充，平涂会让重叠区发脏。

## 4. 版式参数（示例，别照搬）

| 图 | 画布 (in) | 轴标题 pt | 刻度 pt | 图例 pt | 标注 |
|---|---|---|---|---|---|
| Fig1 | 11.8 x 10.2 | 12 | 11 | 13 | 面板字母 22 |
| Fig4 | 10.0 x 4.3 | 16 | 11 | - | - |
| Fig5 | 8.0 x 3.578 | 17.5 | 12.5 | 14 | 分量 12.5 / 样品 13 / 字母 18 |
| Fig6 | 12.0 x 10.8 | 16 | 11 | 8.5 | 面板字母 22 |

## 5. 验收记录

- 已用 `scripts/style_fingerprint.py --ref 原图` 复核：Fig5（刻度 3.36% vs 原图 3.17%，轴标题 6.01% vs 5.96%）。
- 只过了"位置类"项（图例/断口/轴标题距离）、**字号比例还没复核**：Fig1 / Fig6 / S1 / S7 → 下次动手前先跑一遍 fingerprint。
- 已知不可用：断轴过多、面板框不完整的图，fingerprint 会给 `[!]` 提示，按 `figure-qa-checklist.md` 手工量。

## 6. 第三方参考

- [scientific-visualization（K-Dense）](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-visualization)
- [scipy.signal.savgol_filter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html)
- [spectrochempy-omnic](https://github.com/spectrochempy/spectrochempy-omnic)
