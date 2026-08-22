#!/usr/bin/env python3
"""Audit visible Word text colors and font slots for the CUMCM C workflow."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TEXT_PART_PREFIXES = ("word/document.xml", "word/header", "word/footer", "word/footnotes.xml", "word/endnotes.xml")
BLACK_VALUES = {None, "000000", "00000000", "auto"}


def audit(path: Path) -> dict:
    issues: list[dict] = []
    checked_runs = 0
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.startswith(TEXT_PART_PREFIXES) and name.endswith(".xml")]
        for name in names:
            root = ET.fromstring(archive.read(name))
            for index, run in enumerate(root.iter(W + "r"), start=1):
                text = "".join(node.text or "" for node in run.iter(W + "t"))
                if not text.strip():
                    continue
                checked_runs += 1
                rpr = run.find(W + "rPr")
                color = east_asia = ascii_font = hansi_font = None
                if rpr is not None:
                    color_node = rpr.find(W + "color")
                    if color_node is not None:
                        color = color_node.get(W + "val")
                    fonts = rpr.find(W + "rFonts")
                    if fonts is not None:
                        east_asia = fonts.get(W + "eastAsia")
                        ascii_font = fonts.get(W + "ascii")
                        hansi_font = fonts.get(W + "hAnsi")
                if color not in BLACK_VALUES:
                    issues.append({"part": name, "run": index, "type": "non_black_text", "value": color, "text": text[:80]})
                if east_asia and east_asia not in {"宋体", "黑体", "楷体", "仿宋"}:
                    issues.append({"part": name, "run": index, "type": "unexpected_east_asia_font", "value": east_asia, "text": text[:80]})
                for slot, value in (("ascii", ascii_font), ("hAnsi", hansi_font)):
                    if value and value not in {"Times New Roman", "Cambria Math"}:
                        issues.append({"part": name, "run": index, "type": f"unexpected_{slot}_font", "value": value, "text": text[:80]})
    return {"file": str(path), "checked_runs": checked_runs, "issues": issues, "status": "PASS" if not issues else "FAIL"}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 DOCX 正文性文字颜色和字体槽")
    parser.add_argument("docx", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit(args.docx.resolve())
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if args.strict and report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
