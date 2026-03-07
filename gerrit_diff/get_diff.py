#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 Gerrit Change 的 diff 信息
"""

import json
import os
import re
import sys
from requests.auth import HTTPDigestAuth
from pygerrit2.rest import GerritRestAPI


def load_config():
    """
    加载配置，优先级：环境变量 > 配置文件
    
    支持的环境变量：
    - GERRIT_URL / GERRIT_BASE_URL: Gerrit服务器地址
    - GERRIT_USERNAME: 用户名
    - GERRIT_PASSWORD: 密码/Token
    
    配置文件路径（可选，按优先级查找）：
    1. ~/.gerrit/config.json（全局配置）
    2. ./config.json（本地配置）
    """
    config = {}
    
    # 配置文件路径（按优先级）
    config_paths = [
        os.path.expanduser('~/.gerrit/config.json'),
        'config.json'
    ]
    
    # 尝试加载第一个存在的配置文件
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                break
            except (json.JSONDecodeError, IOError):
                continue
    
    # 配置文件值作为默认值
    gerrit_config = config.get('gerrit', {})
    
    # 环境变量优先级最高，覆盖配置文件
    base_url = os.getenv('GERRIT_URL') or os.getenv('GERRIT_BASE_URL') or gerrit_config.get('base_url') or gerrit_config.get('url')
    username = os.getenv('GERRIT_USERNAME') or gerrit_config.get('username')
    password = os.getenv('GERRIT_PASSWORD') or gerrit_config.get('password')
    
    return {
        'gerrit': {
            'base_url': base_url,
            'username': username,
            'password': password
        }
    }


def extract_change_id(url):
    """从 Gerrit URL 中提取 change-id"""
    # 首先检查是否是纯数字
    if re.match(r"^\d+$", url):
        return url
    
    patterns = [
        r"/c/(\d+)",
        r"scgit\.amlogic\.com/(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    if url.startswith("http"):
        numbers = re.findall(r'\d+', url)
        if numbers:
            return numbers[-1]
    
    raise ValueError(f"无法从 URL 提取 change-id: {url}")


def extract_diff_content(patch_text):
    """从 patch 文本中提取 diff 内容"""
    diff_start_marker = 'diff --git'
    start_index = patch_text.find(diff_start_marker)
    if start_index == -1:
        return "Diff content not found"
    return patch_text[start_index:]


def get_diff(gerrit_url, base_url, username, password):
    """获取 Gerrit change 的 diff 信息"""
    auth = HTTPDigestAuth(username, password)
    rest = GerritRestAPI(url=base_url, auth=auth)
    
    change_id = extract_change_id(gerrit_url)
    print(f"Change ID: {change_id}")
    
    # 获取 commit 信息
    commit_info = rest.get(f"/changes/{change_id}/revisions/current/commit")
    commit_message = commit_info['message']
    
    # 获取 patch diff
    patch_diff = rest.get(f"/changes/{change_id}/revisions/current/patch")
    diff_content = extract_diff_content(patch_diff)
    
    return {
        'change_id': change_id,
        'commit_message': commit_message,
        'diff_content': diff_content
    }


def main():
    # 读取配置（环境变量优先）
    config = load_config()
    
    gerrit_config = config['gerrit']
    base_url = gerrit_config['base_url']
    username = gerrit_config['username']
    password = gerrit_config['password']
    
    # 验证配置
    if not base_url:
        print("❌ 错误: GERRIT_URL 或 GERRIT_BASE_URL 环境变量未设置")
        print("   请在环境变量中设置：")
        print("   export GERRIT_URL='https://your-gerrit.com'")
        print("   export GERRIT_USERNAME='your-username'")
        print("   export GERRIT_PASSWORD='your-password'")
        sys.exit(1)
    if not username:
        print("❌ 错误: GERRIT_USERNAME 环境变量未设置")
        sys.exit(1)
    if not password:
        print("❌ 错误: GERRIT_PASSWORD 环境变量未设置")
        sys.exit(1)
    
    # 从命令行获取 URL，或使用默认值
    if len(sys.argv) > 1:
        gerrit_url = sys.argv[1]
    else:
        gerrit_url = "https://scgit.amlogic.com/#/c/642117/"
    
    print(f"正在获取: {gerrit_url}")
    print("-" * 80)
    
    try:
        result = get_diff(gerrit_url, base_url, username, password)
        
        print(f"\n{'='*80}")
        print("Commit Message:")
        print(f"{'='*80}")
        print(result['commit_message'])
        
        print(f"\n{'='*80}")
        print("Diff Content:")
        print(f"{'='*80}")
        print(result['diff_content'])
        
        # 保存到文件
        output_file = f"diff_{result['change_id']}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("Commit Message:\n")
            f.write("="*80 + "\n\n")
            f.write(result['commit_message'])
            f.write("\n\n" + "="*80 + "\n")
            f.write("Diff Content:\n")
            f.write("="*80 + "\n\n")
            f.write(result['diff_content'])
        
        print(f"\n{'='*80}")
        print(f"Diff 信息已保存到: {output_file}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
