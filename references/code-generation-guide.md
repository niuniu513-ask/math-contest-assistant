# 代码模式参考

> 本文件中的代码是教学模式和局部示例，不是所有赛题的强制骨架。先遵循 `编程工作流程.md` 和当前模型合同，再按需复用相关片段。示例中的数据、参数范围、评估指标和图表不得直接当作当前题结果。

## 公共代码头与两阶段执行（强制基线）

### 公共代码头（Python 默认模板）

每个新建求解脚本以公共头开始，按实际依赖裁剪，但保留中文字体配置与统一输出封装：

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os, warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from matplotlib import font_manager as _font_manager
_CJK_FONT_PREF = ['SimHei', 'Microsoft YaHei', 'Noto Sans CJK SC',
                  'Source Han Sans SC', 'WenQuanYi Zen Hei', 'PingFang SC',
                  'Heiti SC', 'STHeiti', 'Songti SC', 'Arial Unicode MS']
_installed_fonts = {f.name for f in _font_manager.fontManager.ttflist}
_cjk_font = next((n for n in _CJK_FONT_PREF if n in _installed_fonts), None)
if _cjk_font is None:
    import warnings as _warnings
    _warnings.warn('未检测到常用中文字体，导出前必须检查中文是否缺字。', RuntimeWarning)
    _cjk_font = 'DejaVu Sans'
plt.rcParams['font.sans-serif'] = [_cjk_font, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

PROJECT_ROOT = os.environ.get('PROJECT_ROOT') or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(PROJECT_ROOT, 'figures')
OUT_DIR = os.path.join(PROJECT_ROOT, 'results')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

def save_fig(fig, name):
    """保存图片；文件名与论文引用一致（中文论文可中文名，美赛一律英文）。"""
    fig.savefig(os.path.join(FIG_DIR, name))
    plt.close(fig)

def save_csv(df, name):
    df.to_csv(os.path.join(OUT_DIR, name), index=False, encoding='utf-8-sig')
```

- `sys.stdout` UTF-8 重包装：解决 Windows 中文乱码，脚本内所有中文输出都依赖这两行。
- matplotlib 用 Agg 后端（无界面），**动态选择已安装的中文字体**（SimHei/YaHei/Noto Sans CJK 等优先），避免静态字体表在缺字体机器上产生乱码/缺字；未检测到中文字体时给出警告，此时必须报告 BLOCKED，不得提交缺字图。`axes.unicode_minus=False` 保证负号正常；输出 150 DPI、tight bbox。
- 落盘统一走 `save_fig`/`save_csv`：图片进 `figures/`、结果进 `results/`（相对 `PROJECT_ROOT`，可用环境变量覆盖）；文件名与论文引用一致，LaTeX 模板（cumcm-jayxin）建议英文/数字命名避免编码问题。

### 两阶段执行（先算后画）

1. **第一阶段纯计算**：加载 → 预处理 → 建模 → 求解，得到全部数值结果；打印每组数据的 min/max/mean/std/CV/amplitude 等统计量，供论文直接引用，避免“先画图再回填数字”。
2. **第二阶段绘图**：数值检查通过后统一画图，每题至少 4–6 张覆盖主要分析维度；图内不写 `set_title`（标题由论文 `\caption{}` 承担）；图内文字必须是**可读字符串**——中文题可用中文或英文可读标签（同一图内尽量一致），**禁止直接把英文列名、变量名、聚类标签（如 `highK`、`Cluster_0`、`PC1`）当作图例**，必须先映射为完整可读标签（如 `高钾` / `High-K`）；美赛全英文。
3. 已有 CSV/图片直接复用，不重复计算；输出文件与论文引用一一对应。

该两阶段规则同样适用于 MATLAB 求解脚本：先完成全部计算并打印统计量，再统一 `apply_publication_style` 绘图。

## 一、示例代码骨架（按任务裁剪）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题N：XXX 的求解
方法：XXX
数学原理：[简述核心公式]
作者：math-contest-assistant
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import optimize, integrate, stats
import warnings
warnings.filterwarnings('ignore')

# === 全局设置 ===
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
np.random.seed(42)
np.set_printoptions(precision=4, suppress=True)

# ============================================================
# 第一步：数据准备
# ============================================================
# 原则：题设中的少量常数可集中定义；附件数据应从只读文件加载并记录哈希
# 格式：使用有意义的变量名、单位和来源注释

print("=== 第一步：数据准备 ===")
# 示例：附件1的测量数据（表1，第2-6行）
time_points = np.array([0, 60, 120, 180, 240, 300])  # 时间点 (s)
x_data = np.array([...])  # x坐标 (cm)，来源：附件1 Sheet1
y_data = np.array([...])  # y坐标 (cm)

# 常量定义（全部大写）
GRAVITY = 9.8          # 重力加速度 (m/s²)
MAX_SPEED = 2.0        # 最大速度限制 (m/s)
SAFE_DISTANCE = 1.7    # 安全距离 (m)

print(f"  数据量: {len(time_points)} 个时间点")
print(f"  x范围: [{x_data.min():.2f}, {x_data.max():.2f}]")
print(f"  y范围: [{y_data.min():.2f}, {y_data.max():.2f}]")

# ============================================================
# 第二步：数据预处理（如需要）
# ============================================================
print("\n=== 第二步：数据预处理 ===")

# 缺失值检测和处理
if np.any(np.isnan(x_data)):
    print("  检测到缺失值，使用线性插值填充")
    # 线性插值填充
    mask = np.isnan(x_data)
    x_data[mask] = np.interp(
        np.flatnonzero(mask),
        np.flatnonzero(~mask),
        x_data[~mask]
    )

# 异常值检测（3σ原则）
mean_val = np.mean(x_data)
std_val = np.std(x_data)
outliers = np.abs(x_data - mean_val) > 3 * std_val
if np.any(outliers):
    print(f"  检测到 {np.sum(outliers)} 个异常值（>3σ），已标记")

# ============================================================
# 第三步：核心模型
# ============================================================
print("\n=== 第三步：核心模型求解 ===")

def core_model(params, x):
    """
    [模型名称]
    
    数学原理: y = f(x; params)
    
    Parameters
    ----------
    params : array_like
        模型参数 [a, b, c, ...]
    x : array_like
        自变量
    
    Returns
    -------
    y_pred : ndarray
        模型预测值
    """
    a, b, c = params
    # 计算公式: y = a * exp(-b * x) + c
    return a * np.exp(-b * x) + c

def objective_function(params, x, y_true):
    """目标函数：最小化均方误差"""
    y_pred = core_model(params, x)
    return np.mean((y_pred - y_true) ** 2)

# 参数初值设定（基于对问题的物理理解）
# 例如：a ≈ max(y) ≈ 10, b ≈ 0.1（衰减速率）, c ≈ 0
initial_guess = [10.0, 0.1, 0.0]

# 使用 scipy.optimize 求解
result = optimize.minimize(
    objective_function,
    initial_guess,
    args=(time_points, y_data),
    method='L-BFGS-B',
    bounds=[(0, None), (0, None), (None, None)]  # 参数物理约束
)

optimal_params = result.x
y_predicted = core_model(optimal_params, time_points)

print(f"  优化状态: {'成功' if result.success else '失败'}")
print(f"  最优参数: {optimal_params}")
print(f"  目标函数值: {result.fun:.6f}")

# 计算评估指标
residuals = y_data - y_predicted
ss_res = np.sum(residuals ** 2)
ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
r_squared = 1 - ss_res / ss_tot
rmse = np.sqrt(np.mean(residuals ** 2))
mae = np.mean(np.abs(residuals))
mape = np.mean(np.abs(residuals / (y_data + 1e-10))) * 100

print(f"\n  模型评估:")
print(f"  R² = {r_squared:.4f}")
print(f"  RMSE = {rmse:.4f}")
print(f"  MAE = {mae:.4f}")
print(f"  MAPE = {mape:.2f}%")

# ============================================================
# 第四步：收敛性/稳定性分析
# ============================================================
print("\n=== 第四步：收敛性分析 ===")

# 方法1：不同初始值的收敛性
print("  测试不同初始值的收敛性...")
initial_trials = [
    [5.0, 0.05, -1.0],
    [15.0, 0.2, 1.0],
    [8.0, 0.15, -0.5],
    [12.0, 0.08, 0.5]
]
for i, init in enumerate(initial_trials):
    res = optimize.minimize(objective_function, init, args=(time_points, y_data),
                           method='L-BFGS-B',
                           bounds=[(0, None), (0, None), (None, None)])
    params_diff = np.max(np.abs(res.x - optimal_params) / (np.abs(optimal_params) + 1e-10))
    print(f"    试验{i+1}: 收敛={'是' if res.success else '否'}, "
          f"参数最大偏差={params_diff:.2%}")

# 方法2：Bootstrap 重采样评估参数稳定性
n_bootstrap = 100
bootstrap_params = []
for _ in range(n_bootstrap):
    indices = np.random.choice(len(time_points), len(time_points), replace=True)
    try:
        res = optimize.minimize(objective_function, initial_guess,
                               args=(time_points[indices], y_data[indices]),
                               method='L-BFGS-B',
                               bounds=[(0, None), (0, None), (None, None)])
        if res.success:
            bootstrap_params.append(res.x)
    except:
        pass

if len(bootstrap_params) > 10:
    bootstrap_params = np.array(bootstrap_params)
    param_std = np.std(bootstrap_params, axis=0)
    print(f"\n  Bootstrap 参数稳定性 (n={len(bootstrap_params)}):")
    for i, name in enumerate(['a', 'b', 'c']):
        print(f"    {name}: {np.mean(bootstrap_params[:, i]):.4f} ± {param_std[i]:.4f}")

# ============================================================
# 第五步：灵敏度分析
# ============================================================
print("\n=== 第五步：灵敏度分析 ===")

# 关键参数 ±20%，分 5 个水平
sensitivity_ratios = np.array([0.8, 0.9, 1.0, 1.1, 1.2])
param_names = ['参数a', '参数b', '参数c']
sensitivity_results = {}

for i, (name, base_val) in enumerate(zip(param_names, optimal_params)):
    print(f"\n  {name} (基准值={base_val:.4f}) 的灵敏度:")
    results_for_param = []
    for ratio in sensitivity_ratios:
        # 扰动当前参数，保持其他参数不变
        perturbed_params = optimal_params.copy()
        perturbed_params[i] = base_val * ratio
        
        y_perturbed = core_model(perturbed_params, time_points)
        rmsd = np.sqrt(np.mean((y_perturbed - y_predicted) ** 2))
        relative_change = (np.mean(y_perturbed) - np.mean(y_predicted)) / (np.mean(y_predicted) + 1e-10) * 100
        
        results_for_param.append({
            'ratio': ratio,
            'param_value': perturbed_params[i],
            'rmsd': rmsd,
            'relative_change': relative_change
        })
        print(f"    比例={ratio:.1f} (值={perturbed_params[i]:.4f}), "
              f"RMSD={rmsd:.4f}, 输出变化={relative_change:+.2f}%")
    
    sensitivity_results[name] = results_for_param

# 计算每个参数的最大影响
print("\n  灵敏度总结:")
for name, results in sensitivity_results.items():
    max_change = max(abs(r['relative_change']) for r in results)
    sensitivity_level = "高" if max_change > 10 else "中" if max_change > 3 else "低"
    print(f"    {name}: 最大输出变化 {max_change:.2f}% → 灵敏度: {sensitivity_level}")

# ============================================================
# 第六步：可视化
# ============================================================
print("\n=== 第六步：生成图表 ===")

fig = plt.figure(figsize=(16, 12))

# 子图1：数据趋势与模型拟合
ax1 = fig.add_subplot(2, 2, 1)
ax1.scatter(time_points, y_data, c='red', s=50, marker='o', 
           label='实测数据', zorder=5, edgecolors='darkred', linewidths=1)
t_smooth = np.linspace(time_points.min(), time_points.max(), 200)
y_smooth = core_model(optimal_params, t_smooth)
ax1.plot(t_smooth, y_smooth, 'b-', linewidth=2, alpha=0.8, 
        label=f'模型拟合 (R²={r_squared:.3f})')
ax1.set_xlabel('时间 (s)', fontsize=12)
ax1.set_ylabel('值', fontsize=12)
# 图内不写标题，标题由论文 \caption{} 承担
ax1.legend(loc='best', fontsize=10)
ax1.grid(True, alpha=0.3)

# 子图2：残差分布
ax2 = fig.add_subplot(2, 2, 2)
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax2.scatter(time_points, residuals, c='green', s=60, marker='D', 
           edgecolors='darkgreen', linewidths=1, zorder=5)
ax2.fill_between(time_points, -2*np.std(residuals), 2*np.std(residuals), 
                 alpha=0.2, color='gray', label='±2σ')
ax2.set_xlabel('时间 (s)', fontsize=12)
ax2.set_ylabel('残差', fontsize=12)
# 图内不写标题，标题由论文 \caption{} 承担
ax2.legend(loc='best', fontsize=10)
ax2.grid(True, alpha=0.3)

# 子图3：收敛性曲线（使用梯度下降类方法时）/ Bootstrap分布
ax3 = fig.add_subplot(2, 2, 3)
if len(bootstrap_params) > 10:
    for i in range(min(3, bootstrap_params.shape[1])):
        ax3.hist(bootstrap_params[:, i], bins=20, alpha=0.5, 
                label=f'{param_names[i]} ({np.mean(bootstrap_params[:, i]):.3f}±{np.std(bootstrap_params[:, i]):.3f})')
    ax3.set_xlabel('参数值', fontsize=12)
    ax3.set_ylabel('频数', fontsize=12)
    # 图内不写标题，标题由论文 \caption{} 承担
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)

# 子图4：灵敏度分析龙卷风图
ax4 = fig.add_subplot(2, 2, 4)
y_pos = np.arange(len(param_names))
max_changes = []
for name in param_names:
    changes = [abs(r['relative_change']) for r in sensitivity_results[name]]
    max_changes.append(max(changes))

colors = ['#e74c3c' if c > 10 else '#f39c12' if c > 3 else '#2ecc71' for c in max_changes]
bars = ax4.barh(y_pos, max_changes, color=colors, edgecolor='black', linewidth=0.5, height=0.5)
ax4.set_yticks(y_pos)
ax4.set_yticklabels(param_names)
ax4.set_xlabel('最大输出变化 (%)')
# 图内不写标题，标题由论文 \caption{} 承担
ax4.axvline(x=3, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='中灵敏度阈值')
ax4.axvline(x=10, color='red', linestyle='--', linewidth=1, alpha=0.5, label='高灵敏度阈值')
for bar, val in zip(bars, max_changes):
    ax4.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2, 
            f'{val:.1f}%', va='center', fontsize=9)
ax4.legend(loc='lower right', fontsize=8)
ax4.grid(True, alpha=0.3, axis='x')

# 图内不写总标题，标题由论文 \caption{} 承担
plt.tight_layout()
plt.savefig('qN_results.pdf', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print(f"  图表已保存: qN_results.pdf")

# ============================================================
# 第七步：结果汇总与导出
# ============================================================
print("\n" + "=" * 60)
print("求解完成 — 结果汇总")
print("=" * 60)

final_results = {
    '问题编号': 'N',
    '方法': 'XXX',
    '最优参数': optimal_params.tolist(),
    '参数名': param_names,
    'R²': round(r_squared, 4),
    'RMSE': round(rmse, 4),
    'MAE': round(mae, 4),
    'MAPE': round(mape, 2),
    '收敛性': '通过' if result.success else '未通过',
    '最大灵敏度': round(max(max_changes), 2),
    '最敏感参数': param_names[np.argmax(max_changes)],
    'Bootstrap样本数': len(bootstrap_params)
}

for key, val in final_results.items():
    if isinstance(val, list):
        print(f"  {key}: {val}")
    else:
        print(f"  {key}: {val}")

# 保存结果到 JSON 供论文使用
import json
with open('qN_final_results.json', 'w', encoding='utf-8') as f:
    json.dump(final_results, f, ensure_ascii=False, indent=2)

print("\n结果已保存到 qN_final_results.json")
```

## 二、按方法类型的代码模板

### 2.1 评价类（AHP / TOPSIS / 熵权法 / 模糊评价 / 灰色关联）

**共同模式**：矩阵输入 → 数据正向化/标准化 → 权重确定 → 得分计算 → 排序输出

```python
# === 评价类通用模板 ===
def normalize_matrix(X, method='vector'):
    """矩阵标准化
    method='vector': 向量归一化 (TOPSIS)
    method='range': 极差归一化
    method='zscore': Z-score 标准化
    """
    if method == 'vector':
        return X / np.sqrt(np.sum(X**2, axis=0))
    elif method == 'range':
        return (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0))
    elif method == 'zscore':
        return (X - X.mean(axis=0)) / X.std(axis=0)

# TOPSIS 核心
def topsis(X, weights):
    """TOPSIS 法：X为标准化矩阵, weights为权重向量"""
    # 加权标准化矩阵
    V = X * weights
    # 正理想解和负理想解
    v_plus = np.max(V, axis=0)
    v_minus = np.min(V, axis=0)
    # 各方案到正负理想解的距离
    d_plus = np.sqrt(np.sum((V - v_plus)**2, axis=1))
    d_minus = np.sqrt(np.sum((V - v_minus)**2, axis=1))
    # 相对贴近度（得分）
    scores = d_minus / (d_plus + d_minus)
    return scores

# 熵权法核心
def entropy_weight(X):
    """熵权法计算客观权重"""
    n, m = X.shape
    # 归一化
    P = X / X.sum(axis=0)
    # 处理 log(0)
    P = np.where(P == 0, 1e-10, P)
    # 信息熵
    e = -np.sum(P * np.log(P), axis=0) / np.log(n)
    # 权重
    w = (1 - e) / np.sum(1 - e)
    return w

# 灰色关联分析核心
def grey_relational(X):
    """灰色关联分析：X每行是一个方案，返回关联度"""
    # 确定参考序列（取每列最优值）
    ref = np.max(X, axis=0)
    # 绝对差
    abs_diff = np.abs(X - ref)
    # 关联系数 (ρ=0.5)
    rho = 0.5
    min_diff = abs_diff.min()
    max_diff = abs_diff.max()
    gamma = (min_diff + rho * max_diff) / (abs_diff + rho * max_diff)
    # 关联度
    return np.mean(gamma, axis=1)
```

### 2.2 优化类（线性规划 / PSO / GA / 模拟退火 / 动态规划）

**共同模式**：定义目标函数 → 定义约束 → 选择优化算法 → 求解 → 验证最优性

```python
# === 线性规划 ===
from scipy.optimize import linprog

# min c^T x  subject to: A_ub x <= b_ub, A_eq x = b_eq, bounds
c = np.array([-3, -4])  # 负号因为 linprog 是 minimize
A_ub = np.array([[1, 2], [3, 1], [0, 1]])
b_ub = np.array([100, 120, 30])
bounds = [(0, None), (0, None)]  # x_i >= 0

result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
print(f"最优解: x1={result.x[0]:.2f}, x2={result.x[1]:.2f}")
print(f"最优值: {-result.fun:.2f}")  # 转回 maximize

# === 整数规划 (使用 pulp) ===
# import pulp
# prob = pulp.LpProblem("Problem", pulp.LpMaximize)
# x1 = pulp.LpVariable("x1", lowBound=0, cat='Integer')
# ...

# === 遗传算法 (核心片断) ===
def genetic_algorithm(objective_func, bounds, pop_size=50, generations=200,
                      crossover_rate=0.8, mutation_rate=0.1):
    """遗传算法求解连续优化问题"""
    n_params = len(bounds)
    
    # 初始化种群
    population = np.random.uniform(
        low=[b[0] for b in bounds],
        high=[b[1] for b in bounds],
        size=(pop_size, n_params)
    )
    
    best_fitness_history = []
    
    for gen in range(generations):
        # 评估适应度
        fitness = np.array([objective_func(ind) for ind in population])
        best_fitness_history.append(fitness.max())
        
        # 选择（锦标赛选择）
        selected = tournament_selection(population, fitness, tournament_size=3)
        
        # 交叉（模拟二进制交叉 SBX）
        offspring = sbx_crossover(selected, crossover_rate)
        
        # 变异（高斯变异）
        offspring = gaussian_mutation(offspring, mutation_rate, bounds)
        
        # 精英保留
        elite_idx = np.argmax(fitness)
        offspring[0] = population[elite_idx].copy()
        
        population = offspring
    
    # 返回最优解
    final_fitness = np.array([objective_func(ind) for ind in population])
    best_idx = np.argmax(final_fitness)
    return population[best_idx], final_fitness[best_idx], best_fitness_history

def tournament_selection(population, fitness, tournament_size=3):
    """锦标赛选择"""
    selected = np.zeros_like(population)
    for i in range(len(population)):
        candidates = np.random.choice(len(population), tournament_size, replace=False)
        winner = candidates[np.argmax(fitness[candidates])]
        selected[i] = population[winner].copy()
    return selected

# === 粒子群优化 (PSO) 核心 ===
def pso(objective_func, bounds, n_particles=30, max_iter=100):
    """粒子群优化"""
    n_dims = len(bounds)
    
    # 初始化
    positions = np.random.uniform(
        low=[b[0] for b in bounds],
        high=[b[1] for b in bounds],
        size=(n_particles, n_dims)
    )
    velocities = np.random.uniform(-1, 1, (n_particles, n_dims))
    
    # 个体最优和全局最优
    p_best_pos = positions.copy()
    p_best_val = np.array([objective_func(p) for p in positions])
    g_best_idx = np.argmin(p_best_val)
    g_best_pos = p_best_pos[g_best_idx].copy()
    g_best_val = p_best_val[g_best_idx]
    
    w = 0.7    # 惯性权重
    c1 = 1.5   # 认知系数
    c2 = 1.5   # 社会系数
    
    history = [g_best_val]
    
    for iter in range(max_iter):
        for i in range(n_particles):
            r1, r2 = np.random.rand(n_dims), np.random.rand(n_dims)
            velocities[i] = (w * velocities[i] + 
                           c1 * r1 * (p_best_pos[i] - positions[i]) +
                           c2 * r2 * (g_best_pos - positions[i]))
            positions[i] += velocities[i]
            # 边界处理
            for d in range(n_dims):
                positions[i, d] = np.clip(positions[i, d], bounds[d][0], bounds[d][1])
        
        # 更新最优
        for i in range(n_particles):
            val = objective_func(positions[i])
            if val < p_best_val[i]:
                p_best_val[i] = val
                p_best_pos[i] = positions[i].copy()
                if val < g_best_val:
                    g_best_val = val
                    g_best_pos = positions[i].copy()
        
        history.append(g_best_val)
    
    return g_best_pos, g_best_val, history
```

### 2.3 预测类（回归 / 灰色预测 / ARIMA / 蒙特卡洛）

```python
# === 灰色预测 GM(1,1) ===
def gm11(x0, predict_n=5):
    """
    灰色预测 GM(1,1) 模型
    
    Parameters
    ----------
    x0 : array_like
        原始数据序列（至少4个数据点）
    predict_n : int
        预测步数
    
    Returns
    -------
    x0_predict : ndarray
        预测值
    grade : float
        模型精度等级（越小越好）
    """
    x0 = np.array(x0, dtype=float)
    n = len(x0)
    
    # 步骤1：级比检验
    lambda_k = x0[:-1] / x0[1:]
    if not (np.all(lambda_k > np.exp(-2/(n+1))) and 
            np.all(lambda_k < np.exp(2/(n+1)))):
        print("  警告：级比检验未通过，考虑对数据平移变换")
    
    # 步骤2：一次累加生成 (1-AGO)
    x1 = np.cumsum(x0)
    
    # 步骤3：构造数据矩阵B和数据向量Y
    # -z1(k) = -0.5 * (x1(k) + x1(k-1)), k=2,3,...,n
    z1 = -0.5 * (x1[1:] + x1[:-1])
    B = np.column_stack([z1, np.ones(n-1)])
    Y = x0[1:]
    
    # 步骤4：最小二乘估计参数 [a, b]^T
    # [a, b]^T = (B^T B)^{-1} B^T Y
    a, b = np.linalg.inv(B.T @ B) @ B.T @ Y
    
    # 步骤5：白化方程的时间响应函数
    # x1_hat(k+1) = (x0(1) - b/a) * exp(-a*k) + b/a
    def gm11_response(k):
        return (x0[0] - b/a) * np.exp(-a * k) + b/a
    
    # 步骤6：预测（还原）
    k_values = np.arange(-1, n + predict_n)  # 从 k=-1 开始（对应原始第1个点）
    x1_hat_all = gm11_response(k_values)
    x1_hat_all[0] = x0[0]  # 修正：x1_hat(1) = x0(1)
    
    # IAGO 还原
    x0_hat_all = np.diff(x1_hat_all)
    x0_hat = x0_hat_all[:n]      # 拟合值
    x0_predict = x0_hat_all[n:]  # 预测值
    
    # 步骤7：精度检验
    residual = x0 - x0_hat
    relative_error = np.abs(residual) / (x0 + 1e-10)
    
    # 后验差比 C = S2/S1
    S1 = np.std(x0, ddof=1)
    S2 = np.std(residual, ddof=1)
    C = S2 / (S1 + 1e-10)
    
    # 小误差概率 P
    avg_residual = np.mean(residual)
    P = np.mean(np.abs(residual - avg_residual) < 0.6745 * S1)
    
    # 精度等级评定
    if P > 0.95 and C < 0.35:
        grade = "一级（好）"
    elif P > 0.80 and C < 0.50:
        grade = "二级（合格）"
    elif P > 0.70 and C < 0.65:
        grade = "三级（勉强）"
    else:
        grade = "四级（不合格）"
    
    print(f"  灰色预测 GM(1,1) 结果:")
    print(f"    发展系数 a={a:.6f}, 灰作用量 b={b:.4f}")
    print(f"    后验差比 C={C:.4f}, 小误差概率 P={P:.4f}")
    print(f"    精度等级: {grade}")
    print(f"    平均相对误差: {np.mean(relative_error)*100:.2f}%")
    print(f"    预测值: {x0_predict}")
    
    return x0_predict, C, x0_hat

# === ARIMA 模型 ===
def arima_model(data, order=(1,1,1), forecast_steps=5):
    """ARIMA 时间序列预测"""
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    
    # ADF 平稳性检验
    adf_result = adfuller(data, autolag='AIC')
    print(f"  ADF 检验: 统计量={adf_result[0]:.4f}, p值={adf_result[1]:.4f}")
    print(f"  结论: {'平稳' if adf_result[1] < 0.05 else '非平稳，需要差分'}")
    
    # 拟合 ARIMA
    model = ARIMA(data, order=order)
    fitted = model.fit()
    
    print(f"  AIC={fitted.aic:.2f}, BIC={fitted.bic:.2f}")
    
    # 预测
    forecast = fitted.forecast(steps=forecast_steps)
    conf_int = fitted.get_forecast(steps=forecast_steps).conf_int()
    
    # 残差诊断
    residuals = fitted.resid
    # Ljung-Box 白噪声检验
    from statsmodels.stats.diagnostic import acorr_ljungbox
    lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)
    print(f"  Ljung-Box 检验 p值: {lb_test['lb_pvalue'].values[0]:.4f}")
    
    return forecast, conf_int, fitted
```

### 2.4 微分方程类（ODE / SIR / 热传导）

```python
# === ODE 数值求解通用模板 ===
from scipy.integrate import solve_ivp

def ode_system(t, y, params):
    """
    微分方程组
    y = [y1, y2, y3, ...]
    params = (a, b, c, ...)
    返回 dy/dt = [dy1/dt, dy2/dt, ...]
    """
    y1, y2, y3 = y
    a, b, c = params
    
    dy1_dt = -a * y1 + b * y2
    dy2_dt = a * y1 - b * y2 - c * y2
    dy3_dt = c * y2
    
    return [dy1_dt, dy2_dt, dy3_dt]

# 初始条件
y0 = [1000, 1, 0]  # [S0, I0, R0]
params = (0.3, 0.1, 0.05)  # [α, β, γ]

# 时间范围
t_span = (0, 100)
t_eval = np.linspace(0, 100, 1000)

# 求解
solution = solve_ivp(ode_system, t_span, y0, args=(params,), 
                     t_eval=t_eval, method='RK45', rtol=1e-8, atol=1e-10)

if solution.success:
    y1, y2, y3 = solution.y
    print(f"  求解成功，{len(solution.t)} 个时间步")
    print(f"  稳态值: y1={y1[-1]:.4f}, y2={y2[-1]:.4f}, y3={y3[-1]:.4f}")
else:
    print(f"  求解失败: {solution.message}")
```

### 2.5 图论类（最短路径 / TSP / 最大流）

```python
# === Floyd 全源最短路径 ===
def floyd_warshall(graph):
    """
    Floyd-Warshall 全源最短路径
    graph: 邻接矩阵, graph[i][j] = 距离, inf = 不可达
    """
    n = len(graph)
    dist = graph.copy()
    path = np.zeros((n, n), dtype=int)  # 记录路径
    
    for k in range(n):       # 中间节点
        for i in range(n):   # 起始节点
            for j in range(n):  # 终止节点
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    path[i][j] = k
    
    return dist, path

# === Dijkstra 单源最短路径（手动实现，不依赖 networkx） ===
def dijkstra(graph, start):
    """Dijkstra 单源最短路径（邻接矩阵实现）"""
    n = len(graph)
    visited = np.zeros(n, dtype=bool)
    dist = np.full(n, np.inf)
    dist[start] = 0
    
    for _ in range(n):
        # 选择未访问的最近节点
        u = np.argmin(np.where(visited, np.inf, dist))
        visited[u] = True
        
        # 更新邻居
        for v in range(n):
            if not visited[v] and graph[u][v] < np.inf:
                new_dist = dist[u] + graph[u][v]
                if new_dist < dist[v]:
                    dist[v] = new_dist
    
    return dist
```

## 三、数据处理模式

### 3.1 题设中的少量常数或手工核对样例

```python
# === 模式：手工录入用于核对的少量题设常数 ===
# 附件 Excel/CSV 应由读取函数加载；这里只适合题干中明确给出的少量常数或手算样例
# 每行注释标注原始位置、单位和用途

# 附件1: 2024年1-6月销售额（万元），Sheet "月度汇总"，行3-8
sales_2024_h1 = np.array([120.5, 135.2, 142.8, 156.3, 148.9, 162.7])

# 附件2: 各供应商报价（元），表2，列B
supplier_prices = np.array([8.5, 9.2, 7.8, 10.1, 8.9])

# 附件3: 距离矩阵 (km)，5个城市之间的距离
distance_matrix = np.array([
    [0, 120, 85, 200, 150],
    [120, 0, 95, 180, 130],
    [85, 95, 0, 160, 110],
    [200, 180, 160, 0, 90],
    [150, 130, 110, 90, 0]
])
```

### 3.2 从赛题文本提取参数

```python
# === 模式：赛题中直接给出的物理参数 ===
# 格式：变量名 = 数值  # 物理含义 (来源：赛题第X页)

# 赛题第2页：板凳参数
BENCH_LENGTH = 3.41      # 板凳长度 (m)
BENCH_WIDTH = 0.30       # 板凳宽度 (m)
HOLE_SPACING = 0.275     # 孔距 (m)
HOLE_DIAMETER = 0.055    # 孔径 (m)

# 赛题第3页：约束条件
MAX_SPEED = 1.0           # 最大速度 (m/s)
SPACING = 0.55            # 板凳间距 (m)
MIN_SAFE_DIST = 1.7       # 最小安全距离 (m)

# 赛题第4页：时间点
TIME_POINTS = np.array([0, 60, 120, 180, 240, 300])  # 观测时刻 (s)
```

### 3.3 坐标/几何数据

```python
# === 模式：几何/坐标数据的结构化录入 ===
# 格式：np.array([[x1,y1], [x2,y2], ...])

# 附件 result1.xlsx: 龙头板凳在 t=0s 时刻的位置坐标
dragon_head_at_t0 = np.array([
    [0.000, 0.000],    # 节点1（龙头前端）
    [0.275, 0.000],    # 节点2
    [0.550, 0.000],    # 节点3
    # ... 共201个节点
])

# 附件 result2.xlsx: 障碍物坐标
obstacles = np.array([
    [15.0, 20.0, 5.0],  # [x, y, radius]
    [35.0, 40.0, 3.0],
])
```

## 四、常见错误自愈策略

### 4.1 代码执行失败的自动修复

| 错误类型 | 典型报错 | 自动修复策略 |
|----------|----------|-------------|
| 导入错误 | `ModuleNotFoundError: No module named 'xxx'` | 使用 `numpy`/`scipy`/`matplotlib`/`pandas`/`sklearn` 替代；或改用纯 Python 实现 |
| 维度不匹配 | `ValueError: operands could not be broadcast together` | 打印 `.shape` 定位 → 添加 `.reshape(-1,1)` 或 `.flatten()` |
| 除零错误 | `RuntimeWarning: divide by zero` | 分母加 `1e-10`；或使用 `np.where(denom==0, 0, num/denom)` |
| 优化不收敛 | `Optimization did not converge` | 换初始值；换 `method`；加约束 `bounds`；对数据做归一化 |
| 矩阵奇异 | `LinAlgError: Singular matrix` | 用 `np.linalg.pinv`（伪逆）替代 `np.linalg.inv` |
| 中文方框 | 图表中中文显示为 □ | 尝试 `'WenQuanYi Micro Hei'`, `'Arial Unicode MS'`；或改用英文标签 |
| 内存溢出 | `MemoryError` | 减少网格分辨率/样本量/迭代次数 |
| 超时 | 执行超过 300 秒 | 减少 `n_samples` / `generations` / `t_eval` 点数；用向量化替代循环 |
| NaN 传播 | `RuntimeWarning: invalid value` | 检查输入范围（如 log/√ 的负数）→ 添加 `np.clip` 或 `np.maximum(x, 1e-10)` |

### 4.2 自检代码模式

```python
# === 每个脚本末尾强制自检 ===
def run_self_checks(result_dict):
    """求解结果自检"""
    checks_passed = 0
    checks_total = 5
    
    # 检查1：数值范围合理性
    if 0 <= result_dict['R_squared'] <= 1:
        checks_passed += 1
    else:
        print(f"  ❌ 检查1失败: R²={result_dict['R_squared']}, 应在[0,1]内")
    
    # 检查2：物理约束
    if result_dict['predicted_value'] >= 0:
        checks_passed += 1
    else:
        print(f"  ❌ 检查2失败: 预测值为负数（物理上不可能）")
    
    # 检查3：误差可接受
    if result_dict['mape'] < 20:
        checks_passed += 1
    else:
        print(f"  ⚠️ 检查3: MAPE={result_dict['mape']}% > 20%（模型可能需要改进）")
    
    # 检查4：灵敏度合理
    if result_dict['max_sensitivity'] < 100:
        checks_passed += 1
    else:
        print(f"  ⚠️ 检查4: 最大灵敏度 > 100%，模型可能不稳定")
    
    # 检查5：图表文件存在
    import os
    if os.path.exists('qN_results.pdf'):
        checks_passed += 1
    else:
        print(f"  ❌ 检查5失败: 图表文件未生成")
    
    score = checks_passed / checks_total
    print(f"\n  自检得分: {checks_passed}/{checks_total} ({score*100:.0f}%)")
    return score >= 0.8  # 至少80%通过
```

## 五、可视化标准模板

```python
# === 标准四宫格图表布局 ===
def create_standard_figure(data, prediction, residuals, sensitivity):
    """生成标准四宫格分析图"""
    fig = plt.figure(figsize=(16, 12))
    
    # (1) 左上：数据与拟合对比
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.scatter(x, y, c='#e74c3c', s=40, label='实测', zorder=5)
    ax1.plot(x_smooth, y_pred, '#2980b9', lw=2, label='拟合')
    ax1.set_xlabel('x', fontsize=12)
    ax1.set_ylabel('y', fontsize=12)
    # 图内不写标题，标题由论文 \caption{} 承担
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # (2) 右上：残差分析
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.axhline(y=0, color='gray', ls='--', lw=1)
    ax2.scatter(x, residuals, c='#27ae60', s=40, zorder=5)
    ax2.fill_between(x, -2*residuals.std(), 2*residuals.std(), 
                     alpha=0.2, color='gray')
    ax2.set_xlabel('x', fontsize=12)
    ax2.set_ylabel('残差', fontsize=12)
    # 图内不写标题，标题由论文 \caption{} 承担
    ax2.grid(True, alpha=0.3)
    
    # (3) 左下：Q-Q图或收敛曲线
    ax3 = fig.add_subplot(2, 2, 3)
    from scipy import stats
    stats.probplot(residuals, dist="norm", plot=ax3)
    # 图内不写标题，标题由论文 \caption{} 承担
    ax3.grid(True, alpha=0.3)
    
    # (4) 右下：灵敏度分析
    ax4 = fig.add_subplot(2, 2, 4)
    # [灵敏度龙卷风图或折线图]
    # 图内不写标题，标题由论文 \caption{} 承担
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
```
