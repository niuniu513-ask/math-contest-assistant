#!/usr/bin/env python3
"""检查 LaTeX 摘要是否超过一页。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def find_aux(project_root: Path) -> Path | None:
    for path in project_root.rglob("*.aux"):
        return path
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--label", default="abstract:end")
    args = parser.parse_args()
    root = args.project_root.resolve()
    aux = find_aux(root)
    if aux is None:
        print("未找到 aux 文件，无法检查摘要页码", file=sys.stderr)
        return 2
    content = aux.read_text(encoding="utf-8", errors="ignore")
    pattern = rf"\\newlabel\{{{re.escape(args.label)}}}\{{\{{(\d+)\}}\{{(\d+)\}}"
    match = re.search(pattern, content)
    if not match:
        print("摘要结束标签未找到", file=sys.stderr)
        return 2
    page = int(match.group(2))
    print(json.dumps({"abstract_end_page": page, "ok": page <= 1}, ensure_ascii=False))
    return 0 if page <= 1 else 1

if __name__ == "__main__":
    raise SystemExit(main())
