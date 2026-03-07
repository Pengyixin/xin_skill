#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 Gerrit Change 的 diff 信息
"""

import json
import re
import sys
from requests.auth import HTTPDigestAuth
from pygerrit2.rest import GerritRestAPI


def extract_change_id(url):
    """从 Gerrit URL 中提取 change-id"""
    patterns = [
        r"/c/(\d+)",
        r"scgit\.amlogic\.com/(\d+)",
        r"^\d+$",
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
    # 读取配置
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    gerrit_config = config['gerrit']
    base_url = gerrit_config['base_url']
    username = gerrit_config['username']
    password = gerrit_config['password']
    
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
