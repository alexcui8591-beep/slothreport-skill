# 图表与工具：图文并茂地落地公式/图/表

核心原则：**图文并茂，论文的重要原图一张都不能丢。** 图片按来源和用途分三类处理，默认偏向"保留原图"。

## 图片三分类（先判类型，再决定怎么处理）

| 类型 | 包含什么 | 怎么处理 |
|---|---|---|
| **① 保留原图** | 实验结果曲线、消融图、架构/框架图、机制示意图、定性样例（输入输出截图）、原文里手绘的概念图 | **抠出原始图文件嵌入**，配 caption + `（来源：原论文 Fig.X）`。这些是证据/是作者的设计表达，**复刻不出来也不该复刻** |
| **② 原生重渲** | 数学公式、作者自己构造的简单流程/关系图 | 公式→KaTeX/LaTeX；流程→Mermaid。**只有这类才不用截图**——一个干净公式没必要截图 |
| **③ 重建** | 你手里有原始数据、想要更清晰/统一配色/中文标注的版本 | matplotlib 重画，并注明"（笔者据原文数据重绘）" |

> **判断默认值：拿不准就归①保留。** 宁可多留一张原图，也不要让读者看不到论文的关键证据。范本里 38 张图大部分属于①，是对的；只有那些"被截成图片的公式"才该归②改成 KaTeX。

## 怎么抠原图（保留①类）

- **arxiv 论文（首选）**：下源码包 `curl -L -o src.tar.gz https://arxiv.org/e-print/<id>` → 解压 → `figures/` 里就是作者用的**原始 png/pdf/eps**，全质量无损；caption 在 .tex 里 `\caption{}`。按图号对应嵌入。
- **非 arxiv PDF**：用 **MinerU**（`opendatalab/MinerU`，布局感知，输出 markdown + 抠好的图 + caption）；或 `anthropic-skills:pdf` 抽内嵌图；实在不行手动截关键页。
- **网页版兜底**：`arxiv.org/html/<id>` 里的 `<img>` 直接有图 URL，可引用。
- 嵌入后**统一放到 `图片和附件/` 目录**（与范本一致），markdown 用相对路径 `![caption](图片和附件/xxx.png)`。

## 四类视觉元素 → 怎么产出

### 1. 公式 —— 用 LaTeX/KaTeX 重渲（②类，唯一该"去截图"的）
- markdown 行内 `$...$`、独立 `$$...$$`。飞书/Notion/typora 都渲染。
- **公式必须来自原文 LaTeX 源**（`arxiv-latex-mcp` 的 `get_paper_prompt`），避免手抄出错。重公式论文 PDF 解析经常糊，源码才准。
- 复杂多行用 `aligned`：
  ```
  $$\begin{aligned}
  \mathcal{L}(\theta) &= \mathbb{E}\big[\min(r_{i,t}\hat A_{i,t},\ \text{clip}(r_{i,t},1-\epsilon_{low},1+\epsilon_{high})\hat A_{i,t})\big]
  \end{aligned}$$
  ```

### 2. 流程 / 架构 / 关系 —— Mermaid（HTML/markdown）或 TikZ（PDF）
- 训练循环、数据流、模块关系用 Mermaid `flowchart`。范本的「整体训练循环」「GRPO Process」都该是 Mermaid 而非截图。
  ```mermaid
  flowchart LR
    Q[问题 q] --> R[Policy 采样 G 个回答 o_i]
    R --> Adv[Reward 打分 → 计算优势 A_i]
    Adv --> Upd[按 r·A、clip、KL 更新 θ]
    Upd -->|迭代数千次| R
  ```
- 出 PDF 时同样的图用 TikZ（`latex-document-skill` 支持 TikZ/Graphviz/PlantUML 四管线）。

### 3. 定量对比 / 曲线 —— 原文结果图优先保留（①），只有拿到数据才重建（③）
- **论文的实验结果图（消融、AIME 曲线、length/entropy 动态）默认保留原图**——它是证据，且你通常没有原始数据点，复刻只会失真。配 caption + 来源。
- **只有当你手里真有数据**（自己跑的、原文给了表格数据）想要更清晰/中文化的版本，才用 `latex-document-skill/generate_chart.py` 重画（9 类图，色盲友好），并注明"笔者据原文数据重绘"。
- 别把"保留原图"误当偷懒——对实验曲线，保留原图才是对的。

### 4. 离散对比 / 配置 —— 表格
- markdown 表用于 diff 表、特性对比、超参表（见 style_devices 器件 1）。
- 出 PDF 用 `latex-document-skill/csv_to_latex.py` → booktabs 三线表。

## 目标格式 → 工具链

| 产出 | 工具 | 适用 |
|---|---|---|
| **markdown**（默认） | 原生 + KaTeX + Mermaid 表 | 飞书/Notion/wiki，和范本一致，最省事 |
| **PDF（推荐）** | **自带 `scripts/md2pdf.py`** | 一步出图文公式齐全的 PDF，无需 TeX Live |
| PDF（排版讲究） | `latex-document-skill` → TeX Live 编译 | 要 LaTeX 级排版、期刊风 |
| **HTML 长文** | `paper-craft-skills` 的 `paper-analyzer`：KaTeX + Mermaid + GitHub 代码交叉引用 | 要交互、要内嵌可跑代码、网页分享 |

### 出 PDF 一步走（自带脚本）

```bash
bash "$SKILL_DIR/scripts/setup.sh"            # 首次：装 poppler/markdown 等（幂等）
python3 "$SKILL_DIR/scripts/md2pdf.py" "报告.md"   # 出同名 PDF
```

`md2pdf.py` 内置了三个**否则每次都要重踩的坑**：

1. **数学保护**：渲染前把 `$...$`/`$$...$$` 抠出来占位，避免 markdown 把公式里的 `_`、`*` 当强调符破坏，渲染后再还原交给 MathJax。
2. **图片 base64 内嵌**：把 `![](图片和附件/x.png)` 转成 data URI 内联——**这正是 md 里图加载不出来的根因**（相对路径 + 中文目录名，viewer 解析失败）；内嵌后任何 viewer 都加载得到。
3. **CJK 字体注入（最坑）**：**无头 Chrome 读不到系统字体**，默认会把正文中英文**全部渲染成空白**（只有 SVG 公式和图能显示）。脚本用 `@font-face` 显式喂一个**单文件** CJK 字体（`find_cjk_font.sh` 自动找，mac 上是 `Arial Unicode.ttf`；`.ttc` 字体集合会加载失败，故只挑单文件），并用经典 `--headless` 而非 `--headless=new`（后者在 mac 上也丢字体）。

> 精简 Linux 上没单文件 CJK 字体时：`apt install fonts-noto-cjk`，`find_cjk_font.sh` 会自动捡到 Noto 的 `.otf`。

## 取材工具

| 用途 | 工具 | 命令/工具名 |
|---|---|---|
| 拿精确 LaTeX 源（公式准） | `arxiv-latex-mcp` | `get_paper_prompt` / `list_paper_sections` / `get_paper_section` |
| 搜论文/查相关工作 | `arxiv-mcp-server` / WebSearch | `search_papers` |
| 读本地 PDF | 内置 Read | `pages` 参数分段，>10 页必须分段 |
| 抓 HTML 版论文 | 内置 WebFetch | `arxiv.org/html/<id>` 比 PDF 解析准 |

## 降级原则（工具没装也能交付）
- 没有 arxiv-latex-mcp → Read 读 PDF / WebFetch 抓 HTML，公式人工核对原文。
- 没有 latex-document-skill → 出 markdown，图用 Mermaid，表用 markdown，放弃 PDF。
- 没有 paper-analyzer → 出 markdown 而非 HTML。
- **核心解读质量（blueprint + style）不依赖任何外部工具**，工具只决定排版上限。
