# Changelog

版本遵循语义化版本（SemVer）：`主版本.次版本.修订`。每次发布更新 `VERSION` 文件并在本文件追加记录；提交信息使用 conventional commits（`feat:`/`fix:`/`refactor:` 等，subject 简洁、≤72 字符、祈使语气，详细说明放正文）。

## [1.4.7] - 2026-08-14

修复无 latexmk 环境下含外部文献库项目无法构建的问题，并恢复 v1.3 同款稳健中文字体选择。

- **fix**：`latex_paper.py build` 未找到 latexmk 时不再拒绝含 BibTeX/BibLaTeX 的项目，自动回退为“引擎 → bibtex/biber → 引擎 ×2”（bibtex/biber 在 `build/` 目录执行），解决 2021B 这类交付在本机无 Perl 环境无法 `build` 的问题。
- **fix**：`code-generation-guide.md` 公共代码头的中文字体从静态列表改为**动态选择已安装字体**（SimHei/YaHei/Noto Sans CJK 等优先，v1.3 同款逻辑），未检测到中文字体时警告并要求报告 BLOCKED，避免缺字体机器上图表文字乱码/缺字。
- **fix**：图表文字语言规则从“中文题必须全中文”调整为“可读中英文均可、同一图内尽量一致”，核心约束改为禁止变量名/列名/聚类标签直接当图例（如 `highK`、`Cluster_0`、`PC1`），保留乱码/缺字检查。
- **docs**：`可视化规范.md` 补充“中文字体动态选择 + 导出前缺字检查”；`tools/latex/SKILL.md`、`LaTeX格式规范-new.md` 同步无 latexmk 回退说明。

## [1.4.6] - 2026-08-13

修复中文竞赛图例/图内文字英文问题，并消除示例骨架与“图内不写标题”规则的矛盾。

- **fix**：`code-generation-guide.md` 把“图例与论文语言一致”升级为硬规则：中文竞赛图内文字（坐标轴/刻度/图例/注释/面板编号）必须全中文，禁止直接把英文列名、变量名、聚类标签（`highK`、`Cluster_0`、`PC1` 等）当图例，须先做中文映射；美赛全英文。
- **fix**：删除示例骨架中全部 `set_title`/`suptitle` 残留（8 处），与“标题由论文 `\caption{}` 承担”规则一致，避免模型照抄示例。
- **docs**：`可视化规范.md`、`图表选择与避坑.md` 补充图内语言与“英文列名直接上 legend”避坑；`论文自审框架.md` W1/W2 清单新增图内文字语言抽检项。

## [1.4.5] - 2026-08-13

恢复国赛正文篇幅质量档（20~25 页）并强化论文质量门禁。

- **feat**：CUMCM 内部质量档定为正文（不含附录）20~25 页（官方 2026 上限 30）：`latex_paper.py` 的 `--quality-checks` 默认 `min_pages=20`、`max_pages=25`、`min_equations=15`、`min_figures=12`；超过 25 页需显式放宽并附 `--override-reason`。
- **docs**：`论文结构硬性要求.md`、`paper-format-cumcm.md`、`论文写作工作流.md`、`论文格式规范-word.md`、`深度写作与竞争力门禁.md`、`论文自审框架.md`、`LaTeX格式规范-new.md`、`tools/latex/SKILL.md`、SKILL.md 同步“20~25 页内部质量档 + 官方 30 页上限”口径，并把“每问至少 1 幅结果图、全篇 ≥12 图、公式 ≥15”写进写作预算与 W2 检查。

## [1.4.4] - 2026-08-12

吸取 Mrite 项目经验，落地四项可执行规范：公共代码头、求解计划模板、摘要三类模板、表格防溢出规则。

- **feat**：`code-generation-guide.md` 新增“公共代码头与两阶段执行（强制基线）”：Python 公共头（UTF-8 中文输出、matplotlib 跨平台中文字体、`save_fig`/`save_csv` 统一落盘）、先算后画两阶段（计算阶段打印 min/max/mean/std/CV/amplitude 供论文引用，绘图阶段不写 `set_title`）。
- **feat**：新增 `references/求解计划模板.md`（六段式：总体方向/各题思路+方法匹配表/输出标准/操作步骤/文件清单/异常预案）与对话内计划状态列表（✅/🔄/⏳，每步完成重输出完整列表）；`建模工作流程.md`、`自主解题协议.md`、SKILL.md 分阶段加载表同步接入。
- **feat**：`论文写作工作流.md` 新增摘要三类模板（有数据建模型/无数据机理优化/建议总结）+ 编译后一页校验（LaTeX 用 `abstract:end` 标签读页码，Word 渲染后检查独占一页）。
- **feat**：`LaTeX格式规范-new.md` 新增表格防溢出规则：全宽/跨页表统一 `longtable` + `>{\centering\arraybackslash}p{}`，列宽比例总和 = 1.04 − 0.04×N，`caption/label/\\` 固定写法与 `endfirsthead/endhead/endfoot` 结构，编译后复查 Overfull。

## [1.4.3] - 2026-08-11

修复结构审计与 DOCX 公式转换在真实 2022C 重构中的缺口。

- **fix**：`paper_content_audit.py` 摘要标题支持“摘 要”带空格写法；章节编号支持多级（6.4）；“问题间关联分析”接受编号小节；门禁词 P1/P2 匹配改为大小写敏感（避免把 `p1_slice.py` 文件名误报）；表格解读层接受“特征”关键词。
- **fix**：`equations.py generate`（Markdown→DOCX）自动把 `\(...\)`/`\[...\]` 转为 `$...$`/`$$...$$` 后再交给 Pandoc（跳过代码围栏），解决 Pandoc 不识别单反斜杠公式导致 DOCX 出现纯文本公式的问题。
- **docs**：DOCX 管线说明同步“Pandoc 数学分隔符由工具自动归一化”的约定。

## [1.4.2] - 2026-08-11

重审并调整论文结构要求：修复结构检查失效 bug、放宽真实标题变体、物理/工程小节按题可选。

- **fix**：`paper_content_audit.py` 的 `audit_paper_structure` 结果此前被下一行赋值覆盖（结构门禁形同失效），现并入 `audit_text` 与 CLI 输出。
- **feat**：结构检查支持真实标题变体——中文编号“一、”/“1.”均可，问题分析可单独或并入重述，模型假设与符号说明可合并或分列，结果部分接受“结果分析/结果分析与讨论/模型检验”，灵敏度接受“敏感性/稳健性分析”。
- **fix**：严格门禁的“物理目标与优化目标”“工程裕度”小节改为按模型台账条件要求：仅当台账含物理目标/直接物理目标实验或工程裕度证据时才强制，统计/数据题不再被迫写物理题专用小节。
- **docs**：重写 `references/论文结构硬性要求.md`（必需结构 + 允许变体、CUMCM 2026 页数/摘要/附录约束、去掉与 2026 冲突的 15~25 页下限、字体字号与格式基线对齐）；同步 `章节模板.md`、`论文写作工作流.md`、`paper-format-cumcm.md`。
- **test**：完整夹具补齐为完整论文结构，覆盖新的必需章节与顺序门禁。

## [1.4.1] - 2026-08-11

统一 LaTeX 模板文字颜色、摘要加粗、表格居中，并补齐 2026 附录清单要求。

- **fix**：`cumcm-jayxin` 模板代码环境（listings）关键字/注释/字符串改为黑色，正文与链接本就为黑色，全篇文字颜色统一。
- **fix**：`table`/`table*` 环境自动 `\centering`，示例章节把 `\centering` 移到题注前，解决表格左偏/题注未随表居中问题。
- **feat**：摘要示例展示关键结果加粗写法（中文 `\heiti{}`、英文/数字 `\textbf{}`），并在格式规范中明确要求。
- **feat**：新增附录 `contents/appendix/a0.tex`（支撑材料文件列表三线表占位），`main.tex` 接入；无支撑材料/未用程序的注明要求写入规范。
- **docs**：`paper-format-cumcm.md`、`LaTeX格式规范-new.md`、`论文结构硬性要求.md` 同步补充文字颜色、表格居中、摘要加粗与附录完整清单要求。

## [1.4.0] - 2026-08-11

新增 jayxin/cumcm 完整 CUMCM LaTeX 模板，并按 2026 官方修订稿校准格式依据。

- **feat**：内置 `tools/latex/assets/templates/cumcm-jayxin/`（github.com/jayxin/cumcm v1.1.0，基于 latexstudio/CUMCMThesis 重组），含 `commons/cumcmthesis.cls`、承诺书/编号专用页、自带 Times/Arial 字体、2026 第一次通知与 2019/2026 格式规范 PDF；`init` 支持 `--template cumcm-jayxin` 按名引用。
- **feat**：`latex_paper.py init` 支持以模板名（`cumcm-jayxin`/`cumcm`/`mcm-icm`）代替完整路径解析内置模板。
- **docs**：`references/paper-format-cumcm.md` 按 2026 修订稿校准（纸质/电子版前言规则、正文上限 30 页、附录与支撑材料要求）；`references/LaTeX格式规范-new.md` 与 `tools/latex/SKILL.md` 登记新模板用法、类选项（`withoutpreface`/`bwprint`/`draft`）及 MiKTeX latexmk 依赖 Perl 的说明。
- **test**：用 MiKTeX + XeLaTeX 实测 jayxin 模板电子版（`withoutpreface`）与纸质版（含承诺书/编号页）均编译通过。

## [1.3.1] - 2026-08-11

质量与文档维护：修复断链、删除重复目录、校准 README、补充冒烟测试。

- **fix**：`论文结构硬性要求.md` 引用不存在的 `apply_cumcm_format.py`，改为指向 `tools/docx/scripts/paper_format.py`。
- **fix**：`tools/docx/scripts/self_check.py` 模板路径适配本仓库（`tools/docx/templates/论文模板.docx`），环境变量改为 `MATH_CONTEST_ASSISTANT_ROOT`。
- **fix**：`scripts/schematic_pptx.py` 修复 `save(export_png=False)` 把 `False` 当导出路径的缺陷；命令行支持 `--help`。
- **docs**：SKILL.md 分阶段加载表补全 14 个未路由参考文档与 3 个脚本；`references/前置合同.md` 更名 `references/模型合同.md`。
- **chore**：删除与 `tools/docx/scripts` 重复且已分化的 `tools/scripts` 目录（64 个文件）。
- **docs**：README 数据校准（41 个参考文档、20 类代码模板、15 个脚本等），补充 MIT LICENSE。
- **test**：新增 `test_smoke.py`（状态机、复现清单、AI 检测 CLI、物理示意图），与既有审计测试合并运行。

## [1.3.0] - 2026-08-06

新增**物理示意图能力**（PowerPoint + python-pptx，代码生成、可复现）。

- **为什么 PPT 而非 Visio**：物理示意图（坐标/光线/矢量/角度/受力/场）是几何关系示意，PPT 自由绘制适配、python-pptx 可编程可复现；Visio 面向工程图且多数环境未装。
- **新增 `scripts/schematic_pptx.py`**：模板原语（line/arrow/ray/axes/arc/mirror/tower/circle/text），逻辑坐标自动映射，导出 PNG(约300dpi) + PPTX 矢量源；内置定日镜反射示例（法向=入射/反射角平分、镜面倾角=法向-90°）。
- **新增 `references/物理示意图绘制规范.md`**：工具选择判据、几何正确性要求、配色/线宽/标注规范、复用与复现、依赖与降级（无 PowerPoint 时标记 BLOCKED）。
- **SKILL.md**：分阶段加载表新增物理示意图入口；语言选型段落补充"物理示意图用 PPT+python-pptx"。

## [1.2.0] - 2026-08-06

新增**论文结构硬性要求**与审计自动执行，并修复章节式表号误报（源自 2023 CUMCM A 定日镜场实战复盘）。

- **表号解析支持章节式/附录式编号（fix）**：`paper_content_audit.py` 三处表号正则升级为 `(?:[A-Za-z]+-)?\d+(?:-\d+)?`，支持顺序编号(表1)、按章编号(表3-1)、附录编号(表A-1)，消除"按章编号被误判为表号重复/未编号"的误报。
- **硬性结构检查（feat）**：新增 `audit_paper_structure()`，自动检查 9 大必需章节齐全且顺序正确、摘要独立一页（关键词后须有分页标记）、模型优缺点各 ≥4 条、改进方案存在、正文至少一次引用附录；附录引用正则收紧避免"附录DNI"等误报。
- **新增 `references/论文结构硬性要求.md`**：强制性章节顺序、排版格式（A4/2.5cm/字号表）、图表按章编号、公式"主体居中+编号右对齐"、附录硬性要求（必须放/绝对不能放/正文引用/A-N编号）。
- **新增 `references/避坑指南.md`**：实战踩坑合集（字符转义 ``/``、审计 vs pandoc 双源格式、pandoc `	ag`/`
ewpage`、后台输出缓冲、代理子集偏差、结构卫生、MATLAB 降级）。

## [1.1.0] - 2026-08-05

新增**代码纪律（强制）**，约束生成代码不炫技、不堆叠、合理规范，并强制求解使用主模型。

- **求解必须用主模型**：目标函数/方程/约束/参数直接取自 `.work/model-contract.json` 的主模型，`最优解`与核心结果必须是该主模型的真实运行输出，禁止用通用示例、罐头模板、占位模型或备选模型冒充（`SKILL.md` §7）。
- **能简不繁、不炫技**：优先成熟库函数，一个脚本一个子问题；方法复杂度与问题需要匹配，删除不承担明确功能的算法/图表；明确 `code-generation-guide.md` / `MATLAB代码生成规范.md` 为教学片段，按当前模型裁剪，不得整套套用强制骨架。
- **规模合理、可解释**：单脚本一般不超过 200 行，超过时拆模块；交付代码必须能被团队成员逐行解释并在答辩中复述。
- **门禁强化**：P1 增加"最小链路实现主模型而非占位模型"检查；P2 增加"代码以实现主模型为准""代码简洁规范无炫技"两项；完成判定新增代码纪律条目。违反代码纪律在 P2 判 `FAIL`。

## [1.0.0] - 2026-08-05

首个正式版本。

- **语言策略**：Python 与 MATLAB 同等重要的一等实现路线，不设主路线/备选；进入编程前由 Agent 按评分卡（`references/语言选型对比.md`）对比选型，结论写入模型合同。
- **参考图统一 MATLAB**：参考图/示意图/流程图/技术路线图统一用 MATLAB 绘制（`MATLAB示意图绘制规范.md` + `apply_publication_style`），数据图仍用选定求解语言。
- **可选双轨交付**：同一题可同时交付 Python 与 MATLAB 两套实现，权威结果一致、统一驱动命令复现、P2 独立复算交叉核验。
- **完整 MATLAB 资产**：五类方法模板（`MATLAB代码生成规范.md`）、图表/配色/示意图规范、4 个 `.m` 出版脚本（`check_matlab_env`/`apply_publication_style`/`audit_publication_figure`/`export_publication_figure`）、国赛 Word 模板。
- **质量门禁**：W1/W2 写作台账、三台账（推导/决策/对标）、三重敏感性、工程裕度、深度档 `lean/standard/full`、验证装置超参 M1 冻结。
- **内容审计**：`paper_content_audit.py`（表号重号/悬空引用、正文策略与结果 CSV 交叉核对、DOCX 重复连续标题检测）。
