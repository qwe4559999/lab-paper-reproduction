# lab-paper-reproduction

把"论文图复现 / 原始数据出图"这件事，固化成一套可验收的流程。

给 Claude / DSH 一类 agent 用的 skill：拿到一篇论文的参考图和数据，按固定步骤建 case profile、核数据身份、量版式、出图、自检，最后交出一张**对得上原图**的图 + 一份说得清来源的记录。

> 不是某篇论文的专用脚本。仓库里的 `references/example-profile.md` 是一个已脱敏的实例，只示范"填好之后长什么样"。

## 它解决什么

论文图复现翻车，很少是因为不会写 matplotlib，而是这几件事：

| 典型翻车 | 本技能怎么处理 |
|---|---|
| 画出来的图"小一号"、字号偏小 | 先定画布，再按"占图高百分比"反算 pt（`style-profile-template.md`） |
| 逐谱归一化，样品间强度关系被抹平 | 明确禁止把归一化当默认美化；只允许常数 offset / 减中位数 |
| PeakFit 的 Peak1-4 直接当 S1-S4 | 强制先核对峰列与分量编号的映射 |
| 只交图，说不清哪一列来自哪个文件 | 图-数据-列对应表 + SHA + 来源层级（raw / processed / fit / figure） |
| "看起来像"就改参数 | 有作者拟合时不重拟合；像素相似不算复现 |

## 两种模式

| | 复现模式（有原图） | 新图模式（只有数据） |
|---|---|---|
| 版式依据 | 从原图逐项量 | `references/style-profile-template.md` 的默认值 |
| 关键动作 | 提风格 profile → 复画 → 两列对照 | 定画布 → 算字号 → 出图 → 自检比例 |
| 验收 | 与原图 Δ ≤ 0.3 个百分点，或逐项人工确认 | 刻度 3.0-3.5% 图高、轴标题 5.7-6.2% 图高 |

## 快速开始

```bash
git clone https://github.com/<you>/lab-paper-reproduction.git
cp -r lab-paper-reproduction ~/.dsh/skills/lab-paper-reproduction     # 或 ~/.claude/skills/
```

然后在对话里调用 `/lab-paper-reproduction`，或直接把 `SKILL.md` 喂给 agent。

最小流程：

1. 复制 `references/case-profile-template.md` → `references/<case>.md`，填样品别名、图-数据-列、单位、待核问题。
2. `python scripts/inventory_inputs.py <数据目录> --out inventory.json` —— 只读盘点文件 / 表头 / SHA。
3. 复现模式：从原图量风格；新图模式：按 style-profile 定画布与字号。
4. 出图后用 `python scripts/style_fingerprint.py out.png [--ref 原图.png]` 自检版式比例。
5. 按 `references/figure-qa-checklist.md` 逐项验收，交 PNG/SVG/PDF + provenance + 未决问题。

## 目录

```
lab-paper-reproduction/
  SKILL.md                          # 主流程（给 agent 读）
  references/
    case-profile-template.md        # 每篇论文先复制这一份
    example-profile.md              # 已脱敏的填好示例
    style-profile-template.md       # 无原图时的默认版式（画布/字号/线宽/填充）
    figure-qa-checklist.md          # 逐项验收清单
    plot-recipes.md                 # 渐变填充、引线、轴标题、图例重排的代码片段
  scripts/
    inventory_inputs.py             # 只读盘点：文件 / 表头 / SHA
    style_fingerprint.py            # 量版式比例，可与原图两列对比
    figure_geometry.py              # 图例 / 断口 / 说明文字对齐小工具
    check_peak_export.py            # PeakFit 八列检查（可选）
  LICENSE
```

## 设计原则

- **数据身份优先于画风**：先确认这一列是什么，再谈配色。
- **比例优先于绝对字号**：先定画布，再按占图高百分比算 pt。
- 先找数值，不要看到图就截图；只有截图时标"参考图复用"，不要写成"数值重建"。
- 平滑不是拟合，偏移不是基线校正，平涂不是填充。
- 一个入口 + 每篇论文一个 profile，不是一堆脚本的拼盘。

## 已验证 / 局限

- 在一个真实的 Cu-MAZ 体系上做过完整试点（Fig1-Fig6 + SI），版式比例复核到 0.2-0.3 个百分点内。
- `style_fingerprint.py` 只适用于"规则矩形面板 + 有边框"的图；断轴很多、面板框不完整的图会给出不可信提示，按 checklist 手工量。
- 光谱读取（`.spa` 等）依赖 `spectrochempy-omnic`，PDF 预览依赖 `pypdfium2`，**不在本仓库内**，需要自行安装。
- 不同仪器导出格式差异大，`inventory_inputs.py` 的格式探针需要按需扩展。
- 只在少量数据集上跑过；欢迎用你自己的论文来提 issue / PR 补案例（请勿上传未发表数据）。

## 许可

MIT，见 [LICENSE](LICENSE)。
