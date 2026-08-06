#!/usr/bin/env python3
"""Audit mathematical-modeling manuscripts for semantic writing completeness.

This complements DOCX/LaTeX structural validators. It audits the canonical Markdown
source before layout conversion, where formulas, figure placement, and internal
benchmark leakage are easiest to detect deterministically.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


TREND_PATTERNS = (
    r"呈现", r"显示", r"可见", r"分布", r"趋势", r"峰值", r"谷值",
    r"最大", r"最小", r"上升", r"下降", r"集中", r"差异", r"变化",
    r"收敛", r"误差", r"波动", r"拐点", r"斜率",
)
CAUSE_PATTERNS = (
    r"由于", r"原因", r"源于", r"这是因为", r"导致", r"受.+影响",
    r"机制", r"约束", r"由.+决定", r"与.+有关",
)
IMPLICATION_PATTERNS = (
    r"说明", r"意味着", r"因此", r"启示", r"支持", r"据此", r"需要",
    r"应当", r"反映", r"可用于", r"决定了", r"提示",
)
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:\s*%|\s*[a-zA-Zμ°]+)?")

EMPTY_FIGURE_PHRASES = (
    "该图用于说明本节的几何关系或数值结果",
    "该图用于说明本节结果",
    "由图可知模型效果较好",
    "由表可知模型效果较好",
)

BENCHMARK_LEAK_PATTERNS = {
    "同届或获奖论文": re.compile(r"(?:获奖论文|特等奖论文|同届论文|往届\s*[A-E]\d{2,3}|[A-E]\d{3}\s*(?:论文|获奖))", re.I),
    "内部对标元话语": re.compile(r"(?:用于对标|用于核对数量级|赛后核对|内部样本|benchmark[-_ ]?gap)", re.I),
    "内部门禁元话语": re.compile(r"(?:Claim.?Evidence|(?:^|[^A-Za-z0-9])[MPW][12](?:[^A-Za-z0-9]|$)|门禁证据)", re.I | re.M),
    "内部路径": re.compile(r"(?:[A-Za-z]:\\[^\s]+|/Users/[^\s]+|/home/[^\s]+|\.work[/\\])"),
}


def issue(severity: str, code: str, message: str, **evidence: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"severity": severity, "code": code, "message": message}
    if evidence:
        item["evidence"] = evidence
    return item


def strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def extract_docx_text(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    prose_paragraphs: list[str] = []
    for paragraph in root.iter(f"{w}p"):
        parts = [node.text or "" for node in paragraph.iter(f"{w}t")]
        if parts:
            value = "".join(parts)
            paragraphs.append(value)
            style_node = paragraph.find(f"./{w}pPr/{w}pStyle")
            style_id = style_node.get(f"{w}val", "") if style_node is not None else ""
            if not re.search(r"code|source|program|代码|程序", style_id, flags=re.I):
                prose_runs: list[str] = []
                for run in paragraph.iter(f"{w}r"):
                    run_style_node = run.find(f"./{w}rPr/{w}rStyle")
                    run_style = run_style_node.get(f"{w}val", "") if run_style_node is not None else ""
                    if re.search(r"code|source|program|代码|程序", run_style, flags=re.I):
                        continue
                    prose_runs.extend(node.text or "" for node in run.iter(f"{w}t"))
                prose_paragraphs.append("".join(prose_runs))
    return "\n".join(paragraphs), "\n".join(prose_paragraphs)


def audit_final_docx(path: Path, forbidden_terms: tuple[str, ...] = ()) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        return [issue("FAIL", "final_docx_missing", f"最终 DOCX 不存在: {path}")], {"final_docx_checked": False}
    try:
        text, prose_text = extract_docx_text(path)
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        return [issue("FAIL", "final_docx_unreadable", f"无法读取最终 DOCX: {exc}")], {"final_docx_checked": False}
    for phrase in EMPTY_FIGURE_PHRASES:
        if phrase in text:
            findings.append(issue("FAIL", "final_docx_empty_commentary", f"最终 DOCX 含模板化图表解读：{phrase}"))
    for name, pattern in BENCHMARK_LEAK_PATTERNS.items():
        matches = [match.group(0)[:120] for match in pattern.finditer(text)]
        if matches:
            findings.append(issue("FAIL", "final_docx_context_leak", f"最终 DOCX 检测到{name}", matches=matches[:10]))
    leaked_terms = [term for term in forbidden_terms if term.casefold() in text.casefold()]
    if leaked_terms:
        findings.append(issue("FAIL", "final_docx_dynamic_benchmark_leak", "最终 DOCX 命中内部对标样本禁漏词", matches=leaked_terms[:20]))
    prose_without_files = re.sub(r"(?:[A-Za-z]:\\|/)?(?:[^\s/\\]+[/\\])*[^\s/\\]+\.(?:py|m|csv|xlsx?|json|ya?ml|tex|md|png|jpe?g|svg|pdf|docx?|txt|log|dat|mat|npz|npy|ipynb)\b", " ", prose_text, flags=re.I)
    plain_math = []
    for pattern in (
        re.compile(r"(?<![\w\\])(?:[A-Za-z]|[α-ωΑ-Ω])_[A-Za-z0-9{}]+"),
        re.compile(r"(?<![\w\\])(?:\d+|[A-Za-z])\^(?:[-+]?\d+|\{[^}]+\})"),
    ):
        plain_math.extend(match.group(0) for match in pattern.finditer(prose_without_files))
    if plain_math:
        findings.append(issue("FAIL", "final_docx_plain_text_math", "最终 DOCX 仍含纯文本数学表达式，必须转换为 OMML", matches=plain_math[:30]))
    headings = extract_docx_headings(path)
    for (prev_style, prev_text), (curr_style, curr_text) in zip(headings, headings[1:]):
        if prev_text == curr_text:
            findings.append(issue("FAIL", "duplicate_docx_heading", f"最终 DOCX 存在重复连续标题：{curr_text}"))
    return findings, {"final_docx_checked": True, "final_docx_characters": len(text), "final_docx_plain_text_math": len(plain_math), "final_docx_headings": len(headings)}


def chinese_char_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def visual_file_is_readable(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    head = data[:512]
    suffix = path.suffix.lower()
    if suffix == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 45:
            return False
        position = 8
        width = height = 0
        seen_idat = seen_iend = False
        while position + 12 <= len(data):
            length = int.from_bytes(data[position:position + 4], "big")
            chunk_type = data[position + 4:position + 8]
            end = position + 12 + length
            if end > len(data):
                return False
            payload = data[position + 8:position + 8 + length]
            expected_crc = int.from_bytes(data[position + 8 + length:end], "big")
            if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != expected_crc:
                return False
            if chunk_type == b"IHDR" and length >= 8:
                width = int.from_bytes(payload[:4], "big")
                height = int.from_bytes(payload[4:8], "big")
            elif chunk_type == b"IDAT":
                seen_idat = True
            elif chunk_type == b"IEND":
                seen_iend = True
                break
            position = end
        return width >= 200 and height >= 120 and seen_idat and seen_iend
    if suffix in {".jpg", ".jpeg"}:
        if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
            return False
        position = 2
        while position + 9 < len(data):
            if data[position] != 0xFF:
                position += 1
                continue
            marker = data[position + 1]
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height = int.from_bytes(data[position + 5:position + 7], "big")
                width = int.from_bytes(data[position + 7:position + 9], "big")
                return width >= 200 and height >= 120
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                position += 2
                continue
            if position + 4 > len(data):
                return False
            segment_length = int.from_bytes(data[position + 2:position + 4], "big")
            if segment_length < 2:
                return False
            position += 2 + segment_length
        return False
    if suffix == ".gif":
        if not head.startswith((b"GIF87a", b"GIF89a")) or len(head) < 10:
            return False
        return int.from_bytes(head[6:8], "little") >= 200 and int.from_bytes(head[8:10], "little") >= 120
    if suffix == ".pdf":
        return head.startswith(b"%PDF-") and b"%%EOF" in data[-2048:] and b"/MediaBox" in data
    if suffix == ".svg":
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return False
        if not root.tag.lower().endswith("svg"):
            return False
        def svg_length(value: str | None) -> float | None:
            if not value:
                return None
            match = re.fullmatch(r"\s*([0-9.]+)\s*(px|pt|pc|mm|cm|in)?\s*", value, flags=re.I)
            if not match:
                return None
            factors = {"px": 1.0, "pt": 96 / 72, "pc": 16.0, "mm": 96 / 25.4, "cm": 96 / 2.54, "in": 96.0}
            return float(match.group(1)) * factors.get((match.group(2) or "px").lower(), 1.0)
        width = svg_length(root.attrib.get("width"))
        height = svg_length(root.attrib.get("height"))
        if width is not None and height is not None:
            return width >= 200 and height >= 120
        viewbox = root.attrib.get("viewBox") or root.attrib.get("viewbox")
        if viewbox:
            try:
                _, _, view_width, view_height = [float(value) for value in re.split(r"[\s,]+", viewbox.strip())]
            except (TypeError, ValueError):
                return False
            return view_width >= 200 and view_height >= 120
        return False
    return False


def next_prose(lines: list[str], start: int, max_paragraphs: int = 1) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("!["):
            break
        if stripped.startswith("\\[") or stripped.startswith("$$") or stripped.startswith("\\begin{"):
            break
        if re.match(r"^\s*\|?.*\|.*$", stripped):
            break
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
                if len(paragraphs) >= max_paragraphs:
                    break
            continue
        current.append(stripped)
    if current and len(paragraphs) < max_paragraphs:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs)


def has_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def audit_interpretation(kind: str, label: str, analysis: str, strict: bool) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    severity = "FAIL" if strict else "WARN"
    if chinese_char_count(analysis) < 80:
        findings.append(issue(severity, f"{kind}_analysis_short", f"{label} 后的解读过短，未形成完整分析段", chinese_chars=chinese_char_count(analysis)))
    layers = {
        "趋势/特征": has_any(analysis, TREND_PATTERNS),
        "成因": has_any(analysis, CAUSE_PATTERNS),
        "启示": has_any(analysis, IMPLICATION_PATTERNS),
        "定量值": bool(NUMBER_PATTERN.search(analysis)),
    }
    missing = [name for name, present in layers.items() if not present]
    if missing:
        findings.append(issue(severity, f"{kind}_analysis_layers", f"{label} 解读缺少：{', '.join(missing)}", analysis=analysis[:240]))
    return findings


def extract_display_math(text: str) -> list[tuple[int, str]]:
    blocks: list[tuple[int, str]] = []
    occupied: list[tuple[int, int]] = []
    patterns = (
        re.compile(r"\\\[(.*?)\\\]", re.S),
        re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}", re.S),
    )
    for pattern in patterns:
        for match in pattern.finditer(text):
            if any(start <= match.start() < end for start, end in occupied):
                continue
            occupied.append(match.span())
            blocks.append((text.count("\n", 0, match.start()) + 1, match.group(0)))
    return sorted(blocks)


def audit_formulas(text: str, strict: bool, min_equations: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    dollar_lines = [i + 1 for i, line in enumerate(text.splitlines()) if "$$" in line]
    if dollar_lines:
        findings.append(issue("FAIL", "double_dollar", "独立公式使用了被禁止的 $$...$$", lines=dollar_lines))

    blocks = extract_display_math(text)
    tags: list[int] = []
    unnumbered: list[int] = []
    signatures: list[str] = []
    for line, block in blocks:
        numeric = [int(value) for value in re.findall(r"\\tag\{(\d+)\}", block)]
        has_label = bool(re.search(r"\\label\{[^}]+\}", block))
        tags.extend(numeric)
        tag_matches = list(re.finditer(r"\\tag\{\d+\}", block))
        cursor = 0
        for tag_match in tag_matches:
            segment = block[cursor:tag_match.start()]
            signature = re.sub(r"\\(?:begin|end)\{[^}]+\}|\\label\{[^}]+\}|\\\[|\\\]|\\\\|\s+", "", segment)
            signatures.append(signature)
            cursor = tag_match.end()
        if not numeric and not has_label and "\\nonumber" not in block:
            unnumbered.append(line)
        position = text.find(block)
        following = text[position + len(block):position + len(block) + 2500] if position >= 0 else ""
        following = re.split(r"\n\s*(?:#|!\[|\\\[|\\begin\{)", following, maxsplit=1)[0]
        required_explanation_chars = 20 * max(1, len(numeric))
        missing_local_references = [
            number for number in numeric
            if not re.search(rf"(?:式|公式)\s*[（(]?{number}[）)]?", following)
        ]
        if chinese_char_count(following) < required_explanation_chars or missing_local_references:
            findings.append(issue("FAIL" if strict else "WARN", "equation_explanation_missing", f"第 {line} 行公式块后缺少逐式作用、变量或推导解释", required_chinese_chars=required_explanation_chars, missing_formula_references=missing_local_references))
    if unnumbered:
        findings.append(issue("FAIL" if strict else "WARN", "unnumbered_display_math", "检测到未编号、无 label 的独立公式", lines=unnumbered))
    if tags:
        expected = list(range(1, max(tags) + 1))
        if tags != expected:
            findings.append(issue("FAIL", "equation_number_sequence", "公式 tag 编号不是从 1 开始的全局连续序列", actual=tags, expected=expected))
        for number in tags:
            if not re.search(rf"(?:式|公式)\s*[（(]?{number}[）)]?", text):
                findings.append(issue("FAIL" if strict else "WARN", "equation_not_referenced", f"公式({number})未在正文中引用"))
    elif blocks:
        findings.append(issue("FAIL" if strict else "WARN", "no_numeric_equation_tags", "独立公式没有可检查的连续数字编号；若使用自动编号，应在最终 LaTeX/DOCX 校验中提供编号证据"))
    structural_signatures = [re.sub(r"_\{?\d+\}?", "_{k}", signature) for signature in signatures]
    duplicate_signatures = sorted({signature for signature in structural_signatures if structural_signatures.count(signature) > 1})
    if duplicate_signatures:
        findings.append(issue("FAIL" if strict else "WARN", "duplicate_equation_bodies", "存在仅改变公式编号或数字下标、数学作用相同的独立公式，不能拆式凑数量", duplicate_groups=len(duplicate_signatures)))
    valid_equations = len(set(signatures)) if tags else 0
    if strict and valid_equations < min_equations:
        findings.append(issue("FAIL", "equation_count_below_target", f"连续编号且内容不重复的有效公式少于完整竞赛论文质量目标 {min_equations} 个", actual=valid_equations, required=min_equations))
    return findings, {"display_equations": len(blocks), "valid_numbered_equations": valid_equations, "numeric_tags": tags, "double_dollar_lines": dollar_lines}


def audit_figures_and_tables(text: str, strict: bool, min_figures: int, project_root: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    lines = text.splitlines()
    figures = 0
    valid_figures = 0
    figure_hashes: set[str] = set()
    figure_files: list[str] = []
    tables = 0
    for index, line in enumerate(lines):
        match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if match:
            figures += 1
            label = match.group(1).strip() or f"第 {figures} 幅图"
            figure_ok = True
            candidate: Path | None = None
            if project_root is not None:
                raw_target = match.group(2).strip().strip("<>")
                if re.match(r"https?://", raw_target, flags=re.I):
                    figure_ok = False
                    findings.append(issue("FAIL", "external_figure_not_archived", f"{label} 使用外部链接，必须归档为项目内真实文件", path=raw_target))
                else:
                    candidate = (project_root / raw_target).resolve()
                    try:
                        candidate.relative_to(project_root.resolve())
                    except ValueError:
                        figure_ok = False
                        findings.append(issue("FAIL", "figure_path_escape", f"{label} 的路径越出项目目录", path=raw_target))
                    else:
                        if not candidate.exists() or not visual_file_is_readable(candidate):
                            figure_ok = False
                            findings.append(issue("FAIL", "figure_file_invalid", f"{label} 的图文件不存在或不是可识别的 PNG/JPEG/GIF/SVG/PDF", path=raw_target))
                        else:
                            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
                            if digest in figure_hashes:
                                figure_ok = False
                                findings.append(issue("FAIL", "duplicate_figure_file", f"{label} 与前图文件内容完全相同，不能重复复制凑图数", path=raw_target))
                            else:
                                figure_hashes.add(digest)
                                figure_files.append(raw_target.replace("\\", "/").casefold())
            if figure_ok:
                valid_figures += 1
            analysis = next_prose(lines, index + 1)
            findings.extend(audit_interpretation("figure", label, analysis, strict))
        if re.match(r"^\s*\|?\s*:?-{3,}", line) and "|" in line:
            title_context = " ".join(lines[max(0, index - 3):index])
            title_match = re.search(r"表\s*((?:[A-Za-z]+-)?\d+(?:-\d+)?)[^\n|]*", title_context)
            tables += 1
            if not title_match:
                findings.append(issue("FAIL" if strict else "WARN", "untitled_table", f"第 {index + 1} 行的 Markdown 表缺少邻近的‘表N’标题，无法建立引用和分析映射"))
            end = index + 1
            while end < len(lines) and ("|" in lines[end] or not lines[end].strip()):
                end += 1
            analysis = next_prose(lines, end)
            label = f"表{title_match.group(1)}" if title_match else f"第 {tables} 个表"
            findings.extend(audit_interpretation("table", label, analysis, strict))
    for phrase in EMPTY_FIGURE_PHRASES:
        if phrase in text:
            findings.append(issue("FAIL", "empty_figure_commentary", f"检测到模板化图表解读：{phrase}"))
    audited_figure_count = valid_figures if project_root is not None else figures
    if strict and audited_figure_count < min_figures:
        findings.append(issue("FAIL", "figure_count_below_target", f"存在真实文件且具备相邻定量分析的正式图少于完整竞赛论文质量目标 {min_figures} 幅", actual=audited_figure_count, required=min_figures))
    return findings, {"figures": audited_figure_count, "figure_markers": figures, "figure_files": figure_files, "figure_hashes": sorted(figure_hashes), "numbered_result_tables": tables}


def load_json(path: Path, label: str) -> tuple[Any | None, list[dict[str, Any]]]:
    if not path.exists():
        return None, [issue("FAIL", f"missing_{label}", f"缺少 {label}: {path}")]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [issue("FAIL", f"invalid_{label}", f"无法读取 {label}: {exc}")]


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def project_evidence_status(project_root: Path, value: Any) -> tuple[bool, str]:
    if not isinstance(value, str) or not value.strip():
        return False, "missing"
    candidate = (project_root / value).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError:
        return False, "escape"
    if not candidate.exists() or not candidate.is_file():
        return False, "missing"
    try:
        if candidate.stat().st_size <= 2:
            return False, "empty"
    except OSError:
        return False, "unreadable"
    return True, "ok"


def project_evidence_digest(project_root: Path, value: Any) -> str | None:
    exists, _ = project_evidence_status(project_root, value)
    if not exists:
        return None
    try:
        return hashlib.sha256((project_root / str(value)).resolve().read_bytes()).hexdigest()
    except OSError:
        return None


def audit_derivation_ledger(path: Path, project_root: Path, strict: bool) -> tuple[list[dict[str, Any]], dict[str, int]]:
    data, findings = load_json(path, "derivation_ledger")
    if data is None:
        return findings, {"models": 0}
    models = data.get("models", []) if isinstance(data, dict) else data
    if not isinstance(models, list) or not models:
        return findings + [issue("FAIL", "empty_derivation_ledger", "推导台账必须包含至少一个核心模型")], {"models": 0}
    required = ("model_id", "question", "model_type", "reality_mapping", "variables", "assumptions", "derivation_steps", "numerical_example", "validation", "evidence_paths", "ambiguity")
    cross_validated_models = 0
    fallback_validated_models = 0
    hard_constraint_ids: set[str] = set()
    for index, model in enumerate(models, 1):
        if not isinstance(model, dict):
            findings.append(issue("FAIL", "invalid_model_record", f"第 {index} 个模型记录不是对象"))
            continue
        model_id = model.get("model_id", f"model_{index}")
        missing = [field for field in required if not nonempty(model.get(field))]
        if missing:
            findings.append(issue("FAIL", "model_fields_missing", f"{model_id} 缺少推导字段：{', '.join(missing)}"))
        for variable in model.get("variables", []):
            if not isinstance(variable, dict) or not all(key in variable and variable[key] != "" for key in ("symbol", "meaning", "unit", "kind")):
                findings.append(issue("FAIL", "variable_definition_incomplete", f"{model_id} 存在未完整定义的变量", variable=variable))
        for assumption in model.get("assumptions", []):
            if not isinstance(assumption, dict) or not all(nonempty(assumption.get(key)) for key in ("statement", "condition", "error_scale")):
                findings.append(issue("FAIL", "assumption_evidence_incomplete", f"{model_id} 的假设缺少成立条件或误差量级", assumption=assumption))
        if len(model.get("derivation_steps", [])) < 2:
            findings.append(issue("FAIL", "derivation_too_short", f"{model_id} 少于两个可核对推导步骤"))
        example = model.get("numerical_example", {})
        if not isinstance(example, dict) or not all(nonempty(example.get(key)) for key in ("inputs", "calculation", "result")):
            findings.append(issue("FAIL", "numerical_example_incomplete", f"{model_id} 的数值代入示例不完整"))

        hard_constraints = model.get("hard_constraints")
        if not isinstance(hard_constraints, list) or any(not isinstance(value, str) or not value.strip() for value in hard_constraints):
            findings.append(issue("FAIL", "hard_constraints_invalid", f"{model_id} 必须用列表声明硬约束 ID；确实没有时填写空列表"))
        else:
            normalized_constraints = {value.strip() for value in hard_constraints}
            if len(normalized_constraints) != len(hard_constraints):
                findings.append(issue("FAIL", "hard_constraints_duplicate", f"{model_id} 的硬约束 ID 存在重复"))
            hard_constraint_ids.update(normalized_constraints)

        model_type = str(model.get("model_type", "")).lower()
        if model_type == "optimization":
            if not nonempty(model.get("objective")) or not nonempty(model.get("constraints")):
                findings.append(issue("FAIL", "optimization_definition_incomplete", f"{model_id} 未完整给出目标函数与全部约束"))
            if len(model.get("algorithm_steps", [])) < 2:
                findings.append(issue("FAIL", "optimization_algorithm_missing", f"{model_id} 缺少分步求解算法及作用说明"))
            optimization_fields = ("physical_goal", "optimized_goal", "goal_relationship", "direct_physical_objective_trial", "tradeoff_evidence")
            missing_optimization = [field for field in optimization_fields if not nonempty(model.get(field))]
            if missing_optimization:
                findings.append(issue("FAIL", "physical_goal_alignment_missing", f"{model_id} 未完成物理目标与优化目标对齐：{', '.join(missing_optimization)}"))
            direct_trial = model.get("direct_physical_objective_trial", {})
            trial_fields = ("objective", "result", "comparison", "evidence")
            if not isinstance(direct_trial, dict) or not all(nonempty(direct_trial.get(field)) for field in trial_fields):
                findings.append(issue("FAIL", "direct_physical_trial_incomplete", f"{model_id} 的直接物理目标试验缺少目标、结果、并列比较或证据文件"))
            else:
                exists, status = project_evidence_status(project_root, direct_trial.get("evidence"))
                if not exists:
                    findings.append(issue("FAIL", "direct_physical_trial_evidence_missing", f"{model_id} 的直接物理目标试验证据无效", path=direct_trial.get("evidence"), status=status))
            tradeoff = model.get("tradeoff_evidence")
            exists, status = project_evidence_status(project_root, tradeoff)
            if not exists:
                findings.append(issue("FAIL", "tradeoff_evidence_missing", f"{model_id} 的目标权衡证据文件无效", path=tradeoff, status=status))
        if model_type == "algorithmic" and len(model.get("algorithm_steps", [])) < 2:
            findings.append(issue("FAIL", "algorithm_steps_missing", f"{model_id} 缺少 Step 1, Step 2…及关键步骤作用"))
        if model_type in {"statistical", "machine_learning"}:
            pipeline = model.get("data_pipeline", {})
            required_pipeline = ("preprocessing", "feature_selection", "parameter_selection", "evaluation_metrics")
            missing_pipeline = [field for field in required_pipeline if not nonempty(pipeline.get(field))]
            if missing_pipeline:
                findings.append(issue("FAIL", "data_pipeline_incomplete", f"{model_id} 的统计/机器学习流程缺少：{', '.join(missing_pipeline)}"))

        ambiguity = str(model.get("ambiguity", "")).strip().lower()
        cross = model.get("cross_validation", {})
        fallback = model.get("sensitivity_fallback")
        methods = cross.get("methods", []) if isinstance(cross, dict) else []
        method_records_ok = len(methods) >= 2 and all(
            isinstance(method, dict)
            and all(nonempty(method.get(field)) for field in ("name", "principle", "result", "evidence"))
            and project_evidence_status(project_root, method.get("evidence"))[0]
            for method in methods
        )
        if method_records_ok and all(nonempty(cross.get(key)) for key in ("comparison_metric", "result", "difference_reason", "selection")):
            method_names = [str(method.get("name", "")).strip().casefold() for method in methods]
            method_principles = [re.sub(r"\s+", "", str(method.get("principle", "")).casefold()) for method in methods]
            method_digests = [project_evidence_digest(project_root, method.get("evidence")) for method in methods]
            if len(set(method_names)) < 2 or len(set(method_principles)) < 2 or None in method_digests or len(set(method_digests)) < 2:
                findings.append(issue("FAIL", "cross_validation_not_independent", f"{model_id} 的两种方法必须名称和原理不同，并绑定内容不同的结果证据"))
            else:
                cross_validated_models += 1
        elif ambiguity not in {"", "none", "无", "不存在", "not_applicable"}:
            if not nonempty(fallback):
                findings.append(issue("FAIL", "ambiguous_model_not_cross_validated", f"{model_id} 存在定义歧义，但没有两种独立方法或极端敏感性失效边界"))
            else:
                if not isinstance(fallback, dict) or not all(nonempty(fallback.get(field)) for field in ("extreme_cases", "failure_boundary", "evidence")):
                    findings.append(issue("FAIL", "sensitivity_fallback_incomplete", f"{model_id} 的极端敏感性替代验证缺少极端工况、失效边界或证据"))
                else:
                    exists, status = project_evidence_status(project_root, fallback.get("evidence"))
                    if not exists:
                        findings.append(issue("FAIL", "sensitivity_fallback_evidence_missing", f"{model_id} 的极端敏感性证据无效", path=fallback.get("evidence"), status=status))
                    else:
                        fallback_validated_models += 1

        for evidence_path in model.get("evidence_paths", []):
            candidate = (project_root / evidence_path).resolve()
            try:
                candidate.relative_to(project_root.resolve())
            except ValueError:
                findings.append(issue("FAIL", "evidence_path_escape", f"{model_id} 的证据路径越出项目目录", path=evidence_path))
                continue
            if not candidate.exists():
                findings.append(issue("FAIL", "evidence_path_missing", f"{model_id} 的证据文件不存在", path=evidence_path))
    if strict and cross_validated_models + fallback_validated_models == 0:
        findings.append(issue("FAIL", "no_independent_model_validation", "完整竞赛论文至少需要一个关键模型完成两种独立方法定量交叉验证，或提供有证据的极端敏感性失效边界"))

    if strict and not isinstance(data, dict):
        findings.append(issue("FAIL", "ledger_top_level_incomplete", "严格模式的推导台账顶层必须包含 models、sensitivity、engineering_margins 和 required_visuals"))
        return findings, {"models": len(models), "cross_validated_models": cross_validated_models, "fallback_validated_models": fallback_validated_models}

    if isinstance(data, dict):
        sensitivity = data.get("sensitivity", {})
        parameters = sensitivity.get("parameter", []) if isinstance(sensitivity, dict) else []
        model_variants = sensitivity.get("model_variants", []) if isinstance(sensitivity, dict) else []
        boundary_variants = sensitivity.get("boundary_variants", []) if isinstance(sensitivity, dict) else []
        if strict and (len(parameters) < 2 or len(model_variants) < 2 or len(boundary_variants) < 2 or not nonempty(sensitivity.get("conclusions") if isinstance(sensitivity, dict) else None)):
            findings.append(issue("FAIL", "triple_sensitivity_incomplete", "三重敏感性不完整：需 2 个连续参数、2 个模型假设、2 个边界规则及适用范围结论"))
        parameter_names = [str(parameter.get("name", "")).strip().casefold() for parameter in parameters if isinstance(parameter, dict)]
        if len(parameter_names) != len(set(parameter_names)):
            findings.append(issue("FAIL", "parameter_sensitivity_not_distinct", "参数敏感性必须选择至少两个不同的连续参数"))
        parameter_digests: list[str] = []
        for parameter in parameters:
            if not isinstance(parameter, dict):
                findings.append(issue("FAIL", "parameter_sensitivity_invalid", "参数敏感性记录必须是对象", value=parameter))
                continue
            levels = parameter.get("levels", [])
            try:
                default_levels_ok = all(any(abs(float(level) - target) < 1e-9 for level in levels) for target in (-0.2, 0.0, 0.2))
            except (TypeError, ValueError):
                default_levels_ok = False
            if not default_levels_ok:
                exception = parameter.get("range_exception", {})
                exception_ok = (
                    isinstance(exception, dict)
                    and all(nonempty(exception.get(field)) for field in ("reason", "feasible_levels", "evidence"))
                    and project_evidence_status(project_root, exception.get("evidence"))[0]
                )
                if not exception_ok:
                    findings.append(issue("FAIL", "parameter_sensitivity_levels", f"参数 {parameter.get('name', '?')} 未覆盖 -20%、基准和 +20%，且没有物理可行域例外证据", levels=levels))
            evidence_path = parameter.get("evidence")
            exists, status = project_evidence_status(project_root, evidence_path)
            if not exists or not nonempty(parameter.get("result_summary")):
                findings.append(issue("FAIL", "sensitivity_evidence_missing", f"参数 {parameter.get('name', '?')} 缺少真实结果证据或关键输出变化摘要", path=evidence_path, status=status))
            else:
                digest = project_evidence_digest(project_root, evidence_path)
                if digest:
                    parameter_digests.append(digest)
        if len(parameters) >= 2 and len(set(parameter_digests)) < 2:
            findings.append(issue("FAIL", "parameter_sensitivity_evidence_not_independent", "两个连续参数必须绑定内容不同的扫描结果证据，不能复用或复制同一实验文件"))

        for variant_kind, variants in (("model", model_variants), ("boundary", boundary_variants)):
            variant_names: list[str] = []
            variant_digests: list[str] = []
            for variant in variants:
                if not isinstance(variant, dict) or not all(nonempty(variant.get(field)) for field in ("name", "result_summary", "evidence")):
                    findings.append(issue("FAIL", f"{variant_kind}_sensitivity_variant_incomplete", f"{variant_kind} 敏感性方案缺少名称、结果摘要或证据文件", variant=variant))
                    continue
                exists, status = project_evidence_status(project_root, variant.get("evidence"))
                if not exists:
                    findings.append(issue("FAIL", f"{variant_kind}_sensitivity_evidence_missing", f"{variant_kind} 敏感性方案 {variant.get('name')} 的证据文件无效", path=variant.get("evidence"), status=status))
                else:
                    variant_names.append(str(variant.get("name")).strip().casefold())
                    digest = project_evidence_digest(project_root, variant.get("evidence"))
                    if digest:
                        variant_digests.append(digest)
            if len(variant_names) != len(set(variant_names)):
                findings.append(issue("FAIL", f"{variant_kind}_sensitivity_variants_duplicate", f"{variant_kind} 敏感性方案名称必须互异"))
            if len(variants) >= 2 and len(set(variant_digests)) < 2:
                findings.append(issue("FAIL", f"{variant_kind}_sensitivity_evidence_not_independent", f"{variant_kind} 敏感性至少需要两份内容不同的方案结果证据"))

        margins = data.get("engineering_margins", [])
        if strict and hard_constraint_ids and (not isinstance(margins, list) or not margins):
            findings.append(issue("FAIL", "engineering_margins_missing", "未计算全部硬约束的工程安全裕度"))
        covered_constraint_ids: set[str] = set()
        for margin in margins if isinstance(margins, list) else []:
            if not isinstance(margin, dict):
                findings.append(issue("FAIL", "engineering_margin_invalid_record", "工程裕度记录必须是对象", value=margin))
                continue
            required_margin = ("constraint_id", "constraint", "constraint_type", "actual", "unit", "margin_percent", "evidence", "uncertainty_discussion")
            missing_margin = [field for field in required_margin if not nonempty(margin.get(field))]
            if missing_margin:
                findings.append(issue("FAIL", "engineering_margin_incomplete", f"约束 {margin.get('constraint', '?')} 的裕度记录缺少：{', '.join(missing_margin)}"))
                continue
            covered_constraint_ids.add(str(margin.get("constraint_id")).strip())
            exists, status = project_evidence_status(project_root, margin.get("evidence"))
            if not exists:
                findings.append(issue("FAIL", "engineering_margin_evidence_missing", f"约束 {margin.get('constraint', '?')} 的裕度证据文件无效", path=margin.get("evidence"), status=status))
            try:
                actual = float(margin["actual"])
                reported = float(margin["margin_percent"])
                constraint_type = str(margin["constraint_type"]).strip().lower()
                if constraint_type == "upper":
                    limit = float(margin["limit"])
                    computed = (limit - actual) / abs(limit) * 100.0
                elif constraint_type == "lower":
                    limit = float(margin["limit"])
                    if abs(limit) < 1e-12:
                        reference_scale = float(margin["reference_scale"])
                        if reference_scale <= 0:
                            raise ValueError("reference_scale must be positive")
                        computed = (actual - limit) / reference_scale * 100.0
                    else:
                        computed = (actual - limit) / abs(limit) * 100.0
                elif constraint_type == "absolute_upper":
                    limit = float(margin["limit"])
                    computed = (limit - abs(actual)) / abs(limit) * 100.0
                elif constraint_type == "two_sided":
                    lower = float(margin["lower"])
                    upper = float(margin["upper"])
                    if not lower < upper:
                        raise ValueError("lower must be smaller than upper")
                    computed = min(actual - lower, upper - actual) / (upper - lower) * 100.0
                else:
                    raise ValueError("unsupported constraint_type")
                if abs(computed - reported) > max(0.01, abs(computed) * 0.01):
                    findings.append(issue("FAIL", "engineering_margin_mismatch", f"约束 {margin['constraint']} 的裕度计算不一致", reported=reported, computed=computed))
                if reported < 1.0:
                    robust = margin.get("robust_resolve", {})
                    robust_ok = (
                        nonempty(margin.get("warning"))
                        and isinstance(robust, dict)
                        and all(nonempty(robust.get(field)) for field in ("tightened_constraint", "result", "evidence"))
                        and project_evidence_status(project_root, robust.get("evidence"))[0]
                    )
                    if not robust_ok:
                        findings.append(issue("FAIL", "low_margin_not_handled", f"约束 {margin['constraint']} 的裕度低于 1%，但没有警示和收紧约束重求解证据", margin_percent=reported))
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                findings.append(issue("FAIL", "engineering_margin_invalid", f"约束 {margin.get('constraint', '?')} 的裕度不是有效数值"))
        if strict and hard_constraint_ids != covered_constraint_ids:
            findings.append(issue("FAIL", "engineering_margin_coverage_mismatch", "工程裕度没有与全部硬约束 ID 一一对应", missing=sorted(hard_constraint_ids - covered_constraint_ids), extra=sorted(covered_constraint_ids - hard_constraint_ids)))

        visuals = data.get("required_visuals", [])
        visual_types = {item.get("type") for item in visuals if isinstance(item, dict)}
        required_types = {"technical_route", "subproblem_flow", "model_comparison", "cumulative_distribution"}
        missing_types = sorted(required_types - visual_types)
        if strict and missing_types:
            findings.append(issue("FAIL", "required_visuals_missing", f"缺少必要视觉证据类型：{', '.join(missing_types)}"))
        for visual in visuals if isinstance(visuals, list) else []:
            if not isinstance(visual, dict):
                findings.append(issue("FAIL", "required_visual_invalid_record", "必要视觉证据记录必须是对象", value=visual))
                continue
            files = visual.get("files", [visual.get("file")])
            files = [value for value in files if value]
            valid_files = []
            for value in files:
                candidate = (project_root / value).resolve()
                try:
                    candidate.relative_to(project_root.resolve())
                except ValueError:
                    continue
                if candidate.exists() and visual_file_is_readable(candidate):
                    valid_files.append(value)
            if not files or len(valid_files) != len(files):
                findings.append(issue("FAIL", "required_visual_file_missing", f"视觉证据 {visual.get('type', '?')} 的文件不存在、越界或不是可识别图像", files=files))
            if not nonempty(visual.get("data_source")) or not nonempty(visual.get("claim")):
                findings.append(issue("FAIL", "required_visual_mapping_missing", f"视觉证据 {visual.get('type', '?')} 缺少数据来源或主张映射"))

        figure_manifest = data.get("figure_manifest", [])
        if strict and (not isinstance(figure_manifest, list) or len(figure_manifest) < 12):
            findings.append(issue("FAIL", "figure_manifest_below_target", "图证据清单少于 12 条，无法证明每幅图均绑定真实数据和主张", actual=len(figure_manifest) if isinstance(figure_manifest, list) else 0, required=12))
        manifest_files: list[str] = []
        manifest_hashes: list[str] = []
        manifest_anchors: list[str] = []
        for index, record in enumerate(figure_manifest, 1) if isinstance(figure_manifest, list) else []:
            if not isinstance(record, dict) or not all(nonempty(record.get(field)) for field in ("file", "question", "data_source", "claim", "analysis_anchor")):
                findings.append(issue("FAIL", "figure_manifest_incomplete", f"第 {index} 条图证据缺少文件、子问题、数据源、主张或解读锚点"))
                continue
            manifest_files.append(str(record["file"]).replace("\\", "/").casefold())
            manifest_anchors.append(str(record["analysis_anchor"]))
            figure_path = (project_root / record["file"]).resolve()
            if not figure_path.exists() or not visual_file_is_readable(figure_path):
                findings.append(issue("FAIL", "figure_manifest_file_invalid", f"第 {index} 条图证据文件无效", path=record["file"]))
            else:
                manifest_hashes.append(hashlib.sha256(figure_path.read_bytes()).hexdigest())
            exists, status = project_evidence_status(project_root, record["data_source"])
            if not exists:
                findings.append(issue("FAIL", "figure_manifest_data_missing", f"第 {index} 条图证据的数据源文件无效", path=record["data_source"], status=status))
        if len(manifest_files) != len(set(manifest_files)):
            findings.append(issue("FAIL", "figure_manifest_duplicate_files", "图证据清单包含重复文件，不能重复计数"))
        if len(manifest_hashes) != len(set(manifest_hashes)):
            findings.append(issue("FAIL", "figure_manifest_duplicate_content", "图证据清单包含内容完全相同的文件，不能复制改名凑数"))

    return findings, {
        "models": len(models),
        "cross_validated_models": cross_validated_models,
        "fallback_validated_models": fallback_validated_models,
        "manifest_figure_files": manifest_files,
        "manifest_figure_hashes": manifest_hashes,
        "manifest_analysis_anchors": manifest_anchors,
    }


def audit_decision_log(path: Path | None, project_root: Path, strict: bool, min_traces: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if path is None:
        severity = "FAIL" if strict else "WARN"
        return [issue(severity, "decision_log_not_supplied", "未提供真实决策痕迹；不得为满足数量要求虚构团队讨论")], {"decision_traces": 0}
    data, findings = load_json(path, "decision_log")
    if data is None:
        return findings, {"decision_traces": 0}
    if not isinstance(data, list):
        return findings + [issue("FAIL", "invalid_decision_log", "decision-traces.json 顶层必须是数组")], {"decision_traces": 0}
    required = ("question", "initial_option", "observed_problem", "evidence", "alternatives", "final_choice", "reason")
    evidence_sets: list[set[str]] = []
    for index, trace in enumerate(data, 1):
        if not isinstance(trace, dict):
            findings.append(issue("FAIL", "decision_trace_invalid", f"第 {index} 条决策痕迹必须是对象", value=trace))
            evidence_sets.append(set())
            continue
        missing = [field for field in required if not nonempty(trace.get(field))]
        if missing:
            findings.append(issue("FAIL", "decision_trace_incomplete", f"第 {index} 条决策痕迹缺少：{', '.join(missing)}"))
        trace_evidence: set[str] = set()
        for evidence_path in trace.get("evidence", []):
            exists, status = project_evidence_status(project_root, evidence_path)
            if not exists:
                findings.append(issue("FAIL", "decision_evidence_missing", f"第 {index} 条决策痕迹证据不存在、为空或越出项目目录", path=evidence_path, status=status))
            else:
                trace_evidence.add(str((project_root / evidence_path).resolve()).casefold())
        evidence_sets.append(trace_evidence)
    if not data:
        findings.append(issue("WARN", "no_decision_traces", "没有真实决策痕迹；正文应少写或不写团队试错，不得随机补齐"))
    if strict and len(data) < min_traces:
        findings.append(issue("FAIL", "decision_traces_below_target", f"真实决策痕迹少于完整竞赛论文质量目标 {min_traces} 条；应补真实候选实验，不得补写虚构对话", actual=len(data), required=min_traces))
    if len(data) > 5:
        findings.append(issue("WARN", "too_many_decision_traces", "决策痕迹超过 5 条，正文只保留最有解释力的 3–5 条"))
    if strict and len(data) >= min_traces:
        unique_evidence = set().union(*evidence_sets) if evidence_sets else set()
        evidence_digests = set()
        for evidence_path in unique_evidence:
            try:
                evidence_digests.add(hashlib.sha256(Path(evidence_path).read_bytes()).hexdigest())
            except OSError:
                continue
        if len(evidence_digests) < min_traces:
            findings.append(issue("FAIL", "decision_evidence_not_distinct", "3–5 条决策痕迹必须合计绑定足够多的内容不同的候选实验或比较证据，不能复制同一文件改名", actual=len(evidence_digests), required=min_traces))
    return findings, {"decision_traces": len(data)}


def audit_benchmark_gap(path: Path | None) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if path is None:
        return [issue("FAIL", "benchmark_gap_not_supplied", "严格模式要求内部对标差距记录，以证明已完成赛后对标隔离")], {"benchmark_samples": 0}
    data, findings = load_json(path, "benchmark_gap")
    if data is None:
        return findings, {"benchmark_samples": 0}
    if not isinstance(data, dict):
        return findings + [issue("FAIL", "invalid_benchmark_gap", "benchmark-gap.json 顶层必须是对象")], {"benchmark_samples": 0}
    samples = data.get("samples", [])
    gaps = data.get("current_gaps", [])
    forbidden_terms = data.get("forbidden_terms", [])
    if not isinstance(samples, list) or not samples:
        findings.append(issue("FAIL", "benchmark_samples_missing", "对标记录缺少样本及主体/附件边界"))
    if not isinstance(gaps, list) or not gaps:
        findings.append(issue("FAIL", "benchmark_gaps_missing", "对标记录缺少当前稿的证据差距"))
    if not isinstance(forbidden_terms, list) or not forbidden_terms or any(not isinstance(term, str) or len(term.strip()) < 2 for term in forbidden_terms):
        findings.append(issue("FAIL", "benchmark_forbidden_terms_missing", "对标记录必须给出由样本编号、标题、作者和独有结果生成的禁漏词清单；每项至少 2 个字符"))
    else:
        forbidden_set = {term.strip().casefold() for term in forbidden_terms}
        expected_terms: list[str] = []
        for index, sample in enumerate(samples, 1) if isinstance(samples, list) else []:
            if not isinstance(sample, dict) or not all(nonempty(sample.get(field)) for field in ("id", "title", "authors", "result_tokens")):
                findings.append(issue("FAIL", "benchmark_sample_metadata_incomplete", f"第 {index} 个对标样本缺少编号、标题、作者或独有结果词"))
                continue
            expected_terms.extend([str(sample["id"]), str(sample["title"])])
            authors = sample["authors"] if isinstance(sample["authors"], list) else [sample["authors"]]
            results = sample["result_tokens"] if isinstance(sample["result_tokens"], list) else [sample["result_tokens"]]
            expected_terms.extend(str(value) for value in authors + results)
        missing_terms = [term for term in expected_terms if len(term.strip()) >= 2 and term.strip().casefold() not in forbidden_set]
        if missing_terms:
            findings.append(issue("FAIL", "benchmark_forbidden_terms_incomplete", "禁漏词没有覆盖每个样本的编号、标题、作者和独有结果", missing=missing_terms[:20]))
    return findings, {"benchmark_samples": len(samples) if isinstance(samples, list) else 0, "benchmark_forbidden_terms": len(forbidden_terms) if isinstance(forbidden_terms, list) else 0}


def read_benchmark_forbidden_terms(path: Path | None) -> tuple[str, ...]:
    if path is None or not path.exists():
        return ()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    terms = data.get("forbidden_terms", []) if isinstance(data, dict) else []
    return tuple(term.strip() for term in terms if isinstance(term, str) and len(term.strip()) >= 2)


def audit_table_references(text: str, strict: bool) -> list[dict[str, Any]]:
    """表号一致性：捕获重号题注、未编号却被正文引用的题注以及悬空表号引用。

    Pandoc 风格引用 `表[N](#tab:xxx)` 会与 `{... #tab:xxx}` 题注锚点互相核对；
    普通 `表N` 引用必须能在已定义的表号集合中找到。这样可发现把两张表都写成
    “表1”或正文引用“表2”而全文没有“表2”题注这类真实交付缺陷。
    """
    findings: list[dict[str, Any]] = []
    numbered_captions: list[str] = []
    caption_lines: set[int] = set()
    label_to_caption: dict[str, tuple[str | None, int]] = {}
    # 支持顺序编号(表1)、按章编号(表3-1)与附录编号(表A-1)
    table_no_re = r"(?:[A-Za-z]+-)?\d+(?:-\d+)?"
    table_cap_re = re.compile(r"^:?\s*表\s*(" + table_no_re + r")(?![\dA-Za-z-])")
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped.startswith((":", "|")):
            continue
        number_match = table_cap_re.match(stripped)
        label_match = re.search(r"\{#(tab:[^}\s]+)\}", stripped)
        if number_match:
            numbered_captions.append(number_match.group(1))
            caption_lines.add(index)
        if label_match:
            label_to_caption[label_match.group(1)] = (
                number_match.group(1) if number_match else None,
                index,
            )

    seen: set[str] = set()
    for number in numbered_captions:
        if number in seen:
            findings.append(issue("FAIL", "duplicate_table_caption_number", f"多个表格使用了相同的表号：表{number}"))
        seen.add(number)

    claimed: set[str] = set(numbered_captions)
    for match in re.finditer(r"表\s*\[(\d+)\]\(#(tab:[^)\s]+)\)", text):
        number, label = match.group(1), match.group(2)
        claimed.add(number)
        if label not in label_to_caption:
            findings.append(issue("FAIL", "table_reference_label_missing", f"正文以表{number}引用，但找不到对应题注 {label}"))
            continue
        explicit, _ = label_to_caption[label]
        if explicit is not None:
            if explicit != number:
                findings.append(issue("FAIL", "table_caption_number_mismatch", f"题注 {label} 标注为表{explicit}，正文却以表{number}引用"))
        elif number in numbered_captions:
            findings.append(issue("FAIL", "duplicate_table_caption_number", f"未编号题注 {label} 被正文引用为表{number}，与已有表{number}题注重号"))

    for match in re.finditer(r"表\s*(" + table_no_re + r")", text):
        if text.count("\n", 0, match.start()) in caption_lines:
            continue
        number = match.group(1)
        if number not in claimed:
            findings.append(issue("FAIL" if strict else "WARN", "dangling_table_reference", f"正文引用表{number}，但没有定义对应表格"))
    return findings


STRATEGY_ALIASES: dict[str, tuple[str, ...]] = {
    "hybrid": ("混合策略",),
    "random": ("随机策略", "随机选取", "随机基线"),
    "pure_exploitation": ("只追求均值", "纯开发", "纯利用", "均值优先", "仅追求均值"),
    "maximin": ("maximin", "最大最小", "空间填充"),
    "uncertainty": ("只追求不确定性", "不确定性优先", "仅追求不确定性"),
}


def audit_results_policy_cross_reference(project_root: Path, text: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """把正文描述的“策略比较”与 results/ 下含 policy 列的 CSV 枚举交叉核对。

    两条规则：
    1. 结果文件真正比较过的策略，正文必须披露（防止选择性汇报，例如回测里
       pure_exploitation 更优却只字不提）；
    2. 正文声称比较过、但结果文件枚举中不存在的策略，必须拦截（防止把
       “只追求不确定性”写成跑过的对比，而实际代码里根本没有这个策略）。
    """
    findings: list[dict[str, Any]] = []
    results_dir = project_root / "results"
    if not results_dir.is_dir():
        return findings, {"results_policy_values": []}
    policy_values: set[str] = set()
    for csv_path in sorted(results_dir.glob("*.csv")):
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if not reader.fieldnames:
                    continue
                policy_column = next((name for name in reader.fieldnames if name.strip().casefold() == "policy"), None)
                if policy_column is None:
                    continue
                for row in reader:
                    value = (row.get(policy_column) or "").strip()
                    if value:
                        policy_values.add(value)
        except (OSError, csv.Error):
            continue
    if not policy_values:
        return findings, {"results_policy_values": []}
    normalized = {value.casefold() for value in policy_values}
    for canonical, aliases in STRATEGY_ALIASES.items():
        if canonical in normalized:
            if not any(alias in text for alias in aliases):
                findings.append(issue("FAIL", "results_policy_not_disclosed", f"结果文件比较了策略 {canonical}，但正文没有披露该策略"))
        else:
            mentioned = [alias for alias in aliases if alias in text]
            if mentioned:
                findings.append(issue("FAIL", "text_describes_unrun_policy", f"正文描述了策略比较（{' / '.join(mentioned)}），但结果文件策略枚举中没有对应项"))
    return findings, {"results_policy_values": sorted(policy_values)}


def extract_docx_headings(path: Path) -> list[tuple[str, str]]:
    """返回 DOCX 中带标题样式的 (styleId, 去空白标题) 列表，用于检测重复标题。"""
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    headings: list[tuple[str, str]] = []
    for paragraph in root.iter(f"{w}p"):
        style_node = paragraph.find(f"./{w}pPr/{w}pStyle")
        style_id = style_node.get(f"{w}val", "") if style_node is not None else ""
        if not re.search(r"(?:heading|标题|^1$|^2$|^Title$)", style_id, flags=re.I):
            continue
        text = "".join(node.text or "" for node in paragraph.iter(f"{w}t"))
        text = re.sub(r"\s+", "", text)
        if text:
            headings.append((style_id, text))
    return headings


def audit_paper_structure(text: str) -> list[dict[str, Any]]:
    """硬性结构检查（见 references/论文结构硬性要求.md）。

    检查：必需章节齐全且顺序正确、摘要单独一页、优缺点各>=4条、
    改进方案、正文引用附录。返回发现的 FAIL 列表。
    """
    findings: list[dict[str, Any]] = []
    required = [
        ("摘要", r"^\s*#+\s*摘要"),
        ("问题重述", r"^\s*#+\s*[1一]\s*问题重述"),
        ("模型假设与符号说明", r"^\s*#+\s*[2二]\s*模型假设与符号说明"),
        ("模型建立与求解", r"^\s*#+\s*[3三]\s*模型建立与求解"),
        ("结果分析与讨论", r"^\s*#+\s*[4四]\s*结果分析与讨论"),
        ("灵敏度分析", r"^\s*#+\s*[5五]\s*灵敏度分析"),
        ("模型评价与改进", r"^\s*#+\s*[6六]\s*模型评价与改进"),
        ("参考文献", r"^\s*#+\s*参考文献"),
        ("附录", r"^\s*#+\s*附录"),
    ]
    positions: list[tuple[str, int]] = []
    for name, pattern in required:
        m = re.search(pattern, text, flags=re.M)
        if not m:
            findings.append(issue("FAIL", "missing_required_section", f"缺少必需章节：{name}"))
            continue
        positions.append((name, m.start()))
    if len(positions) == len(required) and positions != sorted(positions, key=lambda x: x[1]):
        findings.append(issue("FAIL", "section_order_wrong", "必需章节顺序错误，应按规范排列"))

    kw = re.search(r"关键词[:：]", text)
    if kw:
        after = text[kw.end():kw.end() + 300]
        if not re.search(r"newpage|pagebreak|openxml|\\\(\\\\|\\\\pagebreak", after):
            findings.append(issue("FAIL", "abstract_not_own_page", "摘要未单独一页（关键词后缺分页标记）"))

    def count_numbered_items(anchor: str) -> int:
        m = re.search(anchor, text)
        if not m:
            return 0
        seg = text[m.start():m.start() + 700]
        return len(re.findall(r"^\s*\d+[\.、]", seg, flags=re.M))

    if count_numbered_items(r"模型优点") < 4:
        findings.append(issue("FAIL", "advantages_below_target", "模型优点少于 4 条"))
    if count_numbered_items(r"模型缺点") < 4:
        findings.append(issue("FAIL", "disadvantages_below_target", "模型缺点少于 4 条"))
    if not re.search(r"改进方案", text):
        findings.append(issue("FAIL", "missing_improvement_scheme", "缺少改进方案小节"))
    if re.search(r"^\s*#+\s*附录", text, flags=re.M) and not re.search(
            r"详见附录|见附录|附录\s*([A-Z])(?!\w)", text):
        findings.append(issue("FAIL", "appendix_not_referenced", "正文未引用附录（应至少一次“详见附录A”等）"))
    return findings


def audit_text(
    text: str,
    strict: bool,
    min_equations: int,
    min_figures: int,
    min_references: int,
    project_root: Path | None = None,
    forbidden_terms: tuple[str, ...] = (),
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clean = strip_code_fences(text)
    findings = audit_paper_structure(clean)
    findings, formula_metrics = audit_formulas(clean, strict, min_equations)
    figure_findings, visual_metrics = audit_figures_and_tables(clean, strict, min_figures, project_root)
    findings.extend(figure_findings)
    findings.extend(audit_table_references(clean, strict))

    without_math = re.sub(r"\\\[.*?\\\]", " ", clean, flags=re.S)
    without_math = re.sub(r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}.*?\\end\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", " ", without_math, flags=re.S)
    without_math = re.sub(r"(?<!\\)\$(?!\$).*?(?<!\\)\$", " ", without_math, flags=re.S)
    without_math = re.sub(r"`[^`]+`", " ", without_math)
    plain_math: list[dict[str, Any]] = []
    for name, pattern in {
        "下标表达式": re.compile(r"(?<![\w\\])(?:[A-Za-z]|[α-ωΑ-Ω])_[A-Za-z0-9{}]+"),
        "插入符幂表达式": re.compile(r"(?<![\w\\])(?:\d+|[A-Za-z])\^(?:[-+]?\d+|\{[^}]+\})"),
    }.items():
        for match in pattern.finditer(without_math):
            plain_math.append({"kind": name, "text": match.group(0), "line": without_math.count("\n", 0, match.start()) + 1})
    if plain_math:
        findings.append(issue("FAIL", "plain_text_math", "检测到未放入 LaTeX 数学环境的纯文本数学表达式", matches=plain_math[:30]))

    for match in re.finditer(r"(?:见图|如图)\s*\d+(?:\s*所示)?", clean):
        tail = clean[match.end():match.end() + 180]
        if not NUMBER_PATTERN.search(tail):
            findings.append(issue("FAIL", "isolated_figure_reference", "图号引用后没有紧邻的定量观察", reference=match.group(0), line=clean.count("\n", 0, match.start()) + 1))

    for name, pattern in BENCHMARK_LEAK_PATTERNS.items():
        matches = [match.group(0)[:120] for match in pattern.finditer(clean)]
        if matches:
            findings.append(issue("FAIL", "contest_context_leak", f"正式竞赛稿检测到{name}", matches=matches[:10]))
    leaked_terms = [term for term in forbidden_terms if term.casefold() in clean.casefold()]
    if leaked_terms:
        findings.append(issue("FAIL", "dynamic_benchmark_leak", "正式竞赛稿命中内部对标样本禁漏词", matches=leaked_terms[:20]))

    question_count = len(re.findall(r"(?:问题|第)\s*[一二三四五六七八九十1-9]\s*(?:问|：|:)", clean))
    if question_count >= 2 and not re.search(r"^\s*#+\s*问题间关联分析", clean, flags=re.M):
        findings.append(issue("FAIL" if strict else "WARN", "missing_question_linkage", "多问论文缺少专门的“问题间关联分析”小节"))
    if question_count >= 2 and not re.search(r"误差传播|继承.+(?:变量|公式|结果|字段)|与前问的衔接", clean):
        findings.append(issue("FAIL" if strict else "WARN", "question_linkage_not_specific", "问题间关联未具体说明共享变量、公式、结果字段或误差传播"))

    required_sections = {
        "cross_validation_section": r"^\s*#+.*(?:交叉验证|独立方法验证)",
        "sensitivity_section": r"^\s*#+.*灵敏度分析",
        "objective_alignment_section": r"^\s*#+.*(?:物理目标与优化目标|优化目标.*物理目标)",
        "engineering_margin_section": r"^\s*#+.*(?:工程裕度|安全裕度)",
    }
    for code, pattern in required_sections.items():
        if strict and not re.search(pattern, clean, flags=re.M):
            findings.append(issue("FAIL", code, f"完整竞赛论文缺少必要小节：{code}"))
    if strict and not all(term in clean for term in ("参数敏感性", "模型敏感性", "边界规则敏感性")):
        findings.append(issue("FAIL", "triple_sensitivity_not_written", "灵敏度分析正文没有分别报告参数、模型和边界规则三类实验"))

    sequence_count = len(re.findall(r"首先|其次|最后", clean))
    if sequence_count > 12:
        findings.append(issue("WARN", "template_sequence_words", "模板序列词使用偏多，需检查段落节奏", count=sequence_count))

    reference_section = re.split(r"^\s*#+\s*参考文献\s*$", clean, maxsplit=1, flags=re.M)
    reference_entries = re.findall(r"^\s*\[(\d+)\]\s*(.+)$", reference_section[1], flags=re.M) if len(reference_section) == 2 else []
    normalized_references = [re.sub(r"[\s\W_]+", "", entry.casefold()) for _, entry in reference_entries]
    duplicate_reference_numbers = [
        number for (number, _), normalized in zip(reference_entries, normalized_references)
        if normalized_references.count(normalized) > 1
    ]
    if duplicate_reference_numbers:
        findings.append(issue("FAIL", "duplicate_references", "参考文献存在内容重复条目，不能只更换编号凑数量", references=duplicate_reference_numbers))
    reference_count = len(set(normalized_references))
    if strict and reference_count < min_references:
        findings.append(issue("FAIL", "reference_count_below_target", f"真实工程或学术参考文献少于完整竞赛论文质量目标 {min_references} 条", actual=reference_count, required=min_references))
    incomplete_references = []
    placeholder_references = []
    for number, entry in reference_entries:
        if len(entry.strip()) < 25 or not re.search(r"(?:19|20)\d{2}", entry):
            incomplete_references.append(number)
        if re.search(r"(?:真实领域文献|参考文献\s*\d+|待补|占位|example|dummy|unknown)", entry, flags=re.I):
            placeholder_references.append(number)
    if strict and incomplete_references:
        findings.append(issue("FAIL", "reference_metadata_incomplete", "参考文献缺少可追溯的作者/机构、题名、来源或年份元数据", references=incomplete_references))
    if placeholder_references:
        findings.append(issue("FAIL", "reference_placeholder", "参考文献中检测到占位条目", references=placeholder_references))

    human_phrases = len(re.findall(r"我们注意到|坦白说|一个有趣的发现是|我们意识到", clean))
    allowed_human_phrases = max(1, (chinese_char_count(clean) + 799) // 800)
    if human_phrases > allowed_human_phrases:
        findings.append(issue("FAIL" if strict else "WARN", "human_phrase_overuse", "拟人化短语使用过密，超过每 800 个汉字 1 处", actual=human_phrases, allowed=allowed_human_phrases))

    metrics = {
        **formula_metrics,
        **visual_metrics,
        "chinese_characters": chinese_char_count(clean),
        "question_markers": question_count,
        "template_sequence_words": sequence_count,
        "references": reference_count,
        "plain_text_math": len(plain_math),
        "human_phrases": human_phrases,
    }
    if project_root is not None:
        policy_findings, policy_metrics = audit_results_policy_cross_reference(project_root, clean)
        findings.extend(policy_findings)
        metrics.update(policy_metrics)
    return findings, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="数学建模论文内容深度与竞赛语境审计")
    parser.add_argument("paper", type=Path, help="论文规范化 Markdown 源文件；LaTeX 与 DOCX 另由对应结构工具校验")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--derivation-ledger", type=Path, required=True)
    parser.add_argument("--decision-log", type=Path)
    parser.add_argument("--benchmark-gap", type=Path)
    parser.add_argument("--final-docx", type=Path, help="W2 时同时审计最终 DOCX 中的模板句、内部泄漏和纯文本公式")
    parser.add_argument("--min-equations", type=int, default=15)
    parser.add_argument("--min-figures", type=int, default=12)
    parser.add_argument("--min-references", type=int, default=8)
    parser.add_argument("--min-decision-traces", type=int, default=3)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paper = args.paper.resolve()
    project_root = args.project_root.resolve()
    min_equations = max(args.min_equations, 15) if args.strict else max(args.min_equations, 0)
    min_figures = max(args.min_figures, 12) if args.strict else max(args.min_figures, 0)
    min_references = max(args.min_references, 8) if args.strict else max(args.min_references, 0)
    min_decision_traces = max(args.min_decision_traces, 3) if args.strict else max(args.min_decision_traces, 0)
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    paper_text = ""
    text_metrics: dict[str, Any] = {}
    benchmark_path = args.benchmark_gap.resolve() if args.benchmark_gap else None
    benchmark_findings, benchmark_metrics = audit_benchmark_gap(benchmark_path)
    forbidden_terms = read_benchmark_forbidden_terms(benchmark_path)
    if not paper.exists():
        findings.append(issue("FAIL", "paper_missing", f"论文源文件不存在: {paper}"))
    elif paper.suffix.lower() not in {".md", ".markdown"}:
        findings.append(issue("FAIL", "canonical_markdown_required", "内容审计必须输入规范化 Markdown 源；LaTeX/DOCX 另由结构与渲染校验器检查"))
    else:
        paper_text = paper.read_text(encoding="utf-8")
        text_findings, text_metrics = audit_text(paper_text, args.strict, min_equations, min_figures, min_references, project_root, forbidden_terms)
        findings.extend(text_findings)
        metrics.update(text_metrics)

    ledger_findings, ledger_metrics = audit_derivation_ledger(args.derivation_ledger.resolve(), project_root, args.strict)
    if args.strict and paper_text:
        paper_figure_files = set(text_metrics.get("figure_files", []))
        manifest_figure_files = set(ledger_metrics.get("manifest_figure_files", []))
        if paper_figure_files != manifest_figure_files:
            ledger_findings.append(issue("FAIL", "figure_manifest_source_mismatch", "figure_manifest 必须与正文实际引用图集合一一对应", missing=sorted(paper_figure_files - manifest_figure_files), extra=sorted(manifest_figure_files - paper_figure_files)))
        missing_anchors = [anchor for anchor in ledger_metrics.get("manifest_analysis_anchors", []) if anchor not in paper_text]
        if missing_anchors:
            ledger_findings.append(issue("FAIL", "figure_manifest_anchor_missing", "图证据清单中的解读锚点未在正文出现", anchors=missing_anchors[:20]))
    decision_findings, decision_metrics = audit_decision_log(args.decision_log.resolve() if args.decision_log else None, project_root, args.strict, min_decision_traces)
    findings.extend(ledger_findings)
    findings.extend(decision_findings)
    if args.strict:
        findings.extend(benchmark_findings)
    elif benchmark_findings:
        findings.extend({**item, "severity": "WARN"} for item in benchmark_findings)
    metrics.update(ledger_metrics)
    metrics.update(decision_metrics)
    metrics.update(benchmark_metrics)
    if args.final_docx:
        docx_findings, docx_metrics = audit_final_docx(args.final_docx.resolve(), forbidden_terms)
        findings.extend(docx_findings)
        metrics.update(docx_metrics)
    elif args.strict:
        findings.append(issue("FAIL", "final_docx_not_supplied", "严格终稿审计必须提供 --final-docx，确保绝对禁令覆盖最终交付文件"))

    failed = any(item["severity"] == "FAIL" for item in findings)
    report = {
        "ok": not failed,
        "paper": str(paper),
        "project_root": str(project_root),
        "strict": args.strict,
        "metrics": metrics,
        "issues": findings,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
