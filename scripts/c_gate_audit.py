#!/usr/bin/env python3
"""Validate C-problem gate artifacts without running a contest solution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "D1": ["data/数据质量报告.json", "data/处理决策日志.json", "data/处理前后统计对照.csv", ".work/data-contract.json", "数据预处理与探索分析.md"],
    "B1": [".work/baseline-registry.json", "results/baselines"],
    "M1": [".work/model-contract.json", ".work/model-complexity.json"],
}


def nonempty(path: Path) -> bool:
    if path.is_dir():
        return any(item.is_file() and item.stat().st_size > 0 for item in path.rglob("*"))
    return path.is_file() and path.stat().st_size > 0


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 C 题 D1/B1/M1 证据产物")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--gate", choices=tuple(REQUIRED), required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    checks = [{"path": rel, "ok": nonempty(root / rel)} for rel in REQUIRED[args.gate]]
    report = {"gate": args.gate, "status": "PASS" if all(item["ok"] for item in checks) else "FAIL", "checks": checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
