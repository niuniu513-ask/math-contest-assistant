#!/usr/bin/env python3
"""C 题统一 matplotlib 绘图模板。默认不强制禁止其他绘图库，但复用本模板可获得一致风格。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def apply_style() -> None:
    plt.rcParams.update({
        "font.sans-serif": [
            "STHeiti", "SimHei", "Heiti TC",
            "Microsoft YaHei", "Songti SC", "Arial Unicode MS",
            "PingFang SC", "DejaVu Sans",
        ],
        "axes.unicode_minus": False,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "figure.autolayout": True,
    })


def despine(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.3, linestyle="--")


def save_fig(fig: plt.Figure, name: str, directory: str | Path) -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    out = path / name
    fig.savefig(out)
    plt.close(fig)
    return out


def save_csv(df: pd.DataFrame, name: str, directory: str | Path) -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    out = path / name
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def print_group_stats(*, series: Iterable = None, df: pd.DataFrame = None,
                      columns: Iterable[str] = None, label: str = "数据") -> None:
    """打印 min/max/mean/std/CV/amplitude，供论文引用。"""
    if series is not None:
        values = pd.Series(list(series)).dropna()
        _print_stats(label, values)
        return
    if df is None or columns is None:
        raise ValueError("print_group_stats 需要 series 或 df+columns")
    for column in columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        _print_stats(f"{label}.{column}", values)


def _print_stats(label: str, values: pd.Series) -> None:
    if values.empty:
        print(f"{label}: 无有效数值")
        return
    mean = float(values.mean())
    std = float(values.std(ddof=0))
    amplitude = float(values.max() - values.min())
    cv = std / mean if abs(mean) > 1e-12 else float("nan")
    print(
        f"{label}: min={values.min():.6g} max={values.max():.6g} "
        f"mean={mean:.6g} std={std:.6g} CV={cv:.6g} amplitude={amplitude:.6g}"
    )


apply_style()

