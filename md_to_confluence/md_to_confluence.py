#!/usr/bin/env python3
"""
Markdown to Confluence Uploader

将 Markdown 文件转换为 Confluence 页面格式并自动上传。
支持创建新页面和更新现有页面。
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

import markdown_it
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from atlassian import Confluence

# 加载环境变量
load_dotenv()


def load_config(config_path: str) -> Dict[str, Any]:
    """从 JSON 配置文件加载配置"""
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse config file {config_path}: {e}")
        return {}
    except Exception as e:
        print(f"Warning: Failed to load config file {config_path}: {e}")
        return {}


class MarkdownToConfluenceConverter:
    """Markdown 到 Confluence Storage Format 转换器"""
    
    def __init__(self):
        # 创建 Markdown 解析器
        self.md = markdown_it.MarkdownIt('commonmark').enable('table')
    
    def convert(self, markdown_text: str) -> str:
        """将 Markdown 转换为 Confluence Storage Format"""
        # 先转换为 HTML
        html = self.md.render(markdown_text)
        
        # 预处理：转义所有未被转义的尖括号
        # 只转义符合 <Word> 格式的，但排除 HTML 标签
        import re
        html_tags = {'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                     'strong', 'b', 'em', 'i', 'code', 'pre', 'blockquote',
                     'ul', 'ol', 'li', 'a', 'img', 'table', 'tr', 'td', 'th',
                     'thead', 'tbody', 'span', 'div', 'tt', 'ac', 'ri'}
        
        def replace_angle(match):
            tag_name = match.group(1)
            if tag_name.lower() in html_tags:
                return match.group(0)  # 是 HTML 标签，不转义
            return f'&lt;{tag_name}{match.group(2)}&gt;'
        
        html = re.sub(r'<(\w+)([^>]*)>', replace_angle, html)
        
        # 使用 BeautifulSoup 处理 HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # 将 HTML 转换为 Confluence Storage Format
        confluence_xml = self._convert_to_confluence_format(soup)
        
        return confluence_xml
    
    def _convert_to_confluence_format(self, soup: BeautifulSoup) -> str:
        """将 BeautifulSoup 对象转换为 Confluence Storage Format"""
        
        # 存储代码块内容，用于后续 CDATA 替换
        code_blocks_data = []
        
        # 处理代码块 - 转换为 Confluence 代码宏
        for idx, code_block in enumerate(soup.find_all('pre')):
            code_elem = code_block.find('code')
            if code_elem:
                # 提取语言
                language = ''
                classes = code_elem.get('class', [])
                for cls in classes:
                    if cls.startswith('language-'):
                        language = cls.replace('language-', '')
                        break
                
                # 获取代码内容
                code_content = code_elem.get_text()
                
                # 创建占位符
                placeholder = f"__CODE_BLOCK_{idx}__"
                code_blocks_data.append({
                    'placeholder': placeholder,
                    'content': code_content,
                    'language': language
                })
                
                # 创建 Confluence 代码宏（使用占位符）
                code_macro = soup.new_tag('ac:structured-macro')
                # 检测是否是 mermaid 图表（包括 gantt 图）
                if language == 'mermaid':
                    code_macro['ac:name'] = 'mermaid-macro'
                else:
                    code_macro['ac:name'] = 'code'
                code_macro['ac:schema-version'] = '1'
                
                # 添加语言参数（只对非 mermaid 代码块）
                if language and language != 'mermaid':
                    lang_param = soup.new_tag('ac:parameter')
                    lang_param['ac:name'] = 'language'
                    lang_param.string = language
                    code_macro.append(lang_param)
                
                # 添加代码内容 - 使用 plain-text-body 和 CDATA
                code_body = soup.new_tag('ac:plain-text-body')
                code_body.string = placeholder
                code_macro.append(code_body)
                
                # 替换原代码块
                code_block.replace_with(code_macro)
        
        # 处理内联代码
        for inline_code in soup.find_all('code'):
            if inline_code.parent.name != 'pre':  # 跳过代码块中的代码
                inline_code.name = 'tt'
        
        # 处理信息/警告/提示框（通过引用块语法）
        for blockquote in soup.find_all('blockquote'):
            paragraphs = blockquote.find_all('p')
            panel_macros = []
            
            for p in paragraphs:
                text = p.get_text().strip()
                
                # 检测提示类型
                panel_type = None
                content = text
                
                if text.startswith('[info]') or text.startswith('[INFO]'):
                    panel_type = 'info'
                    content = text[6:].strip()
                elif text.startswith('[warning]') or text.startswith('[WARNING]'):
                    panel_type = 'warning'
                    content = text[9:].strip()
                elif text.startswith('[note]') or text.startswith('[NOTE]'):
                    panel_type = 'note'
                    content = text[6:].strip()
                elif text.startswith('[tip]') or text.startswith('[TIP]'):
                    panel_type = 'tip'
                    content = text[5:].strip()
                
                if panel_type:
                    # 创建 Confluence 信息面板
                    panel_macro = soup.new_tag('ac:structured-macro')
                    panel_macro['ac:name'] = panel_type
                    panel_macro['ac:schema-version'] = '1'
                    
                    panel_body = soup.new_tag('ac:rich-text-body')
                    panel_body.append(BeautifulSoup(f"<p>{content}</p>", 'html.parser'))
                    panel_macro.append(panel_body)
                    panel_macros.append(panel_macro)
            
            # 替换 blockquote 为所有面板
            if panel_macros:
                blockquote.replace_with(*panel_macros)
        
        # 处理水平分割线
        for hr in soup.find_all('hr'):
            hr.name = 'hr'
        
        # 将 HTML 转换为字符串，并进行 Confluence 格式调整
        content = str(soup)
        
        # 替换占位符为实际内容
        for block_data in code_blocks_data:
            placeholder = block_data['placeholder']
            code_content = block_data['content']
            # 所有代码块都使用 CDATA 包裹
            cdata_block = f"<![CDATA[{code_content}]]>"
            content = content.replace(placeholder, cdata_block)
        
        # 包装在 Confluence 页面结构中
        confluence_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE storage SYSTEM "-//Atlassian//Confluence Storage Format//EN">
<storage>
{content}
</storage>'''
        
        return confluence_xml


class ConfluenceUploader:
    """Confluence 页面上传器"""
    
    def __init__(self, url: str, username: str, password: str, is_cloud: bool = False):
        """
        初始化 Confluence 连接
        
        Args:
            url: Confluence 实例 URL
            username: 用户名
            password: 密码或 API Token
            is_cloud: 是否为 Atlassian Cloud（默认 False，使用本地部署）
        """
        self.confluence = Confluence(
            url=url,
            username=username,
            password=password,
            cloud=is_cloud
        )
    
    def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[int] = None,
        labels: Optional[List[str]] = None
    ) -> dict:
        """
        创建新页面
        
        Args:
            space_key: Confluence 空间 key
            title: 页面标题
            content: 页面内容（Confluence Storage Format）
            parent_id: 父页面 ID
            labels: 页面标签列表
            
        Returns:
            创建的页面信息
        """
        # 提取 storage body 内容（去掉 XML 声明）
        body = self._extract_storage_body(content)
        
        # 创建页面
        page = self.confluence.create_page(
            space=space_key,
            title=title,
            body=body,
            parent_id=parent_id,
            type='page',
            representation='storage'
        )
        
        # 添加标签
        if labels and page.get('id'):
            self._add_labels(page['id'], labels)
        
        return page
    
    def update_page(
        self,
        page_id: int,
        title: str,
        content: str,
        labels: Optional[List[str]] = None
    ) -> dict:
        """
        更新现有页面
        
        Args:
            page_id: 页面 ID
            title: 页面标题
            content: 页面内容（Confluence Storage Format）
            labels: 页面标签列表
            
        Returns:
            更新的页面信息
        """
        # 提取 storage body 内容
        body = self._extract_storage_body(content)
        
        # 更新页面
        page = self.confluence.update_page(
            page_id=page_id,
            title=title,
            body=body,
            representation='storage'
        )
        
        # 添加标签
        if labels and page.get('id'):
            self._add_labels(page['id'], labels)
        
        return page
    
    def _extract_storage_body(self, content: str) -> str:
        """从 Confluence XML 中提取 storage body 内容"""
        # 如果内容包含 XML 声明，提取 body 部分
        if '<?xml' in content or '<storage>' in content:
            match = re.search(r'<storage>(.*?)</storage>', content, re.DOTALL)
            if match:
                return match.group(1).strip()
        return content
    
    def _add_labels(self, page_id: str, labels: List[str]):
        """为页面添加标签"""
        for label in labels:
            try:
                self.confluence.set_page_label(page_id, label)
            except Exception as e:
                print(f"Warning: Could not add label '{label}': {e}")


def main():
    parser = argparse.ArgumentParser(
        description='将 Markdown 文件上传到 Confluence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用 config.json 中的配置创建新页面（推荐）
  python md_to_confluence.py doc.md --title "文档" --space-key DEV
  
  # 更新现有页面
  python md_to_confluence.py doc.md --page-id 12345678
  
  # 只查看转换结果
  python md_to_confluence.py doc.md --title "测试" --dry-run
  
  # 使用命令行参数覆盖配置
  python md_to_confluence.py doc.md --title "文档" --space-key DEV \
    --confluence-url https://confluence.company.com \
    --username myuser --password mypass
        '''
    )
    
    parser.add_argument(
        'markdown_file',
        help='Markdown 文件路径'
    )
    
    parser.add_argument(
        '--title', '-t',
        help='页面标题（创建新页面时必需）'
    )
    
    parser.add_argument(
        '--space-key', '-s',
        default=os.getenv('CONFLUENCE_SPACE_KEY'),
        help='Confluence 空间 key（默认从环境变量 CONFLUENCE_SPACE_KEY 读取）'
    )
    
    parser.add_argument(
        '--parent-id', '-p',
        type=int,
        help='父页面 ID（可选）'
    )
    
    parser.add_argument(
        '--page-id',
        type=int,
        help='现有页面 ID（用于更新页面）'
    )
    
    parser.add_argument(
        '--label', '-l',
        action='append',
        default=[],
        help='页面标签（可多次使用）'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只打印转换后的内容，不上传到 Confluence'
    )
    
    parser.add_argument(
        '--confluence-url',
        default=os.getenv('CONFLUENCE_URL'),
        help='Confluence URL（默认从环境变量 CONFLUENCE_URL 读取）'
    )
    
    parser.add_argument(
        '--username',
        default=os.getenv('CONFLUENCE_USERNAME'),
        help='用户名（默认从环境变量 CONFLUENCE_USERNAME 读取）'
    )
    
    parser.add_argument(
        '--password',
        default=os.getenv('CONFLUENCE_PASSWORD'),
        help='密码或 API Token（默认从环境变量 CONFLUENCE_PASSWORD 读取）'
    )
    
    parser.add_argument(
        '--config',
        default='config.json',
        help='配置文件路径（默认: config.json）'
    )
    
    parser.add_argument(
        '--cloud',
        action='store_true',
        help='使用 Atlassian Cloud 模式（默认使用本地部署模式）'
    )
    
    args = parser.parse_args()
    
    # 读取配置文件（优先级：环境变量 > 命令行参数 > 配置文件）
    config = load_config(args.config)
    confluence_config = config.get('confluence', {})

    # 获取配置值，优先级：环境变量 > 命令行 > 配置文件
    confluence_url = os.getenv('CONFLUENCE_URL') or args.confluence_url or confluence_config.get('base_url') or confluence_config.get('url')
    username = os.getenv('CONFLUENCE_USERNAME') or args.username or confluence_config.get('username')
    password = os.getenv('CONFLUENCE_PASSWORD') or args.password or confluence_config.get('password') or confluence_config.get('api_token')
    is_cloud = os.getenv('CONFLUENCE_CLOUD', '').lower() == 'true' or args.cloud or confluence_config.get('cloud', False)
    
    # 读取 Markdown 文件
    if not os.path.exists(args.markdown_file):
        print(f"Error: File not found: {args.markdown_file}")
        sys.exit(1)
    
    with open(args.markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 转换 Markdown 到 Confluence 格式
    converter = MarkdownToConfluenceConverter()
    confluence_content = converter.convert(markdown_content)
    
    # 如果是 dry-run，只打印内容
    if args.dry_run:
        print("=" * 80)
        print("转换后的 Confluence Storage Format 内容:")
        print("=" * 80)
        print(confluence_content)
        print("=" * 80)
        print("\nDry run mode - 未上传到 Confluence")
        return
    
    # 检查必要的配置
    if not confluence_url:
        print("Error: Confluence URL 未设置。请设置 CONFLUENCE_URL 环境变量、使用 --confluence-url 参数，或在 config.json 中配置")
        sys.exit(1)
    
    if not username:
        print("Error: 用户名未设置。请设置 CONFLUENCE_USERNAME 环境变量、使用 --username 参数，或在 config.json 中配置")
        sys.exit(1)
    
    if not password:
        print("Error: 密码未设置。请设置 CONFLUENCE_PASSWORD 环境变量、使用 --password 参数，或在 config.json 中配置")
        sys.exit(1)
    
    # 初始化上传器
    uploader = ConfluenceUploader(
        url=confluence_url,
        username=username,
        password=password,
        is_cloud=is_cloud
    )
    
    # 确定标题
    title = args.title
    if not title:
        # 从文件名获取标题
        title = Path(args.markdown_file).stem.replace('_', ' ').replace('-', ' ').title()
    
    try:
        if args.page_id:
            # 更新现有页面
            print(f"Updating page {args.page_id}...")
            page = uploader.update_page(
                page_id=args.page_id,
                title=title,
                content=confluence_content,
                labels=args.label
            )
            print(f"Page updated successfully!")
            page_url = f"{confluence_url}/pages/viewpage.action?pageId={page['id']}"
            print(f"Page URL: {page_url}")
        else:
            # 检查 space_key
            if not args.space_key:
                print("Error: Space key 未设置。请使用 --space-key 参数或设置 CONFLUENCE_SPACE_KEY 环境变量")
                sys.exit(1)
            
            # 创建新页面
            print(f"Creating new page '{title}' in space '{args.space_key}'...")
            page = uploader.create_page(
                space_key=args.space_key,
                title=title,
                content=confluence_content,
                parent_id=args.parent_id,
                labels=args.label
            )
            print(f"Page created successfully!")
            print(f"Page ID: {page['id']}")
            page_url = f"{confluence_url}/pages/viewpage.action?pageId={page['id']}"
            print(f"Page URL: {page_url}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
