#!/usr/bin/env python3
"""审计 C 题图表演化合同：标题、丑图风险、重复文件和来源登记。"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".svg"}


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_python_titles(root: Path) -> list[dict]:
    issues: list[dict] = []
    for path in root.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                name = node.func.attr
                if name in {"set_title", "title", "suptitle"}:
                    issues.append({
                        "file": str(path),
                        "line": getattr(node, "lineno", None),
                        "call": name,
                    })
    return issues


def collect_images(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.suffix.lower() in IMAGE_EXTENSIONS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--title-scan-dir", type=Path, default=Path("src"))
    parser.add_argument("--image-dir", type=Path, default=Path("figures"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()

    title_issues = scan_python_titles(root / args.title_scan_dir)
    images = collect_images(root / args.image_dir)
    by_hash: dict[str, list[str]] = {}
    for path in images:
        by_hash.setdefault(hash_file(path), []).append(str(path))
    duplicates = [{"hash": digest, "files": files} for digest, files in by_hash.items() if len(files) > 1]

    report = {
        "image_count": len(images),
        "title_issues": title_issues,
        "duplicate_images": duplicates,
        "status": "PASS" if not title_issues and not duplicates else "FAIL",
    }
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

