#!/usr/bin/env python3
"""figure_audit.py 图文件审计测试。

通过进程内调用 audit_figure_directory 验证 PNG/SVG 解析、
DPI、配对、类别与子问题覆盖检查。
"""

import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.stem, name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    payload = chunk_type + data
    return (
        struct.pack(">I", len(data))
        + payload
        + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    )


def make_png(width: int = 800, height: int = 600, dpi: int | None = 300) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    out = sig + ihdr
    if dpi is not None:
        ppm = int(round(dpi / 0.0254))
        out += _png_chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
    out += _png_chunk(b"IEND", b"")
    return out


def make_svg(text: bool = True, raster: bool = False) -> str:
    body = "<text>abc</text>" if text else ""
    raster_el = '<image href="data:image/png;base64,AAAA"/>' if raster else ""
    return (
        '<?xml version="1.0"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f"{body}{raster_el}</svg>"
    )


class FigureAuditTestCase(unittest.TestCase):
    def setUp(self):
        self.fa = load_script(SCRIPTS / "figure_audit.py")
        self._tmp = tempfile.TemporaryDirectory()
        self.figures = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def audit(self, **kwargs):
        kwargs.setdefault("require_categories", False)
        return self.fa.audit_figure_directory(self.figures, **kwargs)

    def test_valid_png_with_svg_pair_passes(self):
        (self.figures / "result_q1_curve.png").write_bytes(make_png(dpi=300))
        (self.figures / "result_q1_curve.svg").write_text(make_svg(), encoding="utf-8")
        report = self.audit()
        self.assertTrue(report["ok"], report["issues"])
        self.assertAlmostEqual(report["files"]["result_q1_curve.png"]["dpi_x"], 300, places=1)

    def test_png_without_dpi_fails(self):
        (self.figures / "result_q1_nodpi.png").write_bytes(make_png(dpi=None))
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("缺少 DPI" in i["message"] for i in report["issues"]))

    def test_fake_png_fails(self):
        (self.figures / "result_q1_fake.png").write_text("not a png", encoding="utf-8")
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("无法解析" in i["message"] for i in report["issues"]))

    def test_jpeg_forbidden(self):
        (self.figures / "result_q1_photo.jpg").write_bytes(b"jpeg-bytes")
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("JPEG" in i["message"] for i in report["issues"]))

    def test_svg_without_text_fails(self):
        (self.figures / "result_q1_blank.svg").write_text(make_svg(text=False), encoding="utf-8")
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("没有可编辑文本节点" in i["message"] for i in report["issues"]))

    def test_missing_svg_pair_fails(self):
        (self.figures / "result_q1_solo.png").write_bytes(make_png())
        report = self.audit()
        self.assertFalse(report["ok"])
        self.assertTrue(any("缺少配对格式" in i["message"] for i in report["issues"]))

    def test_categories_and_questions_coverage(self):
        for q in ("q1", "q2"):
            for cat in ("raw_", "process_", "result_"):
                stem = f"{cat}{q}_fig"
                (self.figures / f"{stem}.png").write_bytes(make_png())
                (self.figures / f"{stem}.svg").write_text(make_svg(), encoding="utf-8")
        report = self.audit(require_categories=True, questions=("q1", "q2"))
        self.assertTrue(report["ok"], report["issues"])

    def test_missing_question_fails_category_check(self):
        for cat in ("raw_", "process_", "result_"):
            stem = f"{cat}q1_fig"
            (self.figures / f"{stem}.png").write_bytes(make_png())
            (self.figures / f"{stem}.svg").write_text(make_svg(), encoding="utf-8")
        report = self.audit(require_categories=True, questions=("q1", "q2"))
        self.assertFalse(report["ok"])
        self.assertTrue(any("q2" in i["message"] for i in report["issues"]))

    def test_missing_directory_fails(self):
        missing = self.figures / "nope"
        report = self.fa.audit_figure_directory(missing)
        self.assertFalse(report["ok"])
        self.assertTrue(any("目录不存在" in i["message"] for i in report["issues"]))


if __name__ == "__main__":
    unittest.main()
