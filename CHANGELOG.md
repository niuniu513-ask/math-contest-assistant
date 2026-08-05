# Changelog

版本遵循语义化版本（SemVer）：`主版本.次版本.修订`。每次发布更新 `VERSION` 文件并在本文件追加记录；提交信息使用 conventional commits（`feat:`/`fix:`/`refactor:` 等，subject 简洁、≤72 字符、祈使语气，详细说明放正文）。

## [1.0.0] - 2026-08-05

首个正式版本。

- **语言策略**：Python 与 MATLAB 同等重要的一等实现路线，不设主路线/备选；进入编程前由 Agent 按评分卡（`references/语言选型对比.md`）对比选型，结论写入模型合同。
- **参考图统一 MATLAB**：参考图/示意图/流程图/技术路线图统一用 MATLAB 绘制（`MATLAB示意图绘制规范.md` + `apply_publication_style`），数据图仍用选定求解语言。
- **可选双轨交付**：同一题可同时交付 Python 与 MATLAB 两套实现，权威结果一致、统一驱动命令复现、P2 独立复算交叉核验。
- **完整 MATLAB 资产**：五类方法模板（`MATLAB代码生成规范.md`）、图表/配色/示意图规范、4 个 `.m` 出版脚本（`check_matlab_env`/`apply_publication_style`/`audit_publication_figure`/`export_publication_figure`）、国赛 Word 模板。
- **质量门禁**：W1/W2 写作台账、三台账（推导/决策/对标）、三重敏感性、工程裕度、深度档 `lean/standard/full`、验证装置超参 M1 冻结。
- **内容审计**：`paper_content_audit.py`（表号重号/悬空引用、正文策略与结果 CSV 交叉核对、DOCX 重复连续标题检测）。
