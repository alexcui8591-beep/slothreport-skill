---
name: slothreport
description: 把一篇论文或一个算法深度解读成"教学式"中文 report——公式逐符号拆解、baseline↔new 的 diff 对比表、具体数字举例与生活类比、图表/表格/示意图齐全。当用户要"解读/浅析/深度分析/讲讲"某篇论文或算法、要产出图文公式齐全的解读报告(markdown / PDF / HTML)、或给了 arxiv 链接想要一份带前置铺垫和直觉解释的稿子时使用。不负责纯摘要(那是 summarizer)、不负责写新论文(那是 scientific-writer)。
---

# 🦥 slothreport —— 教学式论文/算法深度解读

## 这个 skill 在追求什么

产出**让人真的看懂**的解读,而不是平铺直叙的总结。判分标准只有一条:**一个没读过原文的人,看完能讲清这个方法"改了什么、为什么改、改了之后好在哪"。** 参照范本是《DAPO 强化学习算法浅析》那种——先讲透前置(GRPO)再讲主角(DAPO),每个改动配 diff 表,每个公式逐符号拆,每个概念先给直觉再上数学,还带作者自己的小实验。

> 黄金法则:**举例 > 类比 > 直觉 > 数学 > 散文。** 能用一个跑通的数字例子说清,就别堆形式化定义。

## 首次使用:装前置(一次性,幂等)

第一次跑、或要出 PDF 前,先跑一次安装脚本(装过会自动跳过,**不要让用户每次手动回退**):

```bash
bash "$SKILL_DIR/scripts/setup.sh"      # $SKILL_DIR = 本 skill 目录
```

它装:`poppler`(抠图)、`python-markdown`(md→html),可选 `matplotlib/numpy/pandas`(重画图表)、`arxiv-latex-mcp`(精确取公式);并检测出 PDF 需要的浏览器 + CJK 字体。**只出 markdown 的话零依赖,可跳过。**

## 何时用 / 不用

- ✅ 用:深度解读一篇论文/一个算法/一项技术;要前置铺垫 + 直觉 + 公式拆解 + 对比表 + 图表的成稿。
- ❌ 不用:只要一段摘要(用 summarizer);要写一篇新论文/综述(用 scientific-writer);只要翻译。

## 工作流(七步,按顺序做)

1. **取真源,别凭记忆。** 有 arxiv id 就用 `arxiv-latex-mcp`(`get_paper_prompt` 拿扁平化 LaTeX,公式/记号才精确);否则用 Read 直接读 PDF(`pages` 分段)。本地文件就直接读。**所有公式和数字都要落到原文,不准脑补。**
2. **定"主角 + 前置"。** 找出这个方法的 baseline/灵感来源(DAPO 的前置是 GRPO)。**前置必须先单独讲透**,否则主角讲不清。列出主角相对 baseline 的全部改动点。
3. **搭骨架**(见 `references/report_blueprint.md`):简介(核心贡献 bullet)→ 前置回顾(机制+损失函数+一个跑通的例子)→ 主体(逐个改动,每个都用"问题→根源→解法→效果")→ 实验/结果 → 总结+链接。
4. **逐节写,套用风格器件**(见 `references/style_devices.md`):每个改动配 **diff 表**(`维度 | baseline | new | 为什么`);每个公式先写 LaTeX 再**逐符号拆**;每个概念**先直觉后数学**;穿插**具体数字例子 + 生活类比**;能复现就加**作者自验**。
5. **保实验 + 图文并茂**(见 `references/experiments_section.md`):实验是"让人信"的核心,必须单独成章——setup / 数据集 / baseline / 主结果 / 消融 / 训练动态,每张结果图都讲清"它让你能下什么结论"。
6. **处理图片(三分类,默认保留原图)**(见 `references/visuals_and_tools.md`):论文里**架构图、结果曲线、机制示意、定性样例 → 抠原图保留**(arxiv 源码包 / MinerU,带 caption + 来源);**公式、自己构造的简单流程 → 原生渲染**(KaTeX / Mermaid);**有原始数据想要更干净 → 重建**(matplotlib)。**拿不准的重要图一律保留,绝不静默丢弃。**
7. **组装成稿**,按目标格式(默认 markdown)。**要 PDF 直接用自带脚本**(已内置"抠图/公式保护/CJK 字体"三件套,不用每次重踩坑):
   ```bash
   python3 "$SKILL_DIR/scripts/md2pdf.py" "你的报告.md"   # 同名 .pdf 落在旁边
   ```
8. **过质检门**(见 `references/quality_gate.md`):前置讲透?每改动有 diff 表?每公式逐符号拆?**实验章节齐全、关键图都在、每图配解读?**至少一个跑通的例子?每个数字溯源?不过关就回去补。

## 风格硬约束(范本提炼)

- **前置先行**:不解释 GRPO 直接讲 DAPO = 失败。先把 baseline 的损失函数、流程、一个数字例子讲透。
- **每个改动一张 diff 表**:`维度/算法 | baseline | new | Reason`。这是范本最有辨识度的器件,必须有。
- **公式逐符号拆**:写完 $\mathcal{L}=\dots$ 后,像"从右往左捋求和符号"那样把每个 $\sum$、每个下标、每个比率讲一遍。
- **直觉三段式**:`什么是X?` → 两个极端(高熵/低熵)各意味着什么 → 后果 → 解法。
- **数字 + 类比**:用真实数字跑场景(如 $\pi_{old}=0.9 \Rightarrow$ 上限 $0.9\times1.2=1.08$);配生活类比(token-level loss = "把所有学生所有科目卷子放一起算总分")。
- **图文并茂、不丢原图**:论文的关键图(架构、曲线、示意、定性样例)是理解和说服的核心,**必须抠原图保留**并配 caption + 来源,绝不因为"想原生渲染"而丢掉。只有公式和自己构造的简单流程才用 KaTeX/Mermaid。
- **实验必须讲透**:setup / baseline / 主结果 / 消融 / 训练动态一个不能少,每张结果图都要回答"它证明了什么"。没有实验的解读 = 没有证据的断言。
- **作者自验**:能跑就跑一个小实验佐证(范本里 $L_{max}=400, L_{cache}=50$,约 40 step 收敛),增可信度。
- **语气**:中英术语并行(Clip-Higher / 提高裁剪上限)、口语化但精确、少量 emoji(👇🏻🌰)提节奏,不滥用。

## 工具栈(按需调用,缺了就降级)

| 用途 | 首选 | 降级方案 |
|---|---|---|
| 取精确公式/LaTeX 源 | `arxiv-latex-mcp`(`get_paper_prompt` / `get_paper_section`) | Read 读 PDF;WebFetch 抓 `arxiv.org/html/<id>` |
| **保留原图(arxiv)** | 下 `arxiv.org/e-print/<id>` 源码包 → 拿原始图文件(png/pdf/eps)+ caption | 截 PDF 图;引 `arxiv.org/html/<id>` 里的图 URL |
| **保留原图(非 arxiv PDF)** | `MinerU`(布局感知抽图+caption)或 `anthropic-skills:pdf`(抽内嵌图) | 手动截关键页 |
| 找论文/查被引 | `arxiv-mcp-server`(`search_papers`) / WebSearch | — |
| **出 PDF(默认,公式+图+表+中文)** | **自带 `scripts/md2pdf.py`**(md→HTML+MathJax→无头 Chrome,图 base64 内嵌、CJK 字体已处理) | `latex-document-skill` 走 TeX Live |
| 出 HTML 长文(KaTeX+Mermaid+代码交叉引用) | `paper-craft-skills` 的 `paper-analyzer` | 纯 markdown |
| 自己构造的流程/架构示意 | Mermaid(markdown 内联) / TikZ(PDF) | 文字描述 |

> 默认产出 **markdown**(飞书/Notion 友好,和范本一致)。用户要 PDF 走 latex-document-skill,要 HTML 走 paper-analyzer。**任何工具缺失都不阻塞**——公式退化成 markdown 里的 LaTeX、图退化成 Mermaid 或文字。

## 关键原则

- **忠实 > 漂亮**:每个公式、阈值、超参、结论都要对得上原文。范本里 $\epsilon_{low}=0.2, \epsilon_{high}=0.28$、lr $=1\text{e-}6$、batch $=512$、$G=16$ 这种数字必须精确。
- **解耦输入与排版**:先把"讲清楚"做对(blueprint + style),再考虑"排得好看"(visuals + tools)。别让排版需求牺牲解释质量。
- **不确定就标注**:原文没讲清/自己推断的地方,显式标"(此处为笔者理解)",不要伪装成原文。
