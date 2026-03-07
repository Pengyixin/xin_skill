#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerrit Comment 评论工具
用于在 Gerrit Change 上添加评论
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


class GerritCommenter:
    """
    Gerrit 评论客户端
    用于在 Gerrit changes 上添加评论
    """

    def __init__(self, base_url, username, password):
        """
        初始化 GerritCommenter

        Args:
            base_url: Gerrit 服务器基础 URL
            username: Gerrit 用户名
            password: Gerrit 密码
        """
        self.base_url = base_url.rstrip('/')
        self.auth = HTTPDigestAuth(username, password)
        self.rest = GerritRestAPI(url=self.base_url, auth=self.auth)

    @staticmethod
    def extract_change_id(url):
        """
        从 Gerrit URL 中提取 change-id
        支持多种格式:
        1. https://scgit.amlogic.com/#/c/644513/  (标准格式)
        2. https://scgit.amlogic.com/c/644513    (简化格式)
        3. https://scgit.amlogic.com/644513      (简单数字格式)
        4. 644513                                (纯数字)

        Args:
            url: Gerrit change URL 或 change ID

        Returns:
            Change ID 字符串
        """
        # 尝试多种匹配模式
        patterns = [
            r"/c/(\d+)",                     # 匹配 /c/644513
            r"scgit\.amlogic\.com/(\d+)",    # 匹配 scgit.amlogic.com/644513
            r"^(\d+)$",                      # 匹配纯数字 644513
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 如果都没有匹配到，尝试匹配完整的URL
        if url.startswith("http"):
            # 从URL中提取数字
            numbers = re.findall(r'\d+', url)
            if numbers:
                # 通常最后一个数字是change ID
                return numbers[-1]
        
        raise ValueError(f"无法从 URL 提取 change-id: {url}")

    def add_comment(self, gerrit_url, message):
        """
        在 Gerrit change 上添加评论

        Args:
            gerrit_url: Gerrit change URL 或 change ID
            message: 评论内容

        Returns:
            bool: 是否成功添加评论
        """
        try:
            change_id = self.extract_change_id(gerrit_url)
            print(f"提取到 Change ID: {change_id}")
            
            # 首先获取 change 信息以确定当前 revision
            change_info = self.rest.get(f"/changes/{change_id}/?o=CURRENT_REVISION")
            current_revision = change_info.get('current_revision')
            
            if not current_revision:
                print("❌ 无法获取当前 revision")
                return False
            
            # 构建评论数据
            comment_data = {
                "message": message,
                "drafts": "PUBLISH_ALL_REVISIONS"  # 发布所有 draft 评论
            }
            
            # 使用 Gerrit API 添加评论
            # POST /changes/{change-id}/revisions/{rev-id}/review/
            endpoint = f"/changes/{change_id}/revisions/{current_revision}/review/"
            
            response = self.rest.post(endpoint, data=comment_data)
            
            print(f"✅ 评论添加成功！")
            print(f"   Change: {change_id}")
            print(f"   Revision: {current_revision}")
            print(f"   消息: {message}")
            return True
            
        except Exception as e:
            print(f"❌ 评论添加失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_inline_comment(self, gerrit_url, message, file_path, line):
        """
        在指定文件的指定行添加行级评论

        Args:
            gerrit_url: Gerrit change URL 或 change ID
            message: 评论内容
            file_path: 文件路径
            line: 行号

        Returns:
            bool: 是否成功添加评论
        """
        try:
            change_id = self.extract_change_id(gerrit_url)
            
            # 构建行级评论数据
            comment_data = {
                "comments": {
                    file_path: [
                        {
                            "line": line,
                            "message": message
                        }
                    ]
                }
            }
            
            # 使用 Gerrit API 添加行级评论
            endpoint = f"/changes/{change_id}/revisions/current/comments/"
            response = self.rest.post(endpoint, data=comment_data)
            
            print(f"✅ 行级评论添加成功！")
            print(f"   Change: {change_id}")
            print(f"   文件: {file_path}")
            print(f"   行号: {line}")
            print(f"   消息: {message}")
            return True
            
        except Exception as e:
            print(f"❌ 行级评论添加失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主函数 - 命令行入口"""
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
    
    # 解析命令行参数
    if len(sys.argv) < 3:
        print("用法: python3 gerrit_comment.py <url> <message>")
        print("  url: Gerrit change URL 或 change ID")
        print("  message: 评论内容")
        print("")
        print("示例:")
        print('  python3 gerrit_comment.py "https://scgit.amlogic.com/#/c/644513/" "test commit"')
        print('  python3 gerrit_comment.py "644513" "test commit"')
        sys.exit(1)
    
    gerrit_url = sys.argv[1]
    message = sys.argv[2]
    
    print(f"正在添加评论到: {gerrit_url}")
    print("-" * 80)
    
    # 创建 commenter 并添加评论
    commenter = GerritCommenter(base_url, username, password)
    success = commenter.add_comment(gerrit_url, message)
    
    if success:
        print("-" * 80)
        print("✅ 操作完成")
        sys.exit(0)
    else:
        print("-" * 80)
        print("❌ 操作失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
