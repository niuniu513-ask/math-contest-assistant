# 学术公式规范

## LaTeX 数学公式排版规范

### 变量
- 单个字母变量：斜体 `$x$`, `$y$`, `$t$`
- 多个字母的变量名：直立（用 `\mathrm{}`），如 `$\mathrm{Re}$`（雷诺数）
- 希腊字母：斜体 `$\alpha$`, `$\beta$`, `$\theta$`（作为变量时）

### 向量与矩阵
- 向量：粗斜体 `$\mathbf{v}$` 或带箭头 `$\vec{v}$`
- 矩阵：粗体大写 `$\mathbf{A}$`, `$\mathbf{X}$`
- 单位矩阵：`$\mathbf{I}$`
- 转置：`$\mathbf{A}^{\mathrm{T}}$`

### 函数与运算符
- 标准函数：直立（LaTeX 内置）
  - `$\sin x$`, `$\cos x$`, `$\ln x$`, `$\log x$`, `$\exp(x)$`
  - `$\max$`, `$\min$`, `$\arg\max$`, `$\arg\min$`
- 自定义运算符：`$\operatorname{Var}$`, `$\operatorname{Cov}$`

### 导数与积分
- 导数：`$\frac{\mathrm{d}y}{\mathrm{d}x}$`（d 直立）
- 偏导数：`$\frac{\partial f}{\partial x}$`
- 积分：`$\int_{0}^{\infty} f(x)\,\mathrm{d}x$`

### 上下标
- 变量下标：斜体 `$x_i$`, `$x_{ij}$`
- 描述性下标：直立 `$x_{\mathrm{max}}$`, `$P_{\mathrm{out}}$`

### 数与单位
- 数字：直立（默认）
- 单位：直立，用 `\mathrm{}` 或 `\text{}`
  - `$v = 3.0 \times 10^8 \, \mathrm{m/s}$`
  - 数字与单位间加小空格 `\,`

### 括号
- 基本：`$(x)$`, `$[x]$`
- 自适应大小：`$\left( \frac{a}{b} \right)$`
- 花括号需要转义：`$\{x\}$`
- 分段函数：
  ```latex
  f(x) = \begin{cases}
    x^2, & x \geq 0 \\
    -x^2, & x < 0
  \end{cases}
  ```

### 常见符号速查

| 含义 | LaTeX | 说明 |
|------|-------|------|
| 求和 | `\sum_{i=1}^{n}` | 上下标在行内公式中显示在右侧 |
| 求积 | `\prod_{i=1}^{n}` | 同上 |
| 极限 | `\lim_{x \to \infty}` | |
| 属于 | `\in` | |
| 任意 | `\forall` | |
| 存在 | `\exists` | |
| 实数集 | `\mathbb{R}` | |
| 自然数集 | `\mathbb{N}` | |
| 约等于 | `\approx` | |
| 正比于 | `\propto` | |
| 偏导 | `\partial` | |
| 无穷 | `\infty` | |
| 梯度/算子 | `\nabla` | |

## 论文中的公式呈现

### 行内公式
短公式放在正文行内，用 `$...$` 包围。

### 独立公式
重要公式单独成行，居中对齐。Markdown 源使用 `\[...\]`，完整 LaTeX 项目使用 `\begin{equation}...\end{equation}` 或 `align`；禁止使用 `$$...$$`：
```latex
\begin{equation}
  \min_{x} \quad f(x) = \sum_{i=1}^{n} (y_i - \hat{y}_i)^2
  \label{eq:objective}
\end{equation}
```

### 多行公式对齐
```latex
\begin{align}
  a &= b + c \\
  d &= e + f + g \nonumber \\
  h &= i + j
\end{align}
```
- `\\` 换行
- `&` 对齐点
- `\nonumber` 取消编号

### 公式引用
- 使用 `\label{...}` 和 `\ref{...}` / `\eqref{...}`:
  - "如公式(\ref{eq:objective})所示..."
  - "由\eqref{eq:objective}可得..."

### 公式后标点
- 若公式是句子的组成部分，公式后加逗号或句号
- 若公式独立构成完整句子，公式后不加标点

## DOCX 中呈现公式

在 DOCX 中生成公式有两种方式：

### 方式 A：使用 python-docx 插入 OMML（推荐）
- 支持原生 Word 公式编辑
- 需要将 LaTeX 公式转换为 OMML
- 使用 `latex2omml` 库或手动构建 OMML XML

### 方式 B：使用 LaTeX 渲染为图片嵌入
- 适合复杂公式
- 缺点是放大后会模糊
- 需要 MathJax/KaTeX 或 LaTeX 发行版

### 方式 C：使用 Unicode + 上下标（简单但有限）
- `x²`、`α`、`∑ᵢ₌₁ⁿ`
- 仅适合极简单的公式

SKILL 默认使用**方式 A**，复杂公式可降级为**方式 B**。
