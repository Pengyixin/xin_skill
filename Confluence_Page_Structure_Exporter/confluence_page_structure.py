#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confluence页面结构导出工具
获取指定Confluence页面的所有子页面标题，并保留其层级结构
"""

import requests
import re
import json
import os
import sys
import html
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class ConfluencePageStructureExporter:
    def __init__(self, config_path=None):
        """
        初始化Confluence页面结构导出器
        :param config_path: 配置文件路径（可选，如提供则优先使用配置文件）
        """
        # 首先尝试从环境变量读取配置
        self.username = os.environ.get('CONFLUENCE_USERNAME')
        self.password = os.environ.get('CONFLUENCE_PASSWORD')
        self.base_url = os.environ.get('CONFLUENCE_URL')
        self.api_token = os.environ.get('CONFLUENCE_API_TOKEN')
        
        # 如果环境变量未设置，则尝试从配置文件读取
        if not all([self.username, self.password, self.base_url]):
            if not config_path:
                raise ValueError("环境变量未设置且未提供配置文件。请设置环境变量(CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD)或使用 -c 参数指定配置文件")
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            # 加载配置文件
            self.config = self.load_config(config_path)
            
            # 验证必需的配置项
            required_keys = ['username', 'password', 'base_url']
            for key in required_keys:
                if key not in self.config.get('confluence', {}):
                    raise ValueError(f"配置文件中缺少必需的配置项: confluence.{key}")
            
            # Confluence配置
            self.username = self.config['confluence']['username']
            self.password = self.config['confluence']['password']
            self.base_url = self.config['confluence']['base_url']
        else:
            print("使用环境变量配置")
        
        # 确保配置值存在
        if not self.username or not self.password or not self.base_url:
            raise ValueError("配置错误：缺少必需的配置项（username, password, base_url）")
        
        # 创建会话
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # 存储页面数据
        self.page_data = {
            'root_page': {},
            'all_pages': [],  # 所有页面（扁平列表）
            'hierarchy': {}   # 层级结构
        }
        
        # 统计信息
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_pages': 0,
            'max_depth': 0
        }
    
    def load_config(self, config_path):
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_page_info_by_url(self, url):
        """通过URL获取页面信息"""
        try:
            # 解析URL
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 尝试匹配 /display/ 格式
            display_match = re.search(r'/display/([^/]+)/(.+)', url)
            
            # 尝试匹配 /pages/viewpage.action?pageId= 格式
            page_id_match = re.search(r'/pages/viewpage\.action\?(?:.*&)?pageId=(\d+)(?:&.*)?(?:#.*)?', url)
            
            if not page_id_match:
                page_id_match = re.search(r'/pages/viewpage\.action.*[?&]pageId=(\d+)', url)
            
            if display_match:
                # 格式1: /display/space_key/page_title
                space_key = display_match.group(1)
                page_title = display_match.group(2).replace('+', ' ')
                
                # 搜索页面
                search_url = f"{base_url}/rest/api/content"
                params = {
                    'spaceKey': space_key,
                    'title': page_title,
                    'expand': 'history.lastUpdated,version,space'
                }
                
                print(f"正在获取页面信息: {page_title} (通过space/title搜索)")
                response = self.session.get(search_url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results'):
                        page = data['results'][0]
                        page_id = page['id']
                        print(f"找到页面ID: {page_id}")
                        
                        return self._get_page_details_by_id(base_url, page_id, url, space_key, page_title)
                    else:
                        print(f"未找到页面: {page_title} (space: {space_key})")
                        return None
                else:
                    print(f"搜索页面失败: HTTP {response.status_code}")
                    return None
                    
            elif page_id_match:
                # 格式2: /pages/viewpage.action?pageId=page_id
                page_id = page_id_match.group(1)
                print(f"正在获取页面信息: 页面ID {page_id} (直接通过ID获取)")
                
                return self._get_page_details_by_id(base_url, page_id, url)
                
            else:
                print(f"错误: 无法解析URL格式: {url}")
                print(f"支持的URL格式:")
                print(f"1. {base_url}/display/SPACEKEY/Page+Title")
                print(f"2. {base_url}/pages/viewpage.action?pageId=PAGE_ID")
                return None
                
        except Exception as e:
            print(f"获取页面信息时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_page_details_by_id(self, base_url, page_id, url, space_key=None, page_title=None):
        """通过页面ID获取页面详细信息"""
        try:
            page_url = f"{base_url}/rest/api/content/{page_id}?expand=history.lastUpdated,version,space"
            page_response = self.session.get(page_url, timeout=30)
            
            if page_response.status_code == 200:
                page_details = page_response.json()
                
                # 获取space_key和title（如果未提供）
                if not space_key:
                    space_key = page_details.get('space', {}).get('key', '')
                
                if not page_title:
                    page_title = html.unescape(page_details.get('title', ''))
                
                return {
                    'id': page_id,
                    'title': page_title,
                    'space_key': space_key,
                    'base_url': base_url,
                    'url': url,
                    'last_updated': page_details.get('history', {}).get('lastUpdated', {}).get('when', ''),
                    'version': page_details.get('version', {}).get('number', ''),
                    'space_name': page_details.get('space', {}).get('name', '')
                }
            else:
                print(f"获取页面内容失败: HTTP {page_response.status_code}")
                print(f"页面ID: {page_id}")
                return None
                
        except Exception as e:
            print(f"获取页面详细信息时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_child_pages(self, parent_id, base_url, max_depth=5, current_depth=1):
        """
        递归获取子页面
        :param parent_id: 父页面ID
        :param base_url: Confluence基础URL
        :param max_depth: 最大递归深度
        :param current_depth: 当前深度
        :return: 包含子页面信息的字典
        """
        if current_depth > max_depth:
            return []
        
        print(f"正在获取深度 {current_depth} 的子页面 (父页面ID: {parent_id})")
        
        # 获取当前页面的子页面
        child_pages = self._get_direct_child_pages(parent_id, base_url)
        
        if not child_pages:
            return []
        
        # 递归获取子页面的子页面
        for child in child_pages:
            child['depth'] = current_depth
            child_children = self.get_child_pages(
                child['id'], 
                base_url, 
                max_depth, 
                current_depth + 1
            )
            child['children'] = child_children if child_children is not None else []
        
        return child_pages
    
    def _get_direct_child_pages(self, parent_id, base_url):
        """获取指定父页面的直接子页面（保持Confluence中的原始顺序）"""
        url = f"{base_url}/rest/api/content/{parent_id}/child/page"
        params = {
            'expand': 'history.lastUpdated,version,space',
            'limit': 1000,
            'start': 0
        }
        
        try:
            children = []
            start = 0
            limit = 100  # 每次获取的数量
            
            while True:
                params['start'] = start
                params['limit'] = limit
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    page_list = data.get('results', [])
                    
                    if not page_list:
                        break
                    
                    for page in page_list:
                        # 构建页面URL
                        webui_link = page.get('_links', {}).get('webui', '')
                        if webui_link:
                            page_url = f"{base_url}{webui_link}"
                        else:
                            # 如果没有webui链接，构建默认URL
                            page_url = f"{base_url}/display/{page.get('space', {}).get('key', '')}/{page['title'].replace(' ', '+')}"
                        
                        children.append({
                            'id': page['id'],
                            'title': page['title'],
                            'url': page_url,
                            'last_updated': page.get('history', {}).get('lastUpdated', {}).get('when', ''),
                            'version': page.get('version', {}).get('number', ''),
                            'space_key': page.get('space', {}).get('key', ''),
                            'children': []  # 占位符，将在递归中填充
                        })
                    
                    # 检查是否还有更多页面
                    if len(page_list) < limit:
                        break
                    
                    start += len(page_list)
                else:
                    print(f"获取子页面失败: HTTP {response.status_code}")
                    break
            
            # 保持Confluence API返回的原始顺序，不进行排序
            print(f"  获取到 {len(children)} 个子页面")
            return children
        except Exception as e:
            print(f"获取子页面时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def flatten_hierarchy(self, node, parent_path=""):
        """将层级结构扁平化为列表"""
        if not node:
            return []
        
        pages = []
        current_path = f"{parent_path}/{node['title']}" if parent_path else node['title']
        
        # 添加当前节点（跳过根节点，因为它已经在root_page中）
        if parent_path:  # 只有子页面才添加到扁平列表
            pages.append({
                'id': node['id'],
                'title': node['title'],
                'url': node['url'],
                'last_updated': node['last_updated'],
                'version': node['version'],
                'depth': node.get('depth', 0),
                'path': current_path
            })
        
        # 递归处理子节点
        for child in node.get('children', []):
            pages.extend(self.flatten_hierarchy(child, current_path))
        
        return pages
    
    def export_page_structure(self, url, max_depth=5, output_format='txt'):
        """
        导出页面结构
        :param url: Confluence页面URL
        :param max_depth: 最大递归深度
        :param output_format: 输出格式 ('txt', 'json', 'md')
        :return: 输出文件路径
        """
        self.stats['start_time'] = datetime.now()
        
        print(f"开始导出页面结构: {url}")
        print(f"最大深度: {max_depth}")
        
        # 获取根页面信息
        root_page = self.get_page_info_by_url(url)
        if not root_page:
            print("获取根页面信息失败")
            return None
        
        self.page_data['root_page'] = root_page
        print(f"根页面: {root_page['title']}")
        print(f"页面ID: {root_page['id']}")
        
        # 递归获取子页面结构
        print("\n开始获取子页面结构...")
        child_pages = self.get_child_pages(
            root_page['id'], 
            root_page['base_url'], 
            max_depth, 
            current_depth=1
        )
        
        # 构建完整的层级结构
        self.page_data['hierarchy'] = {
            'id': root_page['id'],
            'title': root_page['title'],
            'url': root_page['url'],
            'last_updated': root_page['last_updated'],
            'version': root_page['version'],
            'depth': 0,
            'children': child_pages if child_pages else []
        }
        
        # 扁平化层级结构以便统计
        self.page_data['all_pages'] = self.flatten_hierarchy(self.page_data['hierarchy'])
        self.stats['total_pages'] = len(self.page_data['all_pages'])
        
        # 计算最大深度
        if self.page_data['all_pages']:
            self.stats['max_depth'] = max(page['depth'] for page in self.page_data['all_pages'])
        
        self.stats['end_time'] = datetime.now()
        elapsed = self.stats['end_time'] - self.stats['start_time']
        
        # 打印摘要
        self.print_summary(elapsed)
        
        # 生成输出
        output_content = self.generate_output(output_format)
        
        # 生成输出文件名
        safe_title = re.sub(r'[^\w\s-]', '', root_page['title'])
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{safe_title}_structure_{timestamp}.{output_format}"
        
        # 写入文件
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        print(f"\n输出文件已保存: {output_filename}")
        
        return output_filename
    
    def print_summary(self, elapsed):
        """打印摘要信息"""
        print(f"\n{'='*60}")
        print("导出完成!")
        print(f"{'='*60}")
        print(f"根页面: {self.page_data['root_page']['title']}")
        print(f"总页面数: {self.stats['total_pages']}")
        print(f"最大深度: {self.stats['max_depth']}")
        print(f"导出耗时: {elapsed.total_seconds():.2f} 秒")
        
        # 按深度统计
        depth_stats = {}
        for page in self.page_data['all_pages']:
            depth = page['depth']
            depth_stats[depth] = depth_stats.get(depth, 0) + 1
        
        if depth_stats:
            print(f"\n各深度页面统计:")
            for depth in sorted(depth_stats.keys()):
                count = depth_stats[depth]
                print(f"  深度 {depth}: {count} 个页面")
    
    def generate_output(self, output_format):
        """根据格式生成输出内容"""
        if output_format == 'txt':
            return self.generate_txt_output()
        elif output_format == 'json':
            return self.generate_json_output()
        elif output_format == 'md':
            return self.generate_markdown_output()
        else:
            print(f"不支持的输出格式: {output_format}，使用txt格式")
            return self.generate_txt_output()
    
    def generate_txt_output(self):
        """生成文本格式输出"""
        output_lines = []
        
        # 头部信息
        output_lines.append("=" * 80)
        output_lines.append(f"Confluence页面结构导出")
        output_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("=" * 80)
        output_lines.append(f"根页面: {self.page_data['root_page']['title']}")
        output_lines.append(f"根页面URL: {self.page_data['root_page']['url']}")
        output_lines.append(f"最后更新: {self.page_data['root_page']['last_updated']}")
        output_lines.append(f"版本: v{self.page_data['root_page']['version']}")
        output_lines.append(f"总页面数: {self.stats['total_pages']}")
        output_lines.append(f"最大深度: {self.stats['max_depth']}")
        output_lines.append("")
        output_lines.append("页面层级结构:")
        output_lines.append("")
        
        # 递归生成层级结构
        def add_hierarchy_lines(node, indent_level=0):
            if not node:
                return []
            
            lines = []
            indent = "  " * indent_level
            
            # 添加当前节点
            prefix = "├─ " if indent_level > 0 else ""
            title_line = f"{indent}{prefix}{node['title']}"
            
            # 添加元数据（仅显示深度大于0的页面）
            if indent_level > 0:
                title_line += f" (v{node['version']}, {node['last_updated'][:10] if node['last_updated'] else 'N/A'})"
            
            lines.append(title_line)
            
            # 递归添加子节点
            for child in node.get('children', []):
                lines.extend(add_hierarchy_lines(child, indent_level + 1))
            
            return lines
        
        output_lines.extend(add_hierarchy_lines(self.page_data['hierarchy']))
        
        return '\n'.join(output_lines)
    
    def generate_json_output(self):
        """生成JSON格式输出"""
        output_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'root_page': self.page_data['root_page'],
                'statistics': self.stats,
                'total_pages': self.stats['total_pages']
            },
            'hierarchy': self.page_data['hierarchy'],
            'flat_list': self.page_data['all_pages']
        }
        
        return json.dumps(output_data, indent=2, ensure_ascii=False, default=str)
    
    def generate_markdown_output(self):
        """生成Markdown格式输出"""
        output_lines = []
        
        # 头部信息
        output_lines.append(f"# Confluence页面结构: {self.page_data['root_page']['title']}")
        output_lines.append("")
        output_lines.append(f"> **根页面**: [{self.page_data['root_page']['title']}]({self.page_data['root_page']['url']})  ")
        output_lines.append(f"> **最后更新**: {self.page_data['root_page']['last_updated']}  ")
        output_lines.append(f"> **版本**: v{self.page_data['root_page']['version']}  ")
        output_lines.append(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        output_lines.append(f"> **总页面数**: {self.stats['total_pages']}  ")
        output_lines.append(f"> **最大深度**: {self.stats['max_depth']}  ")
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        
        # 递归生成层级结构
        def add_markdown_hierarchy(node, indent_level=0):
            if not node:
                return []
            
            lines = []
            indent = "  " * indent_level
            
            # 添加当前节点
            if indent_level == 0:
                lines.append(f"## {node['title']}")
                lines.append(f"- **URL**: {node['url']}")
                lines.append(f"- **最后更新**: {node['last_updated']}")
                lines.append(f"- **版本**: v{node['version']}")
                lines.append("")
                lines.append("### 子页面结构")
                lines.append("")
            else:
                # 为子页面生成列表项
                bullet = "-" if indent_level == 1 else "  " * (indent_level - 1) + "-"
                title_line = f"{bullet} **{node['title']}**"
                
                # 添加元数据
                meta_parts = []
                if node.get('last_updated'):
                    meta_parts.append(f"最后更新: {node['last_updated'][:10]}")
                if node.get('version'):
                    meta_parts.append(f"版本: v{node['version']}")
                if node.get('url'):
                    meta_parts.append(f"[链接]({node['url']})")
                
                if meta_parts:
                    title_line += f" ({', '.join(meta_parts)})"
                
                lines.append(title_line)
            
            # 递归添加子节点
            for child in node.get('children', []):
                lines.extend(add_markdown_hierarchy(child, indent_level + 1))
            
            return lines
        
        output_lines.extend(add_markdown_hierarchy(self.page_data['hierarchy']))
        
        # 添加扁平列表
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")
        output_lines.append("## 所有页面列表")
        output_lines.append("")
        
        for page in sorted(self.page_data['all_pages'], key=lambda x: x['path']):
            depth_indent = "  " * (page['depth'] - 1) if page['depth'] > 1 else ""
            bullet = "-" if page['depth'] == 1 else "  " * (page['depth'] - 2) + "-"
            output_lines.append(f"{depth_indent}{bullet} [{page['title']}]({page['url']}) (深度: {page['depth']}, 最后更新: {page['last_updated'][:10] if page['last_updated'] else 'N/A'})")
        
        return '\n'.join(output_lines)

def main():
    parser = argparse.ArgumentParser(description='导出Confluence页面结构（包括所有子页面）')
    parser.add_argument('url', help='Confluence页面URL')
    parser.add_argument('-c', '--config', help='配置文件路径（可选，优先使用环境变量）')
    parser.add_argument('-d', '--depth', type=int, default=2, help='最大递归深度（默认：2）')
    parser.add_argument('-f', '--format', choices=['txt', 'json', 'md'], default='txt', 
                       help='输出格式：txt（文本）、json、md（Markdown）（默认：txt）')
    parser.add_argument('-o', '--output', help='输出文件路径（可选，默认自动生成）')
    
    args = parser.parse_args()
    
    # 创建导出器
    try:
        exporter = ConfluencePageStructureExporter(args.config)
    except (ValueError, FileNotFoundError) as e:
        print(f"配置错误: {e}")
        print(f"\n配置方式一（环境变量 - 推荐）：")
        print(f"  export CONFLUENCE_URL=\"https://confluence.yourcompany.com\"")
        print(f"  export CONFLUENCE_USERNAME=\"your_username\"")
        print(f"  export CONFLUENCE_PASSWORD=\"your_password\"")
        print(f"\n配置方式二（配置文件）：")
        print(f"  使用 -c 参数指定配置文件路径")
        print(f"  配置文件格式示例:")
        print(json.dumps({
            "confluence": {
                "username": "your_username",
                "password": "your_password",
                "base_url": "https://confluence.yourcompany.com"
            }
        }, indent=2, ensure_ascii=False))
        return 1
    
    # 导出页面结构
    try:
        output_file = exporter.export_page_structure(args.url, args.depth, args.format)
        
        if not output_file:
            print("导出失败")
            return 1
        
        print(f"\n{'='*60}")
        print(f"页面结构导出成功!")
        print(f"输出文件: {output_file}")
        
    except Exception as e:
        print(f"导出过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
