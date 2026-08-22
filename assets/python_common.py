#!/usr/bin/env python3
"""C 题脚本公共配置：Windows UTF-8 输出与统一环境检查。"""

from __future__ import annotations

import sys


def ensure_utf8_stdout() -> None:
    """让 Windows 控制台中的中文与符号稳定输出为 UTF-8。"""
    if sys.stdout is not None and hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def configure() -> None:
    ensure_utf8_stdout()


configure()

