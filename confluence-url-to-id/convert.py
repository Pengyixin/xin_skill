#!/usr/bin/env python3
"""
Amlogic Confluence URL 转页面 ID 工具

支持将 Amlogic Confluence 页面 URL 转换为页面 ID
"""

import os
import sys
import argparse
import re
import json
from urllib.parse import unquote, urlparse
from typing import Optional, List, Tuple
import requests
from requests.auth import HTTPBasicAuth

# 不再使用 .env 文件，只从环境变量读取配置
# 支持的环境变量：
#   CONFLUENCE_URL - Confluence 服务器地址
#   CONFLUENCE_USERNAME - 用户名
#   CONFLUENCE_PASSWORD - 密码（或 CONFLUENCE_API_TOKEN）
#   CONFLUENCE_API_TOKEN - API Token（优先于密码）


class ConfluenceURLConverter:
    """Confluence URL 转换器"""
    
    def __init__(self, base_url: str, username: str, auth_type: str, auth_value: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.auth_type = auth_type  # 'token', 'password', 或 'pat'
        self.auth_value = auth_value
        
        # 检查是否是 PAT (Personal Access Token)
        # PAT 通常是以 base64 编码的长字符串，用于 Bearer 认证
        if auth_type == 'token' and self._is_pat_token(auth_value):
            self.auth_type = 'pat'
            self.auth = None  # PAT 不需要 auth 对象
        else:
            self.auth = HTTPBasicAuth(username, auth_value)
    
    def _is_pat_token(self, token: str) -> bool:
        """检查 token 是否是 Personal Access Token"""
        # PAT 通常是较长的 base64 字符串（通常 40+ 字符）
        # 而 Atlassian API Token 通常较短
        return len(token) > 40 and token.replace('-', '').replace('_', '').isalnum()
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        headers = {'Accept': 'application/json'}
        if self.auth_type == 'pat':
            headers['Authorization'] = f'Bearer {self.auth_value}'
        return headers
    
    def parse_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析 Confluence URL，提取空间 key 和页面标题
        
        支持格式：
        - https://confluence.amlogic.com/display/SW/Page+Title
        - https://confluence.amlogic.com/pages/viewpage.action?pageId=123456
        - https://confluence.amlogic.com/pages/viewpage.action?spaceKey=SW&title=Page+Title
        """
        parsed = urlparse(url)
        path = unquote(parsed.path)
        query = parsed.query
        
        # 格式 1: /display/SPACE/TITLE
        display_match = re.match(r'/display/([^/]+)/(.+)', path)
        if display_match:
            space_key = display_match.group(1)
            title = display_match.group(2).replace('+', ' ')
            return space_key, title
        
        # 格式 2: /pages/viewpage.action?pageId=123456
        if 'pageId=' in query:
            return None, None  # 已经有 ID 了
        
        # 格式 3: /pages/viewpage.action?spaceKey=SW&title=Page+Title
        if 'spaceKey=' in query and 'title=' in query:
            space_match = re.search(r'spaceKey=([^&]+)', query)
            title_match = re.search(r'title=([^&]+)', query)
            if space_match and title_match:
                space_key = unquote(space_match.group(1))
                title = unquote(title_match.group(1)).replace('+', ' ')
                return space_key, title
        
        return None, None
    
    def get_page_id_by_title(self, space_key: str, title: str) -> Optional[str]:
        """通过空间 key 和标题获取页面 ID"""
        try:
            url = f"{self.base_url}/rest/api/content"
            params = {
                'spaceKey': space_key,
                'title': title,
                'expand': 'id,space'
            }
            
            # 根据认证类型构建请求参数
            request_kwargs = {
                'params': params,
                'headers': self._get_headers(),
                'timeout': 30
            }
            if self.auth_type != 'pat':
                request_kwargs['auth'] = self.auth
            
            response = requests.get(url, **request_kwargs)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    return data['results'][0].get('id')
                else:
                    print(f"⚠️  未找到页面: 空间={space_key}, 标题={title}")
                    return None
            elif response.status_code == 401:
                print("❌ 认证失败 (401): 请检查用户名和 API Token")
                return None
            else:
                print(f"❌ API 错误: HTTP {response.status_code}")
                print(f"响应: {response.text[:200]}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
            return None
    
    def convert_url(self, url: str) -> Optional[dict]:
        """转换 URL 为页面信息"""
        # 检查是否已经有 pageId
        parsed = urlparse(url)
        page_id_match = re.search(r'pageId=(\d+)', parsed.query)
        
        if page_id_match:
            return {
                'url': url,
                'page_id': page_id_match.group(1),
                'space': None,
                'title': None,
                'note': 'URL 中已包含页面 ID'
            }
        
        # 解析 URL
        space_key, title = self.parse_url(url)
        
        if not space_key or not title:
            print(f"❌ 无法解析 URL: {url}")
            print("支持的格式:")
            print("  - https://confluence.amlogic.com/display/SPACE/Page+Title")
            print("  - https://confluence.amlogic.com/pages/viewpage.action?spaceKey=SPACE&title=Page+Title")
            return None
        
        # 获取页面 ID
        page_id = self.get_page_id_by_title(space_key, title)
        
        if page_id:
            return {
                'url': url,
                'page_id': page_id,
                'space': space_key,
                'title': title
            }
        
        return None
    
    def print_result(self, result: dict):
        """打印转换结果"""
        if result:
            print("\n" + "="*60)
            if result.get('title'):
                print(f"页面标题: {result['title']}")
            if result.get('space'):
                print(f"空间: {result['space']}")
            print(f"页面 ID: {result['page_id']}")
            print(f"URL: {result['url']}")
            if result.get('note'):
                print(f"备注: {result['note']}")
            print("="*60)


def interactive_config():
    """交互式配置"""
    print("🔧 Amlogic Confluence URL 转换器 - 配置向导")
    print("="*60)
    
    # 检查当前配置（支持新的环境变量名）
    current_username = os.getenv('CONFLUENCE_USERNAME') or os.getenv('ATLASSIAN_USERNAME', '')
    current_url = os.getenv('CONFLUENCE_URL') or os.getenv('ATLASSIAN_URL', 'https://confluence.amlogic.com')
    current_token = os.getenv('CONFLUENCE_API_TOKEN') or os.getenv('ATLASSIAN_API_TOKEN', '')
    current_password = os.getenv('CONFLUENCE_PASSWORD') or os.getenv('ATLASSIAN_PASSWORD', '')
    current_auth_type = 'token' if current_token else ('password' if current_password else '')
    
    print(f"\n当前配置:")
    print(f"  URL: {current_url}")
    print(f"  用户名: {current_username or '(未设置)'}")
    if current_token:
        print(f"  认证方式: API Token (已设置)")
    elif current_password:
        print(f"  认证方式: 密码 (已设置)")
    else:
        print(f"  认证方式: (未设置)")
    
    print("\n请输入新的配置值（直接回车保持当前值）:")
    
    url = input(f"Confluence URL [{current_url}]: ").strip() or current_url
    username = input(f"用户名 [{current_username}]: ").strip() or current_username
    
    # 选择认证方式
    auth_type = input(f"认证方式 (token/password) [{current_auth_type}]: ").strip().lower() or current_auth_type
    
    if auth_type == 'token':
        token = input("API Token (输入隐藏): ").strip()
        if not token and current_token:
            keep_current = input("保持当前 API Token? (y/n) [y]: ").strip().lower() or 'y'
            if keep_current == 'y':
                token = current_token
        
        # 只显示环境变量导出命令，不保存到文件
        print("\n" + "="*60)
        print("✅ 配置完成! 请设置以下环境变量:")
        print("="*60)
        print(f"export CONFLUENCE_URL=\"{url}\"")
        print(f"export CONFLUENCE_USERNAME=\"{username}\"")
        print(f"export CONFLUENCE_API_TOKEN=\"{token}\"")
        print("="*60)
    else:
        password = input("密码 (输入隐藏): ").strip()
        if not password and current_password:
            keep_current = input("保持当前密码? (y/n) [y]: ").strip().lower() or 'y'
            if keep_current == 'y':
                password = current_password
        
        # 只显示环境变量导出命令，不保存到文件
        print("\n" + "="*60)
        print("✅ 配置完成! 请设置以下环境变量:")
        print("="*60)
        print(f"export CONFLUENCE_URL=\"{url}\"")
        print(f"export CONFLUENCE_USERNAME=\"{username}\"")
        print(f"export CONFLUENCE_PASSWORD=\"{password}\"")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Amlogic Confluence URL 转页面 ID 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s config                           # 交互式配置
  %(prog)s url "https://.../display/SW/Page" # 转换单个 URL
  %(prog)s url URL1 URL2 URL3               # 转换多个 URL
  %(prog)s file urls.txt                    # 从文件批量转换
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # config 命令
    config_parser = subparsers.add_parser('config', help='交互式配置认证信息')
    
    # url 命令
    url_parser = subparsers.add_parser('url', help='转换 URL')
    url_parser.add_argument('urls', nargs='+', help='一个或多个 Confluence URL')
    
    # file 命令
    file_parser = subparsers.add_parser('file', help='从文件批量转换')
    file_parser.add_argument('filepath', help='包含 URL 列表的文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'config':
        interactive_config()
        return
    
    # 获取配置（支持新的环境变量名）
    base_url = os.getenv('CONFLUENCE_URL') or os.getenv('ATLASSIAN_URL', 'https://confluence.amlogic.com')
    username = os.getenv('CONFLUENCE_USERNAME') or os.getenv('ATLASSIAN_USERNAME')
    
    # 优先使用 API Token，如果没有则使用密码
    api_token = os.getenv('CONFLUENCE_API_TOKEN') or os.getenv('ATLASSIAN_API_TOKEN')
    password = os.getenv('CONFLUENCE_PASSWORD') or os.getenv('ATLASSIAN_PASSWORD')
    
    auth_type = 'token'
    auth_value = api_token
    if not auth_value and password:
        auth_type = 'password'
        auth_value = password
    
    if not username or not auth_value:
        print("❌ 错误: 未配置认证信息")
        print("\n请设置以下环境变量:")
        print("  export CONFLUENCE_URL=\"https://confluence.amlogic.com\"")
        print("  export CONFLUENCE_USERNAME=\"your-email@amlogic.com\"")
        print("  export CONFLUENCE_API_TOKEN=\"your-api-token\"")
        print("  # 或者使用密码:")
        print("  export CONFLUENCE_PASSWORD=\"your-password\"")
        print("\n或使用旧的环境变量名:")
        print("  ATLASSIAN_URL, ATLASSIAN_USERNAME, ATLASSIAN_API_TOKEN/ATLASSIAN_PASSWORD")
        sys.exit(1)
    
    # 创建转换器
    converter = ConfluenceURLConverter(base_url, username, auth_type, auth_value)
    
    urls_to_convert = []
    
    if args.command == 'url':
        urls_to_convert = args.urls
    elif args.command == 'file':
        if not os.path.exists(args.filepath):
            print(f"❌ 文件不存在: {args.filepath}")
            sys.exit(1)
        
        with open(args.filepath, 'r') as f:
            urls_to_convert = [line.strip() for line in f if line.strip()]
    
    # 转换 URL
    print(f"🔄 开始转换 {len(urls_to_convert)} 个 URL...")
    print(f"Confluence: {base_url}")
    print(f"用户: {username}")
    # 显示实际的认证类型（可能是 pat/token/password）
    display_auth_type = converter.auth_type
    print(f"认证方式: {display_auth_type}")
    print()
    
    success_count = 0
    for url in urls_to_convert:
        result = converter.convert_url(url)
        if result:
            converter.print_result(result)
            success_count += 1
    
    print(f"\n✅ 完成: {success_count}/{len(urls_to_convert)} 个 URL 转换成功")
    
    if success_count < len(urls_to_convert):
        sys.exit(1)


if __name__ == '__main__':
    main()
