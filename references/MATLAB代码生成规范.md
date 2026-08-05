# MATLAB 代码生成详细规范

> 生成 MATLAB 求解代码时必须严格遵循。覆盖评价、优化、预测、微分方程、图论五类方法，
> 与 Python 代码生成规范同等地位，不是附录或备选。

## 一、通用代码骨架（所有 .m 脚本必须遵循）

```matlab
function main(seed)
% MAIN 问题N：XXX 的求解
%   方法：XXX
%   数学原理：[简述核心公式]
%   作者：math-contest-assistant
arguments
    seed (1,1) double = 42
end

% === 全局设置 ===
rng(seed, "twister");
projectRoot = fileparts(mfilename("fullpath"));
addpath(fullfile(projectRoot, "utils"));

% ============================================================
% 第一步：数据准备
% ============================================================
% 原则：数据量不大时直接硬编码；大数据从文件读取
% 格式：用有意义的变量名，注释标注来源

fprintf("=== 第一步：数据准备 ===\n");

% 示例：附件1的测量数据（表1，第2-6行）
timePoints = (0:60:300)';              % 时间点 (s)
xData = [...];                          % x坐标 (cm)，来源：附件1 Sheet1
yData = [...];                          % y坐标 (cm)

% 常量定义（全部大写）
GRAVITY = 9.8;          % 重力加速度 (m/s²)
MAX_SPEED = 2.0;        % 最大速度限制 (m/s)
SAFE_DISTANCE = 1.7;    % 安全距离 (m)

fprintf("  数据量: %d 个时间点\n", length(timePoints));
fprintf("  x范围: [%.2f, %.2f]\n", min(xData), max(xData));
fprintf("  y范围: [%.2f, %.2f]\n", min(yData), max(yData));

% ============================================================
% 第二步：数据预处理
% ============================================================
fprintf("\n=== 第二步：数据预处理 ===\n");

% 缺失值检测和处理
nanMask = isnan(xData);
if any(nanMask)
    fprintf("  检测到 %d 个缺失值，使用线性插值填充\n", sum(nanMask));
    xData = fillmissing(xData, "linear");
end

% 异常值检测（3σ原则）
mu = mean(xData, "omitnan");
sigma = std(xData, "omitnan");
outliers = abs(xData - mu) > 3 * sigma;
if any(outliers)
    fprintf("  检测到 %d 个异常值（>3σ），已标记\n", sum(outliers));
end

% ============================================================
% 第三步：核心模型
% ============================================================
fprintf("\n=== 第三步：核心模型求解 ===\n");

% 参数初值设定（基于对问题的物理理解）
initialGuess = [10.0, 0.1, 0.0];

% 定义目标函数（最小化均方误差）
objFun = @(params) mean((coreModel(params, timePoints) - yData).^2);

% 使用 fmincon 求解（支持约束）
opts = optimoptions("fmincon", "Display", "iter", ...
    "Algorithm", "sqp", "OptimalityTolerance", 1e-10);
[optimalParams, fval, exitflag, output] = fmincon(objFun, initialGuess, ...
    [], [], [], [], [0, 0, -inf], [inf, inf, inf], [], opts);

% 检查 exitflag
if exitflag <= 0
    warning("优化可能未收敛: exitflag=%d, 消息=%s", exitflag, output.message);
end

yPredicted = coreModel(optimalParams, timePoints);

fprintf("  优化状态: %s\n", output.message);
fprintf("  最优参数: [%.6f, %.6f, %.6f]\n", optimalParams);
fprintf("  目标函数值: %.6f\n", fval);

% 计算评估指标
residuals = yData - yPredicted;
SSres = sum(residuals.^2);
SStot = sum((yData - mean(yData)).^2);
RSquared = 1 - SSres / SStot;
RMSE = sqrt(mean(residuals.^2));
MAE = mean(abs(residuals));
MAPE = mean(abs(residuals ./ (abs(yData) + 1e-10))) * 100;

fprintf("\n  模型评估:\n");
fprintf("  R² = %.4f\n", RSquared);
fprintf("  RMSE = %.4f\n", RMSE);
fprintf("  MAE = %.4f\n", MAE);
fprintf("  MAPE = %.2f%%\n", MAPE);

% ============================================================
% 第四步：收敛性/稳定性分析
% ============================================================
fprintf("\n=== 第四步：收敛性分析 ===\n");

% 方法1：不同初始值的收敛性
fprintf("  测试不同初始值的收敛性...\n");
initialTrials = [
    5.0,  0.05, -1.0;
    15.0, 0.20,  1.0;
    8.0,  0.15, -0.5;
    12.0, 0.08,  0.5
];
for i = 1:size(initialTrials, 1)
    [paramsTrial, ~, ef] = fmincon(objFun, initialTrials(i,:), ...
        [], [], [], [], [0, 0, -inf], [inf, inf, inf]);
    paramsDiff = max(abs(paramsTrial - optimalParams) ./ (abs(optimalParams) + 1e-10));
    fprintf("    试验%d: 收敛=%s, 参数最大偏差=%.2f%%\n", ...
        i, ternary(ef>0, "是", "否"), paramsDiff * 100);
end

% 方法2：Bootstrap 重采样评估参数稳定性
nBootstrap = 100;
bootstrapParams = zeros(nBootstrap, 3);
parfor b = 1:nBootstrap
    idx = randi(length(timePoints), length(timePoints), 1);
    try
        [bp, ~, ef] = fmincon(@(p) mean((coreModel(p, timePoints(idx)) - yData(idx)).^2), ...
            optimalParams, [], [], [], [], [0, 0, -inf], [inf, inf, inf], ...
            optimoptions("fmincon", "Display", "off"));
        if ef > 0
            bootstrapParams(b,:) = bp;
        end
    catch
    end
end

validBoot = bootstrapParams(all(bootstrapParams ~= 0, 2), :);
if size(validBoot, 1) > 10
    paramStd = std(validBoot, 0, 1);
    fprintf("\n  Bootstrap 参数稳定性 (n=%d):\n", size(validBoot, 1));
    paramNames = ["a", "b", "c"];
    for i = 1:3
        fprintf("    %s: %.4f ± %.4f\n", paramNames(i), mean(validBoot(:,i)), paramStd(i));
    end
end

% ============================================================
% 第五步：灵敏度分析
% ============================================================
fprintf("\n=== 第五步：灵敏度分析 ===\n");

sensitivityRatios = [0.8, 0.9, 1.0, 1.1, 1.2];
paramNames = ["参数a", "参数b", "参数c"];
maxChanges = zeros(1, 3);

for i = 1:3
    fprintf("\n  %s (基准值=%.4f) 的灵敏度:\n", paramNames(i), optimalParams(i));
    changes = zeros(1, length(sensitivityRatios));
    for j = 1:length(sensitivityRatios)
        perturbedParams = optimalParams;
        perturbedParams(i) = optimalParams(i) * sensitivityRatios(j);
        yPerturbed = coreModel(perturbedParams, timePoints);
        rmsd = sqrt(mean((yPerturbed - yPredicted).^2));
        pctChange = (mean(yPerturbed) - mean(yPredicted)) / (abs(mean(yPredicted)) + 1e-10) * 100;
        changes(j) = abs(pctChange);
        fprintf("    比例=%.1f (值=%.4f), RMSD=%.4f, 输出变化=%+.2f%%\n", ...
            sensitivityRatios(j), perturbedParams(i), rmsd, pctChange);
    end
    maxChanges(i) = max(changes);
end

fprintf("\n  灵敏度总结:\n");
for i = 1:3
    level = ternary(maxChanges(i) > 10, "高", ternary(maxChanges(i) > 3, "中", "低"));
    fprintf("    %s: 最大输出变化 %.2f%% → 灵敏度: %s\n", paramNames(i), maxChanges(i), level);
end

% ============================================================
% 第六步：可视化
% ============================================================
fprintf("\n=== 第六步：生成图表 ===\n");

fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
t = tiledlayout(fig, 2, 2, "TileSpacing", "compact", "Padding", "compact");

% 子图1：数据与模型拟合
ax1 = nexttile(1);
scatter(ax1, timePoints, yData, 36, style.colors(1,:), "filled", ...
    "MarkerEdgeColor", style.colors(1,:)*0.7, "DisplayName", "实测数据");
hold(ax1, "on");
tSmooth = linspace(min(timePoints), max(timePoints), 200)';
ySmooth = coreModel(optimalParams, tSmooth);
plot(ax1, tSmooth, ySmooth, "Color", style.colors(4,:), "LineWidth", 1.1, ...
    "DisplayName", sprintf("模型拟合 (R²=%.3f)", RSquared));
hold(ax1, "off");
xlabel(ax1, "时间 (s)"); ylabel(ax1, "值");
title(ax1, "数据与模型拟合对比");
legend(ax1, "Location", "best");

% 子图2：残差分布
ax2 = nexttile(2);
yline(ax2, 0, "Color", [0.5 0.5 0.5], "LineStyle", "--");
hold(ax2, "on");
scatter(ax2, timePoints, residuals, 36, style.colors(2,:), "filled", ...
    "MarkerEdgeColor", style.colors(2,:)*0.7);
fill(ax2, [timePoints; flipud(timePoints)], ...
    [2*std(residuals)*ones(size(timePoints)); ...
     -2*std(residuals)*ones(size(timePoints))], ...
    [0.5 0.5 0.5], "FaceAlpha", 0.15, "EdgeColor", "none", ...
    "DisplayName", "±2σ");
hold(ax2, "off");
xlabel(ax2, "时间 (s)"); ylabel(ax2, "残差");
title(ax2, sprintf("残差分布 (σ=%.4f)", std(residuals)));

% 子图3：参数分布
ax3 = nexttile(3);
if size(validBoot, 1) > 10
    h = histogram(ax3, validBoot(:,1), 20, "FaceAlpha", 0.5, ...
        "DisplayName", sprintf("a (%.3f±%.3f)", mean(validBoot(:,1)), std(validBoot(:,1))));
    hold(ax3, "on");
    histogram(ax3, validBoot(:,2), 20, "FaceAlpha", 0.5, ...
        "DisplayName", sprintf("b (%.3f±%.3f)", mean(validBoot(:,2)), std(validBoot(:,2))));
    hold(ax3, "off");
    legend(ax3, "Location", "best");
end
xlabel(ax3, "参数值"); ylabel(ax3, "频数");
title(ax3, sprintf("Bootstrap 参数分布 (n=%d)", size(validBoot, 1)));

% 子图4：灵敏度分析
ax4 = nexttile(4);
colors = cell(1, 3);
for i = 1:3
    if maxChanges(i) > 10;      colors{i} = [0.91 0.30 0.24];
    elseif maxChanges(i) > 3;   colors{i} = [0.95 0.61 0.07];
    else;                       colors{i} = [0.18 0.80 0.44];
    end
end
b = barh(ax4, 1:3, maxChanges, 0.5);
for i = 1:3; b.FaceColor = "flat"; b.CData(i,:) = colors{i}; end
set(ax4, "YTickLabel", paramNames);
xlabel(ax4, "最大输出变化 (%)");
title(ax4, "参数灵敏度分析 (±20%)");
xline(ax4, 3, "--", "Color", [0.95 0.61 0.07], "Alpha", 0.5);
xline(ax4, 10, "--", "Color", [0.91 0.30 0.24], "Alpha", 0.5);

title(t, "问题N求解结果");
export_publication_figure(fig, fullfile(projectRoot, "figures", "result_qN_overview"));
close(fig);

% ============================================================
% 第七步：结果汇总与导出
% ============================================================
fprintf("\n%s\n", repmat("=", 1, 60));
fprintf("求解完成 — 结果汇总\n");
fprintf("%s\n", repmat("=", 1, 60));

finalResults = struct(...
    "问题编号", "N", ...
    "方法", "XXX", ...
    "最优参数", optimalParams, ...
    "R2", RSquared, ...
    "RMSE", RMSE, ...
    "MAE", MAE, ...
    "MAPE", MAPE, ...
    "收敛性", ternary(exitflag > 0, "通过", "未通过"), ...
    "最大灵敏度", max(maxChanges), ...
    "Bootstrap样本数", size(validBoot, 1));

disp(finalResults);

% 保存结果到 JSON 供论文使用
resultJson = jsonencode(finalResults, "PrettyPrint", true);
fid = fopen(fullfile(projectRoot, "results", "qN_final_results.json"), "w");
fprintf(fid, "%s", resultJson);
fclose(fid);
fprintf("\n结果已保存到 results/qN_final_results.json\n");

end

% ============================================================
% 模型函数（独立函数，与主脚本同文件或独立文件）
% ============================================================
function yPred = coreModel(params, x)
    % COREMODEL [模型名称]
    %   数学原理: y = a * exp(-b * x) + c
    a = params(1); b = params(2); c = params(3);
    yPred = a * exp(-b * x) + c;
end

function s = ternary(cond, t, f)
    % 三元运算符辅助函数
    if cond; s = t; else; s = f; end
end
```

### MATLAB 特有要求

- **入口函数**：每个求解脚本必须定义 `function main(seed)` 作为入口，使用 `arguments` 校验输入。
- **随机种子**：入口第一句 `rng(seed, "twister")`，禁止使用默认种子。
- **路径**：用 `fileparts(mfilename("fullpath"))` 获取脚本所在目录，用 `fullfile` 构造所有子路径。
- **函数分离**：核心模型函数独立定义，与主脚本同文件或独立 `.m` 文件。函数名与文件名一致。
- **表格 I/O**：优先 `readtable`/`writetable`；纯数值用 `readmatrix`/`writematrix`。
- **并行**：独立循环可用 `parfor`（需 Parallel Computing Toolbox）；无该工具箱时退化为 `for`。
- **优化收敛**：所有优化必须检查 `exitflag`；非正值必须 warning。
- **现代语法**：默认使用 R2019b+ 特性：`arguments`、`tiledlayout`、`exportgraphics`、`"string"` 双引号。

---

## 二、按方法类型的代码模板

### 2.1 评价类（AHP / TOPSIS / 熵权法 / 模糊评价 / 灰色关联）

```matlab
function scores = topsis(X, weights)
% TOPSIS 优劣解距离法
%   X: n×m 原始数据矩阵（n个方案，m个指标）
%   weights: 1×m 权重向量
arguments
    X (:,:) double
    weights (1,:) double {mustBeNonnegative}
end

% 步骤1：向量归一化
X_norm = X ./ sqrt(sum(X.^2, 1));

% 步骤2：加权标准化矩阵
V = X_norm .* weights;

% 步骤3：正理想解和负理想解
vPlus = max(V, [], 1);
vMinus = min(V, [], 1);

% 步骤4：各方案到正负理想解的距离
dPlus = sqrt(sum((V - vPlus).^2, 2));
dMinus = sqrt(sum((V - vMinus).^2, 2));

% 步骤5：相对贴近度（得分）
scores = dMinus ./ (dPlus + dMinus);
end

function w = entropyWeight(X)
% 熵权法计算客观权重
%   X: n×m 矩阵（已正向化）
arguments
    X (:,:) double
end
[n, m] = size(X);

% 归一化
P = X ./ sum(X, 1);

% 处理 log(0)
P(P == 0) = 1e-10;

% 信息熵
e = -sum(P .* log(P), 1) / log(n);

% 权重
w = (1 - e) / sum(1 - e);
end

function gamma = greyRelational(X)
% 灰色关联分析
%   X: n×m 矩阵，每行一个方案
[n, ~] = size(X);

% 参考序列（取每列最优值）
ref = max(X, [], 1);

% 绝对差矩阵
absDiff = abs(X - ref);

% 关联系数 (ρ=0.5)
rho = 0.5;
minDiff = min(absDiff, [], "all");
maxDiff = max(absDiff, [], "all");
xi = (minDiff + rho * maxDiff) ./ (absDiff + rho * maxDiff);

% 关联度（等权平均）
gamma = mean(xi, 2);
end
```

### 2.2 优化类（线性规划 / PSO / GA / 模拟退火 / 动态规划）

```matlab
% === 线性规划 (linprog) ===
% min c'*x  subject to: A*x <= b, Aeq*x = beq, lb <= x <= ub
f = [-3; -4];                   % 目标系数（负号因为求最大化）
A = [1, 2; 3, 1; 0, 1];        % 不等式约束矩阵
b = [100; 120; 30];             % 不等式约束右侧
lb = [0; 0];                    % 下界
ub = [];                        % 上界（无约束）

opts = optimoptions("linprog", "Display", "iter", "Algorithm", "dual-simplex");
[x, fval, exitflag] = linprog(f, A, b, [], [], lb, ub, opts);
fprintf("最优解: x1=%.2f, x2=%.2f\n", x);
fprintf("最优值: %.2f\n", -fval);  % 转回最大化

% === 整数线性规划 (intlinprog) ===
% min f'*x, subject to: 整数约束 intcon
f = [8; 5];                     % 目标系数
intcon = [1; 2];                % 整数变量索引
A = [1, 1; 2, 1];
b = [6; 8];
lb = [0; 0];

[x, fval, exitflag] = intlinprog(f, intcon, A, b, [], [], lb, []);
fprintf("最优整数解: x1=%d, x2=%d\n", x);
fprintf("最优值: %.2f\n", fval);

% === 非线性约束优化 (fmincon) ===
function [xOpt, fOpt] = solveNonlinear()
    % 目标函数
    objFun = @(x) (x(1)-2)^2 + (x(2)-3)^2 + x(1)*x(2);

    % 非线性约束函数
    nonlcon = @(x) deal(...
        [x(1)^2 + x(2)^2 - 10], ...  % c(x) <= 0
        []);                           % ceq(x) = 0

    x0 = [0; 0];
    lb = [-5; -5];
    ub = [5; 5];

    opts = optimoptions("fmincon", "Algorithm", "sqp", ...
        "Display", "iter", "OptimalityTolerance", 1e-10);
    [xOpt, fOpt, exitflag] = fmincon(objFun, x0, [], [], [], [], lb, ub, nonlcon, opts);

    if exitflag <= 0
        warning("fmincon 未收敛: exitflag=%d", exitflag);
    end
end

% === 粒子群优化 (PSO) ===
function [gBest, gBestVal, history] = pso(objFun, nDims, bounds, opts)
% PSO 粒子群优化
arguments
    objFun function_handle
    nDims (1,1) double {mustBeInteger, mustBePositive}
    bounds (:,2) double
    opts.nParticles (1,1) double = 30
    opts.maxIter (1,1) double = 200
    opts.w (1,1) double = 0.7     % 惯性权重
    opts.c1 (1,1) double = 1.5    % 认知系数
    opts.c2 (1,1) double = 1.5    % 社会系数
end

nParticles = opts.nParticles;
maxIter = opts.maxIter;

% 初始化位置和速度
lb = bounds(:,1)'; ub = bounds(:,2)';
positions = lb + rand(nParticles, nDims) .* (ub - lb);
velocities = -1 + 2 * rand(nParticles, nDims);

% 评估初始适应度
pBestPos = positions;
pBestVal = inf(nParticles, 1);
for i = 1:nParticles
    pBestVal(i) = objFun(positions(i,:));
end
[gBestVal, idx] = min(pBestVal);
gBest = positions(idx,:);

history = zeros(maxIter, 1);
history(1) = gBestVal;

% 线性递减惯性权重
wStart = opts.w; wEnd = 0.4;

for iter = 1:maxIter
    w = wStart - (wStart - wEnd) * iter / maxIter;

    for i = 1:nParticles
        r1 = rand(1, nDims); r2 = rand(1, nDims);
        velocities(i,:) = w * velocities(i,:) ...
            + opts.c1 * r1 .* (pBestPos(i,:) - positions(i,:)) ...
            + opts.c2 * r2 .* (gBest - positions(i,:));
        positions(i,:) = positions(i,:) + velocities(i,:);

        % 边界处理
        positions(i,:) = max(min(positions(i,:), ub), lb);
    end

    % 更新最优
    for i = 1:nParticles
        val = objFun(positions(i,:));
        if val < pBestVal(i)
            pBestVal(i) = val;
            pBestPos(i,:) = positions(i,:);
            if val < gBestVal
                gBestVal = val;
                gBest = positions(i,:);
            end
        end
    end
    history(iter) = gBestVal;
end
end

% === 遗传算法 (GA 核心组件) ===
function chrom = initPopulation(popSize, nVars, bounds)
    % 实数编码初始化
    lb = bounds(:,1)'; ub = bounds(:,2)';
    chrom = lb + rand(popSize, nVars) .* (ub - lb);
end

function offspring = sbxCrossover(parents, pc, bounds, eta)
    % 模拟二进制交叉 (SBX)
    arguments
        parents (:,:) double
        pc (1,1) double = 0.8
        bounds (:,2) double
        eta (1,1) double = 20
    end
    [popSize, nVars] = size(parents);
    lb = bounds(:,1)'; ub = bounds(:,2)';
    offspring = parents;
    for i = 1:2:popSize-1
        if rand < pc
            u = rand(1, nVars);
            beta = zeros(1, nVars);
            mask = u <= 0.5;
            beta(mask) = (2 * u(mask)).^(1 / (eta + 1));
            beta(~mask) = (1 ./ (2 * (1 - u(~mask)))).^(1 / (eta + 1));
            offspring(i,:)   = 0.5 * ((1 + beta) .* parents(i,:) + (1 - beta) .* parents(i+1,:));
            offspring(i+1,:) = 0.5 * ((1 - beta) .* parents(i,:) + (1 + beta) .* parents(i+1,:));
            % 边界钳制
            offspring(i,:)   = max(min(offspring(i,:), ub), lb);
            offspring(i+1,:) = max(min(offspring(i+1,:), ub), lb);
        end
    end
end

function mutated = gaussianMutation(pop, pm, bounds, sigma)
    % 高斯变异
    arguments
        pop (:,:) double
        pm (1,1) double = 0.1
        bounds (:,2) double
        sigma (1,1) double = 0.1
    end
    lb = bounds(:,1)'; ub = bounds(:,2)';
    range = ub - lb;
    mutated = pop;
    for i = 1:size(pop, 1)
        if rand < pm
            mutated(i,:) = pop(i,:) + sigma * range .* randn(1, size(pop, 2));
            mutated(i,:) = max(min(mutated(i,:), ub), lb);
        end
    end
end

function selected = tournamentSelect(pop, fitness, tournamentSize)
    % 锦标赛选择
    arguments
        pop (:,:) double
        fitness (:,1) double
        tournamentSize (1,1) double = 3
    end
    popSize = size(pop, 1);
    selected = zeros(size(pop));
    for i = 1:popSize
        candidates = randi(popSize, tournamentSize, 1);
        [~, best] = min(fitness(candidates));
        selected(i,:) = pop(candidates(best), :);
    end
end

% === 模拟退火 (SA) ===
function [xBest, fBest, history] = simulatedAnnealing(objFun, x0, bounds, opts)
arguments
    objFun function_handle
    x0 (1,:) double
    bounds (:,2) double
    opts.T0 (1,1) double = 1000
    opts.Tmin (1,1) double = 0.01
    opts.alpha (1,1) double = 0.95     % 降温系数
    opts.maxIter (1,1) double = 1000
    opts.stepSize (1,1) double = 0.1
end

lb = bounds(:,1)'; ub = bounds(:,2)';
x = x0; f = objFun(x);
xBest = x; fBest = f;
T = opts.T0;
history = zeros(opts.maxIter, 1);

for iter = 1:opts.maxIter
    % 产生新解
    xNew = x + opts.stepSize * (ub - lb) .* randn(1, length(x0));
    xNew = max(min(xNew, ub), lb);
    fNew = objFun(xNew);

    % Metropolis 准则
    delta = fNew - f;
    if delta < 0 || rand < exp(-delta / T)
        x = xNew; f = fNew;
    end

    % 更新最优
    if f < fBest
        xBest = x; fBest = f;
    end

    history(iter) = fBest;
    T = T * opts.alpha;
    if T < opts.Tmin; break; end
end
end
```

### 2.3 预测类（回归 / 灰色预测 / ARIMA / 蒙特卡洛）

```matlab
% === 灰色预测 GM(1,1) ===
function [x0Predict, grade, x0Hat] = gm11(x0, predictN)
% GM11 灰色预测 GM(1,1) 模型
arguments
    x0 (:,1) double
    predictN (1,1) double {mustBeInteger, mustBePositive} = 5
end

n = length(x0);

% 步骤1：级比检验
lambda = x0(1:end-1) ./ x0(2:end);
if any(lambda <= exp(-2/(n+1)) | lambda >= exp(2/(n+1)))
    warning("级比检验未通过，考虑对数据平移变换");
end

% 步骤2：一次累加生成 (1-AGO)
x1 = cumsum(x0);

% 步骤3：构造数据矩阵 B 和数据向量 Y
z1 = -0.5 * (x1(2:end) + x1(1:end-1));
B = [z1, ones(n-1, 1)];
Y = x0(2:end);

% 步骤4：最小二乘估计
ab = B \ Y;
a = ab(1); b = ab(2);

% 步骤5：白化方程的时间响应函数
gmResp = @(k) (x0(1) - b/a) * exp(-a * k) + b/a;

% 步骤6：预测（还原）
kAll = (-1:n+predictN-2)';
x1HatAll = gmResp(kAll);
x1HatAll(1) = x0(1);

% IAGO 还原
x0HatAll = diff(x1HatAll);
x0Hat = x0HatAll(1:n);          % 拟合值
x0Predict = x0HatAll(n+1:end);  % 预测值

% 步骤7：精度检验
residual = x0 - x0Hat;
relativeError = abs(residual) ./ (abs(x0) + 1e-10);

% 后验差比 C = S2/S1
S1 = std(x0, 1);
S2 = std(residual, 1);
C = S2 / (S1 + 1e-10);

% 小误差概率 P
avgResidual = mean(residual);
P = mean(abs(residual - avgResidual) < 0.6745 * S1);

% 精度等级评定
if P > 0.95 && C < 0.35
    grade = "一级（好）";
elseif P > 0.80 && C < 0.50
    grade = "二级（合格）";
elseif P > 0.70 && C < 0.65
    grade = "三级（勉强）";
else
    grade = "四级（不合格）";
end

fprintf("  灰色预测 GM(1,1) 结果:\n");
fprintf("    发展系数 a=%.6f, 灰作用量 b=%.4f\n", a, b);
fprintf("    后验差比 C=%.4f, 小误差概率 P=%.4f\n", C, P);
fprintf("    精度等级: %s\n", grade);
fprintf("    平均相对误差: %.2f%%\n", mean(relativeError)*100);
fprintf("    预测值: %s\n", mat2str(x0Predict, 4));
end

% === 蒙特卡洛模拟 ===
function [estimate, ci, samples] = monteCarlo(simFun, nSamples, alpha)
% MONTECARLO 蒙特卡洛模拟
%   simFun: 无输入函数句柄，每次调用返回一个标量模拟结果
arguments
    simFun function_handle
    nSamples (1,1) double {mustBeInteger, mustBePositive} = 10000
    alpha (1,1) double = 0.05
end

samples = zeros(nSamples, 1);
parfor i = 1:nSamples
    samples(i) = simFun();
end

estimate = mean(samples);
se = std(samples) / sqrt(nSamples);
z = norminv(1 - alpha/2);
ci = [estimate - z*se, estimate + z*se];

fprintf("蒙特卡洛估计: %.6f\n", estimate);
fprintf("%.0f%% CI: [%.6f, %.6f]\n", (1-alpha)*100, ci);
fprintf("标准差: %.6f, 标准误: %.6f\n", std(samples), se);
end
```

### 2.4 微分方程类（ODE / SIR / 热传导）

```matlab
% === ODE 数值求解通用模板 ===
function solveODE()
    % 初始条件
    y0 = [1000; 1; 0];  % [S0, I0, R0]

    % 时间范围
    tSpan = [0, 100];

    % 求解 (使用 ode45)
    opts = odeset("RelTol", 1e-8, "AbsTol", 1e-10);
    [t, y] = ode45(@sirODE, tSpan, y0, opts);

    % 结果
    S = y(:,1); I = y(:,2); R = y(:,3);
    fprintf("  求解成功，%d 个时间步\n", length(t));
    fprintf("  终止值: S=%.4f, I=%.4f, R=%.4f\n", S(end), I(end), R(end));

    % 绘图
    fig = figure("Visible", "off");
    style = apply_publication_style(fig, "zh", "report");
    plot(t, S, "Color", style.colors(1,:), "LineWidth", 1.1, "DisplayName", "S(t) 易感者");
    hold on;
    plot(t, I, "Color", style.colors(4,:), "LineWidth", 1.1, "DisplayName", "I(t) 感染者");
    plot(t, R, "Color", style.colors(3,:), "LineWidth", 1.1, "DisplayName", "R(t) 康复者");
    hold off;
    xlabel("时间"); ylabel("人数");
    legend("Location", "best");
    title("SIR 模型数值解");
    export_publication_figure(fig, "figures/process_qN_sir");
    close(fig);
end

function dydt = sirODE(t, y)
    % SIR 传染病模型
    %   y = [S; I; R]
    beta = 0.3;   % 感染率
    gamma = 0.1;  % 康复率
    S = y(1); I = y(2); R = y(3);
    dydt = [-beta * S * I;
             beta * S * I - gamma * I;
             gamma * I];
end

% === 偏微分方程 (PDE) — 一维热传导 ===
function solveHeatEquation()
    % 参数
    L = 1;          % 杆长
    T = 0.5;        % 总时间
    alpha = 0.01;   % 热扩散系数
    nx = 50;        % 空间网格点数
    nt = 500;       % 时间步数

    dx = L / (nx - 1);
    dt = T / nt;
    r = alpha * dt / dx^2;

    if r > 0.5
        warning("CFL条件不满足: r=%.3f > 0.5", r);
    end

    % 初始化
    x = linspace(0, L, nx)';
    u = sin(pi * x / L);  % 初始温度分布
    u(1) = 0; u(end) = 0; % 边界条件：两端恒温0

    % 时间推进（显式格式）
    for n = 1:nt
        uNew = u;
        for i = 2:nx-1
            uNew(i) = u(i) + r * (u(i+1) - 2*u(i) + u(i-1));
        end
        u = uNew;
    end

    % 绘图
    fig = figure("Visible", "off");
    plot(x, u, "LineWidth", 1.5);
    xlabel("位置 x"); ylabel("温度 u");
    title(sprintf("一维热传导 t=%.2f", T));
    export_publication_figure(fig, "figures/process_qN_heat");
    close(fig);
end

% === 参数估计（ODE 逆问题） ===
function estimatedParams = estimateODEParams(tData, yData, paramGuess)
% ESTIMATEODEPARAMS 使用 fmincon 拟合 ODE 参数
    function sse = objective(p)
        [~, ySim] = ode45(@(t,y) sirODEWithParams(t, y, p), tData, yData(1,:));
        sse = sum((ySim(:) - yData(:)).^2);
    end

    lb = [0, 0];     % 参数下界
    ub = [1, 1];     % 参数上界
    opts = optimoptions("fmincon", "Display", "iter");
    estimatedParams = fmincon(@objective, paramGuess, [], [], [], [], lb, ub, [], opts);
end

function dydt = sirODEWithParams(~, y, p)
    beta = p(1); gamma = p(2);
    dydt = [-beta * y(1) * y(2);
             beta * y(1) * y(2) - gamma * y(2);
             gamma * y(2)];
end
```

### 2.5 图论类（最短路径 / TSP / 最大流）

```matlab
% === Dijkstra 最短路径 ===
function [dist, path] = dijkstra(adjMatrix, start)
% DIJKSTRA 单源最短路径（邻接矩阵实现）
arguments
    adjMatrix (:,:) double
    start (1,1) double {mustBeInteger, mustBePositive}
end

n = size(adjMatrix, 1);
visited = false(n, 1);
dist = inf(n, 1);
dist(start) = 0;
prev = zeros(n, 1);

for iter = 1:n
    % 选择未访问的最近节点
    unvisited = inf(n, 1);
    unvisited(~visited) = dist(~visited);
    [~, u] = min(unvisited);
    if isinf(dist(u)); break; end
    visited(u) = true;

    % 更新邻居
    for v = 1:n
        if ~visited(v) && adjMatrix(u, v) < inf
            alt = dist(u) + adjMatrix(u, v);
            if alt < dist(v)
                dist(v) = alt;
                prev(v) = u;
            end
        end
    end
end

% 回溯路径
path = cell(n, 1);
for v = 1:n
    if isinf(dist(v)); path{v} = []; continue; end
    p = v;
    pathV = v;
    while prev(p) ~= 0
        p = prev(p);
        pathV = [p, pathV]; %#ok<AGROW>
    end
    path{v} = pathV;
end
end

% === Floyd-Warshall 全源最短路径 ===
function [dist, next] = floydWarshall(adjMatrix)
arguments
    adjMatrix (:,:) double
end
n = size(adjMatrix, 1);
dist = adjMatrix;
next = repmat((1:n)', 1, n);

for k = 1:n
    for i = 1:n
        for j = 1:n
            if dist(i,k) + dist(k,j) < dist(i,j)
                dist(i,j) = dist(i,k) + dist(k,j);
                next(i,j) = next(i,k);
            end
        end
    end
end
end

% === 最小生成树 (Prim) ===
function [mstEdges, totalWeight] = primMST(adjMatrix)
    n = size(adjMatrix, 1);
    visited = false(n, 1);
    visited(1) = true;
    mstEdges = zeros(n-1, 2);
    totalWeight = 0;

    for e = 1:n-1
        minWeight = inf;
        u = 0; v = 0;
        for i = 1:n
            if visited(i)
                for j = 1:n
                    if ~visited(j) && adjMatrix(i,j) < minWeight
                        minWeight = adjMatrix(i,j);
                        u = i; v = j;
                    end
                end
            end
        end
        visited(v) = true;
        mstEdges(e,:) = [u, v];
        totalWeight = totalWeight + minWeight;
    end
end

% === 使用内置 graph/digraph 对象（推荐） ===
function demoBuiltinGraph()
    % 创建有向图
    s = [1 1 2 2 3 3 4 5];
    t = [2 3 3 4 5 4 5 4];
    weights = [10 5 2 8 7 4 3 6];
    G = digraph(s, t, weights);

    % 最短路径
    [path, dist] = shortestpath(G, 1, 4);
    fprintf("最短路径: %s, 距离=%.2f\n", mat2str(path), dist);

    % 最小生成树（无向图）
    G2 = graph(s, t, weights);
    T = minspTree(G2);
    fprintf("MST 边数: %d, 总权重: %.2f\n", size(T.Edges,1), sum(T.Edges.Weight));

    % 可视化
    fig = figure("Visible", "off");
    p = plot(G, "EdgeLabel", G.Edges.Weight);
    highlight(p, path, "EdgeColor", "r", "LineWidth", 2);
    title("最短路径可视化");
    export_publication_figure(fig, "figures/result_qN_graph");
    close(fig);
end
```

---

## 三、数据处理模式

### 3.1 数据硬编码

```matlab
% === 模式：从赛题附件手动录入关键数据 ===
% 原则：只录入求解需要用到的数据
% 格式：每行注释标注数据在原始文件中的位置

% 附件1: 2024年1-6月销售额（万元），Sheet "月度汇总"，行3-8
sales2024H1 = [120.5; 135.2; 142.8; 156.3; 148.9; 162.7];

% 附件2: 各供应商报价（元），表2，列B
supplierPrices = [8.5; 9.2; 7.8; 10.1; 8.9];

% 附件3: 距离矩阵 (km)，5个城市
distanceMatrix = [
    0   120  85  200  150;
    120   0  95  180  130;
    85   95   0  160  110;
    200 180 160    0   90;
    150 130 110   90    0
];
```

### 3.2 从文件读取

```matlab
% === Excel 读取 ===
dataTable = readtable(fullfile(projectRoot, "data", "附件1.xlsx"), ...
    "Sheet", "月度汇总", "Range", "A3:F8");
numericData = table2array(dataTable);

% === CSV 读取 ===
csvData = readmatrix(fullfile(projectRoot, "data", "input.csv"));

% === 文本文件读取 ===
fid = fopen(fullfile(projectRoot, "data", "params.txt"), "r");
params = textscan(fid, "%f %f %f", "CollectOutput", true);
fclose(fid);
```

### 3.3 缺失值与异常值

```matlab
% 缺失值检测与填充
nanMask = ismissing(dataTable);           % table 类型
nanMask = isnan(numericData);             % 矩阵类型
filled = fillmissing(data, "linear");     % 线性插值
filled = fillmissing(data, "movmedian", 5); % 移动中位数

% 异常值检测 (MAD 方法，更鲁棒)
med = median(data, "omitnan");
mad = median(abs(data - med), "omitnan");
outlierMask = abs(data - med) > 3 * 1.4826 * mad;

% 异常值处理（winsorize）
dataClipped = data;
dataClipped(outlierMask) = med + 3*1.4826*mad * sign(data(outlierMask) - med);
```

### 3.4 几何/坐标数据

```matlab
% === 模式：几何/坐标数据的结构化录入 ===
% 附件 result1.xlsx: 龙头板凳在 t=0s 时刻的位置坐标
dragonHeadT0 = [
    0.000, 0.000;    % 节点1（龙头前端）
    0.275, 0.000;    % 节点2
    0.550, 0.000;    % 节点3
    % ... 共201个节点
];

% 障碍物坐标 [x, y, radius]
obstacles = [
    15.0, 20.0, 5.0;
    35.0, 40.0, 3.0
];
```

---

## 四、常见错误自愈策略

| 错误类型 | 典型报错 | 自动修复策略 |
|----------|----------|-------------|
| 工具箱缺失 | `Unable to resolve the name...` | 用基础 MATLAB 函数替代；如无 Optimization Toolbox 则用 `fminsearch` 替代 `fmincon` |
| 维度不匹配 | `Arrays have incompatible sizes` | 打印 `size()` 定位 → 添加 `'` 转置或 `reshape` |
| 除零/对数零 | `Warning: Divide by zero` | 分母加 `eps` 或用 `max(x, eps)` |
| 矩阵奇异 | `Matrix is singular` | 用 `pinv`（伪逆）替代 `inv` 或 `\` |
| 优化不收敛 | `Solver stopped prematurely` | 换初始值；换 `Algorithm`；使用 `GlobalSearch`/`MultiStart` |
| 内存溢出 | `Out of memory` | 减少网格分辨率；用 `sparse` 稀疏矩阵；分块处理 |
| 中文方框 | 图表中中文显示为 □ | 用 `listfonts` 查找可用字体 → 设置 `FontName` |
| 超时 | 执行超过 300 秒 | 减少 `nSamples`/代数/网格点数；启用 `parfor` |
| NaN 传播 | 结果全为 NaN | 检查 `log`/`sqrt` 负数输入 → 添加 `realmax` 钳制 |
| 路径错误 | `Invalid file identifier` | 用 `fullfile` 替代字符串拼接；检查 `exist(file, "file")` |

### 自检代码模式

```matlab
function passed = runSelfChecks(results)
% RUNSELFCHECKS 求解结果自检
arguments
    results struct
end

checksPassed = 0; checksTotal = 5;

% 检查1：数值范围合理性
if results.R2 >= 0 && results.R2 <= 1
    checksPassed = checksPassed + 1;
else
    fprintf("  ❌ 检查1失败: R²=%.4f, 应在[0,1]内\n", results.R2);
end

% 检查2：物理约束
if all(results.predicted >= 0)
    checksPassed = checksPassed + 1;
else
    fprintf("  ❌ 检查2失败: 预测值为负数（物理上不可能）\n");
end

% 检查3：误差可接受
if results.MAPE < 20
    checksPassed = checksPassed + 1;
else
    fprintf("  ⚠️ 检查3: MAPE=%.2f%% > 20%%（模型可能需要改进）\n", results.MAPE);
end

% 检查4：优化收敛
if results.converged
    checksPassed = checksPassed + 1;
else
    fprintf("  ❌ 检查4失败: 优化未收敛\n");
end

% 检查5：图表文件存在
figFiles = dir(fullfile(results.projectRoot, "figures", "*.png"));
if ~isempty(figFiles)
    checksPassed = checksPassed + 1;
else
    fprintf("  ❌ 检查5失败: 图表文件未生成\n");
end

score = checksPassed / checksTotal;
fprintf("\n  自检得分: %d/%d (%.0f%%)\n", checksPassed, checksTotal, score*100);
passed = score >= 0.8;
end
```

---

## 五、可视化标准模板

```matlab
function fig = createStandardFigure(x, y, yPred, residuals, bootstrapParams, ...
    sensitivityResults, projectRoot)
% CREATESTANDARDFIGURE 生成标准四宫格分析图
fig = figure("Visible", "off");
style = apply_publication_style(fig, "zh", "report");
t = tiledlayout(fig, 2, 2, "TileSpacing", "compact", "Padding", "compact");

% (1) 左上：数据与拟合对比
ax1 = nexttile(1);
scatter(ax1, x, y, 30, style.colors(1,:), "filled", ...
    "MarkerEdgeAlpha", 0.6, "DisplayName", "实测");
hold(ax1, "on");
xSmooth = linspace(min(x), max(x), 200)';
plot(ax1, xSmooth, yPred(xSmooth), "Color", style.colors(4,:), ...
    "LineWidth", 1.1, "DisplayName", "拟合");
hold(ax1, "off");
xlabel(ax1, "x"); ylabel(ax1, "y");
title(ax1, "(a) 数据与模型拟合");
legend(ax1, "Location", "best");

% (2) 右上：残差分析
ax2 = nexttile(2);
yline(ax2, 0, "Color", [0.5 0.5 0.5], "LineStyle", "--");
hold(ax2, "on");
scatter(ax2, x, residuals, 30, style.colors(2,:), "filled", "MarkerEdgeAlpha", 0.6);
rStd = std(residuals);
patch(ax2, [x; flipud(x)], [2*rStd*ones(size(x)); -2*rStd*ones(size(x))], ...
    [0.5 0.5 0.5], "FaceAlpha", 0.12, "EdgeColor", "none");
hold(ax2, "off");
xlabel(ax2, "x"); ylabel(ax2, "残差");
title(ax2, "(b) 残差分布");

% (3) 左下：参数分布或 Q-Q 图
ax3 = nexttile(3);
if size(bootstrapParams, 1) > 10
    histogram(ax3, bootstrapParams(:,1), 20, "FaceAlpha", 0.5);
    hold(ax3, "on");
    histogram(ax3, bootstrapParams(:,2), 20, "FaceAlpha", 0.5);
    hold(ax3, "off");
    xlabel(ax3, "参数值"); ylabel(ax3, "频数");
end
title(ax3, "(c) 参数 Bootstrap 分布");

% (4) 右下：灵敏度分析
ax4 = nexttile(4);
barh(ax4, maxChanges, 0.5);
set(ax4, "YTickLabel", paramNames);
xlabel(ax4, "最大输出变化 (%)");
title(ax4, "(d) 参数灵敏度分析");

export_publication_figure(fig, fullfile(projectRoot, "figures", "result_qN_std"));
end
```

---

## 六、MATLAB vs Python 对照速查

| 操作 | Python (NumPy/SciPy) | MATLAB |
|------|---------------------|--------|
| 线性方程组 | `np.linalg.solve(A, b)` | `A \ b` |
| 最小二乘 | `np.linalg.lstsq(A, b)` | `A \ b` 或 `lsqr` |
| 伪逆 | `np.linalg.pinv(A)` | `pinv(A)` |
| 特征值 | `np.linalg.eig(A)` | `eig(A)` 或 `[V,D]=eig(A)` |
| SVD | `np.linalg.svd(A)` | `[U,S,V]=svd(A)` |
| 非线性优化 | `scipy.optimize.minimize` | `fmincon` / `fminunc` / `lsqnonlin` |
| 线性规划 | `scipy.optimize.linprog` | `linprog` |
| 整数规划 | `pulp` 库 | `intlinprog` |
| ODE 求解 | `scipy.integrate.solve_ivp` | `ode45` / `ode15s` / `ode23s` |
| 插值 | `scipy.interpolate.interp1d` | `interp1` / `griddedInterpolant` |
| 拟合 | `scipy.optimize.curve_fit` | `fit` / `lsqcurvefit` |
| 滤波 | `scipy.signal` | `filter` / `smoothdata` |
| FFT | `np.fft.fft` | `fft` |
| 主成分分析 | `sklearn.decomposition.PCA` | `pca` |
| 统计检验 | `scipy.stats.ttest_ind` | `ttest2` |
| 相关系数 | `np.corrcoef` | `corrcoef` |
| 随机数 | `np.random` | `rand`/`randn`/`randi` + `rng(seed)` |
| 表格操作 | `pd.DataFrame` | `table` / `readtable` / `writetable` |
| 并行循环 | —（需额外库） | `parfor` |
| 符号计算 | `sympy` | `syms` / Symbolic Math Toolbox |
