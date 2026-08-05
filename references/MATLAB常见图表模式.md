# MATLAB 常见图表模式

> 与 Python `常见模式.md` 等价的 MATLAB 图表实现。所有代码默认已执行
> `style = apply_publication_style(fig, "zh", "report")`。

## 三大可视化类别速查

| 类别 | 目的 | 推荐图表类型 | 产出阶段 |
|------|------|-------------|---------|
| **① 原始数据图** | 理解数据特征 | `histogram`、`boxplot`、`scatter`、`plot`、`heatmap` | 拿到数据后立即绘制 |
| **② 模型过程图** | 展示求解过程 | `plot`（收敛曲线）、`bar`（分组对比）、`scatter`（残差）、`confusionchart` | 模型运行中 |
| **③ 最终结果图** | 支撑核心结论 | `bar`（对比）、`plot`+`patch`（预测+CI）、`bubblechart`、`tiledlayout` 组合 | 求解完成后 |

文件名格式：`raw_q1_*`、`process_q1_*`、`result_q1_*`；每个子问题在三类中各至少 1 张。

---

## 一、柱状图

### 模式 1：分组柱状图

```matlab
function groupedBarChart(categories, dataDict, colors)
% GROUPEDBARCHART 分组柱状图：多方法对比
%   categories: 1×m string 数组
%   dataDict: struct，每个字段是一个 1×m 数值向量
arguments
    categories (1,:) string
    dataDict struct
    colors (:,:) double = []
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
hold on;

methodNames = fieldnames(dataDict);
nMethods = numel(methodNames);
nCats = numel(categories);
width = 0.8 / nMethods;
x = 1:nCats;

if isempty(colors); colors = style.colors; end

for i = 1:nMethods
    values = dataDict.(methodNames{i});
    offset = (i - nMethods/2 + 0.5) * width;
    bar(x + offset, values, width, ...
        "FaceColor", colors(i,:), "EdgeColor", "white", ...
        "LineWidth", 0.3, "DisplayName", methodNames{i});
end

set(gca, "XTick", x, "XTickLabel", categories);
legend("Location", "best", "FontSize", 6.5);
hold off;
export_publication_figure(fig, "figures/result_qN_groupedbar");
close(fig);
end
```

### 模式 2：堆叠柱状图

```matlab
function stackedBarChart(categories, parts, labels, colors)
% STACKEDBARCHART 堆叠柱状图：组成结构
%   parts: nParts×nCats 矩阵
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
hold on;

x = 1:numel(categories);
bottom = zeros(1, numel(categories));
for i = 1:size(parts, 1)
    bar(x, parts(i,:), 0.6, "Bottom", bottom, ...
        "FaceColor", colors(i,:), "EdgeColor", "white", ...
        "LineWidth", 0.3, "DisplayName", labels(i));
    bottom = bottom + parts(i,:);
end

set(gca, "XTick", x, "XTickLabel", categories);
legend("Location", "best", "FontSize", 6.5);
hold off;
export_publication_figure(fig, "figures/result_qN_stackedbar");
close(fig);
end
```

### 补充模式：点估计 + 区间（推荐替代矮胖柱状图）

```matlab
function dotEstimateChart(labels, values, lower, upper, color)
% DOTESTIMATECHART 点估计+区间图（优于少量类别的柱状图）
arguments
    labels (1,:) string
    values (1,:) double
    lower (1,:) double = []
    upper (1,:) double = []
    color (1,3) double = []
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
if isempty(color); color = style.colors(1,:); end
hold on;

y = 1:numel(labels);
if isempty(lower) || isempty(upper)
    plot(values, y, "o", "Color", color, "MarkerSize", 5, ...
        "MarkerFaceColor", color);
else
    xneg = values - lower;
    xpos = upper - values;
    errorbar(values, y, xneg, xpos, "horizontal", "o", ...
        "Color", color, "MarkerSize", 5, "MarkerFaceColor", color, ...
        "CapSize", 3, "LineWidth", 1);
end

set(gca, "YTick", y, "YTickLabel", labels, "YDir", "reverse");
xlabel("估计值");
hold off;
export_publication_figure(fig, "figures/result_qN_dotest");
close(fig);
end
```

---

## 二、折线图

### 模式 3：趋势 + 置信区间

```matlab
function trendWithCI(x, y, lowerCI, upperCI, color, labelStr)
% TRENDWITHCI 折线图 + 置信区间
arguments
    x (:,1) double
    y (:,1) double
    lowerCI (:,1) double
    upperCI (:,1) double
    color (1,3) double = []
    labelStr string = ""
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
if isempty(color); color = style.colors(1,:); end
hold on;

% 置信区间填充
xFill = [x; flipud(x)];
yFill = [upperCI; flipud(lowerCI)];
fill(xFill, yFill, color, "FaceAlpha", 0.12, "EdgeColor", "none", ...
    "DisplayName", "95% CI");

% 主线
p = plot(x, y, "Color", color, "LineWidth", 1.5);
if strlength(labelStr) > 0; p.DisplayName = labelStr; end

xlabel("x"); ylabel("y");
if strlength(labelStr) > 0; legend("Location", "best", "FontSize", 6.5); end
hold off;
export_publication_figure(fig, "figures/result_qN_trendci");
close(fig);
end
```

### 模式 4：多线对比

```matlab
function multiLineChart(x, dataDict, xlabelStr, ylabelStr)
% MULTILINECHART 多线对比
%   dataDict: struct，每个字段有 .y 和 .color
arguments
    x (:,1) double
    dataDict struct
    xlabelStr string = "x"
    ylabelStr string = "y"
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
hold on;

fn = fieldnames(dataDict);
for i = 1:numel(fn)
    d = dataDict.(fn{i});
    plot(x, d.y, "Color", d.color, "LineWidth", 1.5, "DisplayName", fn{i});
end

xlabel(xlabelStr); ylabel(ylabelStr);
legend("Location", "best", "FontSize", 6.5);
hold off;
export_publication_figure(fig, "figures/result_qN_multiline");
close(fig);
end
```

---

## 三、热力图

### 模式 5：相关性矩阵 / 数值热力图

```matlab
function matHeatmap(data, rowLabels, colLabels, cmap, cbarLabel, annot)
% MATHEATMAP 带可选标注的热力图
arguments
    data (:,:) double
    rowLabels (1,:) string = []
    colLabels (1,:) string = []
    cmap (1,:) char {mustBeMember(cmap, ...
        {'RdBu_r','viridis','parula','Blues','default'})} = 'RdBu_r'
    cbarLabel string = ""
    annot (1,1) logical = true
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");

if strcmp(cmap, "default"); cmap = "parula"; end

% 热搜图
h = heatmap(colLabels, rowLabels, data);
h.Colormap = feval(cmap, 256);
h.CellLabelFormat = "%.2f";
h.FontName = style.font;
h.FontSize = 7;

if ~annot; h.CellLabelColor = "none"; end

if strlength(cbarLabel) > 0
    h.ColorbarVisible = "on";
end

title("相关性矩阵");
export_publication_figure(fig, "figures/result_qN_heatmap");
close(fig);
end
```

### Z-score 偏差热图（手动颜色映射）

```matlab
function zscoreHeatmap(data, rowLabels, colLabels)
% ZSCOREHEATMAP 数据标准化后热力图
z = (data - mean(data, 1)) ./ std(data, 0, 1);

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");

imagesc(z);
colormap(redbluecmap(256));  % 自定义红蓝发散色图
cbar = colorbar;
cbar.Label.String = "Z-score";
cbar.Label.FontSize = 7;
clim([-2.5, 2.5]);

set(gca, "XTick", 1:numel(colLabels), "XTickLabel", colLabels, ...
    "YTick", 1:numel(rowLabels), "YTickLabel", rowLabels);

% 单元格标注
for i = 1:size(z,1)
    for j = 1:size(z,2)
        text(j, i, sprintf("%.2f", z(i,j)), ...
            "HorizontalAlignment", "center", "FontSize", 6, ...
            "Color", ternary(abs(z(i,j))>1.5, "white", [0.2 0.2 0.2]));
    end
end

export_publication_figure(fig, "figures/result_qN_zscoreheat");
close(fig);
end

function cm = redbluecmap(n)
    % 自定义红-白-蓝发散色图（替代 jet）
    x = linspace(0, 1, n)';
    r = min(max((1 - 2*abs(x-0.5))*2, 0), 1);
    g = min(max(1 - 2*abs(x-0.5), 0), 1);
    b = min(max((2*abs(x-0.5))*2, 0), 1);
    cm = [r g b];
end
```

---

## 四、散点图

### 模式 6：气泡图

```matlab
function bubbleChart3D(x, y, sizeVar, color, xlabelStr, ylabelStr)
% BUBBLECHART3D 气泡图：大小表示第三维
arguments
    x (:,1) double; y (:,1) double; sizeVar (:,1) double
    color (1,3) double = []; xlabelStr string = ""; ylabelStr string = ""
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
if isempty(color); color = style.colors(1,:); end

% 归一化气泡大小
sz = 30 + 70 * (sizeVar - min(sizeVar)) / (max(sizeVar) - min(sizeVar) + 1e-10);
scatter(x, y, sz, color, "filled", ...
    "MarkerEdgeColor", "white", "LineWidth", 0.3, "MarkerFaceAlpha", 0.7);

if strlength(xlabelStr) > 0; xlabel(xlabelStr); end
if strlength(ylabelStr) > 0; ylabel(ylabelStr); end
export_publication_figure(fig, "figures/result_qN_bubble");
close(fig);
end
```

### 模式 7：散点 + 拟合线 + 参考线

```matlab
function scatterWithFit(x, y, xlabelStr, ylabelStr)
% SCATTERWITHFIT 散点 + 线性拟合 + 象限分割
arguments
    x (:,1) double; y (:,1) double
    xlabelStr string = ""; ylabelStr string = ""
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
hold on;

% 散点
scatter(x, y, 18, style.colors(1,:), "filled", ...
    "MarkerEdgeColor", "white", "LineWidth", 0.2, "MarkerFaceAlpha", 0.55);

% 拟合线
p = polyfit(x, y, 1);
xLine = [min(x), max(x)];
plot(xLine, polyval(p, xLine), "-", "Color", style.colors(4,:), "LineWidth", 1.2);

% 中位数分割线
xline(median(x), "--", "Color", [0.5 0.5 0.5], "LineWidth", 0.8);
yline(median(y), "--", "Color", [0.5 0.5 0.5], "LineWidth", 0.8);

if strlength(xlabelStr) > 0; xlabel(xlabelStr); end
if strlength(ylabelStr) > 0; ylabel(ylabelStr); end
hold off;
export_publication_figure(fig, "figures/result_qN_scatterfit");
close(fig);
end
```

---

## 五、分布图

### 模式 8：箱线图 + 散点叠加

```matlab
function boxplotWithPoints(dataCell, groupLabels, colors)
% BOXPLOTWITHPOINTS 箱线图 + 原始数据点叠加
arguments
    dataCell cell
    groupLabels (1,:) string
    colors (:,:) double = []
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
if isempty(colors); colors = style.colors; end
hold on;

nGroups = numel(dataCell);
% 手动绘制（boxplot 函数在出版级设置下行为不稳定）
for i = 1:nGroups
    d = dataCell{i};
    q = prctile(d, [25 50 75]);
    iqr = q(3) - q(1);
    whiskerLo = max(min(d), q(1) - 1.5*iqr);
    whiskerHi = min(max(d), q(3) + 1.5*iqr);

    % 箱体
    rectangle("Position", [q(1), i-0.25, iqr, 0.5], ...
        "FaceColor", [colors(i,:) 0.25], "EdgeColor", colors(i,:)*0.7, ...
        "LineWidth", 0.8);

    % 中位线
    plot([q(2) q(2)], [i-0.25 i+0.25], "-", ...
        "Color", colors(i,:)*0.7, "LineWidth", 1.2);

    % 须线
    plot([whiskerLo q(1)], [i i], "-", "Color", colors(i,:)*0.7, "LineWidth", 0.8);
    plot([q(3) whiskerHi], [i i], "-", "Color", colors(i,:)*0.7, "LineWidth", 0.8);

    % 抖动散点
    jitter = (rand(size(d)) - 0.5) * 0.2;
    scatter(d, i + jitter, 10, colors(i,:), "filled", ...
        "MarkerEdgeColor", "white", "LineWidth", 0.1, ...
        "MarkerFaceAlpha", 0.4);
end

set(gca, "YTick", 0:nGroups-1, "YTickLabel", groupLabels);
ylabel("分组"); xlabel("值");
hold off;
export_publication_figure(fig, "figures/raw_qN_boxplot");
close(fig);
end
```

---

## 六、分类决策图

### PR 曲线

```matlab
function prCurve(recall, precision, prevalence, labelStr, color)
% PRCURVE PR 曲线 + 阳性率基线
arguments
    recall (:,1) double; precision (:,1) double
    prevalence (1,1) double
    labelStr string = ""; color (1,3) double = []
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
if isempty(color); color = style.colors(1,:); end
hold on;

plot(recall, precision, "Color", color, "LineWidth", 1.1, "DisplayName", labelStr);
yline(prevalence, "--", "Color", [0.5 0.5 0.5], "LineWidth", 0.8, ...
    "DisplayName", sprintf("阳性率基线 %.2f", prevalence));

xlabel("召回率"); ylabel("精确率");
xlim([0 1]); ylim([0 1]);
legend("Location", "best", "FontSize", 6.5);
hold off;
export_publication_figure(fig, "figures/result_qN_prcurve");
close(fig);
end
```

### 紧凑型 2×2 混淆矩阵

```matlab
function confusionMatrix2x2(matrix, classLabels)
% CONFUSIONMATRIX2X2 紧凑混淆矩阵（无冗余 colorbar）
arguments
    matrix (2,2) double
    classLabels (1,2) string = ["阴性", "阳性"]
end

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");

imagesc(matrix);
colormap(flipud(gray(256)));  % 白到黑：高值深色
hold on;

for i = 1:2
    rowTotal = sum(matrix(i,:));
    for j = 1:2
        ratio = matrix(i,j) / rowTotal;
        text(j, i, sprintf("%d\n%.1f%%", matrix(i,j), ratio*100), ...
            "HorizontalAlignment", "center", "FontSize", 7, ...
            "Color", ternary(matrix(i,j)>rowTotal/2, "white", [0.2 0.2 0.2]));
    end
end

set(gca, "XTick", [1 2], "XTickLabel", "预测"+classLabels, ...
    "YTick", [1 2], "YTickLabel", "真实"+classLabels);
title("混淆矩阵");
hold off;
export_publication_figure(fig, "figures/result_qN_confmat");
close(fig);
end
```

---

## 七、布局模式

### tiledlayout 非对称面板布局

MATLAB 的 `tiledlayout` 支持跨行列的网格，天然适合非对称布局：

```matlab
function asymmetricLayout()
% ASYMMETRICLAYOUT 主图+辅助证据的非对称布局
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "double");

% 创建 3×5 网格：主面板跨 3 行 3 列，辅助面板跨 3 行 2 列
t = tiledlayout(fig, 3, 5, "TileSpacing", "compact", "Padding", "compact");

% 主面板：左 3 列
ax1 = nexttile([3 3]);
% ... 绘制主图 ...

% 辅助面板：右 2 列，上中下各 1 行
ax2 = nexttile([1 2]);  % 上
% ... 辅助图 1 ...
ax3 = nexttile([1 2]);  % 中
% ... 辅助图 2 ...
ax4 = nexttile([1 2]);  % 下
% ... 辅助图 3 ...

title(t, "综合结果展示");
export_publication_figure(fig, "figures/result_qN_asymmetric");
close(fig);
end
```

### 面板编号与统计标注

```matlab
function addPanelLabelsMATLAB(axArray)
% ADDPANELLABELSMATLAB 统一面板编号 a, b, c...
arguments
    axArray (1,:) matlab.graphics.axis.Axes
end
labels = {'a','b','c','d','e','f','g','h'};
for i = 1:numel(axArray)
    text(axArray(i), axArray(i).XLim(1), axArray(i).YLim(2), ...
        labels{i}, "FontSize", 8, "FontWeight", "bold", ...
        "VerticalAlignment", "top", "HorizontalAlignment", "left");
end
end

function addStatLabel(ax, statText)
% ADDSTATLABEL 添加统计标注（右上角）
text(ax, 0.02, 0.98, statText, "Units", "normalized", ...
    "FontSize", 7, "Color", [0.3 0.3 0.3], ...
    "VerticalAlignment", "top", "FontAngle", "italic");
end
```

### 图例专用区域

```matlab
function legendAxis = createSharedLegend(axMain, axLegend)
% CREATESHAREDLEGEND 将图例放在独立坐标轴区域
set(axLegend, "Visible", "off");
% 收集 axMain 中的所有 DisplayName
lines = findobj(axMain, "-property", "DisplayName");
handles = lines(arrayfun(@(l) strlength(l.DisplayName) > 0, lines));
legend(axLegend, handles, "Location", "west", "FontSize", 6.5, "Box", "off");
end
```

---

## 八、L*a*b 亮度判断辅助

```matlab
function textColor = luminanceTextColor(bgColor)
% LUMINANCETEXTCOLOR 根据背景色返回高对比文字颜色
%   bgColor: 0-1 范围的 RGB 三元组
L = 0.299*bgColor(1) + 0.587*bgColor(2) + 0.114*bgColor(3);
if L < 0.5
    textColor = [1 1 1];     % 白色文字
else
    textColor = [0.2 0.2 0.2]; % 深灰文字
end
end
```

---

## 九、图表类型速查（MATLAB 函数映射）

| 展示内容 | Python 模式 | MATLAB 等效函数 |
|---------|------------|----------------|
| 多方法多指标对比 | 模式 1：分组柱状图 | `bar(x+offset, values, width)` |
| 总量组成结构 | 模式 2：堆叠柱状图 | `bar(..., "Bottom", bottom)` |
| 随时间变化趋势 | 模式 3：趋势+CI | `plot` + `fill(xFill, yFill, ...)` |
| 多方法收敛速度 | 模式 4：多线对比 | `plot(x, y1); hold on; plot(x, y2)` |
| 变量相关性 | 模式 5：热力图 | `heatmap` 或 `imagesc` |
| 三维变量关系 | 模式 6：气泡图 | `scatter(x, y, sz, c, "filled")` |
| x-y 相关性+拟合 | 模式 7：散点+拟合 | `scatter` + `polyfit` + `plot` |
| 数据分布对比 | 模式 8：箱线图 | 手动 `rectangle` + `scatter` |
| 分类性能 | PR 曲线 | `plot(recall, precision)` + `yline` |
| 少量参数估计 | 点估计+区间 | `errorbar(..., "horizontal")` |
| 主次证据组合 | 非对称 tiledlayout | `tiledlayout(m, n)` + `nexttile([r c])` |
| 图例太多 | 独立图例区 | `legend(axLegend, ...)` |
| 面板编号 | add_panel_labels | 手动 `text(ax, ...)` |
