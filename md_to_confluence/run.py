#!/usr/bin/env python3
"""
Markdown to Confluence Uploader Runner Script
Runs the uploader with automatic virtual environment handling
Compatible with Windows and Unix-like systems
"""

import os
import sys
import subprocess
from pathlib import Path


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


def check_venv():
    """Check if virtual environment exists"""
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("错误: 虚拟环境不存在，请先运行 python setup.py")
        sys.exit(1)


def main():
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    check_venv()
    venv_python = get_venv_python()

    script_path = script_dir / "md_to_confluence.py"

    if not script_path.exists():
        print("错误: md_to_confluence.py 不存在")
        sys.exit(1)

    result = subprocess.run(
        [str(venv_python), str(script_path)] + sys.argv[1:]
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
