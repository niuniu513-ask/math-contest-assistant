# C题图表与可视化规范

## 默认库

默认使用 matplotlib，生成统一、可复现、可审计的 PNG/PDF。确有需要时可以使用其他必要库，但必须在交付清单中记录理由与依赖，不能为了视觉特效绕过本项目风格。

## 统一配置

使用 `assets/c_plot_template.py`，至少覆盖：

```python
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['STHeiti','SimHei','Microsoft YaHei','Songti SC','DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'
```

```python
ax.grid(alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
```

调色板默认使用 `viridis`、`RdBu_r`、`tab10`、`Set3`。不得为了图表美观使用无解释的主题色。

## 先算后画

每个求解脚本分两阶段：

1. 读数据、预处理、建模、求解，保存全部数值；
2. 打印每组 `min/max/mean/std/CV/amplitude`，再绘图。

绘图不得作为检查模型正确性的前置依赖。

## 图文分离

- 图内不写 `set_title()`；图题目由论文 `\caption{}` 承担；
- 图内只保留数据、坐标轴、刻度、图例；图例与标签必须可读；
- 图表中文字体统一，负号正确；
- 图表颜色不得是论文正文黑色的例外，除非确有数据区分需要。

## 图表类型

按数据与结论选择：

| 类型 | 适用 |
|---|---|
| 柱状图 | 类别对比、分组对比 |
| 折线图 | 时间变化、趋势 |
| 散点图 | 双变量关系、分布 |
| 箱线图 | 多组分布与离群 |
| 热力图 | 矩阵与相关性 |
| 饼图 | 少类别的构成占比 |

相同结论不重复绘制多张图。

## 目录与来源

图保存为：

```text
求解/问题X/图片/
```

结果保存为：

```text
求解/问题X/结果/
```

每张图必须可追溯到源数据、脚本、关键数值和所属子问题。生成后立即登记到 `results/图表清单.json` 与 `results/图片哈希.json`。

## 质量验收

在 P2 或 W2 阶段运行 `scripts/figure_audit.py` 与 `scripts/c_plot_contract_audit.py`，检查：

- 文件存在、非空、尺寸正常；
- 分辨率与 `\textwidth` 匹配程度；
- 标签、刻度、图例是否齐全；
- 是否存在重复图；
- 灰度可辨性；
- Python 代码是否存在不必要的 `set_title()`；
- 图片来源是否绑定结果链。

