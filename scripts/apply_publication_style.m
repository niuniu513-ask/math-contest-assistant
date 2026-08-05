function style = apply_publication_style(fig, language, widthProfile, opts)
%APPLY_PUBLICATION_STYLE 为数学建模论文图应用统一出版样式。
%   style = APPLY_PUBLICATION_STYLE(fig, language, widthProfile)
%   支持两种配色方案：竞赛获奖配色（默认）和 Nature/Wong 期刊配色。
%
%   Inputs:
%     fig          — 目标 figure 句柄
%     language     — "zh"(中文) | "en"(英文)，默认 "zh"
%     widthProfile — "single"(3.5in) | "double"(7.2in) | "report"(6.3in)，默认 "report"
%     opts.profile — "competition"(竞赛获奖配色, 默认) | "nature"(Nature/Wong色板)
%
%   Outputs:
%     style — 含 font, colors, sizeInches 的结构体，后续绘图直接引用
%
%   Example:
%     fig = figure("Visible","off");
%     style = apply_publication_style(fig, "zh", "report", "profile", "competition");
%     plot(x, y, "Color", style.colors(1,:), "LineWidth", 1.5);
%     export_publication_figure(fig, "figures/result_q1");

arguments
    fig (1,1) matlab.ui.Figure
    language (1,1) string {mustBeMember(language,["zh","en"])} = "zh"
    widthProfile (1,1) string {mustBeMember(widthProfile,["single","double","report"])} = "report"
    opts.profile (1,1) string {mustBeMember(opts.profile,["competition","nature"])} = "competition"
end

% === 尺寸设定 ===
widths = struct("single", 3.5, "double", 7.2, "report", 6.3);
widthIn = widths.(widthProfile);

% === 配色方案 ===
if opts.profile == "competition"
    % 竞赛获奖配色 — 来自历年国赛一等奖作品 + B站晴天教程实战验证
    % 高对比度、适合黑白打印、色觉友好
    colors = [
        0.906 0.298 0.235;   % #E74C3C  Coral红   — 数据散点、关键标记
        0.161 0.502 0.725;   % #2980B9  Steel蓝   — 拟合曲线、主要方法
        0.153 0.682 0.376;   % #27AE60  Emerald绿 — 残差、辅助指标
        0.082 0.592 0.647;   % #1597A5  DeepTeal  — 收敛曲线、PSO/GA
        0.953 0.612 0.071;   % #F39C12  Amber橙   — 警告阈值、灵敏度中
        0.204 0.596 0.859;   % #3498DB  Dodger蓝  — 第二方法、对比柱
        0.584 0.647 0.651;   % #95A5A6  Cloud灰   — 参考线、网格、次要
    ];
else
    % Nature/Wong 期刊配色 — 色觉友好、低饱和度、符合 SCI 期刊规范
    colors = [
        0.0000 0.4471 0.6980;   % #0072B2  Blue
        0.9020 0.6235 0.0000;   % #E69F00  Orange
        0.0000 0.6196 0.4510;   % #009E73  Green
        0.8353 0.3686 0.0000;   % #D55E00  Vermillion
        0.8000 0.4745 0.6549;   % #CC79A7  Purple
        0.3373 0.7059 0.9137;   % #56B4E9  Sky Blue
        0.4196 0.4471 0.5020;   % #6B7280  Gray
    ];
end

% === 字体选择 ===
fontName = chooseFont(language);

% === 设置图窗尺寸 ===
fig.Units = "inches";
fig.Position(3:4) = [widthIn, widthIn * 0.62];
fig.Color = "white";

% === 全局默认样式 ===
set(fig, "DefaultAxesFontName", fontName, ...
    "DefaultAxesFontSize", 7.5, ...
    "DefaultAxesLineWidth", 0.7, ...
    "DefaultAxesTitleFontSizeMultiplier", 1.0, ...
    "DefaultAxesTitleFontWeight", "normal", ...
    "DefaultAxesLabelFontSizeMultiplier", 1.0, ...
    "DefaultAxesColorOrder", colors, ...
    "DefaultLineLineWidth", 1.1, ...
    "DefaultLineMarkerSize", 3.5, ...
    "DefaultLegendBox", "off");

% === 逐坐标轴应用 ===
axesList = findall(fig, "Type", "axes");
for k = 1:numel(axesList)
    ax = axesList(k);
    ax.FontName = fontName;
    ax.FontSize = 7.5;
    ax.LineWidth = 0.7;
    ax.TitleFontSizeMultiplier = 1.0;
    ax.TitleFontWeight = "normal";
    ax.LabelFontSizeMultiplier = 1.0;
    ax.ColorOrder = colors;
    ax.Box = "off";
    grid(ax, "off");
end

% === 返回样式结构体 ===
style = struct(...
    "font", fontName, ...
    "colors", colors, ...
    "sizeInches", [widthIn, widthIn * 0.62], ...
    "profile", opts.profile);
end

function fontName = chooseFont(language)
% 按语言和系统可用字体选择
fonts = string(listfonts);
if language == "zh"
    candidates = ["Noto Sans CJK SC", "Source Han Sans SC", ...
        "Microsoft YaHei", "SimHei", "PingFang SC"];
else
    candidates = ["Arial", "Helvetica", "Times New Roman"];
end
fontName = "Helvetica";
for candidate = candidates
    if any(strcmpi(fonts, candidate))
        fontName = candidate;
        return;
    end
end
warning("未找到首选字体，导出后必须检查中文与特殊符号是否缺字。");
end
