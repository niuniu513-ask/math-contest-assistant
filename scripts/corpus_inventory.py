#!/usr/bin/env python3
"""为赛题、获奖论文和模板建立轻量可检索清单。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


YEAR_RE = re.compile(r"(?:19|20)\d{2}")
PROBLEM_RE = re.compile(r"(?<![A-Za-z])([A-E])(?:题|\d{2,3}|\b)", re.I)
DEFAULT_QUESTION_DIR_NAME = "1.历年国赛赛题（1992-2025）"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_metadata(path: Path) -> tuple[str | None, str | None]:
    text = "/".join(path.parts)
    year_match = YEAR_RE.search(text)
    problem_match = PROBLEM_RE.search(path.stem) or PROBLEM_RE.search(text)
    return (
        year_match.group(0) if year_match else None,
        problem_match.group(1).upper() if problem_match else None,
    )


def scan(root: Path, kind: str, include_hash: bool, questions_dir_name: str = DEFAULT_QUESTION_DIR_NAME) -> list[dict]:
    records = []
    if not root.is_dir():
        return records
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if kind == "award_paper" and questions_dir_name in relative.parts:
            continue
        year, problem = infer_metadata(relative)
        record = {
            "kind": kind,
            "root": str(root),
            "path": str(relative),
            "extension": path.suffix.casefold(),
            "bytes": path.stat().st_size,
            "year": year,
            "problem_id": problem,
        }
        if include_hash:
            record["sha256"] = sha256_file(path)
        records.append(record)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="建立数学建模本地语料清单")
    parser.add_argument("--questions-root", type=Path)
    parser.add_argument("--papers-root", type=Path)
    parser.add_argument("--latex-root", type=Path)
    parser.add_argument("--word-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hash", action="store_true", help="计算全部文件 SHA-256（大型语料较慢）")
    parser.add_argument(
        "--questions-dir-name",
        default=DEFAULT_QUESTION_DIR_NAME,
        help="赛题目录名（用于排除获奖论文目录中嵌套的赛题副本），默认按当前语料布局",
    )
    args = parser.parse_args()

    roots = (
        (args.questions_root, "question"),
        (args.papers_root, "award_paper"),
        (args.latex_root, "latex_template"),
        (args.word_root, "word_template"),
    )
    records = []
    missing = []
    for raw_root, kind in roots:
        if raw_root is None:
            continue
        root = raw_root.expanduser().resolve()
        if not root.is_dir():
            missing.append(str(root))
            continue
        records.extend(scan(root, kind, args.hash, args.questions_dir_name))

    summary = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": len(records),
        "by_kind": dict(Counter(record["kind"] for record in records)),
        "by_extension": dict(Counter(record["extension"] for record in records)),
        "missing_roots": missing,
        "notes": [
            "获奖论文目录中的嵌套历年赛题副本已排除",
            "此清单只提供发现与过滤；使用前仍须回读原文件",
        ],
        "files": records,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "files"}, ensure_ascii=False))
    return 1 if missing and not records else 0


if __name__ == "__main__":
    raise SystemExit(main())
