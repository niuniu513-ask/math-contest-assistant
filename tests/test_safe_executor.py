#!/usr/bin/env python3
"""safe_executor.py 沙箱行为测试。

沙箱通过子进程执行包装脚本，因此测试进程内调用
create_sandbox_wrapper + run_with_timeout 验证各边界行为。
"""

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.stem, name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_script(base, name, source):
    path = Path(base) / name
    path.write_text(source, encoding="utf-8")
    return str(path)


class SandboxTestCase(unittest.TestCase):
    def setUp(self):
        self.se = load_script(SCRIPTS / "safe_executor.py")
        # 基目录必须位于系统临时目录之外：沙箱为兼容 tempfile 允许写系统临时目录，
        # 若基目录建在 tempdir 内，"允许目录外"的断言将无法触发。
        self.base = Path.cwd() / ".sandbox_test_base"
        if self.base.exists():
            import shutil
            shutil.rmtree(self.base)
        self.base.mkdir()
        self.out = self.base / "out"
        self.out.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.base, ignore_errors=True)

    def run_script(self, source, timeout=30):
        script = write_script(self.base, "user_script.py", source)
        wrapper = self.se.create_sandbox_wrapper(script, str(self.out))
        return self.se.run_with_timeout(wrapper, timeout, str(self.out))

    def test_ok_execution_and_write_within_output(self):
        res = self.run_script(
            'print("hello-sandbox")\n'
            'with open("out.txt", "w", encoding="utf-8") as f:\n'
            '    f.write("written")\n'
        )
        self.assertTrue(res["success"], res["stderr"])
        self.assertIn("hello-sandbox", res["stdout"])
        self.assertTrue((self.out / "out.txt").exists())

    def test_write_outside_output_denied(self):
        res = self.run_script(
            "with open(%r, 'w', encoding='utf-8') as f:\n"
            "    f.write('x')\n" % str(self.base / "forbidden.txt")
        )
        self.assertFalse(res["success"])
        self.assertIn("禁止写入", res["stderr"])
        self.assertFalse((self.base / "forbidden.txt").exists())

    def test_import_subprocess_blocked(self):
        res = self.run_script("import subprocess\n")
        self.assertFalse(res["success"])
        self.assertIn("被禁用", res["stderr"])

    def test_import_socket_blocked(self):
        res = self.run_script("import socket\n")
        self.assertFalse(res["success"])
        self.assertIn("被禁用", res["stderr"])

    def test_os_remove_blocked_and_file_survives(self):
        victim = self.base / "victim.txt"
        victim.write_text("x", encoding="utf-8")
        res = self.run_script(
            "import os\nos.remove(%r)\n" % str(victim)
        )
        self.assertFalse(res["success"])
        self.assertIn("危险操作", res["stderr"])
        self.assertTrue(victim.exists())

    def test_os_system_blocked_even_via_from_import(self):
        res = self.run_script("from os import system\nsystem('echo hi')\n")
        self.assertFalse(res["success"])
        self.assertIn("危险操作", res["stderr"])

    def test_shutil_rmtree_outside_denied(self):
        res = self.run_script(
            "import shutil\nshutil.rmtree(%r)\n" % str(self.base / "victim_dir")
        )
        self.assertFalse(res["success"])
        self.assertIn("危险操作", res["stderr"])

    def test_timeout_kills_long_script(self):
        res = self.run_script("import time\ntime.sleep(30)\n", timeout=1)
        self.assertTrue(res["timeout"])


if __name__ == "__main__":
    unittest.main()
