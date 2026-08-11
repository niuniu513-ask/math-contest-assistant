# 数学建模竞赛辅助 Skill (math-contest-assistant)

数学建模竞赛全流程辅助 Agent Skill，支持 **Claude Code / Cursor / Copilot / Codex CLI / Windsurf** 等 AI 编码助手。
采用 **建模手 → 编程手 → 论文手** 三阶段流程，每阶段配备独立质检门禁（M1/P1/P2/W1/W2）。
输出符合国赛(CUMCM)或美赛(MCM/ICM)格式的完整论文(.docx + .pdf)。

## 兼容性

| AI 助手 | 质检模式 | 安装方式 |
|---------|---------|---------|
| **Claude Code** | 模式 A（多 Agent 独立质检） | `npx skills add` 或 `~/.claude/skills/` |
| **Cursor** | 模式 A（Agent 模式支持时） | `~/.cursor/skills/` 或项目 `.cursor/skills/` |
| **Codex CLI** | 模式 B（清单自审） | `~/.codex/skills/` 或 `codex skills add` |
| **GitHub Copilot** | 模式 B（清单自审） | `.github/copilot/skills/` 或项目根目录 |
| **Windsurf** | 模式 B（清单自审） | `~/.windsurf/skills/` |

> **双模式设计**：支持多 Agent 的环境使用模式 A（独立质检 Agent 验收），不支持的环境使用模式 B（严格按清单逐项自审 + 输出证据）。详见 [质检门禁策略](#质检门禁双模式)。

## 功能概览

- **三阶段流程**：建模手（破题+选模型）→ 编程手（求解+可视化）→ 论文手（写作+排版+降AI）
- **双模式质检**：模式 A（独立 Agent 验收 M1/P1/P2/W1/W2）/ 模式 B（清单自审）
- **内嵌方法库**：20 类代码模板（AHP/TOPSIS/灰色预测/ARIMA/PSO/GA 等）+ 7 类算法说明（含神经网络/LSTM）
- **37 篇获奖论文分析**：2023-2025 国赛优秀论文写作范式提炼
- **双格式输出**：LaTeX PDF + Word DOCX，正文数据图表结论一致
- **降 AI 痕迹**：内置 ai_detector.py 启发式检测，两遍改写+自审流程
- **内置基线模板**：CUMCM 完整模板 `cumcm-jayxin`（含 2026 官方格式与自带字体）与最小基线开箱即用，也可指定当届官方模板

## 质检门禁（双模式）

本 Skill 的核心质量保障。根据运行环境自动选择：

| 模式 | 适用环境 | 机制 |
|------|---------|------|
| **模式 A** | Claude Code、Cursor（支持 Agent 派发） | 独立质检 Agent 在 M1/P1/P2/W1/W2 节点验收，未通过不得进入下一阶段 |
| **模式 B** | Codex CLI、Copilot、Windsurf（单 Agent） | 严格按 `references/建模质检清单.md` / `references/编程质检清单.md` / `references/论文自审框架.md` 逐项自审，输出每项检查结果和证据 |

两种模式都不能用"已检查"一笔带过。

## 前置依赖

本 Skill 需配合以下 Skill 使用（均需单独安装到对应 Agent 的 skills 目录）：

| Skill | 用途 | 安装 |
|-------|------|------|
| `scientific-toolkit-skill` | 科学计算、可视化 | 用户自行安装 |
| `research-writing-skill` | 学术写作规范 | 用户自行安装 |
| `office-academic-skill` | DOCX/PPT 排版 | 用户自行安装 |
| `humanizer_academic` | 降 AI 写作痕迹 | [GitHub](https://github.com/matsuikentaro1/humanizer_academic) |

### 环境依赖

- **Python 3.9+**：一等实现路线之一——代码求解、DOCX 生成、图表审计（numpy/scipy/matplotlib/pandas/sklearn）
- **MATLAB**：与 Python 同等重要的一等实现路线——备齐工具箱后按 `references/语言选型对比.md` 对当前题对比选型；随附 `check_matlab_env.m`、`apply_publication_style.m`、`audit_publication_figure.m`、`export_publication_figure.m` 与五类方法模板、配色/图表/示意图规范
- **LaTeX (XeLaTeX + latexmk)**：PDF 论文编译
- **Pandoc**：LaTeX → DOCX 转换

> 语言选型：Python 与 MATLAB 同等重要，不设主路线/备选。进入编程前由 Agent 按评分卡对比两种语言对当前题的适配（算法覆盖、工具箱、复现、团队可辩护性、数据图出版、交付约束），结论写入模型合同；求解代码与数据图用选定语言，**参考图/示意图/流程图统一用 MATLAB 绘制**（风格统一）；可按需**双轨交付** Python + MATLAB 两套实现并交叉核验。

## 安装

### Claude Code

```bash
# 方式一：npx skills
npx skills add <your-username>/math-contest-assistant --global

# 方式二：手动
git clone https://github.com/<your-username>/math-contest-assistant.git ~/.claude/skills/math-contest-assistant

# 方式三：解压 zip
# 下载 math-contest-assistant.zip → 解压到 ~/.claude/skills/math-contest-assistant/
```

### Cursor

```bash
mkdir -p ~/.cursor/skills
git clone https://github.com/<your-username>/math-contest-assistant.git ~/.cursor/skills/math-contest-assistant
```

### Codex CLI

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/<your-username>/math-contest-assistant.git ~/.codex/skills/math-contest-assistant
```

### GitHub Copilot

参考 [Copilot Skills 文档](https://code.visualstudio.com/docs/copilot/copilot-skills)，
将本目录放到项目 `.github/copilot/skills/` 下或全局配置中。

### Windsurf

```bash
mkdir -p ~/.windsurf/skills
git clone https://github.com/<your-username>/math-contest-assistant.git ~/.windsurf/skills/math-contest-assistant
```

### 通用：直接下载 zip

1. 下载 `math-contest-assistant.zip`
2. 解压到你的 Agent 对应 skills 目录

## 使用方式

用户只需提供：
1. **赛题 PDF** — 放入工作目录
2. **附件数据** — 放入工作目录 `data/`

竞赛类型、届次、题号 Skill 自动从赛题内容识别。历年赛题库、获奖论文库、LaTeX/Word 模板、配色方案等全部内嵌，零配置开箱即用。

## 文件结构

```
math-contest-assistant/
├── SKILL.md                    # 主技能定义
├── README.md                   # 本文件
├── references/                 # 参考文档（41 个 .md）
│   ├── Subagent调度.md         #   模式 A 质检调度规则
│   ├── 算法索引.md             #   算法速查路由
│   ├── code-generation-guide.md #  20 类方法代码模板（835行）
│   ├── 可视化规范.md           #   Nature/SCI 出版级图表
│   ├── 图表选择与避坑.md       #   选图四问 + 主动拦截问题清单
│   ├── 英文化工作流.md         #   美赛三阶段英文化
│   ├── 论文自审框架.md         #   4 类 40+ 检查项
│   ├── 章节模板.md             #   论文章节推导范式
│   ├── award-paper-patterns*.md #   37 篇获奖论文分析
│   └── ...                     #   更多
├── tools/                      # 工具技能（5 个）
│   ├── docx/                   #   Word DOCX 生成/校验
│   ├── latex/                  #   LaTeX 项目/编译/校验
│   ├── pdf/                    #   PDF 读取/提取/OCR
│   ├── xlsx/                   #   Excel 数据处理
│   └── paper_search/           #   文献搜索
├── assets/                     # 算法详细说明（7 类）
├── scripts/                    # Python/MATLAB 脚本（15 个）
├── test_smoke.py               # 核心脚本冒烟测试（python test_smoke.py）
├── LICENSE                     # MIT 许可证
└── .gitignore
```

## 使用方式

在任意支持的 AI 编码助手中提及数学建模相关任务即可激活：

- "帮我做 2025 国赛 C 题"
- "分析这道数学建模题"
- "写这个模型的论文"
- "只跑代码出图"

也可以指定单阶段：
- "只做题目分析，不写代码"
- "只写论文，代码和结果已经有了"

## 输出产物

```
PROJECT_ROOT/
├── 完整论文.docx            # Word 版本
├── 完整论文.pdf             # LaTeX 编译版本
├── 完整论文-LaTeX/          # LaTeX 源码项目
├── code_and_figures.zip     # 代码 + 图表 + 日志
├── humanization_notes.md    # 降 AI 润色笔记
└── results/                 # 中间结果
```

## 行为准则

1. 建模完成后**必须等待用户确认**才进入编程阶段
2. 代码最多重试 3 次，超过标记问题而非死循环
3. 降 AI 最多 3 轮（两遍流程 + 最多 1 轮补充）
4. 所有计算结论来自实际运行结果，禁止编造数据
5. 论文格式以当届官方规则为准，不以本 Skill 默认值替代

## License

MIT
