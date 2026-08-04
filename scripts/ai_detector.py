#!/usr/bin/env python3
"""
AI 文本检测器
基于词汇多样性、句式复杂度、困惑度启发式的简易 AI 文本检测

用法:
    python ai_detector.py <input_md_file> --output <report.json>
"""

import argparse
import json
import re
import sys
import math
from collections import Counter
from pathlib import Path


def extract_paragraphs(text: str) -> list[dict]:
    """
    从 Markdown 文本中提取正文段落。
    跳过标题行、代码块、表格、LaTeX 公式块。
    返回 [{index, text, section}]
    """
    lines = text.split('\n')
    paragraphs = []
    current_section = "前言"
    in_code_block = False
    current_paragraph_lines = []
    para_index = 0

    for line in lines:
        stripped = line.strip()

        # 跟踪代码块
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # 跟踪节标题
        if stripped.startswith('#'):
            current_section = stripped.lstrip('#').strip()
            continue

        # 跳过长公式行
        if stripped.startswith('$$') or stripped.startswith('\\begin'):
            continue

        # 跳过表格
        if stripped.startswith('|'):
            continue

        # 跳过空行——如果积累了内容，保存为一个段落
        if not stripped:
            if current_paragraph_lines:
                para_text = ' '.join(current_paragraph_lines)
                # 只保留足够长的段落（至少 50 个中文字符或 100 个英文字符）
                if len(para_text) >= 50:
                    paragraphs.append({
                        "index": para_index,
                        "text": para_text,
                        "section": current_section,
                    })
                    para_index += 1
                current_paragraph_lines = []
            continue

        current_paragraph_lines.append(stripped)

    # 处理最后一段
    if current_paragraph_lines:
        para_text = ' '.join(current_paragraph_lines)
        if len(para_text) >= 50:
            paragraphs.append({
                "index": para_index,
                "text": para_text,
                "section": current_section,
            })

    return paragraphs


def compute_lexical_diversity(text: str) -> float:
    """
    计算词汇多样性（type-token ratio 的变化版本）。
    中文：按 2-gram 字符计算重复度；英文：按单词计算。
    """
    # 中文：按字符 2-gram
    chinese_chars = re.findall(r'[一-鿿]', text)
    if len(chinese_chars) >= 20:
        bigrams = [''.join(chinese_chars[i:i+2]) for i in range(len(chinese_chars)-1)]
        if len(bigrams) > 0:
            unique_ratio = len(set(bigrams)) / len(bigrams)
            return unique_ratio
    return 0.5  # 默认中等


def compute_sentence_pattern_score(text: str) -> float:
    """
    分析句式模式。AI 生成文本常过度使用某些句式。
    返回 0~1 之间的分数，越高越像 AI。
    """
    # AI 常见句式和过渡词
    ai_patterns = [
        r'首先.*其次.*最后',
        r'不仅.*而且|不仅.*还',
        r'综上所述|总而言之|综上所述',
        r'值得注意的是|值得一提的是',
        r'换句话说|换言之',
        r'显然|明显|显而易见',
        r'由此可知|由此可见',
        r'然而.*但是|虽然.*但是.*然而',
        r'通过.*分析.*可以.*看出',
        r'根据.*结果.*表明',
    ]

    score = 0
    for pattern in ai_patterns:
        matches = re.findall(pattern, text)
        if matches:
            score += len(matches) * 0.05

    return min(score, 1.0)


def compute_repetition_score(text: str) -> float:
    """
    检测内容重复度。
    同一段落中出现高度相似的句子是 AI 常见特征。
    """
    sentences = re.split(r'[。！？\.\!\?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if len(sentences) < 3:
        return 0.0

    # 用简单的字符集重叠率检测相似句子
    similar_pairs = 0
    total_pairs = 0
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            total_pairs += 1
            set_i = set(sentences[i])
            set_j = set(sentences[j])
            if len(set_i | set_j) > 0:
                overlap = len(set_i & set_j) / len(set_i | set_j)
                if overlap > 0.7:
                    similar_pairs += 1

    if total_pairs == 0:
        return 0.0
    return similar_pairs / total_pairs


def compute_paragraph_score(para: dict) -> dict:
    """
    对一个段落计算 AI 痕迹分数。
    """
    text = para['text']

    lex_div = compute_lexical_diversity(text)
    pattern = compute_sentence_pattern_score(text)
    repetition = compute_repetition_score(text)

    # 词汇多样性低 → 更像 AI（AI 倾向重复用词）
    lex_ai_score = max(0, (0.85 - lex_div) / 0.85) if lex_div > 0 else 0.5

    # 综合分数（加权平均）
    combined = 0.35 * lex_ai_score + 0.35 * pattern + 0.30 * repetition

    return {
        "index": para['index'],
        "section": para['section'],
        "text_preview": text[:120] + ("..." if len(text) > 120 else ""),
        "text_full": text,
        "lexical_diversity": round(lex_div, 3),
        "sentence_pattern_score": round(pattern, 3),
        "repetition_score": round(repetition, 3),
        "ai_probability": round(combined, 4),
    }


def detect_ai_text(md_path: str) -> dict:
    """
    对 Markdown 文件执行完整的 AI 文本检测。
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()

    paragraphs = extract_paragraphs(text)

    if not paragraphs:
        return {
            "error": "未找到足够的正文段落（每个段落至少需要 50 个中文字符）",
            "overall_probability": 0,
            "paragraphs": [],
            "high_risk_paragraphs": [],
        }

    # 逐段落评分
    scored = [compute_paragraph_score(p) for p in paragraphs]

    # 整体 AI 痕迹概率（所有段落平均）
    overall = sum(s['ai_probability'] for s in scored) / len(scored)

    # 高风险段落（概率 > 0.3）
    high_risk = [s for s in scored if s['ai_probability'] > 0.3]
    high_risk.sort(key=lambda x: x['ai_probability'], reverse=True)

    return {
        "file": md_path,
        "total_paragraphs": len(paragraphs),
        "overall_probability": round(overall, 4),
        "verdict": "likely-human" if overall < 0.15 else "needs-review" if overall < 0.4 else "likely-ai",
        "paragraphs": scored,
        "high_risk_paragraphs": high_risk,
    }


def main():
    parser = argparse.ArgumentParser(description="AI 文本检测器")
    parser.add_argument("input", help="要检测的 Markdown 文件路径")
    parser.add_argument("--output", required=True, help="检测报告输出路径 (JSON)")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"错误：输入文件不存在 {args.input}")
        sys.exit(1)

    result = detect_ai_text(args.input)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"文件: {args.input}")
    print(f"段落总数: {result.get('total_paragraphs', 0)}")
    print(f"整体 AI 痕迹概率: {result.get('overall_probability', 0):.4f}")
    print(f"判定: {result.get('verdict', 'unknown')}")
    print(f"高风险段落数: {len(result.get('high_risk_paragraphs', []))}")
    if result.get('high_risk_paragraphs'):
        print("\n高风险段落:")
        for p in result['high_risk_paragraphs'][:5]:
            print(f"  [{p['index']}] ({p['section']}) 概率={p['ai_probability']:.3f}: {p['text_preview'][:80]}...")

    print(f"\n检测报告已保存到: {args.output}")


if __name__ == "__main__":
    main()
