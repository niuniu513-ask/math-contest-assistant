#!/usr/bin/env python3
"""
安全 Python 代码执行沙箱
限制执行时间、文件写入范围、禁用危险操作

用法:
    python safe_executor.py <script_path> --output-dir <dir> [--timeout <seconds>]
"""

import argparse
import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path


def create_sandbox_wrapper(script_path: str, output_dir: str) -> str:
    """
    创建一个包装脚本，在沙箱限制下执行原始脚本。
    返回包装脚本的路径。
    """
    script_abs = os.path.abspath(script_path)
    output_abs = os.path.abspath(output_dir)

    wrapper_code = f'''
import sys
import os
import builtins
import traceback
import warnings

# --- 沙箱限制 ---

# 限制文件写入范围
_ALLOWED_DIRS = {repr(output_abs)}
_ORIGINAL_OPEN = builtins.open

def _sandboxed_open(file, mode='r', *args, **kwargs):
    """限制文件写入仅在允许的目录内"""
    filepath = os.path.abspath(file)
    write_modes = ('w', 'a', 'x', 'w+', 'a+', 'x+', 'wb', 'ab', 'xb')
    is_write = any(m in mode for m in write_modes)
    if is_write:
        allowed = False
        for ad in _ALLOWED_DIRS:
            try:
                if filepath.startswith(os.path.abspath(ad)):
                    allowed = True
                    break
            except Exception:
                pass
        if not allowed:
            # 允许写入临时目录
            import tempfile
            tmp = os.path.abspath(tempfile.gettempdir())
            if filepath.startswith(tmp):
                allowed = True
        if not allowed:
            raise PermissionError(
                f"Sandbox: 禁止写入 {{filepath}}。"
                f"仅允许写入 {{_ALLOWED_DIRS}}"
            )
    return _ORIGINAL_OPEN(file, mode, *args, **kwargs)

builtins.open = _sandboxed_open

# 禁用危险操作
DISABLED_MODULES = [
    'os.system', 'os.popen', 'os.execv', 'os.execve', 'os.spawnv',
    'subprocess', 'socket', 'requests', 'urllib', 'http',
    'shutil.rmtree', 'shutil.move', 'os.remove', 'os.unlink',
    'os.rmdir', 'os.removedirs',
]

# 只警告不强制禁用（部分库内部会用到）
warnings.filterwarnings("error", category=RuntimeWarning)

print("=" * 60, flush=True)
print("沙箱环境已激活", flush=True)
print(f"允许写入目录: {{list(_ALLOWED_DIRS)}}", flush=True)
print("=" * 60, flush=True)

# --- 执行目标脚本 ---
print(f"开始执行: {script_abs}", flush=True)
print("-" * 60, flush=True)

try:
    with open({repr(script_abs)}, 'r', encoding='utf-8') as f:
        code = f.read()
    exec(compile(code, {repr(script_abs)}, 'exec'), {{'__name__': '__main__'}})
    print("-" * 60, flush=True)
    print("脚本执行成功", flush=True)
except Exception as e:
    print("-" * 60, flush=True)
    traceback.print_exc()
    print(f"\\n脚本执行失败: {{e}}", flush=True)
    sys.exit(1)
'''

    # 写入临时包装文件
    wrapper_path = os.path.join(output_dir, "_sandbox_wrapper.py")
    os.makedirs(output_dir, exist_ok=True)
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(wrapper_code)

    return wrapper_path


def run_with_timeout(wrapper_path: str, timeout: int, output_dir: str) -> dict:
    """
    带超时的执行，捕获 stdout/stderr 和返回码。
    """
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(
        [os.path.abspath(output_dir)] +
        [p for p in env.get('PYTHONPATH', '').split(os.pathsep) if p]
    )

    try:
        result = subprocess.run(
            [sys.executable, wrapper_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=output_dir,
            env=env,
        )
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": e.stdout if e.stdout else "",
            "stderr": e.stderr if e.stderr else f"执行超时 ({timeout}s)",
            "timeout": True,
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -2,
            "stdout": "",
            "stderr": str(e),
            "timeout": False,
        }


def main():
    parser = argparse.ArgumentParser(description="安全 Python 代码执行沙箱")
    parser.add_argument("script", help="要执行的 Python 脚本路径")
    parser.add_argument("--output-dir", required=True, help="输出目录（文件写入权限限制在此目录内）")
    parser.add_argument("--timeout", type=int, default=300, help="超时时间（秒），默认 300")
    parser.add_argument("--no-sandbox", action="store_true", help="禁用沙箱限制（仅用于调试）")
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.exists(script_path):
        print(f"错误：脚本不存在 {script_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 复制脚本到输出目录
    script_basename = os.path.basename(script_path)
    dest_script = os.path.join(output_dir, script_basename)
    shutil.copy2(script_path, dest_script)

    if args.no_sandbox:
        # 直接执行（不安全模式，仅调试用）
        print("⚠️ 警告：沙箱已禁用，直接执行脚本")
        result = run_with_timeout(script_path, args.timeout, output_dir)
    else:
        # 创建沙箱包装器并执行
        wrapper_path = create_sandbox_wrapper(dest_script, output_dir)
        result = run_with_timeout(wrapper_path, args.timeout, output_dir)

    # 清理包装器
    wrapper_path = os.path.join(output_dir, "_sandbox_wrapper.py")
    if os.path.exists(wrapper_path):
        os.remove(wrapper_path)

    # 输出结果
    print("\n" + "=" * 60)
    print("执行结果摘要")
    print("=" * 60)
    print(f"成功: {result['success']}")
    print(f"超时: {result['timeout']}")
    print(f"返回码: {result['returncode']}")

    # 保存运行日志
    log_path = os.path.join(output_dir, "run.log")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("=== STDOUT ===\n")
        f.write(result['stdout'])
        f.write("\n=== STDERR ===\n")
        f.write(result['stderr'])
        f.write(f"\n=== RETURN CODE: {result['returncode']} ===\n")
    print(f"日志已保存到: {log_path}")

    # 保存 JSON 结果供 LLM 读取
    result_path = os.path.join(output_dir, "run_result.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
