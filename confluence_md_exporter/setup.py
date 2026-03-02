#!/usr/bin/env python3
"""
Confluence Markdown Exporter Setup Script
Creates virtual environment and installs dependencies
Compatible with Windows and Unix-like systems
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python 3.10+ is available"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"错误: 需要 Python 3.10+，当前版本: {sys.version}")
        print("请先安装 Python 3.10 或更高版本")
        sys.exit(1)
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")


def get_venv_python():
    """Get the Python executable path for the virtual environment"""
    script_dir = Path(__file__).parent.resolve()
    if sys.platform == "win32":
        venv_python = script_dir / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = script_dir / "venv" / "bin" / "python"
    return venv_python


def create_virtual_env():
    """Create virtual environment if it doesn't exist"""
    script_dir = Path(__file__).parent.resolve()
    venv_path = script_dir / "venv"

    if venv_path.exists():
        print("虚拟环境已存在")
    else:
        print("创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("虚拟环境创建完成")


def upgrade_pip():
    """Upgrade pip in the virtual environment"""
    print("升级 pip...")
    venv_python = get_venv_python()
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)


def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("安装依赖包...")
    script_dir = Path(__file__).parent.resolve()
    requirements_file = script_dir / "requirements.txt"

    if not requirements_file.exists():
        print("警告: requirements.txt 不存在")
        return

    venv_python = get_venv_python()
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
        check=True
    )


def main():
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    print("=" * 40)
    print("Confluence Markdown Exporter 初始化")
    print("=" * 40)
    print()

    check_python_version()
    create_virtual_env()
    upgrade_pip()
    install_dependencies()

    print()
    print("=" * 40)
    print("初始化完成!")
    print("=" * 40)
    print()
    print("使用方法:")
    print("  python run.py pages <page-id> [--output <目录>]")
    print("  python run.py --help")
    print()
    print("配置认证信息:")
    print("  1. 编辑 .env 文件")
    print("  2. 或设置环境变量:")
    print("     ATLASSIAN_USERNAME=your-email@company.com")
    print("     ATLASSIAN_API_TOKEN=your-api-token")
    print("     ATLASSIAN_URL=https://confluence.company.com")
    print()


if __name__ == "__main__":
    main()
