# MATLAB 实现规范

MATLAB 与 Python 是同等支持的实现语言，不把 MATLAB 作为仅供参考的附录。本文件只收录 MATLAB 内置函数或已发布工具箱中的真实接口，不使用未随 skill 交付的脚本。

## 环境与依赖

用真实命令检查工具箱，不假设存在任何脚本：

```text
matlab -batch "disp(ver('Statistics_Toolbox')); disp(license('test','Optimization_Toolbox'))"
```

| 功能 | 真实接口 | 所属 |
|---|---|---|
| 线性/非线性/整数优化 | `lsqcurvefit`、`fmincon`、`intlinprog` | Optimization Toolbox |
| 非线性模型拟合 | `fitnlm`、`fit`（库模型） | Statistics and ML Toolbox |
| 回归/分类/聚类 | `fitlm`、`fitglm`、`glmfit`、`TreeBagger`、`fitcknn`、`kmeans` | Statistics and ML Toolbox |
| 时间序列与计量 | `arima`、`adftest`、`autocorr` | Econometrics Toolbox |
| 符号推导 | `syms`、`solve`、`diff`、`simplify` | Symbolic Math Toolbox |
| 矩阵/图论/基础可视化 | `pca`、`graph`、`shortestpath`、`plot` | 基础环境 + Statistics |

只检查选中功能对应的工具箱，不默认要求全部，也不因缺少未使用工具箱而阻断。

## 代码结构

```matlab
function main(seed)
arguments
    seed (1,1) double = 42
end
rng(seed, "twister");

projectRoot = fileparts(mfilename("fullpath"));
data = readtable(fullfile(projectRoot, "data", "input.csv"));
result = solveModel(data);
writetable(result.table, fullfile(projectRoot, "results", "问题1_结果.csv"));
end
```

- 用 `fullfile` 构造路径，不依赖当前工作目录；`arguments` 校验输入。
- 随机算法调用 `rng(seed, "twister")`；`readtable`/`writetable` 走表，`readmatrix`/`writematrix` 走矩阵。
- 优化结果必须检查 `exitflag`/`output.iterations` 与约束残差。
- ≥3 个独立子问题按问题拆分函数文件（`q1.m`、`q2.m`…），主脚本只做调度，避免单文件堆积千行。
- MATLAB 工具箱函数随版本更名（如 `zscore`、`TreeBagger` 在部分版本位于 Statistics Toolbox），`ver` 记录实际版本。

## 常用赛题流程的 MATLAB 配方

以下模式覆盖国赛常见环节，均可直接用内置函数实现：

- **按分组交叉验证（无内置 GroupKFold）**：对组标签取唯一值，按组序号手工折分，保证同一组的全部行只进训练折或验证折；内层调参对训练折内的组再次折分。留一验证即每折只留一组。
- **bootstrap 按组重采样**：`groups = unique(table.g);` 后 `ridx = randsample(numel(groups), numel(groups), true);` 按 `groups(ridx)` 拼接成重采样表；循环内重训模型。
- **形状保持插值优化**：`pchip(x, y, xq)`（内置）或 `interp1(x, y, xq, 'pchip')`；对转化率与选择性分别插值后相乘得到收率，并在每配方实测温域内细网格扫描。
- **随机森林**：`TreeBagger(nTrees, X, y, 'Method','regression', 'MinLeafSize', k, 'NumPredictorsToSample', 'all')`；树间分歧用 `oobPredict` 或逐树预测的标准差估计。
- **广义加性近似**：用 `spline` 构造温度样条基列，连同其他连续变量经 `zscore` 后交给 `ridge` 或 `fitlm`；预测经 `logit`/`invlogit` 变换（`logit`、`1./(1+exp(-z))`）。
- **非线性失活/动力学拟合**：`fitnlm` 或 `lsqcurvefit` 拟合 `X(t)=Xinf+A*exp(-k*t)`；AICc/留一误差手工循环计算。
- **相关性**：`corr(x, y, 'Type', 'Spearman')`。
- **PCA 与标准化**：`zscore`、`pca`；`ecdf` 画累积分布。
- **历史回测**：掩蔽点循环 + `randsample`；把策略权重与接受阈值写入 `model-contract.json` 后再运行，禁止事后反推权重。

## 结果与复现

记录 MATLAB `version`、`ver` 中实际用到的工具箱、随机种子、输入 SHA-256、参数和唯一命令，例如 `matlab -batch "main(42)"`。生成清单：

```powershell
python "<SKILL_ROOT>/scripts/repro_manifest.py" `
  --project-root "<PROJECT_ROOT>" --seed 42 `
  --runtime matlab --runtime-version "R2025b" `
  --dependencies '{"Statistics and Machine Learning Toolbox":"25.2"}' `
  --command 'matlab -batch "main(42)"'
```

## 出版级绘图

- 统一中文字体与色觉友好配色在 `main` 开头用 `set(groot, "DefaultAxesFontName", "SimHei")` 等设置；绘图前完成数据剖析、单图核心结论与图表契约。
- 导出用真实内置接口：`exportgraphics(fig, "fig.png", "Resolution", 300)`（R2020a+），可编辑源用 `print(fig, "-dsvg", "fig.svg")`；旧版本用 `print(fig, "-dpng", "-r300", "fig.png")`。
- 导出后运行语言无关的 `figure_audit.py` 做结构与尺寸检查，再实际打开 PNG 检查缺字、刻度重叠、遮挡与多面板一致性。
- 主结论与辅助证据信息量不同时用非对称 `tiledlayout`，不机械创建等宽双子图。
- 确有数值意义的参考线用 `xline`/`yline` 并在图注说明，不调用 `grid on`。

## 与审计工具衔接

`figure_audit.py`、`paper_content_audit.py`、`repro_manifest.py` 只读取图文件、规范化 Markdown 与结果 CSV，与实现语言无关；MATLAB 路线同样必须通过相同门禁。
