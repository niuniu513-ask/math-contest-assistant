#!/usr/bin/env python3
"""核心脚本冒烟测试：状态机、复现清单、AI 检测、物理示意图。

说明：本仓库路径含中文，当前 Python 运行环境下子进程会破坏中文 cwd/argv，
因此测试统一在进程内调用脚本入口，不派生子进程。
"""

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(os.environ.get("SMOKE_REPO_ROOT", Path(os.getcwd())))
if not (REPO_ROOT / "SKILL.md").exists():
    REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.stem, name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_main(module, argv):
    old_argv = sys.argv
    sys.argv = [module.__file__ or "script", *argv]
    try:
        return module.main()
    except SystemExit as exc:
        return exc.code
    finally:
        sys.argv = old_argv


class TestProjectState(unittest.TestCase):
    def test_init_and_status(self):
        project_state = load_script(SCRIPTS / "project_state.py")
        with tempfile.TemporaryDirectory() as tmp:
            rc = run_main(project_state, ["init", "--project-root", tmp, "--mode", "full"])
            self.assertEqual(rc, 0)
            state = Path(tmp) / ".work" / "run-state.json"
            self.assertTrue(state.exists())
            data = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(data["stage"], "intake")
            self.assertEqual(data["mode"], "full")
            rc = run_main(project_state, ["status", "--project-root", tmp])
            self.assertEqual(rc, 0)


class TestReproManifest(unittest.TestCase):
    def test_manifest_created(self):
        repro = load_script(SCRIPTS / "repro_manifest.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "input.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            rc = run_main(repro, [
                "--project-root", tmp,
                "--input", str(tmp_path / "input.csv"),
                "--seed", "42",
                "--parameters", "{}",
                "--command", "python solve.py",
            ])
            self.assertEqual(rc, 0)
            manifest = tmp_path / "results" / "复现清单.json"
            self.assertTrue(manifest.exists())
            data = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(data["random_seed"], 42)
            self.assertEqual(len(data["input_files"]), 1)
            self.assertEqual(len(data["input_files"][0]["sha256"]), 64)


class TestAiDetector(unittest.TestCase):
    def test_detect_on_markdown(self):
        ai = load_script(SCRIPTS / "ai_detector.py")
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "sample.md"
            md.write_text(
                "# 标题\n\n这是正文段落，包含足够长度的内容用于启发式检测。\n\n第二段用于测试。\n",
                encoding="utf-8",
            )
            report = ai.detect_ai_text(str(md))
            self.assertIsInstance(report, dict)
            self.assertGreater(len(report), 0)


class TestSchematicPptx(unittest.TestCase):
    def test_generates_pptx_without_png(self):
        mod = load_script(SCRIPTS / "schematic_pptx.py")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo.pptx"
            s = mod.Schematic(xlim=(0, 12), ylim=(0, 6))
            s.line((0, 1), (5, 1))
            s.save(str(out), export_png=False, export_svg=False)
            self.assertTrue(out.exists())
            self.assertTrue(zipfile.is_zipfile(out))
            self.assertFalse(Path(tmp, "False").exists())

    def test_help_does_not_create_file(self):
        source = (SCRIPTS / "schematic_pptx.py").read_text(encoding="utf-8")
        old_argv = sys.argv
        sys.argv = ["schematic_pptx.py", "--help"]
        code = None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(source, "schematic_pptx.py", "exec"), {"__name__": "__main__"})
        except SystemExit as exc:
            code = exc.code
        finally:
            sys.argv = old_argv
        self.assertEqual(code, 0)
        self.assertFalse(Path(SCRIPTS, "--help").exists())
        self.assertFalse(Path(SCRIPTS, "--help.pptx").exists())


if __name__ == "__main__":
    unittest.main()
