# 美国大学生数学建模竞赛（MCM/ICM）论文格式规范

## 基本结构

```
Title Page（标题页）
  - Team Control Number
  - Problem Chosen
  - Title
Summary Sheet（摘要页）
  - Summary（一页以内）
  - Keywords
Table of Contents（目录，可选但推荐）
正文
  - 1. Introduction
    - 1.1 Problem Background
    - 1.2 Restatement of the Problem
    - 1.3 Literature Review (optional)
  - 2. Assumptions and Justifications
  - 3. Notations and Terminology
  - 4. Models（按子问题分节）
    - 4.1 Model 1: ...
    - 4.2 Model 2: ...
  - 5. Sensitivity Analysis（或用专门一节）
  - 6. Model Evaluation
    - 6.1 Strengths
    - 6.2 Weaknesses and Limitations
    - 6.3 Future Improvements
  - 7. Conclusion
  - References
  - Appendices（可选）
    - Appendix A: Code
    - Appendix B: Additional Tables/Figures
  - 最后：Memorandum（MCM C 题）/ Letter（ICM 各题）
```

## 格式要求

### 页面设置
- 纸张：US Letter（8.5 × 11 inch）
- 页边距：上下 1 inch，左右 1 inch（约 2.54cm）
- 正文行距：单倍行距或 1.15 倍行距

### 字体与字号
| 元素 | 字体 | 字号 |
|------|------|------|
| 标题 | Times New Roman | 14-16pt Bold |
| 一级标题 | Times New Roman | 13pt Bold |
| 二级标题 | Times New Roman | 12pt Bold |
| 正文 | Times New Roman | 11-12pt |
| 图表标题 | Times New Roman | 10pt |
| 参考文献 | Times New Roman | 10pt |
| 代码（附录） | Courier New | 9-10pt |
| 摘要正文 | Times New Roman | 12pt |

### 图表
- 图标题在图下方，格式：`Figure X: Description`
- 表标题在表上方，格式：`Table X: Description`
- 图表编号全篇连续
- 倾向于彩色图表（美赛允许彩色）

### 公式
- 居中，编号右对齐：`(1)` `(2)`
- 使用 LaTeX 或 Equation Editor

### 参考文献
- 格式：APA 或 IEEE
- APA 示例：[1] Author, A. A. (Year). Title of work. Publisher.
- IEEE 示例：[1] A. Author, "Title," Journal, vol. x, no. x, pp. xx-xx, Year.

## 摘要页特殊要求

- Summary 标题（居中，Times New Roman 14pt Bold）
- 内容控制在 1 页以内
- 包含：问题简述 → 方法 → 主要结果（具体数值）→ 结论

## MCM/ICM 特殊要求

### MCM A题（连续型）
- 强调微分方程、优化、模拟等方法
- 必须有灵敏度分析

### MCM B题（离散型）
- 强调算法设计、图论、排队论等
- 复杂度分析重要

### MCM C题（大数据/数据洞察）
- 强调数据处理、特征工程、数据可视化
- 可交付 Memo/Report 形式的结果

### ICM D题（运筹学/网络科学）
- 强调网络分析、优化调度等

### ICM E题（环境科学）
- 强调科学建模、政策建议

### ICM F题（政策）
- 强调定量政策分析、影响评估

## 写作风格

- 使用第一人称复数 "we"（不用 "I" 或 "the author"）
- 主动语态优先（"We developed a model..." 而非 "A model was developed..."）
- 图表必须有实质性说明文字，不只是标题
- 过渡句自然流畅，引导读者阅读
