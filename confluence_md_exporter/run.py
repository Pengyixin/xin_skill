#!/usr/bin/env python3
"""
Confluence Markdown Exporter Runner Script
Runs the exporter with retry mechanism
Compatible with Windows and Unix-like systems
"""

import os
import sys
import argparse
import subprocess
import time
import shutil
from pathlib import Path


def flatten_markdown_files(output_path):
    """将嵌套的 md 文件移动到扁平目录结构"""
    if not output_path or not os.path.exists(output_path):
        return

    output_path = Path(output_path)
    moved_files = []
    used_names = {}

    for item in output_path.rglob("*"):
        if item.is_file() and item.suffix == ".md":
            original_name = item.name
            target_path = output_path / original_name

            if item != target_path:
                counter = 1
                while target_path.exists():
                    new_name = f"{item.stem}_{counter}{item.suffix}"
                    target_path = output_path / new_name
                    counter += 1

                shutil.move(str(item), str(target_path))
                moved_files.append(target_path.name)

    # 不删除任何目录，保持用户目录结构完整

    if moved_files:
        print(f"✓ 已将 {len(moved_files)} 个文件移动到扁平目录")


def get_venv_python():
    """Get the Python executable path for the virtual environment"""
    script_dir = Path(__file__).parent.resolve()
    if sys.platform == "win32":
        return script_dir / "venv" / "Scripts" / "python.exe"
    else:
        return script_dir / "venv" / "bin" / "python"


def get_venv_root():
    """Get the virtual environment root directory"""
    script_dir = Path(__file__).parent.resolve()
    return script_dir / "venv"


def load_dotenv():
    """Load .env file if it exists"""
    script_dir = Path(__file__).parent.resolve()
    env_file = script_dir / ".env"

    if not env_file.exists():
        return

    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        # Fallback: manually parse .env file
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ.setdefault(key, value)


def run_exporter(args):
    """Run confluence-markdown-exporter with given arguments"""
    venv_python = get_venv_python()
    venv_root = get_venv_root()

    if not venv_python.exists():
        print("错误: 虚拟环境不存在，请先运行 python setup.py")
        sys.exit(1)

    if sys.platform == "win32":
        exporter_cmd = str(venv_root / "Scripts" / "confluence-markdown-exporter.exe")
    else:
        exporter_cmd = str(venv_root / "bin" / "confluence-markdown-exporter")

    result = subprocess.run(
        [exporter_cmd] + args,
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def run_with_retry(args, max_retries, retry_delay):
    """Run exporter with retry mechanism"""
    attempt = 1
    last_error = ""
    exit_code = 1

    while attempt <= max_retries:
        print(f"尝试 {attempt}/{max_retries}...")

        exit_code, stdout, stderr = run_exporter(args)

        if exit_code == 0:
            if stdout:
                print(stdout)
            print("✓ 导出成功")
            return 0, stdout

        last_error = stderr or stdout or f"未知错误 (退出码: {exit_code})"

        if attempt < max_retries:
            print(f"✗ 导出失败 (退出码: {exit_code})，{retry_delay}秒后重试...")
            print(last_error)
            time.sleep(retry_delay)
        else:
            print(f"✗ 导出失败，已重试 {max_retries} 次")
            print("--- 错误信息 ---")
            print(last_error)

        attempt += 1

    return exit_code, last_error


def main():
    parser = argparse.ArgumentParser(
        description="Confluence Markdown Exporter - 导出 Confluence 页面为 Markdown 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s pages 123456789
  %(prog)s --retries 5 pages 123456789
  %(prog)s --retries 2 --retry-delay 5 pages-with-descendants 123456789
  %(prog)s spaces YOURSPACE --output ./docs
        """
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="设置重试次数 (默认: 3)"
    )

    parser.add_argument(
        "--retry-delay",
        type=int,
        default=2,
        help="设置重试间隔秒数 (默认: 2)"
    )

    parser.add_argument(
        "--flatten",
        action="store_true",
        default=True,
        help="将 md 文件移动到扁平目录结构 (默认: 开启)"
    )

    parser.add_argument(
        "--no-flatten",
        action="store_false",
        dest="flatten",
        help="关闭扁平化输出，保持原有多层目录结构"
    )

    parser.add_argument(
        "command",
        choices=["pages", "pages-with-descendants", "spaces", "all-spaces", "config", "version"],
        help="要执行的命令"
    )

    parser.add_argument(
        "args",
        nargs="*",
        help="命令的参数 (页面ID、空间key等)"
    )

    parser.add_argument(
        "--output-path",
        dest="output_path",
        help="指定输出目录"
    )

    parsed, remaining = parser.parse_known_args()

    final_args = [parsed.command] + parsed.args

    if parsed.output_path:
        final_args.extend(["--output-path", parsed.output_path])

    load_dotenv()

    if os.environ.get("ATLASSIAN_USERNAME"):
        print(f"使用配置的账户: {os.environ['ATLASSIAN_USERNAME']}")

    exit_code, output = run_with_retry(final_args, parsed.retries, parsed.retry_delay)

    if exit_code == 0 and parsed.flatten and parsed.output_path:
        flatten_markdown_files(parsed.output_path)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
