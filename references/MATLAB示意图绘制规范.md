# MATLAB 示意图绘制规范

> 论文中需要流程图、框图、系统架构、几何示意图、算法流程图等非数据图时，
> 优先使用 MATLAB 而非外部工具绘制，以保证字体、颜色、尺寸与数据图统一。

## 一、何时用 MATLAB 画示意图

| 示意图类型 | 适用场景 | 核心函数 |
|-----------|---------|---------|
| 算法流程图 | 模型求解步骤、决策逻辑 | `annotation` + `rectangle` + `text` |
| 系统架构框图 | 多模块协作、数据流 | `rectangle` + `quiver` + `text` |
| 几何/物理示意图 | 问题场景、坐标系统 | `patch` + `plot` + `fill` + `text` |
| 网络拓扑图 | 节点关系、路径规划 | `graph`/`digraph` + `plot` |
| 层次结构图 | 指标体系、分类树 | `rectangle` + `line` + `text` |
| 时间线/甘特图 | 任务调度、工序安排 | `barh` + `xline` + `text` |

## 二、通用原则

1. **与数据图统一风格**：调用 `apply_publication_style()` 设置字体、颜色基线；不另起一套视觉语言。
2. **矢量输出**：使用 `export_publication_figure()` 导出 SVG + PNG；禁止截图。
3. **LaTeX 兼容**：标签中的数学符号使用 LaTeX 格式，设置 `Interpreter="latex"`。
4. **色觉友好**：使用 `apply_publication_style` 返回的 `style.colors` 色板；不用高饱和纯色。
5. **最小标注**：只标注论文中会讨论的关键节点/流程；不把全部实现细节堆在图上。
6. **可编辑文本**：所有文字使用 `text()` 而非在位图软件中后期添加。

## 三、算法流程图

```matlab
function drawAlgorithmFlowchart(projectRoot)
% DRAWALGORITHMFLOWCHART 绘制算法流程图
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "double");
hold on;
axis equal off;

% 定义节点位置 — 使用归一化坐标 [x, y, width, height]
nodes = struct();
nodes.start    = [0.45, 0.92, 0.10, 0.05];  % 开始
nodes.load     = [0.45, 0.82, 0.10, 0.05];  % 加载数据
nodes.preproc  = [0.45, 0.70, 0.10, 0.05];  % 数据预处理
nodes.check    = [0.45, 0.56, 0.10, 0.05];  % 异常检测
nodes.model    = [0.20, 0.38, 0.14, 0.08];  % 核心模型
nodes.optim    = [0.55, 0.38, 0.14, 0.08];  % 参数优化
nodes.verify   = [0.37, 0.20, 0.26, 0.08];  % 模型验证
nodes.output   = [0.45, 0.06, 0.10, 0.05];  % 输出结果

% 绘制节点（圆角矩形效果用 rectangle + Curvature）
fn = fieldnames(nodes);
for i = 1:numel(fn)
    pos = nodes.(fn{i});
    if pos(3) > 0.12  % 宽节点 — 核心步骤
        rectangle("Position", pos, "Curvature", 0.1, ...
            "FaceColor", [0.9 0.95 1], "EdgeColor", style.colors(1,:), "LineWidth", 1.2);
    else  % 普通节点
        rectangle("Position", pos, "Curvature", 0.15, ...
            "FaceColor", [0.95 0.95 0.95], "EdgeColor", [0.3 0.3 0.3], "LineWidth", 0.8);
    end
    % 标签
    labels = struct(...
        "start", "开始", "load", "加载附件数据", ...
        "preproc", "数据预处理", "check", "异常值检测与处理", ...
        "model", "核心模型求解", "optim", "参数优化\n(PSO/GA)", ...
        "verify", "模型验证与灵敏度分析", "output", "输出结果与图表");
    text(pos(1)+pos(3)/2, pos(2)+pos(4)/2, labels.(fn{i}), ...
        "HorizontalAlignment", "center", "FontSize", 7, "FontName", style.font);
end

% 绘制箭头
arrowOpts = {"HeadWidth", 5, "HeadLength", 5, "LineWidth", 0.8, ...
    "Color", [0.3 0.3 0.3]};
annotation("arrow", [0.5 0.5], [0.87 0.84], arrowOpts{:});  % start→load
annotation("arrow", [0.5 0.5], [0.77 0.72], arrowOpts{:});  % load→preproc
annotation("arrow", [0.5 0.5], [0.65 0.62], arrowOpts{:});  % preproc→check

% 分支箭头：check → model (正常), check → preproc (异常)
annotation("arrow", [0.5 0.27], [0.56 0.44], arrowOpts{:});  % check→model
annotation("arrow", [0.55 0.55], [0.56 0.73], "Color", [0.85 0.33 0.1], ...
    "HeadWidth", 5, "HeadLength", 5, "LineWidth", 0.8, "LineStyle", "--");
text(0.57, 0.64, "有异常值", "FontSize", 6, "Color", [0.85 0.33 0.1]);

% model→verify, optim→verify
annotation("arrow", [0.27 0.40], [0.38 0.26], arrowOpts{:});
annotation("arrow", [0.62 0.55], [0.38 0.26], arrowOpts{:});
annotation("arrow", [0.5 0.5], [0.20 0.12], arrowOpts{:});  % verify→output

hold off;
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_algorithm_flow"));
close(fig);
end
```

## 四、系统架构框图

```matlab
function drawSystemArchitecture(projectRoot)
% DRAWSYSTEMARCHITECTURE 绘制多模块系统架构框图
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "double");
hold on;
axis equal off;

% 模块颜色
primaryColor   = style.colors(1,:);
secondaryColor = style.colors(2,:);
tertiaryColor  = style.colors(3,:);
neutralColor   = [0.7 0.7 0.7];

% === 模块绘制函数 ===
    function h = drawModule(x, y, w, h, label, color, isMain)
        if nargin < 7; isMain = false; end
        lw = ternary(isMain, 1.5, 0.8);
        fs = ternary(isMain, 8, 7);
        rectangle("Position", [x y w h], "Curvature", 0.08, ...
            "FaceColor", [color 0.15], "EdgeColor", color, "LineWidth", lw);
        text(x+w/2, y+h/2, label, "HorizontalAlignment", "center", ...
            "FontSize", fs, "FontName", style.font, "Color", color*0.7);
    end

    function drawArrow(x1, y1, x2, y2, label)
        annotation("arrow", [x1 x2], [y1 y2], ...
            "HeadWidth", 5, "HeadLength", 5, "LineWidth", 0.8, "Color", [0.4 0.4 0.4]);
        if nargin > 4
            text((x1+x2)/2, (y1+y2)/2+0.01, label, ...
                "HorizontalAlignment", "center", "FontSize", 5.5, ...
                "Color", [0.4 0.4 0.4], "FontName", style.font);
        end
    end

% 数据层（顶部）
drawModule(0.08, 0.80, 0.84, 0.14, "数据输入层\n附件1: 测量数据  |  附件2: 参数表  |  附件3: 约束条件", neutralColor);

% 中间计算层
drawModule(0.08, 0.45, 0.25, 0.28, "数据预处理\n• 缺失值填充\n• 异常值检测\n• 归一化", primaryColor, true);
drawModule(0.38, 0.45, 0.25, 0.28, "核心求解器\n• 模型构建\n• 参数估计\n• 约束处理", primaryColor, true);
drawModule(0.68, 0.45, 0.25, 0.28, "后处理\n• 灵敏度分析\n• Bootstrap\n• 不确定性量化", primaryColor);

% 输出层（底部）
drawModule(0.08, 0.15, 0.84, 0.14, "输出层\n数值结果表格  |  可视化图表（SVG+PNG）  |  复现清单 JSON", neutralColor);

% 优化引擎（侧边）
drawModule(0.08, 0.33, 0.84, 0.06, "优化引擎: fmincon / PSO / GA / 模拟退火  (按问题类型自动选择)", secondaryColor);

% 箭头
drawArrow(0.50, 0.80, 0.50, 0.74, "数据流");
drawArrow(0.20, 0.74, 0.20, 0.74, "");
drawArrow(0.50, 0.74, 0.50, 0.74, "");
drawArrow(0.80, 0.74, 0.80, 0.74, "");
drawArrow(0.20, 0.45, 0.20, 0.40, "");
drawArrow(0.50, 0.45, 0.50, 0.40, "");
drawArrow(0.80, 0.45, 0.80, 0.40, "");
drawArrow(0.50, 0.39, 0.50, 0.30, "");

hold off;
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_system_arch"));
close(fig);
end

function s = ternary(cond, t, f)
    if cond; s = t; else; s = f; end
end
```

## 五、几何/物理示意图

MATLAB 最强的示意图能力在于精确几何绘制，直接用数据坐标画。

```matlab
function drawGeometrySchematic(projectRoot)
% DRAWGEOMETRYSCHEMATIC 绘制问题几何场景示意图
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
hold on;
axis equal;

% === 示例：圆形障碍物环境中的路径规划场景 ===

% 边界
xlim([-5, 55]); ylim([-5, 45]);
xlabel("x (m)"); ylabel("y (m)");

% 起点和终点
plot(0, 0, "o", "MarkerFaceColor", style.colors(3,:), ...
    "MarkerEdgeColor", "k", "MarkerSize", 10, "DisplayName", "起点");
plot(50, 40, "s", "MarkerFaceColor", style.colors(1,:), ...
    "MarkerEdgeColor", "k", "MarkerSize", 10, "DisplayName", "终点");
text(0, -2, "A(0,0)", "HorizontalAlignment", "center", "FontSize", 7);
text(50, 42, "B(50,40)", "HorizontalAlignment", "center", "FontSize", 7);

% 障碍物（圆形）
obstacles = [15, 12, 5; 30, 25, 6; 40, 15, 4; 20, 32, 3.5];
for i = 1:size(obstacles, 1)
    cx = obstacles(i,1); cy = obstacles(i,2); r = obstacles(i,3);
    % 填充圆
    t = linspace(0, 2*pi, 100);
    patch(cx + r*cos(t), cy + r*sin(t), [0.85 0.33 0.1], ...
        "FaceAlpha", 0.3, "EdgeColor", [0.85 0.33 0.1], "LineWidth", 1);
    text(cx, cy, sprintf("O%d", i), "HorizontalAlignment", "center", ...
        "FontSize", 7, "Color", [0.85 0.33 0.1]*0.6);
end

% 规划路径（折线 + Bezier 平滑）
waypoints = [0, 0; 8, 6; 22, 18; 35, 30; 42, 35; 50, 40];
plot(waypoints(:,1), waypoints(:,2), "o-", "Color", style.colors(1,:), ...
    "LineWidth", 1.5, "MarkerSize", 4, "MarkerFaceColor", style.colors(1,:), ...
    "DisplayName", "规划路径");

% 安全距离标注
cx = obstacles(2,1); cy = obstacles(2,2); r = obstacles(2,3);
safeR = r + 2;
tAnn = linspace(-pi/4, pi/4, 50);
plot(cx + safeR*cos(tAnn), cy + safeR*sin(tAnn), "--", ...
    "Color", [0.5 0.5 0.5], "LineWidth", 0.8);
text(cx + safeR + 1, cy, "安全距离", "FontSize", 6, "Color", [0.4 0.4 0.4]);

% 图例
legend("Location", "northeastoutside");

hold off;
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_geometry"));
close(fig);
end
```

### 常用几何绘制函数速查

```matlab
% 圆形
t = linspace(0, 2*pi, 100);
plot(cx + r*cos(t), cy + r*sin(t));

% 填充多边形
patch(xCoords, yCoords, faceColor, "FaceAlpha", 0.3, "EdgeColor", edgeColor);

% 矩形
rectangle("Position", [x, y, w, h], "Curvature", curv);

% 椭圆
t = linspace(0, 2*pi, 200);
plot(cx + a*cos(t), cy + b*sin(t));  % 或使用 fill

% 箭头（数据空间内）
quiver(x, y, dx, dy, 0, "LineWidth", 1.2, "MaxHeadSize", 0.5);

% 双头箭头标注（annotation 使用归一化坐标）
annotation("doublearrow", [x1 x2], [y1 y2]);

% 虚线参考线
xline(x0, "--", "Color", [0.5 0.5 0.5]);
yline(y0, "--", "Color", [0.5 0.5 0.5]);

% 角度弧线标注
theta = linspace(theta1, theta2, 50);
plot(cx + r*cos(theta), cy + r*sin(theta), "k-", "LineWidth", 0.8);

% 区域阴影（半透明覆盖）
fill([x1 x2 x2 x1], [y1 y1 y2 y2], color, "FaceAlpha", 0.1, "EdgeColor", "none");
```

## 六、网络拓扑 / 图论示意图

```matlab
function drawNetworkTopology(projectRoot)
% DRAWNNETWORKTOPOLOGY 使用 graph 对象绘制网络拓扑
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");

% 构建图
s = [1 1 2 2 3 3 4 4 5 5 6 6 7 7 8];
t = [2 3 3 4 5 6 5 7 6 8 7 8 8 9 9];
weights = [4 2 5 10 3 8 4 6 7 3 2 9 5 6 4];
G = graph(s, t, weights);

% 节点名称
nodeNames = ["仓库A" "配送站1" "配送站2" "客户1" "客户2" "客户3" "客户4" "客户5" "客户6"];

% 自定义节点坐标（模拟地理位置）
nodeX = [0, 2, 5, 1, 3, 6, 2, 5, 4];
nodeY = [8, 6, 7, 3, 4, 5, 1, 2, 0];

% 绘制
p = plot(G, "XData", nodeX, "YData", nodeY);
p.MarkerSize = 8;
p.NodeColor = style.colors(1,:);
p.EdgeColor = [0.5 0.5 0.5];
p.LineWidth = G.Edges.Weight / max(G.Edges.Weight) * 2;
p.NodeLabel = nodeNames;
p.NodeFontSize = 6.5;
p.NodeFontName = style.font;

% 标注边权重
labeledge(p, s, t, string(weights));

% 高亮最短路径
[path, ~] = shortestpath(G, 1, 9);
highlight(p, path, "EdgeColor", style.colors(4,:), "LineWidth", 2.5);

title("配送网络拓扑 — 最短路径高亮");
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_network"));
close(fig);
end
```

## 七、层次结构图（指标体系、分类树）

```matlab
function drawHierarchyTree(projectRoot)
% DRAWHIERARCHYTREE 绘制指标体系层次结构
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "double");
hold on;
axis off;

% 定义树结构：{label, x, y, [children indices]}
% 第0层 — 根
nodes = {
    "综合评价", 0.50, 0.92;   % 1
    % 第1层 — 一级指标
    "经济效益", 0.20, 0.70;    % 2
    "社会效益", 0.50, 0.70;    % 3
    "环境效益", 0.80, 0.70;    % 4
    % 第2层 — 二级指标
    "投入产出比", 0.10, 0.45;   % 5
    "利润率",     0.22, 0.45;   % 6
    "成本回收期", 0.30, 0.45;   % 7
    "就业贡献",   0.42, 0.45;   % 8
    "技术溢出",   0.58, 0.45;   % 9
    "碳排放",     0.70, 0.45;   % 10
    "能耗",       0.82, 0.45;   % 11
    "污染物排放", 0.90, 0.45;   % 12
};

% 连接关系：[parentIdx, childIdx]
edges = [1 2; 1 3; 1 4;
         2 5; 2 6; 2 7;
         3 8; 3 9;
         4 10; 4 11; 4 12];

% 绘制连接线
for i = 1:size(edges, 1)
    p = edges(i,1); c = edges(i,2);
    plot([nodes{p,2} nodes{c,2}], [nodes{p,3} nodes{c,3}], ...
        "-", "Color", [0.5 0.5 0.5], "LineWidth", 0.8);
end

% 绘制节点
for i = 1:size(nodes, 1)
    label = nodes{i,1}; x = nodes{i,2}; y = nodes{i,3};
    if i == 1  % 根节点
        rectangle("Position", [x-0.08 y-0.025 0.16 0.05], "Curvature", 0.2, ...
            "FaceColor", style.colors(1,:), "EdgeColor", "none");
        text(x, y, label, "HorizontalAlignment", "center", "FontSize", 8, ...
            "Color", "white", "FontName", style.font, "FontWeight", "bold");
    elseif i <= 4  % 一级指标
        rectangle("Position", [x-0.06 y-0.025 0.12 0.05], "Curvature", 0.15, ...
            "FaceColor", [style.colors(2,:) 0.2], ...
            "EdgeColor", style.colors(2,:), "LineWidth", 1);
        text(x, y, label, "HorizontalAlignment", "center", "FontSize", 7, ...
            "Color", style.colors(2,:)*0.7, "FontName", style.font);
    else  % 二级指标
        text(x, y, label, "HorizontalAlignment", "center", "FontSize", 6.5, ...
            "Color", [0.3 0.3 0.3], "FontName", style.font);
    end
end

hold off;
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_hierarchy"));
close(fig);
end
```

## 八、时间线 / 甘特图

```matlab
function drawGanttChart(projectRoot)
% DRAWGANTTCHART 绘制任务调度甘特图
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");

% 任务数据：{名称, 开始时间, 持续时间, 颜色索引}
tasks = {
    "数据加载",     0,  2,  1;
    "数据预处理",   1,  3,  2;
    "模型A求解",    3,  4,  1;
    "模型B求解",    4,  5,  3;
    "结果对比",     8,  2,  4;
    "灵敏度分析",   9,  3,  2;
    "论文撰写",    10,  4,  5;
};
nTasks = size(tasks, 1);
colors = style.colors;

hold on;
for i = 1:nTasks
    name = tasks{i,1};
    tStart = tasks{i,2};
    dur = tasks{i,3};
    cIdx = tasks{i,4};

    % 任务条
    rectangle("Position", [tStart, nTasks-i+0.75, dur, 0.5], ...
        "Curvature", 0.1, "FaceColor", [colors(cIdx,:) 0.7], ...
        "EdgeColor", colors(cIdx,:)*0.7, "LineWidth", 0.8);
    % 标签
    text(tStart + dur/2, nTasks-i+1, name, ...
        "HorizontalAlignment", "center", "FontSize", 7, ...
        "Color", colors(cIdx,:)*0.6, "FontName", style.font);
end

% 关键时间节点
xline(3, "--r", "模型开始", "FontSize", 6);
xline(8, "--b", "结果对比", "FontSize", 6);

set(gca, "YTick", 1:nTasks, "YTickLabel", []);
xlabel("时间 (h)");
title("任务调度计划");
xlim([0, 15]);

hold off;
export_publication_figure(fig, fullfile(projectRoot, "figures", "schematic_gantt"));
close(fig);
end
```

## 九、示意图导出后检查

1. 所有文字可被 PDF 阅读器选中（矢量文本，非位图文字）。
2. 在灰度模式下层级仍可区分。
3. 线条和文字在论文预计尺寸下不模糊、不重叠。
4. 数学符号正确渲染（`Interpreter="latex"` 模式）。
5. 与同期数据图使用相同字体和颜色语义。
