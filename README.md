# 国赛 C 题数学建模辅助 Skill

`math-contest-assistant-c` 是 [`math-contest-assistant`](https://github.com/niuniu513-ask/math-contest-assistant) 的国赛 C 题优化分支。它继承通用版的附件读取、建模、编程、验证、图表、论文排版和复现能力，重点改进数据预处理前置、简单基线、模型复杂度控制和 C 题论文质量。

本分支不把 C 题等同于某一种固定模型，也不写死某一届赛题。模型必须由题面、附件数据和基线实验共同决定。

## 核心改进

- **数据前置**：正式定模前完成数据质量、处理决策、可辨识性和建模信号分析，通过 D1 门禁。
- **简单基线**：预测、评价、优化、分类、聚类、仿真等子问题先运行对应基线，通过 B1 门禁。
- **复杂度控制**：模型按 L0–L4 分级；复杂模型只有在修复基线关键缺陷且收益覆盖成本时才能升级。
- **证据写作**：公式、图表、表格和结论均绑定真实代码输出与验证记录。
- **论文深度**：正文内部目标为 25–30 页，通常包含 20–35 个有效编号公式、12–18 幅有效图和 8–12 张核心表；这些区间用于发现论证缺口，不用于机械凑数。
- **统一排版**：正文性文字统一黑色，中文正文使用宋体，英文和数字优先使用 Times New Roman，并提供 DOCX 样式审计。
- **可恢复执行**：状态、门禁、产物哈希、运行日志和复现命令持续记录，失败后从有效检查点继续。

## 工作模式

本 Skill 不只用于一次性生成完整论文。根据用户请求，可以选择以下任一模式：

| 模式 | 适用请求 | 主要交付 |
|---|---|---|
| `data` | 只处理附件和分析数据 | 处理后数据、质量报告、探索分析、复现脚本 |
| `model` | 只分析题目和建立模型 | 题目分析、基线结果、候选比较、模型合同 |
| `code` | 根据模型编写和运行代码 | 源码、结果、验证记录、复现清单 |
| `visualization` | 根据数据或结果制作图表 | 图表、源数据、生成脚本、图表清单 |
| `paper` | 根据已有模型和结果写论文 | Word 论文；按需生成 LaTeX/PDF |
| `full` | 从题面和附件完成全部工作 | 数据、模型、代码、图表、论文和复现材料 |

单阶段模式只补齐不可缺少的上游证据，不会擅自扩展为完整论文。

## 完整流程

```text
intake
→ data → D1
→ parse → research
→ baseline → B1
→ model → M1
→ prototype → P1
→ solve → validate → P2
→ evidence → W1
→ write → format → W2
→ package
```

支持独立 Agent 的环境可执行独立质检；不支持时按相同清单自审并明确标记 `LIMITED`，不能把自审写成独立验收。

## 安装

本功能目前位于仓库的 `cumcm-c-optimized` 分支。安装时必须指定该分支，并使用独立目录名，避免覆盖通用版。

### Codex

```powershell
git clone --branch cumcm-c-optimized --single-branch `
  https://github.com/niuniu513-ask/math-contest-assistant.git `
  "$env:USERPROFILE\.codex\skills\math-contest-assistant-c"
```

### Claude Code

```bash
git clone --branch cumcm-c-optimized --single-branch \
  https://github.com/niuniu513-ask/math-contest-assistant.git \
  ~/.claude/skills/math-contest-assistant-c
```

### Cursor

```bash
git clone --branch cumcm-c-optimized --single-branch \
  https://github.com/niuniu513-ask/math-contest-assistant.git \
  ~/.cursor/skills/math-contest-assistant-c
```

其他支持 Agent Skills 的工具同样应把该分支安装为 `math-contest-assistant-c`，并确保目录根部直接包含 `SKILL.md`。

## 使用

明确指定 skill 和工作范围最可靠：

```text
请使用 math-contest-assistant-c 完成这道国赛 C 题，只做数据预处理和探索分析。
```

```text
请使用 math-contest-assistant-c，根据已有数据完成题目分析、简单基线和模型选择，不写代码。
```

```text
请使用 math-contest-assistant-c，根据现有模型合同编写代码、运行求解并生成可视化。
```

```text
请使用 math-contest-assistant-c，根据已有模型、代码和真实结果完成 Word 论文。
```

```text
请使用 math-contest-assistant-c，从题面和附件开始运行 full 完整流程。
```

建议同时提供题面、附件、输出目录、剩余时间、期望格式，以及是否允许在 M1 后直接继续。完整模式默认在 M1 后提交模型方案并等待确认；用户预先明确授权时可记录授权后继续。

## 数据与模型原则

- 预处理必须说明发现、方法、依据、影响范围和对模型结论的影响。
- 每个子问题先运行简单基线；基线不一定写入正文，但必须保留结果。
- 不因模型名称高级、获奖论文使用过或可以增加公式数量而升级模型。
- 复杂模型必须与同口径基线比较关键指标、样本外表现、稳定性、运行成本和可解释性。
- 结果必须来自真实运行；禁止用示例、占位数据或人工填写指标冒充主模型输出。
- 当届官方规则和模板始终优先于本 Skill 的内部质量目标。

## 论文与排版

- 摘要原则上不超过一页，正文不生成目录。
- 正文 25–30 页是内部质量目标，不是官方要求，也不是注水依据。
- 公式必须形成从变量、假设、目标或方程、约束、求解到验证的完整推导链。
- 图表必须来自真实数据或结果，绑定明确主张和关键数值。
- 标题、正文、公式、图表标题、页码、参考文献和超链接显示文字统一为黑色。
- 彩色只用于确有信息区分需要的图表，并保证灰度打印可辨。
- 最终 Word 与 PDF 必须完成内容审计、样式审计和逐页视觉检查。

## 主要文件

```text
math-contest-assistant-c/
├── SKILL.md
├── 使用指南.md
├── references/
│   └── cumcm-c/
│       ├── C题自主解题协议.md
│       ├── 数据预处理与D1门禁.md
│       ├── 模型复杂度与基线.md
│       ├── C题论文结构与公式.md
│       └── C题Word排版规范.md
├── scripts/
│   ├── project_state.py
│   ├── c_gate_audit.py
│   ├── docx_style_audit.py
│   └── ...
├── tools/
│   ├── docx/
│   ├── latex/
│   ├── pdf/
│   ├── xlsx/
│   ├── paper_search/
│   └── humanizer-zh/
├── assets/
└── tests/
```

## 校验命令

```bash
python -m py_compile scripts/project_state.py scripts/c_gate_audit.py scripts/docx_style_audit.py
python scripts/c_gate_audit.py <PROJECT_ROOT> --gate D1
python scripts/c_gate_audit.py <PROJECT_ROOT> --gate B1
python scripts/docx_style_audit.py <FINAL.docx> --strict
```

`c_gate_audit.py` 检查门禁产物是否存在且非空；它不能替代数据内容、模型合理性和论文质量的人工或独立审查。

## 使用边界

Skill 生成的分析、代码、结果和论文需要参赛队人工核对、理解和改写。正式提交前必须确认数值、公式、引用、附件、匿名要求、文件大小和当届官方规则。该 Skill 不承诺竞赛成绩。

## License

MIT
