#!/usr/bin/env python3
"""生成 C 题输入预读摘要，避免反复解析原始大附件。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


PROBLEM_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
TABLE_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_hashes(directory: Path, extensions: set[str]) -> dict[str, str]:
    before: dict[str, str] = {}
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            before[str(path.relative_to(directory))] = sha256_file(path)
    return before


def pdf_summary(path: Path) -> list[str]:
    lines = [f"## PDF: {path.name}", f"size_bytes: {path.stat().st_size}"]
    try:
        import pypdf
    except ImportError:
        lines.append("状态: pypdf 未安装，无法提取文本层")
        return lines
    try:
        reader = pypdf.PdfReader(str(path))
        lines.append(f"pages: {len(reader.pages)}")
        sample = []
        for page in reader.pages[:4]:
            text = (page.extract_text() or "").strip()
            if text:
                sample.append(text[:600])
        if sample:
            lines.append("text_layer: available")
            lines.append("sample:")
            lines.extend(sample)
        else:
            lines.append("text_layer: empty_or_scanned")
    except Exception as exc:
        lines.append(f"status: read_error: {exc}")
    return lines


def excel_summary(path: Path) -> list[str]:
    lines = [f"## 表格: {path.name}", f"size_bytes: {path.stat().st_size}"]
    try:
        import pandas as pd
    except ImportError:
        lines.append("状态: pandas 未安装，无法检查表格")
        return lines
    try:
        if path.suffix.lower() == ".csv":
            frame = pd.read_csv(path, nrows=2000)
            lines.extend(_frame_summary("csv", frame))
            return lines
        sheets = pd.read_excel(path, sheet_name=None, nrows=500)
        for name, frame in sheets.items():
            lines.append(f"## sheet: {name}")
            lines.extend(_frame_summary(f"sheet:{name}", frame))
    except Exception as exc:
        lines.append(f"状态: read_error: {exc}")
    return lines


def _frame_summary(label: str, frame) -> list[str]:
    lines = [
        f"source: {label}",
        f"shape: {frame.shape[0]} rows x {frame.shape[1]} cols",
        "columns: " + ", ".join(str(c) for c in frame.columns.tolist()),
        "dtypes: " + ", ".join(f"{c}:{frame[c].dtype}" for c in frame.columns),
    ]
    if not frame.empty:
        lines.append("head:")
        lines.append(frame.head(5).to_string(index=False))
        lines.append("tail:")
        lines.append(frame.tail(3).to_string(index=False))
    lines.append("missing_total: " + str(int(frame.isna().sum().sum())))
    exact_duplicates = int(frame.duplicated().sum())
    lines.append("exact_duplicate_rows: " + str(exact_duplicates))
    return lines


def write_if_different(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="预读 C 题文档与数据")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--problem-dir", type=Path, default=Path("题目"))
    parser.add_argument("--data-dir", type=Path, default=Path("数据"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    problem_dir = root / args.problem_dir
    data_dir = root / args.data_dir
    problem_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    current_hashes = collect_hashes(data_dir, TABLE_EXTENSIONS) | collect_hashes(problem_dir, PROBLEM_EXTENSIONS)
    hash_path = data_dir / "处理前哈希.json"
    previous_hashes: dict[str, str] = {}
    if hash_path.exists() and not args.force:
        try:
            previous_hashes = json.loads(hash_path.read_text(encoding="utf-8"))
        except Exception:
            previous_hashes = {}

    hash_changed = current_hashes != previous_hashes
    problem_text = problem_dir / "题目内容.txt"
    data_text = data_dir / "数据摘要.txt"

    if hash_changed or args.force or not problem_text.exists() or not data_text.exists():
        problem_parts: list[str] = ["# 题目预读"]
        data_parts: list[str] = ["# 数据摘要"]
        for path in sorted(problem_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in PROBLEM_EXTENSIONS:
                if path.name in {"题目内容.txt"}:
                    continue
                if path.suffix.lower() == ".pdf":
                    problem_parts.extend(pdf_summary(path))
                else:
                    problem_parts.append(f"## {path.name}")
                    problem_parts.append(path.read_text(encoding="utf-8", errors="ignore")[:12000])
        for path in sorted(data_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in TABLE_EXTENSIONS:
                if path.name in {"数据摘要.txt", "处理前哈希.json"}:
                    continue
                data_parts.extend(excel_summary(path))
        write_if_different(problem_text, "\n\n".join(problem_parts) + "\n")
        write_if_different(data_text, "\n\n".join(data_parts) + "\n")
        hash_path.write_text(json.dumps(current_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "problem_summary": str(problem_text),
        "data_summary": str(data_text),
        "hash_path": str(hash_path),
        "hash_changed": hash_changed,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

